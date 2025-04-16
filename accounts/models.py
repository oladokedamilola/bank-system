from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid
from django.utils.timezone import now
from datetime import timedelta
import bcrypt


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, first_name='', last_name=''):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email=email, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user



class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=False)  # Inactive until email is verified
    is_staff = models.BooleanField(default=False)  # Required for admin access
    date_joined = models.DateTimeField(auto_now_add=True)
    pin = models.CharField(max_length=60, blank=True, null=True)  # PIN field for storing hashed PIN

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No first name or last name required at signup

    def __str__(self):
        return self.email
    
    def set_pin(self, raw_pin):
        """
        Set the pin for the user, hashed for security.
        """
        salt = bcrypt.gensalt()
        self.pin = bcrypt.hashpw(raw_pin.encode('utf-8'), salt).decode('utf-8')
        self.save()

    def check_pin(self, raw_pin):
        """
        Check the provided pin against the stored hash.
        """
        return bcrypt.checkpw(raw_pin.encode('utf-8'), self.pin.encode('utf-8'))

    def __str__(self):
        return self.username

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)  # Email verification
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(blank=True, null=True)
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    reset_token_expiry = models.DateTimeField(blank=True, null=True)

    def generate_otp(self):
        import random
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        self.save()
        return self.otp

    def is_otp_valid(self, entered_otp):
        return self.otp == entered_otp and self.otp_expiry > now()

    def generate_verification_token(self):
        return str(uuid.uuid4())  # Unique token for email verification
    
    def generate_reset_token(self):
        self.reset_token = str(uuid.uuid4())  # Generate a unique token
        self.reset_token_expiry = now() + timedelta(hours=1)  # Token valid for 1 hour
        self.save()
        return self.reset_token

    def is_reset_token_valid(self, token):
        return self.reset_token == token and self.reset_token_expiry > now()





class Account(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=10, unique=True, blank=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.account_number:
            from .utils import generate_unique_account_number
            self.account_number = generate_unique_account_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email}'s Account"



class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal')])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} of ${self.amount} on {self.timestamp}"
