#!/bin/bash

# Cloud Doctor MVP 전체 리소스 삭제 스크립트
# 주의: 이 스크립트는 생성된 모든 리소스를 삭제합니다.

set -e  # 에러 발생 시 중단

echo "============================================"
echo "Cloud Doctor MVP 리소스 정리 시작"
echo "============================================"
echo ""

# 환경 변수 로드
source ~/.bashrc 2>/dev/null || true

# 환경 변수 확인
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "AWS_ACCOUNT_ID 환경 변수가 설정되지 않았습니다."
    echo "AWS 계정 ID를 입력하세요:"
    read AWS_ACCOUNT_ID
fi

if [ -z "$GCP_PROJECT_ID" ]; then
    echo "GCP_PROJECT_ID 환경 변수가 설정되지 않았습니다."
    echo "GCP 프로젝트 ID를 입력하세요:"
    read GCP_PROJECT_ID
fi

echo "AWS 계정 ID: $AWS_ACCOUNT_ID"
echo "GCP 프로젝트 ID: $GCP_PROJECT_ID"
echo ""
echo "계속하시겠습니까? (y/N)"
read -r confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "삭제가 취소되었습니다."
    exit 0
fi

echo ""
echo "============================================"
echo "Phase 1: GCP 리소스 삭제"
echo "============================================"
echo ""

# GCP Service Account 이메일
GCP_SA_EMAIL="cloud-doctor-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

echo "1. Cloud Run 서비스 삭제 중..."
if gcloud run services describe cloud-doctor --region us-central1 &>/dev/null; then
    gcloud run services delete cloud-doctor \
        --region us-central1 \
        --quiet
    echo "   ✓ Cloud Run 서비스 삭제 완료"
else
    echo "   - Cloud Run 서비스가 존재하지 않습니다."
fi
echo ""

echo "2. GCR 이미지 삭제 중..."
if gcloud container images describe gcr.io/${GCP_PROJECT_ID}/cloud-doctor:latest &>/dev/null; then
    gcloud container images delete \
        gcr.io/${GCP_PROJECT_ID}/cloud-doctor:latest \
        --quiet
    echo "   ✓ GCR 이미지 삭제 완료"
else
    echo "   - GCR 이미지가 존재하지 않습니다."
fi
echo ""

echo "3. Service Account IAM 바인딩 제거 중..."
# aiplatform.user
gcloud projects remove-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${GCP_SA_EMAIL}" \
    --role="roles/aiplatform.user" \
    --quiet 2>/dev/null || echo "   - aiplatform.user 바인딩이 존재하지 않습니다."

# run.invoker
gcloud projects remove-iam-policy-binding ${GCP_PROJECT_ID} \
    --member="serviceAccount:${GCP_SA_EMAIL}" \
    --role="roles/run.invoker" \
    --quiet 2>/dev/null || echo "   - run.invoker 바인딩이 존재하지 않습니다."

# iam.serviceAccountTokenCreator
gcloud iam service-accounts remove-iam-policy-binding ${GCP_SA_EMAIL} \
    --member="serviceAccount:${GCP_SA_EMAIL}" \
    --role="roles/iam.serviceAccountTokenCreator" \
    --quiet 2>/dev/null || echo "   - iam.serviceAccountTokenCreator 바인딩이 존재하지 않습니다."

echo "   ✓ IAM 바인딩 제거 완료"
echo ""

echo "4. Service Account 삭제 중..."
if gcloud iam service-accounts describe ${GCP_SA_EMAIL} &>/dev/null; then
    gcloud iam service-accounts delete ${GCP_SA_EMAIL} \
        --quiet
    echo "   ✓ Service Account 삭제 완료"
else
    echo "   - Service Account가 존재하지 않습니다."
fi
echo ""

echo "============================================"
echo "Phase 2: AWS 리소스 삭제"
echo "============================================"
echo ""

echo "5. CloudWatch Log Group 삭제 중..."
if aws logs describe-log-groups --log-group-name-prefix /aws/ec2/chaos-app --region eu-west-1 --query 'logGroups[0]' --output text &>/dev/null; then
    aws logs delete-log-group \
        --log-group-name /aws/ec2/chaos-app \
        --region eu-west-1
    echo "   ✓ CloudWatch Log Group 삭제 완료"
else
    echo "   - CloudWatch Log Group이 존재하지 않습니다."
fi
echo ""

echo "6. ECR 리포지토리 삭제 중..."
if aws ecr describe-repositories --repository-names chaos-app --region eu-west-1 &>/dev/null; then
    aws ecr delete-repository \
        --repository-name chaos-app \
        --force \
        --region eu-west-1
    echo "   ✓ ECR 리포지토리 삭제 완료"
else
    echo "   - ECR 리포지토리가 존재하지 않습니다."
fi
echo ""

echo "7. AWS IAM Role (CloudDoctorRole) 정리 중..."
# 정책 분리
if aws iam get-role --role-name CloudDoctorRole &>/dev/null; then
    echo "   - CloudWatch 정책 분리 중..."
    aws iam detach-role-policy \
        --role-name CloudDoctorRole \
        --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsReadOnlyAccess \
        2>/dev/null || echo "     정책이 이미 분리되었습니다."

    echo "   - Role 삭제 중..."
    aws iam delete-role --role-name CloudDoctorRole
    echo "   ✓ CloudDoctorRole 삭제 완료"
else
    echo "   - CloudDoctorRole이 존재하지 않습니다."
fi
echo ""

echo "8. AWS IAM Role (CloudWatch-Agent-Role) 정리 중..."
if aws iam get-role --role-name CloudWatch-Agent-Role &>/dev/null; then
    # Instance Profile에서 Role 제거
    echo "   - Instance Profile에서 Role 제거 중..."
    aws iam remove-role-from-instance-profile \
        --instance-profile-name CloudWatch-Agent-Profile \
        --role-name CloudWatch-Agent-Role \
        2>/dev/null || echo "     이미 제거되었습니다."

    # Instance Profile 삭제
    echo "   - Instance Profile 삭제 중..."
    aws iam delete-instance-profile \
        --instance-profile-name CloudWatch-Agent-Profile \
        2>/dev/null || echo "     Instance Profile이 존재하지 않습니다."

    # 정책 분리
    echo "   - 정책 분리 중..."
    aws iam detach-role-policy \
        --role-name CloudWatch-Agent-Role \
        --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy \
        2>/dev/null || true

    aws iam detach-role-policy \
        --role-name CloudWatch-Agent-Role \
        --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly \
        2>/dev/null || true

    # Role 삭제
    echo "   - Role 삭제 중..."
    aws iam delete-role --role-name CloudWatch-Agent-Role
    echo "   ✓ CloudWatch-Agent-Role 삭제 완료"
else
    echo "   - CloudWatch-Agent-Role이 존재하지 않습니다."
fi
echo ""

echo "============================================"
echo "Phase 3: EC2 인스턴스 확인"
echo "============================================"
echo ""

echo "9. EC2 인스턴스 확인 중..."
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=cloud-doctor-patient" \
              "Name=instance-state-name,Values=running,stopped" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text \
    --region eu-west-1 2>/dev/null)

if [ "$INSTANCE_ID" != "None" ] && [ -n "$INSTANCE_ID" ]; then
    echo "   EC2 인스턴스 발견: $INSTANCE_ID"
    echo ""
    echo "   주의: EC2 인스턴스를 종료하시겠습니까? (y/N)"
    echo "   (EC2에서 실행 중인 Docker 컨테이너도 중지됩니다)"
    read -r ec2_confirm

    if [ "$ec2_confirm" = "y" ] || [ "$ec2_confirm" = "Y" ]; then
        echo "   - EC2 인스턴스 종료 중..."
        aws ec2 terminate-instances \
            --instance-ids $INSTANCE_ID \
            --region eu-west-1
        echo "   ✓ EC2 인스턴스 종료 시작 (완료까지 수 분 소요)"
        echo "   - 인스턴스 ID: $INSTANCE_ID"
    else
        echo "   - EC2 인스턴스는 수동으로 종료해주세요."
        echo "   - AWS Console: https://eu-west-1.console.aws.amazon.com/ec2/"
    fi
else
    echo "   - EC2 인스턴스가 존재하지 않습니다."
fi
echo ""

echo "10. 보안 그룹 확인 중..."
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=cloud-doctor-sg" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region eu-west-1 2>/dev/null)

if [ "$SG_ID" != "None" ] && [ -n "$SG_ID" ]; then
    echo "   보안 그룹 발견: $SG_ID"
    echo "   EC2 인스턴스 종료 후 수동으로 삭제하세요."
    echo "   명령어: aws ec2 delete-security-group --group-id $SG_ID --region eu-west-1"
else
    echo "   - 보안 그룹이 존재하지 않습니다."
fi
echo ""

echo "============================================"
echo "정리 완료"
echo "============================================"
echo ""
echo "삭제된 리소스:"
echo "  [GCP]"
echo "  ✓ Cloud Run 서비스: cloud-doctor"
echo "  ✓ GCR 이미지: gcr.io/${GCP_PROJECT_ID}/cloud-doctor:latest"
echo "  ✓ Service Account: ${GCP_SA_EMAIL}"
echo ""
echo "  [AWS]"
echo "  ✓ CloudWatch Log Group: /aws/ec2/chaos-app"
echo "  ✓ ECR 리포지토리: chaos-app"
echo "  ✓ IAM Role: CloudDoctorRole"
echo "  ✓ IAM Role: CloudWatch-Agent-Role"
if [ "$INSTANCE_ID" != "None" ] && [ -n "$INSTANCE_ID" ]; then
    if [ "$ec2_confirm" = "y" ] || [ "$ec2_confirm" = "Y" ]; then
        echo "  ✓ EC2 인스턴스: $INSTANCE_ID (종료 진행 중)"
    else
        echo "  - EC2 인스턴스: $INSTANCE_ID (수동 종료 필요)"
    fi
fi
echo ""
echo "추가 수동 작업 필요:"
echo "  1. AWS IAM 사용자 (cloud-doctor-admin) - AWS Console에서 삭제"
echo "  2. AWS 키 페어 (cloud-doctor-key.pem) - 로컬 파일 삭제: rm ~/cloud-doctor-key.pem"
if [ "$SG_ID" != "None" ] && [ -n "$SG_ID" ]; then
    echo "  3. 보안 그룹 ($SG_ID) - EC2 종료 후 삭제"
fi
echo ""
echo "환경 변수 정리 (선택사항):"
echo "  ~/.bashrc 파일에서 Cloud Doctor 관련 환경 변수 제거"
echo ""
echo "============================================"
