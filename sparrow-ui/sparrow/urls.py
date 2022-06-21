from django.urls import path
from .views import dashboard, forms, tables, identity, ocr, mapping, review, export

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('forms', forms, name='forms'),
    path('tables', tables, name='tables'),
    path('identity', identity, name='identity'),
    path('ocr', ocr, name='ocr'),
    path('mapping', mapping, name='mapping'),
    path('review', review, name='review'),
    path('export', export, name='export')
]