from django.shortcuts import render


def dashboard(request):
    return render(request, 'sparrow/dashboard.html')


def forms(request):
    return render(request, 'sparrow/forms.html')


def tables(request):
    return render(request, 'sparrow/tables.html')


def identity(request):
    return render(request, 'sparrow/identity.html')


def ocr(request):
    return render(request, 'sparrow/ocr.html')


def mapping(request):
    return render(request, 'sparrow/mapping.html')


def review(request):
    return render(request, 'sparrow/review.html')


def export(request):
    return render(request, 'sparrow/export.html')
