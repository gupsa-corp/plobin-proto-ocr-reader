"""
OCR 앱의 시리얼라이저
"""
from rest_framework import serializers
from .models import ProcessingRequest, PageResult


class BlockInfoSerializer(serializers.Serializer):
    """블록 정보 시리얼라이저"""
    text = serializers.CharField()
    confidence = serializers.FloatField()
    bbox = serializers.ListField(child=serializers.ListField())
    block_type = serializers.CharField()


class ProcessingResultSerializer(serializers.Serializer):
    """OCR 처리 결과 시리얼라이저"""
    request_id = serializers.UUIDField()
    status = serializers.CharField()
    original_filename = serializers.CharField()
    file_type = serializers.CharField()
    file_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    processing_time = serializers.FloatField()
    processing_url = serializers.CharField()


class ProcessingRequestSerializer(serializers.ModelSerializer):
    """처리 요청 시리얼라이저"""

    class Meta:
        model = ProcessingRequest
        fields = [
            'id', 'original_filename', 'file_type', 'file_size',
            'description', 'status', 'merge_blocks', 'merge_threshold',
            'create_sections', 'build_hierarchy_tree', 'total_pages',
            'processing_time', 'error_message', 'created_at',
            'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'status', 'processing_time', 'error_message',
            'created_at', 'updated_at', 'completed_at'
        ]


class PageResultSerializer(serializers.ModelSerializer):
    """페이지 결과 시리얼라이저"""

    class Meta:
        model = PageResult
        fields = [
            'id', 'page_number', 'width', 'height',
            'total_blocks', 'confidence_avg',
            'original_image_path', 'visualization_path',
            'result_json_path', 'created_at'
        ]
        read_only_fields = fields


class HealthCheckSerializer(serializers.Serializer):
    """헬스 체크 시리얼라이저"""
    status = serializers.CharField()
    gpu_available = serializers.BooleanField()
    supported_languages = serializers.ListField(child=serializers.CharField())
    version = serializers.CharField()


class ServerStatsSerializer(serializers.Serializer):
    """서버 통계 시리얼라이저"""
    start_time = serializers.DateTimeField()
    uptime_seconds = serializers.FloatField()
    total_requests = serializers.IntegerField()
    total_images_processed = serializers.IntegerField()
    total_pdfs_processed = serializers.IntegerField()
    total_blocks_extracted = serializers.IntegerField()
    total_processing_time = serializers.FloatField()
    average_processing_time = serializers.FloatField()
    last_request_time = serializers.DateTimeField(allow_null=True)
    errors = serializers.IntegerField()
