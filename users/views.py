from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import UserRegisterForm, UserProfileForm,UserLoginForm
from .models import User,Interest
from django.contrib.auth.decorators import login_required
import json
from django.http import JsonResponse
from django.utils import timezone

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile_view(request):
    completion = request.user.profile_completion()
    can_access_match = completion >= 80
    return render(request, 'users/profile.html', {
        'completion': completion,
        'can_access_match': can_access_match,
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            interest_ids = request.POST.getlist('interests')
            user.interests.set(interest_ids)
            messages.success(request, "Profile updated!")
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)

    interests_data = list(Interest.objects.values_list('id', 'name'))
    selected_ids = list(request.user.interests.values_list('id', flat=True))

    return render(request, 'users/edit_profile.html', {
        'form': form,
        'interests_data': json.dumps(interests_data),
        'selected_ids': json.dumps(selected_ids),
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('users:profile')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserLoginForm()

    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You’ve been logged out successfully.")
    return redirect('home')


@login_required
def update_last_seen(request):
    request.user.last_seen = timezone.now()
    request.user.save(update_fields=['last_seen'])
    return JsonResponse({'status': 'updated'})