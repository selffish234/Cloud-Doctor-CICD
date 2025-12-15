# Patient Zone - Frontend

**Next.js 16 게시판 애플리케이션** - Cloud Doctor MVP의 환자 영역 프론트엔드

## 📋 개요

이 프론트엔드는 AWS CloudFront + S3 또는 독립 실행형 Next.js 서버로 배포되는 3-Tier 아키텍처의 프레젠테이션 계층입니다.

## 🛠️ 기술 스택

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4
- **Authentication**: JWT (localStorage)
- **Deployment**: CloudFront + S3 (Static) 또는 ECS Fargate (SSR)

## 📂 디렉토리 구조

```
frontend/
├── app/
│   ├── layout.tsx          # 루트 레이아웃 (네비게이션, 헤더, 푸터)
│   ├── page.tsx            # 홈페이지
│   ├── globals.css         # 글로벌 스타일
│   ├── login/
│   │   └── page.tsx        # 로그인/회원가입 페이지
│   └── posts/
│       ├── page.tsx        # 게시글 목록
│       ├── new/
│       │   └── page.tsx    # 새 게시글 작성
│       └── [id]/
│           └── page.tsx    # 게시글 상세보기
├── lib/
│   └── api.ts              # API 클라이언트 (TypeScript)
├── public/                 # 정적 파일
├── Dockerfile              # 컨테이너 이미지 빌드
├── package.json
└── README.md
```

## 🔑 주요 기능

### 1. 사용자 인증
- **회원가입**: 이메일, 비밀번호, 이름
- **로그인**: JWT 토큰 발급 및 localStorage 저장
- **로그아웃**: 토큰 삭제 및 홈으로 리다이렉트

### 2. 게시판 CRUD
- **목록 조회**: 최신순 20개 게시글 표시
- **상세 조회**: 게시글 내용 + 작성자 정보
- **게시글 작성**: 로그인 사용자만 가능
- **게시글 삭제**: 본인이 작성한 글만 가능

### 3. 클라이언트 상태 관리
- React Hooks (`useState`, `useEffect`)
- localStorage를 통한 인증 상태 유지
- 라우터 기반 페이지 전환 (`next/navigation`)

## 🚀 로컬 실행

### 1. 환경 변수 설정
```bash
# .env.local 파일 생성
echo "NEXT_PUBLIC_API_URL=http://localhost:3000" > .env.local
```

### 2. 의존성 설치 및 실행
```bash
npm install
npm run dev
```

브라우저에서 http://localhost:3001 접속

## 🐳 Docker 빌드

### Standalone 모드 빌드
```bash
docker build -t patient-frontend:latest .
docker run -p 3001:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-alb-endpoint.amazonaws.com \
  patient-frontend:latest
```

### ECR 푸시
```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태그 및 푸시
docker tag patient-frontend:latest {ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/patient-frontend:latest
docker push {ACCOUNT_ID}.dkr.ecr.ap-northeast-2.amazonaws.com/patient-frontend:latest
```

## 📡 API 연동

### API 클라이언트 (`lib/api.ts`)

모든 백엔드 API 호출은 TypeScript 타입이 지정된 `api.ts`를 통해 이루어집니다:

```typescript
import { login, register, getPosts, createPost, getToken } from '@/lib/api'

// 로그인
const response = await login('user@example.com', 'password123')
if (response.data) {
  saveToken(response.data.token)
  saveUser(response.data.user)
}

// 게시글 목록
const posts = await getPosts(20, 0)

// 게시글 작성
const token = getToken()
await createPost('제목', '내용', token)
```

### 지원 엔드포인트

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 |
| GET | `/api/auth/verify` | JWT 토큰 검증 |
| GET | `/api/posts` | 게시글 목록 |
| GET | `/api/posts/:id` | 게시글 상세 |
| POST | `/api/posts` | 게시글 작성 |
| DELETE | `/api/posts/:id` | 게시글 삭제 |

## 🎨 UI/UX

### Tailwind CSS 스타일링
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **색상 팔레트**: Blue (primary), Gray (neutral), Red (error)
- **컴포넌트**: 카드, 버튼, 폼, 네비게이션

### 사용자 경험
- **로딩 상태**: 스피너 및 "처리 중..." 메시지
- **에러 처리**: 빨간색 배너로 오류 메시지 표시
- **인증 확인**: 미로그인 시 `/login`으로 리다이렉트

## 🌐 배포 옵션

### Option 1: CloudFront + S3 (Static Export)
```bash
# next.config.js에 추가
module.exports = {
  output: 'export',
  images: { unoptimized: true }
}

# 빌드 및 S3 업로드
npm run build
aws s3 sync out/ s3://patient-frontend-bucket
```

### Option 2: ECS Fargate (SSR)
```bash
# Dockerfile을 사용하여 ECS 태스크로 배포
# 환경 변수로 NEXT_PUBLIC_API_URL 주입
```

## 🔐 보안 고려사항

1. **JWT 저장**: localStorage 사용 (XSS 공격에 주의)
   - 프로덕션에서는 HttpOnly 쿠키 권장
2. **CORS**: 백엔드 ALB에서 허용된 origin만 접근 가능
3. **환경 변수**: 민감한 정보는 `.env.local`에 저장 (`.gitignore`에 추가됨)
4. **HTTPS**: CloudFront에서 SSL/TLS 인증서 사용

## 📊 Megazone Cloud 포트폴리오 포인트

✅ **Next.js 16 최신 기술**: App Router, React 19, TypeScript
✅ **클라우드 네이티브**: Docker 컨테이너화, ECR 통합
✅ **3-Tier 아키텍처**: Frontend ↔ ALB ↔ Backend 분리
✅ **반응형 UI**: 모바일 친화적 사용자 경험
✅ **JWT 인증**: 보안 토큰 기반 세션 관리

---

**작성일**: 2024-12-10
**문의**: Cloud Doctor MVP 프로젝트 팀
