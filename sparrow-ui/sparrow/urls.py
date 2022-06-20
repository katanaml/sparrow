from django.urls import path
from .views import dashboard, forms

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('forms', forms, name='forms')
]