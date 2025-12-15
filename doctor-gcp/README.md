# Doctor Zone - Enhanced AI Monitoring

**GCP Cloud Run 기반 하이브리드 클라우드 모니터링 시스템**

AWS Patient Zone의 CloudWatch Logs를 실시간 분석하고, AI로 문제를 진단하며, Terraform 코드를 자동 생성합니다.

## 📋 개요

Doctor Zone은 **Gemini 2.5 Flash**로 로그를 분석하고, **Claude Sonnet 4.5**로 인프라 수정 코드를 생성하는 AI 기반 SRE 도구입니다.

### 아키텍처

```
AWS Patient Zone (CloudWatch Logs)
        ↓
    [OIDC Auth]
        ↓
GCP Doctor Zone (Cloud Run)
        ↓
    ┌───────┴───────┐
    ↓               ↓
Gemini 2.5      Claude 3.5
(Log Analysis)  (Terraform Gen)
    ↓               ↓
    └───────┬───────┘
            ↓
      Slack Notification
```

## 🎯 주요 기능

### 1. 로그 분석 (Gemini 2.5 Flash)
- CloudWatch Logs에서 에러 패턴 감지
- 7가지 장애 시나리오 자동 분류:
  - `db-failure`: 데이터베이스 연결 실패
  - `pool-exhaustion`: 커넥션 풀 고갈
  - `memory-leak`: 메모리 누수
  - `slow-query`: N+1 쿼리 문제
  - `api-timeout`: 외부 API 타임아웃
  - `jwt-expiry`: JWT 토큰 만료
  - `high-cpu`: 높은 CPU 사용률

### 2. Terraform 코드 생성 (Claude Sonnet 4.5)
- 감지된 문제에 대한 IaC 수정 코드 자동 생성
- ECS, RDS, ALB 설정 최적화
- 프로덕션 안전성 고려 (무중단 배포)

### 3. Slack 통합
- 실시간 알림 (심각도별 색상 구분)
- 분석 결과 + Terraform 코드 전송
- 적용 가이드 포함

## 🛠️ 사전 준비

### 1. API 키 발급

```bash
# Gemini API Key
# https://aistudio.google.com/app/apikey

# Claude API Key
# https://console.anthropic.com/

# Slack Webhook URL
# https://api.slack.com/messaging/webhooks
```

### 2. AWS 자격증명

```bash
# AWS Access Key (CloudWatch Logs 읽기 권한 필요)
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cat > .env <<EOF
GEMINI_API_KEY=your-gemini-api-key
CLAUDE_API_KEY=your-claude-api-key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-northeast-2
LOG_GROUP_NAME=/ecs/patient-zone
EOF
```

## 🚀 로컬 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 서버 시작

```bash
python main.py
```

서버가 http://localhost:8080 에서 실행됩니다.

### 3. 테스트

```bash
# Health Check
curl http://localhost:8080/health

# Slack 연동 테스트
curl -X POST http://localhost:8080/slack/test

# 로그 분석 실행
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "time_range_minutes": 30,
    "max_logs": 100,
    "generate_terraform": true,
    "send_to_slack": true
  }'
```

## ☁️ GCP Cloud Run 배포

### 1. Docker 이미지 빌드

```bash
# GCP 프로젝트 설정
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=asia-northeast3

# Artifact Registry 인증
gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev

# 이미지 빌드 및 푸시
docker build -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/cloud-doctor/doctor-zone:latest .
docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/cloud-doctor/doctor-zone:latest
```

### 2. Cloud Run 배포

```bash
gcloud run deploy doctor-zone \
  --image ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/cloud-doctor/doctor-zone:latest \
  --platform managed \
  --region ${GCP_REGION} \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=${GEMINI_API_KEY}" \
  --set-env-vars "CLAUDE_API_KEY=${CLAUDE_API_KEY}" \
  --set-env-vars "SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}" \
  --set-env-vars "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" \
  --set-env-vars "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" \
  --set-env-vars "AWS_REGION=ap-northeast-2" \
  --set-env-vars "LOG_GROUP_NAME=/ecs/patient-zone" \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 3
```

### 3. 배포 확인

```bash
# 서비스 URL 확인
gcloud run services describe doctor-zone --region ${GCP_REGION} --format 'value(status.url)'

# Health Check
SERVICE_URL=$(gcloud run services describe doctor-zone --region ${GCP_REGION} --format 'value(status.url)')
curl ${SERVICE_URL}/health
```

## 📡 API 엔드포인트

### POST /analyze

로그 분석 및 Terraform 코드 생성

**Request:**
```json
{
  "time_range_minutes": 30,
  "max_logs": 100,
  "generate_terraform": true,
  "send_to_slack": true
}
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2024-12-10T...",
  "summary": {
    "total_logs_analyzed": 47,
    "time_range_minutes": 30,
    "log_group": "/ecs/patient-zone"
  },
  "analysis": {
    "detected_issues": ["slow-query", "memory-leak"],
    "severity": "warning",
    "summary": "...",
    "recommendations": ["..."],
    "affected_resources": ["..."]
  },
  "terraform": {
    "terraform_code": "...",
    "explanation": "...",
    "apply_instructions": ["..."]
  },
  "slack_sent": true
}
```

### POST /slack/test

Slack Webhook 연동 테스트

## 🔍 워크플로우

1. **CloudWatch Logs 수집**
   - AWS SDK (boto3)로 Patient Zone CloudWatch Logs 조회
   - 에러 필터 패턴 적용

2. **AI 로그 분석 (Gemini)**
   - 7가지 장애 시나리오 감지
   - 심각도 평가 (critical/warning/info)
   - 영향받은 리소스 식별
   - 권장사항 생성

3. **Terraform 코드 생성 (Claude)**
   - 감지된 문제에 대한 IaC 수정안 작성
   - 프로덕션 안전성 고려
   - 적용 가이드 포함

4. **Slack 알림**
   - 분석 결과 전송
   - Terraform 코드 미리보기
   - 심각도별 색상 구분

## 📊 모니터링

### Cloud Run 로그 확인

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=doctor-zone" --limit 50
```

### 메트릭 확인

```bash
# 요청 수
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"'

# 응답 시간
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_latencies"'
```

## 💰 비용 최적화

- **Cloud Run**: 요청 기반 과금 (무료 티어: 월 200만 요청)
- **Gemini API**: 무료 티어 사용 (분당 15 RPM, 일일 1500 RPM)
- **Claude API**: 종량제 (입력 $3/MTok, 출력 $15/MTok)
- **예상 월 비용**: ~$10-20 (테스트 환경)

## 🎯 Megazone Cloud 포트폴리오 포인트

✅ **Hybrid Cloud**: AWS + GCP 통합 아키텍처
✅ **AI 활용**: Gemini (분석) + Claude (코드생성) 2단계 AI 파이프라인
✅ **IaC 자동화**: 문제 → Terraform 코드 자동 생성
✅ **SRE 실무**: CloudWatch Logs 기반 장애 감지
✅ **Slack DevOps**: 실시간 알림 및 협업 도구 통합

---

**작성일**: 2024-12-10
**문의**: Cloud Doctor MVP 프로젝트 팀
