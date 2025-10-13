# FastAPI OCR Reader Makefile

.PHONY: install test test-unit test-integration test-api test-coverage clean lint format help

# 기본 Python 인터프리터
PYTHON := python3
PIP := pip3

# 가상환경 활성화 (필요시)
VENV_ACTIVATE := source paddle_ocr_env/bin/activate

help: ## 사용 가능한 명령어 표시
	@echo "사용 가능한 명령어:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 의존성 설치
	$(PIP) install -r requirements.txt

test: ## 모든 테스트 실행
	$(PYTHON) -m pytest tests/ -v

test-unit: ## 단위 테스트만 실행
	$(PYTHON) -m pytest tests/unit/ -v -m unit

test-integration: ## 통합 테스트만 실행
	$(PYTHON) -m pytest tests/integration/ -v -m integration

test-api: ## API 테스트만 실행
	$(PYTHON) -m pytest tests/api/ -v -m api

test-coverage: ## 테스트 커버리지 측정
	$(PYTHON) -m pytest tests/ --cov=api --cov=services --cov-report=html --cov-report=term-missing

test-fast: ## 빠른 테스트 (LLM 연결 제외)
	$(PYTHON) -m pytest tests/ -v -m "not requires_llm and not slow"

test-with-llm: ## LLM 연결이 필요한 테스트 실행
	$(PYTHON) -m pytest tests/ -v -m requires_llm

lint: ## 코드 스타일 검사
	$(PYTHON) -m flake8 api/ services/ --max-line-length=120
	$(PYTHON) -m mypy api/ services/ --ignore-missing-imports

format: ## 코드 포맷팅
	$(PYTHON) -m black api/ services/ tests/ --line-length=120
	$(PYTHON) -m isort api/ services/ tests/

run-server: ## 개발 서버 실행
	$(PYTHON) -m uvicorn api_server:app --host 0.0.0.0 --port 6003 --reload

run-tests-with-server: ## 서버와 함께 테스트 실행
	@echo "서버 시작 중..."
	$(PYTHON) -m uvicorn api_server:app --host 0.0.0.0 --port 6003 &
	@sleep 5
	@echo "테스트 실행 중..."
	$(PYTHON) -m pytest tests/ -v
	@echo "서버 종료 중..."
	@pkill -f "uvicorn.*6003" || true

clean: ## 임시 파일 정리
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage

install-dev: ## 개발 환경 설정
	$(PIP) install -r requirements.txt
	$(PIP) install black flake8 mypy isort

check: ## 전체 코드 품질 검사
	make lint
	make test-coverage

docker-build: ## Docker 이미지 빌드
	docker build -t ocr-reader:latest .

docker-run: ## Docker 컨테이너 실행
	docker run -p 6003:6003 ocr-reader:latest

# 테스트 데이터 생성
generate-test-data: ## 테스트 데이터 생성
	mkdir -p tests/fixtures/files
	@echo "테스트 파일 생성 완료"

# 테스트 보고서 생성
test-report: ## 상세 테스트 보고서 생성
	$(PYTHON) -m pytest tests/ --html=test-report.html --self-contained-html

# 성능 테스트
test-performance: ## 성능 테스트 실행
	$(PYTHON) -m pytest tests/ -v -m slow