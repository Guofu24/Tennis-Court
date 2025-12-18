from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import *

class PasswordResetRequestForm(forms.Form):
    username = forms.CharField(max_length=150, label="Enter your username")

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'userID', 'dob', 'gender', 'phone', 'address', 'email']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

# Form đăng ký người dùng
class UserRegistrationForm(UserCreationForm):
    dob = forms.DateField(
        input_formats=['%d/%m/%Y'],
        widget=forms.DateInput(attrs={'placeholder': 'DD/MM/YYYY', 'class': 'form-control'})
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
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'user'
        if commit:
            user.save()
        return user

# Form đăng ký quản trị viên
class AdminRegistrationForm(UserCreationForm):
    dob = forms.DateField(
        input_formats=['%d/%m/%Y'], 
        widget=forms.DateInput(attrs={'placeholder': 'DD/MM/YYYY', 'class': 'form-control'})
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

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)], attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Not over 150 words'}),
        }
        
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
            'quantity_of_balls': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'In each court, we have at least 10 balls, please enter the of missing ball'}),
            'quality_of_court': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe court quality'}),
            'additional_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any additional details'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }