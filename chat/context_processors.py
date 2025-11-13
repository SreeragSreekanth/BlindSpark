# context_processors.py (create if not exists)
from chat.models import ChatRoom, Message
from django.db.models import Q
from match.models import Match

def unread_count(request):
    if not request.user.is_authenticated:
        return {}

    total_unread = 0
    matches = Match.objects.filter(
        is_active=True
    ).filter(
        Q(user_a=request.user) | Q(user_b=request.user)
    )

    for m in matches:
        room = ChatRoom.objects.filter(match=m).first()
        if room:
            other = m.user_b if m.user_a == request.user else m.user_a
            unread = Message.objects.filter(
                chat=room,
                sender=other,
                is_read=False
            ).count()
            total_unread += unread

    return {'total_unread': total_unread}