import smtplib
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from .utils import *
from .models import *
from .forms import *
from django.contrib.auth import get_user_model
from django_ratelimit.decorators import ratelimit
import logging
from django.http import HttpResponseForbidden
from django.core.signing import dumps, loads, BadSignature, SignatureExpired
from django.urls import reverse
from django.contrib import messages
import smtplib
import socket
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)
User = get_user_model()



# Rate limit the signup view to 5 attempts per 10 minutes per IP address
@ratelimit(key='ip', rate='5/10m', method='POST', block=False)
def signup(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many signup attempts. Please try again in a few minutes.")
        return render(request, 'registration/signup.html', {'form': CustomUserCreationForm()})

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            if User.objects.filter(email=email).exists():
                messages.error(request, "This email is already registered. Please log in.")
                return redirect('login')

            # Generate a time-sensitive token (valid for 30 minutes)
            token = dumps(email)  # token includes timestamp

            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': token})
            )

            email_sent = send_verification_email(email, verification_url)

            if email_sent:
                request.session['pending_user_email'] = email  # Just for display purposes
                return redirect('verification_sent')
            else:
                messages.error(request, "Failed to send verification email. Please try again later.")
                return render(request, 'registration/signup.html', {'form': form})
    else:
        initial_data = {'email': request.session.get('pending_user_email', '')}
        form = CustomUserCreationForm(initial=initial_data)

    return render(request, 'registration/signup.html', {'form': form})


def verification_sent(request):
    email = request.session.get('pending_user_email', '')
    if not email:
        return redirect('signup')

    return render(request, 'registration/verification_sent.html', {'email': email})


def verify_email(request, token):
    try:
        # Try to decode the token with a max age of 1800 seconds (30 minutes)
        email = loads(token, max_age=1800)
    except SignatureExpired:
        messages.error(request, 'Verification link has expired. Please sign up again.')
        return redirect('signup')
    except BadSignature:
        messages.error(request, 'Invalid verification link.')
        return redirect('signup')

    # Store email in session for the password setup step
    request.session['verified_email'] = email

    messages.success(request, 'Email verified! Now, set your password.')
    return redirect('set_password')


def set_password(request):
    email = request.session.get('verified_email')

    if not email:
        messages.error(request, "Session expired. Please verify your email again.")
        return redirect('signup')

    # Check if the user already exists (avoid duplicate accounts)
    if User.objects.filter(email=email).exists():
        messages.warning(request, "An account with this email already exists. Please log in.")
        return redirect('login')

    # Create a temporary user object for form validation (with empty names to avoid DB error)
    temp_user = User(email=email)

    if request.method == 'POST':
        form = SetPasswordForm(temp_user, request.POST)
        if form.is_valid():
            password = form.cleaned_data['new_password1']

            # Create and save the actual user
            user = User.objects.create_user(email=email, first_name='', last_name='')
            user.set_password(password)
            user.is_active = True
            user.save()

            # Create user profile and account
            UserProfile.objects.create(user=user, is_verified=True)
            Account.objects.create(user=user, balance=0.0)  # Adjust fields as necessary

            # Send the welcome email
            send_welcome_email(user.email, user.email)

            # Clear session
            del request.session['verified_email']

            # Check if the user has set a PIN
            if not user.pin:  # If the user has not set a PIN
                messages.info(request, 'You need to set your PIN before proceeding.')
                return redirect('set_pin')  # Redirect to the set pin page

            messages.success(request, 'Your password has been set and you are automatically logged in.')
            user.backend = 'accounts.backends.EmailBackend'
            login(request, user)
            return redirect('home')
        else:
            # Flash each form error
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = SetPasswordForm(temp_user)

    return render(request, 'registration/set_password.html', {'form': form})



@ratelimit(key='ip', rate='3/10m', method='POST', block=False)
def user_login(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many login attempts. Please try again in a few minutes.")
        return render(request, 'registration/login.html', {'form': CustomLoginForm()})

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=email, password=password)
            if user is not None:
                profile = UserProfile.objects.get(user=user)

                if not profile.is_verified:
                    messages.error(request, 'Please verify your email first.')
                    return redirect('login')

                if not user.is_active:
                    messages.error(request, 'Your account is inactive. Please contact support.')
                    return redirect('login')

                # Generate OTP
                otp = profile.generate_otp()

                try:
                    send_otp_email(user, otp)

                except (smtplib.SMTPException, socket.error, ConnectionError, ImproperlyConfigured) as e:
                    logger.exception(f"SMTP/Connection error while sending OTP to {email}: {e}")
                    messages.error(request, "Unable to send OTP email due to a server or network issue. Please try again shortly.")
                    return render(request, 'registration/login.html', {'form': form})

                except Exception as e:
                    logger.exception(f"Unexpected error sending OTP to {email}: {e}")
                    messages.error(request, "An unexpected error occurred while sending your OTP. Please try again later.")
                    return render(request, 'registration/login.html', {'form': form})

                # Store user ID for OTP verification
                request.session['user_id_for_otp'] = str(user.id)
                messages.info(request, 'An OTP has been sent to your email.')
                return redirect('verify_otp')

            else:
                messages.error(request, "Invalid email or password.")
        else:
            print(f"Form errors: {form.errors}")
    else:
        form = CustomLoginForm()

    return render(request, 'registration/login.html', {'form': form})



@ratelimit(key='ip', rate='3/10m', method='POST', block=False)
def verify_otp(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many OTP attempts. Please try again later.")
        return render(request, 'registration/verify_otp.html')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        user_id = request.session.get('user_id_for_otp')

        if user_id:
            try:
                profile = UserProfile.objects.get(user_id=user_id)
                if profile.is_otp_valid(otp):
                    user = profile.user

                    # Optional: check is_active again
                    if not user.is_active:
                        messages.error(request, 'Your account is inactive.')
                        return redirect('login')
                    
                    user.backend = 'accounts.backends.EmailBackend'
                    # Login the user
                    login(request, user)
                    del request.session['user_id_for_otp']

                    # Check if the user has set a PIN
                    if not user.pin:  # If the user has not set a PIN
                        messages.info(request, 'You need to set your PIN before proceeding.')
                        return redirect('set_pin')  # Redirect to the set pin page

                    messages.success(request, 'OTP verified successfully. You are now logged in.')
                    return redirect('dashboard')

                messages.error(request, 'Invalid or expired OTP.')
                return redirect('user_login')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User session expired or invalid.')
                return redirect('login')

    return render(request, 'registration/verify_otp.html')



@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id_for_otp')

        if not user_id:
            return JsonResponse({'status': 'error', 'message': 'Session expired. Please log in again.'}, status=400)

        try:
            user = User.objects.get(pk=user_id)
            profile = UserProfile.objects.get(user=user)

            # Generate new OTP and send it
            otp = profile.generate_otp()
            send_otp_email(user, otp)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.exception(f"Error resending OTP: {e}")
            return JsonResponse({'status': 'error', 'message': 'Unable to send OTP at this time.'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')  



@ratelimit(key='ip', rate='3/10m', method='POST', block=False)
def request_password_reset(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many password reset requests. Please try again later.")
        return render(request, 'registration/request_reset.html')

    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            profile = UserProfile.objects.get(user=user)
            reset_token = profile.generate_reset_token()

            reset_url = request.build_absolute_uri(f'/accounts/reset-password/{reset_token}/')
            send_password_reset_email(email, reset_url)

            messages.success(request, 'A password reset link has been sent to your email.')
            return redirect('request_reset')

        except User.DoesNotExist:
            messages.info(request, 'If the email is registered a reset link will be sent to it.')

    return render(request, 'registration/request_reset.html')

from django.contrib.auth.forms import SetPasswordForm

@ratelimit(key='ip', rate='3/10m', method='POST', block=False)
def reset_password(request, token):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many password reset attempts. Please try again later.")
        return render(request, 'registration/reset_password.html', {'token': token})

    try:
        profile = UserProfile.objects.get(reset_token=token)
        if not profile.is_reset_token_valid(token):
            messages.error(request, 'Invalid or expired token.')
            return redirect('request_reset')

        user = profile.user

        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()  # This sets the password and saves the user
                # Clear reset token after success
                profile.reset_token = None
                profile.reset_token_expiry = None
                profile.save()

                messages.success(request, 'Your password has been reset. Please log in.')
                return redirect('login')
            else:
                # Show form errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, error)
        else:
            form = SetPasswordForm(user)

    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid token.')
        return redirect('request_reset')

    return render(request, 'registration/reset_password.html', {'token': token, 'form': form})




@login_required
def view_account(request, account_id):
    account = get_object_or_404(Account, id=account_id)
    if account.user != request.user:  # Ensure the account belongs to the logged-in user
        return HttpResponseForbidden("You do not have permission to view this account.")
    return render(request, 'accounts/account_detail.html', {'account': account})

@login_required
def dashboard(request):
    user = request.user

    # Redirect to NIN/BVN verification page if not verified
    if not hasattr(user, 'bio_data'):
        return redirect('verify_intro')

    # Redirect to set PIN if not set
    if not user.pin:
        return redirect('set_pin')

    # Check if PIN is submitted via modal
    if request.method == 'POST' and 'pin' in request.POST:
        pin = request.POST.get('pin')
        if user.check_pin(pin):
            request.session['pin_verified'] = True
            request.session['pin_success_gif'] = True
            messages.success(request, 'PIN verified successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid PIN. Please try again.")

    # Check if success modal should be shown
    show_success_modal = False
    if request.session.get('pin_success_gif'):
        show_success_modal = True
        del request.session['pin_success_gif']

    # Load account and transactions
    try:
        account = Account.objects.get(user=user)
    except Account.DoesNotExist:
        messages.error(request, "Your account could not be found. Please contact support.")
        return redirect('home')

    # Fetch biodata
    bio_data = BioData.objects.filter(user=user).first()
    transactions = Transaction.objects.filter(account=account).order_by('-timestamp')
    no_transactions_message = None
    if not transactions.exists():
        no_transactions_message = "You haven't made any transactions."

    return render(request, 'accounts/dashboard.html', {
        'account': account,
        'transactions': transactions,
        'no_transactions_message': no_transactions_message,
        'show_pin_modal': not request.session.get('pin_verified'),
        'show_success_modal': show_success_modal,
        'bio_data': bio_data,
    })


@login_required
def verify_intro(request):
    # Redirect if user is already verified
    if hasattr(request.user, 'bio_data'):
        return redirect('dashboard')
    return render(request, 'accounts/verify_intro.html')

@login_required
def verify_account(request):
    user = request.user

    if request.method == 'POST':
        id_type = request.POST.get('id_type')
        id_number = request.POST.get('id_number')

        # Simulated delay for the loading spinner
        import time
        time.sleep(2)

        record = None
        if id_type == 'nin':
            record = NINDatabase.objects.filter(nin=id_number).first()
        elif id_type == 'bvn':
            record = BVNDatabase.objects.filter(bvn=id_number).first()

        if record:
            # Check if already used - check against the correct field based on id_type
            if id_type == 'nin' and BioData.objects.filter(nin=record.nin).exists():
                messages.error(request, f"This NIN has already been used.")
                return redirect('verify_account')
            elif id_type == 'bvn' and BioData.objects.filter(bvn=record.bvn).exists():
                messages.error(request, f"This BVN has already been used.")
                return redirect('verify_account')

            # Create BioData linked to the user
            BioData.objects.create(
                user=user,
                nin=record.nin if id_type == 'nin' else None,
                bvn=record.bvn if id_type == 'bvn' else None,
                first_name=record.first_name,
                middle_name=record.middle_name,
                last_name=record.last_name,
                date_of_birth=record.date_of_birth,
                address=record.address,
                phone_number=record.phone_number
            )

            messages.success(request, 'Account verified successfully!')
            request.session['account_verified'] = True  # To trigger success GIF
            return redirect('dashboard')
        else:
            messages.error(request, f"{id_type.upper()} not found in the system.")

    return render(request, 'accounts/verify_account.html')



@login_required
def set_pin(request):
    if request.method == 'POST':
        form = PinForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data['pin']
            user = request.user
            user.set_pin(pin)  # Make sure set_pin method hashes and saves the PIN
            messages.success(request, 'Your PIN has been successfully set.')
            request.session['pin_set_success_gif'] = True
            return redirect('home')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PinForm()

    return render(request, 'accounts/set-pin.html', {'form': form})