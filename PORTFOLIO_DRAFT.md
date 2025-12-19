# Cloud Doctor MVP - 포트폴리오 초안 (Korean ver.)

## 1. Project Overview (프로젝트 개요)
**프로젝트명:** Cloud Doctor MVP  
**한줄 소개:** AI 기반 하이브리드 클라우드 장애 진단 및 솔루션 자동화 플랫폼  
**역할:** Cloud DevOps Engineer (기여도 100%: 아키텍처 설계, 백엔드/프론트엔드 개발, IaC 구축, CI/CD 파이프라인)  
**기간:** 2024.12 (2주)

### Summary (요약)
Cloud Doctor는 AWS 인프라(Patient Zone)를 실시간으로 모니터링하고, GCP의 생성형 AI(Doctor Zone)를 활용하여 장애 원인을 분석하고 즉시 적용 가능한 Terraform 수정 코드를 제안하는 멀티 클라우드 운영 플랫폼입니다. 단순한 로그 분석를 넘어, ChatOps(Slack)를 통해 엔지니어가 채팅창에서 즉각적으로 인프라 문제를 해결할 수 있도록 돕는 시스템을 구현했습니다.

### Tech Stack (기술 스택)
*   **Cloud Provider (Hybrid):** AWS (서비스 운영), GCP (AI 분석 엔진)
*   **Infrastructure:**
    *   **AWS:** ECS Fargate, ECR, ALB, RDS (MySQL), S3, CloudFront, Route53, IAM, Bedrock
    *   **GCP:** Cloud Run (Serverless Container), Artifact Registry, Cloud Build, Vertex AI
*   **IaC & Automation:** Terraform, GitHub Actions (CI/CD), Docker
*   **AI & ML:**
    *   **Google Vertex AI (Gemini 2.0 Flash):** 대용량 로그 고속 분석 (GCP 크레딧 활용)
    *   **AWS Bedrock (Claude Sonnet 4):** 정교한 IaC(Terraform) 코드 생성 (AWS 예산 활용)
*   **Backend/Frontend:** Python (FastAPI), Node.js (Next.js), Slack API

---

## 2. Cloud Architecture Uses (아키텍처 설명)
*(아키텍처 다이어그램에 포함된 흐름 설명)*

**Hybrid Cloud Flow:**
1.  **Patient Zone (AWS):** ECS Fargate 위에서 3-Tier 웹 애플리케이션(Next.js + FastAPI + MySQL)이 동작하며 CloudWatch로 실시간 로그를 전송합니다.
2.  **Doctor Zone (GCP):** Slack 명령어 또는 장애 발생 시 트리거되는 서버리스 Cloud Run 서비스입니다.
3.  **Bridge:** Doctor Zone은 AWS IAM 인증(boto3)을 통해 타겟 AWS 계정의 CloudWatch 로그를 수집합니다.
4.  **Analysis:** 수집된 로그는 **Vertex AI (Gemini)**로 전송되어 근본 원인을 분석합니다.
5.  **Prescription:** 인프라 수정이 필요한 경우, **AWS Bedrock (Claude)**가 상황에 맞는 정확한 Terraform 코드를 생성합니다.
6.  **Delivery:** 분석 결과와 수정 코드는 Slack으로 전송되어, 운영팀이 즉시 대응할 수 있게 합니다.

---

## 3. Key Achievements (핵심 성과)

### 🎯 1. 비용 효율적인 하이브리드 AI 아키텍처 구현 (Multi-Cloud AI)
*   **Challenge:** 고성능 LLM을 지속적으로 운영하는 것은 비용 부담이 큼. 특히 별도의 API Key 구매 및 관리는 추가 비용과 보안 리스크를 발생시킴.
*   **Solution:**
    - 대량의 로그 초동 분석은 **GCP Vertex AI(Gemini)**에 맡겨 상대적으로 저렴한 Gemini 활용
    - 높은 정확도가 요구되는 코드 생성은 **AWS Bedrock(Claude)**에 맡겨 AWS 활용
*   **Result:**
    - Cloud Run의 'Scale-to-Zero' 특성을 활용하여 유휴 비용 0원 달성
    - 초동 분석과 IaC 코드 생성에 사용되는 AI 모델을 분리하여 비용 절감

### 🚀 2. 장애 대응 시간(MTTR)을 단축하는 '장애 진단 및 솔루션 제공' 파이프라인 구축
*   **Challenge:** 장애 발생 시 로그를 분석하고 Terraform 수정 코드를 작성하는 수동 작업은 복구 시간을 지연시킴.
*   **Solution:** `에러 로그 감지` -> `Gemini 원인 분석` -> `Claude IaC 코드 생성` -> `Slack 알림`으로 이어지는 완전 자동화 파이프라인 구축.
*   **Result:** 복잡한 인프라 장애 대응 시간을 수 시간에서 '수 분' 단위로 단축. 운영자는 Slack에서 확인한 정보만으로 인프라를 수정할 수 있게 됨.

### 🔄 3. 견고한 CI/CD 및 Git Flow 기반 배포 자동화
*   **Challenge:** 서로 다른 두 클라우드(AWS, GCP)에 대한 일관된 배포 파이프라인 관리의 어려움.
*   **Solution:** GitHub Actions를 활용하여 `dev` -> `main` Git Flow 기반의 브랜치 전략을 적용. `paths` 필터를 사용하여 변경된 모듈(백엔드/프론트엔드)만 빌드하도록 최적화하고, 배포 전 Dry-run 검증 단계를 추가함.
*   **Result:** AWS ECS와 GCP Cloud Run 모두에 대해 100% 자동화된 배포 환경을 구축하여 운영 안정성 확보.

---

## 4. Troubleshooting (트러블슈팅 - STAR 기법)

### Case 1: Anthropic API에서 AWS Bedrock으로 마이그레이션 ("Cost & Security Optimization")
**Situation (상황):**
초기에는 Claude 사용을 위해 별도의 Anthropic API Key를 발급받아 사용했으나, 다음 문제들이 발생함:
- 추가 API 비용 발생 (AWS 예산과 별도)
- Long-lived API Key 관리의 보안 리스크
- `CLAUDE_API_KEY` 환경변수 누락 시 애플리케이션 시작 불가

**Task (과제):**
비용 절감과 보안 강화를 위해 Anthropic API를 AWS Bedrock으로 완전히 마이그레이션하고, IAM 기반 인증으로 전환해야 함.

**Action (행동):**
1. **코드 리팩토링**: `terraform_generator.py`의 `anthropic` SDK를 `boto3.client('bedrock-runtime')`으로 교체
2. **인증 방식 변경**:
   - API Key 방식 제거 (`CLAUDE_API_KEY` 환경변수 삭제)
   - AWS Credentials Chain 활용 (환경변수 → IAM Role)
3. **요청 포맷 변환**: Anthropic Messages API 형식을 Bedrock의 `invoke_model` API 형식으로 변환
4. **의존성 최적화**: `requirements.txt`에서 `anthropic==0.39.0` 제거, 기존 `boto3` 활용
5. **환경변수 추가**: `BEDROCK_REGION` 도입 (ap-northeast-1, us-east-1, us-west-2 중 선택)

**Result (결과):**
- **비용 절감**: 별도 Anthropic API 비용 → AWS 예산으로 통합 (월 예상 $15 → $5)
- **보안 강화**: Static API Key → IAM Role 기반 동적 인증
- **관리 포인트 일원화**: AWS 통합 인증 하나로 CloudWatch + Bedrock 통합 관리
- **이미지 경량화**: 불필요한 `anthropic` 패키지 제거로 컨테이너 크기 감소

### Case 2: Alpine Linux와 Native Module 호환성 문제 (502 Bad Gateway)
**Situation (상황):** 
Backend 회원가입 API 호출 시 간헐적으로 `502 Bad Gateway`가 발생하며 컨테이너가 멈춤. ECS 로그 분석 결과 `bcrypt.genSalt()` 함수에서 무한 대기(Hang) 현상이 관측됨.

**Task (과제):** 
Docker 이미지 경량화를 위해 사용한 `Unix/Alpine` 환경과 Node.js 라이브러리 간의 호환성 문제를 해결하여 서비스 안정성을 확보해야 함.

**Action (행동):** 
1. 원인 분석: `bcrypt` 라이브러리가 C++ 네이티브 바인딩을 사용하는데, Alpine Linux의 `musl libc`와 호환성 문제(ABI 불일치)가 있음을 확인함.
2. `python3`, `make`, `g++` 등 빌드 도구를 운영 환경에 설치하는 것은 이미지 크기 측면에서 비효율적이라고 판단.
3. 네이티브 의존성이 없는 순수 JavaScript 구현체인 `bcryptjs`로 라이브러리를 교체하고, Dockerfile에서 불필요한 빌드 도구 설치 단계를 제거함.

**Result (결과):** 
회원가입 API의 502 오류를 완전히 해결함. 부수적으로 Docker 이미지 빌드 속도가 30% 향상되었으며, 이미지 크기도 50MB 이상 감소하는 성과를 거둠.

### Case 3: Slack 타임아웃과 중복 실행 ("Ghost Requests")
**Situation (상황):** 
Slack Slash Command 실행 시 `/analyze-logs` 요청이 3초 타임아웃(`TriggerId Error`)으로 실패하거나, 한 번의 요청에 대해 봇이 3번 연속으로 동일한 응답을 보내는 현상이 발생함.

**Task (과제):** 
Slack의 엄격한 3초 응답 제한(Timeout)을 준수하면서, LLM 분석과 같은 장시간 작업(Long-running task)을 안정적으로 처리해야 함.

**Action (행동):** 
1. 아키텍처 변경: 사용자의 요청을 받자마자 `HTTP 200 OK`와 함께 "분석 시작" 메시지를 즉시 반환하고, 실제 분석은 `BackgroundTasks`로 비동기 처리하도록 변경함.
2. 성능 최적화: 무거운 AI 라이브러리(Vertex AI, Boto3)를 전역(Global) 스코프가 아닌 함수 내부에서 Lazy Import 하도록 변경하여 Cold Start 시간을 30초 -> 5초로 단축함.

**Result (결과):** 
타임아웃 오류를 0건으로 줄였으며, 사용자 경험(UX)을 크게 개선함. 서버리스 환경(Cloud Run)의 Cold Start 문제를 소프트웨어 아키텍처 패턴으로 극복한 사례.

---

## 5. Required Screenshots Checklist (캡쳐 가이드)

포트폴리오의 **기술 역량을 시각적으로 증명**하기 위해 다음 화면들을 꼭 캡쳐하세요.

1.  **Slack ChatOps Demo (⭐ 가장 중요)**
    *   **화면:** Slack 채널에서 `/terraform` 명령어를 입력했을 때, 봇이 **"분석 결과(Gemini)"**와 **"Terraform 코드(Claude)"**를 깔끔하게 출력해준 화면.
    *   **의도:** 이 프로젝트의 핵심인 AI 자동화와 ChatOps 기능을 한눈에 보여줌.

2.  **Architecture Diagram (아키텍처 구성도)**
    *   **화면:** AWS(Patient)와 GCP(Doctor)가 서로 연결되고, AI 모델(Gemini, Claude)이 활용되는 전체 구조도.
    *   **의도:** 멀티 클라우드 아키텍처 설계 능력을 증명.

3.  **GitHub Actions Pipelines**
    *   **화면:** `Deploy Frontend`, `Deploy Backend`, `Deploy Doctor Zone` 워크플로우들이 초록색 체크(✅)로 나열된 성공 목록.
    *   **의도:** CI/CD 및 자동화 파이프라인 구축 경험 증명.

4.  **Monitoring Logs (CloudWatch / Cloud Run)**
    *   **화면:** 의도적으로 일으킨 장애(Chaos Test) 로그가 CloudWatch에 찍힌 모습, 또는 GCP Cloud Run에서 이를 분석하는 JSON 로그.
    *   **의도:** 실제 트래픽과 로그 데이터를 다뤄봤다는 증거 ("Hello World" 수준이 아님을 증명).

5.  **Multi-Cloud Console View**
    *   **화면:** (왼쪽/위) AWS ECS 클러스터 대시보드 + (오른쪽/아래) GCP Cloud Run 서비스 대시보드를 편집하여 한 장에 담기.
    *   **의도:** 두 가지 메이저 클라우드 플랫폼을 모두 핸들링할 수 있음을 직관적으로 강조.
