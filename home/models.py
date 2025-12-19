from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.db import models
from django.utils.timezone import now, timedelta
import uuid


class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser model"""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        
        email = self.normalize_email(email) if email else None
        
        # Auto-generate userID if not provided
        if 'userID' not in extra_fields or not extra_fields['userID']:
            extra_fields['userID'] = f"U{uuid.uuid4().hex[:8].upper()}"
        
        extra_fields.setdefault('role', 'user')
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        # Auto-generate userID for superuser
        if 'userID' not in extra_fields or not extra_fields['userID']:
            extra_fields['userID'] = f"ADMIN{uuid.uuid4().hex[:6].upper()}"

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='user')
    userID = models.CharField(max_length=20, unique=True, primary_key=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    photo = models.ImageField(null=True, blank=True)
    balance = models.FloatField(default=0.0)  

    # Custom manager
    objects = CustomUserManager()

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_user_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def deposit(self, amount):
        """Nạp tiền vào tài khoản người dùng."""
        if amount > 0:
            self.balance += amount
            self.save()

    def deduct(self, amount):
        """Trừ tiền trong tài khoản người dùng."""
        if amount > 0 and self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    def is_admin(self):
        return self.role == 'admin'

    def is_user(self):
        return self.role == 'user'

    @property
    def PhotoURL(self):
        try:
            url = self.photo.url
        except:
            url = ''
        return url

    def save(self, *args, **kwargs):
        # Set is_staff based on role, but don't override for superusers
        if self.is_superuser:
            self.is_staff = True
        elif self.role == 'admin':
            self.is_staff = True
        else:
            self.is_staff = False
        super().save(*args, **kwargs)

class Tennis(models.Model):
    STATUS_CHOICES = [ 
        ('Available', 'Available'),
        ('Repairing', 'Repairing'),
    ]
    name = models.CharField(max_length=255, null=True)
    price = models.FloatField()
    squared = models.FloatField()
    limit = models.IntegerField()
    court_address = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Available')
    image = models.ImageField(null=True, blank=True)
    hours = models.IntegerField()  
    brief = models.CharField(max_length=100000, null=True)
    
    playTime = models.CharField(max_length=255, null=True, blank=True)
    booked_times = models.JSONField(default=list) 
    dateTime = models.DateField(null=True, blank=True)  
    
    @property
    def ImageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

    def generate_play_times(self):
        if self.hours is None or self.hours <= 0:
            return []
        
        start_hour = 8
        end_hour = 22
        play_times = []
        for start in range(start_hour, end_hour, self.hours):
            end = start + self.hours
            if end <= end_hour and start < 10 :
                play_times.append(f"{start} hours -{end} hours")
            elif end <= end_hour and start > 10 :
                play_times.append(f"{start} hours - {end} hours")
        return play_times

    def save(self, *args, **kwargs):
        if not self.playTime:  
            self.playTime = ', '.join(self.generate_play_times())
        super().save(*args, **kwargs)

    def book_time(self, play_time):
        if play_time not in self.booked_times:
            self.booked_times.append(play_time)
            self.save()

    def cancel_booking(self, play_time):
        if play_time in self.booked_times:
            self.booked_times.remove(play_time)
            self.save()
            
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum([review.rating for review in reviews]) / len(reviews), 1)
        return 0
class Booking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    tennis_court = models.ForeignKey(Tennis, on_delete=models.CASCADE)
    play_time = models.CharField(max_length=100)
    
    def __str__(self):
        return f'{self.user.username} booked {self.tennis_court.name} at {self.play_time}'
    
class Review(models.Model):
    court = models.ForeignKey(Tennis, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    comment = models.TextField(max_length=150,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['court', 'user']  
        
    def average_rating(self):
        reviews = Review.objects.filter(court=self.court)
        total_reviews = reviews.count()
        total_rating = sum(review.rating for review in reviews)
        return total_rating / total_reviews if total_reviews > 0 else 0

    def __str__(self):
        return f"Review for {self.court.name} by {self.user.username}"
    
class Report(models.Model):
    COURT_STATUS_CHOICES = [
        ('Good', 'Good'),
        ('Damaged', 'Damaged'),
        ('Needs Repair', 'Needs Repair'),
    ]

    court = models.ForeignKey(Tennis, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    court_status = models.CharField(max_length=50, choices=COURT_STATUS_CHOICES, default='Damaged')
    quantity_of_balls = models.IntegerField(blank=True, null=True)
    quality_of_court = models.TextField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.court.name} by {self.reporter.username}"
class Invoice(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='invoices')
    booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, related_name='invoices')
    amount = models.FloatField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def pay(self):
        if self.status == 'Pending' and self.user.deduct(self.amount):
            self.status = 'Paid'
            self.save()
            system_account = SystemAccount.objects.first() 
            if system_account:
                system_account.add_funds(self.amount)
            RevenueHistory.objects.create(
                invoice=self,
                amount=self.amount,
                transaction_type='Payment'
            )
            return True
        return False

    def refund(self):
        """Xử lý hoàn tiền khi booking bị hủy."""
        if self.status == 'Paid':
            self.status = 'Cancelled'
            self.save()
            system_account = SystemAccount.objects.first()
            if system_account:
                system_account.deduct_funds(self.amount)
            RevenueHistory.objects.create(
                invoice=self,
                amount=self.amount,
                transaction_type='Refund'
            )
            return True
        return False

class SystemAccount(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='system_account')
    current_balance = models.FloatField(default=0.0)  # Số dư hiện tại

    def add_funds(self, amount):
        if amount > 0:
            self.current_balance += amount
            self.save()

    def deduct_funds(self, amount):
        if amount > 0 and self.current_balance >= amount:
            self.current_balance -= amount
            self.save()
            return True
        return False

    def __str__(self):
        return f"System Account managed by {self.admin.username} - Balance: {self.current_balance}"


class RevenueHistory(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('Payment', 'Payment'),
        ('Refund', 'Refund'), 
    ]

    invoice = models.OneToOneField('Invoice', on_delete=models.CASCADE, related_name='revenue_history')
    amount = models.FloatField() 
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"Invoice {self.invoice.id} - {self.transaction_type} - Amount: {self.amount}"

    class Meta:
        ordering = ['-timestamp']

class TransactionHistory(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('Deposit', 'Deposit'),  
        ('Payment', 'Payment'),  
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.FloatField() 
    timestamp = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f'{self.user.username} - {self.transaction_type} - {self.amount} at {self.timestamp}'

    class Meta:
        ordering = ['-timestamp'] 
        
class PasswordResetRequest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Approved' if self.is_approved else 'Pending'}"
