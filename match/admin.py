from django.contrib import admin
from .models import Match, DiscoveryLog

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('user_a', 'user_b', 'compatibility_score', 'matched_on', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user_a__username', 'user_b__username')


@admin.register(DiscoveryLog)
class DiscoveryLogAdmin(admin.ModelAdmin):
    list_display = ('viewer', 'viewed_user', 'viewed_on')
    search_fields = ('viewer__username', 'viewed_user__username')
