from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date

from users.models import User
from match.models import Match  # <-- import Match from your match app
from .models import ChatRoom, Message,RevealRequest  # <-- import Message as well
from django.db import models
from django.db.models import Q
from django.views.decorators.http import require_POST


# Create your views here.


@login_required
def chatroom(request, match_id):
    match = get_object_or_404(Match, id=match_id, is_active=True)

    if request.user not in (match.user_a, match.user_b):
        return HttpResponseForbidden()

    chatroom, _ = ChatRoom.objects.get_or_create(match=match)
    other_user = match.user_b if request.user == match.user_a else match.user_a

    # Mark messages as read
    Message.objects.filter(
        chat=chatroom,
        sender=other_user,
        is_read=False
    ).update(is_read=True)

    reveal_request = RevealRequest.objects.filter(
        match=match,
        requester=other_user
    ).exists()

    reveal_requested = RevealRequest.objects.filter(
        match=match,
        requester=request.user
    ).exists()

    # Add today and yesterday for date separators
    from datetime import date, timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)

    return render(request, 'chat/chatroom.html', {
        'chatroom': chatroom,
        'match': match,
        'other_user': other_user,
        'reveal_request': reveal_request,
        'reveal_requested': reveal_requested,
        'today': today,
        'yesterday': yesterday,
    })


@login_required
def fetch_messages(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)

    if request.user not in (chat.match.user_a, chat.match.user_b):
        return HttpResponseForbidden()

    other_user = chat.match.user_b if request.user == chat.match.user_a else chat.match.user_a

    # ✅ Mark new messages from the other user as read
    Message.objects.filter(
        chat=chat,
        sender=other_user,
        is_read=False
    ).update(is_read=True)

    # Add today and yesterday for date separators
    from datetime import date, timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)

    msgs = chat.messages.select_related('sender')
    html = render(request, 'chat/_messages.html', {
        'messages': msgs,
        'user': request.user,
        'today': today,
        'yesterday': yesterday
    }).content.decode()

    return JsonResponse({
        'html': html,
        'messages_count': msgs.count(),
    })



@login_required
def send_message(request, chat_id):
    if request.method == 'POST':
        chat = get_object_or_404(ChatRoom, id=chat_id)
        if request.user not in (chat.match.user_a, chat.match.user_b):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(
                chat=chat,
                sender=request.user,
                text=text,
                is_read=False  # ← New message = unread for receiver
            )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid'}, status=400)


@login_required
def chat_list(request):
    matches = Match.objects.filter(
        is_active=True
    ).filter(
        models.Q(user_a=request.user) | models.Q(user_b=request.user)
    ).select_related('user_a', 'user_b')

    chatrooms = []
    for m in matches:
        room, _ = ChatRoom.objects.get_or_create(match=m)
        other_user = m.user_b if m.user_a == request.user else m.user_a
        last_msg = Message.objects.filter(chat=room).order_by('-timestamp').first()

        # Unread count (simple)
        unread = Message.objects.filter(
            chat=room,
            sender=other_user,
            is_read=False  # ← Only unread
        ).count()

        chatrooms.append({
            "room": room,
            "other": other_user,
            "last_msg": last_msg,
            "unread": unread,
            "can_see_photo": m.is_friend
        })

    return render(request, 'chat/chat_list.html', {
        'chatrooms': chatrooms
    })


@login_required
@require_POST
def delete_message(request, message_id):
    msg = get_object_or_404(Message, id=message_id)
    if msg.sender != request.user:
        return JsonResponse({'error': 'Not your message'}, status=403)

    msg.is_deleted = True
    msg.save(update_fields=['is_deleted'])
    return JsonResponse({'success': True})



@login_required
def request_reveal(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.user not in (match.user_a, match.user_b):
        return HttpResponseForbidden()

    if match.is_friend:
        return JsonResponse({'already': True})

    # Create request
    RevealRequest.objects.get_or_create(match=match, requester=request.user)
    return JsonResponse({'requested': True})


@login_required
def accept_reveal(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    if request.user not in (match.user_a, match.user_b):
        return HttpResponseForbidden()

    other_user = match.user_b if request.user == match.user_a else match.user_a

    # Accept: mark friend + delete request
    if not match.is_friend:
        match.is_friend = True
        match.save(update_fields=['is_friend'])

    RevealRequest.objects.filter(match=match, requester=other_user).delete()
    return JsonResponse({'accepted': True, 'unblurred': True})


@login_required
def unread_count_api(request):
    total_unread = 0
    matches = Match.objects.filter(is_active=True).filter(
        Q(user_a=request.user) | Q(user_b=request.user)
    )
    for m in matches:
        room = ChatRoom.objects.filter(match=m).first()
        if room:
            other = m.user_b if m.user_a == request.user else m.user_a
            unread = Message.objects.filter(chat=room, sender=other, is_read=False).count()
            total_unread += unread

    return JsonResponse({"unread_count": total_unread})