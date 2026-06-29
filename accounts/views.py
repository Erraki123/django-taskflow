"""
Accounts app views: registration, login, logout, profile.
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from core.models import ActivityLog

from .forms import ProfileForm, RegistrationForm, StyledAuthenticationForm, UserUpdateForm


class StyledLoginView(LoginView):
    """
    Custom login view built on top of Django's class-based LoginView,
    using our own form (username-or-email + "remember me") and
    template, and logging the event to the activity feed.
    """
    template_name = 'accounts/login.html'
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        response = super().form_valid(form)
        if not remember_me:
            # Session expires when the browser closes.
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days

        ActivityLog.log(
            user=self.request.user,
            action=ActivityLog.ActionType.LOGGED_IN,
            description='Logged in to TaskFlow',
            icon='fa-right-to-bracket',
        )
        messages.success(self.request, f'Welcome back, {self.request.user.first_name or self.request.user.username}!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid credentials. Please check your username/email and password.')
        return super().form_invalid(form)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            ActivityLog.log(
                user=user,
                action=ActivityLog.ActionType.REGISTERED,
                description='Created a TaskFlow account',
                icon='fa-user-plus',
            )
            login(request, user)
            messages.success(request, f'Welcome to TaskFlow, {user.first_name or user.username}! Your account is ready.')
            return redirect('dashboard:home')
        messages.error(request, 'Please fix the errors below and try again.')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def logout_view(request):
    ActivityLog.log(
        user=request.user,
        action=ActivityLog.ActionType.LOGGED_OUT,
        description='Logged out of TaskFlow',
        icon='fa-right-from-bracket',
    )
    logout(request)
    messages.info(request, 'You have been logged out. See you soon!')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            ActivityLog.log(
                user=request.user,
                action=ActivityLog.ActionType.PROFILE_UPDATED,
                description='Updated profile information',
                icon='fa-id-card',
            )
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')
        messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    recent_activity = request.user.activity_logs.all()[:10]

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'recent_activity': recent_activity,
    }
    return render(request, 'accounts/profile.html', context)
