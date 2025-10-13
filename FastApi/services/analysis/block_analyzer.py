#!/usr/bin/env python3
"""
Block-level content analysis and summarization
"""

import re
from typing import Dict, List, Any
from datetime import datetime


class BlockAnalyzer:
    """블록 레벨 콘텐츠 분석 및 요약"""

    def __init__(self):
        # 패턴 정의
        self.patterns = {
            'money': r'[\$₩¥€£]\s*[\d,]+\.?\d*|[\d,]+\.?\d*\s*[\$₩¥€£]',
            'date': r'\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{4}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            'number': r'\b\d+\.?\d*\b',
            'korean': r'[가-힣]+',
            'english': r'[A-Za-z]+',
        }

        # 중요도 키워드
        self.critical_keywords = [
            'invoice', 'total', 'amount', 'due', 'payment', 'contract',
            '인보이스', '총액', '합계', '지불', '계약', '청구서'
        ]

        self.important_keywords = [
            'company', 'client', 'date', 'number', 'address', 'tax',
            '회사', '고객', '날짜', '번호', '주소', '세금'
        ]

    def analyze_block(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """개별 블록 분석 및 요약 생성"""
        text = block.get('text', '').strip()
        confidence = block.get('confidence', 0.0)

        if not text:
            return self._empty_summary()

        # 기본 분석
        content_type = self._classify_content_type(text)
        language = self._detect_language(text)
        text_preview = text[:30] + ('...' if len(text) > 30 else '')
        keywords = self._extract_keywords(text)
        confidence_level = self._get_confidence_level(confidence)
        importance = self._estimate_importance(text, content_type)

        # 특수 콘텐츠 검출
        contains_numbers = bool(re.search(self.patterns['number'], text))
        contains_dates = bool(re.search(self.patterns['date'], text))
        contains_money = bool(re.search(self.patterns['money'], text))
        contains_email = bool(re.search(self.patterns['email'], text))
        contains_phone = bool(re.search(self.patterns['phone'], text))

        return {
            'content_type': content_type,
            'language': language,
            'text_preview': text_preview,
            'keywords': keywords,
            'confidence_level': confidence_level,
            'estimated_importance': importance,
            'contains_numbers': contains_numbers,
            'contains_dates': contains_dates,
            'contains_money': contains_money,
            'contains_email': contains_email,
            'contains_phone': contains_phone,
            'text_length': len(text),
            'word_count': len(text.split()),
            'analyzed_at': datetime.now().isoformat()
        }

    def _classify_content_type(self, text: str) -> str:
        """텍스트 콘텐츠 타입 분류"""
        text_lower = text.lower()

        # 제목/헤더 패턴
        if (len(text) < 50 and
            (any(word in text_lower for word in ['invoice', 'contract', 'report', '인보이스', '계약서', '보고서']) or
             text.isupper() or
             re.match(r'^[A-Z][^a-z]*$', text))):
            return 'title'

        # 헤더 패턴
        if (len(text) < 100 and
            any(word in text_lower for word in ['from:', 'to:', 'date:', 'subject:', '발신:', '수신:', '날짜:', '제목:'])):
            return 'header'

        # 테이블 패턴
        if (('\t' in text or '|' in text) or
            (contains_numbers := bool(re.search(r'\d+', text))) and len(text.split()) >= 3):
            return 'table'

        # 숫자 중심 콘텐츠
        if re.search(self.patterns['money'], text) or re.search(r'^\d+\.?\d*$', text.strip()):
            return 'number'

        # 주소 패턴
        if any(word in text_lower for word in ['street', 'avenue', 'road', 'city', '시', '구', '동', '로', '길']):
            return 'address'

        # 날짜 패턴
        if re.search(self.patterns['date'], text):
            return 'date'

        # 이메일
        if re.search(self.patterns['email'], text):
            return 'email'

        # 전화번호
        if re.search(self.patterns['phone'], text):
            return 'phone'

        # 긴 텍스트는 본문
        if len(text) > 100:
            return 'body'

        return 'other'

    def _detect_language(self, text: str) -> str:
        """언어 검출"""
        korean_chars = len(re.findall(self.patterns['korean'], text))
        english_chars = len(re.findall(self.patterns['english'], text))

        if korean_chars > english_chars * 2:
            return 'korean'
        elif english_chars > korean_chars * 2:
            return 'english'
        elif korean_chars > 0 and english_chars > 0:
            return 'mixed'
        else:
            return 'other'

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """키워드 추출"""
        # 간단한 키워드 추출 (공백 기준 분할 후 필터링)
        words = re.findall(r'\b\w+\b', text.lower())

        # 불용어 제거 및 길이 필터링
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', '의', '이', '가', '을', '를', '에', '에서'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]

        # 빈도 기반 정렬 (간단한 구현)
        keyword_freq = {}
        for word in keywords:
            keyword_freq[word] = keyword_freq.get(word, 0) + 1

        # 상위 키워드 반환
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:max_keywords]]

    def _get_confidence_level(self, confidence: float) -> str:
        """신뢰도 레벨 분류"""
        if confidence >= 0.95:
            return 'high'
        elif confidence >= 0.8:
            return 'medium'
        else:
            return 'low'

    def _estimate_importance(self, text: str, content_type: str) -> str:
        """중요도 추정"""
        text_lower = text.lower()

        # 콘텐츠 타입 기반 기본 중요도
        type_importance = {
            'title': 'critical',
            'number': 'important',
            'date': 'important',
            'email': 'important',
            'phone': 'important',
            'address': 'important',
            'header': 'important',
            'table': 'normal',
            'body': 'normal',
            'other': 'low'
        }

        base_importance = type_importance.get(content_type, 'normal')

        # 키워드 기반 중요도 조정
        if any(keyword in text_lower for keyword in self.critical_keywords):
            return 'critical'
        elif any(keyword in text_lower for keyword in self.important_keywords):
            return 'important'

        return base_importance

    def _empty_summary(self) -> Dict[str, Any]:
        """빈 블록에 대한 기본 요약"""
        return {
            'content_type': 'empty',
            'language': 'unknown',
            'text_preview': '',
            'keywords': [],
            'confidence_level': 'low',
            'estimated_importance': 'low',
            'contains_numbers': False,
            'contains_dates': False,
            'contains_money': False,
            'contains_email': False,
            'contains_phone': False,
            'text_length': 0,
            'word_count': 0,
            'analyzed_at': datetime.now().isoformat()
        }

    def analyze_blocks_batch(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """여러 블록 일괄 분석"""
        return [self.analyze_block(block) for block in blocks]