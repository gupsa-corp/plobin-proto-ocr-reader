#!/usr/bin/env python3
"""
Page-level content analysis and summarization
"""

import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import Counter


class PageAnalyzer:
    """페이지 레벨 콘텐츠 분석 및 요약"""

    def __init__(self):
        # 문서 타입 키워드
        self.document_type_keywords = {
            'invoice': ['invoice', 'bill', 'payment', 'due', '인보이스', '청구서', '지불'],
            'contract': ['contract', 'agreement', 'terms', '계약', '약정', '조건'],
            'report': ['report', 'analysis', 'summary', '보고서', '분석', '요약'],
            'letter': ['dear', 'sincerely', 'regards', '님께', '올림', '드림'],
            'form': ['form', 'application', 'request', '양식', '신청서', '요청서'],
            'receipt': ['receipt', 'purchased', 'sold', '영수증', '구매', '판매']
        }

        # 엔티티 추출 패턴
        self.entity_patterns = {
            'money': r'[\$₩¥€£]\s*[\d,]+\.?\d*|[\d,]+\.?\d*\s*[\$₩¥€£]',
            'date': r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4}',
            'invoice_number': r'(?:invoice|inv|bill|no)[-#:\s]*(\w+[-\w]*)',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'company': r'(?:company|corp|corporation|ltd|inc|co\.)\s*[^,\n]*|[^,\n]*\s*(?:company|corp|corporation|ltd|inc|co\.)',
        }

    def analyze_page(self, blocks: List[Dict[str, Any]], block_summaries: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """페이지 전체 분석 및 요약 생성"""
        if not blocks:
            return self._empty_page_summary()

        # 텍스트 통합
        full_text = ' '.join([block.get('text', '') for block in blocks])

        # 기본 분석
        document_type = self._classify_document_type(full_text, blocks)
        main_content = self._generate_main_content_summary(blocks, document_type)
        key_entities = self._extract_key_entities(full_text)
        content_sections = self._analyze_content_sections(blocks, block_summaries)
        quality_metrics = self._calculate_quality_metrics(blocks)

        # 언어 분석
        language_distribution = self._analyze_language_distribution(blocks)

        # 구조적 분석
        structural_analysis = self._analyze_structure(blocks)

        return {
            'document_type': document_type,
            'main_content': main_content,
            'key_entities': key_entities,
            'content_sections': content_sections,
            'quality_metrics': quality_metrics,
            'language_distribution': language_distribution,
            'structural_analysis': structural_analysis,
            'total_blocks': len(blocks),
            'total_characters': len(full_text),
            'analyzed_at': datetime.now().isoformat()
        }

    def _classify_document_type(self, full_text: str, blocks: List[Dict[str, Any]]) -> str:
        """문서 타입 분류"""
        text_lower = full_text.lower()

        # 키워드 기반 점수 계산
        type_scores = {}
        for doc_type, keywords in self.document_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[doc_type] = score

        # 구조적 특성 고려
        has_table_structure = any('table' in block.get('block_type', '') for block in blocks)
        has_money_amounts = bool(re.search(self.entity_patterns['money'], full_text))
        has_dates = bool(re.search(self.entity_patterns['date'], full_text))

        # 인보이스 특별 검증
        if (has_money_amounts and has_dates and
            any(keyword in text_lower for keyword in ['total', 'amount', 'due', '합계', '총액'])):
            type_scores['invoice'] = type_scores.get('invoice', 0) + 3

        # 가장 높은 점수의 타입 반환
        if type_scores:
            return max(type_scores, key=type_scores.get)

        return 'mixed'

    def _generate_main_content_summary(self, blocks: List[Dict[str, Any]], document_type: str) -> str:
        """주요 콘텐츠 요약 생성"""
        # 중요한 블록들을 찾아서 요약 생성
        important_texts = []

        for block in blocks[:5]:  # 상위 5개 블록 우선 고려
            text = block.get('text', '').strip()
            confidence = block.get('confidence', 0.0)

            if confidence > 0.8 and len(text) > 5:
                important_texts.append(text)

        if not important_texts:
            return "No clear content summary available"

        # 문서 타입별 요약 전략
        if document_type == 'invoice':
            return self._summarize_invoice(important_texts)
        elif document_type == 'contract':
            return self._summarize_contract(important_texts)
        else:
            # 일반적인 요약
            return '. '.join(important_texts[:3])[:200] + ('...' if len(' '.join(important_texts[:3])) > 200 else '')

    def _summarize_invoice(self, texts: List[str]) -> str:
        """인보이스 요약"""
        summary_parts = []

        # 회사명 찾기
        for text in texts:
            if any(keyword in text.lower() for keyword in ['company', 'corp', 'ltd', '회사']):
                summary_parts.append(f"Invoice from {text}")
                break

        # 서비스/상품 찾기
        for text in texts:
            if any(keyword in text.lower() for keyword in ['service', 'development', 'consulting', '서비스', '개발']):
                summary_parts.append(f"for {text.lower()}")
                break

        return ' '.join(summary_parts) if summary_parts else f"Invoice document - {texts[0][:100]}..."

    def _summarize_contract(self, texts: List[str]) -> str:
        """계약서 요약"""
        return f"Contract document - {texts[0][:100]}..." if texts else "Contract document"

    def _extract_key_entities(self, full_text: str) -> Dict[str, List[str]]:
        """주요 엔티티 추출"""
        entities = {
            'companies': [],
            'dates': [],
            'amounts': [],
            'emails': [],
            'phones': [],
            'invoice_numbers': []
        }

        # 금액 추출
        money_matches = re.findall(self.entity_patterns['money'], full_text, re.IGNORECASE)
        entities['amounts'] = list(set(money_matches))[:5]  # 최대 5개

        # 날짜 추출
        date_matches = re.findall(self.entity_patterns['date'], full_text)
        entities['dates'] = list(set(date_matches))[:5]

        # 이메일 추출
        email_matches = re.findall(self.entity_patterns['email'], full_text, re.IGNORECASE)
        entities['emails'] = list(set(email_matches))[:3]

        # 전화번호 추출
        phone_matches = re.findall(self.entity_patterns['phone'], full_text)
        entities['phones'] = [match[0] if isinstance(match, tuple) else match for match in phone_matches][:3]

        # 인보이스 번호 추출
        invoice_matches = re.findall(self.entity_patterns['invoice_number'], full_text, re.IGNORECASE)
        entities['invoice_numbers'] = list(set(invoice_matches))[:3]

        # 회사명 추출 (간단한 휴리스틱)
        company_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Company|Corp|Corporation|Ltd|Inc|Co\.))',
            r'([가-힣]+\s*(?:회사|주식회사|기업|코퍼레이션))'
        ]

        for pattern in company_patterns:
            company_matches = re.findall(pattern, full_text)
            entities['companies'].extend(company_matches)

        entities['companies'] = list(set(entities['companies']))[:3]

        return entities

    def _analyze_content_sections(self, blocks: List[Dict[str, Any]], block_summaries: List[Dict[str, Any]] = None) -> Dict[str, int]:
        """콘텐츠 섹션 분석"""
        sections = {
            'title': 0,
            'header': 0,
            'body': 0,
            'table': 0,
            'footer': 0,
            'other': 0
        }

        if block_summaries:
            # 블록 요약이 있으면 활용
            for summary in block_summaries:
                content_type = summary.get('content_type', 'other')
                if content_type in sections:
                    sections[content_type] += 1
                else:
                    sections['other'] += 1
        else:
            # 블록 타입 기반 추정
            for block in blocks:
                block_type = block.get('block_type', 'other')
                if block_type in sections:
                    sections[block_type] += 1
                else:
                    sections['other'] += 1

        return sections

    def _calculate_quality_metrics(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """품질 메트릭 계산"""
        if not blocks:
            return {'overall_confidence': 0.0, 'readability': 'unknown', 'completeness': 'empty'}

        # 전체 신뢰도
        confidences = [block.get('confidence', 0.0) for block in blocks]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # 가독성 평가
        avg_text_length = sum(len(block.get('text', '')) for block in blocks) / len(blocks)
        if avg_text_length > 20:
            readability = 'high'
        elif avg_text_length > 10:
            readability = 'medium'
        else:
            readability = 'low'

        # 완성도 평가
        high_confidence_blocks = [b for b in blocks if b.get('confidence', 0.0) > 0.9]
        completeness_ratio = len(high_confidence_blocks) / len(blocks) if blocks else 0.0

        if completeness_ratio > 0.8:
            completeness = 'complete'
        elif completeness_ratio > 0.6:
            completeness = 'mostly_complete'
        elif completeness_ratio > 0.3:
            completeness = 'partial'
        else:
            completeness = 'incomplete'

        return {
            'overall_confidence': round(overall_confidence, 3),
            'readability': readability,
            'completeness': completeness,
            'high_confidence_blocks': len(high_confidence_blocks),
            'low_confidence_blocks': len([b for b in blocks if b.get('confidence', 0.0) < 0.7])
        }

    def _analyze_language_distribution(self, blocks: List[Dict[str, Any]]) -> Dict[str, float]:
        """언어 분포 분석"""
        korean_pattern = r'[가-힣]'
        english_pattern = r'[A-Za-z]'

        total_chars = 0
        korean_chars = 0
        english_chars = 0

        for block in blocks:
            text = block.get('text', '')
            total_chars += len(text)
            korean_chars += len(re.findall(korean_pattern, text))
            english_chars += len(re.findall(english_pattern, text))

        if total_chars == 0:
            return {'korean': 0.0, 'english': 0.0, 'other': 0.0}

        korean_ratio = korean_chars / total_chars
        english_ratio = english_chars / total_chars
        other_ratio = 1.0 - korean_ratio - english_ratio

        return {
            'korean': round(korean_ratio, 3),
            'english': round(english_ratio, 3),
            'other': round(other_ratio, 3)
        }

    def _analyze_structure(self, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """구조적 분석"""
        # 블록 위치 분석 (bbox 기반)
        y_positions = []
        for block in blocks:
            bbox = block.get('bbox', [])
            if bbox and len(bbox) >= 2:
                # bbox는 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형태
                y_pos = bbox[0][1] if len(bbox[0]) >= 2 else 0
                y_positions.append(y_pos)

        # 상하좌우 분포
        structure_info = {
            'has_header': False,
            'has_footer': False,
            'column_layout': 'single',
            'text_alignment': 'mixed'
        }

        if y_positions:
            y_positions.sort()
            # 상위 20%를 헤더로, 하위 20%를 푸터로 간주
            header_threshold = y_positions[int(len(y_positions) * 0.2)] if len(y_positions) > 5 else y_positions[0]
            footer_threshold = y_positions[int(len(y_positions) * 0.8)] if len(y_positions) > 5 else y_positions[-1]

            structure_info['has_header'] = any(y <= header_threshold for y in y_positions[:3])
            structure_info['has_footer'] = any(y >= footer_threshold for y in y_positions[-3:])

        return structure_info

    def _empty_page_summary(self) -> Dict[str, Any]:
        """빈 페이지에 대한 기본 요약"""
        return {
            'document_type': 'empty',
            'main_content': 'No content available',
            'key_entities': {},
            'content_sections': {},
            'quality_metrics': {
                'overall_confidence': 0.0,
                'readability': 'unknown',
                'completeness': 'empty'
            },
            'language_distribution': {'korean': 0.0, 'english': 0.0, 'other': 0.0},
            'structural_analysis': {},
            'total_blocks': 0,
            'total_characters': 0,
            'analyzed_at': datetime.now().isoformat()
        }