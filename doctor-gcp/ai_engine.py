"""
AI Engine - Gemini 2.5를 활용한 로그 분석
GCP Vertex AI를 통해 AWS 로그를 지능적으로 분석합니다.
메가존클라우드 채용 포인트: AI 기반 자동화 및 인사이트 도출
"""

import logging
from typing import List, Dict, Any
import json

from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, Content, Part
import vertexai

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """
    Gemini 2.5 Flash를 사용한 로그 분석 엔진

    특징:
    - 다수의 에러 로그를 한 번에 분석
    - 근본 원인 식별 및 해결책 제시
    - 우선순위 판단 (Critical, High, Medium, Low)
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-2.0-flash-exp"  # 또는 gemini-1.5-flash
    ):
        """
        Args:
            project_id: GCP 프로젝트 ID
            location: Vertex AI 리전
            model_name: 사용할 Gemini 모델명
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Vertex AI 초기화
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(model_name)

        logger.info(f"🤖 Gemini AI Engine initialized: {model_name}")

    def _create_analysis_prompt(self, logs: List[Dict[str, Any]]) -> str:
        """
        로그 분석을 위한 프롬프트 생성

        메가존클라우드 채용 포인트:
        - Prompt Engineering을 통한 정확한 분석 유도
        - 구조화된 출력 (JSON) 요청
        """
        # 로그를 텍스트로 변환
        log_text = "\n".join([
            f"[{log['timestamp']}] {log['message']}"
            for log in logs
        ])

        prompt = f"""
당신은 클라우드 인프라 전문가입니다. 아래 AWS CloudWatch 로그를 분석하여 문제를 진단해 주세요.

## 로그 데이터
```
{log_text}
```

## 분석 요구사항
다음 형식의 JSON으로 분석 결과를 제공해 주세요:

{{
  "summary": "전체 로그에 대한 한 줄 요약 (한글, 50자 이내)",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW 중 하나",
  "issues": [
    {{
      "type": "에러 유형 (예: Database Connection Failure)",
      "count": 로그에서 발견된 횟수,
      "description": "문제 설명 (한글, 100자 이내)",
      "root_cause": "근본 원인 추정 (한글)",
      "solution": "해결 방법 제안 (한글, 구체적으로)"
    }}
  ],
  "priority_actions": [
    "우선적으로 해야 할 조치 1",
    "우선적으로 해야 할 조치 2",
    "우선적으로 해야 할 조치 3"
  ],
  "technical_keywords": ["관련된", "기술", "키워드", "리스트"]
}}

## 중요 사항
- 반드시 유효한 JSON만 반환하세요 (추가 설명 없이)
- 에러가 여러 종류라면 issues 배열에 모두 포함하세요
- 우선순위는 영향도와 긴급성을 고려하세요
- 한글로 명확하고 실용적인 조언을 제공하세요
"""
        return prompt

    async def analyze_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        로그를 Gemini AI로 분석합니다.

        Args:
            logs: 로그 이벤트 리스트

        Returns:
            분석 결과 딕셔너리
        """
        try:
            if not logs:
                return {
                    "summary": "분석할 로그가 없습니다",
                    "severity": "LOW",
                    "issues": [],
                    "priority_actions": []
                }

            logger.info(f"🤖 Analyzing {len(logs)} logs with Gemini AI...")

            # 프롬프트 생성
            prompt = self._create_analysis_prompt(logs)

            # Gemini API 호출
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,  # 일관성 있는 분석을 위해 낮은 temperature
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )

            # 응답 텍스트 추출
            response_text = response.text.strip()

            logger.info(f"📝 Raw Gemini Response:\n{response_text[:500]}...")

            # JSON 파싱 시도
            try:
                # JSON 코드 블록 제거 (Gemini가 ```json ... ``` 형태로 반환할 수 있음)
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif response_text.startswith("```"):
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                analysis_result = json.loads(response_text)
                logger.info("✅ Successfully parsed AI analysis result")

                return analysis_result

            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse JSON response: {str(e)}")
                logger.error(f"   Raw response: {response_text}")

                # Fallback: 기본 구조 반환
                return {
                    "summary": "AI 분석 결과 파싱 실패",
                    "severity": "UNKNOWN",
                    "issues": [{
                        "type": "Analysis Error",
                        "count": 0,
                        "description": "AI 응답을 JSON으로 변환하지 못했습니다",
                        "root_cause": "응답 형식 불일치",
                        "solution": "프롬프트를 수정하거나 모델을 재시도하세요"
                    }],
                    "priority_actions": ["AI 분석 재시도"],
                    "raw_response": response_text[:500]
                }

        except Exception as e:
            logger.error(f"❌ AI analysis failed: {str(e)}", exc_info=True)

            return {
                "summary": "AI 분석 중 오류 발생",
                "severity": "UNKNOWN",
                "issues": [{
                    "type": "System Error",
                    "count": 0,
                    "description": str(e),
                    "root_cause": "AI 엔진 오류",
                    "solution": "시스템 로그를 확인하고 관리자에게 문의하세요"
                }],
                "priority_actions": ["시스템 점검 필요"]
            }

    async def analyze_single_log(self, log_message: str) -> str:
        """
        단일 로그 메시지에 대한 간단한 분석 (빠른 진단용)

        Args:
            log_message: 로그 메시지 텍스트

        Returns:
            한 문장 요약
        """
        try:
            prompt = f"""
다음 에러 로그를 보고, 원인과 해결책을 **한 문장**으로 요약해 주세요.

로그: {log_message}

형식: "[원인] ... 때문에 발생. [해결] ... 하세요."
"""

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 200
                }
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Single log analysis failed: {str(e)}")
            return f"분석 실패: {str(e)}"

    def format_for_slack(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        분석 결과를 Slack Block Kit 형식으로 변환

        Args:
            analysis: analyze_logs() 결과

        Returns:
            Slack message payload
        """
        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "UNKNOWN": "⚪"
        }

        emoji = severity_emoji.get(analysis.get("severity", "UNKNOWN"), "⚪")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Cloud Doctor 진단 결과"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*심각도:*\n{analysis.get('severity', 'UNKNOWN')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*요약:*\n{analysis.get('summary', 'N/A')}"
                    }
                ]
            },
            {"type": "divider"}
        ]

        # 발견된 이슈들
        for i, issue in enumerate(analysis.get("issues", []), 1):
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Issue #{i}: {issue.get('type')}*\n"
                            f"• 발생 횟수: {issue.get('count')}회\n"
                            f"• 원인: {issue.get('root_cause', 'N/A')}\n"
                            f"• 해결책: {issue.get('solution', 'N/A')}"
                }
            })

        # 우선 조치 사항
        if analysis.get("priority_actions"):
            actions_text = "\n".join([
                f"{i}. {action}"
                for i, action in enumerate(analysis["priority_actions"], 1)
            ])

            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🎯 우선 조치 사항:*\n{actions_text}"
                }
            })

        return {
            "blocks": blocks
        }


# 사용 예시 (테스트용)
if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        analyzer = GeminiAnalyzer(
            project_id=os.getenv("GCP_PROJECT_ID", "your-project-id"),
            location="us-central1"
        )

        # 샘플 로그
        sample_logs = [
            {
                "timestamp": "2024-01-10T10:30:15",
                "message": "[ERROR] Connection refused: Could not connect to database at 10.0.2.55"
            },
            {
                "timestamp": "2024-01-10T10:30:45",
                "message": "[ERROR] SQLSTATE[HY000] [2002] Connection timed out after 30s"
            },
            {
                "timestamp": "2024-01-10T10:31:20",
                "message": "[MEMORY ERROR] OutOfMemoryError: Java heap space exceeded"
            }
        ]

        print("Analyzing sample logs...")
        result = await analyzer.analyze_logs(sample_logs)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n" + "="*60)
        print("Slack format:")
        slack_msg = analyzer.format_for_slack(result)
        print(json.dumps(slack_msg, indent=2, ensure_ascii=False))

    asyncio.run(test())
