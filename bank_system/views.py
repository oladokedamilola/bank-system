from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    if request.user.is_authenticated:
        user = request.user
        print(f"User PIN: {user.pin}")  
        if not user.pin:
            return redirect('set_pin')

        return render(request, 'home.html')
    else:
        return render(request, 'home.html')
    

def terms_of_service(request):
    return render(request, 'terms_of_service.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')
