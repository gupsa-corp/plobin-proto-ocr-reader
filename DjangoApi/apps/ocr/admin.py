"""
OCR 앱의 Django Admin 설정
"""
from django.contrib import admin
from .models import ProcessingRequest, PageResult


@admin.register(ProcessingRequest)
class ProcessingRequestAdmin(admin.ModelAdmin):
    """처리 요청 관리"""
    list_display = [
        'id', 'original_filename', 'file_type', 'status',
        'total_pages', 'processing_time', 'created_at'
    ]
    list_filter = ['status', 'file_type', 'created_at']
    search_fields = ['original_filename', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'completed_at',
        'processing_time', 'error_message'
    ]
    ordering = ['-created_at']


@admin.register(PageResult)
class PageResultAdmin(admin.ModelAdmin):
    """페이지 결과 관리"""
    list_display = [
        'id', 'request', 'page_number', 'total_blocks',
        'confidence_avg', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['request__original_filename']
    readonly_fields = ['created_at']
    ordering = ['request', 'page_number']
