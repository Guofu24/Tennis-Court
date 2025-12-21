"""
Utility functions để theo dõi và ghi lại hoạt động người dùng
"""
from django.utils import timezone
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncHour
from datetime import timedelta


def get_client_ip(request):
    """Lấy địa chỉ IP của client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(request, activity_type, description=None, extra_data=None):
    """
    Ghi lại hoạt động người dùng
    
    Args:
        request: HttpRequest object
        activity_type: Loại hoạt động (register, login, booking, etc.)
        description: Mô tả hoạt động
        extra_data: Dict chứa dữ liệu bổ sung
    """
    from .models import UserActivity
    
    try:
        user = request.user if request.user.is_authenticated else None
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        
        activity = UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            page_url=request.build_absolute_uri(),
            referrer=referrer if referrer else None,
            extra_data=extra_data or {}
        )
        return activity
    except Exception as e:
        print(f"Error logging activity: {e}")
        return None


def get_analytics_data(days=30):
    """
    Lấy dữ liệu thống kê hoạt động
    
    Args:
        days: Số ngày cần lấy dữ liệu
    
    Returns:
        Dict chứa các thống kê
    """
    from .models import UserActivity, PageView, VisitorSession, CustomUser, Booking, Invoice
    
    now = timezone.now()
    start_date = now - timedelta(days=days)
    
    # Thống kê hoạt động
    activities = UserActivity.objects.filter(created_at__gte=start_date)
    
    # Thống kê theo loại hoạt động
    activity_stats = activities.values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Thống kê theo ngày
    daily_stats = activities.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Thống kê theo giờ
    hourly_stats = activities.annotate(
        hour=TruncHour('created_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-hour')[:24]
    
    # Top pages
    top_pages = PageView.objects.all().order_by('-view_count')[:10]
    
    # Visitor sessions
    active_sessions = VisitorSession.objects.filter(
        last_activity__gte=now - timedelta(minutes=30)
    ).count()
    
    # Thống kê thiết bị
    device_stats = VisitorSession.objects.filter(
        started_at__gte=start_date
    ).values('device_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Thống kê trình duyệt
    browser_stats = VisitorSession.objects.filter(
        started_at__gte=start_date
    ).values('browser').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Thống kê người dùng mới
    new_users = CustomUser.objects.filter(
        date_joined__gte=start_date
    ).count()
    
    # Thống kê đặt sân
    bookings = Booking.objects.filter(
        id__gte=0  # Tất cả booking (nếu có field created_at thì dùng filter theo ngày)
    ).count()
    
    # Thống kê doanh thu
    total_revenue = Invoice.objects.filter(
        status='Paid',
        created_at__gte=start_date
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Tổng số lượt xem
    total_page_views = PageView.objects.aggregate(
        total=Sum('view_count')
    )['total'] or 0
    
    return {
        'activity_stats': list(activity_stats),
        'daily_stats': list(daily_stats),
        'hourly_stats': list(hourly_stats),
        'top_pages': top_pages,
        'active_sessions': active_sessions,
        'device_stats': list(device_stats),
        'browser_stats': list(browser_stats),
        'new_users': new_users,
        'total_bookings': bookings,
        'total_revenue': total_revenue,
        'total_page_views': total_page_views,
        'days': days,
    }


def get_recent_activities(limit=50):
    """Lấy các hoạt động gần đây"""
    from .models import UserActivity
    return UserActivity.objects.select_related('user').order_by('-created_at')[:limit]


def get_online_users_count():
    """Đếm số người dùng đang online"""
    from django.core.cache import cache
    from .models import CustomUser
    
    online_count = 0
    users = CustomUser.objects.all()
    
    for user in users:
        cache_key = f'online_user_{user.userID}'
        if cache.get(cache_key):
            online_count += 1
    
    return online_count


def get_user_activity_summary(user):
    """
    Lấy tóm tắt hoạt động của một người dùng cụ thể
    
    Args:
        user: CustomUser object
    
    Returns:
        Dict chứa thống kê hoạt động của user
    """
    from .models import UserActivity
    
    activities = UserActivity.objects.filter(user=user)
    
    return {
        'total_activities': activities.count(),
        'login_count': activities.filter(activity_type='login').count(),
        'booking_count': activities.filter(activity_type='booking').count(),
        'page_views': activities.filter(activity_type='page_view').count(),
        'last_activity': activities.first(),
        'activity_by_type': list(activities.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')),
    }


def update_daily_stats():
    """Cập nhật thống kê hàng ngày"""
    from .models import DailyStats, UserActivity, CustomUser, Booking, Invoice
    
    today = timezone.now().date()
    
    # Lấy hoặc tạo record cho ngày hôm nay
    stats, created = DailyStats.objects.get_or_create(date=today)
    
    # Cập nhật thống kê
    today_start = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.min.time())
    )
    today_end = timezone.make_aware(
        timezone.datetime.combine(today, timezone.datetime.max.time())
    )
    
    stats.total_visits = UserActivity.objects.filter(
        created_at__range=(today_start, today_end),
        activity_type='page_view'
    ).count()
    
    stats.unique_visitors = UserActivity.objects.filter(
        created_at__range=(today_start, today_end)
    ).values('ip_address').distinct().count()
    
    stats.new_registrations = CustomUser.objects.filter(
        date_joined__range=(today_start, today_end)
    ).count()
    
    stats.total_bookings = UserActivity.objects.filter(
        created_at__range=(today_start, today_end),
        activity_type='booking'
    ).count()
    
    stats.total_revenue = Invoice.objects.filter(
        status='Paid',
        created_at__range=(today_start, today_end)
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    stats.save()
    return stats
