"""
Cloud Doctor Auto-Trigger Lambda Function
CloudWatch Alarm -> SNS -> Lambda -> GCP Cloud Run

이 Lambda는 CloudWatch 알람이 트리거되면 GCP Cloud Run의 Doctor Zone을 호출합니다.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 환경변수
DOCTOR_ZONE_URL = os.environ.get('DOCTOR_ZONE_URL', '')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', '')


def lambda_handler(event, context):
    """
    SNS 메시지를 받아 Cloud Run Doctor Zone을 호출합니다.

    Event 구조 (SNS -> Lambda):
    {
        "Records": [
            {
                "Sns": {
                    "Message": "{\"AlarmName\": \"...\", \"NewStateValue\": \"ALARM\", ...}"
                }
            }
        ]
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # SNS 메시지 파싱
        sns_message = event['Records'][0]['Sns']['Message']
        alarm_data = json.loads(sns_message)

        alarm_name = alarm_data.get('AlarmName', 'Unknown')
        alarm_state = alarm_data.get('NewStateValue', 'Unknown')
        alarm_reason = alarm_data.get('NewStateReason', 'No reason provided')
        alarm_time = alarm_data.get('StateChangeTime', datetime.utcnow().isoformat())

        logger.info(f"Alarm: {alarm_name}, State: {alarm_state}, Reason: {alarm_reason}")

        # ALARM 상태일 때만 Doctor Zone 호출
        if alarm_state != 'ALARM':
            logger.info(f"Alarm state is {alarm_state}, skipping Doctor Zone trigger")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': f'Skipped - alarm state is {alarm_state}'})
            }

        # Doctor Zone URL 확인
        if not DOCTOR_ZONE_URL:
            logger.error("DOCTOR_ZONE_URL environment variable not set")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'DOCTOR_ZONE_URL not configured'})
            }

        # Doctor Zone 호출
        result = call_doctor_zone(alarm_name, alarm_reason, alarm_time)

        # Slack 직접 알림 (Doctor Zone 실패 시 백업)
        if not result['success'] and SLACK_WEBHOOK_URL:
            send_slack_fallback(alarm_name, alarm_reason, alarm_time, result['error'])

        return {
            'statusCode': 200 if result['success'] else 500,
            'body': json.dumps(result)
        }

    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}", exc_info=True)

        # 에러 발생 시 Slack 직접 알림
        if SLACK_WEBHOOK_URL:
            send_slack_fallback("Lambda Error", str(e), datetime.utcnow().isoformat(), str(e))

        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def call_doctor_zone(alarm_name: str, alarm_reason: str, alarm_time: str) -> dict:
    """
    GCP Cloud Run Doctor Zone의 /analyze 엔드포인트를 호출합니다.
    """
    try:
        url = f"{DOCTOR_ZONE_URL.rstrip('/')}/analyze"

        payload = {
            "time_range_minutes": 30,
            "generate_terraform": False,
            "send_to_slack": True,
            "triggered_by": "cloudwatch_alarm",
            "alarm_info": {
                "name": alarm_name,
                "reason": alarm_reason,
                "time": alarm_time
            }
        }

        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'CloudDoctor-Lambda-Trigger/1.0'
            },
            method='POST'
        )

        logger.info(f"Calling Doctor Zone: {url}")

        with urllib.request.urlopen(req, timeout=60) as response:
            response_body = response.read().decode('utf-8')
            logger.info(f"Doctor Zone response: {response_body[:500]}")

            return {
                'success': True,
                'status_code': response.status,
                'response': json.loads(response_body) if response_body else {}
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else str(e)
        logger.error(f"Doctor Zone HTTP error: {e.code} - {error_body}")
        return {
            'success': False,
            'error': f"HTTP {e.code}: {error_body[:200]}"
        }

    except urllib.error.URLError as e:
        logger.error(f"Doctor Zone URL error: {str(e)}")
        return {
            'success': False,
            'error': f"URL Error: {str(e)}"
        }

    except Exception as e:
        logger.error(f"Doctor Zone call failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def send_slack_fallback(alarm_name: str, alarm_reason: str, alarm_time: str, error: str):
    """
    Doctor Zone 호출 실패 시 Slack으로 직접 알림을 보냅니다.
    """
    try:
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "CloudWatch Alarm Triggered",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Alarm:*\n{alarm_name}"},
                        {"type": "mrkdwn", "text": f"*Time:*\n{alarm_time}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Reason:*\n```{alarm_reason[:500]}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Doctor Zone Error:*\n```{error[:300]}```"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "This is a fallback notification. Doctor Zone could not be reached."
                        }
                    ]
                }
            ]
        }

        data = json.dumps(payload).encode('utf-8')

        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            logger.info(f"Slack fallback sent: {response.status}")

    except Exception as e:
        logger.error(f"Slack fallback failed: {str(e)}")
