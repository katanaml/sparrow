from django.urls import path
from .views import dashboard, document, expense, identity, upload, mapping, setup, export, training, evaluation, \
    summary, passwordreset, profilelock

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('document', document, name='document'),
    path('expense', expense, name='expense'),
    path('identity', identity, name='identity'),
    path('upload', upload, name='upload'),
    path('mapping', mapping, name='mapping'),
    path('setup', setup, name='setup'),
    path('export', export, name='export'),
    path('training', training, name='training'),
    path('evaluation', evaluation, name='evaluation'),
    path('summary', summary, name='summary'),
    path('passwordreset', passwordreset, name='passwordreset'),
    path('profilelock', profilelock, name='profilelock')
]
