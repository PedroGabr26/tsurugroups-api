"""
Views for core functionality.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    LoginView as DjangoLoginView,
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView
)
from django.contrib.auth import get_user_model
from apps.subscriptions.models import Plan
from django import forms

from apps.whatsapp.models import WhatsAppGroup, WhatsAppInstance

User = get_user_model()


class CustomUserCreationForm(forms.ModelForm):
    """Custom user creation form."""
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password']
    
    def clean_email(self):
        """Check if email already exists."""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está em uso.')
        return email


class HomeView(TemplateView):
    """Home page view."""
    template_name = 'home_simple.html'


class CustomLoginView(DjangoLoginView):
    """Custom login view."""
    template_name = 'auth/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Get success URL after login."""
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('dashboard')
    
    def form_invalid(self, form):
        """Handle invalid form submission."""
        messages.error(self.request, 'E-mail ou senha incorretos.')
        return super().form_invalid(form)


class CustomRegisterView(CreateView):
    """Custom registration view."""
    model = User
    form_class = CustomUserCreationForm
    template_name = 'auth/register.html'
    success_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        """Add extra context."""
        context = super().get_context_data(**kwargs)
        # Get selected plan from URL parameter
        plan_slug = self.request.GET.get('plan')
        if plan_slug:
            try:
                plan = Plan.objects.get(slug=plan_slug, is_active=True)
                context['selected_plan'] = plan
            except Plan.DoesNotExist:
                pass
        return context
    
    def form_valid(self, form):
        """Handle valid form submission."""
        # Set password properly
        print("AQUI")
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.username = user.email  # Use email as username
        user.save()
        
        messages.success(
            self.request, 
            'Conta criada com sucesso! Faça login para continuar.'
        )
        
        # If there's a selected plan, redirect to plans page after login
        selected_plan = self.request.GET.get('plan')
        if selected_plan:
            login_url = reverse_lazy('login')
            return redirect(f"{login_url}?next={reverse_lazy('plans')}")
        
        return super().form_valid(form)


class CustomPasswordResetView(DjangoPasswordResetView):
    """Custom password reset view."""
    template_name = 'auth/password_reset.html'
    email_template_name = 'auth/password_reset_email.html'
    subject_template_name = 'auth/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def form_valid(self, form):
        """Handle valid form submission."""
        messages.success(
            self.request,
            'Se o e-mail informado estiver cadastrado, você receberá instruções para redefinir sua senha.'
        )
        return super().form_valid(form)


class CustomPasswordResetConfirmView(DjangoPasswordResetConfirmView):
    """Custom password reset confirm view."""
    template_name = 'auth/password_reset_confirm.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        """Handle valid form submission."""
        messages.success(
            self.request,
            'Sua senha foi redefinida com sucesso! Faça login com sua nova senha.'
        )
        return super().form_valid(form)


@login_required
def dashboard_view(request):
    """Dashboard view."""
    context = {
        'user': request.user,
        'whatsapp_instances': WhatsAppInstance.objects.filter(user=request.user).count() if hasattr(request.user, 'whatsapp_instance') else 0,
        'groups_count': WhatsAppGroup.objects.filter(whatsapp_instance__user=request.user).count() if hasattr(request.user, 'whatsapp_instance') else 0,
    }
    
    # Add subscription info if user has one
    if hasattr(request.user, 'current_subscription') and request.user.current_subscription:
        context['subscription'] = request.user.current_subscription
    
    return render(request, 'dashboard.html', context)




@login_required
def logout_view(request):
    """Custom logout view."""
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('home')


# Password reset done view
class PasswordResetDoneView(TemplateView):
    """Password reset done view."""
    template_name = 'auth/password_reset_done.html'


# Password reset complete view  
class PasswordResetCompleteView(TemplateView):
    """Password reset complete view."""
    template_name = 'auth/password_reset_complete.html'