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

# Import Vertex AI version
from aws_client import AWSClientDirect
from log_analyzer_vertex import LogAnalyzer, format_analysis_for_slack
from terraform_generator import TerraformGenerator, format_terraform_for_slack
from slack_notifier import SlackNotifier

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
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
LOG_GROUP_NAME = os.getenv("LOG_GROUP_NAME", "/ecs/patient-zone")


def check_environment():
    """Check required environment variables"""
    required = {
        "GCP_PROJECT_ID": GCP_PROJECT_ID,
        "CLAUDE_API_KEY": CLAUDE_API_KEY,
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_KEY
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        logger.error(f"❌ Missing required environment variables: {missing}")
    else:
        logger.info("✅ All required environment variables configured")

    if not SLACK_WEBHOOK_URL:
        logger.warning("⚠️ SLACK_WEBHOOK_URL not set - notifications will be disabled")


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("🩺 Cloud Doctor Enhanced (Vertex AI) - Starting...")
    logger.info("   Patient Zone: AWS (CloudWatch Logs)")
    logger.info("   Doctor Zone:  GCP Cloud Run")
    logger.info("   AI Analysis:  Vertex AI Gemini 2.0 Flash ✨")
    logger.info("   IaC Generate: Claude Sonnet 4.5")
    logger.info("   💰 Uses GCP Credits!")
    logger.info("=" * 60)
    check_environment()
    logger.info("✅ Doctor Zone Ready")
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

        logger.info(f"🔍 Starting analysis (last {time_range} minutes, max {max_logs} logs)")

        # Step 1: Fetch CloudWatch Logs
        logger.info("📥 Step 1: Fetching logs from AWS CloudWatch...")

        if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
            raise HTTPException(
                status_code=500,
                detail="AWS credentials not configured"
            )

        aws_client = AWSClientDirect(
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region=AWS_REGION
        )

        logs = aws_client.get_error_logs(
            log_group_name=LOG_GROUP_NAME,
            minutes=time_range,
            max_logs=max_logs
        )

        logger.info(f"✅ Fetched {len(logs)} logs")

        if not logs:
            return {
                "status": "no_errors",
                "message": "No error logs found in the specified time range",
                "time_range_minutes": time_range
            }

        # Step 2: Analyze with Vertex AI Gemini
        logger.info("🤖 Step 2: Analyzing logs with Vertex AI Gemini...")

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

        logger.info(f"✅ Analysis completed - Severity: {analysis['severity']}")
        logger.info(f"   Detected issues: {analysis['detected_issues']}")

        # Step 3: Generate Terraform fix (if requested and issues found)
        terraform_result = None
        if generate_terraform and analysis["detected_issues"]:
            logger.info("🔧 Step 3: Generating Terraform fix with Claude...")

            if not CLAUDE_API_KEY:
                logger.warning("⚠️ CLAUDE_API_KEY not set - skipping Terraform generation")
            else:
                generator = TerraformGenerator(api_key=CLAUDE_API_KEY)

                patient_info = {
                    "region": AWS_REGION,
                    "vpc_cidr": "10.0.0.0/16",
                    "ecs_cluster": "patient-zone-cluster",
                    "rds_instance": "patient-zone-mysql",
                    "alb_name": "patient-zone-alb"
                }

                terraform_result = generator.generate_fix(analysis, patient_info)
                logger.info("✅ Terraform code generated")

        # Step 4: Send to Slack (if requested)
        slack_sent = False
        if send_to_slack and SLACK_WEBHOOK_URL:
            logger.info("📨 Step 4: Sending notification to Slack...")

            notifier = SlackNotifier(webhook_url=SLACK_WEBHOOK_URL)
            slack_sent = notifier.send_alert(
                analysis=analysis,
                terraform_result=terraform_result,
                include_code=True
            )

            if slack_sent:
                logger.info("✅ Slack notification sent")
            else:
                logger.warning("⚠️ Failed to send Slack notification")

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
        logger.error(f"❌ Analysis failed: {str(e)}", exc_info=True)
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


# Cloud Run execution
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main_vertex:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
