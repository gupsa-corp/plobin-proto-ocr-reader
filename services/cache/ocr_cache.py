#!/usr/bin/env python3
"""
OCR 결과 캐싱 시스템 - RTX 3090 최적화
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import pickle


class OCRCache:
    """OCR 결과를 캐싱하여 중복 처리 방지"""

    def __init__(self, cache_dir: str = "cache", max_cache_size: int = 1000):
        """
        캐시 초기화

        Args:
            cache_dir: 캐시 디렉토리
            max_cache_size: 최대 캐시 항목 수
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = max_cache_size
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()

    def _load_cache_index(self) -> Dict[str, Dict[str, Any]]:
        """캐시 인덱스 로드"""
        try:
            if self.cache_index_file.exists():
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"캐시 인덱스 로드 실패: {e}")
        return {}

    def _save_cache_index(self):
        """캐시 인덱스 저장"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"캐시 인덱스 저장 실패: {e}")

    def _generate_cache_key(self, image_path: str, config: Dict[str, Any]) -> str:
        """
        이미지와 설정을 기반으로 캐시 키 생성

        Args:
            image_path: 이미지 파일 경로
            config: OCR 설정

        Returns:
            캐시 키 (해시)
        """
        # 이미지 파일의 해시 계산
        try:
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            # 파일을 읽을 수 없으면 경로와 수정 시간 사용
            stat = os.stat(image_path)
            image_hash = hashlib.md5(
                f"{image_path}_{stat.st_mtime}_{stat.st_size}".encode()
            ).hexdigest()

        # 설정 해시 계산
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()

        return f"{image_hash}_{config_hash}"

    def get(self, image_path: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        캐시에서 OCR 결과 조회

        Args:
            image_path: 이미지 파일 경로
            config: OCR 설정

        Returns:
            캐시된 OCR 결과 또는 None
        """
        cache_key = self._generate_cache_key(image_path, config)

        if cache_key not in self.cache_index:
            return None

        cache_info = self.cache_index[cache_key]
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if not cache_file.exists():
            # 캐시 파일이 없으면 인덱스에서 제거
            del self.cache_index[cache_key]
            self._save_cache_index()
            return None

        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)

            # 액세스 시간 업데이트
            cache_info['last_accessed'] = time.time()
            cache_info['access_count'] = cache_info.get('access_count', 0) + 1
            self._save_cache_index()

            print(f"캐시 히트: {cache_key[:8]}... (접근 횟수: {cache_info['access_count']})")
            return result

        except Exception as e:
            print(f"캐시 로드 실패: {e}")
            # 손상된 캐시 파일 제거
            try:
                cache_file.unlink()
                del self.cache_index[cache_key]
                self._save_cache_index()
            except Exception:
                pass
            return None

    def set(self, image_path: str, config: Dict[str, Any], result: Dict[str, Any]):
        """
        OCR 결과를 캐시에 저장

        Args:
            image_path: 이미지 파일 경로
            config: OCR 설정
            result: OCR 결과
        """
        cache_key = self._generate_cache_key(image_path, config)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            # 캐시 크기 제한 확인
            if len(self.cache_index) >= self.max_cache_size:
                self._cleanup_old_cache()

            # 결과 저장
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)

            # 인덱스 업데이트
            self.cache_index[cache_key] = {
                'created': time.time(),
                'last_accessed': time.time(),
                'access_count': 1,
                'image_path': image_path,
                'file_size': cache_file.stat().st_size
            }

            self._save_cache_index()
            print(f"캐시 저장: {cache_key[:8]}... (파일 크기: {cache_file.stat().st_size} bytes)")

        except Exception as e:
            print(f"캐시 저장 실패: {e}")

    def _cleanup_old_cache(self):
        """오래된 캐시 항목 정리"""
        try:
            # 액세스 시간 기준으로 정렬
            sorted_items = sorted(
                self.cache_index.items(),
                key=lambda x: x[1].get('last_accessed', 0)
            )

            # 오래된 항목 25% 제거
            items_to_remove = len(sorted_items) // 4

            for cache_key, _ in sorted_items[:items_to_remove]:
                cache_file = self.cache_dir / f"{cache_key}.pkl"
                try:
                    cache_file.unlink(missing_ok=True)
                    del self.cache_index[cache_key]
                except Exception:
                    pass

            self._save_cache_index()
            print(f"캐시 정리 완료: {items_to_remove}개 항목 제거")

        except Exception as e:
            print(f"캐시 정리 실패: {e}")

    def clear(self):
        """전체 캐시 삭제"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()

            self.cache_index.clear()
            self._save_cache_index()
            print("전체 캐시 삭제 완료")

        except Exception as e:
            print(f"캐시 삭제 실패: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            total_files = len(list(self.cache_dir.glob("*.pkl")))
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))

            total_access = sum(info.get('access_count', 0) for info in self.cache_index.values())

            return {
                "total_items": len(self.cache_index),
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_access_count": total_access,
                "cache_hit_ratio": f"{total_access / max(len(self.cache_index), 1):.2f}"
            }
        except Exception as e:
            print(f"캐시 통계 조회 실패: {e}")
            return {}


# 전역 캐시 인스턴스
_ocr_cache = None

def get_ocr_cache() -> OCRCache:
    """OCR 캐시 인스턴스 반환 (싱글톤)"""
    global _ocr_cache
    if _ocr_cache is None:
        _ocr_cache = OCRCache()
    return _ocr_cache


__all__ = ['OCRCache', 'get_ocr_cache']