# 🩺 Cloud Doctor MVP

> **Hybrid Cloud Log Analyst**: AWS 컨테이너 환경의 장애를 GCP AI가 외부에서 진단하는 하이브리드 클라우드 솔루션

**메가존클라우드 채용 포트폴리오** | 공고 마감: 2024.12.19

---

## 📋 프로젝트 개요

Cloud Doctor는 **AWS의 컨테이너 환경에서 발생한 장애를 GCP의 AI가 Cross-Cloud로 진단**하는 MVP입니다.

### 핵심 가치 제안

- **Hybrid Cloud Integration**: AWS + GCP 두 클라우드를 유기적으로 연결
- **Keyless Security**: AssumeRole 기반 임시 자격증명 사용 (장기 키 노출 방지)
- **AI-Powered Analysis**: Gemini 2.5를 활용한 지능형 로그 분석
- **Enterprise Ready**: ECR, CloudWatch, IAM 등 엔터프라이즈급 AWS 서비스 활용

---

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        Patient Zone (AWS)                        │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────────┐  │
│  │  ECR (Private│──>   │  EC2 (t2.    │──>   │  CloudWatch   │  │
│  │  Registry)   │      │  micro)      │      │  Logs         │  │
│  │              │      │  + Docker    │      │               │  │
│  │  chaos-app   │      │  + chaos-app │      │  /aws/ec2/... │  │
│  └──────────────┘      └──────────────┘      └───────────────┘  │
│                                                        │          │
│                        ┌───────────────────────────────┘          │
│                        │  IAM Role (Trust Policy)                │
│                        │  Allow: GCP Service Account             │
└────────────────────────┼─────────────────────────────────────────┘
                         │
                         │ AssumeRole (임시 자격증명 발급)
                         │
┌────────────────────────┼─────────────────────────────────────────┐
│                        ▼       Doctor Zone (GCP)                 │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐   │
│  │  Cloud Run   │<──│  Vertex AI   │   │  Secret Manager    │   │
│  │  (FastAPI)   │   │  Gemini 2.5  │   │  (환경변수 관리)   │   │
│  │              │   │  Flash       │   └────────────────────┘   │
│  │  /analyze    │   └──────────────┘                            │
│  └──────────────┘                                                │
│         │                                                         │
│         └────────────> Slack (ChatOps Interface)                 │
└─────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름

1. **Chaos Generation**: AWS EC2의 컨테이너가 의도적인 에러 로그 생성 → CloudWatch
2. **Trigger**: 운영자가 Slack에서 `/doctor analyze` 명령 실행
3. **Authentication**: GCP Cloud Run이 AWS STS에 AssumeRole 요청 → 임시 자격증명 획득
4. **Log Fetch**: Cloud Run이 AWS CloudWatch Logs API 호출 → 에러 로그 수집
5. **AI Analysis**: Gemini 2.5가 로그 분석 → 근본 원인 및 해결책 도출
6. **Report**: 분석 결과를 Slack으로 전송

---

## 🎯 메가존클라우드 채용 어필 포인트

### 1. **ECR 활용 능력**
- Docker Hub가 아닌 **AWS Native Registry(ECR)** 사용
- Private Registry 관리 및 이미지 버전 관리 경험

### 2. **Hybrid Cloud 보안 구현**
- **AssumeRole 기반 Cross-Cloud 인증**
  - 장기 Access Key 대신 임시 자격증명 사용 (보안 모범 사례)
  - Trust Relationship 설정으로 GCP Service Account 신뢰
- **Keyless Authentication** 구현

### 3. **AI 기반 자동화**
- Gemini 2.5를 활용한 로그 분석 자동화
- Prompt Engineering을 통한 구조화된 출력(JSON)
- 운영 효율성 향상 (수동 로그 분석 → AI 자동 진단)

### 4. **클라우드 네이티브 설계**
- **서버리스 아키텍처** (Cloud Run): 비용 효율적, 자동 확장
- **컨테이너 기반 배포** (Docker): 일관된 환경, 이식성
- **ChatOps 통합** (Slack): DevOps 문화 적용

---

## 🚀 빠른 시작

### 사전 요구사항

- **AWS 계정** (EC2, ECR, CloudWatch Logs, IAM 권한)
- **GCP 계정** (Cloud Run, Vertex AI 권한)
- **Slack Workspace** (선택사항)
- Docker 설치
- AWS CLI & gcloud CLI 설치

### 1단계: Patient (AWS) 배포

#### 1.1 ECR 리포지토리 생성

```bash
# ECR 리포지토리 생성
aws ecr create-repository \
  --repository-name chaos-app \
  --region eu-west-1

# ECR 로그인
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com
```

#### 1.2 Docker 이미지 빌드 & 푸시

```bash
cd patient-aws/

# 이미지 빌드
docker build -t chaos-app:latest .

# ECR에 태그 지정
docker tag chaos-app:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com/chaos-app:latest

# ECR에 푸시
docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com/chaos-app:latest
```

#### 1.3 EC2에서 컨테이너 실행

```bash
# EC2 인스턴스에 SSH 접속 후
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com

# 이미지 Pull
docker pull <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com/chaos-app:latest

# 컨테이너 실행 (로그를 CloudWatch로 전송하려면 awslogs driver 설정)
docker run -d \
  --log-driver=awslogs \
  --log-opt awslogs-region=eu-west-1 \
  --log-opt awslogs-group=/aws/ec2/chaos-app \
  --log-opt awslogs-create-group=true \
  <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.eu-west-1.amazonaws.com/chaos-app:latest
```

#### 1.4 IAM Role 설정 (Trust Relationship)

AWS IAM 콘솔에서 다음 Trust Policy를 가진 Role 생성:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "accounts.google.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "accounts.google.com:aud": "<GCP_SERVICE_ACCOUNT_EMAIL>"
        }
      }
    }
  ]
}
```

권한 정책: `CloudWatchLogsReadOnlyAccess`

### 2단계: Doctor (GCP) 배포

#### 2.1 Docker 이미지 빌드 & GCR 푸시

```bash
cd doctor-gcp/

# GCP 프로젝트 설정
export PROJECT_ID=<YOUR_GCP_PROJECT_ID>
gcloud config set project $PROJECT_ID

# 이미지 빌드
docker build -t gcr.io/$PROJECT_ID/cloud-doctor:latest .

# GCR에 푸시
docker push gcr.io/$PROJECT_ID/cloud-doctor:latest
```

#### 2.2 Cloud Run 배포

```bash
gcloud run deploy cloud-doctor \
  --image gcr.io/$PROJECT_ID/cloud-doctor:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AWS_ROLE_ARN=arn:aws:iam::<AWS_ACCOUNT_ID>:role/CloudDoctorRole \
  --set-env-vars AWS_LOG_GROUP_NAME=/aws/ec2/chaos-app \
  --set-env-vars AWS_REGION=eu-west-1 \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --set-env-vars GCP_LOCATION=us-central1
```

#### 2.3 Vertex AI 활성화

```bash
# Vertex AI API 활성화
gcloud services enable aiplatform.googleapis.com
```

### 3단계: 테스트

#### API 직접 호출 테스트

```bash
curl -X POST https://<CLOUD_RUN_URL>/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "time_range_minutes": 30,
    "max_logs": 50
  }'
```

#### 응답 예시

```json
{
  "status": "success",
  "timestamp": "2024-01-10T12:34:56",
  "summary": {
    "total_logs_analyzed": 23,
    "log_group": "/aws/ec2/chaos-app",
    "time_range_minutes": 30
  },
  "analysis": {
    "summary": "데이터베이스 연결 실패 및 메모리 부족 에러 발생",
    "severity": "HIGH",
    "issues": [
      {
        "type": "Database Connection Failure",
        "count": 15,
        "description": "10.0.2.55의 데이터베이스에 연결할 수 없음",
        "root_cause": "네트워크 문제 또는 DB 서버 다운",
        "solution": "DB 서버 상태 확인 및 네트워크 라우팅 점검"
      }
    ],
    "priority_actions": [
      "데이터베이스 서버 헬스체크 실행",
      "네트워크 연결 상태 확인",
      "CloudWatch 알람 설정 검토"
    ]
  }
}
```

---

## 📁 프로젝트 구조

```
cloud-doctor-mvp/
├── patient-aws/              # AWS 환경 (고장난 시스템)
│   ├── app.py                # 에러 로그 생성 Python 스크립트
│   ├── Dockerfile            # ECR용 도커 이미지
│   └── requirements.txt      # Python 의존성
│
├── doctor-gcp/               # GCP 환경 (진단 시스템)
│   ├── main.py               # FastAPI 엔트리포인트
│   ├── aws_client.py         # AWS AssumeRole & CloudWatch 클라이언트
│   ├── ai_engine.py          # Gemini AI 분석 엔진
│   ├── Dockerfile            # Cloud Run용 도커 이미지
│   └── requirements.txt      # Python 의존성
│
└── README.md                 # 프로젝트 문서 (현재 파일)
```

---

## 🔐 보안 고려사항

### 구현된 보안 기능

1. **Keyless Authentication**
   - AWS Access Key를 코드에 저장하지 않음
   - AssumeRole을 통한 임시 자격증명만 사용 (1시간 유효)

2. **최소 권한 원칙 (Least Privilege)**
   - IAM Role에는 CloudWatch Logs 읽기 권한만 부여
   - GCP Service Account도 필요한 API만 호출

3. **Trust Relationship 제한**
   - 특정 GCP Service Account만 AssumeRole 가능

4. **비root 컨테이너 실행**
   - Dockerfile에서 `appuser` 생성 및 사용

### 프로덕션 환경 추가 권장 사항

- Secret Manager를 통한 환경변수 관리
- VPC Peering으로 프라이빗 네트워크 연결
- CloudTrail 로깅 활성화
- Cloud Armor를 통한 DDoS 방어

---

## 🎓 기술 스택

| 영역 | 기술 | 용도 |
|------|------|------|
| **AWS** | EC2 | 컨테이너 실행 환경 |
| | ECR | Private Docker Registry |
| | CloudWatch Logs | 로그 집계 및 저장 |
| | IAM | AssumeRole 기반 인증 |
| | STS | 임시 자격증명 발급 |
| **GCP** | Cloud Run | 서버리스 API 호스팅 |
| | Vertex AI | Gemini 2.5 Flash 모델 |
| | Secret Manager | 환경변수 보안 관리 |
| **언어/프레임워크** | Python 3.11 | 백엔드 언어 |
| | FastAPI | REST API 프레임워크 |
| | Boto3 | AWS SDK |
| **DevOps** | Docker | 컨테이너화 |
| | GitHub Actions | CI/CD (예정) |
| **인터페이스** | Slack | ChatOps |

---

## 📊 성능 및 비용

### 예상 비용 (월 30일 기준)

- **AWS**
  - EC2 t2.micro (프리티어): $0
  - CloudWatch Logs (1GB): ~$0.50
  - ECR 스토리지 (500MB): ~$0.05

- **GCP**
  - Cloud Run (월 100만 요청): ~$0.40
  - Vertex AI (월 1,000회 분석): ~$2.00

**총 예상 비용: 약 $3/월** (프리티어 활용 시 더 낮음)

### 응답 시간

- 로그 수집: ~2초
- AI 분석: ~3-5초
- **총 응답 시간: ~7초**

---

## 🚧 향후 개선 계획

### Phase 2 (확장 기능)
- [ ] Slack Slash Command 완전 통합
- [ ] 실시간 알림 (CloudWatch Events → EventBridge → Cloud Run)
- [ ] 대시보드 구축 (Grafana/Looker)
- [ ] 여러 AWS 계정 지원 (Multi-Account)

### Phase 3 (엔터프라이즈)
- [ ] Kubernetes 환경 지원 (EKS, GKE)
- [ ] Azure 통합 (Triple Cloud)
- [ ] 자동 복구 (Auto-Remediation)
- [ ] 머신러닝 기반 이상 탐지

---

## 📝 라이센스

이 프로젝트는 포트폴리오 목적으로 제작되었습니다.

---

## 👤 제작자

**메가존클라우드 지원자**

- 목표: 클라우드 엔지니어로 Hybrid/Multi-Cloud 환경에서 고객의 문제를 해결하고 싶습니다.
- 강점: AWS/GCP 실무 경험, 보안 중심 설계, AI 기술 활용

---

## 🙏 감사의 말

이 프로젝트는 메가존클라우드의 **"ECR, Hybrid Cloud, AI"** 기술 요구사항을 충족하기 위해 설계되었습니다.

실제 고객사 환경에서 발생할 수 있는 Cross-Cloud 로그 분석 시나리오를 MVP로 구현하였으며,
이를 통해 **실무 즉시 투입 가능한 엔지니어**임을 증명하고자 합니다.

---

**Made with ❤️ for Megazone Cloud**
