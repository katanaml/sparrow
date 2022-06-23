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


def review(request):
    return render(request, 'sparrow/review.html')


def export(request):
    return render(request, 'sparrow/export.html')
