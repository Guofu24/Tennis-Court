from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate,logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import *
from .models import *
from django.db.models import Avg, Count
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

def auth_user(request):
    register_form = UserRegistrationForm()

    if request.method == 'POST':
        if 'register' in request.POST:
            register_form = UserRegistrationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save()  
                login(request, user)  
                messages.success(request, 'Account created successfully!')
                return redirect('home') 

        elif 'login' in request.POST:
                if request.method == 'POST':
                    username = request.POST.get('userName')
                    password = request.POST.get('userPass')
                    user = authenticate(request, username=username, password=password)
                    
                    if user is not None:
                        if user.is_user():
                            login(request, user)
                            return redirect('home')
                        else:
                            messages.error(request, 'User does not have admin privileges.')
                    else: 
                        messages.error(request, 'UserName or password is incorrect!')

    return render(request, "apps/login_user.html", {'register_form': register_form})

def auth_admin(request):
    register_form_admin = AdminRegistrationForm()

    if request.method == 'POST':
        if 'register' in request.POST:
            register_form_admin = AdminRegistrationForm(request.POST)
            if register_form_admin.is_valid():
                user = register_form_admin.save()  
                login(request, user)  
                messages.success(request, 'Account created successfully!')
                return redirect('home') 

        elif 'login' in request.POST:
            if request.method == 'POST':
                username = request.POST.get('adminName')
                password = request.POST.get('adminPass')
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    if user.is_admin():
                        login(request, user)
                        return redirect('home')
                    else:
                        messages.error(request, 'User does not have admin privileges.')
                else: 
                    messages.error(request, 'UserName or password is incorrect!')

    return render(request, "apps/login_admin.html", {'register_form_admin': register_form_admin})

def logoutPage(request):
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

    if request.method == 'POST':
        form = TennisForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sân tennis mới đã được thêm thành công!')
            return redirect('property_list')
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

    if request.method == 'POST':
        if 'cancel' in request.POST:
            del request.session['temp_booking']
            messages.warning(request, "Booking cancelled.")
            return redirect(f'/detail/?id={court.id}')
        elif 'pay' in request.POST:
            if user_balance >= court_price:
                request.user.balance -= court_price
                request.user.save()

                booking = Booking.objects.create(
                    tennis_court=court,
                    user=request.user,
                    play_time=play_time
                )

                invoice = Invoice.objects.create(
                    user=request.user,
                    booking=booking,
                    amount=court_price,
                    status='Paid'
                )

                TransactionHistory.objects.create(
                    user=request.user,
                    transaction_type='Payment',
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
                del request.session['temp_booking']
                # messages.success(request, "Payment successful! Your booking is confirmed.")
                return redirect('booking_success')
            else:
                messages.error(request, "Insufficient balance. Please top up your account.")
                return redirect('top_up')

    return render(request, 'apps/checkout.html', {
        'court': court,
        'play_time': play_time,
        'user_balance': user_balance,
        'court_price': court_price
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
    if request.method == 'POST':
        bank = request.POST.get('bank')
        wallet = request.POST.get('wallet')
        account_name = request.POST.get('account_name')
        password = request.POST.get('password')
        top_up_amount = float(request.POST.get('amount'))
        if top_up_amount <= 0:
            messages.error(request, "Please enter a valid amount to deposit.")
            return redirect('top_up')
        request.user.balance += top_up_amount
        request.user.save()
        TransactionHistory.objects.create(
            user=request.user,
            transaction_type='Deposit',
            amount=top_up_amount
        )

        messages.success(request, f"Successfully topped up ${top_up_amount}. Your new balance is ${request.user.balance}.")
        return redirect('property_list')

    return render(request, 'apps/top_up.html')


@login_required
def profile(request):
    user = request.user 
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
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


@login_required
def edit_profile(request):
        if request.method == 'POST':
            user = request.user
            # Parse full_name into first_name and last_name
            full_name = request.POST.get('full_name', '').strip()
            if full_name:
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    # Vietnamese name: last word is first_name (tên), rest is last_name (họ)
                    user.first_name = name_parts[-1]  # Tên (ví dụ: Phú)
                    user.last_name = ' '.join(name_parts[:-1])  # Họ (ví dụ: Nguyễn Quốc)
                else:
                    user.first_name = full_name
                    user.last_name = ''
            
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.address = request.POST.get('address', user.address)
            
            # Handle date of birth
            dob = request.POST.get('dob')
            if dob:
                user.dob = dob
            
            user.gender = request.POST.get('gender', user.gender)
            if request.FILES.get('photo'):
                user.photo = request.FILES['photo']
            user.save()
            messages.success(request, 'Profile updated successfully!')
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