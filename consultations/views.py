from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import FileResponse, Http404
from django.contrib import messages
from django.utils import timezone
from .models import ConsultationRequest, TeacherAssignment, Document, StudentDocumentStatus, Notification
from .forms import ConsultationRequestForm, ConsultationResponseForm, DocumentUploadForm
from .forms import TeacherNotificationForm
from .forms import TeacherDocumentUploadForm 
from accounts.models import User
 
# ==================== DASHBOARDS ====================
class StudentDashboardView(LoginRequiredMixin, ListView):
    model = ConsultationRequest
    template_name = 'consultations/student_dashboard.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return ConsultationRequest.objects.filter(student=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        context['pending_count'] = qs.filter(status='pending').count()
        context['resolved_count'] = qs.filter(status='resolved').count()
        return context

class TeacherDashboardView(LoginRequiredMixin, ListView):
    model = ConsultationRequest
    template_name = 'consultations/teacher_dashboard.html'
    context_object_name = 'pending_requests'

    def get_queryset(self):
        return ConsultationRequest.objects.filter(teacher=self.request.user, status='pending').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resolved_requests'] = ConsultationRequest.objects.filter(teacher=self.request.user, status='resolved').order_by('-resolved_at')
        context['pending_count'] = self.get_queryset().count()
        context['all_students'] = TeacherAssignment.objects.filter(teacher=self.request.user, is_active=True).select_related('student')
        return context

# ==================== CONSULTATION REQUESTS ====================
class CreateRequestView(LoginRequiredMixin, CreateView):
    model = ConsultationRequest
    form_class = ConsultationRequestForm
    template_name = 'consultations/create_request.html'
    success_url = reverse_lazy('consultations:student_dashboard')

    def form_valid(self, form):
        assignment = TeacherAssignment.objects.filter(student=self.request.user, is_active=True).first()
        if not assignment:
            messages.error(self.request, "No tienes un profesor asignado.")
            return redirect('consultations:student_dashboard')
        form.instance.student = self.request.user
        form.instance.teacher = assignment.teacher
        form.instance.status = 'pending'
        response = super().form_valid(form)
        Notification.objects.create(
            recipient=assignment.teacher,
            actor=self.request.user,
            verb=f"Nueva consulta: {form.instance.title}",
            notification_type='request_created',
            target_id=form.instance.id,
            target_model='consultationrequest'
        )
        messages.success(self.request, "Consulta enviada.")
        return response

class ViewRequestDetailView(LoginRequiredMixin, DetailView):
    model = ConsultationRequest
    template_name = 'consultations/view_request.html'
    context_object_name = 'consultation'

    def get_queryset(self):
        user = self.request.user
        return ConsultationRequest.objects.filter(student=user) | ConsultationRequest.objects.filter(teacher=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        return context

class RespondRequestView(LoginRequiredMixin, UpdateView):
    model = ConsultationRequest
    form_class = ConsultationResponseForm
    template_name = 'consultations/respond_request.html'
    success_url = reverse_lazy('consultations:teacher_dashboard')

    def get_queryset(self):
        return ConsultationRequest.objects.filter(teacher=self.request.user, status='pending')

    def form_valid(self, form):
        form.instance.status = 'resolved'
        form.instance.resolved_at = timezone.now()
        response = super().form_valid(form)
        Notification.objects.create(
            recipient=form.instance.student,
            actor=self.request.user,
            verb=f"Tu consulta '{form.instance.title}' ha sido respondida",
            notification_type='request_responded',
            target_id=form.instance.id,
            target_model='consultationrequest'
        )
        messages.success(self.request, "Respuesta enviada.")
        return response

# ==================== DOCUMENT UPLOAD (general) ====================
class UploadDocumentView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Document
    form_class = TeacherDocumentUploadForm   # cambia de DocumentUploadForm a TeacherDocumentUploadForm
    template_name = 'consultations/upload_document.html'
    success_url = reverse_lazy('consultations:teacher_dashboard')

    def test_func(self):
        return self.request.user.role == 'teacher' or self.request.user.is_superuser

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Guardar el documento
        document = form.save(commit=False)
        document.teacher = self.request.user
        document.save()
        
        # Determinar destinatarios
        send_to_all = form.cleaned_data['send_to_all']
        selected_students = form.cleaned_data['selected_students']
        
        if send_to_all:
            students = User.objects.filter(assigned_teachers__teacher=self.request.user, assigned_teachers__is_active=True)
        else:
            students = selected_students
        
        # Crear notificaciones para cada estudiante
        for student in students:
            Notification.objects.create(
                recipient=student,
                actor=self.request.user,
                verb=f"Nuevo documento: {document.title}",
                notification_type='document_uploaded',
                target_id=document.id,
                target_model='document'
            )
        
        messages.success(self.request, f"Documento subido exitosamente. Enviado a {students.count()} estudiante(s).")
        return super().form_valid(form)


class UploadDocumentToRequestView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = 'consultations/upload_document_to_request.html'

    def dispatch(self, request, *args, **kwargs):
        self.consultation_request = get_object_or_404(ConsultationRequest, pk=kwargs['request_pk'])
        if request.user != self.consultation_request.student and request.user != self.consultation_request.teacher:
            messages.error(request, "No tienes permiso para subir documentos aquí.")
            return redirect('consultations:view_request', pk=self.consultation_request.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.consultation_request = self.consultation_request
        if self.request.user.role == 'teacher':
            form.instance.teacher = self.request.user
        else:
            form.instance.student = self.request.user
            form.instance.teacher = self.consultation_request.teacher
        response = super().form_valid(form)
        # Notificar a la otra parte
        recipient = self.consultation_request.teacher if self.request.user == self.consultation_request.student else self.consultation_request.student
        Notification.objects.create(
            recipient=recipient,
            actor=self.request.user,
            verb=f"Documento subido a la consulta: {form.instance.title}",
            notification_type='document_uploaded',
            target_id=form.instance.id,
            target_model='document'
        )
        messages.success(self.request, "Documento adjuntado.")
        return response

    def get_success_url(self):
        return reverse_lazy('consultations:view_request', kwargs={'pk': self.consultation_request.pk})

# ==================== STUDENT DOCUMENT LISTS ====================
class StudentDocumentsView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'consultations/student_documents.html'
    context_object_name = 'documents'

    def get_queryset(self):
        teacher_ids = TeacherAssignment.objects.filter(student=self.request.user, is_active=True).values_list('teacher_id', flat=True)
        return Document.objects.filter(
            teacher_id__in=teacher_ids,
            document_type__in=['material', 'exercise']
        ).exclude(
            studentdocumentstatus__student=self.request.user,
            studentdocumentstatus__is_hidden=True
        ).order_by('-uploaded_at')

class StudentExercisesView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'consultations/student_exercises.html'
    context_object_name = 'exercises'

    def get_queryset(self):
        teacher_ids = TeacherAssignment.objects.filter(student=self.request.user, is_active=True).values_list('teacher_id', flat=True)
        return Document.objects.filter(teacher_id__in=teacher_ids, document_type='exercise').order_by('-uploaded_at')

class SubmitExerciseView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentUploadForm
    template_name = 'consultations/submit_exercise.html'

    def dispatch(self, request, *args, **kwargs):
        self.exercise = get_object_or_404(Document, pk=kwargs['exercise_id'], document_type='exercise')
        if not TeacherAssignment.objects.filter(student=request.user, teacher=self.exercise.teacher, is_active=True).exists():
            messages.error(request, "No tienes permiso para entregar este ejercicio.")
            return redirect('consultations:student_exercises')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.document_type = 'submission'
        form.instance.teacher = self.exercise.teacher
        form.instance.student = self.request.user
        form.instance.parent_document = self.exercise
        response = super().form_valid(form)
        Notification.objects.create(
            recipient=self.exercise.teacher,
            actor=self.request.user,
            verb=f"Entregó ejercicio: {form.instance.title}",
            notification_type='document_uploaded',
            target_id=form.instance.id,
            target_model='document'
        )
        messages.success(self.request, "Ejercicio entregado.")
        return response

    def get_success_url(self):
        return reverse_lazy('consultations:my_submissions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exercise'] = self.exercise
        return context

class MySubmissionsView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'consultations/my_submissions.html'
    context_object_name = 'submissions'

    def get_queryset(self):
        return Document.objects.filter(student=self.request.user, document_type='submission').order_by('-uploaded_at')

class ReviewSubmissionsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Document
    template_name = 'consultations/review_submissions.html'
    context_object_name = 'submissions'

    def test_func(self):
        return self.request.user.role == 'teacher'

    def get_queryset(self):
        return Document.objects.filter(teacher=self.request.user, document_type='submission').order_by('-uploaded_at')

# ==================== DOCUMENT DOWNLOAD & HIDE ====================
class DownloadDocumentView(LoginRequiredMixin, View):
    def get(self, request, doc_id):
        document = get_object_or_404(Document, pk=doc_id)
        user = request.user
        has_access = False

        if user.role == 'student':
            has_access = TeacherAssignment.objects.filter(student=user, teacher=document.teacher, is_active=True).exists()
            if not has_access and document.student == user:
                has_access = True
        elif user.role == 'teacher':
            if document.teacher == user:
                has_access = True
            elif document.student and TeacherAssignment.objects.filter(student=document.student, teacher=user, is_active=True).exists():
                has_access = True

        if not has_access:
            raise Http404("No tienes permiso para descargar este documento.")

        return FileResponse(document.file.open(), as_attachment=True)

class HideDocumentView(LoginRequiredMixin, View):
    def post(self, request, doc_id):
        document = get_object_or_404(Document, pk=doc_id)
        if not TeacherAssignment.objects.filter(student=request.user, teacher=document.teacher, is_active=True).exists():
            messages.error(request, "No tienes permiso para ocultar este documento.")
            return redirect('consultations:student_documents')
        status, _ = StudentDocumentStatus.objects.get_or_create(student=request.user, document=document)
        status.is_hidden = True
        status.hidden_at = timezone.now()
        status.save()
        messages.success(request, "Documento oculto.")
        return redirect('consultations:student_documents')

# ==================== NOTIFICATIONS ====================
class NotificationsView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'consultations/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.is_read = True
        notification.save()
        return redirect('consultations:notifications')
    
class SendNotificationView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'consultations/send_notification.html'
    form_class = TeacherNotificationForm
    success_url = reverse_lazy('consultations:teacher_dashboard')

    def test_func(self):
        return self.request.user.role == 'teacher' or self.request.user.is_superuser

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.request.user
        return kwargs

    def form_valid(self, form):
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        send_to_all = form.cleaned_data['send_to_all']
        selected_students = form.cleaned_data['selected_students']

        if send_to_all:
            students = User.objects.filter(assigned_teachers__teacher=self.request.user, assigned_teachers__is_active=True)
        else:
            students = selected_students

        for student in students:
            Notification.objects.create(
                recipient=student,
                actor=self.request.user,
                verb=message,
                notification_type='system'
            )

        messages.success(self.request, f'Notificación enviada a {students.count()} estudiante(s).')
        return super().form_valid(form)


class RespondRequestView(LoginRequiredMixin, UpdateView):
    model = ConsultationRequest
    form_class = ConsultationResponseForm   # <-- asegurar esta línea
    template_name = 'consultations/respond_request.html'
    success_url = reverse_lazy('consultations:teacher_dashboard')
    context_object_name = 'consultation'

    def get_queryset(self):
        # Solo consultas pendientes del profesor actual
        return ConsultationRequest.objects.filter(teacher=self.request.user, status='pending')

    def form_valid(self, form):
        # Obtener la consulta sin guardar aún
        consultation = form.save(commit=False)
        consultation.status = 'resolved'
        consultation.resolved_at = timezone.now()
        consultation.save()   # Guardar cambios

        # Crear notificación al estudiante
        Notification.objects.create(
            recipient=consultation.student,
            actor=self.request.user,
            verb=f"Tu consulta '{consultation.title}' ha sido respondida",
            notification_type='request_responded',
            target_id=consultation.id,
            target_model='consultationrequest'
        )
        messages.success(self.request, "Respuesta enviada correctamente.")
        return redirect(self.get_success_url())
    
    