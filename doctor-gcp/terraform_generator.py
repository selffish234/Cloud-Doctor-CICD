"""
Doctor Zone - Terraform Generator
Uses AWS Bedrock (Claude 3.5 Sonnet) to generate infrastructure fixes as Terraform code
"""

import boto3
import json
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class TerraformGenerator:
    """Generates Terraform code to fix detected infrastructure issues using AWS Bedrock"""

    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize AWS Bedrock Runtime client
        Claude 3.5 Sonnet is available in us-east-1, us-west-2, etc. default to us-east-1
        """
        self.client = boto3.client("bedrock-runtime", region_name=region_name)
        # Claude 3.5 Sonnet Model ID in Bedrock
        self.model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    def generate_fix(self, analysis: Dict, patient_zone_info: Dict) -> Dict:
        """
        Generate Terraform code to fix detected issues

        Args:
            analysis: Analysis result from Gemini
            patient_zone_info: Current Patient Zone infrastructure info

        Returns:
            Dict containing:
            - terraform_code: Generated Terraform code
            - explanation: Human-readable explanation
            - apply_instructions: How to apply the fix
        """
        if not analysis.get("issues"):
            return {
                "terraform_code": "",
                "explanation": "No issues detected - no infrastructure changes needed.",
                "apply_instructions": []
            }

        prompt = self._build_generation_prompt(analysis, patient_zone_info)

        try:
            # Bedrock converse API structure
            response = self.client.converse(
                modelId=self.model_id,
                messages=[{
                    "role": "user",
                    "content": [{"text": prompt}]
                }],
                inferenceConfig={
                    "maxTokens": 4096,
                    "temperature": 0.5,
                    "topP": 0.9
                }
            )

            # Extract response text
            response_text = response['output']['message']['content'][0]['text']
            result = self._parse_claude_response(response_text)
            return result

        except Exception as e:
            logger.error(f"Bedrock generation error: {str(e)}", exc_info=True)
            return {
                "terraform_code": f"# Error generating Terraform code: {str(e)}",
                "explanation": f"Failed to generate fix: {str(e)}",
                "apply_instructions": ["Check Bedrock IAM permissions", "Verify AWS credentials"]
            }

    def _build_generation_prompt(self, analysis: Dict, patient_info: Dict) -> str:
        """Build Terraform generation prompt for Claude"""

        issues_list = analysis.get("issues", [])
        issues_desc = "\n".join([f"- {issue['type']}: {issue['description']}" for issue in issues_list])
        
        prompt = f"""You are a Cloud Infrastructure Engineer specializing in AWS and Terraform.

**Current Situation:**
A monitoring system detected the following issues in a production AWS environment:

Issues Detected:
{issues_desc}
Summary: {analysis.get("summary", "N/A")}
Severity: {analysis.get("severity", "UNKNOWN")}

**Current Infrastructure (Patient Zone):**
- Region: {patient_info.get("region", "ap-northeast-2")}
- VPC CIDR: {patient_info.get("vpc_cidr", "10.0.0.0/16")}
- ECS Cluster: {patient_info.get("ecs_cluster", "patient-zone-cluster")}
- RDS Instance: {patient_info.get("rds_instance", "patient-zone-mysql")}
- ALB: {patient_info.get("alb_name", "patient-zone-alb")}

**Your Task:**
Generate Terraform code to fix the detected issues. Follow these guidelines:

1. **Only fix the specific problems detected** - don't make unnecessary changes
2. **Use existing resource names** from patient_info
3. **Add comments explaining each fix**
4. **Include variable definitions if needed**
5. **Make changes production-safe** (no downtime if possible)

**Response Format:**

Please provide your response in this exact format:

## Terraform Code

```hcl
[Your Terraform code here - with English comments]
```

## Explanation

[Brief explanation in KOREAN (한국어) of what the code does and why it fixes the issue]

## Apply Instructions

1. [Step-by-step instructions to apply this fix - can be in English]
2. [Include backup/rollback steps if needed]
3. [Verification steps]

**IMPORTANT:** Write the "Explanation" section in Korean (한국어). The Terraform code comments can be in English, but the explanation must be in Korean.
"""
        return prompt

    def _parse_claude_response(self, response_text: str) -> Dict:
        """Parse Claude's response and extract Terraform code"""

        terraform_code = ""
        explanation = ""
        apply_instructions = []

        lines = response_text.split("\n")
        current_section = None
        code_block = False

        for line in lines:
            line_stripped = line.strip()

            # Detect sections
            if line_stripped.startswith("## Terraform Code"):
                current_section = "terraform"
                continue
            elif line_stripped.startswith("## Explanation"):
                current_section = "explanation"
                continue
            elif line_stripped.startswith("## Apply Instructions"):
                current_section = "instructions"
                continue

            # Handle code blocks
            if line_stripped.startswith("```"):
                code_block = not code_block
                continue

            # Extract content based on current section
            if current_section == "terraform":
                if code_block or line_stripped.startswith("#") or line_stripped.startswith("resource") or line_stripped.startswith("variable"):
                    terraform_code += line + "\n"

            elif current_section == "explanation":
                if line_stripped and not line_stripped.startswith("##"):
                    explanation += line_stripped + " "

            elif current_section == "instructions":
                if line_stripped.startswith(("1.", "2.", "3.", "4.", "5.", "-", "*")):
                    apply_instructions.append(line_stripped.lstrip("123456789.-* "))

        return {
            "terraform_code": terraform_code.strip(),
            "explanation": explanation.strip(),
            "apply_instructions": apply_instructions if apply_instructions else [
                "Review the generated Terraform code",
                "Run 'terraform plan' to verify changes",
                "Apply with 'terraform apply' after confirmation"
            ]
        }


def format_terraform_for_slack(terraform_result: Dict) -> str:
    """Format Terraform generation result for Slack notification"""

    message = "🔧 *Terraform Fix Generated (via AWS Bedrock)*\n\n"
    message += f"*Explanation:* {terraform_result['explanation']}\n\n"

    if terraform_result['terraform_code']:
        # Show first 500 chars of code
        code_preview = terraform_result['terraform_code'][:500]
        message += f"*Terraform Code Preview:*\n```\n{code_preview}...\n```\n\n"

    if terraform_result['apply_instructions']:
        message += "*Apply Instructions:*\n"
        for i, instruction in enumerate(terraform_result['apply_instructions'][:5], 1):
            message += f"{i}. {instruction}\n"

    return message
