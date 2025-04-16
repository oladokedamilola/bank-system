from django.shortcuts import render


def home(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user

        # Check if the user has set their PIN
        if not user.pin:
            # If the user hasn't set a PIN, show the PIN modal
            return render(request, 'home.html', {'show_pin_modal': True, 'show_success_modal': False})

        # Check if the success GIF should be shown after the PIN is set
        show_success_modal = False
        if request.session.get('pin_set_success_gif'):
            show_success_modal = True
            del request.session['pin_set_success_gif']  # Clear the flag after showing the GIF modal

        return render(request, 'home.html', {
            'show_pin_modal': False,  # Pin modal will not show if the pin is set
            'show_success_modal': show_success_modal,  # Show success GIF modal if flag is set
        })
    else:
        # If the user is not authenticated, render the home page without any PIN-related logic
        return render(request, 'home.html', {
            'show_pin_modal': False,
            'show_success_modal': False,
        })

