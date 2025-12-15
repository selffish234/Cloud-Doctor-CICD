# Patient Backend - Cloud Doctor

> AWS 3-Tier 아키텍처의 Backend API 서버
> Express + Sequelize + MySQL (RDS)

---

## 📋 개요

이 Backend는 Cloud Doctor 프로젝트의 **Patient Zone (고객사 시뮬레이션)**입니다.

- **목적**: MSP가 관제할 대상 시스템
- **역할**: 의도적인 장애 발생 → CloudWatch Logs 수집 → Doctor(GCP)가 분석

---

## 🏗️ 아키텍처

```
ALB → ECS Fargate (이 Backend) → RDS MySQL
                ↓
         CloudWatch Logs
                ↓
         Doctor (GCP AI)
```

---

## 📁 디렉토리 구조

```
backend/
├── src/
│   ├── config/
│   │   └── database.js       # RDS MySQL 연결 설정
│   ├── models/
│   │   ├── User.js           # 사용자 모델
│   │   ├── Post.js           # 게시글 모델
│   │   └── index.js          # 모델 통합
│   ├── routes/
│   │   ├── auth.js           # 인증 API (로그인/회원가입)
│   │   └── posts.js          # 게시판 API (CRUD)
│   ├── chaos/                # ⭐ 장애 시나리오 7종
│   │   ├── db-failure.js     # DB 연결 실패
│   │   ├── pool-exhaustion.js # Connection Pool 고갈
│   │   ├── memory-leak.js    # 메모리 누수
│   │   ├── slow-query.js     # 느린 쿼리 (N+1)
│   │   ├── api-timeout.js    # API 타임아웃
│   │   ├── jwt-expiry.js     # JWT 만료
│   │   └── high-cpu.js       # 높은 CPU 사용률
│   └── index.js              # Express 서버
├── Dockerfile
├── package.json
└── .env.example
```

---

## 🚀 로컬 실행

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 RDS 연결 정보 입력
```

### 2. 의존성 설치

```bash
npm install
```

### 3. 서버 시작

```bash
npm start        # Production
npm run dev      # Development (nodemon)
```

---

## 🐳 Docker 빌드

```bash
# 이미지 빌드
docker build -t patient-backend .

# 로컬 실행 (DB 연결 필요)
docker run -d \
  --name patient-backend \
  -p 3000:3000 \
  --env-file .env \
  patient-backend
```

---

## 📡 API 엔드포인트

### 헬스체크

```
GET  /              # 기본 헬스체크
GET  /health        # 상세 헬스체크 (DB 포함)
GET  /api/metrics   # 시스템 메트릭
```

### 인증

```
POST /api/auth/register   # 회원가입
POST /api/auth/login      # 로그인
GET  /api/auth/verify     # 토큰 검증
```

### 게시판

```
GET    /api/posts         # 게시글 목록
GET    /api/posts/:id     # 게시글 상세
POST   /api/posts         # 게시글 작성 (인증 필요)
DELETE /api/posts/:id     # 게시글 삭제 (본인만)
```

### 장애 시나리오 (테스트용)

```
POST /api/chaos/db-fail          # DB 연결 실패
POST /api/chaos/pool-exhaustion  # Connection Pool 고갈
POST /api/chaos/memory-leak      # 메모리 누수 (30초)
POST /api/chaos/slow-query       # 느린 쿼리 (N+1)
POST /api/chaos/api-timeout      # API 타임아웃
POST /api/chaos/jwt-expiry       # JWT 만료
POST /api/chaos/high-cpu         # 높은 CPU 사용률 (30초)
```

---

## 💥 장애 시나리오 설명

| 시나리오 | 트리거 | 로그 패턴 | Doctor 기대 진단 |
|---------|--------|----------|------------------|
| **DB 연결 실패** | 잘못된 DB 엔드포인트 | `SequelizeConnectionError` | RDS 엔드포인트 확인 필요 |
| **Pool 고갈** | 동시 100개 요청 | `ResourceRequest timed out` | ECS Task 수 증가 권장 |
| **메모리 누수** | 대량 데이터 캐싱 | `JavaScript heap out of memory` | Task 메모리 512MB → 1GB |
| **느린 쿼리** | N+1 문제 | `Query execution time: XXXms` | JOIN 쿼리 사용 권장 |
| **API 타임아웃** | 외부 서비스 지연 | `ETIMEDOUT` | 타임아웃 설정 증가 |
| **JWT 만료** | 짧은 토큰 수명 | `TokenExpiredError` | expiresIn 24h로 증가 |
| **높은 CPU** | 무한 루프 | `CPU usage: 98%` | 코드 최적화 필요 |

---

## 🧪 장애 시나리오 테스트

### CLI에서 직접 실행

```bash
npm run chaos:db-fail
npm run chaos:slow-query
npm run chaos:memory-leak
```

### curl로 API 호출

```bash
curl -X POST http://localhost:3000/api/chaos/db-fail
curl -X POST http://localhost:3000/api/chaos/slow-query
```

---

## 🔐 환경변수

| 변수 | 설명 | 예시 |
|------|------|------|
| `NODE_ENV` | 실행 환경 | `production` |
| `PORT` | 서버 포트 | `3000` |
| `DB_HOST` | RDS 엔드포인트 | `xxx.eu-west-1.rds.amazonaws.com` |
| `DB_PORT` | DB 포트 | `3306` |
| `DB_NAME` | 데이터베이스 이름 | `patient_db` |
| `DB_USER` | DB 사용자 | `admin` |
| `DB_PASSWORD` | DB 비밀번호 | `SecurePassword123!` |
| `JWT_SECRET` | JWT 서명 키 | `your-secret-key` |
| `CHAOS_MODE` | 장애 모드 활성화 | `false` |

---

## 📊 데이터베이스 스키마

### users 테이블

```sql
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(255) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  name VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### posts 테이블

```sql
CREATE TABLE posts (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 🩺 Doctor가 분석할 로그 예시

```json
{
  "timestamp": "2024-12-10T10:30:45.123Z",
  "level": "error",
  "type": "DB CONNECTION ERROR",
  "error": "SequelizeConnectionError: connect ETIMEDOUT",
  "host": "cloud-doctor-patient-db.xxx.eu-west-1.rds.amazonaws.com",
  "code": "ETIMEDOUT"
}
```

---

**Made with ❤️ for Megazone Cloud**
