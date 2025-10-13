#!/usr/bin/env python3
"""
추천 시스템 테스트 실행 스크립트
"""

import unittest
import sys
import os
import argparse
from io import StringIO

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_unit_tests():
    """단위 테스트 실행"""
    print("🧪 단위 테스트 실행 중...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_recommendations')

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    return result.wasSuccessful()

def run_api_tests():
    """API 테스트 실행"""
    print("\n🌐 API 테스트 실행 중...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_recommendations_api')

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    return result.wasSuccessful()

def run_integration_tests():
    """통합 테스트 실행 (서버 필요)"""
    print("\n🔗 통합 테스트 실행 중...")
    print("주의: 이 테스트는 localhost:6003에서 실행 중인 서버가 필요합니다.")

    try:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName('tests.test_recommendations_integration')

        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)

        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ 통합 테스트 실행 실패: {e}")
        return False

def run_performance_tests():
    """성능 테스트 실행"""
    print("\n⚡ 성능 테스트 실행 중...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('tests.test_recommendations_performance')

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    return result.wasSuccessful()

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 모든 테스트 실행 중...")

    results = []

    # 단위 테스트
    results.append(("단위 테스트", run_unit_tests()))

    # API 테스트
    results.append(("API 테스트", run_api_tests()))

    # 통합 테스트
    results.append(("통합 테스트", run_integration_tests()))

    # 성능 테스트
    results.append(("성능 테스트", run_performance_tests()))

    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{test_name:15s}: {status}")
        if not passed:
            all_passed = False

    print("="*50)
    if all_passed:
        print("🎉 모든 테스트가 성공적으로 통과했습니다!")
        return True
    else:
        print("😞 일부 테스트가 실패했습니다.")
        return False

def run_quick_tests():
    """빠른 테스트 (단위 + API 테스트만)"""
    print("⚡ 빠른 테스트 실행 중...")

    results = []
    results.append(("단위 테스트", run_unit_tests()))
    results.append(("API 테스트", run_api_tests()))

    # 결과 요약
    print("\n" + "="*30)
    print("📊 빠른 테스트 결과")
    print("="*30)

    all_passed = True
    for test_name, passed in results:
        status = "✅ 통과" if passed else "❌ 실패"
        print(f"{test_name:15s}: {status}")
        if not passed:
            all_passed = False

    return all_passed

def install_test_dependencies():
    """테스트 의존성 설치"""
    print("📦 테스트 의존성 설치 중...")

    try:
        import requests
        import psutil
        import memory_profiler
        print("✅ 모든 의존성이 이미 설치되어 있습니다.")
        return True
    except ImportError as e:
        print(f"❌ 누락된 의존성: {e}")
        print("다음 명령어로 설치하세요:")
        print("pip install requests psutil memory-profiler")
        return False

def main():
    parser = argparse.ArgumentParser(description='추천 시스템 테스트 실행')
    parser.add_argument('--type', choices=['unit', 'api', 'integration', 'performance', 'all', 'quick'],
                       default='quick', help='실행할 테스트 타입')
    parser.add_argument('--check-deps', action='store_true', help='의존성 확인')

    args = parser.parse_args()

    if args.check_deps:
        install_test_dependencies()
        return

    print("🎯 추천 시스템 테스트 스위트")
    print("=" * 40)

    success = False

    if args.type == 'unit':
        success = run_unit_tests()
    elif args.type == 'api':
        success = run_api_tests()
    elif args.type == 'integration':
        success = run_integration_tests()
    elif args.type == 'performance':
        success = run_performance_tests()
    elif args.type == 'all':
        success = run_all_tests()
    elif args.type == 'quick':
        success = run_quick_tests()

    if success:
        print("\n🎉 테스트 완료!")
        sys.exit(0)
    else:
        print("\n💥 테스트 실패!")
        sys.exit(1)

if __name__ == '__main__':
    main()