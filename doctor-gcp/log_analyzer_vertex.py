"""
Doctor Zone - Log Analyzer (Vertex AI Version)
Uses Gemini 2.5 Flash via Vertex AI to analyze CloudWatch Logs
GCP 크레딧 사용 가능!
"""

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from typing import Dict, List
import json


class LogAnalyzer:
    """Analyzes AWS CloudWatch Logs using Gemini AI via Vertex AI"""

    FAILURE_SCENARIOS = [
        "db-failure",
        "pool-exhaustion",
        "memory-leak",
        "slow-query",
        "api-timeout",
        "jwt-expiry",
        "high-cpu"
    ]

    def __init__(self, project_id: str, location: str = "us-central1"):
        """
        Initialize Gemini AI client via Vertex AI

        Args:
            project_id: GCP Project ID
            location: Vertex AI location (default: us-central1)
        """
        # Vertex AI 초기화
        vertexai.init(project=project_id, location=location)

        # Gemini 2.0 Flash 모델 로드 (실험 버전, us-central1 지원)
        self.model = GenerativeModel("gemini-2.0-flash-exp")

        # Generation config
        self.generation_config = GenerationConfig(
            temperature=0.2,  # 일관된 분석을 위해 낮게 설정
            max_output_tokens=2048,
        )

    def analyze_logs(self, logs: List[Dict]) -> Dict:
        """
        Analyze CloudWatch Logs to detect failure scenarios

        Args:
            logs: List of log events from CloudWatch (each is a dict with 'timestamp', 'message', 'log_stream')

        Returns:
            Dict containing:
            - detected_issues: List of detected failure types
            - severity: "critical", "warning", or "info"
            - summary: Human-readable summary
            - recommendations: List of recommended actions
            - affected_resources: List of affected AWS resources
        """
        if not logs:
            return {
                "detected_issues": [],
                "severity": "info",
                "summary": "No logs to analyze",
                "recommendations": [],
                "affected_resources": []
            }

        # Prepare prompt for Gemini
        prompt = self._build_analysis_prompt(logs)

        try:
            # Vertex AI로 요청
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            result = self._parse_gemini_response(response.text)
            return result

        except Exception as e:
            return {
                "detected_issues": ["analysis-error"],
                "severity": "critical",
                "summary": f"Failed to analyze logs: {str(e)}",
                "recommendations": ["Check Vertex AI configuration", "Verify GCP project permissions"],
                "affected_resources": []
            }

    def _build_analysis_prompt(self, logs: List[Dict]) -> str:
        """Build analysis prompt for Gemini"""

        # Extract message from each log dict and format with timestamp
        log_lines = []
        for log in logs[:100]:  # Limit to 100 logs
            timestamp = log.get('timestamp', 'unknown')
            message = log.get('message', '')
            log_lines.append(f"[{timestamp}] {message}")

        log_sample = "\n".join(log_lines)

        prompt = f"""당신은 AWS CloudWatch 로그를 분석하는 클라우드 운영 AI입니다. 3-tier 웹 애플리케이션의 로그를 분석합니다.

**애플리케이션 아키텍처:**
- Frontend: CloudFront + S3의 Next.js
- Backend: ECS Fargate의 Node.js/Express
- Database: RDS MySQL 8.0

**알려진 장애 시나리오:**
1. db-failure: 데이터베이스 연결 오류 (잘못된 엔드포인트, 네트워크 문제)
2. pool-exhaustion: 커넥션 풀 고갈 (max_connections 초과)
3. memory-leak: 메모리 지속적 증가 (OOM 위험)
4. slow-query: N+1 쿼리 문제 또는 인덱스 누락
5. api-timeout: 외부 API 호출 타임아웃
6. jwt-expiry: JWT 토큰 만료 문제
7. high-cpu: CPU 집약적 연산으로 인한 성능 저하

**CloudWatch 로그:**
```
{log_sample}
```

**작업:**
로그를 분석하고 다음 JSON 구조로 반환하세요. summary와 recommendations는 한국어로 작성:

{{
  "detected_issues": ["scenario1", "scenario2"],  // 감지된 시나리오 이름 (영어 그대로)
  "severity": "critical|warning|info",            // 심각도 (영어 그대로)
  "summary": "문제 설명 (한국어로 1-2문장)",
  "recommendations": [                             // 권장사항 (한국어로 작성)
    "인덱스를 추가하여 쿼리 성능 개선",
    "ECS 메모리를 512MB에서 1024MB로 증가"
  ],
  "affected_resources": [                          // 영향받은 리소스 (영어 그대로)
    "ECS Task: arn:aws:ecs:...",
    "RDS Instance: patient-zone-mysql"
  ]
}}

**중요:**
- 유효한 JSON만 반환, 마크다운 코드 블록 없이
- detected_issues는 위 시나리오 이름 사용 (영어)
- severity는 critical/warning/info 중 하나 (영어)
- summary와 recommendations만 한국어로 작성
- affected_resources는 실제 AWS 리소스 이름 (영어)
- 문제가 없으면 빈 배열과 severity "info" 반환
"""
        return prompt

    def _parse_gemini_response(self, response_text: str) -> Dict:
        """Parse Gemini's response and extract structured data"""

        try:
            # Remove markdown code blocks if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            # Parse JSON
            result = json.loads(cleaned.strip())

            # Validate required fields
            required_fields = ["detected_issues", "severity", "summary", "recommendations", "affected_resources"]
            for field in required_fields:
                if field not in result:
                    result[field] = [] if field in ["detected_issues", "recommendations", "affected_resources"] else "unknown"

            return result

        except json.JSONDecodeError as e:
            # Fallback: extract information from raw text
            return {
                "detected_issues": self._extract_scenarios_from_text(response_text),
                "severity": "warning",
                "summary": response_text[:200],
                "recommendations": ["Review logs manually for detailed analysis"],
                "affected_resources": []
            }

    def _extract_scenarios_from_text(self, text: str) -> List[str]:
        """Extract scenario names from plain text response"""
        detected = []
        text_lower = text.lower()

        for scenario in self.FAILURE_SCENARIOS:
            if scenario.replace("-", " ") in text_lower or scenario in text_lower:
                detected.append(scenario)

        return detected


def format_analysis_for_slack(analysis: Dict) -> str:
    """Format analysis result for Slack notification"""

    severity_emoji = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️"
    }

    emoji = severity_emoji.get(analysis["severity"], "🔍")

    message = f"{emoji} *Cloud Doctor Alert - {analysis['severity'].upper()}*\n\n"
    message += f"*Summary:* {analysis['summary']}\n\n"

    if analysis["detected_issues"]:
        message += "*Detected Issues:*\n"
        for issue in analysis["detected_issues"]:
            message += f"  • `{issue}`\n"
        message += "\n"

    if analysis["recommendations"]:
        message += "*Recommendations:*\n"
        for i, rec in enumerate(analysis["recommendations"], 1):
            message += f"{i}. {rec}\n"
        message += "\n"

    if analysis["affected_resources"]:
        message += "*Affected Resources:*\n"
        for resource in analysis["affected_resources"]:
            message += f"  • {resource}\n"

    return message
