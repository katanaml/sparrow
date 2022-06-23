from django.urls import path
from .views import dashboard, document, expense, identity, upload, mapping, review, export

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('document', document, name='document'),
    path('expense', expense, name='expense'),
    path('identity', identity, name='identity'),
    path('upload', upload, name='upload'),
    path('mapping', mapping, name='mapping'),
    path('review', review, name='review'),
    path('export', export, name='export')
]