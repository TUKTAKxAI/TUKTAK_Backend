# TUKTAK Backend

FastAPI 기반 TukTak 백엔드입니다. 현재 인증, 사용자·시공자 가입, 약관 동의,
JWT 갱신/폐기, MySQL 비동기 연결 및 Alembic 초기 마이그레이션이 구성되어 있습니다.

## 로컬 실행

1. `.env.example`을 `.env`로 복사하고 DB 접속값과 32자 이상의 `SECRET_KEY`를 설정합니다.
2. 의존성을 설치합니다.
3. 마이그레이션을 적용합니다.
4. API 서버를 실행합니다.

```powershell
python -m pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8081
```

Swagger UI는 `http://localhost:8081/docs`, 상태 확인은 `/health`에서 제공합니다.

## 인증 API

- `GET /api/v1/agreements/required`
- `POST /api/v1/auth/signup/customer`
- `POST /api/v1/auth/signup/contractor`
- `GET /api/v1/auth/email-availability?email=...`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

보호 API는 로그인 응답의 액세스 토큰을 `Authorization: Bearer <token>`으로 전달합니다.
리프레시 토큰은 DB에 원문이 아닌 SHA-256 해시로 저장되며 갱신 시 회전됩니다...
