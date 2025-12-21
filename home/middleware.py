"""
Middleware để theo dõi hoạt động người dùng và lượt truy cập trang
"""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
import re


class ActivityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware để tự động theo dõi:
    - Lượt xem trang
    - Phiên truy cập
    - Hoạt động người dùng
    """
    
    # Các URL pattern không cần theo dõi
    EXCLUDED_PATHS = [
        r'^/static/',
        r'^/media/',
        r'^/admin/jsi18n/',
        r'^/favicon\.ico$',
        r'\.css$',
        r'\.js$',
        r'\.png$',
        r'\.jpg$',
        r'\.jpeg$',
        r'\.gif$',
        r'\.ico$',
        r'\.woff',
        r'\.ttf',
        r'\.svg$',
    ]
    
    # Mapping URL patterns to page names
    PAGE_NAMES = {
        r'^/$': 'Trang chủ',
        r'^/home/?$': 'Trang chủ',
        r'^/about/?$': 'Giới thiệu',
        r'^/contact/?$': 'Liên hệ',
        r'^/auth/?$': 'Đăng nhập/Đăng ký User',
        r'^/auth_admin/?$': 'Đăng nhập/Đăng ký Admin',
        r'^/hire/?$': 'Danh sách sân tennis',
        r'^/detail/\d+/?$': 'Chi tiết sân',
        r'^/checkout/\d+/?$': 'Thanh toán',
        r'^/booking-success/?$': 'Đặt sân thành công',
        r'^/my-bookings/?$': 'Đặt chỗ của tôi',
        r'^/all-bookings/?$': 'Tất cả đặt chỗ',
        r'^/top-up/?$': 'Nạp tiền',
        r'^/transaction-history/?$': 'Lịch sử giao dịch',
        r'^/user-profile/?$': 'Hồ sơ người dùng',
        r'^/review/\d+/?$': 'Đánh giá sân',
        r'^/report/\d+/?$': 'Báo cáo sân',
        r'^/add-tennis/?$': 'Thêm sân mới',
        r'^/manage-users/?$': 'Quản lý người dùng',
        r'^/admin-reports/?$': 'Báo cáo admin',
        r'^/analytics/?$': 'Thống kê hoạt động',
    }
    
    def should_track(self, path):
        """Kiểm tra xem path có cần được theo dõi không"""
        for pattern in self.EXCLUDED_PATHS:
            if re.search(pattern, path, re.IGNORECASE):
                return False
        return True
    
    def get_page_name(self, path):
        """Lấy tên trang từ URL"""
        for pattern, name in self.PAGE_NAMES.items():
            if re.match(pattern, path, re.IGNORECASE):
                return name
        return path
    
    def get_client_ip(self, request):
        """Lấy địa chỉ IP của client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_device_info(self, user_agent):
        """Phân tích thông tin thiết bị từ User-Agent"""
        user_agent_lower = user_agent.lower() if user_agent else ''
        
        # Detect device type
        if 'mobile' in user_agent_lower or 'android' in user_agent_lower:
            if 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
                device_type = 'tablet'
            else:
                device_type = 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            device_type = 'tablet'
        else:
            device_type = 'desktop'
        
        # Detect browser
        if 'chrome' in user_agent_lower and 'edg' not in user_agent_lower:
            browser = 'Chrome'
        elif 'firefox' in user_agent_lower:
            browser = 'Firefox'
        elif 'safari' in user_agent_lower and 'chrome' not in user_agent_lower:
            browser = 'Safari'
        elif 'edg' in user_agent_lower:
            browser = 'Edge'
        elif 'opera' in user_agent_lower or 'opr' in user_agent_lower:
            browser = 'Opera'
        else:
            browser = 'Other'
        
        # Detect OS
        if 'windows' in user_agent_lower:
            os_name = 'Windows'
        elif 'mac os' in user_agent_lower or 'macintosh' in user_agent_lower:
            os_name = 'macOS'
        elif 'linux' in user_agent_lower:
            os_name = 'Linux'
        elif 'android' in user_agent_lower:
            os_name = 'Android'
        elif 'iphone' in user_agent_lower or 'ipad' in user_agent_lower:
            os_name = 'iOS'
        else:
            os_name = 'Other'
        
        return device_type, browser, os_name
    
    def process_request(self, request):
        """Xử lý request và ghi lại hoạt động"""
        path = request.path
        
        # Bỏ qua các static files và assets
        if not self.should_track(path):
            return None
        
        # Import models ở đây để tránh circular import
        from .models import PageView, UserActivity, VisitorSession
        
        try:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            referrer = request.META.get('HTTP_REFERER', '')
            
            # Lấy hoặc tạo session key
            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            
            # Ghi lại lượt xem trang
            page_name = self.get_page_name(path)
            PageView.record_view(path, page_name)
            
            # Cập nhật hoặc tạo visitor session
            device_type, browser, os_name = self.get_device_info(user_agent)
            
            session, created = VisitorSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'device_type': device_type,
                    'browser': browser,
                    'os': os_name,
                }
            )
            
            # Cập nhật user nếu đã đăng nhập
            if request.user.is_authenticated:
                session.user = request.user
            
            session.page_views += 1
            session.last_activity = timezone.now()
            session.save()
            
            # Ghi lại hoạt động xem trang (chỉ cho các trang quan trọng)
            important_pages = ['/', '/home', '/hire', '/about', '/contact']
            if path in important_pages or path.startswith('/detail/'):
                user = request.user if request.user.is_authenticated else None
                UserActivity.objects.create(
                    user=user,
                    activity_type='page_view',
                    description=f'Xem trang: {page_name}',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    page_url=request.build_absolute_uri(),
                    referrer=referrer if referrer else None,
                    extra_data={
                        'path': path,
                        'page_name': page_name,
                        'device_type': device_type,
                        'browser': browser,
                        'os': os_name,
                    }
                )
        except Exception as e:
            # Log lỗi nhưng không làm gián đoạn request
            print(f"Activity tracking error: {e}")
        
        return None


class OnlineUsersMiddleware(MiddlewareMixin):
    """
    Middleware để theo dõi số người dùng đang online
    """
    
    def process_request(self, request):
        from django.core.cache import cache
        from .models import CustomUser
        
        # Thời gian timeout (5 phút)
        ONLINE_TIMEOUT = 300
        
        if request.user.is_authenticated:
            # Lưu user vào cache với timestamp
            cache_key = f'online_user_{request.user.userID}'
            cache.set(cache_key, timezone.now(), ONLINE_TIMEOUT)
            
            # Cập nhật last_login
            if hasattr(request.user, 'last_login'):
                request.user.last_login = timezone.now()
                request.user.save(update_fields=['last_login'])
        
        return None
