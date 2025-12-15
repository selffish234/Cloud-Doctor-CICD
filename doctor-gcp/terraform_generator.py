"""
Doctor Zone - Terraform Generator
Uses Claude 3.5 Sonnet to generate infrastructure fixes as Terraform code
"""

import anthropic
from typing import Dict, List


class TerraformGenerator:
    """Generates Terraform code to fix detected infrastructure issues"""

    def __init__(self, api_key: str):
        """Initialize Claude AI client"""
        self.client = anthropic.Anthropic(api_key=api_key)

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
        if not analysis["detected_issues"]:
            return {
                "terraform_code": "",
                "explanation": "No issues detected - no infrastructure changes needed.",
                "apply_instructions": []
            }

        prompt = self._build_generation_prompt(analysis, patient_zone_info)

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text
            result = self._parse_claude_response(response_text)
            return result

        except Exception as e:
            return {
                "terraform_code": f"# Error generating Terraform code: {str(e)}",
                "explanation": f"Failed to generate fix: {str(e)}",
                "apply_instructions": ["Check Claude API configuration", "Verify API key"]
            }

    def _build_generation_prompt(self, analysis: Dict, patient_info: Dict) -> str:
        """Build Terraform generation prompt for Claude"""

        issues = ", ".join(analysis["detected_issues"])
        recommendations = "\n".join(f"- {rec}" for rec in analysis["recommendations"])

        prompt = f"""You are a Cloud Infrastructure Engineer specializing in AWS and Terraform.

**Current Situation:**
A monitoring system detected the following issues in a production AWS environment:

Issues: {issues}
Severity: {analysis["severity"]}
Summary: {analysis["summary"]}

Recommendations from log analysis:
{recommendations}

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

**Common Fix Patterns:**

For "db-failure":
- Check RDS security group rules
- Verify subnet group configuration
- Add RDS connection endpoint validation

For "pool-exhaustion":
- Increase RDS max_connections parameter
- Adjust ECS task count or resources
- Add connection pool monitoring

For "memory-leak":
- Increase ECS task memory limits
- Add memory-based auto-scaling
- Configure OOM kill handling

For "slow-query":
- Enable RDS Performance Insights
- Adjust slow_query_log parameters
- Add RDS read replicas if needed

For "api-timeout":
- Increase ALB target group deregistration delay
- Adjust ECS health check settings
- Add timeout configuration to task definition

For "jwt-expiry":
- Add environment variable for token expiration
- Update task definition with correct JWT_EXPIRATION value

For "high-cpu":
- Increase ECS task CPU units
- Add CPU-based auto-scaling policy
- Enable ECS Container Insights

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

**IMPORTANT:** Write the "Explanation" section in Korean (한국어). The Terraform code comments can be in English, but the explanation must be in Korean for Korean-speaking MSP engineers.

**Important:**
- Use Terraform 1.0+ syntax
- Include proper resource dependencies
- Add tags for resource tracking
- Consider blast radius (minimize impact)
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

    message = "🔧 *Terraform Fix Generated*\n\n"
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
