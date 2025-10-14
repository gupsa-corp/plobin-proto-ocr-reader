"""
OCR 앱의 데이터 모델
"""
from django.db import models
import uuid


class ProcessingRequest(models.Model):
    """OCR 처리 요청 모델"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # UUID 기반 ID (v7 호환)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 파일 정보
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10)  # 'image', 'pdf'
    file_size = models.IntegerField()  # bytes

    # 요청 정보
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # 처리 설정
    merge_blocks = models.BooleanField(default=True)
    merge_threshold = models.IntegerField(default=30)
    create_sections = models.BooleanField(default=False)
    build_hierarchy_tree = models.BooleanField(default=False)

    # 처리 결과
    total_pages = models.IntegerField(default=0)
    processing_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'ocr_processing_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"


class PageResult(models.Model):
    """페이지별 OCR 결과 모델"""

    request = models.ForeignKey(
        ProcessingRequest,
        on_delete=models.CASCADE,
        related_name='pages'
    )
    page_number = models.IntegerField()

    # 페이지 정보
    width = models.IntegerField()
    height = models.IntegerField()

    # 블록 통계
    total_blocks = models.IntegerField(default=0)
    confidence_avg = models.FloatField(null=True, blank=True)

    # 파일 경로 (상대 경로)
    original_image_path = models.CharField(max_length=500)
    visualization_path = models.CharField(max_length=500, blank=True, null=True)
    result_json_path = models.CharField(max_length=500)

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ocr_page_results'
        ordering = ['request', 'page_number']
        unique_together = [['request', 'page_number']]
        indexes = [
            models.Index(fields=['request', 'page_number']),
        ]

    def __str__(self):
        return f"Page {self.page_number} of {self.request.original_filename}"
