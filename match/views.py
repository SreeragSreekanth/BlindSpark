# matches/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date

from users.models import User
from .models import Match, DiscoveryLog, Like
from .utils import calculate_match_score, haversine_km
from chat.models import ChatRoom



@login_required
def discover_matches(request):
    user = request.user

    # Require 80% profile completion
    if user.profile_completion() < 80:
        messages.warning(request, "Complete 80% of your profile to access discovery.")
        return redirect('users:edit')

    # Only users 18+
    eighteen_years_ago = date.today().replace(year=date.today().year - 18)
    potential = User.objects.exclude(id=user.id).filter(
        dob__isnull=False,
        dob__lte=eighteen_years_ago,
    )

    # Filter by opposite gender if set
    if user.gender in ('M', 'F'):
        potential = potential.filter(gender=('F' if user.gender == 'M' else 'M'))

    # Exclude users already viewed
    viewed_ids = DiscoveryLog.objects.filter(viewer=user).values_list('viewed_user_id', flat=True)
    potential = potential.exclude(id__in=viewed_ids).prefetch_related('interests')

    # Stable ordering by id for consistent pagination
    potential = potential.order_by('id')

    # Precompute user interests & location
    user_interests = set(user.interests.values_list('id', flat=True))
    user_lat, user_lon = user.latitude, user.longitude

    results = []
    for p in potential:
        # Interest score (0-70)
        shared = len(user_interests & set(p.interests.values_list('id', flat=True)))
        interest_score = (shared / max(len(user_interests), 1)) * 70

        # Location score (0-30)
        distance = None
        loc_score = 15.0
        if user_lat and user_lon and p.latitude and p.longitude:
            distance = round(haversine_km(user_lat, user_lon, p.latitude, p.longitude), 1)
            loc_score = max(0, 30 - distance * 0.3)
            print(f"Distance to {p.username}: {distance} km, loc_score: {loc_score}")

        total_score = interest_score + loc_score
        if total_score >= 10:  # only include relevant matches
            results.append({
                'user': p,
                'score': round(total_score, 2),
                'distance': distance
            })

    # Sort by score DESC, then id ASC to avoid duplicates across pages
    results.sort(key=lambda x: (-x['score'], x['user'].id))


    # Pagination
    paginator = Paginator(results, 9)  # 9 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # AJAX infinite scroll
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cards_html = render(request, 'matches/_cards.html', {'page_obj': page_obj}).content.decode()
        return JsonResponse({'html': cards_html, 'has_next': page_obj.has_next()})

    return render(request, 'matches/discover.html', {'page_obj': page_obj,'has_next': page_obj.has_next()})


@login_required
def view_profile(request, user_id):
    target = get_object_or_404(User, id=user_id)

    # 18+ CHECK
    if not target.dob or target.age < 18:
        raise Http404("User must be 18+")

    if target.id == request.user.id:
        return redirect('users:profile')

    # LOG ONLY WHEN USER ACTUALLY OPENS PROFILE
    DiscoveryLog.objects.get_or_create(viewer=request.user, viewed_user=target)

    score = calculate_match_score(request.user, target)
    a, b = sorted([request.user.id, target.id])
    match = Match.objects.filter(user_a_id=a, user_b_id=b).first()

    is_liked_by_me = Like.objects.filter(from_user=request.user, to_user=target).exists()
    is_liked_by_them = Like.objects.filter(from_user=target, to_user=request.user).exists()

    return render(request, 'matches/view_profile.html', {
        'target': target,
        'score': score,
        'match': match,
        'is_liked_by_me': is_liked_by_me,
        'is_liked_by_them': is_liked_by_them,
    })


@login_required
def like_user(request, user_id):
    target = get_object_or_404(User, id=user_id)

    if not target.dob or target.age < 18:
        return JsonResponse({'error': 'User must be 18+'}, status=400)

    if target.id == request.user.id:
        return JsonResponse({'error': 'Cannot like yourself'}, status=400)

    with transaction.atomic():
        like, created = Like.objects.select_for_update().get_or_create(
            from_user=request.user, to_user=target
        )

        reverse_like = Like.objects.select_for_update().filter(
            from_user=target, to_user=request.user
        ).first()

        if reverse_like:
            a_id, b_id = sorted([request.user.id, target.id])
            match_obj, _ = Match.objects.get_or_create(
                user_a_id=a_id, user_b_id=b_id,
                defaults={'compatibility_score': calculate_match_score(request.user, target)}
            )
            match_obj.is_active = True
            match_obj.save()
            ChatRoom.objects.get_or_create(match=match_obj)


            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'mutual': True, 'message': f"Mutual like with {target.username}!"})
            messages.success(request, f"Mutual like with {target.username}! Chat unlocked")
            return redirect('matches:view_profile', user_id=target.id)

        if created:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'liked': True, 'message': 'Liked!'})
            messages.info(request, f"You liked {target.username}")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'already_liked': True})
            messages.warning(request, "Already liked")

    return redirect('matches:discover') if not request.headers.get('x-requested-with') else JsonResponse({'success': True})


