# Patient Zone - Terraform Infrastructure

**AWS 3-Tier Architecture IaC** - Cloud Doctor MVP의 환자 영역 인프라를 Terraform으로 관리합니다.

## 📋 개요

이 Terraform 구성은 다음 AWS 리소스를 자동으로 프로비저닝합니다:

### 아키텍처

```
Internet
    |
    ↓
[CloudFront] ← Frontend (Next.js)
    |
    ↓
[ALB] ← Public Subnets (2 AZs)
    |
    ↓
[ECS Fargate] ← Private App Subnets (2 AZs)
    |
    ↓
[RDS MySQL] ← Private DB Subnets (2 AZs)
```

### 리소스 목록

- **Network**: VPC, Subnets (Public/Private App/Private DB), NAT Gateway, Internet Gateway, Route Tables
- **Database**: RDS MySQL 8.0, Security Groups, Parameter Groups, Subnet Groups
- **Compute**: ECS Fargate Cluster, Task Definitions, Services, ECR Repositories
- **Load Balancing**: Application Load Balancer, Target Groups, Listeners
- **Frontend**: S3 Bucket, CloudFront Distribution, Origin Access Control
- **Monitoring**: CloudWatch Log Groups, Container Insights

## 🛠️ 사전 준비

### 1. 필수 도구 설치

```bash
# Terraform 설치 확인
terraform version  # >= 1.0

# AWS CLI 설치 확인
aws --version

# AWS 자격증명 설정
aws configure
# Access Key ID, Secret Access Key, Region 입력
```

### 2. 변수 파일 설정

```bash
cd terraform/patient-aws

# 예시 파일 복사
cp terraform.tfvars.example terraform.tfvars

# 변수 편집 (중요: 실제 값으로 변경!)
vi terraform.tfvars
```

**필수 변경 항목:**
- `db_password`: RDS 마스터 비밀번호 (최소 8자)
- `jwt_secret`: JWT 토큰 서명용 비밀키
- `frontend_bucket_name`: S3 버킷명 (전역 고유해야 함)

## 🚀 인프라 배포

### 1. Terraform 초기화

```bash
terraform init
```

### 2. 계획 확인

```bash
terraform plan
```

생성될 리소스 목록을 확인합니다 (약 50개 리소스).

### 3. 인프라 생성

```bash
terraform apply
```

⏱️ **소요 시간**: 약 10-15분 (RDS Multi-AZ 생성 포함)

### 4. 출력 확인

```bash
terraform output
```

주요 출력:
- `alb_dns_name`: 백엔드 API 엔드포인트
- `cloudfront_url`: 프론트엔드 URL
- `ecr_repository_url`: Docker 이미지 푸시 URL
- `deployment_instructions`: 배포 가이드

## 📦 애플리케이션 배포

### Backend (Docker → ECR → ECS)

```bash
# 1. ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url)

# 2. Docker 이미지 빌드
cd ../../patient-aws/backend
docker build -t $(terraform output -raw ecr_repository_url):latest .

# 3. ECR에 푸시
docker push $(terraform output -raw ecr_repository_url):latest

# 4. ECS 서비스 업데이트
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment \
  --region ap-northeast-2
```

### Frontend (Next.js → S3 → CloudFront)

```bash
# 1. 빌드 (환경변수 주입)
cd ../../patient-aws/frontend
export NEXT_PUBLIC_API_URL=http://$(terraform output -raw alb_dns_name)
npm run build

# 2. S3 업로드
aws s3 sync out/ s3://$(terraform output -raw s3_bucket_name)/ --delete

# 3. CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## 🧪 동작 확인

### Backend Health Check

```bash
ALB_URL=$(terraform output -raw alb_dns_name)
curl http://$ALB_URL/health

# 예상 출력:
# {"status":"ok","database":{"connected":true},"memory":{"used":"XX.XXMB"}}
```

### Frontend Access

```bash
# CloudFront URL 출력
terraform output cloudfront_url

# 브라우저에서 접속
```

## 📊 모니터링

### CloudWatch Logs

```bash
# 로그 그룹명 확인
terraform output cloudwatch_log_group

# 로그 스트림 조회
aws logs tail /ecs/patient-zone --follow
```

### ECS 콘솔

```bash
# ECS 클러스터 URL
echo "https://console.aws.amazon.com/ecs/v2/clusters/$(terraform output -raw ecs_cluster_name)"
```

## 🧹 인프라 삭제

**주의**: 모든 리소스가 영구 삭제됩니다!

```bash
# 1. S3 버킷 비우기 (CloudFront OAC 때문에 수동 필요)
aws s3 rm s3://$(terraform output -raw s3_bucket_name) --recursive

# 2. ECR 이미지 삭제
aws ecr batch-delete-image \
  --repository-name patient-zone-backend \
  --image-ids imageTag=latest

# 3. Terraform destroy
terraform destroy
```

## 📁 모듈 구조

```
patient-aws/
├── main.tf                    # 메인 구성 (모듈 조합)
├── variables.tf               # 입력 변수 정의
├── outputs.tf                 # 출력 변수 정의
├── terraform.tfvars.example   # 변수 예시
├── .gitignore
├── README.md
└── modules/
    ├── network/               # VPC, Subnets, NAT, Security Groups
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── database/              # RDS MySQL
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── app_cluster/           # ECS, ECR, ALB
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── static_site/           # S3, CloudFront
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## 🔐 보안 고려사항

1. **Secrets 관리**
   - `terraform.tfvars`는 절대 Git에 커밋하지 않음 (.gitignore 포함)
   - 프로덕션에서는 AWS Secrets Manager 사용 권장

2. **Network 보안**
   - RDS는 Private 서브넷에만 배치
   - ECS 태스크는 ALB에서만 트래픽 수신
   - Security Group으로 최소 권한 원칙 적용

3. **Data 보안**
   - RDS 암호화 활성화 (storage_encrypted = true)
   - S3 버킷 Public Access 차단
   - CloudFront HTTPS 강제 리디렉션

## 💰 비용 최적화

### 개발/테스트 환경

```hcl
# terraform.tfvars
db_instance_class = "db.t3.micro"     # ~$15/월
db_multi_az       = false             # Multi-AZ 비활성화
ecs_desired_count = 1                 # 최소 태스크 수
```

### 프로덕션 환경

```hcl
# terraform.tfvars
db_instance_class = "db.t3.small"     # ~$30/월
db_multi_az       = true              # 고가용성 활성화
ecs_desired_count = 2                 # 이중화
```

**예상 월 비용**: 약 $50-100 (사용량에 따라 변동)

## 🎯 Megazone Cloud 포트폴리오 포인트

✅ **Terraform IaC**: 코드로 관리되는 전체 인프라
✅ **3-Tier Architecture**: VPC 설계 + 보안 그룹 분리
✅ **고가용성**: Multi-AZ 배포 + Auto Scaling 준비
✅ **모듈화**: 재사용 가능한 Terraform 모듈 설계
✅ **보안**: 최소 권한 원칙 + 암호화 + Private Subnet
✅ **모니터링**: CloudWatch Logs + Container Insights

---

**작성일**: 2024-12-10
**문의**: Cloud Doctor MVP 프로젝트 팀
