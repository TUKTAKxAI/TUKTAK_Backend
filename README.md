# 🛠️ TUKTAK Backend

TUKTAK Backend는 집수리 AI 견적, 리스크 리포트, 시공자 프로필, 견적서, 시공 건, 리뷰, 알림 기능을 제공하는 FastAPI 기반 백엔드입니다.

프로젝트 API 명세서와 테이블 정의서를 기준으로 구현 중이며, 일부 Matching API는 현재 구현 범위에서 제외되어 있습니다.

---

## 🚀 Tech Stack

- 🐍 Python 3.12+
- ⚡ FastAPI
- 🗄️ SQLAlchemy Async
- 🧬 Alembic
- 🐬 MySQL
- 🔐 JWT Authentication
- ✅ Pydantic v2

---

## ▶️ 실행 방법

```powershell
conda activate tuktak-backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8081
```

Swagger UI:

```text
http://localhost:8081/docs
```

Health Check:

```text
GET /health
```

---

## 🔐 인증 방식

로그인 후 발급받은 `access_token`을 Swagger UI의 `Authorize` 버튼에 입력하면 인증이 필요한 API를 사용할 수 있습니다.

```text
Authorization: Bearer <access_token>
```

---

## 📌 구현된 주요 기능

### 🔑 Auth

회원가입, 로그인, 토큰 재발급, 로그아웃 기능입니다.

- 일반 사용자 회원가입
- 시공자 회원가입
- 이메일 중복 확인
- JWT 로그인
- Access Token 재발급
- Refresh Token 폐기

### 📄 Agreement

회원가입에 필요한 약관 목록을 제공합니다.

- 필수/선택 약관 조회
- 약관 타입, 버전, 제목, 원문 URL 관리

### 👤 User

로그인한 사용자의 기본 정보를 조회하고 수정합니다.

- 내 정보 조회
- 닉네임, 이름, 전화번호, 프로필 이미지 수정

### 🧩 Reference Code / Service Task

지역, 수리 객체, 문제 유형, 수리 작업 같은 기준정보를 조회합니다.

- 공통 코드 조회
- 수리 카테고리 및 작업 기준정보 조회

### 👷 Contractor Profile

시공자 프로필과 전문 분야를 관리합니다.

- 시공자 본인 프로필 조회
- 시공자 기본 정보 수정
- 전문 분야/서비스 지역 목록 조회
- 전문 분야/서비스 지역 일괄 저장
- 신규 매칭 알림 수신 여부 설정
- 사용자용 시공자 공개 프로필 조회

### 🤖 AI Estimate

사진과 설명 기반 AI 견적 요청 및 조회 기능입니다.

- AI 견적 생성 요청
- AI 견적 상세 조회
- 내 AI 견적 목록 조회
- 실패한 AI 견적 재시도

현재 외부 AI 서버 연동 전 단계이므로 견적 생성 시 `PROCESSING` 상태로 저장됩니다.

### ⚠️ Risk Report

AI 견적 기반 리스크 리포트 기능입니다.

- 리스크 리포트 생성 요청
- 내 리스크 리포트 목록 조회
- 리스크 리포트 상세 조회
- 리스크 항목, 체크리스트, 근거 출처 조회

현재 외부 RAG/AI 연동 전 단계이므로 생성 시 `PROCESSING` 상태로 저장됩니다.

### 🧠 Admin RAG

관리자용 RAG 기준 문서 관리 기능입니다.

- RAG 문서 등록
- RAG 문서 목록 조회
- RAG 문서 상세 조회
- RAG 문서 메타데이터 수정
- RAG 문서 비활성화

관리자 권한(`ADMIN`)이 필요합니다.

### 💬 Quote

시공자가 매칭 요청에 대해 견적서를 작성하고 조회하는 기능입니다.

- 시공자 견적서 작성
- 견적서 상세 조회
- 내가 발송한 견적 목록 조회

### 🏗️ Work Order

선택된 견적 기반 시공 건을 조회합니다.

- 시공 건 상세 조회
- 고객/시공자 정보
- 일정, 금액, 리뷰 작성 가능 여부 확인

### 🔔 Notification

로그인 사용자의 인앱 알림 기능입니다.

- 알림 목록 조회
- 읽지 않은 알림 개수 조회
- 알림 읽음 처리

### ⭐ Review

완료된 시공 건에 대한 리뷰 기능입니다.

- 리뷰 작성
- 내가 작성한 리뷰 목록 조회
- 시공자 공개 리뷰 조회
- 리뷰 수정
- 리뷰 삭제
- 시공자 평균 평점/리뷰 수 갱신

---

## 🚫 제외된 API

아래 Matching API는 현재 구현 범위에서 제외되어 있습니다.

```text
POST /api/v1/matching-requests
GET  /api/v1/matching-requests
GET  /api/v1/matching-requests/{matching_request_id}
GET  /api/v1/matching-requests/{matching_request_id}/quotes
POST /api/v1/matching-requests/{matching_request_id}/select-quote
GET  /api/v1/contractors/me/matching-requests
```

---

## 🗄️ DB Migration

테이블 생성/변경은 Alembic으로 관리합니다.

```powershell
alembic upgrade head
```

현재 주요 테이블:

- users
- auth_tokens
- user_agreements
- reference_codes
- service_tasks
- contractor_profiles
- contractor_services
- ai_estimates
- risk_reports
- rag_documents
- rag_document_chunks
- risk_report_sources
- matching_requests
- matching_targets
- contractor_quotes
- work_orders
- reviews
- notifications
- attachments
- pricing_rules

---

## 📚 API 문서 확인

서버 실행 후 Swagger UI에서 전체 API와 요청/응답 스키마를 확인할 수 있습니다.

```text
http://localhost:8081/docs
```
