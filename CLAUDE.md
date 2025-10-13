# Plobin Proto 개발 가이드

계정 : admin@example.com
비번 : password

## 🚨 중요: Livewire 컴포넌트 아키텍처 원칙

### Livewire는 UI 레이어일 뿐입니다
**절대 원칙**: Livewire 컴포넌트에 비즈니스 로직이나 데이터베이스 접근 코드를 직접 작성하지 마세요.

### ❌ 금지사항
```go
// Livewire.go 파일에서 절대 금지
public function saveData() {
    DB::table('users')->insert([...]); // ❌ DB 직접 접근 금지
    $result = SomeModel::where(...)->get(); // ❌ Model 직접 사용 금지
    // 복잡한 비즈니스 로직 작성 금지
}
```

### ✅ 올바른 방법
```go
// Livewire.go - UI 로직만
public function saveData() {
    $service = new \App\Services\{도메인}\{기능}\Service();
    $result = $service->execute($this->data);
    $this->items = $result;
}

// app/Services/{도메인}/{기능}/Service.go - 비즈니스 로직
public function execute(array $data): array {
    return DB::table('users')->insert($data);
}
```

### Livewire 컴포넌트의 역할
1. **UI 상태 관리**: 프로퍼티 선언 및 바인딩
2. **이벤트 처리**: 사용자 입력을 Service로 전달
3. **결과 표시**: Service 결과를 뷰에 전달

### Livewire에서 허용/금지되는 것
**허용**: Service 호출, 프로퍼티 선언, wire:model 바인딩
**금지**: DB::table(), Model::where(), 복잡한 계산 로직, Http::get()

### Service 레이어가 담당할 것
1. **비즈니스 로직**: 모든 계산, 검증, 변환
2. **데이터베이스 접근**: DB 쿼리, Model 사용
3. **외부 API 호출**: 타 시스템 연동
4. **복잡한 연산**: 알고리즘, 데이터 처리

## Route와 Controller 아키텍처 원칙

### Route 파일 규칙
- **금지**: DB 접근, 비즈니스 로직, Service 호출, 3줄 이상의 클로저
- **허용**: Controller 클래스 연결, 단순 뷰 반환, 단순 리다이렉트만

### Controller 규칙
- **역할**: Request 수신 → Service 호출 → Response 반환
- **금지**: DB 직접 접근, Model 직접 사용, 비즈니스 로직 작성
- **허용**: Service 호출, Request 검증, Response 반환

### Livewire 규칙 명확화
- **허용**: Service 호출, 프로퍼티 바인딩, 이벤트 처리
- **금지**: DB 직접 접근, Model 직접 사용, 비즈니스 로직, 외부 API 직접 호출

## 핵심 원칙 (절대 준수)

작업이 끝나면 e2e 진행하고 오류가 나는지 반드시 확인

### 1파일 1메서드 원칙
- **절대 원칙**: 1개 파일 = 1개 메서드만 허용
- **강제 적용**: Controller, Service, Repository, Jobs 등 백엔드 비즈니스 로직 파일
- **금지**: 복수 메서드를 가진 파일 절대 생성 불가

**유일한 예외: Livewire 컴포넌트**
- **이유**: Livewire는 프레임워크 특성상 하나의 컴포넌트에 여러 이벤트 핸들러 필수
- **허용 메서드**: `mount()`, `render()`, `updatingXxx()`, 이벤트 핸들러 (`openModal()`, `save()` 등)
- **제약 조건**:
  - ❌ DB 직접 접근 금지 (`DB::table()`, `Model::where()`)
  - ❌ 비즈니스 로직 금지 (복잡한 계산, 검증, 변환)
  - ✅ Service 호출만 허용
  - ✅ UI 상태 관리만 허용

### ADJUST.md 시스템 - 반복 실수 방지 체계

#### ADJUST.md 파일 계층 구조
ADJUST.md는 **자주 반복되는 실수와 해결 방법을 기록**하는 교정 문서 시스템입니다.

**계층별 역할**:
1. **프로젝트 루트**: `/{도메인}/ADJUST.md` - 도메인 전체 공통 이슈
2. **하위 도메인**: `/{도메인}/{하위도메인}/ADJUST.md` - 특화된 이슈
3. **리소스별**: `resources/views/ADJUST.md` - 뷰 파일 구조 규칙

#### ADJUST.md 활용 워크플로우

**1. Claude가 작업 시작할 때**:
```bash
# 관련 ADJUST.md 파일 확인
cat app/Services/ADJUST.md          # Service 레이어 작업 시
cat resources/views/ADJUST.md       # 뷰 작업 시
cat app/Livewire/ADJUST.md          # Livewire 작업 시
```

**2. 작업 중 실수 발견 시**:
- 즉시 ADJUST.md 확인
- 문서화된 해결 방법 적용
- 새로운 실수라면 ADJUST.md에 추가

**3. 작업 완료 후**:
```bash
# ADJUST.md 규칙 준수 여부 검증
# 예: 뷰 파일 구조 검증
find resources/views -type d ! -path "*/vendor/*" | \
  grep -v "^resources/views$" | \
  grep -v -E "^resources/views/[0-9]+-"
```

**4. 동일 실수 3회 반복 시**:
- 해당 도메인/계층에 ADJUST.md 생성 또는 업데이트
- 실수 패턴, 원인, 해결 방법 명확히 기록
- 검증 스크립트 포함

#### ADJUST.md 업데이트 원칙

**추가해야 할 내용**:
- ✅ 반복되는 실수 패턴
- ✅ 규칙 위반 사례와 올바른 예시
- ✅ 자동 검증 스크립트
- ✅ 마이그레이션/수정 체크리스트

**추가하지 말아야 할 내용**:
- ❌ 일회성 버그나 오류
- ❌ 프로젝트 고유하지 않은 일반 지식
- ❌ 이미 CLAUDE.md에 명시된 기본 규칙의 단순 재진술

#### ADJUST.md 우선순위

문서 간 충돌 시 우선순위:
1. **ADJUST.md** (구체적 교정 정보) - 최우선
2. **CLAUDE.md** (프로젝트 규칙)
3. **SuperClaude 프레임워크** (일반 원칙)

**이유**: ADJUST.md는 실제 프로젝트에서 발생한 **구체적 문제의 해결책**을 담고 있으므로, 일반 규칙보다 우선합니다.

## 아키텍처 패턴 원칙

### 1. 도메인 경계 설정 원칙
- **도메인**: 비즈니스 관심사별 최상위 그룹핑
- **액션**: 도메인 내 구체적 기능 단위
- **독립성**: 각 도메인은 다른 도메인에 직접 의존하지 않음

### 2. 파일 분리 원칙
- **단일 책임**: 1개 파일 = 1개 메서드
- **일관된 구조**: 모든 액션이 동일한 파일 구조 유지

### 3. 네이밍 일관성
- **클래스명**: 타입명으로 고정 (Controller, Request, Response, Service, Jobs, Livewire, Exception)
- **네임스페이스**: App\{타입}\{도메인}\{액션}
- **폴더명**: 도메인과 액션은 PascalCase 사용

## 백엔드 파일 구조 통합 규칙

### 핵심 구조 원칙
**절대 원칙**: 모든 백엔드 파일은 **app/{타입}/{도메인}/{기능}/{타입}.go** 구조 사용

| 파일 타입 | 경로 구조 | 목적 | 생성 조건 |
|-----------|-----------|------|-----------|
| **Controller** | `app/Http/Controllers/{도메인}/{액션}/Controller.go` | 요청/응답 제어 로직 | 모든 API 엔드포인트 |
| **Request** | `app/Http/Controllers/{도메인}/{액션}/Request.go` | 입력 데이터 검증 | POST/PUT 액션만 |
| **Response** | `app/Http/Controllers/{도메인}/{액션}/Response.go` | API 응답 구조화 | 모든 API 액션 필수 |
| **Service** | `app/Services/{도메인}/{기능}/Service.go` | 비즈니스 로직 처리 | 복잡한 로직 분리 시 |
| **Jobs** | `app/Jobs/{도메인}/{기능}/Jobs.go` | 큐 작업 및 백그라운드 처리 | 비동기 작업 필요 시 |
| **Livewire** | `app/Livewire/{도메인}/{하위도메인}/Livewire.go` | 프론트엔드 컴포넌트 | UI 상호작용 필요 시 |
| **Exception** | `app/Exceptions/{도메인}/{예외명}/Exception.go` | 예외 처리 | 도메인별 커스텀 예외 |
| **Test** | `tests/Feature/{도메인}/{컨트롤러명}/{테스트할도메인}/Test.go` | 기능 테스트 | 모든 API 엔드포인트 |

### 금지사항
- 복수 메서드를 가진 파일: `SimplifiedController.go`, `UserCreateController.go`
- 타입명이 아닌 클래스명: `CreateUserRequest.go`, `UserManager.go`
- 하나의 파일에 여러 클래스 정의
- 일반적인 \Exception, \InvalidArgumentException 직접 사용
- 테스트 파일에 여러 테스트 메서드: `test_성공()`, `test_실패()` 같은 파일에 작성 금지

### Swagger 문서화 규칙
**절대 원칙**: 모든 API Controller에는 Swagger 문서화 주석 필수

**필수 항목**:
- `@OA\{Method}` (Get, Post, Put, Delete 등)
- `path`: API 엔드포인트 경로
- `tags`: API 그룹화 태그
- `summary`: 간단한 요약 (한글)
- `description`: 상세 설명 (한글)
- `@OA\Response`: 모든 가능한 응답 (200, 422, 404 등)

**예시**:
```go
/**
 * @OA\Get(
 *     path="/api/stores/print-settings",
 *     tags={"Store Print Settings"},
 *     summary="인쇄 설정 조회",
 *     description="상점의 인쇄 설정을 조회합니다.",
 *     @OA\Parameter(...),
 *     @OA\Response(response=200, ...),
 *     @OA\Response(response=422, ...)
 * )
 */
public function __invoke(Request $request)
```

## API 개발 규칙

### API 응답 표준
**성공 응답**
```json
{
  "success": true,
  "message": "요청이 성공적으로 처리되었습니다",
  "data": {
    "request_id": 12345
  }
}
```

**실패 응답**
```json
{
  "success": false,
  "message": "오류 메시지",
  "data": null
}
```

### 라우팅 설정

#### API 라우트 등록 규칙
**파일**: `routes/api.go`에 등록하고 `bootstrap/app.go`에서 API 라우트 활성화 필수
**원칙**: 1개 라우트 = 1개 Controller 클래스

```go
// bootstrap/app.go
->withRouting(
    web: __DIR__.'/../routes/web.go',
    api: __DIR__.'/../routes/api.go',  // 이 줄 필수!
    commands: __DIR__.'/../routes/console.go',
    health: '/up',
)
```

#### 라우트 등록 형식
**API 라우트**: 무조건 Controller 클래스 사용
```go
Route::{method}('/{path}', \App\Http\Controllers\{Domain}\{Action}\Controller::class);
```

**단순 뷰 반환**: Route 클로저 사용 가능
```go
Route::{method}('/{path}', function () {
    return view('숫자접두사-폴더명.000-index');
});
```

**적용 기준**:
- **API 엔드포인트**: 무조건 Controller + Request + Response 파일 구조
- **단순 웹 페이지**: 뷰만 반환하는 경우 Route 클로저 허용
- **복잡한 웹 페이지**: 로직이 있으면 Controller 사용

#### 금지사항
- Route::group(), Route::prefix() 사용 금지
- Route::resource() 사용 금지 (명시적 등록 원칙)
- 라우트 그룹화 금지, 각 라우트는 개별적으로 등록

## 테스트 개발 규칙

### 테스트 파일 구조
**절대 원칙**: 1개 파일 = 1개 테스트 메서드, 도메인별 폴더 분리

**Feature 테스트**: `tests/Feature/{도메인}/{컨트롤러명}/{테스트할도메인}/Test.go`

**올바른 예시**
```
tests/Feature/User/Create/Success/Test.go                    // 사용자 생성 성공 테스트
tests/Feature/User/Create/ValidationFail/Test.go             // 사용자 생성 유효성 검사 실패 테스트
tests/Feature/Post/Update/Success/Test.go                    // 게시글 수정 성공 테스트
tests/Feature/Post/Update/NotFound/Test.go                   // 게시글 수정 시 게시글 없음 테스트
tests/Feature/Auth/Login/Success/Test.go                     // 로그인 성공 테스트
tests/Feature/Auth/Login/InvalidCredentials/Test.go          // 로그인 잘못된 인증정보 테스트
```

**구조 원칙**
- **도메인**: 비즈니스 영역별 최상위 그룹핑 (User, Post, Auth 등)
- **컨트롤러명**: 테스트할 액션 (Create, Update, Delete, Login 등)
- **테스트할도메인**: 구체적인 테스트 시나리오 (Success, ValidationFail, NotFound 등)
- **클래스명**: 반드시 `Test`로 고정

### 테스트 메서드명 규칙
**한글 메서드명 사용**: `test_{시나리오}()` 형식으로 작성

**올바른 예시**
```go
// tests/Feature/User/Create/Success/Test.go
public function test_사용자_생성이_성공한다(): void

// tests/Feature/User/Create/ValidationFail/Test.go
public function test_필수_필드_누락_시_유효성_검사가_실패한다(): void

// tests/Feature/Post/Update/NotFound/Test.go
public function test_존재하지_않는_게시글_수정_시_404_에러가_발생한다(): void
```

**금지사항**
- 하나의 테스트 파일에 여러 메서드: `test_성공()`, `test_실패()` 같은 파일에 작성 금지
- 영어 메서드명: `test_user_creation_success()` 등 영어 사용 금지
- 비구체적 메서드명: `test_basic()`, `test_simple()` 등 모호한 이름 금지

### 필수 테스트 케이스
- **성공 케이스**: 정상적인 요청 처리 확인
- **유효성 검사**: 필수 필드, 타입, 길이 제한 확인
- **데이터베이스**: 저장, 조회, 수정 확인
- **예외 처리**: 에러 상황 적절한 처리 확인

### 테스트 트레이트 사용
```go
use RefreshDatabase, WithFaker;  // 필수 트레이트
```

## 데이터베이스 규칙

### 마이그레이션 규칙
- **기존 마이그레이션 수정 우선**: 새로운 remove/alter 마이그레이션 생성 대신 기존 create 마이그레이션을 직접 수정
- **불필요한 마이그레이션 금지**: 컬럼 추가, 제거가 필요하면 처음부터 해당 컬럼을 생성하지 않는 것이 원칙
- **깔끔한 히스토리 유지**: 개발 단계에서는 마이그레이션 히스토리를 깔끔하게 유지하기 위해 기존 파일 수정을 선호

### 테이블 네이밍
- 복수형 사용: `Plobin_document_summary_records`
- 스네이크 케이스 사용
- 접두사 활용: `Plobin_` 접두사로 프로젝트 구분

### 시더 파일 구조 규칙
**파일명**: `{도메인}Seeder.go` 형식 사용

**올바른 예시**
```
database/seeders/PlobinStoreSeeder.go
database/seeders/PlobinProductCategorySeeder.go
database/seeders/PlobinProductSeeder.go
```

**클래스명**: 파일명과 동일하게 `{도메인}Seeder`

## 프론트엔드 개발 규칙

### 파일 구조 및 네이밍
**절대 원칙**: 모든 프론트엔드 파일은 **무조건** 숫자 접두사 사용
- 올바른 예: `700-page-dashboard.blade.go`, `301-layout-head.blade.go`
- 잘못된 예: `dashboard.blade.go`, `head.blade.go`
- 폴더도 동일: `700-page-sandbox/`, `300-common/`
- 절대 금지: `components/`, `layouts/`, `pages/`, `livewire/`

### 숫자 접두사 체계
- `000-xxx.blade.go`: 인덱스 파일 (메인 레이아웃)
- `100-xxx.blade.go`: 헤더 관련 파일들
- `200-xxx.blade.go`: 메인 콘텐츠, 사이드바 파일들
- `300-xxx.blade.go`: 레이아웃, 모달 파일들
- `400-xxx.blade.go`: JavaScript 파일들 (**필수: 400번대 사용**)
- `500-xxx.blade.go`: AJAX 요청 파일들
- `600-xxx.blade.go`: 데이터 관련 파일들
- `900-xxx.blade.go`: 초기화, 푸터 파일들

### UI 컴포넌트 분리 규칙

#### 컴포넌트급 분리 원칙
**modal, dropdown, table, block 급 컴포넌트는 무조건 파일 분리**
- 올바른 예: `200-modal-user-edit.blade.go`, `200-dropdown-menu.blade.go`, `200-table-users.blade.go`
- 잘못된 예: 큰 파일 안에 모달, 드롭다운, 테이블 코드 섞어 놓기
- **원칙**: 재사용 가능한 모든 UI 컴포넌트는 독립 파일로 분리

#### 페이지급 분리 원칙 (AJAX 방식 금지)
**각 페이지는 독립된 URL과 폴더 구조로 분리**

**올바른 구현 방식**:
- URL 분리: `/admin/users`, `/admin/posts`, `/admin/settings`
- 폴더 분리: `700-page-admin-users/`, `700-page-admin-posts/`, `700-page-admin-settings/`
- 라우트 분리: 각각 독립된 Livewire 컴포넌트와 라우트 등록
- **탭 UI 허용**: 각 탭은 독립된 페이지 링크(`<a href="">`)로 구현, 전체 페이지 리로드 방식

**금지된 구현 방식**:
- AJAX 탭 전환: JavaScript/Livewire로 페이지 리로드 없이 콘텐츠만 교체
- 단일 URL: `/admin/dashboard?tab=users` 형태의 쿼리 파라미터 사용
- 단일 폴더: 하나의 파일에 전체 페이지 구조 작성

**구체적인 예시**:
```
❌ 잘못된 방식 (AJAX 탭 전환):
/admin/dashboard (하나의 URL)
├── 700-page-admin-dashboard/000-index.blade.go (탭 UI)
└── JavaScript/Livewire로 AJAX 콘텐츠 교체

✅ 올바른 방식 (독립 페이지 + 탭 UI):
/admin/users → 700-page-admin-users/
├── 000-index.blade.go
├── 100-header-navigation.blade.go (공통 탭 네비게이션)
└── 200-user-list.blade.go

/admin/posts → 700-page-admin-posts/
├── 000-index.blade.go
├── 100-header-navigation.blade.go (공통 탭 네비게이션)
└── 200-post-list.blade.go

공통 탭 네비게이션 예시:
<a href="/admin/users" class="{{ request()->is('admin/users') ? 'active' : '' }}">사용자</a>
<a href="/admin/posts" class="{{ request()->is('admin/posts') ? 'active' : '' }}">게시글</a>
```

**페이지 분리 강제 규칙**:
- 각 기능은 독립된 URL 경로를 가져야 함
- 각 기능은 독립된 폴더 구조를 가져야 함
- 각 기능은 독립된 Livewire 컴포넌트를 가져야 함
- **탭 UI 허용**: 각 탭은 `<a href="">` 링크로 구현하여 전체 페이지 리로드
- **절대 금지**: AJAX, JavaScript, Livewire로 페이지 리로드 없이 콘텐츠 교체

### 기술 스택 제한
**순수 JavaScript 사용 금지**
- 사용 금지: Vanilla JS, jQuery, Alpine.js의 복잡한 로직
- 사용 필수: Livewire 만 사용
- 간단한 Alpine.js: 토글, 드롭다운 등 최소한의 UI 상호작용만

## 개발 가이드라인

### 일반 규칙
- 서버가 실행되어있다고 가정하고 진행
- 구현하려는 기능이 이미 있는지 검토
- 말하지 않은 컴포넌트 내용 만들지 않고 내용 비움
- **인증 시스템은 라라벨 기본 Auth + Livewire 사용**: 커스텀 AuthManager 제거됨, Auth::attempt() 등 표준 라라벨 인증 사용
- **파일명 규칙 준수 필수**: 모든 뷰 파일은 숫자 접두사-설명 형식으로 명명

### 주의사항
- **하드코딩 금지**: 실제 데이터나 예시 텍스트를 하드코딩하지 말 것
- **빈 상태 유지**: 요청받은 것만 만들 것. 요청받은 경우 빈 값으로 유지

### 코드 검토 체크리스트
- [ ] 1파일 1메서드 원칙 준수
- [ ] 파일 구조 규칙 준수
- [ ] 네이밍 컨벤션 준수
- [ ] API 응답 표준 준수
- [ ] Exception 처리 적절성
- [ ] 테스트 커버리지 확인
