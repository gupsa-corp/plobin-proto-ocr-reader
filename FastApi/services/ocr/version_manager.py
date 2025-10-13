#!/usr/bin/env python3
"""
OCR 버전 관리 및 원복 시스템
"""

import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class OCRVersion(Enum):
    """OCR 시스템 버전"""
    V1_KOREAN_ENHANCED = "v1_korean_enhanced"  # 현재 한글 최적화 버전
    V2_PPOCRV5 = "v2_ppocrv5"  # PP-OCRv5 업그레이드 버전
    V3_DOMAIN_TUNED = "v3_domain_tuned"  # 도메인 특화 파인튜닝 버전

class OCRVersionManager:
    """OCR 버전 관리자"""

    def __init__(self, base_path: str = "services/ocr"):
        self.base_path = base_path
        self.backup_path = "services/ocr_backups"
        self.version_file = "services/ocr_version.json"
        self._ensure_backup_directory()

    def _ensure_backup_directory(self):
        """백업 디렉토리 생성"""
        os.makedirs(self.backup_path, exist_ok=True)

    def get_current_version(self) -> Dict:
        """현재 OCR 버전 정보 조회"""
        if os.path.exists(self.version_file):
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": OCRVersion.V1_KOREAN_ENHANCED.value,
            "created_at": datetime.now().isoformat(),
            "description": "한글 최적화 기본 버전"
        }

    def create_backup(self, version: OCRVersion, description: str = "") -> str:
        """현재 OCR 시스템 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{version.value}_{timestamp}"
        backup_dir = os.path.join(self.backup_path, backup_name)

        # OCR 디렉토리 백업
        if os.path.exists(self.base_path):
            shutil.copytree(self.base_path, backup_dir)

        # 백업 메타데이터 저장
        metadata = {
            "version": version.value,
            "backup_name": backup_name,
            "created_at": datetime.now().isoformat(),
            "description": description,
            "path": backup_dir
        }

        metadata_file = os.path.join(backup_dir, "backup_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 현재 버전 정보 업데이트
        self._update_version_info(metadata)

        print(f"✅ OCR 시스템 백업 생성: {backup_name}")
        return backup_name

    def restore_backup(self, backup_name: str) -> bool:
        """백업에서 OCR 시스템 복원"""
        backup_dir = os.path.join(self.backup_path, backup_name)

        if not os.path.exists(backup_dir):
            print(f"❌ 백업을 찾을 수 없습니다: {backup_name}")
            return False

        # 현재 시스템을 임시 백업
        temp_backup = f"temp_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(self.base_path):
            shutil.move(self.base_path, os.path.join(self.backup_path, temp_backup))

        try:
            # 백업에서 복원
            shutil.copytree(backup_dir, self.base_path)

            # 백업 메타데이터에서 버전 정보 복원
            metadata_file = os.path.join(backup_dir, "backup_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                self._update_version_info(metadata)

            print(f"✅ OCR 시스템 복원 완료: {backup_name}")
            print(f"💾 이전 상태는 {temp_backup}에 백업됨")
            return True

        except Exception as e:
            # 복원 실패 시 원상복구
            if os.path.exists(self.base_path):
                shutil.rmtree(self.base_path)
            shutil.move(os.path.join(self.backup_path, temp_backup), self.base_path)
            print(f"❌ 복원 실패: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """사용 가능한 백업 목록 조회"""
        backups = []

        if not os.path.exists(self.backup_path):
            return backups

        for backup_name in os.listdir(self.backup_path):
            backup_dir = os.path.join(self.backup_path, backup_name)
            metadata_file = os.path.join(backup_dir, "backup_metadata.json")

            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                backups.append(metadata)

        # 생성 시간 역순 정렬
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups

    def _update_version_info(self, metadata: Dict):
        """버전 정보 파일 업데이트"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

# 전역 버전 매니저 인스턴스
version_manager = OCRVersionManager()

def create_backup(version: OCRVersion, description: str = "") -> str:
    """OCR 시스템 백업 생성 (편의 함수)"""
    return version_manager.create_backup(version, description)

def restore_backup(backup_name: str) -> bool:
    """OCR 시스템 복원 (편의 함수)"""
    return version_manager.restore_backup(backup_name)

def list_backups() -> List[Dict]:
    """백업 목록 조회 (편의 함수)"""
    return version_manager.list_backups()

def get_current_version() -> Dict:
    """현재 버전 정보 조회 (편의 함수)"""
    return version_manager.get_current_version()