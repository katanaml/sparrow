from django.shortcuts import render


def dashboard(request):
    return render(request, 'sparrow/dashboard.html')


def forms(request):
    return render(request, 'sparrow/forms.html')
