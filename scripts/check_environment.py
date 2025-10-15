#!/usr/bin/env python3
"""
OCR API 환경 검증 스크립트
서비스 시작 전에 필요한 디렉토리, 권한, 종속성을 확인합니다.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import subprocess
import json
from datetime import datetime

class EnvironmentChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.base_dir = Path(__file__).parent.parent

    def log_error(self, message):
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message):
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_success(self, message):
        print(f"✅ {message}")

    def check_directories(self):
        """필수 디렉토리 존재 및 권한 확인"""
        print("\n📁 디렉토리 검증 중...")

        required_dirs = [
            (self.base_dir / "output", "출력 디렉토리"),
            (self.base_dir / "FastApi", "FastAPI 코드 디렉토리"),
            (self.base_dir / "FastApi" / "services", "서비스 모듈 디렉토리"),
        ]

        for dir_path, description in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.log_success(f"{description} 생성됨: {dir_path}")
                except Exception as e:
                    self.log_error(f"{description} 생성 실패 {dir_path}: {e}")
                    continue

            # 권한 확인
            if not os.access(dir_path, os.R_OK | os.W_OK):
                self.log_error(f"{description} 읽기/쓰기 권한 없음: {dir_path}")
            else:
                self.log_success(f"{description} 권한 확인됨: {dir_path}")

    def check_temp_directory(self):
        """임시 디렉토리 접근 및 쓰기 권한 확인"""
        print("\n📂 임시 디렉토리 검증 중...")

        try:
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(b"test")
                tmp_file.flush()
                self.log_success(f"임시 파일 생성/쓰기 가능: {tmp_file.name}")
        except Exception as e:
            self.log_error(f"임시 파일 생성 실패: {e}")

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                test_file = Path(tmp_dir) / "test.txt"
                test_file.write_text("test")
                self.log_success(f"임시 디렉토리 생성/쓰기 가능: {tmp_dir}")
        except Exception as e:
            self.log_error(f"임시 디렉토리 생성 실패: {e}")

    def check_disk_space(self):
        """디스크 공간 확인"""
        print("\n💾 디스크 공간 검증 중...")

        # 최소 1GB 여유 공간 요구
        min_space_gb = 1

        try:
            stat = shutil.disk_usage(self.base_dir)
            free_gb = stat.free / (1024**3)

            if free_gb < min_space_gb:
                self.log_error(f"디스크 여유 공간 부족: {free_gb:.1f}GB (최소 {min_space_gb}GB 필요)")
            else:
                self.log_success(f"디스크 여유 공간 충분: {free_gb:.1f}GB")

        except Exception as e:
            self.log_error(f"디스크 공간 확인 실패: {e}")

    def check_python_dependencies(self):
        """Python 패키지 의존성 확인"""
        print("\n🐍 Python 의존성 검증 중...")

        required_packages = [
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("PyMuPDF", "fitz"),
            ("Pillow", "PIL"),
            ("numpy", "numpy"),
        ]

        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                self.log_success(f"패키지 확인됨: {package_name}")
            except ImportError:
                self.log_error(f"패키지 누락: {package_name}")

    def check_file_permissions(self):
        """주요 파일들의 실행 권한 확인"""
        print("\n🔐 파일 권한 검증 중...")

        executable_files = [
            self.base_dir / "scripts" / "start_server.sh",
            self.base_dir / "scripts" / "stop_server.sh",
        ]

        for file_path in executable_files:
            if file_path.exists():
                if os.access(file_path, os.X_OK):
                    self.log_success(f"실행 권한 확인됨: {file_path}")
                else:
                    try:
                        file_path.chmod(0o755)
                        self.log_success(f"실행 권한 설정됨: {file_path}")
                    except Exception as e:
                        self.log_error(f"실행 권한 설정 실패 {file_path}: {e}")
            else:
                self.log_warning(f"파일 없음: {file_path}")

    def check_ports(self):
        """포트 사용 가능성 확인"""
        print("\n🌐 포트 검증 중...")

        import socket

        default_ports = [6003, 8000, 8001]

        for port in default_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    self.log_warning(f"포트 {port} 이미 사용 중")
                else:
                    self.log_success(f"포트 {port} 사용 가능")
            except Exception as e:
                self.log_warning(f"포트 {port} 확인 실패: {e}")
            finally:
                sock.close()

    def create_environment_info(self):
        """환경 정보 파일 생성"""
        print("\n📋 환경 정보 생성 중...")

        import platform

        env_info = {
            "timestamp": datetime.now().isoformat(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "working_directory": str(self.base_dir),
            "user": os.getenv("USER", "unknown"),
            "errors": self.errors,
            "warnings": self.warnings
        }

        try:
            info_file = self.base_dir / "environment_check.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(env_info, f, indent=2, ensure_ascii=False)
            self.log_success(f"환경 정보 저장됨: {info_file}")
        except Exception as e:
            self.log_error(f"환경 정보 저장 실패: {e}")

    def run_all_checks(self):
        """모든 검증 실행"""
        print("🔍 OCR API 환경 검증 시작\n" + "="*50)

        self.check_directories()
        self.check_temp_directory()
        self.check_disk_space()
        self.check_python_dependencies()
        self.check_file_permissions()
        self.check_ports()
        self.create_environment_info()

        print("\n" + "="*50)
        print("📊 검증 결과 요약:")
        print(f"   ❌ 오류: {len(self.errors)}개")
        print(f"   ⚠️  경고: {len(self.warnings)}개")

        if self.errors:
            print("\n❌ 발견된 오류들:")
            for error in self.errors:
                print(f"   • {error}")
            print("\n⚠️  서비스 시작 전에 위 오류들을 해결해주세요.")
            return False
        else:
            print("\n✅ 모든 검증을 통과했습니다. 서비스를 시작할 수 있습니다.")
            if self.warnings:
                print("\n⚠️  경고사항:")
                for warning in self.warnings:
                    print(f"   • {warning}")
            return True


def main():
    checker = EnvironmentChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()