"""
Doctor Zone - Slack Notifier
Sends alerts and Terraform fixes to Slack via Webhook
"""

import requests
from typing import Dict, Optional
import json


class SlackNotifier:
    """Sends notifications to Slack via Webhook"""

    def __init__(self, webhook_url: str):
        """
        Initialize Slack Notifier

        Args:
            webhook_url: Slack Webhook URL (https://hooks.slack.com/services/...)
        """
        self.webhook_url = webhook_url

    def send_alert(
        self,
        analysis: Dict,
        terraform_result: Optional[Dict] = None,
        include_code: bool = False
    ) -> bool:
        """
        Send alert to Slack

        Args:
            analysis: Log analysis result from Gemini
            terraform_result: Optional Terraform generation result from Claude
            include_code: Whether to include full Terraform code

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            payload = self._build_slack_payload(analysis, terraform_result, include_code)
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Failed to send Slack notification: {str(e)}")
            return False

    def _build_slack_payload(
        self,
        analysis: Dict,
        terraform_result: Optional[Dict],
        include_code: bool
    ) -> Dict:
        """Build Slack message payload with blocks"""

        # Color based on severity
        color_map = {
            "critical": "#d32f2f",  # Red
            "warning": "#f57c00",   # Orange
            "info": "#388e3c"       # Green
        }
        color = color_map.get(analysis.get("severity", "info"), "#757575")

        # Emoji based on severity
        emoji_map = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        emoji = emoji_map.get(analysis.get("severity", "info"), "🔍")

        blocks = []

        # Header
        severity_map = {
            "critical": "긴급",
            "warning": "경고",
            "info": "정보"
        }
        severity_kr = severity_map.get(analysis.get('severity', 'unknown'), '알 수 없음')

        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Cloud Doctor 알림 - {severity_kr.upper()}"
            }
        })

        # Summary
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*요약*\n\n{analysis.get('summary', '요약 정보 없음')}"
            }
        })

        blocks.append({"type": "divider"})

        # Detected Issues
        if analysis.get("detected_issues"):
            issues_text = "\n\n".join([f"• `{issue}`" for issue in analysis["detected_issues"]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*감지된 문제*\n\n{issues_text}"
                }
            })

        # Affected Resources
        if analysis.get("affected_resources"):
            resources_text = "\n".join([f"• {resource}" for resource in analysis["affected_resources"]])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*영향받은 리소스*\n{resources_text}"
                }
            })

        # Recommendations (해결방법 포함)
        if analysis.get("recommendations"):
            recs_text = "\n\n".join([f"{i}. {rec}" for i, rec in enumerate(analysis["recommendations"], 1)])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*해결 방법*\n\n{recs_text}"
                }
            })

        # Terraform Fix (if provided)
        if terraform_result:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🔧 Terraform 수정 코드 생성됨"
                }
            })

            # Explanation
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*설명*\n{terraform_result.get('explanation', '설명 없음')}"
                }
            })

            # Terraform Code Preview (or full code)
            if terraform_result.get("terraform_code"):
                code = terraform_result["terraform_code"]
                if not include_code and len(code) > 500:
                    code = code[:500] + "\n...\n(축약됨 - 전체 코드는 API 응답 확인)"

                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Terraform 코드*\n```\n{code}\n```"
                    }
                })

            # Apply Instructions
            if terraform_result.get("apply_instructions"):
                instructions_text = "\n".join([
                    f"{i}. {instr}"
                    for i, instr in enumerate(terraform_result["apply_instructions"][:5], 1)
                ])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*적용 방법*\n{instructions_text}"
                    }
                })

        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [{
                "type": "mrkdwn",
                "text": "🩺 Cloud Doctor MVP | Powered by Gemini + Claude"
            }]
        })

        # Build final payload
        payload = {
            "attachments": [{
                "color": color,
                "blocks": blocks
            }]
        }

        return payload

    def send_test_message(self) -> bool:
        """Send a test message to verify Slack integration"""

        payload = {
            "text": "🩺 Cloud Doctor Test Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Slack Integration Test"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "If you're seeing this, Slack Webhook is working correctly!\n\n*Next Steps:*\n1. Doctor Zone is monitoring CloudWatch Logs\n2. Gemini AI will analyze logs for failures\n3. Claude AI will generate Terraform fixes\n4. Alerts will be sent here"
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
            print(f"Failed to send test message: {str(e)}")
            return False

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
