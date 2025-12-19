from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import re
from .models import *

# =========================
# VALIDATORS
# =========================

def validate_phone(value):
    """Validate phone number - only digits, 10-15 characters"""
    if value:
        cleaned = re.sub(r'[\s\-\(\)]', '', value)  # Remove spaces, dashes, parentheses
        if not re.match(r'^\+?\d{10,15}$', cleaned):
            raise ValidationError('Số điện thoại phải có 10-15 chữ số.')
    return value

def validate_name(value):
    """Validate name - only letters, spaces, and Vietnamese characters"""
    if value:
        # Allow Vietnamese characters, letters, spaces
        if not re.match(r'^[\u00C0-\u024F\u1E00-\u1EFFa-zA-Z\s\-\']+$', value):
            raise ValidationError('Tên chỉ được chứa chữ cái và khoảng trắng.')
        if len(value) < 2:
            raise ValidationError('Tên phải có ít nhất 2 ký tự.')
        if len(value) > 100:
            raise ValidationError('Tên không được quá 100 ký tự.')
    return value

def validate_username(value):
    """Validate username - alphanumeric and underscore only"""
    if value:
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValidationError('Username chỉ được chứa chữ cái, số và dấu gạch dưới.')
        if len(value) < 3:
            raise ValidationError('Username phải có ít nhất 3 ký tự.')
        if len(value) > 30:
            raise ValidationError('Username không được quá 30 ký tự.')
    return value

def validate_citizen_id(value):
    """Validate Citizen ID - digits only, 9 or 12 characters for Vietnam"""
    if value:
        if not re.match(r'^\d{9,12}$', value):
            raise ValidationError('CCCD/CMND phải có 9-12 chữ số.')
    return value

def validate_dob(value):
    """Validate date of birth - must be in the past and reasonable age"""
    if value:
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if value > today:
            raise ValidationError('Ngày sinh không thể ở tương lai.')
        if age < 13:
            raise ValidationError('Bạn phải ít nhất 13 tuổi.')
        if age > 120:
            raise ValidationError('Ngày sinh không hợp lệ.')
    return value

def validate_password_strength(value):
    """Validate password strength"""
    if value:
        if len(value) < 8:
            raise ValidationError('Mật khẩu phải có ít nhất 8 ký tự.')
        if not re.search(r'[A-Z]', value):
            raise ValidationError('Mật khẩu phải có ít nhất 1 chữ hoa.')
        if not re.search(r'[a-z]', value):
            raise ValidationError('Mật khẩu phải có ít nhất 1 chữ thường.')
        if not re.search(r'\d', value):
            raise ValidationError('Mật khẩu phải có ít nhất 1 chữ số.')
    return value

def validate_address(value):
    """Validate address"""
    if value:
        if len(value) < 5:
            raise ValidationError('Địa chỉ phải có ít nhất 5 ký tự.')
        if len(value) > 255:
            raise ValidationError('Địa chỉ không được quá 255 ký tự.')
    return value

def validate_email_format(value):
    """Validate email format"""
    if value:
        email_validator = EmailValidator(message='Email không hợp lệ.')
        email_validator(value)
    return value


class PasswordResetRequestForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        label="Enter your username",
        validators=[validate_username]
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'userID', 'dob', 'gender', 'phone', 'address', 'email']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def clean_first_name(self):
        value = self.cleaned_data.get('first_name')
        return validate_name(value)
    
    def clean_phone(self):
        value = self.cleaned_data.get('phone')
        return validate_phone(value)
    
    def clean_email(self):
        value = self.cleaned_data.get('email')
        return validate_email_format(value)
    
    def clean_dob(self):
        value = self.cleaned_data.get('dob')
        return validate_dob(value)
    
    def clean_address(self):
        value = self.cleaned_data.get('address')
        return validate_address(value)

# Form đăng ký người dùng
class UserRegistrationForm(UserCreationForm):
    GENDER_CHOICES = [
        ('', '-- Chọn giới tính --'),
        ('Male', 'Nam'),
        ('Female', 'Nữ'),
        ('Other', 'Khác'),
    ]
    
    dob = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={'placeholder': 'DD/MM/YYYY', 'class': 'form-control'}),
        validators=[validate_dob]
    )
    first_name = forms.CharField(
        max_length=100,
        validators=[validate_name],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên'})
    )
    phone = forms.CharField(
        max_length=15,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'})
    )
    email = forms.EmailField(
        validators=[validate_email_format],
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        validators=[validate_address],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ'})
    )
    userID = forms.CharField(
        max_length=20,
        validators=[validate_citizen_id],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CCCD/CMND'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'userID', 'dob', 'gender', 'phone', 'address', 'email', 'password1', 'password2', 'photo']
        labels = {
            'username': 'UserName',
            'first_name': 'Full name',
            'userID': 'CitizenID',
            'dob': 'Date of Birth',
            'gender': 'Gender',
            'phone': 'Phone number',
            'address': 'Address',
            'email': 'Email',
            'password1': 'Password',
            'password2': 'Repeat Password',
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_gender(self):
        value = self.cleaned_data.get('gender')
        if not value:
            raise ValidationError('Vui lòng chọn giới tính.')
        return value
    
    def clean_username(self):
        value = self.cleaned_data.get('username')
        validate_username(value)
        # Check if username already exists
        if CustomUser.objects.filter(username=value).exists():
            raise ValidationError('Username đã tồn tại.')
        return value
    
    def clean_email(self):
        value = self.cleaned_data.get('email')
        validate_email_format(value)
        # Check if email already exists
        if CustomUser.objects.filter(email=value).exists():
            raise ValidationError('Email đã được sử dụng.')
        return value
    
    def clean_userID(self):
        value = self.cleaned_data.get('userID')
        validate_citizen_id(value)
        # Check if userID already exists
        if CustomUser.objects.filter(userID=value).exists():
            raise ValidationError('CCCD/CMND đã được sử dụng.')
        return value
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'user'
        if commit:
            user.save()
        return user

# Form đăng ký quản trị viên
class AdminRegistrationForm(UserCreationForm):
    GENDER_CHOICES = [
        ('', '-- Chọn giới tính --'),
        ('Male', 'Nam'),
        ('Female', 'Nữ'),
        ('Other', 'Khác'),
    ]
    
    dob = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'], 
        widget=forms.DateInput(attrs={'placeholder': 'DD/MM/YYYY', 'class': 'form-control'}),
        validators=[validate_dob]
    )
    first_name = forms.CharField(
        max_length=100,
        validators=[validate_name],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ và tên'})
    )
    phone = forms.CharField(
        max_length=15,
        validators=[validate_phone],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Số điện thoại'})
    )
    email = forms.EmailField(
        validators=[validate_email_format],
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    address = forms.CharField(
        max_length=255,
        required=False,
        validators=[validate_address],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Địa chỉ'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'userID', 'dob', 'gender', 'phone', 'address', 'email', 'password1', 'password2', 'photo']
        labels = {
            'username': 'UserName',
            'first_name': 'Full name',
            'userID': 'AdminID',
            'dob': 'Date of Birth',
            'gender': 'Gender',
            'phone': 'Phone number',
            'address': 'Address',
            'email': 'Email',
            'password1': 'Password',
            'password2': 'Repeat Password',
        }

    def clean_gender(self):
        value = self.cleaned_data.get('gender')
        if not value:
            raise ValidationError('Vui lòng chọn giới tính.')
        return value

    def clean_username(self):
        value = self.cleaned_data.get('username')
        validate_username(value)
        if CustomUser.objects.filter(username=value).exists():
            raise ValidationError('Username đã tồn tại.')
        return value
    
    def clean_email(self):
        value = self.cleaned_data.get('email')
        validate_email_format(value)
        if CustomUser.objects.filter(email=value).exists():
            raise ValidationError('Email đã được sử dụng.')
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'admin'
        if commit:
            user.save()
        return user

class TennisForm(forms.ModelForm):
    class Meta:
        model = Tennis
        fields = ['name', 'price', 'court_address', 'squared', 'limit', 'brief', 'hours', 'image', 'playTime', 'dateTime']
        widgets = {
            'dateTime': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.hours:
            play_times = self.instance.generate_play_times()
            self.fields['playTime'].choices = [(time, time) for time in play_times]
    
    def clean_name(self):
        value = self.cleaned_data.get('name')
        if value:
            if len(value) < 2:
                raise ValidationError('Tên sân phải có ít nhất 2 ký tự.')
            if len(value) > 100:
                raise ValidationError('Tên sân không được quá 100 ký tự.')
        return value
    
    def clean_price(self):
        value = self.cleaned_data.get('price')
        if value is not None:
            if value < 0:
                raise ValidationError('Giá không được âm.')
            if value > 10000:
                raise ValidationError('Giá không được quá $10,000.')
        return value
    
    def clean_court_address(self):
        value = self.cleaned_data.get('court_address')
        if value:
            if len(value) < 5:
                raise ValidationError('Địa chỉ sân phải có ít nhất 5 ký tự.')
        return value
    
    def clean_squared(self):
        value = self.cleaned_data.get('squared')
        if value is not None:
            if value <= 0:
                raise ValidationError('Diện tích phải lớn hơn 0.')
        return value
    
    def clean_limit(self):
        value = self.cleaned_data.get('limit')
        if value is not None:
            if value < 2:
                raise ValidationError('Giới hạn người chơi phải ít nhất 2.')
            if value > 20:
                raise ValidationError('Giới hạn người chơi không được quá 20.')
        return value
    
    def clean_hours(self):
        value = self.cleaned_data.get('hours')
        if value is not None:
            if value < 1:
                raise ValidationError('Số giờ phải ít nhất 1.')
            if value > 24:
                raise ValidationError('Số giờ không được quá 24.')
        return value

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)], attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Không quá 150 từ'}),
        }
    
    def clean_rating(self):
        value = self.cleaned_data.get('rating')
        if value is not None:
            if value < 1 or value > 5:
                raise ValidationError('Đánh giá phải từ 1 đến 5 sao.')
        return value
    
    def clean_comment(self):
        value = self.cleaned_data.get('comment')
        if value:
            words = value.split()
            if len(words) > 150:
                raise ValidationError('Bình luận không được quá 150 từ.')
            if len(value) > 1000:
                raise ValidationError('Bình luận không được quá 1000 ký tự.')
        return value
        
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['court_status', 'quantity_of_balls', 'quality_of_court', 'additional_info', 'image']
        labels = {
            'court_status': 'Court Status',
            'quantity_of_balls': 'Quantity of Balls',
            'quality_of_court': 'Quality of Court',
            'additional_info': 'Additional Information',
            'image': 'Upload Image (optional)',
        }
        widgets = {
            'court_status': forms.Select(attrs={'class': 'form-control'}),
            'quantity_of_balls': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mỗi sân có ít nhất 10 bóng, nhập số bóng thiếu'}),
            'quality_of_court': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mô tả chất lượng sân'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Thông tin bổ sung'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_quantity_of_balls(self):
        value = self.cleaned_data.get('quantity_of_balls')
        if value is not None:
            if value < 0:
                raise ValidationError('Số lượng bóng không được âm.')
            if value > 100:
                raise ValidationError('Số lượng bóng thiếu không được quá 100.')
        return value
    
    def clean_quality_of_court(self):
        value = self.cleaned_data.get('quality_of_court')
        if value:
            if len(value) < 10:
                raise ValidationError('Mô tả chất lượng sân phải có ít nhất 10 ký tự.')
        return value