# OIDC Keyless Authentication Setup Guide

GCP Cloud Run에서 AWS 리소스에 접근할 때 **Access Key 없이** OIDC 토큰으로 인증하는 방법입니다.

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    GCP Cloud Run                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  1. GCP 메타데이터 서버에서 OIDC ID 토큰 획득              │ │
│  │     GET http://metadata.google.internal/.../identity       │ │
│  │     → JWT 토큰 (sub: GCP Service Account Email)            │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 2. AssumeRoleWithWebIdentity
                              │    (OIDC 토큰 + Role ARN)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AWS STS                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  3. Trust Policy 검증                                      │ │
│  │     - Federated Principal: accounts.google.com             │ │
│  │     - Condition: sub == GCP Service Account Email          │ │
│  │                                                            │ │
│  │  4. 임시 자격증명 발급 (1시간 유효)                        │ │
│  │     → AccessKeyId, SecretAccessKey, SessionToken           │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 5. CloudWatch Logs API 호출
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS CloudWatch Logs                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  임시 자격증명으로 로그 조회                               │ │
│  │  (Access Key가 환경변수에 노출되지 않음!)                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 설정 단계

### Step 1: GCP Service Account 이메일 확인

Cloud Run 서비스의 Service Account 이메일을 확인합니다:

```bash
# 현재 Cloud Run 서비스의 Service Account 확인
gcloud run services describe doctor-zone \
  --region asia-northeast3 \
  --format 'value(spec.template.spec.serviceAccountName)'

# 또는 프로젝트의 기본 Compute Service Account 확인
gcloud iam service-accounts list --filter="displayName:Compute Engine default"
```

일반적인 형식:
- `PROJECT_NUMBER-compute@developer.gserviceaccount.com` (기본 Compute SA)
- `custom-sa@PROJECT_ID.iam.gserviceaccount.com` (커스텀 SA)

### Step 2: AWS IAM Role 생성

#### 2.1 AWS Console에서 생성

1. **AWS Console** → **IAM** → **Roles** → **Create role**

2. **Trusted entity type**: `Web identity`

3. **Identity provider**: `Google` (accounts.google.com)

4. **Audience**: GCP Service Account 이메일
   - 예: `123456789012-compute@developer.gserviceaccount.com`

5. **Role name**: `CloudDoctorRole`

#### 2.2 AWS CLI로 생성

```bash
# 변수 설정
GCP_SERVICE_ACCOUNT_EMAIL="123456789012-compute@developer.gserviceaccount.com"
ROLE_NAME="CloudDoctorRole"

# Trust Policy 생성
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "accounts.google.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "accounts.google.com:sub": "${GCP_SERVICE_ACCOUNT_EMAIL}"
        }
      }
    }
  ]
}
EOF

# Role 생성
aws iam create-role \
  --role-name ${ROLE_NAME} \
  --assume-role-policy-document file://trust-policy.json \
  --description "Role for GCP Cloud Run to access AWS CloudWatch Logs"

echo "Role ARN: arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/${ROLE_NAME}"
```

### Step 3: CloudWatch Logs 권한 추가

```bash
# CloudWatch Logs 읽기 권한 정책 생성
cat > cloudwatch-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:ap-northeast-2:*:log-group:/ecs/patient-zone:*",
        "arn:aws:logs:ap-northeast-2:*:log-group:/ecs/patient-zone"
      ]
    }
  ]
}
EOF

# 정책 생성 및 Role에 연결
aws iam put-role-policy \
  --role-name CloudDoctorRole \
  --policy-name CloudWatchLogsReadAccess \
  --policy-document file://cloudwatch-policy.json
```

### Step 4: 배포

```bash
# 환경변수 설정 (Access Key 없음!)
export AWS_ROLE_ARN="arn:aws:iam::123456789012:role/CloudDoctorRole"
export CLAUDE_API_KEY="your-claude-api-key"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# 배포
cd doctor-gcp
./deploy.sh
```

### Step 5: 테스트

```bash
# 서비스 URL 확인
SERVICE_URL=$(gcloud run services describe doctor-zone \
  --region asia-northeast3 \
  --format 'value(status.url)')

# 분석 요청 테스트
curl -X POST "${SERVICE_URL}/analyze" \
  -H "Content-Type: application/json" \
  -d '{"time_range_minutes": 30}'
```

## Troubleshooting

### Error: "Could not assume role"

**원인**: Trust Policy의 `accounts.google.com:sub` 값이 일치하지 않음

**해결**:
```bash
# GCP Service Account 이메일 재확인
gcloud run services describe doctor-zone \
  --region asia-northeast3 \
  --format 'value(spec.template.spec.serviceAccountName)'

# AWS Trust Policy 업데이트
aws iam update-assume-role-policy \
  --role-name CloudDoctorRole \
  --policy-document file://trust-policy.json
```

### Error: "Access Denied to CloudWatch Logs"

**원인**: Role에 CloudWatch Logs 권한이 없음

**해결**:
```bash
# 권한 확인
aws iam list-role-policies --role-name CloudDoctorRole

# 권한 추가 (Step 3 참조)
```

### Error: "Failed to get GCP token"

**원인**: 로컬 환경에서 실행 (GCP 메타데이터 서버 없음)

**해결**: Cloud Run에서만 OIDC Keyless 사용 가능. 로컬 테스트는 Access Key 사용.

## 보안 이점

| 항목 | Access Key 방식 | OIDC Keyless 방식 |
|------|----------------|-------------------|
| 키 노출 위험 | 환경변수에 노출 | 키 자체가 없음 |
| 키 교체 | 수동 교체 필요 | 자동 (1시간마다 갱신) |
| 유출 시 영향 | 영구 접근 가능 | 최대 1시간 유효 |
| 감사 추적 | 키 ID만 기록 | GCP SA + 세션 ID 기록 |
| gcloud describe로 조회 | 키 값 노출 | Role ARN만 노출 |

## 관련 파일

- `doctor-gcp/aws_client.py`: `AWSLogFetcher` 클래스 (OIDC 인증 구현)
- `doctor-gcp/main.py`: `AWS_ROLE_ARN` 환경변수 사용
- `doctor-gcp/deploy.sh`: Access Key 없이 배포
