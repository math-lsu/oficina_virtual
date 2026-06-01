from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import User

class RegisterView(SuccessMessageMixin, CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:dashboard')
    success_message = "Registro exitoso. Bienvenido."

    def form_valid(self, form):
        response = super().form_valid(form)
        # Autenticar al usuario después del registro
        from django.contrib.auth import login
        login(self.request, self.object)
        return response

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')


 

class DashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Si es superusuario o staff, ir al admin
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/admin/')
        
        # Redirigir según rol
        if request.user.role == 'student':
            return redirect('consultations:student_dashboard')
        elif request.user.role == 'teacher':
            return redirect('consultations:teacher_dashboard')
        else:
            return render(request, 'accounts/dashboard.html')