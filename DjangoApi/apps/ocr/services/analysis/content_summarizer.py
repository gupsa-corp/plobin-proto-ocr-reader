#!/usr/bin/env python3
"""
Content summarization orchestrator
"""

from typing import Dict, List, Any
from .block_analyzer import BlockAnalyzer
from .page_analyzer import PageAnalyzer


class ContentSummarizer:
    """콘텐츠 요약 통합 관리자"""

    def __init__(self):
        self.block_analyzer = BlockAnalyzer()
        self.page_analyzer = PageAnalyzer()

    def create_comprehensive_summary(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """종합적인 콘텐츠 요약 생성"""
        # 1. 블록별 요약 생성
        block_summaries = self.block_analyzer.analyze_blocks_batch(blocks)

        # 2. 페이지 전체 요약 생성
        page_summary = self.page_analyzer.analyze_page(blocks, block_summaries)

        # 3. 통합 요약 구성
        comprehensive_summary = {
            'page_summary': page_summary,
            'block_summaries': block_summaries,
            'insights': self._generate_insights(blocks, block_summaries, page_summary),
            'recommendations': self._generate_recommendations(page_summary)
        }

        return comprehensive_summary

    def _generate_insights(self, blocks: List[Dict[str, Any]],
                          block_summaries: List[Dict[str, Any]],
                          page_summary: Dict[str, Any]) -> List[str]:
        """데이터 기반 인사이트 생성"""
        insights = []

        # 신뢰도 관련 인사이트
        quality_metrics = page_summary.get('quality_metrics', {})
        overall_confidence = quality_metrics.get('overall_confidence', 0.0)

        if overall_confidence > 0.95:
            insights.append("매우 높은 OCR 정확도로 신뢰할 수 있는 결과입니다.")
        elif overall_confidence < 0.7:
            insights.append("일부 텍스트의 OCR 정확도가 낮아 수동 검토가 필요할 수 있습니다.")

        # 콘텐츠 타입 관련 인사이트
        doc_type = page_summary.get('document_type', '')
        if doc_type == 'invoice':
            key_entities = page_summary.get('key_entities', {})
            amounts = key_entities.get('amounts', [])
            if len(amounts) > 1:
                insights.append(f"총 {len(amounts)}개의 금액이 발견되었습니다.")

        # 언어 분포 관련 인사이트
        lang_dist = page_summary.get('language_distribution', {})
        korean_ratio = lang_dist.get('korean', 0.0)
        english_ratio = lang_dist.get('english', 0.0)

        if korean_ratio > 0.7:
            insights.append("주로 한국어 문서입니다.")
        elif english_ratio > 0.7:
            insights.append("주로 영어 문서입니다.")
        elif korean_ratio > 0.3 and english_ratio > 0.3:
            insights.append("한국어와 영어가 혼재된 다국어 문서입니다.")

        # 중요 블록 관련 인사이트
        critical_blocks = [s for s in block_summaries if s.get('estimated_importance') == 'critical']
        if len(critical_blocks) > 3:
            insights.append(f"{len(critical_blocks)}개의 중요한 정보 블록이 식별되었습니다.")

        return insights

    def _generate_recommendations(self, page_summary: Dict[str, Any]) -> List[str]:
        """처리 권장사항 생성"""
        recommendations = []

        quality_metrics = page_summary.get('quality_metrics', {})
        overall_confidence = quality_metrics.get('overall_confidence', 0.0)
        low_confidence_blocks = quality_metrics.get('low_confidence_blocks', 0)

        # 품질 개선 권장사항
        if overall_confidence < 0.8:
            recommendations.append("이미지 해상도를 높이거나 더 선명한 스캔을 사용하면 OCR 정확도가 향상될 수 있습니다.")

        if low_confidence_blocks > 5:
            recommendations.append("신뢰도가 낮은 블록들에 대해 수동 검토를 권장합니다.")

        # 문서 타입별 권장사항
        doc_type = page_summary.get('document_type', '')
        if doc_type == 'invoice':
            recommendations.append("인보이스 데이터를 회계 시스템으로 자동 가져오기가 가능합니다.")
        elif doc_type == 'contract':
            recommendations.append("계약서의 주요 조항들을 별도로 추출하여 관리하는 것을 권장합니다.")

        # 구조적 권장사항
        content_sections = page_summary.get('content_sections', {})
        table_count = content_sections.get('table', 0)
        if table_count > 2:
            recommendations.append("테이블 데이터를 스프레드시트 형태로 내보내기를 고려해보세요.")

        return recommendations

    def create_block_summary(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """단일 블록 요약 생성"""
        return self.block_analyzer.analyze_block(block)

    def create_page_summary(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """페이지 요약 생성"""
        return self.page_analyzer.analyze_page(blocks)