#!/usr/bin/env python3
"""
OCR 버전 제어 CLI 도구
"""

import sys
from services.ocr.version_manager import (
    OCRVersion, version_manager, create_backup, restore_backup,
    list_backups, get_current_version
)

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1]

    if command == "backup":
        # 현재 시스템 백업
        if len(sys.argv) < 3:
            print("❌ 버전을 지정해주세요: v1_korean_enhanced, v2_ppocrv5, v3_domain_tuned")
            return

        version_str = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else ""

        try:
            version = OCRVersion(version_str)
            backup_name = create_backup(version, description)
            print(f"✅ 백업 생성 완료: {backup_name}")
        except ValueError:
            print(f"❌ 잘못된 버전: {version_str}")

    elif command == "restore":
        # 백업에서 복원
        if len(sys.argv) < 3:
            print("❌ 백업 이름을 지정해주세요")
            return

        backup_name = sys.argv[2]
        success = restore_backup(backup_name)
        if success:
            print("✅ 복원 완료")
        else:
            print("❌ 복원 실패")

    elif command == "list":
        # 백업 목록 조회
        backups = list_backups()
        if not backups:
            print("📋 백업이 없습니다")
            return

        print("📋 사용 가능한 백업:")
        for backup in backups:
            print(f"  - {backup['backup_name']}")
            print(f"    버전: {backup['version']}")
            print(f"    생성: {backup['created_at']}")
            print(f"    설명: {backup.get('description', '없음')}")
            print()

    elif command == "current":
        # 현재 버전 정보
        version_info = get_current_version()
        print("📋 현재 OCR 버전:")
        print(f"  버전: {version_info['version']}")
        print(f"  생성: {version_info['created_at']}")
        print(f"  설명: {version_info.get('description', '없음')}")

    else:
        print_help()

def print_help():
    print("OCR 버전 제어 도구")
    print()
    print("사용법:")
    print("  python3 ocr_version_control.py backup <버전> [설명]  - 현재 시스템 백업")
    print("  python3 ocr_version_control.py restore <백업명>     - 백업에서 복원")
    print("  python3 ocr_version_control.py list                 - 백업 목록 조회")
    print("  python3 ocr_version_control.py current              - 현재 버전 정보")
    print()
    print("버전:")
    print("  v1_korean_enhanced  - 한글 최적화 기본 버전")
    print("  v2_ppocrv5          - PP-OCRv5 업그레이드 버전")
    print("  v3_domain_tuned     - 도메인 특화 파인튜닝 버전")
    print()
    print("예시:")
    print("  python3 ocr_version_control.py backup v1_korean_enhanced '현재 한글 최적화 시스템'")
    print("  python3 ocr_version_control.py restore v1_korean_enhanced_20241009_182800")

if __name__ == "__main__":
    main()