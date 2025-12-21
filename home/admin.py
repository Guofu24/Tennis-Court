from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserActivity, PageView, DailyStats, VisitorSession

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'dob', 'gender', 'address', 'photo')}),
        ('Roles and Permissions', {'fields': ('role', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'description', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'activity_type', 'description', 'ip_address', 'user_agent', 'page_url', 'referrer', 'created_at', 'extra_data')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('page_name', 'page_url', 'view_count', 'last_viewed')
    list_filter = ('last_viewed',)
    search_fields = ('page_url', 'page_name')
    ordering = ('-view_count',)
    readonly_fields = ('page_url', 'page_name', 'view_count', 'unique_visitors', 'last_viewed', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_visits', 'unique_visitors', 'new_registrations', 'total_bookings', 'total_revenue')
    list_filter = ('date',)
    ordering = ('-date',)
    readonly_fields = ('date', 'total_visits', 'unique_visitors', 'new_registrations', 'total_bookings', 'total_revenue')


@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key_short', 'user', 'device_type', 'browser', 'os', 'page_views', 'started_at', 'last_activity')
    list_filter = ('device_type', 'browser', 'os', 'started_at')
    search_fields = ('session_key', 'user__username', 'ip_address')
    ordering = ('-last_activity',)
    readonly_fields = ('session_key', 'user', 'ip_address', 'user_agent', 'device_type', 'browser', 'os', 'country', 'city', 'started_at', 'last_activity', 'page_views')
    
    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..."
    session_key_short.short_description = 'Session Key'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Đăng ký vào admin
admin.site.register(CustomUser, CustomUserAdmin)
