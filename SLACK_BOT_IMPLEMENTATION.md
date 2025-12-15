# Slack Bot 구현 계획

## 📋 개요

**목표:** MSP 관리직원이 Slack에서 명령어를 입력하면 자동으로 로그 분석 결과를 받는 시스템

**현재 방식:**
```
고객 불만 → 직원 → curl 명령어 입력 → 분석 결과
```

**원하는 방식:**
```
고객 불만 → 직원 → Slack에서 "/analyze-logs" 입력 → Slack으로 결과 수신
```

---

## 🎯 구현 단계

### Step 1: Slack App 생성 (5분)

1. https://api.slack.com/apps 접속
2. **"Create New App"** → **"From scratch"**
3. App Name: `Cloud Doctor`
4. Workspace 선택
5. App 생성 완료

### Step 2: Slash Command 추가 (3분)

**Slack App 설정에서:**

1. 좌측 메뉴: **"Slash Commands"** 클릭
2. **"Create New Command"** 클릭
3. 설정 입력:
   - **Command**: `/analyze-logs`
   - **Request URL**: `https://doctor-zone-XXXXX.a.run.app/slack/command`
   - **Short Description**: `Patient Zone 로그 분석 및 Terraform 코드 생성`
   - **Usage Hint**: `[시간(분), 기본값: 30]`
4. **"Save"** 클릭

**💡 참고:**
- Request URL은 Doctor Zone URL + `/slack/command`
- 현재 Doctor Zone URL 확인: `echo $DOCTOR_URL`

### Step 3: Doctor Zone 코드 수정 (10분)

#### 3-1. `main.py`에 `/slack/command` 엔드포인트 추가

**위치:** `/slack/test` 엔드포인트 아래

**추가할 코드:**

```python
@app.post("/slack/command")
async def slack_command(request: Request, background_tasks: BackgroundTasks):
    """
    Slack Slash Command handler

    /analyze-logs 30 → 최근 30분 로그 분석
    """
    try:
        # Parse Slack form data
        form_data = await request.form()

        command = form_data.get("command", "")
        text = form_data.get("text", "")
        user_name = form_data.get("user_name", "Unknown")

        logger.info(f"📨 Slack command: {command} from {user_name}")

        # Parse time range (default: 30 minutes)
        time_range = 30
        if text and text.isdigit():
            time_range = int(text)
            time_range = min(max(time_range, 5), 120)  # 5-120분 사이

        # Background task 시작
        background_tasks.add_task(
            analyze_and_send_to_slack,
            time_range_minutes=time_range,
            triggered_by=user_name
        )

        # 즉시 응답 (Slack 3초 제한)
        return {
            "response_type": "in_channel",
            "text": f"🔍 Patient Zone 로그 분석 중... (최근 {time_range}분)",
            "attachments": [{
                "color": "#36a64f",
                "text": f"분석 완료 시 결과를 전송합니다.\n요청자: @{user_name}"
            }]
        }

    except Exception as e:
        logger.error(f"❌ Slack command error: {str(e)}", exc_info=True)
        return {
            "response_type": "ephemeral",
            "text": f"❌ 오류 발생: {str(e)}"
        }


async def analyze_and_send_to_slack(time_range_minutes: int, triggered_by: str):
    """Background task: 로그 분석 후 Slack 전송"""
    try:
        logger.info(f"🔍 Background analysis started (by {triggered_by})")

        # Step 1: CloudWatch Logs 조회
        aws_client = AWSClientDirect(
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region=AWS_REGION
        )

        logs = aws_client.get_error_logs(
            log_group_name=LOG_GROUP_NAME,
            minutes=time_range_minutes,
            max_logs=100
        )

        logger.info(f"✅ Fetched {len(logs)} logs")

        # 로그 없으면 정상 메시지 전송
        if not logs:
            if SLACK_WEBHOOK_URL:
                notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
                notifier.send_simple_message(
                    f"✅ 로그 분석 완료 (요청: @{triggered_by})",
                    f"최근 {time_range_minutes}분간 오류 로그가 없습니다. 시스템 정상!"
                )
            return

        # Step 2: Gemini 분석
        analyzer = LogAnalyzer(
            project_id=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        analysis = analyzer.analyze_logs(logs)

        # Step 3: Terraform 생성
        terraform_result = None
        if analysis["detected_issues"]:
            generator = TerraformGenerator(api_key=CLAUDE_API_KEY)

            patient_info = {
                "region": AWS_REGION,
                "ecs_cluster": "patient-zone-cluster",
                "rds_instance": "patient-zone-mysql",
                "alb_name": "patient-zone-alb"
            }

            terraform_result = generator.generate_fix(analysis, patient_info)

        # Step 4: Slack 전송
        if SLACK_WEBHOOK_URL:
            notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
            slack_sent = notifier.send_alert(
                analysis=analysis,
                terraform_result=terraform_result,
                include_code=False
            )

            if slack_sent:
                logger.info("✅ Slack notification sent")

        logger.info(f"🎉 Analysis complete (by {triggered_by})")

    except Exception as e:
        logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)

        # 오류 메시지 Slack 전송
        if SLACK_WEBHOOK_URL:
            try:
                notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
                notifier.send_simple_message(
                    f"❌ 분석 실패 (요청: @{triggered_by})",
                    f"오류: {str(e)}"
                )
            except:
                pass
```

#### 3-2. `slack_notifier.py`에 `send_simple_message()` 추가

**위치:** `send_test_message()` 아래

```python
def send_simple_message(self, title: str, message: str) -> bool:
    """간단한 메시지 전송 (정상 상태, 오류 알림용)"""

    payload = {
        "text": title,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*\n\n{message}"
                }
            }
        ]
    }

    try:
        response = requests.post(
            self.webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send simple message: {str(e)}")
        return False
```

### Step 4: 재배포 (10분)

```bash
cd ~/workspace/cloud-doctor-mvp/doctor-gcp
./deploy.sh
```

### Step 5: Slack App 설치 (2분)

**Slack App 설정에서:**

1. 좌측 메뉴: **"Install App"** 클릭
2. **"Install to Workspace"** 클릭
3. 권한 승인
4. 완료!

---

## ✅ 사용 방법

### Slack에서 명령어 입력:

```
/analyze-logs
```
또는
```
/analyze-logs 60
```
(최근 60분 로그 분석)

### 예상 동작:

1. **즉시 응답 (3초 이내):**
   ```
   🔍 Patient Zone 로그 분석 중... (최근 30분)
   분석 완료 시 결과를 전송합니다.
   요청자: @your-name
   ```

2. **분석 완료 후 (10-30초):**
   ```
   ⚠️ Cloud Doctor 알림 - 경고

   요약
   N+1 쿼리 문제가 백엔드 애플리케이션에서 감지되었습니다.

   감지된 문제
   • slow-query

   권장사항
   1. 백엔드 로그에서 느린 쿼리를 식별하세요
   2. EXPLAIN을 사용하여 쿼리 실행 계획을 분석하세요
   ...

   🔧 Terraform 수정 코드 생성됨
   ...
   ```

---

## 🔧 트러블슈팅

### 문제 1: "Slash command failed"

**원인:** Request URL이 잘못되었거나 Doctor Zone이 응답하지 않음

**해결:**
```bash
# Doctor Zone URL 확인
echo $DOCTOR_URL

# Health check
curl $DOCTOR_URL/health

# Request URL을 다음으로 설정:
# https://your-doctor-zone.a.run.app/slack/command
```

### 문제 2: 응답은 오는데 Slack 알림이 안 옴

**원인:** Background task가 실패했거나 SLACK_WEBHOOK_URL이 잘못됨

**확인:**
```bash
# Cloud Run 로그 확인
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=doctor-zone" --limit 20 --format=json

# SLACK_WEBHOOK_URL 확인
gcloud run services describe doctor-zone --region asia-northeast3 --format="value(spec.template.spec.containers[0].env)" | grep SLACK
```

### 문제 3: "This app responded with Status Code 500"

**원인:** Python 코드에 오류가 있음

**해결:**
- Cloud Run 로그 확인
- 코드 수정 후 재배포

---

## 📝 참고 사항

### Slack 응답 시간 제한

- Slack은 **3초 이내** 응답 요구
- 즉시 응답(`return {...}`)하고 백그라운드에서 처리(`background_tasks.add_task()`)
- 분석 완료 후 Webhook으로 결과 전송

### Background Task 처리

- FastAPI의 `BackgroundTasks` 사용
- Cloud Run은 요청 완료 후에도 백그라운드 태스크가 완료될 때까지 대기
- 최대 300초 (deploy.sh의 `--timeout 300s`)

### 보안

- Slack App 권한은 최소한으로 (Slash Commands만)
- Request URL은 HTTPS 필수 (Cloud Run이 자동 제공)
- Webhook URL은 환경변수로 관리

---

## 🎯 완료 체크리스트

- [ ] Slack App 생성
- [ ] Slash Command 추가 (`/analyze-logs`)
- [ ] `main.py`에 `/slack/command` 엔드포인트 추가
- [ ] `slack_notifier.py`에 `send_simple_message()` 추가
- [ ] 재배포 (`./deploy.sh`)
- [ ] Slack App 워크스페이스에 설치
- [ ] `/analyze-logs` 명령어 테스트
- [ ] 결과 Slack으로 수신 확인

---

## 🚀 다음 단계 (선택사항)

### 1. 추가 명령어

```python
/check-patient-zone        # 간단한 health check
/analyze-logs 60           # 시간 지정
/fix-apply <issue-type>    # Terraform 자동 적용 (고급)
```

### 2. Interactive Components

- 버튼: "Terraform 적용", "무시", "자세히 보기"
- 모달: 상세 로그 표시

### 3. 자동 모니터링

- Cloud Scheduler로 주기적 실행
- 문제 발견 시에만 Slack 알림

---

## 📌 중요 파일 위치

```
doctor-gcp/
├── main.py                    # /slack/command 엔드포인트 추가
├── slack_notifier.py          # send_simple_message() 추가
└── deploy.sh                  # 배포 스크립트
```

## 🔗 관련 문서

- Slack API Docs: https://api.slack.com/interactivity/slash-commands
- FastAPI BackgroundTasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Cloud Run Timeouts: https://cloud.google.com/run/docs/configuring/request-timeout
