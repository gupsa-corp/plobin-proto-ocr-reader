"""
Requests 앱의 URL 설정
"""
from django.urls import path
from .views import RequestListView, RequestDetailView

app_name = 'requests'

urlpatterns = [
    path('requests/', RequestListView.as_view(), name='list'),
    path('requests/<uuid:request_id>/', RequestDetailView.as_view(), name='detail'),
]
