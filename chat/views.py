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
from .models import ChatRoom, Message  # <-- import Message as well
from django.db import models
from django.views.decorators.http import require_POST

# Create your views here.


@login_required
def chatroom(request, match_id):
    match = get_object_or_404(Match, id=match_id, is_active=True)
    if request.user not in (match.user_a, match.user_b):
        return HttpResponseForbidden()

    chatroom, _ = ChatRoom.objects.get_or_create(match=match)
    other_user = match.user_b if request.user == match.user_a else match.user_a

    # MARK ALL MESSAGES FROM OTHER USER AS READ
    Message.objects.filter(
        chat=chatroom,
        sender=other_user,
        is_read=False
    ).update(is_read=True)

    can_see_photo = match.is_friend

    return render(request, 'chat/chatroom.html', {
        'chatroom': chatroom,
        'match': match,
        'other_user': other_user,
        'can_see_photo': can_see_photo
    })


@login_required
def fetch_messages(request, chat_id):
    chat = get_object_or_404(ChatRoom, id=chat_id)

    if request.user not in (chat.match.user_a, chat.match.user_b):
        return HttpResponseForbidden()

    msgs = chat.messages.select_related('sender')
    html = render(request, 'chat/_messages.html', {'messages': msgs}).content.decode()
    return JsonResponse({'html': html})



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