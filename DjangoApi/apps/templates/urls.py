"""
Templates 앱의 URL 설정
"""
from django.urls import path
from .views import TemplateListView

app_name = 'templates'

urlpatterns = [
    path('templates/', TemplateListView.as_view(), name='list'),
]
