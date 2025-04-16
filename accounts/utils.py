from django.core.mail import send_mail
from django.conf import settings
import logging
import random


logger = logging.getLogger(__name__)  # Log errors


def send_verification_email(email, verification_url):
    # Debugging: Print the configuration values
    print(f"Sending email to: {email}")
    print(f"Subject: Verify your email address - {settings.APP_NAME}")
    print(f"Message: Click the link below to verify your email:\n{verification_url}")
    print(f"Using email host: {settings.EMAIL_HOST}")
    print(f"SMTP user: {settings.EMAIL_HOST_USER}")
    
    subject = f"Verify your email address - {settings.APP_NAME}"
    message = f'Click the link below to verify your email:\n{verification_url} \n\n\n\n This link expres in 30 minutes...'
    
    try:
        # Debugging: Confirm before trying to send the email
        print("Attempting to send email...")
        
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
        
        # Debugging: If the email was successfully sent
        print(f"Verification email sent successfully to {email}")
        
    except Exception as e:
        # Debugging: If there's an error sending the email
        print(f"Failed to send verification email to {email}: {e}")
        logger.error(f"Failed to send verification email to {email}: {e}")
        return False
        
    return True


def send_welcome_email(user_email, user_name):
    """
    Sends a welcome email to the user after successful account setup.
    """
    subject = 'Welcome to Bank System'
    message = f'Hello {user_name},\n\nWelcome to Bank System! Your account has been successfully created and your password is set. We are excited to have you on board.\n\nBest regards,\nBank System Team'
    
    # Sending the email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,  
        [user_email],  
        fail_silently=False,
    )


def send_otp_email(user, otp):
    subject = f'Your OTP for Login - {settings.APP_NAME}'
    message = f'Your OTP is: {otp}. It will expire in 10 minutes.'
    
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {e}")  # Log the error
        return False  # Return False to handle failure
    return True  # Return True if successful




def send_password_reset_email(email, reset_url):
    subject = f'Reset Your Password - {settings.APP_NAME}'
    message = f'Click the link below to reset your password:\n{reset_url}'
    
    try:
        send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {e}")
        return False
    return True



def generate_unique_account_number():
    from .models import Account  # Avoid circular import

    while True:
        account_number = '04' + ''.join([str(random.randint(0, 9)) for _ in range(8)])
        if not Account.objects.filter(account_number=account_number).exists():
            return account_number

