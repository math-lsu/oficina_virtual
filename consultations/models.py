from django.db import models
from django.conf import settings

class TeacherAssignment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_teachers')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_students')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'teacher')

    def __str__(self):
        return f"{self.student.username} -> {self.teacher.username}"

class ConsultationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('resolved', 'Resuelta'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consultation_requests')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultation_requests_received')

    def __str__(self):
        return self.title

class Document(models.Model):
    DOCUMENT_TYPES = (
        ('material', 'Material de estudio'),
        ('exercise', 'Ejercicio'),
        ('submission', 'Entrega de estudiante'),
        ('feedback', 'Retroalimentación'),
    )
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents_created')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='documents_received')
    consultation_request = models.ForeignKey(ConsultationRequest, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    parent_document = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title

class StudentDocumentStatus(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=False)
    hidden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'document')

    def __str__(self):
        return f"{self.student.username} - {self.document.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('request_created', 'Nueva consulta'),
        ('request_responded', 'Consulta respondida'),
        ('document_uploaded', 'Documento subido'),
    )
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    verb = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='request_created')
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_model = models.CharField(max_length=100, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.recipient.username}: {self.verb}"