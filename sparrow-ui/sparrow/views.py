from django.shortcuts import render


def dashboard(request):
    return render(request, 'sparrow/dashboard.html')


def document(request):
    return render(request, 'sparrow/document.html')


def expense(request):
    return render(request, 'sparrow/expense.html')


def identity(request):
    return render(request, 'sparrow/identity.html')


def upload(request):
    return render(request, 'sparrow/upload.html')


def mapping(request):
    return render(request, 'sparrow/mapping.html')


def setup(request):
    return render(request, 'sparrow/setup.html')


def export(request):
    return render(request, 'sparrow/export.html')


def training(request):
    return render(request, 'sparrow/training.html')


def evaluation(request):
    return render(request, 'sparrow/evaluation.html')


def summary(request):
    return render(request, 'sparrow/summary.html')


def passwordreset(request):
    return render(request, 'sparrow/passwordreset.html')


def profilelock(request):
    return render(request, 'sparrow/profilelock.html')
