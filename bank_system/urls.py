from django.contrib import admin
from django.urls import path
from accounts.views import (
    signup, verification_sent, verify_email,set_password, user_login, verify_otp, user_logout, 
    request_password_reset, reset_password, dashboard, set_pin
)
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Custom authentication views
    path('accounts/signup/', signup, name='signup'),
    path('accounts/verification-sent/', verification_sent, name='verification_sent'),
    path('accounts/verify-email/<str:token>/', verify_email, name='verify_email'),
    path('accounts/set-password/', set_password, name='set_password'),
    path('accounts/login/', user_login, name='login'),
    path('accounts/verify-otp/', verify_otp, name='verify_otp'),
    path('accounts/logout/', user_logout, name='logout'),

    # Custom password reset views
    path('accounts/request-reset/', request_password_reset, name='request_reset'),
    path('accounts/reset-password/<str:token>/', reset_password, name='reset_password'),

    # Home and dashboard
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('dashboard/', dashboard, name='dashboard'),

    path('set-pin/', set_pin, name='set_pin'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_URL)
