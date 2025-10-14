"""
OCR 앱의 API 뷰
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

import tempfile
import shutil
import time
import os
from pathlib import Path
from datetime import datetime

from .serializers import (
    ProcessingResultSerializer,
    HealthCheckSerializer,
    ServerStatsSerializer,
    ProcessingRequestSerializer
)
from .services.ocr.extraction import DocumentBlockExtractor, crop_all_blocks
from .services.pdf import PDFToImageProcessor
from .services.file.storage import RequestStorage
from .models import ProcessingRequest


class OCRProcessorMixin:
    """OCR 처리 공통 기능 믹스인"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._extractor = None
        self._pdf_processor = None
        self._storage = None
        self._stats = {
            "start_time": timezone.now(),
            "total_requests": 0,
            "total_images_processed": 0,
            "total_pdfs_processed": 0,
            "total_blocks_extracted": 0,
            "total_processing_time": 0.0,
            "last_request_time": None,
            "errors": 0
        }

    @property
    def extractor(self):
        """OCR 추출기 게터 (지연 초기화)"""
        if self._extractor is None:
            ocr_config = settings.OCR_SETTINGS
            self._extractor = DocumentBlockExtractor(
                use_gpu=ocr_config.get('USE_GPU', True),
                lang=ocr_config.get('LANGUAGE', 'ko'),
                use_korean_enhancement=ocr_config.get('USE_KOREAN_ENHANCEMENT', False),
                use_ppocrv5=ocr_config.get('USE_PPOCRV5', False)
            )
        return self._extractor

    @property
    def pdf_processor(self):
        """PDF 처리기 게터 (지연 초기화)"""
        if self._pdf_processor is None:
            self._pdf_processor = PDFToImageProcessor()
        return self._pdf_processor

    @property
    def storage(self):
        """스토리지 게터"""
        if self._storage is None:
            self._storage = RequestStorage(str(settings.OUTPUT_DIR))
        return self._storage

    def update_stats(self, **kwargs):
        """통계 업데이트"""
        for key, value in kwargs.items():
            if key in self._stats:
                if isinstance(self._stats[key], (int, float)):
                    self._stats[key] += value
                else:
                    self._stats[key] = value


class ProcessImageView(OCRProcessorMixin, APIView):
    """이미지 파일 OCR 처리 API"""

    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="이미지 파일 OCR 처리",
        description="이미지 파일을 업로드하여 OCR 처리를 수행합니다.",
        parameters=[
            OpenApiParameter(
                name='merge_blocks',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='인접한 블록들을 병합하여 문장 단위로 그룹화',
                default=True
            ),
            OpenApiParameter(
                name='merge_threshold',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='블록 병합 임계값 (픽셀 단위)',
                default=30
            ),
            OpenApiParameter(
                name='create_sections',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='블록들을 논리적 섹션으로 그룹화 (header, body, footer 등)',
                default=False
            ),
            OpenApiParameter(
                name='build_hierarchy_tree',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='블록 간 계층 구조 구축 (포함 관계)',
                default=False
            ),
        ],
        responses={200: ProcessingResultSerializer}
    )
    def post(self, request):
        """이미지 파일 OCR 처리"""
        start_time = time.time()
        self.update_stats(total_requests=1, last_request_time=timezone.now())

        # 파라미터 파싱
        merge_blocks = request.query_params.get('merge_blocks', 'true').lower() == 'true'
        merge_threshold = int(request.query_params.get('merge_threshold', 30))
        create_sections = request.query_params.get('create_sections', 'false').lower() == 'true'
        build_hierarchy_tree = request.query_params.get('build_hierarchy_tree', 'false').lower() == 'true'

        # 파일 검증
        file = request.FILES.get('file')
        if not file:
            self.update_stats(errors=1)
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.content_type.startswith('image/'):
            self.update_stats(errors=1)
            return Response(
                {"error": "File must be an image"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tmp_path = None
        try:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.name).suffix) as tmp_file:
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # OCR 처리
            result = self.extractor.extract_blocks(
                tmp_path,
                merge_blocks=merge_blocks,
                merge_threshold=merge_threshold,
                create_sections=create_sections,
                build_hierarchy_tree=build_hierarchy_tree
            )
            blocks = result.get('blocks', [])

            if not blocks:
                return Response({
                    "request_id": None,
                    "status": "completed",
                    "original_filename": file.name,
                    "file_type": "image",
                    "file_size": file.size,
                    "total_pages": 1,
                    "total_blocks": 0,
                    "processing_time": round(time.time() - start_time, 3),
                })

            # 통계 업데이트
            processing_time = time.time() - start_time
            self.update_stats(
                total_images_processed=1,
                total_blocks_extracted=len(blocks),
                total_processing_time=processing_time
            )

            # RequestStorage를 사용해서 저장
            request_id = self.storage.create_request(
                file.name,
                "image",
                file.size,
                total_pages=1
            )

            # 메타데이터 준비
            ocr_metadata = {}
            if create_sections and 'sections' in result:
                ocr_metadata['sections'] = result['sections']
                ocr_metadata['section_summary'] = result.get('section_summary', {})

            if build_hierarchy_tree and 'hierarchical_blocks' in result:
                ocr_metadata['hierarchical_blocks'] = result['hierarchical_blocks']
                ocr_metadata['hierarchy_statistics'] = result.get('hierarchy_statistics', {})

            # 페이지 결과 저장
            self.storage.save_page_result(
                request_id,
                1,
                blocks,
                processing_time,
                metadata=ocr_metadata if ocr_metadata else None
            )

            # 원본 이미지 저장
            if tmp_path and os.path.exists(tmp_path):
                try:
                    self.storage.save_original_image(request_id, 1, tmp_path)
                except Exception as e:
                    print(f"원본 이미지 저장 실패: {e}")

            # 블록별 이미지 크롭 및 저장
            if tmp_path and os.path.exists(tmp_path) and blocks:
                try:
                    cropped_blocks = crop_all_blocks(tmp_path, blocks, padding=5)
                    self.storage.save_block_images(request_id, 1, cropped_blocks)
                except Exception as e:
                    print(f"블록 이미지 저장 실패: {e}")

            # 시각화 저장
            if tmp_path and os.path.exists(tmp_path):
                try:
                    viz_path = settings.OUTPUT_DIR / request_id / "pages" / "001" / "visualization.png"
                    self.extractor.visualize_blocks(tmp_path, {'blocks': blocks}, str(viz_path))
                except Exception as e:
                    print(f"시각화 생성 실패: {e}")

            # 요청 완료 처리
            avg_confidence = sum(b['confidence'] for b in blocks) / len(blocks)
            summary_data = {
                "total_pages": 1,
                "total_blocks": len(blocks),
                "overall_confidence": round(avg_confidence, 3),
                "processing_time": round(processing_time, 3),
                "completed_at": timezone.now().isoformat(),
                "sections_created": create_sections,
                "hierarchy_built": build_hierarchy_tree
            }

            if create_sections and 'sections' in result:
                summary_data['total_sections'] = len(result['sections'])
                summary_data['section_summary'] = result.get('section_summary', {})

            if build_hierarchy_tree and 'hierarchy_statistics' in result:
                summary_data['hierarchy_statistics'] = result['hierarchy_statistics']

            self.storage.complete_request(request_id, summary_data)

            response_data = {
                "request_id": request_id,
                "status": "completed",
                "original_filename": file.name,
                "file_type": "image",
                "file_size": file.size,
                "total_pages": 1,
                "processing_time": round(processing_time, 3),
                "processing_url": f"/api/requests/{request_id}"
            }

            serializer = ProcessingResultSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)

        except Exception as e:
            self.update_stats(errors=1)
            return Response(
                {"error": f"Processing error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)


class HealthCheckView(APIView):
    """헬스 체크 API"""

    @extend_schema(
        summary="서버 헬스 체크",
        description="서버 상태 및 GPU 사용 가능 여부를 확인합니다.",
        responses={200: HealthCheckSerializer}
    )
    def get(self, request):
        """헬스 체크"""
        import torch

        data = {
            "status": "healthy",
            "gpu_available": torch.cuda.is_available(),
            "supported_languages": ["ko", "en", "ja", "zh", "90+ languages via Surya OCR"],
            "version": "2.0.0"
        }

        serializer = HealthCheckSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ProcessPDFView(OCRProcessorMixin, APIView):
    """PDF 파일 OCR 처리 API"""

    parser_classes = (MultiPartParser, FormParser)

    @extend_schema(
        summary="PDF 파일 OCR 처리",
        description="PDF 파일을 업로드하여 페이지별로 OCR 처리를 수행합니다.",
        parameters=[
            OpenApiParameter(
                name='merge_blocks',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='인접한 블록들을 병합하여 문장 단위로 그룹화',
                default=True
            ),
            OpenApiParameter(
                name='merge_threshold',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='블록 병합 임계값 (픽셀 단위)',
                default=30
            ),
            OpenApiParameter(
                name='create_sections',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='블록들을 논리적 섹션으로 그룹화',
                default=False
            ),
            OpenApiParameter(
                name='build_hierarchy_tree',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='블록 간 계층 구조 구축',
                default=False
            ),
        ],
        responses={200: ProcessingResultSerializer}
    )
    def post(self, request):
        """PDF 파일 OCR 처리"""
        start_time = time.time()
        self.update_stats(total_requests=1, last_request_time=timezone.now())

        # 파라미터 파싱
        merge_blocks = request.query_params.get('merge_blocks', 'true').lower() == 'true'
        merge_threshold = int(request.query_params.get('merge_threshold', 30))
        create_sections = request.query_params.get('create_sections', 'false').lower() == 'true'
        build_hierarchy_tree = request.query_params.get('build_hierarchy_tree', 'false').lower() == 'true'

        # 파일 검증
        file = request.FILES.get('file')
        if not file:
            self.update_stats(errors=1)
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if file.content_type != 'application/pdf':
            self.update_stats(errors=1)
            return Response(
                {"error": "File must be a PDF"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tmp_path = None
        temp_dir = None
        try:
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in file.chunks():
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # PDF를 이미지로 변환
            temp_dir = tempfile.mkdtemp()
            image_paths = self.pdf_processor.convert_pdf_to_images(tmp_path, temp_dir)
            total_pages = len(image_paths)

            # 요청 생성
            request_id = self.storage.create_request(
                file.name,
                "pdf",
                file.size,
                total_pages=total_pages
            )

            # 페이지별 처리
            all_pages_data = []
            total_blocks_count = 0
            total_confidence_sum = 0

            for i, image_path in enumerate(image_paths):
                page_num = i + 1
                page_start_time = time.time()

                # OCR 처리
                result = self.extractor.extract_blocks(
                    image_path,
                    merge_blocks=merge_blocks,
                    merge_threshold=merge_threshold,
                    create_sections=create_sections,
                    build_hierarchy_tree=build_hierarchy_tree
                )
                blocks = result.get('blocks', [])
                page_processing_time = time.time() - page_start_time

                # 메타데이터 준비
                ocr_metadata = {}
                if create_sections and 'sections' in result:
                    ocr_metadata['sections'] = result['sections']
                    ocr_metadata['section_summary'] = result.get('section_summary', {})

                if build_hierarchy_tree and 'hierarchical_blocks' in result:
                    ocr_metadata['hierarchical_blocks'] = result['hierarchical_blocks']
                    ocr_metadata['hierarchy_statistics'] = result.get('hierarchy_statistics', {})

                # 페이지 결과 저장
                self.storage.save_page_result(
                    request_id,
                    page_num,
                    blocks,
                    page_processing_time,
                    metadata=ocr_metadata if ocr_metadata else None
                )

                # 원본 이미지 저장
                try:
                    self.storage.save_original_image(request_id, page_num, image_path)
                except Exception as e:
                    print(f"페이지 {page_num} 원본 이미지 저장 실패: {e}")

                # 블록별 이미지 크롭 및 저장
                if blocks:
                    try:
                        cropped_blocks = crop_all_blocks(image_path, blocks, padding=5)
                        self.storage.save_block_images(request_id, page_num, cropped_blocks)
                    except Exception as e:
                        print(f"페이지 {page_num} 블록 이미지 저장 실패: {e}")

                # 시각화 저장
                if blocks:
                    try:
                        viz_path = settings.OUTPUT_DIR / request_id / "pages" / f"{page_num:03d}" / "visualization.png"
                        self.extractor.visualize_blocks(image_path, {'blocks': blocks}, str(viz_path))
                    except Exception as e:
                        print(f"페이지 {page_num} 시각화 생성 실패: {e}")

                # 통계 누적
                total_blocks_count += len(blocks)
                if blocks:
                    page_confidence = sum(b['confidence'] for b in blocks) / len(blocks)
                    total_confidence_sum += page_confidence
                    all_pages_data.append({
                        "page_number": page_num,
                        "total_blocks": len(blocks),
                        "average_confidence": round(page_confidence, 3),
                        "processing_time": round(page_processing_time, 3)
                    })
                else:
                    all_pages_data.append({
                        "page_number": page_num,
                        "total_blocks": 0,
                        "average_confidence": 0.0,
                        "processing_time": round(page_processing_time, 3)
                    })

            # 요청 완료 처리
            processing_time = time.time() - start_time
            pages_with_blocks = [p for p in all_pages_data if p["total_blocks"] > 0]
            overall_confidence = total_confidence_sum / max(len(pages_with_blocks), 1)

            summary_data = {
                "total_pages": total_pages,
                "total_blocks": total_blocks_count,
                "overall_confidence": round(overall_confidence, 3),
                "processing_time": round(processing_time, 3),
                "pages": all_pages_data,
                "completed_at": timezone.now().isoformat(),
                "sections_created": create_sections,
                "hierarchy_built": build_hierarchy_tree
            }
            self.storage.complete_request(request_id, summary_data)

            # 통계 업데이트
            self.update_stats(
                total_pdfs_processed=1,
                total_blocks_extracted=total_blocks_count,
                total_processing_time=processing_time
            )

            response_data = {
                "request_id": request_id,
                "status": "completed",
                "original_filename": file.name,
                "file_type": "pdf",
                "file_size": file.size,
                "total_pages": total_pages,
                "processing_time": round(processing_time, 3),
                "processing_url": f"/api/requests/{request_id}"
            }

            serializer = ProcessingResultSerializer(data=response_data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)

        except Exception as e:
            self.update_stats(errors=1)
            return Response(
                {"error": f"Processing error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


class ServerStatusView(OCRProcessorMixin, APIView):
    """서버 상태 API"""

    @extend_schema(
        summary="서버 상태 및 통계",
        description="서버 통계 및 처리 정보를 조회합니다.",
        responses={200: ServerStatsSerializer}
    )
    def get(self, request):
        """서버 상태 조회"""
        uptime = (timezone.now() - self._stats['start_time']).total_seconds()
        avg_processing_time = (
            self._stats['total_processing_time'] / self._stats['total_images_processed']
            if self._stats['total_images_processed'] > 0
            else 0
        )

        data = {
            **self._stats,
            "uptime_seconds": round(uptime, 2),
            "average_processing_time": round(avg_processing_time, 3)
        }

        serializer = ServerStatsSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
