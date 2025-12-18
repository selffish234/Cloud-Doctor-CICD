"""
Cloud Doctor - Enhanced Doctor Zone Server (Vertex AI Version)
Uses GCP credits! Vertex AI for Gemini + Claude API for Terraform generation
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# SlackNotifier만 상단에서 import (가벼운 모듈)
from slack_notifier import SlackNotifier

# 무거운 모듈들은 필요한 함수 안에서만 lazy import
# - AWSClientDirect, LogAnalyzer, TerraformGenerator

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Cloud Doctor - Enhanced (Vertex AI)",
    description="Hybrid Cloud Monitoring with Vertex AI Gemini + Claude",
    version="2.1.0"
)

# Environment variables
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
# CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY") # Removed: Using AWS Bedrock
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
# OIDC Keyless Authentication - AWS Access Key 불필요
AWS_ROLE_ARN = os.getenv("AWS_ROLE_ARN")  # e.g., arn:aws:iam::123456789012:role/CloudDoctorRole
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
LOG_GROUP_NAME = os.getenv("LOG_GROUP_NAME", "/ecs/patient-zone")


def check_environment():
    """Check required environment variables"""
    required = {
        "GCP_PROJECT_ID": GCP_PROJECT_ID,
        # "CLAUDE_API_KEY": CLAUDE_API_KEY,  # Removed: using AWS Bedrock (OIDC)
        "AWS_ROLE_ARN": AWS_ROLE_ARN  # OIDC Keyless - Access Key 불필요
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
    else:
        logger.info("All required environment variables configured")
        logger.info(f"   AWS Authentication: OIDC Keyless (Role: {AWS_ROLE_ARN})")

    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set - notifications will be disabled")


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Cloud Doctor Enhanced (Vertex AI) - Starting...")
    logger.info("   Patient Zone: AWS (CloudWatch Logs)")
    logger.info("   Doctor Zone:  GCP Cloud Run")
    logger.info("   AI Analysis:  Vertex AI Gemini 2.0 Flash")
    logger.info("   IaC Generate: Claude Sonnet 4.5")
    logger.info("   AWS Auth:     OIDC Keyless (No Access Keys!)")
    logger.info("   Uses GCP Credits!")
    logger.info("=" * 60)
    check_environment()
    logger.info("Doctor Zone Ready")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Cloud Doctor Enhanced (Vertex AI)",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "features": {
            "log_analysis": "Vertex AI Gemini 2.0 Flash",
            "terraform_generation": "Claude Sonnet 4.5",
            "slack_notifications": bool(SLACK_WEBHOOK_URL),
            "uses_gcp_credits": True
        }
    }


@app.get("/health")
async def health_check():
    """GCP Cloud Run health check"""
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_patient_zone(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Analyze Patient Zone logs and generate Terraform fixes

    Request Body:
    {
        "time_range_minutes": 30,
        "max_logs": 100,
        "generate_terraform": true,
        "send_to_slack": true
    }
    """
    try:
        # Parse request
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}

        time_range = body.get("time_range_minutes", 30)
        max_logs = body.get("max_logs", 100)
        generate_terraform = body.get("generate_terraform", True)
        send_to_slack = body.get("send_to_slack", bool(SLACK_WEBHOOK_URL))

        logger.info(f"Starting analysis (last {time_range} minutes, max {max_logs} logs)")

        # Lazy import - 필요할 때만 로드
        from aws_client import AWSLogFetcher
        from log_analyzer_vertex import LogAnalyzer
        from terraform_generator import TerraformGenerator

        # Step 1: Fetch CloudWatch Logs (OIDC Keyless)
        logger.info("Step 1: Fetching logs from AWS CloudWatch (OIDC Keyless)...")

        if not AWS_ROLE_ARN:
            raise HTTPException(
                status_code=500,
                detail="AWS_ROLE_ARN not configured for OIDC Keyless authentication"
            )

        aws_client = AWSLogFetcher(
            role_arn=AWS_ROLE_ARN,
            region=AWS_REGION
        )

        logs = aws_client.get_error_logs(
            log_group_name=LOG_GROUP_NAME,
            minutes=time_range,
            max_logs=max_logs
        )

        logger.info(f"Fetched {len(logs)} logs")

        if not logs:
            return {
                "status": "no_errors",
                "message": "No error logs found in the specified time range",
                "time_range_minutes": time_range
            }

        # Step 2: Analyze with Vertex AI Gemini
        logger.info("Step 2: Analyzing logs with Vertex AI Gemini...")

        if not GCP_PROJECT_ID:
            raise HTTPException(
                status_code=500,
                detail="GCP_PROJECT_ID not configured"
            )

        analyzer = LogAnalyzer(
            project_id=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        analysis = analyzer.analyze_logs(logs)

        logger.info(f"Analysis completed - Severity: {analysis['severity']}")
        logger.info(f"   Detected issues: {analysis['detected_issues']}")

        # Step 3: Generate Terraform fix (if requested and issues found)
        terraform_result = None
        if generate_terraform and analysis["detected_issues"]:
            logger.info("Step 3: Generating Terraform fix with Claude...")

            # if not CLAUDE_API_KEY:
            #     logger.warning("CLAUDE_API_KEY not set - skipping Terraform generation")
            # else:
            generator = TerraformGenerator(region_name=AWS_REGION)

            patient_info = {
                "region": AWS_REGION,
                "vpc_cidr": "10.0.0.0/16",
                "ecs_cluster": "patient-zone-cluster",
                "rds_instance": "patient-zone-mysql",
                "alb_name": "patient-zone-alb"
            }

            terraform_result = generator.generate_fix(analysis, patient_info)
            logger.info("Terraform code generated")

        # Step 4: Send to Slack (if requested)
        slack_sent = False
        if send_to_slack and SLACK_WEBHOOK_URL:
            logger.info("Step 4: Sending notification to Slack...")

            notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
            slack_sent = notifier.send_alert(
                analysis=analysis,
                terraform_result=terraform_result,
                include_code=False  # Slack has 3000 char limit per block
            )

            if slack_sent:
                logger.info("Slack notification sent")
            else:
                logger.warning("Failed to send Slack notification")

        # Return result
        result = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_logs_analyzed": len(logs),
                "time_range_minutes": time_range,
                "log_group": LOG_GROUP_NAME,
                "ai_engine": "Vertex AI Gemini 2.0 Flash"
            },
            "analysis": analysis,
            "slack_sent": slack_sent
        }

        if terraform_result:
            result["terraform"] = terraform_result

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": type(e).__name__
            }
        )


@app.post("/slack/test")
async def test_slack():
    """Test Slack integration"""
    if not SLACK_WEBHOOK_URL:
        raise HTTPException(
            status_code=400,
            detail="SLACK_WEBHOOK_URL not configured"
        )

    notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
    success = notifier.send_test_message()

    if success:
        return {"status": "success", "message": "Test message sent to Slack"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send test message to Slack"
        )


@app.post("/slack/command")
async def slack_command(request: Request, background_tasks: BackgroundTasks):
    """
    Slack Slash Command handler

    /analyze-logs 30 → 최근 30분 로그 분석 (Gemini only)
    /terraform 30 → 최근 30분 로그 분석 + Terraform 코드 생성 (Gemini + Claude)
    """
    try:
        # Detect Slack retry - ignore duplicate requests
        retry_num = request.headers.get("X-Slack-Retry-Num")
        retry_reason = request.headers.get("X-Slack-Retry-Reason")

        if retry_num:
            logger.warning(f"Slack retry #{retry_num} detected (reason: {retry_reason}), ignoring duplicate request")
            return {
                "response_type": "ephemeral",
                "text": "요청이 이미 진행 중입니다. 잠시만 기다려주세요."
            }

        # Parse Slack form data
        form_data = await request.form()

        command = form_data.get("command", "")
        text = form_data.get("text", "")
        user_name = form_data.get("user_name", "Unknown")

        request_id = f"{user_name}_{datetime.utcnow().strftime('%H%M%S')}"
        logger.info(f"[REQ-{request_id}] Slack command: {command} from {user_name}")

        # Parse time range (default: 30 minutes)
        time_range = 30
        if text and text.isdigit():
            time_range = int(text)
            time_range = min(max(time_range, 5), 120)  # 5-120분 사이

        # Command routing
        if command == "/terraform":
            # Terraform 생성 명령어
            logger.info(f"[REQ-{request_id}] Starting Terraform generation task")
            background_tasks.add_task(
                generate_terraform_and_send_to_slack,
                time_range_minutes=time_range,
                triggered_by=user_name,
                request_id=request_id
            )

            logger.info(f"[REQ-{request_id}] Immediate response sent to Slack")
            return {
                "response_type": "ephemeral",
                "text": f"✅ Terraform 코드 생성 요청이 접수되었습니다. (최근 {time_range}분)\n\n생성 완료 시 자동으로 결과를 전송합니다."
            }
        else:
            # 기본 로그 분석 명령어 (/analyze-logs)
            logger.info(f"[REQ-{request_id}] Starting log analysis task")
            background_tasks.add_task(
                analyze_and_send_to_slack,
                time_range_minutes=time_range,
                triggered_by=user_name,
                request_id=request_id
            )

            logger.info(f"[REQ-{request_id}] Immediate response sent to Slack")
            return {
                "response_type": "ephemeral",
                "text": f"✅ 로그 분석 요청이 접수되었습니다. (최근 {time_range}분)\n\n분석 완료 시 자동으로 결과를 전송합니다."
            }

    except Exception as e:
        logger.error(f"Slack command error: {str(e)}", exc_info=True)
        return {
            "response_type": "ephemeral",
            "text": f"⚠️ 요청 처리 중 오류가 발생했습니다.\n\n관리자에게 문의해주세요."
        }


async def analyze_and_send_to_slack(time_range_minutes: int, triggered_by: str, request_id: str):
    """Background task: 로그 분석 후 Slack 전송"""
    start_time = datetime.utcnow()
    try:
        logger.info(f"[REQ-{request_id}] Background analysis started (by {triggered_by}) at {start_time.strftime('%H:%M:%S')}")

        # Lazy import - 백그라운드 태스크에서만 로드
        import_start = datetime.utcnow()
        from aws_client import AWSLogFetcher
        from log_analyzer_vertex import LogAnalyzer
        from terraform_generator import TerraformGenerator
        import_duration = (datetime.utcnow() - import_start).total_seconds()
        logger.info(f"[REQ-{request_id}] Module imports took {import_duration:.2f}s")

        # Step 1: CloudWatch Logs 조회 (OIDC Keyless)
        step1_start = datetime.utcnow()
        logger.info(f"[REQ-{request_id}] Step 1: Fetching CloudWatch logs (OIDC Keyless)...")
        aws_client = AWSLogFetcher(
            role_arn=AWS_ROLE_ARN,
            region=AWS_REGION
        )

        logs = aws_client.get_error_logs(
            log_group_name=LOG_GROUP_NAME,
            minutes=time_range_minutes,
            max_logs=100
        )
        step1_duration = (datetime.utcnow() - step1_start).total_seconds()
        logger.info(f"[REQ-{request_id}] Fetched {len(logs)} logs in {step1_duration:.2f}s")

        # 로그 없으면 정상 메시지 전송
        if not logs:
            if SLACK_WEBHOOK_URL:
                slack_start = datetime.utcnow()
                logger.info(f"[REQ-{request_id}] No errors found, sending normal status to Slack...")
                notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
                notifier.send_simple_message(
                    f"✅ 로그 분석 완료 (요청: @{triggered_by})",
                    f"최근 {time_range_minutes}분간 오류 로그가 없습니다. 시스템 정상!"
                )
                slack_duration = (datetime.utcnow() - slack_start).total_seconds()
                total_duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"[REQ-{request_id}] Normal status sent to Slack in {slack_duration:.2f}s (total: {total_duration:.2f}s)")
            return

        # Step 2: Gemini 분석
        step2_start = datetime.utcnow()
        logger.info(f"[REQ-{request_id}] Step 2: Analyzing logs with Vertex AI Gemini...")
        analyzer = LogAnalyzer(
            project_id=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        analysis = analyzer.analyze_logs(logs)
        step2_duration = (datetime.utcnow() - step2_start).total_seconds()
        logger.info(f"[REQ-{request_id}] Analysis completed in {step2_duration:.2f}s - Severity: {analysis.get('severity', 'unknown')}")

        # Step 3: Slack 전송 (Terraform 없이 분석 결과만)
        if SLACK_WEBHOOK_URL:
            step3_start = datetime.utcnow()
            logger.info(f"[REQ-{request_id}] Step 3: Sending analysis result to Slack...")
            notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
            slack_sent = notifier.send_alert(
                analysis=analysis,
                terraform_result=None,  # Terraform 생성 안함
                include_code=False
            )
            step3_duration = (datetime.utcnow() - step3_start).total_seconds()

            if slack_sent:
                logger.info(f"[REQ-{request_id}] Slack notification sent in {step3_duration:.2f}s")
            else:
                logger.warning(f"[REQ-{request_id}] Failed to send Slack notification")

        total_duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"[REQ-{request_id}] Log analysis complete (by {triggered_by}) - Total time: {total_duration:.2f}s")

    except Exception as e:
        total_duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"[REQ-{request_id}] Analysis failed after {total_duration:.2f}s: {str(e)}", exc_info=True)

        # 오류 메시지 Slack 전송
        if SLACK_WEBHOOK_URL:
            try:
                logger.info(f"[REQ-{request_id}] Sending error notification to Slack...")
                notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
                notifier.send_simple_message(
                    f"❌ 분석 실패 (요청: @{triggered_by})",
                    f"오류: {str(e)}"
                )
                logger.info(f"[REQ-{request_id}] Error notification sent to Slack")
            except Exception as slack_error:
                logger.error(f"[REQ-{request_id}] Failed to send error to Slack: {str(slack_error)}")


async def generate_terraform_and_send_to_slack(time_range_minutes: int, triggered_by: str, request_id: str):
    """Background task: 로그 분석 + Terraform 코드 생성 후 Slack 전송"""
    start_time = datetime.utcnow()
    try:
        logger.info(f"[REQ-{request_id}] Background Terraform generation started (by {triggered_by}) at {start_time.strftime('%H:%M:%S')}")

        # Lazy import - 백그라운드 태스크에서만 로드
        import_start = datetime.utcnow()
        from aws_client import AWSLogFetcher
        from log_analyzer_vertex import LogAnalyzer
        from terraform_generator import TerraformGenerator
        import_duration = (datetime.utcnow() - import_start).total_seconds()
        logger.info(f"[REQ-{request_id}] Module imports took {import_duration:.2f}s")

        # Step 1: CloudWatch Logs 조회 (OIDC Keyless)
        step1_start = datetime.utcnow()
        logger.info(f"[REQ-{request_id}] Step 1: Fetching CloudWatch logs (OIDC Keyless)...")
        aws_client = AWSLogFetcher(
            role_arn=AWS_ROLE_ARN,
            region=AWS_REGION
        )

        logs = aws_client.get_error_logs(
            log_group_name=LOG_GROUP_NAME,
            minutes=time_range_minutes,
            max_logs=100
        )
        step1_duration = (datetime.utcnow() - step1_start).total_seconds()
        logger.info(f"[REQ-{request_id}] Fetched {len(logs)} logs in {step1_duration:.2f}s")

        # 로그 없으면 정상 메시지 전송
        if not logs:
            if SLACK_WEBHOOK_URL:
                slack_start = datetime.utcnow()
                logger.info(f"[REQ-{request_id}] No errors found, sending normal status to Slack...")
                notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
                notifier.send_simple_message(
                    f"✅ Terraform 생성 요청 (요청: @{triggered_by})",
                    f"최근 {time_range_minutes}분간 오류 로그가 없습니다.\n\nTerraform 코드를 생성할 문제가 없습니다."
                )
                slack_duration = (datetime.utcnow() - slack_start).total_seconds()
                total_duration = (datetime.utcnow() - start_time).total_seconds()
                logger.info(f"[REQ-{request_id}] Normal status sent to Slack in {slack_duration:.2f}s (total: {total_duration:.2f}s)")
            return

        # Step 2: Gemini 분석
        step2_start = datetime.utcnow()
        logger.info(f"[REQ-{request_id}] Step 2: Analyzing logs with Vertex AI Gemini...")
        analyzer = LogAnalyzer(
            project_id=GCP_PROJECT_ID,
            location=GCP_LOCATION
        )
        analysis = analyzer.analyze_logs(logs)
        step2_duration = (datetime.utcnow() - step2_start).total_seconds()
        logger.info(f"[REQ-{request_id}] Analysis completed in {step2_duration:.2f}s - Severity: {analysis.get('severity', 'unknown')}")

        # Step 3: Terraform 생성 (문제가 있을 때만)
        terraform_result = None
        if analysis["detected_issues"]:
            step3_start = datetime.utcnow()
            logger.info(f"[REQ-{request_id}] Step 3: Generating Terraform fix with Claude...")

            # if not CLAUDE_API_KEY:
            #     logger.warning(f"[REQ-{request_id}] CLAUDE_API_KEY not set - skipping Terraform generation")
            #     if SLACK_WEBHOOK_URL:
            #         notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
            #         notifier.send_simple_message(
            #             f"⚠️ Terraform 생성 실패 (요청: @{triggered_by})",
            #             f"Claude API 키가 설정되지 않았습니다.\n\n관리자에게 문의해주세요."
            #         )
            #     return

            generator = TerraformGenerator(region_name=AWS_REGION)

            patient_info = {
                "region": AWS_REGION,
                "ecs_cluster": "patient-zone-cluster",
                "rds_instance": "patient-zone-mysql",
                "alb_name": "patient-zone-alb"
            }

            terraform_result = generator.generate_fix(analysis, patient_info)
            step3_duration = (datetime.utcnow() - step3_start).total_seconds()
            logger.info(f"[REQ-{request_id}] Terraform code generated in {step3_duration:.2f}s")
        else:
            logger.info(f"[REQ-{request_id}] No critical issues detected - skipping Terraform generation")

        # Step 4: Slack 전송 (분석 결과 + Terraform 코드)
        if SLACK_WEBHOOK_URL:
            step4_start = datetime.utcnow()
            logger.info(f"[REQ-{request_id}] Step 4: Sending alert with Terraform to Slack...")
            notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
            slack_sent = notifier.send_alert(
                analysis=analysis,
                terraform_result=terraform_result,
                include_code=False
            )
            step4_duration = (datetime.utcnow() - step4_start).total_seconds()

            if slack_sent:
                logger.info(f"[REQ-{request_id}] Slack notification sent in {step4_duration:.2f}s")
            else:
                logger.warning(f"[REQ-{request_id}] Failed to send Slack notification")

        total_duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"[REQ-{request_id}] Terraform generation complete (by {triggered_by}) - Total time: {total_duration:.2f}s")

    except Exception as e:
        total_duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"[REQ-{request_id}] Terraform generation failed after {total_duration:.2f}s: {str(e)}", exc_info=True)

        # 오류 메시지 Slack 전송
        if SLACK_WEBHOOK_URL:
            try:
                logger.info(f"[REQ-{request_id}] Sending error notification to Slack...")
                notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
                notifier.send_simple_message(
                    f"❌ Terraform 생성 실패 (요청: @{triggered_by})",
                    f"오류: {str(e)}"
                )
                logger.info(f"[REQ-{request_id}] Error notification sent to Slack")
            except Exception as slack_error:
                logger.error(f"[REQ-{request_id}] Failed to send error to Slack: {str(slack_error)}")


# Cloud Run execution
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main_vertex:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
