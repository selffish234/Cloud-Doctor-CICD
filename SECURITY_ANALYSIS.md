# Cloud Doctor MVP - 보안 취약점 분석 보고서

**분석 일자:** 2025-12-16
**분석 대상:** Cloud Doctor MVP (AWS-GCP Hybrid Architecture)
**분석가:** Antigravity (Google DeepMind)

---

## 1. 현재 AWS-GCP 연결 방식 분석

### 🔐 현재 방식: 장기 Access Key 기반 인증 (Long-lived IAM User Credentials)
현재 **GCP Doctor Zone(Cloud Run)**은 AWS 리소스(CloudWatch Logs, Bedrock)에 접근하기 위해 **AWS IAM User**의 **Access Key**를 사용하고 있습니다.

1.  **AWS:** IAM User(`cloud-doctor-user`) 생성 및 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` 발급.
2.  **Delivery:** GitHub Secrets에 저장된 키를 `gcloud run deploy` 시 환경 변수(`--set-env-vars`)로 주입.
3.  **GCP:** Cloud Run 컨테이너 내부에서 환경 변수를 읽어 `boto3` 클라이언트 초기화.

### ⚠️ 보안 취약점 (Security Risks)
이 방식은 MVP 단계에서는 빠르지만, 운영 환경에서는 **매우 높은 보안 위험**을 가집니다.

1.  **키 유출 위험 (Key Leakage):**
    *   컨테이너 환경 변수는 `gcloud run services describe` 명령어나 GCP 콘솔에서 조회 가능하므로, **Cloud Run 뷰어 권한**만 있어도 AWS 관리자급 키를 탈취할 수 있습니다.
    *   소스 코드나 로그에 실수로 키가 출력될 경우 영구적인 백도어가 됩니다.
2.  **키 순환 부재 (No Rotation):**
    *   현재 키는 수동으로 교체하지 않는 한 영원히 유효합니다. (Static Long-lived Credentials)
    *   키가 탈취되어도 즉시 알아차리기 어렵습니다.
3.  **권한 격리 부족:**
    *   하나의 IAM User가 CloudWatch 읽기 권한과 Bedrock 실행 권한을 모두 가집니다. (최소 권한 원칙 위배 가능성)

---

## 2. 프로젝트 전체 취약점 분석 (Top 3 Critical Issues)

### 🚨 1. GCP Doctor Zone의 무방비 노출 (Public Endpoint)
**위험도: Critical (치명적)**

*   **현황:** Cloud Run 배포 시 `--allow-unauthenticated` 옵션을 사용하여 **인터넷상의 누구든지** 서비스 URL(`https://doctor-zone-....run.app`)을 알고 있다면 접근할 수 있습니다.
*   **취약점:**
    *   공격자가 `/slack/command` 엔드포인트에 `POST` 요청을 보내 슬랙 명령어를 위조(Spoofing)할 수 있습니다.
    *   `/analyze` 엔드포인트를 무작위로 호출하여 **GCP 비용(Gemini/Claude 사용료) 폭탄**을 유발하거나, AWS Bedrock을 트리거하여 비용을 발생시킬 수 있습니다 (DoS/Resource Exhaustion).

### 🚨 2. Slack 요청 서명 검증 부재 (Missing Signature Verification)
**위험도: High (높음)**

*   **현황:** `doctor-gcp/main.py` 코드는 Slack에서 보낸 요청인지 확인하는 **전자 서명(`X-Slack-Signature`) 검증 로직이 없습니다.**
*   **취약점:**
    *   공격자가 `curl` 등으로 Slack 요청인 척 위장하여 `/slack/command`를 호출하면, 서버는 의심 없이 명령을 수행합니다.
    *   이는 1번 취약점(Public Endpoint)과 결합되어 **누구나 봇을 마음대로 조종**할 수 있게 만듭니다.

### ⚠️ 3. 하드코딩된 설정 및 환경 변수 의존성
**위험도: Medium (중간)**

*   **현황:** `deploy.sh`나 가이드 문서에서 `AWS_ACCESS_KEY_ID` 등을 쉘 변수로 처리하고 있습니다.
*   **취약점:**
    *   개발자의 로컬 `.bash_history`나 CI/CD 로그에 민감한 키 값이 평문으로 남을 가능성이 높습니다.
    *   `TROUBLESHOOTING.md` 등 문서에 예시로 실제 키 값이 들어갈 위험이 있습니다.

---

## 3. 권장 해결 방안 (Remediation Plan)

### ✅ Action 1: Workload Identity Federation 도입 (For AWS-GCP Connect)
AWS Access Key를 완전히 제거하고, **Keyless** 인증 방식으로 전환해야 합니다.

1.  **GCP:** 전용 Service Account 생성.
2.  **AWS:** IAM Role을 생성하되, 신뢰 관계(Trust Relationship)에 **"GCP의 OIDC Provider"**를 등록.
3.  **Flow:** GCP Cloud Run이 실행될 때 GCP Identity Token을 발급받아 AWS STS `AssumeRoleWithWebIdentity`를 호출 -> 임시 AWS 자격 증명 획득.
4.  **결과:** 코드나 환경 변수에 저장되는 영구적인 비밀 키가 **0개**가 됩니다.

### ✅ Action 2: Slack Request Signature 검증 로직 추가
`main.py`에 미들웨어를 추가하여 모든 `/slack/*` 요청의 서명을 검증해야 합니다.

```python
from slack_sdk.signature import SignatureVerifier

verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

@app.middleware("http")
async def verify_slack_signature(request: Request, call_next):
    if request.url.path.startswith("/slack/"):
        # 헤더와 바디를 사용하여 서명 검증
        if not verifier.is_valid_request(await request.body(), request.headers):
            return JSONResponse({"error": "invalid signature"}, status_code=403)
    return await call_next(request)
```

### ✅ Action 3: Cloud Run 접근 제어 강화
Slack은 Public Endpoint를 요구하므로 완전히 비공개로 할 수는 없지만, 최소한의 방어책이 필요합니다.

*   **서명 검증(Action 2) 필수 적용:** 인증되지 않은 요청은 403 Forbidden으로 즉시 차단하여 AI 비용 발생 방지.
*   **WAF (Web Application Firewall):** Cloud Load Balancing을 앞단에 두고 Cloud Armor를 적용하여 Slack IP 대역만 허용하거나 DDoS 방어 (엔터프라이즈급 대응).

---

## 4. 요약
현재 Cloud Doctor MVP는 **기능 구현(Functionality)**에 초점이 맞춰져 있어, **보안(Security)** 측면에서는 "모든 문이 열려 있는 상태"입니다.
특히 **공개된 Cloud Run 주소**와 **검증 없는 API 엔드포인트**는 비용 공격이나 데이터 유출로 이어질 수 있는 가장 시급한 개선 사항입니다.

포트폴리오나 면접에서는 **"현재는 MVP라 Access Key를 사용했지만, 실제 운영 환경에서는 Workload Identity Federation과 Slack Signature Verification을 필수적으로 도입해야 함을 인지하고 있다"**고 언급하는 것이 중요합니다.
