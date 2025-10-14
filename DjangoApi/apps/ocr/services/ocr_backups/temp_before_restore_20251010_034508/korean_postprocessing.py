#!/usr/bin/env python3
"""
한글 OCR 결과 후처리 및 정확도 향상 모듈
"""

import re
import unicodedata
from typing import List, Dict, Tuple, Any
from difflib import SequenceMatcher


class KoreanTextPostProcessor:
    """한글 텍스트 OCR 결과 후처리기"""

    def __init__(self):
        # 한글 문자 패턴
        self.hangul_pattern = re.compile('[가-힣]+')
        self.korean_char_pattern = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]+')

        # 일반적인 OCR 오류 패턴 (한글 특화)
        self.common_errors = {
            # 자주 혼동되는 한글 문자들
            '스': ['ス', '人'],
            '인': ['ㅇㄴ', 'ㅏㄴ'],
            '의': ['ㄴㅏ', 'ㅗㅣ'],
            '에': ['ㅔ', 'ㅞ'],
            '를': ['ㄹㅡㄹ', 'ㄹㅏ'],
            '와': ['ㅗㅏ', '외'],
            '위': ['ㅟ', 'ㅗㅣ'],
            '여': ['ㅕ', 'ㅓ'],
            '로': ['ㄹㅗ', 'ㄹㅏ'],
            '기': ['ㄱㅣ', 'ㅂㅣ'],
            '다': ['ㄷㅏ', 'ㄱㅏ'],
            '마': ['ㅁㅏ', 'ㅂㅏ'],
            '바': ['ㅂㅏ', 'ㅁㅏ'],
            '사': ['ㅅㅏ', 'ㅊㅏ'],
            '아': ['ㅏ', 'ㅑ'],
            '자': ['ㅈㅏ', 'ㅊㅏ'],
            '차': ['ㅊㅏ', 'ㅈㅏ'],
            '카': ['ㅋㅏ', 'ㅂㅏ'],
            '타': ['ㅌㅏ', 'ㄷㅏ'],
            '파': ['ㅍㅏ', 'ㅂㅏ'],
            '하': ['ㅎㅏ', 'ㅂㅏ'],
        }

        # 숫자 관련 오류 패턴
        self.number_errors = {
            '0': ['O', 'o', '°', '〇'],
            '1': ['l', 'I', '|', '!'],
            '2': ['z', 'Z'],
            '3': ['з'],
            '4': ['А'],
            '5': ['S', 's'],
            '6': ['б', 'G'],
            '7': ['7'],
            '8': ['8', 'B'],
            '9': ['9', 'g']
        }

        # 영어 문자 오류 패턴
        self.english_errors = {
            'O': ['0', '〇'],
            'I': ['1', 'l', '|'],
            'S': ['5'],
            'G': ['6'],
            'B': ['8']
        }

        # 일반적인 한글 단어 (문맥 기반 보정용)
        self.common_korean_words = {
            # 일반적인 단어들
            '주식회사', '유한회사', '대표이사', '전화번호', '휴대폰',
            '주소', '서울', '부산', '대구', '인천', '광주', '대전', '울산',
            '경기도', '강원도', '충청북도', '충청남도', '전라북도', '전라남도',
            '경상북도', '경상남도', '제주도',
            '영수증', '거래명세서', '세금계산서', '송장', '계산서',
            '합계', '소계', '부가세', '공급가액', '총액',
            '현금', '카드', '계좌이체', '결제',
            '년', '월', '일', '시', '분', '초',
            '원', '달러', '엔', '유로',
            # 자주 사용되는 접사
            '에서', '에게', '에대한', '에의한', '으로', '로서', '로써',
            '입니다', '습니다', '하였습니다', '되었습니다'
        }

    def process_ocr_results(self, ocr_results: List[Dict[str, Any]],
                          confidence_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        OCR 결과 종합 후처리

        Args:
            ocr_results: OCR 결과 리스트
            confidence_threshold: 신뢰도 임계값

        Returns:
            후처리된 OCR 결과
        """
        processed_results = []

        for result in ocr_results:
            original_text = result.get('text', '')
            confidence = result.get('confidence', 0.0)

            # 1. 기본 정제
            cleaned_text = self._clean_basic_errors(original_text)

            # 2. 한글 문자 보정
            corrected_text = self._correct_korean_characters(cleaned_text)

            # 3. 숫자 및 영어 보정
            corrected_text = self._correct_numbers_and_english(corrected_text)

            # 4. 문맥 기반 보정 (낮은 신뢰도일 때)
            if confidence < confidence_threshold:
                corrected_text = self._context_based_correction(corrected_text)

            # 5. 최종 정제
            final_text = self._final_cleanup(corrected_text)

            # 결과 업데이트
            updated_result = result.copy()
            updated_result['text'] = final_text
            updated_result['original_text'] = original_text
            updated_result['was_corrected'] = original_text != final_text

            # 보정된 경우 신뢰도 조정
            if updated_result['was_corrected']:
                correction_penalty = 0.1  # 보정 시 신뢰도 10% 감소
                updated_result['confidence'] = max(0.0, confidence - correction_penalty)
                updated_result['correction_applied'] = True
            else:
                updated_result['correction_applied'] = False

            processed_results.append(updated_result)

        return processed_results

    def _clean_basic_errors(self, text: str) -> str:
        """기본적인 텍스트 정제"""
        if not text:
            return text

        # 유니코드 정규화
        text = unicodedata.normalize('NFC', text)

        # 불필요한 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()

        # 특수문자 정리 (한글, 영어, 숫자, 기본 특수문자만 유지)
        text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?()[\]{}"\'/-]', '', text)

        return text

    def _correct_korean_characters(self, text: str) -> str:
        """한글 문자 보정"""
        corrected_text = text

        # 일반적인 한글 오류 패턴 보정
        for correct_char, error_patterns in self.common_errors.items():
            for error_pattern in error_patterns:
                corrected_text = corrected_text.replace(error_pattern, correct_char)

        # 자모 분리 문제 해결
        corrected_text = self._fix_separated_jamo(corrected_text)

        return corrected_text

    def _fix_separated_jamo(self, text: str) -> str:
        """분리된 자모 결합"""
        # 분리된 자모를 찾아서 결합
        # 예: ㄱㅏ -> 가, ㄴㅏ -> 나
        jamo_pattern = re.compile(r'([ㄱ-ㅎ])([ㅏ-ㅣ])([ㄱ-ㅎ]?)')

        def combine_jamo(match):
            initial = match.group(1)
            medial = match.group(2)
            final = match.group(3) if match.group(3) else ''

            try:
                # 한글 음절 조합
                initial_code = ord(initial) - 0x1100
                medial_code = ord(medial) - 0x1161
                final_code = ord(final) - 0x11A7 if final else 0

                if 0 <= initial_code <= 18 and 0 <= medial_code <= 20 and 0 <= final_code <= 27:
                    combined_code = 0xAC00 + (initial_code * 21 + medial_code) * 28 + final_code
                    return chr(combined_code)
            except:
                pass

            return match.group(0)  # 실패시 원본 반환

        return jamo_pattern.sub(combine_jamo, text)

    def _correct_numbers_and_english(self, text: str) -> str:
        """숫자 및 영어 문자 보정"""
        corrected_text = text

        # 숫자 보정
        for correct_num, error_patterns in self.number_errors.items():
            for error_pattern in error_patterns:
                corrected_text = corrected_text.replace(error_pattern, correct_num)

        # 영어 문자 보정
        for correct_eng, error_patterns in self.english_errors.items():
            for error_pattern in error_patterns:
                corrected_text = corrected_text.replace(error_pattern, correct_eng)

        return corrected_text

    def _context_based_correction(self, text: str) -> str:
        """문맥 기반 보정"""
        # 일반적인 한글 단어와의 유사도 검사
        words = text.split()
        corrected_words = []

        for word in words:
            if self.korean_char_pattern.search(word):
                # 한글이 포함된 단어에 대해 유사도 검사
                best_match = self._find_best_word_match(word)
                corrected_words.append(best_match if best_match else word)
            else:
                corrected_words.append(word)

        return ' '.join(corrected_words)

    def _find_best_word_match(self, word: str, similarity_threshold: float = 0.8) -> str:
        """가장 유사한 단어 찾기"""
        if len(word) < 2:
            return word

        best_match = None
        best_similarity = 0.0

        for common_word in self.common_korean_words:
            similarity = SequenceMatcher(None, word, common_word).ratio()
            if similarity > best_similarity and similarity >= similarity_threshold:
                best_similarity = similarity
                best_match = common_word

        return best_match

    def _final_cleanup(self, text: str) -> str:
        """최종 정제"""
        if not text:
            return text

        # 연속된 동일 문자 제거 (3개 이상)
        text = re.sub(r'(.)\1{2,}', r'\1\1', text)

        # 불필요한 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()

        # 구두점 정리
        text = re.sub(r'([.!?])\1+', r'\1', text)

        return text

    def calculate_korean_text_quality(self, text: str) -> float:
        """한글 텍스트 품질 점수 계산"""
        if not text:
            return 0.0

        score = 1.0

        # 한글 문자 비율
        korean_chars = len(self.korean_char_pattern.findall(text))
        total_chars = len([c for c in text if c.isalnum() or self.korean_char_pattern.match(c)])

        if total_chars > 0:
            korean_ratio = korean_chars / total_chars
            score *= korean_ratio

        # 일반적인 단어 포함 여부
        word_match_score = 0.0
        words = text.split()
        for word in words:
            if word in self.common_korean_words:
                word_match_score += 1.0

        if words:
            word_match_score /= len(words)
            score = (score + word_match_score) / 2

        return min(1.0, score)


def enhance_korean_ocr_results(ocr_results: List[Dict[str, Any]],
                              confidence_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """
    한글 OCR 결과 향상 (편의 함수)

    Args:
        ocr_results: OCR 결과 리스트
        confidence_threshold: 신뢰도 임계값

    Returns:
        향상된 OCR 결과
    """
    processor = KoreanTextPostProcessor()
    return processor.process_ocr_results(ocr_results, confidence_threshold)


__all__ = ['KoreanTextPostProcessor', 'enhance_korean_ocr_results']