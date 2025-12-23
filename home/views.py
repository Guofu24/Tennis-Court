from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate,logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import *
from .models import *
from .activity_tracker import log_activity, get_analytics_data, get_recent_activities, get_online_users_count, get_user_activity_summary
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.timezone import now
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import SetPasswordForm
from django.core.paginator import Paginator
import os
from datetime import timedelta

def auth_user(request):
    register_form = UserRegistrationForm()
    show_register = False  # Flag to show register form on errors

    if request.method == 'POST':
        if 'register' in request.POST:
            register_form = UserRegistrationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()  
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')  
                # Ghi lại hoạt động đăng ký
                log_activity(request, 'register', f'User mới đăng ký: {user.username}', {
                    'user_id': user.userID,
                    'email': user.email
                })
                messages.success(request, 'Tạo tài khoản thành công!')
                return redirect('home')
            else:
                show_register = True  # Keep register form open on validation errors 

        elif 'login' in request.POST:
                if request.method == 'POST':
                    username = request.POST.get('userName', '').strip()
                    password = request.POST.get('userPass', '')
                    
                    # Validate input
                    if not username:
                        messages.error(request, 'Vui lòng nhập tên đăng nhập.')
                        return render(request, "apps/login_user.html", {'register_form': register_form})
                    
                    if not password:
                        messages.error(request, 'Vui lòng nhập mật khẩu.')
                        return render(request, "apps/login_user.html", {'register_form': register_form})
                    
                    if len(username) < 3:
                        messages.error(request, 'Tên đăng nhập phải có ít nhất 3 ký tự.')
                        return render(request, "apps/login_user.html", {'register_form': register_form})
                    
                    user = authenticate(request, username=username, password=password)
                    
                    if user is not None:
                        if user.is_user():
                            login(request, user)
                            # Ghi lại hoạt động đăng nhập
                            log_activity(request, 'login', f'User {username} đã đăng nhập')
                            return redirect('home')
                        else:
                            messages.error(request, 'Tài khoản này không có quyền user.')
                    else: 
                        messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')

    return render(request, "apps/login_user.html", {'register_form': register_form, 'show_register': show_register})

def auth_admin(request):
    register_form_admin = AdminRegistrationForm()
    show_register = False  # Flag to show register form on errors

    if request.method == 'POST':
        if 'register' in request.POST:
            register_form_admin = AdminRegistrationForm(request.POST)
            if register_form_admin.is_valid():
                user = register_form_admin.save()  
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')  
                messages.success(request, 'Tạo tài khoản thành công!')
                return redirect('home')
            else:
                show_register = True  # Keep register form open on validation errors

        elif 'login' in request.POST:
            if request.method == 'POST':
                username = request.POST.get('adminName', '').strip()
                password = request.POST.get('adminPass', '')
                
                # Validate input
                if not username:
                    messages.error(request, 'Vui lòng nhập tên đăng nhập.')
                    return render(request, "apps/login_admin.html", {'register_form_admin': register_form_admin, 'show_register': show_register})
                
                if not password:
                    messages.error(request, 'Vui lòng nhập mật khẩu.')
                    return render(request, "apps/login_admin.html", {'register_form_admin': register_form_admin, 'show_register': show_register})
                
                if len(username) < 3:
                    messages.error(request, 'Tên đăng nhập phải có ít nhất 3 ký tự.')
                    return render(request, "apps/login_admin.html", {'register_form_admin': register_form_admin, 'show_register': show_register})
                
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    if user.is_admin():
                        login(request, user)
                        return redirect('home')
                    else:
                        messages.error(request, 'Tài khoản này không có quyền admin.')
                else: 
                    messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng!')

    return render(request, "apps/login_admin.html", {'register_form_admin': register_form_admin, 'show_register': show_register})

def logoutPage(request):
    if request.user.is_authenticated:
        log_activity(request, 'logout', f'User {request.user.username} đã đăng xuất')
    logout(request)
    return redirect('home')

def request_password_reset(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = CustomUser.objects.get(username=username)
                # Tạo yêu cầu nếu chưa tồn tại
                reset_request, created = PasswordResetRequest.objects.get_or_create(user=user)
                if not created:
                    messages.warning(request, "You have already requested a password reset.")
                else:
                    messages.success(request, "Your request has been sent to admin.")
            except CustomUser.DoesNotExist:
                messages.error(request, "Username does not exist.")
    else:
        form = PasswordResetRequestForm()
    return render(request, 'apps/request_password_reset.html', {'form': form})

@login_required
def admin_view_password_reset_requests(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized.")

    requests = PasswordResetRequest.objects.filter(is_approved=False)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        reset_request = get_object_or_404(PasswordResetRequest, user_id=user_id)
        reset_request.is_approved = True
        reset_request.save()
        messages.success(request, f"Password reset approved for {reset_request.user.username}.")
        return JsonResponse({'status': 'approved'})

    return render(request, 'apps/admin_password_reset_requests.html', {'requests': requests})

def set_new_password(request, username):
    user = get_object_or_404(CustomUser, username=username)
    reset_request = get_object_or_404(PasswordResetRequest, user=user, is_approved=True)

    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            reset_request.delete() 
            messages.success(request, "Your password has been updated.")
            return redirect('auth_user')
    else:
        form = SetPasswordForm(user)

    return render(request, 'apps/set_new_password.html', {'form': form})

def check_password_reset_status(request):
    if request.user.is_authenticated:
        reset_request = PasswordResetRequest.objects.filter(user=request.user).first()
        if reset_request and reset_request.is_approved:
            return JsonResponse({'is_approved': True, 'username': request.user.username})
    return JsonResponse({'is_approved': False})

@login_required
def add_tennis(request):
    if not request.user.is_admin():
        messages.error(request, 'Bạn không có quyền truy cập vào trang này.')
        return HttpResponseForbidden("Bạn không có quyền truy cập vào trang này.")

    # Check if AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        try:
            # Check if image is provided
            has_image = 'image' in request.FILES and request.FILES['image']
            
            # Debug: Log file info
            print("=" * 50)
            print("ADD TENNIS - DEBUG INFO")
            print(f"FILES: {request.FILES}")
            print(f"is_ajax: {is_ajax}")
            if has_image:
                img = request.FILES['image']
                print(f"Image name: {img.name}")
                print(f"Image size: {img.size}")
                print(f"Image content_type: {img.content_type}")
            else:
                print("Note: No image uploaded")
            print("=" * 50)
            
            form = TennisForm(request.POST, request.FILES)
            if form.is_valid():
                court = form.save()
                if is_ajax:
                    return JsonResponse({'success': True, 'redirect': '/hire/'})
                messages.success(request, f'Sân tennis "{court.name}" đã được thêm thành công!')
                return redirect('property_list')
            else:
                # Collect validation errors
                errors = []
                print(f"Form errors: {form.errors}")
                
                # Field label mapping for better error messages
                field_labels = {
                    'name': 'Court Name',
                    'price': 'Price',
                    'court_address': 'Court Address',
                    'squared': 'Area',
                    'limit': 'Player Limit',
                    'brief': 'Description',
                    'hours': 'Playing Hours',
                    'image': 'Court Image',
                    'playTime': 'Play Time',
                    'dateTime': 'Available Date',
                }
                
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        error_str = str(error)  # Ensure it's a string
                        if field == '__all__':
                            errors.append(error_str)
                        else:
                            # Get label from mapping or form fields or use field name
                            field_label = field_labels.get(field)
                            if not field_label and field in form.fields and hasattr(form.fields[field], 'label'):
                                field_label = form.fields[field].label
                            if not field_label:
                                field_label = field.replace('_', ' ').title()
                            errors.append(f'{field_label}: {error_str}')
                
                print(f"Collected errors: {errors}")  # Debug
                
                if is_ajax:
                    return JsonResponse({'success': False, 'errors': errors})
                
                for error in errors:
                    messages.error(request, error)
        except Exception as e:
            print(f"Exception in add_tennis: {e}")
            if is_ajax:
                return JsonResponse({'success': False, 'errors': [str(e)]})
            messages.error(request, str(e))
    else:
        form = TennisForm()
    return render(request, 'apps/add_tennis.html', {'form': form})

@login_required
def edit_court(request, court_id):
    court = get_object_or_404(Tennis, id=court_id)

    if not request.user.is_admin:
        return redirect('property_list')  

    if request.method == 'POST':
        today = timezone.now().date()
        court.name = request.POST['name']
        court.price = request.POST['price']
        court.court_address = request.POST['court_address']
        court.limit = request.POST['limit']
        court.squared = request.POST['squared']
        court.hours = int(request.POST.get("hours"))
        court.dateTime = request.POST['dateTime']
        court.playTime = ', '.join(court.generate_play_times())  
        if court.dateTime < str(today):
            messages.error(request, 'The date must be today or in the future.')
            return render(request, 'apps/detail.html', {'court': court, 'today': today})
        
        if request.FILES.get('image'):
            court.image = request.FILES['image']
        court.save()
        
        return redirect('property_list')

    return redirect('property_list')

@login_required
def delete_court(request, court_id):
    court = get_object_or_404(Tennis, id=court_id)
    if not request.user.is_admin:
        return redirect('property_list')  
    court.delete()
    return redirect('property_list')

def home(request):
    tennis = Tennis.objects.all()
    top_court = Tennis.objects.annotate(vote_count=Count('reviews')).order_by('-vote_count').first()
    return render(request, "apps/index.html", {'tennis_courts': tennis, 'top_court': top_court})

def about(request):
    top_court = Tennis.objects.annotate(vote_count=Count('reviews')).order_by('-vote_count').first()
    
    return render(request, "apps/about.html", {'top_court': top_court})

def property_list(request):
    tennis_courts = Tennis.objects.all()
    for court in tennis_courts:
        court.playTime_list = court.playTime.split(', ') if court.playTime else []
    
    return render(request, 'apps/property-list.html', {'tennis_courts': tennis_courts})


def search_courts(request):
    """Tìm kiếm sân tennis theo tên, giá và địa chỉ"""
    tennis_courts = Tennis.objects.all()
    
    # Lấy các tham số tìm kiếm
    name = request.GET.get('name', '').strip()
    price = request.GET.get('price', '').strip()
    address = request.GET.get('address', '').strip()
    
    # Kiểm tra nếu không có tham số nào được nhập
    if not name and not price and not address:
        messages.info(request, 'Vui lòng nhập ít nhất một tiêu chí tìm kiếm.')
        return redirect('property_list')
    
    # Lọc theo tên (tìm kiếm không phân biệt hoa thường)
    if name:
        tennis_courts = tennis_courts.filter(name__icontains=name)
    
    # Lọc theo giá
    if price:
        if price == '0-500':
            tennis_courts = tennis_courts.filter(price__lt=500)
        elif price == '500-2000':
            tennis_courts = tennis_courts.filter(price__gte=500, price__lt=2000)
        elif price == '2000-5000':
            tennis_courts = tennis_courts.filter(price__gte=2000, price__lt=5000)
        elif price == '5000+':
            tennis_courts = tennis_courts.filter(price__gte=5000)
    
    # Lọc theo địa chỉ
    if address:
        tennis_courts = tennis_courts.filter(court_address__icontains=address)
    
    # Thêm playTime_list cho mỗi sân
    for court in tennis_courts:
        court.playTime_list = court.playTime.split(', ') if court.playTime else []
    
    # Tạo thông báo kết quả
    if tennis_courts.exists():
        messages.success(request, f'Tìm thấy {tennis_courts.count()} sân tennis phù hợp.')
    else:
        messages.warning(request, 'Không tìm thấy sân tennis nào phù hợp với tiêu chí tìm kiếm.')
    
    return render(request, 'apps/property-list.html', {
        'tennis_courts': tennis_courts,
        'search_name': name,
        'search_price': price,
        'search_address': address,
    })


def detail(request):
    if not request.user.is_authenticated:  
        messages.error(request, "Redirect to login page.")
        return redirect('auth_user') 
    court_id = request.GET.get('id', '')  
    court = get_object_or_404(Tennis, id=court_id)  
    
    if court.playTime:
        court.playTime_list = court.playTime.split(', ')
    else:
        court.playTime_list = []

    is_admin = request.user.is_authenticated and request.user.is_admin()

    return render(request, "apps/detail.html", {
        'tennis_courts': [court],  
        'is_admin': is_admin,  
    })

@login_required
def rent_court(request, court_id):
    court = get_object_or_404(Tennis, id=court_id)

    if court.status == 'Repairing':
        messages.error(request, "This court is under repair and cannot be booked at the moment.")
        return redirect('property_list')

    booked_times = Booking.objects.filter(tennis_court=court).values_list('play_time', flat=True)

    if request.method == 'POST':
        play_time = request.POST.get('play_time')

        if play_time:
            if play_time in booked_times:
                messages.error(request, "The selected play time is already booked. Please choose another time.")
                return redirect(f'/detail/?id={court.id}')
            request.session['temp_booking'] = {
                'court_id': court.id,
                'play_time': play_time,
            }
            return redirect('checkout')

    return render(request, 'apps/detail.html', {
        'court': court,
        'booked_times': booked_times
    })

@login_required
def checkout(request):
    temp_booking = request.session.get('temp_booking')
    if not temp_booking:
        messages.error(request, "Invalid booking request. Please try again.")
        return redirect('property_list')

    court = get_object_or_404(Tennis, id=temp_booking['court_id'])
    play_time = temp_booking['play_time']
    court_price = court.price
    user_balance = request.user.balance
    
    # Nếu sân FREE, bỏ qua bước thanh toán và tạo booking trực tiếp
    if court_price == 0:
        booking = Booking.objects.create(
            tennis_court=court,
            user=request.user,
            play_time=play_time
        )

        invoice = Invoice.objects.create(
            user=request.user,
            booking=booking,
            amount=0,
            status='Paid',
            payment_method='free',
            card_last_four=None,
            transaction_id=None
        )
        
        # Ghi lại hoạt động đặt sân miễn phí
        log_activity(request, 'booking', f'Đặt sân miễn phí {court.name} lúc {play_time}', {
            'court_id': court.id,
            'court_name': court.name,
            'play_time': play_time,
            'amount': 0
        })
        
        del request.session['temp_booking']
        messages.success(request, f"Successfully booked {court.name} for FREE!")
        return redirect('booking_success')
    
    # Các phương thức thanh toán có sẵn
    payment_methods = [
        {'id': 'balance', 'name': 'Account Balance', 'icon': 'fa-wallet', 'description': f'Current balance: ${user_balance:.2f}'},
        {'id': 'credit_card', 'name': 'Credit Card', 'icon': 'fa-credit-card', 'description': 'Visa, Mastercard, JCB'},
        {'id': 'momo', 'name': 'Momo Wallet', 'icon': 'fa-mobile-alt', 'description': 'Pay with Momo e-wallet'},
        {'id': 'bank_transfer', 'name': 'Bank Transfer', 'icon': 'fa-university', 'description': 'Direct bank transfer'},
        {'id': 'vnpay', 'name': 'VNPay', 'icon': 'fa-qrcode', 'description': 'Pay with VNPay QR'},
        {'id': 'zalopay', 'name': 'ZaloPay', 'icon': 'fa-money-bill-wave', 'description': 'Pay with ZaloPay'},
    ]

    if request.method == 'POST':
        if 'cancel' in request.POST:
            del request.session['temp_booking']
            messages.warning(request, "Booking cancelled.")
            return redirect(f'/detail/?id={court.id}')
        elif 'pay' in request.POST:
            payment_method = request.POST.get('payment_method', 'balance')
            card_number = request.POST.get('card_number', '')
            card_last_four = card_number[-4:] if len(card_number) >= 4 else None
            
            # Xử lý thanh toán theo từng phương thức
            payment_success = False
            transaction_id = None
            
            if payment_method == 'balance':
                # Thanh toán bằng số dư tài khoản
                if user_balance >= court_price:
                    request.user.balance -= court_price
                    request.user.save()
                    payment_success = True
                else:
                    messages.error(request, "Insufficient balance. Please top up your account or choose another payment method.")
                    return redirect('checkout')
            
            elif payment_method == 'credit_card':
                # Mô phỏng thanh toán thẻ tín dụng
                card_number = request.POST.get('card_number', '').replace(' ', '')
                card_expiry = request.POST.get('card_expiry', '')
                card_cvv = request.POST.get('card_cvv', '')
                
                if not card_number or len(card_number) < 13:
                    messages.error(request, "Invalid card number.")
                    return redirect('checkout')
                if not card_expiry:
                    messages.error(request, "Please enter card expiry date.")
                    return redirect('checkout')
                if not card_cvv or len(card_cvv) < 3:
                    messages.error(request, "Invalid CVV.")
                    return redirect('checkout')
                
                # Giả lập xử lý thanh toán thẻ (trong thực tế sẽ gọi API gateway)
                import uuid
                transaction_id = f"CC-{uuid.uuid4().hex[:12].upper()}"
                card_last_four = card_number[-4:]
                payment_success = True
            
            elif payment_method == 'momo':
                # Mô phỏng thanh toán Momo
                import uuid
                transaction_id = f"MOMO-{uuid.uuid4().hex[:12].upper()}"
                payment_success = True
            
            elif payment_method == 'bank_transfer':
                # Mô phỏng chuyển khoản ngân hàng
                import uuid
                transaction_id = f"BANK-{uuid.uuid4().hex[:12].upper()}"
                payment_success = True
                
            elif payment_method == 'vnpay':
                # Mô phỏng thanh toán VNPay
                import uuid
                transaction_id = f"VNPAY-{uuid.uuid4().hex[:12].upper()}"
                payment_success = True
                
            elif payment_method == 'zalopay':
                # Mô phỏng thanh toán ZaloPay
                import uuid
                transaction_id = f"ZALO-{uuid.uuid4().hex[:12].upper()}"
                payment_success = True
            
            if payment_success:
                booking = Booking.objects.create(
                    tennis_court=court,
                    user=request.user,
                    play_time=play_time
                )

                invoice = Invoice.objects.create(
                    user=request.user,
                    booking=booking,
                    amount=court_price,
                    status='Paid',
                    payment_method=payment_method,
                    card_last_four=card_last_four,
                    transaction_id=transaction_id
                )

                TransactionHistory.objects.create(
                    user=request.user,
                    transaction_type='Payment',
                    payment_method=payment_method,
                    amount=court_price
                )
                system_account = SystemAccount.objects.first()
                if system_account:
                    system_account.add_funds(court.price)
                RevenueHistory.objects.create(
                    invoice=invoice,
                    amount=court.price,
                    transaction_type='Payment'
                )
                
                # Ghi lại hoạt động đặt sân và thanh toán
                log_activity(request, 'booking', f'Đặt sân {court.name} lúc {play_time}', {
                    'court_id': court.id,
                    'court_name': court.name,
                    'play_time': play_time,
                    'amount': court_price
                })
                log_activity(request, 'payment', f'Thanh toán {court_price} cho sân {court.name} via {payment_method}', {
                    'invoice_id': invoice.id,
                    'amount': court_price,
                    'payment_method': payment_method,
                    'transaction_id': transaction_id
                })
                
                del request.session['temp_booking']
                return redirect('booking_success')

    return render(request, 'apps/checkout.html', {
        'court': court,
        'play_time': play_time,
        'user_balance': user_balance,
        'court_price': court_price,
        'payment_methods': payment_methods
    })



@login_required
def booking_success(request):
    last_booking = Booking.objects.filter(user=request.user).order_by('-id').first()
    if not last_booking:
        messages.error(request, "No recent booking found.")
        return redirect('property_list')

    court = last_booking.tennis_court
    play_time = last_booking.play_time

    return render(request, 'apps/booking_success.html', {
        'court': court,
        'play_time': play_time,
    })


@login_required
def top_up(request):
    # Danh sách ngân hàng và ví điện tử Việt Nam
    banks = [
        {'id': 'vcb', 'name': 'Vietcombank', 'logo': 'vcb'},
        {'id': 'tcb', 'name': 'Techcombank', 'logo': 'tcb'},
        {'id': 'mb', 'name': 'MB Bank', 'logo': 'mb'},
        {'id': 'acb', 'name': 'ACB', 'logo': 'acb'},
        {'id': 'bidv', 'name': 'BIDV', 'logo': 'bidv'},
        {'id': 'vib', 'name': 'VIB', 'logo': 'vib'},
        {'id': 'vpb', 'name': 'VPBank', 'logo': 'vpb'},
        {'id': 'scb', 'name': 'Sacombank', 'logo': 'scb'},
    ]
    
    wallets = [
        {'id': 'momo', 'name': 'Momo', 'logo': 'momo'},
        {'id': 'zalopay', 'name': 'ZaloPay', 'logo': 'zalopay'},
        {'id': 'vnpay', 'name': 'VNPay', 'logo': 'vnpay'},
        {'id': 'shopeepay', 'name': 'ShopeePay', 'logo': 'shopeepay'},
    ]
    
    # Số tiền nhanh để chọn
    quick_amounts = [50, 100, 200, 500, 1000, 2000]
    
    if request.method == 'POST':
        payment_type = request.POST.get('payment_type', '').strip()  # 'bank' hoặc 'wallet'
        bank_id = request.POST.get('bank', '').strip()
        wallet_id = request.POST.get('wallet', '').strip()
        account_number = request.POST.get('account_number', '').strip()
        account_name = request.POST.get('account_name', '').strip()
        card_number = request.POST.get('card_number', '').strip().replace(' ', '')
        card_expiry = request.POST.get('card_expiry', '').strip()
        card_cvv = request.POST.get('card_cvv', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        otp_code = request.POST.get('otp_code', '').strip()
        password = request.POST.get('password', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        
        # Validation errors
        errors = []
        
        # Validate payment type
        if not payment_type:
            errors.append("Please select a payment method.")
        elif payment_type == 'bank':
            if not bank_id:
                errors.append("Please select a bank.")
            
            # Validate card number (13-19 digits)
            if not card_number:
                errors.append("Please enter card number.")
            elif not card_number.isdigit():
                errors.append("Card number can only contain digits.")
            elif len(card_number) < 13 or len(card_number) > 19:
                errors.append("Card number must be 13-19 digits.")
            else:
                # Luhn algorithm validation (kiểm tra tính hợp lệ của số thẻ)
                def luhn_check(card_num):
                    def digits_of(n):
                        return [int(d) for d in str(n)]
                    digits = digits_of(card_num)
                    odd_digits = digits[-1::-2]
                    even_digits = digits[-2::-2]
                    checksum = sum(odd_digits)
                    for d in even_digits:
                        checksum += sum(digits_of(d * 2))
                    return checksum % 10 == 0
                
                if not luhn_check(card_number):
                    errors.append("Card number is invalid (Luhn check failed).")
            
            # Validate card expiry (MM/YY format)
            if not card_expiry:
                errors.append("Please enter card expiry date.")
            else:
                import re
                if not re.match(r'^\d{2}/\d{2}$', card_expiry):
                    errors.append("Expiry must be in MM/YY format.")
                else:
                    month, year = card_expiry.split('/')
                    month = int(month)
                    year = int('20' + year)
                    if month < 1 or month > 12:
                        errors.append("Invalid month (1-12).")
                    else:
                        from datetime import datetime
                        current_date = datetime.now()
                        if year < current_date.year or (year == current_date.year and month < current_date.month):
                            errors.append("Card has expired.")
            
            # Validate CVV (3-4 digits)
            if not card_cvv:
                errors.append("Please enter CVV.")
            elif not card_cvv.isdigit() or len(card_cvv) < 3 or len(card_cvv) > 4:
                errors.append("CVV must be 3-4 digits.")
                
        elif payment_type == 'wallet':
            if not wallet_id:
                errors.append("Please select an e-wallet.")
            
            # Validate phone number for wallet
            if not phone_number:
                errors.append("Please enter phone number.")
            else:
                import re
                # Validate Vietnamese phone number
                phone_clean = re.sub(r'[\s\-\(\)]', '', phone_number)
                if not re.match(r'^(0|\+84)(3|5|7|8|9)\d{8}$', phone_clean):
                    errors.append("Invalid phone number. Please enter a valid Vietnamese phone number.")
            
            # Validate OTP (6 digits)
            if not otp_code:
                errors.append("Please enter OTP code.")
            elif not otp_code.isdigit() or len(otp_code) != 6:
                errors.append("OTP must be exactly 6 digits.")
        
        # Validate account name
        if not account_name:
            errors.append("Please enter account holder name.")
        elif len(account_name) < 2:
            errors.append("Account name must be at least 2 characters.")
        elif len(account_name) > 100:
            errors.append("Account name cannot exceed 100 characters.")
        else:
            import re
            # Only allow letters, spaces, and Vietnamese characters
            if not re.match(r'^[\u00C0-\u024F\u1E00-\u1EFFa-zA-Z\s]+$', account_name):
                errors.append("Account name can only contain letters and spaces.")
        
        # Validate password
        if not password:
            errors.append("Please enter confirmation password.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        
        # Validate amount
        top_up_amount = 0
        if not amount_str:
            errors.append("Please enter top-up amount.")
        else:
            try:
                top_up_amount = float(amount_str)
                if top_up_amount <= 0:
                    errors.append("Top-up amount must be greater than 0.")
                elif top_up_amount < 10:
                    errors.append("Minimum top-up amount is $10.")
                elif top_up_amount > 10000:
                    errors.append("Maximum top-up amount is $10,000 per transaction.")
                elif not (top_up_amount * 100).is_integer():
                    # Only allow 2 decimal places
                    errors.append("Amount can only have up to 2 decimal places.")
            except (ValueError, TypeError):
                errors.append("Invalid amount. Please enter a number.")
        
        # Check daily limit
        from datetime import datetime, timedelta
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_deposits = TransactionHistory.objects.filter(
            user=request.user,
            transaction_type='Deposit',
            timestamp__gte=today_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if today_deposits + top_up_amount > 50000:
            errors.append(f"Daily limit exceeded ($50,000). Already deposited today: ${today_deposits}.")
        
        # Check if AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if errors:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': errors})
            for error in errors:
                messages.error(request, error)
            return render(request, 'apps/top_up.html', {
                'banks': banks,
                'wallets': wallets,
                'quick_amounts': quick_amounts,
                'form_data': request.POST
            })
        
        # Process top-up
        import uuid
        transaction_id = f"TU-{uuid.uuid4().hex[:12].upper()}"
        
        request.user.balance += top_up_amount
        request.user.save()
        
        # Determine payment method for transaction history
        payment_method = bank_id if payment_type == 'bank' else wallet_id
        
        TransactionHistory.objects.create(
            user=request.user,
            transaction_type='Deposit',
            payment_method=payment_method if payment_method in ['momo', 'zalopay', 'vnpay'] else 'bank_transfer',
            amount=top_up_amount
        )
        
        # Ghi lại hoạt động nạp tiền
        log_activity(request, 'top_up', f'Nạp tiền ${top_up_amount}', {
            'amount': top_up_amount,
            'payment_type': payment_type,
            'bank': bank_id,
            'wallet': wallet_id,
            'transaction_id': transaction_id,
            'new_balance': request.user.balance
        })

        messages.success(request, f"Nạp tiền thành công ${top_up_amount:.2f}! Mã giao dịch: {transaction_id}. Số dư hiện tại: ${request.user.balance:.2f}.")
        
        # Always redirect on success (will reload page)
        if is_ajax:
            return JsonResponse({'success': True, 'redirect': True})
        return redirect('top_up')

    return render(request, 'apps/top_up.html', {
        'banks': banks,
        'wallets': wallets,
        'quick_amounts': quick_amounts,
        'current_balance': request.user.balance
    })


@login_required
def profile(request):
    user = request.user 
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Ghi lại hoạt động cập nhật profile
            log_activity(request, 'profile_update', 'Cập nhật thông tin cá nhân')
            messages.success(request, "Thông tin tài khoản đã được cập nhật thành công.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user)

    return render(request, "apps/user_profile.html", {'user': user, 'form': form, 'balance': user.balance})

@login_required
def delete_account(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user and user == request.user:
            user.delete()
            messages.success(request, "Your account has been deleted successfully.")
            return redirect('auth_user')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'apps/delete_account.html')

@login_required
def transaction_history(request):
    user = request.user
    transactions = TransactionHistory.objects.filter(user=user)
    return render(request, 'apps/transaction_history.html', {'transactions': transactions})


def validate_profile_data(full_name, email, phone, address, dob):
    """Validate profile data and return errors"""
    import re
    from datetime import date
    errors = []
    
    # Validate full name (required)
    if not full_name:
        errors.append('Vui lòng nhập họ tên.')
    elif len(full_name) < 2:
        errors.append('Họ tên phải có ít nhất 2 ký tự.')
    elif len(full_name) > 100:
        errors.append('Họ tên không được quá 100 ký tự.')
    elif not re.match(r'^[\u00C0-\u024F\u1E00-\u1EFFa-zA-Z\s\-\']+$', full_name):
        errors.append('Họ tên chỉ được chứa chữ cái và khoảng trắng.')
    
    # Validate email (required)
    if not email:
        errors.append('Vui lòng nhập email.')
    elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors.append('Email không hợp lệ.')
    
    # Validate phone (required and must be valid)
    if not phone:
        errors.append('Vui lòng nhập số điện thoại.')
    else:
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
        if not re.match(r'^\+?\d{10,15}$', cleaned_phone):
            errors.append('Số điện thoại phải có 10-15 chữ số.')
    
    # Validate address (required)
    if not address:
        errors.append('Vui lòng nhập địa chỉ.')
    elif len(address) < 5:
        errors.append('Địa chỉ phải có ít nhất 5 ký tự.')
    elif len(address) > 255:
        errors.append('Địa chỉ không được quá 255 ký tự.')
    
    # Validate date of birth (required)
    if not dob:
        errors.append('Vui lòng nhập ngày sinh.')
    else:
        try:
            from datetime import datetime
            if isinstance(dob, str):
                dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            else:
                dob_date = dob
            today = date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            if dob_date > today:
                errors.append('Ngày sinh không thể ở tương lai.')
            if age < 13:
                errors.append('Bạn phải ít nhất 13 tuổi.')
            if age > 120:
                errors.append('Ngày sinh không hợp lệ.')
        except ValueError:
            errors.append('Định dạng ngày sinh không hợp lệ.')
    
    return errors


@login_required
def edit_profile(request):
        if request.method == 'POST':
            user = request.user
            
            # Get form data
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            address = request.POST.get('address', '').strip()
            dob = request.POST.get('dob', '').strip()
            gender = request.POST.get('gender', '').strip()
            
            # Validate data
            errors = validate_profile_data(full_name, email, phone, address, dob)
            
            # Check if email is already used by another user
            if email and email != user.email:
                from .models import CustomUser
                if CustomUser.objects.filter(email=email).exclude(userID=user.userID).exists():
                    errors.append('Email đã được sử dụng bởi người dùng khác.')
            
            # Validate gender (required)
            if not gender:
                errors.append('Vui lòng chọn giới tính.')
            elif gender not in ['Male', 'Female', 'Other']:
                errors.append('Giới tính không hợp lệ.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('user_profile')
            
            # Parse full_name into first_name and last_name
            # Parse full_name into first_name and last_name (Vietnamese style)
            name_parts = full_name.split() if full_name else []
            if len(name_parts) >= 2:
                # Vietnamese name: last word is first_name (tên), rest is last_name (họ)
                user.first_name = name_parts[-1]  # Tên (ví dụ: Phú)
                user.last_name = ' '.join(name_parts[:-1])  # Họ (ví dụ: Nguyễn Quốc)
            elif len(name_parts) == 1:
                user.first_name = full_name
                user.last_name = ''
            else:
                user.first_name = ''
                user.last_name = ''
            
            # Update all fields (allow empty values to clear fields)
            user.email = email
            user.phone = phone
            user.address = address
            user.dob = dob if dob else None
            user.gender = gender if gender else None
                
            if request.FILES.get('photo'):
                photo = request.FILES['photo']
                
                # Validate photo file
                import os
                ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
                ALLOWED_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/jpg']
                MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
                
                ext = os.path.splitext(photo.name)[1].lower()
                
                if ext not in ALLOWED_EXTENSIONS:
                    messages.error(request, f'Chỉ cho phép tải lên file ảnh ({", ".join(ALLOWED_EXTENSIONS)}). File của bạn có định dạng: {ext}')
                    return redirect('user_profile')
                
                if hasattr(photo, 'size') and photo.size > MAX_FILE_SIZE:
                    size_mb = photo.size / (1024 * 1024)
                    messages.error(request, f'Kích thước file không được vượt quá 5MB. File của bạn có kích thước: {size_mb:.2f}MB')
                    return redirect('user_profile')
                
                if hasattr(photo, 'content_type') and photo.content_type not in ALLOWED_CONTENT_TYPES:
                    messages.error(request, f'File không phải là ảnh hợp lệ. Content type: {photo.content_type}')
                    return redirect('user_profile')
                
                user.photo = photo
            user.save()
            messages.success(request, 'Cập nhật thông tin thành công!')
            return redirect('user_profile')
        return render(request, 'apps/user_profile.html', {'user': request.user})

@login_required
def all_user_bookings(request):
    if not request.user.is_admin():
        return HttpResponseForbidden("You are not authorized to view this page.")

    bookings = Booking.objects.select_related('tennis_court', 'user').all()

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id)

        if 'edit' in request.POST:
            new_play_time = request.POST.get('play_time')
            if Booking.objects.filter(tennis_court=booking.tennis_court, play_time=new_play_time).exists():
                messages.error(request, "The selected play time is already booked. Please choose another time.")
            else:
                booking.play_time = new_play_time
                booking.save()
                messages.success(request, f"Booking time for {booking.user.username} updated successfully!")

        elif 'cancel' in request.POST:
            court = booking.tennis_court
            play_time_list = court.playTime.split(', ') if court.playTime else []

            if booking.play_time not in play_time_list:
                play_time_list.append(booking.play_time)
            
            court.playTime = ', '.join(play_time_list)
            court.save()
            user = booking.user
            user.deposit(court.price)
            TransactionHistory.objects.create(
                user=user,
                transaction_type='Deposit',
                amount=court.price
            )
            invoice = Invoice.objects.create(
                user=user,
                booking=booking,
                amount=court.price,
                status='Cancelled' 
            )
            system_account = SystemAccount.objects.first()
            if system_account:
                system_account.deduct_funds(court.price)
            RevenueHistory.objects.create(
                invoice=invoice,
                amount=court.price,
                transaction_type='Refund'
            )
            booking.delete()
            messages.success(request, f"Booking for {booking.user.username} has been cancelled and refund processed.")

        return redirect('bookings')
    for booking in bookings:
        if booking.tennis_court.playTime:
            booking.tennis_court.available_times = booking.tennis_court.playTime.split(', ')

    return render(request, 'apps/all_bookings.html', {'bookings': bookings})

def revenue_data(request):
    system_account = SystemAccount.objects.first()
    system_balance = system_account.current_balance if system_account else 0.0
    transactions = RevenueHistory.objects.select_related('invoice').all()
    return render(request, 'apps/report_all_payments.html', {
        "system_balance": system_balance,
        "transactions": transactions
    })

@login_required
def my_bookings(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).select_related('tennis_court')
    transactions = TransactionHistory.objects.filter(user=user)
    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        booking = get_object_or_404(Booking, id=booking_id, user=request.user)

        if 'edit' in request.POST:
            new_play_time = request.POST.get('play_time')
            if Booking.objects.filter(tennis_court=booking.tennis_court, play_time=new_play_time).exists():
                messages.error(request, "The selected play time is already booked. Please choose another time.")
            else:
                booking.play_time = new_play_time
                booking.save()
                messages.success(request, "Play time updated successfully!")

        elif 'cancel' in request.POST:
            court = booking.tennis_court
            play_time_list = court.playTime.split(', ') if court.playTime else []

            if booking.play_time not in play_time_list:
                play_time_list.append(booking.play_time)
            
            court.playTime = ', '.join(play_time_list)
            court.save()
            
            user.deposit(court.price)
            TransactionHistory.objects.create(
                user=request.user,
                transaction_type='Deposit',
                amount=court.price
            )
            invoice = Invoice.objects.create(
                user=user,
                booking=booking,
                amount=court.price,
                status='Cancelled' 
            )
            system_account = SystemAccount.objects.first()
            if system_account:
                system_account.deduct_funds(court.price)
            RevenueHistory.objects.create(
                invoice=invoice,
                amount=court.price,
                transaction_type='Refund'
            )
            booking.delete()
            # messages.success(request, 'Booking has been cancelled and refund processed successfully.')

        return redirect('booking')
    for booking in bookings:
        if booking.tennis_court.playTime:
            booking.tennis_court.available_times = booking.tennis_court.playTime.split(', ')

    return render(request, 'apps/my_bookings.html', {'bookings': bookings})

@login_required
def report_court(request, court_id):
    court = Tennis.objects.get(id=court_id)
    if request.method == 'POST':
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.court = court
            report.reporter = request.user
            report.save()
            # Ghi lại hoạt động báo cáo
            log_activity(request, 'report', f'Báo cáo sân {court.name}', {
                'court_id': court_id,
                'court_name': court.name,
                'status': report.court_status
            })
            return redirect(f'/detail/?id={court.id}')
    else:
        form = ReportForm()
    return render(request, 'apps/report.html', {'form': form, 'court': court})

@login_required
def admin_reports(request):
    if not request.user.is_authenticated:
        messages.error(request, "Redirect to login page.")
        return redirect('auth_user')
    if not request.user.is_admin():
        messages.error(request, 'You do not allow access this page.')
        return HttpResponseForbidden("You do not allow access this page.")

    reports = Report.objects.all()
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        action = request.POST.get('action')
        report = get_object_or_404(Report, id=report_id)
        court = report.court

        if action == 'accept':
            court.status = 'Repairing'
            court.save()
            messages.success(request, f"Court {court.name} is now under repair. Users cannot book this court.")

        elif action == 'fixed':
            court.status = 'Available'
            court.save()
            messages.success(request, f"Court {court.name} is now fixed and available for booking.")
            report.delete()

    if request.GET.get('download') == 'pdf':
        court_id = request.GET.get('court_id')
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="admin_reports.pdf"'

        if court_id:
            court = get_object_or_404(Tennis, id=court_id)
            report_data = reports.filter(court=court)
            filename = f"report_{court.name}.pdf"
        else:
            report_data = reports
            filename = "report_all_courts.pdf"

        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        doc = SimpleDocTemplate(response, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Admin Reports", styles['Title']))
        elements.append(Spacer(1, 12))

        courts = report_data.values_list('court', flat=True).distinct()
        for court_id in courts:
            court = Tennis.objects.get(id=court_id)
            elements.append(Paragraph(f"Tennis Court: {court.name}", styles['Heading2']))
            elements.append(Spacer(1, 6))

            court_reports = report_data.filter(court=court)

            table_data = [['ID', 'Status', 'Missing Ball', 'Quality', 'Date', 'Description', 'By']]
            for report in court_reports:
                table_data.append([
                    report.id,
                    Paragraph(report.court_status, styles['Normal']),
                    report.quantity_of_balls,
                    Paragraph(report.quality_of_court or 'No comment', styles['Normal']),
                    report.created_at.strftime('%Y-%m-%d %H:%M'),
                    Paragraph(report.additional_info or 'No comment', styles['Normal']),
                    Paragraph(report.reporter.username or 'No comment', styles['Normal']),
                ])

            table = Table(table_data, colWidths=[30, 65, 80, 80, 100, 150, 50])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Đảm bảo căn dòng trên
            ]))
            elements.append(table)
            elements.append(Spacer(1, 12))

        doc.build(elements)
        return response

    # Render giao diện
    return render(request, 'apps/admin_reports.html', {'reports': reports})

@login_required
def add_review(request, court_id):
    tennis_court = Tennis.objects.get(id=court_id)
    user = request.user

    booking = Booking.objects.filter(user=user, tennis_court=tennis_court).first()

    if not booking:
        messages.error(request, 'You do not allow to rate because you did not rent this court.')
        return redirect(f'/detail/?id={tennis_court.id}')

    try:
        play_time_parts = booking.play_time.split('-')
        start_time = play_time_parts[0].strip()
        end_time = play_time_parts[1].strip()

        start_hour = int(start_time.split(' ')[0])
        end_hour = int(end_time.split(' ')[0])
    except (ValueError, IndexError):
        messages.error(request, 'Invalid play time format. Please contact support.')
        return redirect(f'/detail/?id={tennis_court.id}')


    booking_date = booking.tennis_court.dateTime
    current_time = now()

    if booking_date > current_time.date():
        messages.error(request, 'Only rating after play time ends.')
        return redirect(f'/detail/?id={tennis_court.id}')
    
    if Review.objects.filter(user=user, court=tennis_court).exists():
        messages.error(request, 'You have already rated this court.')
        return redirect(f'/detail/?id={tennis_court.id}')

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = user
            review.court = tennis_court
            review.save()
            # Ghi lại hoạt động đánh giá
            log_activity(request, 'review', f'Đánh giá sân {tennis_court.name}', {
                'court_id': court_id,
                'court_name': tennis_court.name,
                'rating': review.rating
            })
            messages.success(request, 'Rating succesfully!')
            return redirect(f'/detail/?id={tennis_court.id}')
    form = ReviewForm()
    return render(request, 'apps/review.html', {'form': form, 
                                                'court': tennis_court,
                                                'average_rating': tennis_court.reviews.aggregate(Avg('rating'))['rating__avg'] or 0,})

def validate_booking_completion(user, court):
    booking = Booking.objects.filter(user=user, tennis_court=court).first()
    if not booking:
        raise ValidationError("You cannot review this court because you have not booked it.")
    current_time = now()
    play_time_parts = booking.play_time.split('-')
    end_hour = int(play_time_parts[1].split(' ')[0])
    if booking.tennis_court.dateTime == current_time.date() and current_time.hour < end_hour:
        raise ValidationError("You can only review this court after your booking time has ended.")

def admin_required(user):
    return user.is_staff

@login_required
@user_passes_test(admin_required)
def manage_users(request):
    users = CustomUser.objects.filter(role='user') 

    if request.method == 'POST':  
        user_id = request.POST.get('user_id')  
        user_to_delete = CustomUser.objects.filter(userID=user_id).first()
        if user_to_delete:
            user_to_delete.delete()
            messages.success(request, f'User {user_to_delete.username} has been deleted successfully!')
        else:
            messages.error(request, 'User not found.')

        return redirect('manage_users') 

    return render(request, 'apps/manage_users.html', {'users': users})


@login_required
@user_passes_test(admin_required)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, userID=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.role = request.POST.get('role', user.role)
        user.save()
        messages.success(request, 'User updated successfully!')
        return redirect('manage_users')
    return render(request, 'apps/edit_user.html', {'user': user})

@login_required
@user_passes_test(admin_required)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, userID=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully!')
        return redirect('manage_users')
    return render(request, 'apps/delete_user.html', {'user': user})
    
def tennis_court_reviews(request, court_id):
    tennis_court = get_object_or_404(Tennis, id=court_id)
    return render(request, 'apps/rating.html', {'tennis_court': tennis_court})

def property_type(request):
    return render(request, "apps/property-type.html")

def agent(request):
    return render(request, "apps/property-agent.html")

def testimonial(request):
    return render(request, "apps/testimonial.html")

def error(request):
    return render(request, "apps/404.html")

def contact(request):
    return render(request, "apps/contact.html")

def register(request):
    return render(request, "apps/register.html")

def login1(request):
    return render(request, "apps/login.html")


def test_media(request):
    file_path = os.path.join(settings.MEDIA_ROOT, "San1_ky5T64P.jpg")
    if os.path.exists(file_path):
        return HttpResponse(f"Found file: {file_path}")
    else:
        return HttpResponse("File NOT FOUND")

def google_login(request):
    """Redirect to Google OAuth login"""
    from allauth.socialaccount.providers.google.views import oauth2_login
    return oauth2_login(request)


# ==================== ANALYTICS DASHBOARD ====================

@login_required
def analytics_dashboard(request):
    """Trang thống kê hoạt động người dùng - chỉ admin được truy cập"""
    if not request.user.is_admin():
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    # Lấy số ngày từ query params (mặc định 30 ngày)
    days = int(request.GET.get('days', 30))
    
    # Lấy dữ liệu thống kê
    analytics_data = get_analytics_data(days)
    
    # Hoạt động gần đây
    recent_activities = get_recent_activities(50)
    
    # Số người online
    online_users = get_online_users_count()
    
    # Thống kê người dùng
    total_users = CustomUser.objects.count()
    total_admins = CustomUser.objects.filter(role='admin').count()
    total_regular_users = CustomUser.objects.filter(role='user').count()
    
    # Thống kê sân
    total_courts = Tennis.objects.count()
    available_courts = Tennis.objects.filter(status='Available').count()
    repairing_courts = Tennis.objects.filter(status='Repairing').count()
    
    # Thống kê đặt sân theo ngày (7 ngày gần nhất)
    today = timezone.now().date()
    booking_chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = UserActivity.objects.filter(
            activity_type='booking',
            created_at__date=date
        ).count()
        booking_chart_data.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    # Thống kê đăng ký theo ngày (7 ngày gần nhất)
    register_chart_data = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = CustomUser.objects.filter(date_joined__date=date).count()
        register_chart_data.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    # Top người dùng hoạt động
    from django.db.models import Count as DjangoCount
    top_active_users = UserActivity.objects.filter(
        user__isnull=False
    ).values(
        'user__username', 'user__userID'
    ).annotate(
        activity_count=DjangoCount('id')
    ).order_by('-activity_count')[:10]
    
    context = {
        'analytics_data': analytics_data,
        'recent_activities': recent_activities,
        'online_users': online_users,
        'total_users': total_users,
        'total_admins': total_admins,
        'total_regular_users': total_regular_users,
        'total_courts': total_courts,
        'available_courts': available_courts,
        'repairing_courts': repairing_courts,
        'booking_chart_data': booking_chart_data,
        'register_chart_data': register_chart_data,
        'top_active_users': top_active_users,
        'days': days,
    }
    
    return render(request, 'apps/analytics.html', context)


@login_required
def analytics_api(request):
    """API endpoint để lấy dữ liệu analytics (JSON)"""
    if not request.user.is_admin():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    days = int(request.GET.get('days', 30))
    analytics_data = get_analytics_data(days)
    
    # Convert QuerySets to serializable format
    response_data = {
        'activity_stats': analytics_data['activity_stats'],
        'daily_stats': [
            {'date': str(item['date']), 'count': item['count']} 
            for item in analytics_data['daily_stats']
        ],
        'device_stats': analytics_data['device_stats'],
        'browser_stats': analytics_data['browser_stats'],
        'active_sessions': analytics_data['active_sessions'],
        'new_users': analytics_data['new_users'],
        'total_bookings': analytics_data['total_bookings'],
        'total_revenue': analytics_data['total_revenue'],
        'total_page_views': analytics_data['total_page_views'],
        'top_pages': [
            {'url': page.page_url, 'name': page.page_name, 'views': page.view_count}
            for page in analytics_data['top_pages']
        ],
    }
    
    return JsonResponse(response_data)


@login_required 
def user_activity_detail(request, user_id):
    """Xem chi tiết hoạt động của một user cụ thể"""
    if not request.user.is_admin():
        messages.error(request, 'Bạn không có quyền truy cập trang này.')
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    user = get_object_or_404(CustomUser, userID=user_id)
    activity_summary = get_user_activity_summary(user)
    activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:100]
    
    # Phân trang
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_activities = paginator.get_page(page_number)
    
    context = {
        'target_user': user,
        'activity_summary': activity_summary,
        'activities': page_activities,
    }
    
    return render(request, 'apps/user_activity_detail.html', context)