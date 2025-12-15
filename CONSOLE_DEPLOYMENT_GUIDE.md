# Cloud Doctor MVP - 콘솔 수동 배포 가이드

> AWS와 GCP 콘솔을 사용한 전체 시스템 수동 배포 가이드
>
> **작성일**: 2025-12-12
> **소요 시간**: 약 2-3시간
> **난이도**: 중급

---

## 📋 목차

### 사전 준비
1. [필요한 도구 및 계정](#필요한-도구-및-계정)
2. [환경 변수 준비](#환경-변수-준비)

### AWS Patient Zone 배포
3. [Step 1: VPC 및 네트워크 구성 (30분)](#step-1-vpc-및-네트워크-구성)
4. [Step 2: RDS 데이터베이스 생성 (20분)](#step-2-rds-데이터베이스-생성)
5. [Step 3: ECR 및 Docker 이미지 푸시 (15분)](#step-3-ecr-및-docker-이미지-푸시)
6. [Step 4: ECS 클러스터 및 서비스 생성 (30분)](#step-4-ecs-클러스터-및-서비스-생성)
7. [Step 5: Application Load Balancer 구성 (20분)](#step-5-application-load-balancer-구성)
8. [Step 6: Frontend 배포 (S3 + CloudFront) (25분)](#step-6-frontend-배포-s3--cloudfront)

### GCP Doctor Zone 배포
9. [Step 7: GCP Cloud Run 배포 (20분)](#step-7-gcp-cloud-run-배포)

### 통합 및 테스트
10. [Step 8: Slack Bot 연동 (15분)](#step-8-slack-bot-연동)
11. [Step 9: 전체 시스템 테스트 (15분)](#step-9-전체-시스템-테스트)

---

## 필요한 도구 및 계정

### ✅ 필수 계정

1. **AWS 계정**
   - IAM 사용자 권한: Administrator 또는 다음 권한:
     - VPC, EC2, ECS, RDS, ECR, S3, CloudFront, IAM, CloudWatch

2. **GCP 계정**
   - 프로젝트 생성 권한
   - Cloud Run, Artifact Registry, Vertex AI 활성화 권한

3. **Slack Workspace** (선택)
   - App 생성 및 Webhook 설정 권한

### ✅ 필수 도구

```bash
# 설치 확인
docker --version        # Docker 20.10+
aws --version           # AWS CLI v2
gcloud --version        # Google Cloud SDK
node --version          # Node.js 18+
npm --version           # npm 9+
```

### ✅ 계정 설정

```bash
# AWS CLI 설정
aws configure
# AWS Access Key ID: your-key
# AWS Secret Access Key: your-secret
# Default region: ap-northeast-2
# Default output format: json

# GCP CLI 설정
gcloud auth login
gcloud config set project your-project-id
```

---

## 환경 변수 준비

### 🔐 생성 및 저장할 값들

배포 중 생성되는 값들을 메모장에 기록하세요:

```bash
# AWS 관련
export AWS_REGION="ap-northeast-2"
export VPC_ID=""                    # Step 1에서 생성
export DB_ENDPOINT=""               # Step 2에서 생성
export DB_PASSWORD="Wkrwjs12*"      # 원하는 비밀번호
export JWT_SECRET="$(openssl rand -base64 32)"  # 랜덤 생성
export ECR_URI=""                   # Step 3에서 생성
export ALB_DNS_NAME=""              # Step 5에서 생성
export CLOUDFRONT_URL=""            # Step 6에서 생성

# GCP 관련
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-northeast3"
export DOCTOR_ZONE_URL=""           # Step 7에서 생성

# Slack 관련 (선택)
export SLACK_WEBHOOK_URL=""         # Step 8에서 생성
```

---

## Step 1: VPC 및 네트워크 구성

### 1-1. VPC 생성

1. **AWS Console → VPC → "Create VPC"**
2. 설정값 입력:
   ```
   Name tag: patient-zone-vpc
   IPv4 CIDR block: 10.0.0.0/16
   IPv6 CIDR block: No IPv6
   Tenancy: Default
   ```
3. **"Create VPC"** 클릭
4. 생성된 VPC ID를 메모: `vpc-xxxxxxxxx`

```bash
export VPC_ID="vpc-xxxxxxxxx"
```

### 1-2. Internet Gateway 생성 및 연결

1. **VPC → Internet Gateways → "Create internet gateway"**
2. 설정:
   ```
   Name tag: patient-zone-igw
   ```
3. 생성 후 **"Actions" → "Attach to VPC"** 선택
4. VPC 선택: `patient-zone-vpc`

### 1-3. Subnets 생성

#### Public Subnet 1
1. **VPC → Subnets → "Create subnet"**
2. 설정:
   ```
   VPC: patient-zone-vpc
   Subnet name: patient-zone-public-1
   Availability Zone: ap-northeast-2a
   IPv4 CIDR block: 10.0.1.0/24
   ```

#### Public Subnet 2
```
Subnet name: patient-zone-public-2
Availability Zone: ap-northeast-2c
IPv4 CIDR block: 10.0.2.0/24
```

#### Private Subnet 1 (ECS)
```
Subnet name: patient-zone-private-1
Availability Zone: ap-northeast-2a
IPv4 CIDR block: 10.0.11.0/24
```

#### Private Subnet 2 (ECS)
```
Subnet name: patient-zone-private-2
Availability Zone: ap-northeast-2c
IPv4 CIDR block: 10.0.12.0/24
```

#### Database Subnet 1
```
Subnet name: patient-zone-db-1
Availability Zone: ap-northeast-2a
IPv4 CIDR block: 10.0.21.0/24
```

#### Database Subnet 2
```
Subnet name: patient-zone-db-2
Availability Zone: ap-northeast-2c
IPv4 CIDR block: 10.0.22.0/24
```

### 1-4. NAT Gateway 생성

1. **VPC → NAT Gateways → "Create NAT gateway"**
2. 설정:
   ```
   Name: patient-zone-nat
   Subnet: patient-zone-public-1 (Public subnet 선택!)
   ```
3. **"Allocate Elastic IP"** 클릭 (새 EIP 할당)
4. **"Create NAT gateway"** 클릭
5. 생성 완료까지 약 2-3분 대기

### 1-5. Route Tables 생성 및 설정

#### Public Route Table
1. **VPC → Route Tables → "Create route table"**
2. 설정:
   ```
   Name: patient-zone-public-rt
   VPC: patient-zone-vpc
   ```
3. 생성 후 **"Routes" 탭 → "Edit routes"**
4. Route 추가:
   ```
   Destination: 0.0.0.0/0
   Target: Internet Gateway (patient-zone-igw)
   ```
5. **"Subnet associations" 탭 → "Edit subnet associations"**
6. Public subnets 선택:
   - `patient-zone-public-1`
   - `patient-zone-public-2`

#### Private Route Table
1. Route Table 생성:
   ```
   Name: patient-zone-private-rt
   VPC: patient-zone-vpc
   ```
2. Route 추가:
   ```
   Destination: 0.0.0.0/0
   Target: NAT Gateway (patient-zone-nat)
   ```
3. Subnet associations:
   - `patient-zone-private-1`
   - `patient-zone-private-2`

#### Database Route Table
1. Route Table 생성:
   ```
   Name: patient-zone-db-rt
   VPC: patient-zone-vpc
   ```
2. Route: Local만 유지 (외부 통신 불필요)
3. Subnet associations:
   - `patient-zone-db-1`
   - `patient-zone-db-2`

### 1-6. Security Groups 생성

#### ALB Security Group
1. **EC2 → Security Groups → "Create security group"**
2. 설정:
   ```
   Security group name: patient-zone-alb-sg
   Description: ALB security group
   VPC: patient-zone-vpc
   ```
3. Inbound rules:
   ```
   Type: HTTP
   Port: 80
   Source: 0.0.0.0/0
   Description: Allow HTTP from internet
   ```
4. Outbound rules: 기본값 유지 (All traffic)

#### ECS Security Group
```
Security group name: patient-zone-ecs-sg
Description: ECS tasks security group
VPC: patient-zone-vpc

Inbound rules:
- Type: Custom TCP
  Port: 3000
  Source: patient-zone-alb-sg
  Description: Allow traffic from ALB

Outbound rules: All traffic
```

#### RDS Security Group
```
Security group name: patient-zone-rds-sg
Description: RDS security group
VPC: patient-zone-vpc

Inbound rules:
- Type: MySQL/Aurora
  Port: 3306
  Source: patient-zone-ecs-sg
  Description: Allow MySQL from ECS

Outbound rules: All traffic
```

### ✅ Step 1 완료 확인

다음 항목들이 생성되었는지 확인:
- ✅ VPC: `patient-zone-vpc` (10.0.0.0/16)
- ✅ Subnets: 6개 (Public 2, Private 2, DB 2)
- ✅ Internet Gateway: 연결됨
- ✅ NAT Gateway: Public subnet에 배치됨
- ✅ Route Tables: 3개 (Public, Private, DB)
- ✅ Security Groups: 3개 (ALB, ECS, RDS)

---

## Step 2: RDS 데이터베이스 생성

### 2-1. DB Subnet Group 생성

1. **RDS → Subnet groups → "Create DB subnet group"**
2. 설정:
   ```
   Name: patient-zone-db-subnet-group
   Description: Patient Zone database subnet group
   VPC: patient-zone-vpc

   Add subnets:
   - Availability Zone: ap-northeast-2a
     Subnet: patient-zone-db-1 (10.0.21.0/24)
   - Availability Zone: ap-northeast-2c
     Subnet: patient-zone-db-2 (10.0.22.0/24)
   ```
3. **"Create"** 클릭

### 2-2. RDS 인스턴스 생성

1. **RDS → Databases → "Create database"**
2. 설정 입력:

#### Engine options
```
Engine type: MySQL
Edition: MySQL Community
Engine version: 8.0.35 (또는 최신 8.0.x)
```

#### Templates
```
Template: Production (또는 Free tier로 테스트)
```

#### Settings
```
DB instance identifier: patient-zone-mysql
Master username: admin
Master password: Wkrwjs12*
Confirm password: Wkrwjs12*
```

#### Instance configuration
```
DB instance class: db.t3.micro (Free tier)
또는: db.m5.large (Production)
```

#### Storage
```
Storage type: General Purpose SSD (gp3)
Allocated storage: 20 GiB
Storage autoscaling: Enable (최대 100 GiB)
```

#### Connectivity
```
Virtual private cloud (VPC): patient-zone-vpc
DB subnet group: patient-zone-db-subnet-group
Public access: No
VPC security group:
- Remove default
- Add: patient-zone-rds-sg
Availability Zone: No preference
```

#### Database authentication
```
Database authentication: Password authentication
```

#### Additional configuration
```
Initial database name: patient_db
DB parameter group: default.mysql8.0
Backup retention period: 7 days
Enable encryption: Yes
Enable Enhanced monitoring: Yes (선택)
```

3. **"Create database"** 클릭
4. 생성 완료까지 약 10-15분 대기

### 2-3. 엔드포인트 확인

생성 완료 후:
1. 데이터베이스 선택 → **"Connectivity & security"** 탭
2. **Endpoint** 복사:
   ```
   patient-zone-mysql.cxxxxxx.ap-northeast-2.rds.amazonaws.com
   ```

```bash
export DB_ENDPOINT="patient-zone-mysql.cxxxxxx.ap-northeast-2.rds.amazonaws.com"
```

### ✅ Step 2 완료 확인

```bash
# RDS 연결 테스트 (ECS 환경에서만 가능, 지금은 Skip)
# mysql -h $DB_ENDPOINT -u admin -p patient_db
```

- ✅ RDS 인스턴스: `Available` 상태
- ✅ Endpoint 확인됨
- ✅ Security group 적용됨

---

## Step 3: ECR 및 Docker 이미지 푸시

### 3-1. ECR Repository 생성

1. **ECR → Repositories → "Create repository"**
2. 설정:
   ```
   Visibility settings: Private
   Repository name: patient-zone-backend
   Tag immutability: Disabled
   Scan on push: Enabled (선택)
   Encryption settings: AES-256
   ```
3. **"Create repository"** 클릭
4. URI 복사:
   ```
   827913617839.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend
   ```

```bash
export ECR_URI="827913617839.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend"
```

### 3-2. Backend Docker 이미지 빌드 및 푸시

```bash
cd ~/workspace/cloud-doctor-mvp/patient-aws/backend

# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin $ECR_URI

# Docker 이미지 빌드
docker build -t patient-zone-backend:latest .

# 태그 설정
docker tag patient-zone-backend:latest $ECR_URI:latest

# ECR에 푸시
docker push $ECR_URI:latest
```

**예상 출력:**
```
The push refers to repository [827913617839.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend]
latest: digest: sha256:xxxxx size: 1234
```

### ✅ Step 3 완료 확인

- ✅ ECR repository 생성됨
- ✅ Docker 이미지 푸시 성공
- ✅ 이미지 태그: `latest`

---

## Step 4: ECS 클러스터 및 서비스 생성

### 4-1. ECS Cluster 생성

1. **ECS → Clusters → "Create cluster"**
2. 설정:
   ```
   Cluster name: patient-zone-cluster
   Infrastructure: AWS Fargate (serverless)
   ```
3. **"Create"** 클릭

### 4-2. CloudWatch Logs 그룹 생성

1. **CloudWatch → Log groups → "Create log group"**
2. 설정:
   ```
   Log group name: /ecs/patient-zone
   Retention setting: 7 days (또는 원하는 기간)
   ```

### 4-3. IAM Role 생성 (ECS Task Execution Role)

1. **IAM → Roles → "Create role"**
2. 설정:
   ```
   Trusted entity type: AWS service
   Use case: Elastic Container Service → Elastic Container Service Task
   ```
3. Permissions policies:
   - `AmazonECSTaskExecutionRolePolicy`
4. Role name: `patient-zone-ecs-execution-role`
5. **"Create role"** 클릭

### 4-4. Task Definition 생성

1. **ECS → Task Definitions → "Create new task definition"**
2. **"Create new task definition" → "JSON"** 클릭
3. 다음 JSON 입력 (값들을 실제 값으로 변경):

```json
{
  "family": "patient-zone-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::827913617839:role/patient-zone-ecs-execution-role",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "827913617839.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NODE_ENV",
          "value": "production"
        },
        {
          "name": "DB_HOST",
          "value": "patient-zone-mysql.cxxxxxx.ap-northeast-2.rds.amazonaws.com"
        },
        {
          "name": "DB_PORT",
          "value": "3306"
        },
        {
          "name": "DB_NAME",
          "value": "patient_db"
        },
        {
          "name": "DB_USER",
          "value": "admin"
        },
        {
          "name": "DB_PASSWORD",
          "value": "Wkrwjs12*"
        },
        {
          "name": "JWT_SECRET",
          "value": "YOUR_JWT_SECRET_HERE"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/patient-zone",
          "awslogs-region": "ap-northeast-2",
          "awslogs-stream-prefix": "backend"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:3000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

4. **"Create"** 클릭

### ✅ Step 4 완료 확인

- ✅ ECS Cluster 생성됨
- ✅ CloudWatch Log group 생성됨
- ✅ Task Definition 생성됨
- ✅ Task Definition revision: 1

---

## Step 5: Application Load Balancer 구성

### 5-1. Target Group 생성

1. **EC2 → Target Groups → "Create target group"**
2. 설정:

#### Basic configuration
```
Choose a target type: IP addresses
Target group name: patient-zone-tg
Protocol: HTTP
Port: 3000
VPC: patient-zone-vpc
Protocol version: HTTP1
```

#### Health checks
```
Health check protocol: HTTP
Health check path: /health
Advanced health check settings:
  Port: Traffic port
  Healthy threshold: 2
  Unhealthy threshold: 3
  Timeout: 5
  Interval: 30
  Success codes: 200
```

3. **"Next"** 클릭
4. Register targets: Skip (ECS 서비스가 자동 등록)
5. **"Create target group"** 클릭

### 5-2. Application Load Balancer 생성

1. **EC2 → Load Balancers → "Create load balancer"**
2. **"Application Load Balancer" → "Create"**

#### Basic configuration
```
Load balancer name: patient-zone-alb
Scheme: Internet-facing
IP address type: IPv4
```

#### Network mapping
```
VPC: patient-zone-vpc
Mappings:
  - ap-northeast-2a: patient-zone-public-1
  - ap-northeast-2c: patient-zone-public-2
```

#### Security groups
```
- Remove default
- Add: patient-zone-alb-sg
```

#### Listeners and routing
```
Protocol: HTTP
Port: 80
Default action: Forward to target group
  Target group: patient-zone-tg
```

3. **"Create load balancer"** 클릭
4. 생성 완료까지 약 3-5분 대기

### 5-3. ALB DNS 이름 확인

1. Load Balancer 선택
2. **"DNS name"** 복사:
   ```
   patient-zone-alb-789996804.ap-northeast-2.elb.amazonaws.com
   ```

```bash
export ALB_DNS_NAME="patient-zone-alb-789996804.ap-northeast-2.elb.amazonaws.com"
```

### ✅ Step 5 완료 확인

- ✅ Target Group 생성됨
- ✅ ALB 생성됨 (상태: active)
- ✅ ALB DNS 이름 확인됨

---

## Step 5-4: ECS Service 생성

이제 ALB가 준비되었으니 ECS Service를 생성합니다.

1. **ECS → Clusters → patient-zone-cluster → "Services" → "Create"**

#### Environment
```
Compute options: Launch type
Launch type: FARGATE
Platform version: LATEST
```

#### Deployment configuration
```
Application type: Service
Family: patient-zone-task
Revision: 1 (latest)
Service name: patient-zone-service
Service type: Replica
Desired tasks: 2
```

#### Networking
```
VPC: patient-zone-vpc
Subnets:
  - patient-zone-private-1
  - patient-zone-private-2
Security group: patient-zone-ecs-sg
Public IP: DISABLED
```

#### Load balancing
```
Load balancer type: Application Load Balancer
Load balancer: patient-zone-alb
Listener: 80:HTTP
Target group: patient-zone-tg
Health check grace period: 60 seconds
```

#### Service auto scaling
```
Use service auto scaling: No (나중에 설정 가능)
```

2. **"Create"** 클릭
3. 서비스 시작까지 약 5분 대기

### 5-5. ECS Service 상태 확인

```bash
# ECS 서비스 상태 확인
aws ecs describe-services \
  --cluster patient-zone-cluster \
  --services patient-zone-service \
  --region ap-northeast-2 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount}'
```

**예상 출력:**
```json
{
    "Status": "ACTIVE",
    "Running": 2,
    "Desired": 2
}
```

### 5-6. Target Group Health Check 확인

1. **EC2 → Target Groups → patient-zone-tg → "Targets" 탭**
2. Health status: `healthy` (2/2 targets)

### 5-7. ALB 테스트

```bash
# Health check
curl http://$ALB_DNS_NAME/health

# 예상 응답
{"status":"ok"}
```

### ✅ Step 5-4 완료 확인

- ✅ ECS Service 생성됨
- ✅ Running tasks: 2/2
- ✅ Target group: healthy (2/2)
- ✅ ALB 응답 확인

---

## Step 6: Frontend 배포 (S3 + CloudFront)

### 6-1. S3 Bucket 생성

1. **S3 → Buckets → "Create bucket"**
2. 설정:
   ```
   Bucket name: cloud-doctor-patient-frontend-[random-string]
   예: cloud-doctor-patient-frontend-joon234

   AWS Region: ap-northeast-2

   Object Ownership: ACLs disabled

   Block Public Access settings:
   - Block all public access: UNCHECK (CloudFront will access)

   Bucket Versioning: Disable

   Default encryption: Enable (SSE-S3)
   ```
3. **"Create bucket"** 클릭

### 6-2. S3 Bucket Policy 설정

1. 생성한 버킷 선택 → **"Permissions" 탭**
2. **"Bucket policy" → "Edit"**
3. 다음 Policy 입력 (버킷 이름 수정):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::cloud-doctor-patient-frontend-joon234/*"
        }
    ]
}
```

### 6-3. Frontend 빌드 (환경 변수 설정)

```bash
cd ~/workspace/cloud-doctor-mvp/patient-aws/frontend

# ALB URL을 환경 변수로 설정 (빌드 시 사용)
export NEXT_PUBLIC_API_URL=""

# Next.js 빌드 실행
npm run build
```

**빌드 성공 확인:**
```
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages
✓ Finalizing page optimization
```

### 6-4. S3에 빌드 파일 업로드

```bash
# S3에 빌드 결과 업로드
aws s3 sync out/ s3://cloud-doctor-patient-frontend-joon234/ --delete

# 업로드 확인
aws s3 ls s3://cloud-doctor-patient-frontend-joon234/ --recursive | head -10
```

### 6-5. CloudFront Distribution 생성

1. **CloudFront → Distributions → "Create distribution"**

#### Origin settings
```
Origin domain: cloud-doctor-patient-frontend-joon234.s3.ap-northeast-2.amazonaws.com
Name: S3-patient-frontend
Origin access: Origin access control settings (recommended)
  - Click "Create control setting"
    Origin access control:
      Name: patient-frontend-oac
      Signing behavior: Sign requests
      Origin type: S3
```

#### Default cache behavior
```
Viewer protocol policy: Redirect HTTP to HTTPS
Allowed HTTP methods: GET, HEAD
Cache policy: CachingOptimized
```

#### Settings
```
Price class: Use only North America and Europe (lowest cost)
Alternate domain name (CNAME): 비어있음 (optional)
Custom SSL certificate: Default CloudFront certificate
Supported HTTP versions: HTTP/2
Default root object: cloud-doctor/index.html
```

2. **"Create distribution"** 클릭
3. 배포 완료까지 약 10-15분 대기 (Status: Deployed)

### 6-6. S3 Bucket Policy 업데이트 (CloudFront용)

1. CloudFront Distribution 생성 완료 후
2. **"Copy policy"** 버튼 클릭 (또는 수동으로 ARN 복사)
3. **S3 → Bucket → Permissions → Bucket policy → Edit**
4. 다음 Policy로 **전체 교체**:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::cloud-doctor-patient-frontend-joon234/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::827913617839:distribution/E3TGIUAI1WR54Q"
                }
            }
        }
    ]
}
```

### 6-7. CloudFront URL 확인

1. CloudFront Distribution 선택
2. **"Distribution domain name"** 복사:
   ```
   d1234abcd5678.cloudfront.net
   ```

```bash
export CLOUDFRONT_URL="https://d1234abcd5678.cloudfront.net"
```

### 6-8. Frontend 접속 테스트

```bash
# 브라우저에서 접속
echo "$CLOUDFRONT_URL/cloud-doctor"
```

**예상 결과:**
- Cloud Doctor 홈 화면 표시
- "로그인" 버튼 클릭 시 로그인 페이지 이동
- 회원가입 및 로그인 가능

### ✅ Step 6 완료 확인

- ✅ S3 Bucket 생성 및 파일 업로드
- ✅ CloudFront Distribution 배포됨
- ✅ Frontend 접속 가능
- ✅ API 통신 정상 (ALB 프록시)

---

## Step 7: GCP Cloud Run 배포

### 7-1. GCP 프로젝트 설정

```bash
# GCP 프로젝트 ID 설정
export GCP_PROJECT_ID="cloud-doctor-mvp-480808"
gcloud config set project $GCP_PROJECT_ID

# 필요한 API 활성화
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 7-2. Artifact Registry Repository 생성

1. **GCP Console → Artifact Registry → "CREATE REPOSITORY"**
2. 설정:
   ```
   Name: cloud-doctor
   Format: Docker
   Mode: Standard
   Location type: Region
   Region: asia-northeast3 (Seoul)

   Encryption: Google-managed encryption key
   Immutable image tags: Disabled
   Cleanup policies: Keep all artifacts
   ```
3. **"CREATE"** 클릭

### 7-3. Docker 인증 설정

```bash
# Artifact Registry 인증
gcloud auth configure-docker asia-northeast3-docker.pkg.dev
```

### 7-4. 환경 변수 설정

```bash
cd ~/workspace/cloud-doctor-mvp/doctor-gcp

# 환경 변수 설정
export GCP_PROJECT_ID="cloud-doctor-mvp-480808"
export CLAUDE_API_KEY="your-claude-api-key"
export SLACK_WEBHOOK_URL="your-slack-webhook-url"
export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
export AWS_REGION="ap-northeast-2"
export LOG_GROUP_NAME="/ecs/patient-zone"
```

### 7-5. Docker 이미지 빌드 및 푸시

```bash
# 이미지 빌드
docker build -t asia-northeast3-docker.pkg.dev/$GCP_PROJECT_ID/cloud-doctor/doctor-zone:latest .

# 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/$GCP_PROJECT_ID/cloud-doctor/doctor-zone:latest
```

### 7-6. Cloud Run 서비스 배포 (콘솔)

1. **GCP Console → Cloud Run → "CREATE SERVICE"**

#### Container settings
```
Container image URL:
  asia-northeast3-docker.pkg.dev/cloud-doctor-mvp-480808/cloud-doctor/doctor-zone:latest

Service name: doctor-zone
Region: asia-northeast3 (Seoul)
CPU allocation and pricing: CPU is only allocated during request processing
```

#### Autoscaling
```
Minimum number of instances: 0
Maximum number of instances: 10
```

#### Ingress control
```
Ingress: Allow all traffic
```

#### Authentication
```
Authentication: Allow unauthenticated invocations
```

#### Container(s), Volumes, Networking, Security
- **"CONTAINER" 탭 클릭 → "Environment variables"**

환경 변수 추가:
```
GCP_PROJECT_ID = cloud-doctor-mvp-480808
GCP_LOCATION = us-central1
CLAUDE_API_KEY = your-claude-api-key
SLACK_WEBHOOK_URL = your-slack-webhook-url
AWS_ACCESS_KEY_ID = AKIA...
AWS_SECRET_ACCESS_KEY = ...
AWS_REGION = ap-northeast-2
LOG_GROUP_NAME = /ecs/patient-zone
```

- **"RESOURCES" 설정:**
```
Memory: 2 GiB
CPU: 1
```

- **"REQUEST TIMEOUT":**
```
Request timeout: 300 seconds
```

2. **"CREATE"** 클릭
3. 배포 완료까지 약 3-5분 대기

### 7-7. Cloud Run URL 확인

배포 완료 후:
```
Service URL: https://doctor-zone-843761229274.asia-northeast3.run.app
```

```bash
export DOCTOR_ZONE_URL="https://doctor-zone-843761229274.asia-northeast3.run.app"
```

### 7-8. Doctor Zone 테스트

```bash
# Health check
curl $DOCTOR_ZONE_URL/health

# 예상 응답
{"status":"ok"}

# 상세 정보
curl $DOCTOR_ZONE_URL/ | jq .
```

**예상 응답:**
```json
{
  "service": "Cloud Doctor Enhanced (Vertex AI)",
  "status": "healthy",
  "timestamp": "2025-12-12T10:30:00.123Z",
  "version": "2.1.0",
  "features": {
    "log_analysis": "Vertex AI Gemini 2.0 Flash",
    "terraform_generation": "Claude Sonnet 4.5",
    "slack_notifications": true,
    "uses_gcp_credits": true
  }
}
```

### ✅ Step 7 완료 확인

- ✅ Artifact Registry repository 생성
- ✅ Docker 이미지 푸시 성공
- ✅ Cloud Run 서비스 배포됨
- ✅ Health check 정상 응답

---

## Step 8: Slack Bot 연동

### 8-1. Slack App 생성

1. **https://api.slack.com/apps 접속**
2. **"Create New App" → "From scratch"**
3. 설정:
   ```
   App Name: Cloud_Doctor
   Pick a workspace: 본인의 Slack Workspace
   ```
4. **"Create App"** 클릭

### 8-2. Incoming Webhooks 설정

1. 좌측 메뉴 **"Incoming Webhooks"** 클릭
2. **"Activate Incoming Webhooks" → ON**
3. 하단 **"Add New Webhook to Workspace"** 클릭
4. 채널 선택 (예: #cloud-doctor)
5. **"Allow"** 클릭
6. Webhook URL 복사:
   ```
   https://hooks.slack.com/services/T.../B.../xxx...
   ```

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### 8-3. Cloud Run 환경 변수 업데이트

```bash
# Cloud Run 서비스에 Slack Webhook URL 추가
gcloud run services update doctor-zone \
  --region asia-northeast3 \
  --update-env-vars SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL
```

### 8-4. Slash Commands 설정

#### /analyze-logs 커맨드

1. 좌측 메뉴 **"Slash Commands"** 클릭
2. **"Create New Command"** 클릭
3. 설정:
   ```
   Command: /analyze-logs
   Request URL: https://doctor-zone-843761229274.asia-northeast3.run.app/slack/command
   Short Description: 로그 분석 (Gemini)
   Usage Hint: [시간(분), 기본값: 30]
   ```
4. **"Save"** 클릭

#### /terraform 커맨드

1. **"Create New Command"** 클릭
2. 설정:
   ```
   Command: /terraform
   Request URL: https://doctor-zone-843761229274.asia-northeast3.run.app/slack/command
   Short Description: Terraform 코드 생성 (Gemini + Claude)
   Usage Hint: [시간(분), 기본값: 30]
   ```
3. **"Save"** 클릭

### 8-5. Slack App 재설치

1. 상단 배너에 **"You've changed the permission scopes..."** 메시지 표시
2. **"reinstall your app"** 링크 클릭
3. **"Allow"** 클릭

### 8-6. Slack Bot 테스트

#### Webhook 테스트
```bash
curl -X POST $DOCTOR_ZONE_URL/slack/test
```

**Slack 채널 확인:**
```
✅ Slack 연동 테스트

이 메시지가 보인다면, Slack Webhook이 정상 작동합니다!
```

#### Slash Command 테스트

Slack 채널에서 입력:
```
/analyze-logs 10
```

**예상 응답:**
```
✅ 로그 분석 요청이 접수되었습니다. (최근 10분)

분석 완료 시 자동으로 결과를 전송합니다.
```

### ✅ Step 8 완료 확인

- ✅ Slack App 생성됨
- ✅ Incoming Webhooks 설정됨
- ✅ Slash Commands 설정됨 (/analyze-logs, /terraform)
- ✅ Webhook 테스트 성공
- ✅ Slash command 테스트 성공

---

## Step 9: 전체 시스템 테스트

### 9-1. Frontend 접속 테스트

```bash
echo "Frontend URL: $CLOUDFRONT_URL/cloud-doctor"
```

**테스트 시나리오:**
1. 브라우저에서 Frontend URL 접속
2. **"회원가입"** 클릭
   ```
   이메일: test@example.com
   비밀번호: test123456
   이름: 테스트사용자
   ```
3. 회원가입 후 자동 로그인
4. **"게시판"** 메뉴 클릭
5. **"글쓰기"** 클릭
   ```
   제목: 테스트 게시글
   내용: Cloud Doctor MVP 테스트입니다!
   ```
6. 게시글 목록에서 방금 작성한 글 확인

### 9-2. API 직접 테스트

```bash
# 회원가입
curl -X POST "http://$ALB_DNS_NAME/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api-test@example.com",
    "password": "test123456",
    "name": "API Test User"
  }'

# 로그인
curl -X POST "http://$ALB_DNS_NAME/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "api-test@example.com",
    "password": "test123456"
  }' | jq .
```

**예상 응답:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "email": "api-test@example.com",
    "name": "API Test User"
  }
}
```

### 9-3. 장애 시나리오 테스트

#### Scenario 1: DB Connection Failure

```bash
curl -X POST "http://$ALB_DNS_NAME/api/debug/scenario?type=db-failure&duration=180"
```

**Slack에서 확인:**
```
/analyze-logs 5
```

**예상 결과:**
- Gemini가 DB 연결 오류 분석
- 해결 방법 제시
- Slack 알림 수신

#### Scenario 2: High Memory Usage

```bash
curl -X POST "http://$ALB_DNS_NAME/api/debug/scenario?type=memory-leak&duration=180"
```

**Slack에서 확인:**
```
/analyze-logs 5
```

### 9-4. Terraform 코드 생성 테스트

```bash
# DB 오류 시나리오 실행 중
/terraform 5
```

**예상 결과:**
- Gemini 분석 결과
- Claude가 생성한 Terraform 코드
- RDS 설정 수정 제안

### 9-5. CloudWatch Logs 확인

```bash
# 최근 5분간 ECS 로그 확인
aws logs tail /ecs/patient-zone --since 5m --region ap-northeast-2
```

### 9-6. Cloud Run Logs 확인

```bash
# Cloud Run 로그 확인 (최근 50개)
gcloud run services logs read doctor-zone --region asia-northeast3 --limit 50
```

또는 GCP Console에서:
```
https://console.cloud.google.com/run/detail/asia-northeast3/doctor-zone/logs?project=cloud-doctor-mvp-480808
```

### ✅ Step 9 완료 확인

- ✅ Frontend 회원가입/로그인 정상
- ✅ 게시글 CRUD 정상
- ✅ API 직접 호출 정상
- ✅ 장애 시나리오 감지 정상
- ✅ Slack Bot 응답 정상
- ✅ CloudWatch 로그 수집 정상
- ✅ Cloud Run 로그 확인 가능

---

## 🎉 배포 완료!

### 📝 배포된 리소스 요약

#### AWS Patient Zone
```
VPC: 10.0.0.0/16
  - Public Subnets: 2개
  - Private Subnets: 2개 (ECS)
  - Database Subnets: 2개

RDS MySQL:
  - Endpoint: patient-zone-mysql.cxxxxxx.ap-northeast-2.rds.amazonaws.com
  - Database: patient_db
  - Instance: db.t3.micro (또는 db.m5.large)

ECS Fargate:
  - Cluster: patient-zone-cluster
  - Service: patient-zone-service
  - Tasks: 2 (desired)

ALB:
  - DNS: patient-zone-alb-789996804.ap-northeast-2.elb.amazonaws.com
  - Target Group: patient-zone-tg

Frontend:
  - S3: cloud-doctor-patient-frontend-joon234
  - CloudFront: d1234abcd5678.cloudfront.net
```

#### GCP Doctor Zone
```
Cloud Run:
  - Service: doctor-zone
  - Region: asia-northeast3 (Seoul)
  - URL: https://doctor-zone-843761229274.asia-northeast3.run.app
  - Memory: 2 GiB
  - CPU: 1

Artifact Registry:
  - Repository: cloud-doctor
  - Region: asia-northeast3
```

#### Slack Integration
```
Slack App: Cloud_Doctor
Commands:
  - /analyze-logs: Gemini 로그 분석
  - /terraform: Gemini + Claude Terraform 생성
Webhook: Incoming Webhooks
```

### 🔗 접속 URL

```bash
# Frontend (사용자용)
echo "$CLOUDFRONT_URL/cloud-doctor"
# 예: https://d1234abcd5678.cloudfront.net/cloud-doctor

# Backend API (내부용)
echo "http://$ALB_DNS_NAME"
# 예: http://patient-zone-alb-789996804.ap-northeast-2.elb.amazonaws.com

# Doctor Zone (내부용)
echo "$DOCTOR_ZONE_URL"
# 예: https://doctor-zone-843761229274.asia-northeast3.run.app
```

### 💰 예상 월 비용

#### AWS (약 $100-150/월)
- RDS db.t3.micro: $15
- RDS db.m5.large: $140 (Production)
- ECS Fargate (2 tasks): $30
- ALB: $20
- NAT Gateway: $35
- S3 + CloudFront: $5

#### GCP (약 $10-20/월)
- Cloud Run (min=0): $10
- Cloud Run (min=1): $15
- Artifact Registry: $1
- Vertex AI (usage): $3

**총 예상 비용: $110-170/월** (Free tier 제외)

### 🛠️ 운영 가이드

#### 로그 모니터링
```bash
# AWS CloudWatch
aws logs tail /ecs/patient-zone --follow --region ap-northeast-2

# GCP Cloud Run
gcloud run services logs read doctor-zone --region asia-northeast3 --limit 50
```

#### 스케일링
```bash
# ECS 서비스 스케일링
aws ecs update-service \
  --cluster patient-zone-cluster \
  --service patient-zone-service \
  --desired-count 4 \
  --region ap-northeast-2

# Cloud Run은 자동 스케일링 (max-instances: 10)
```

#### 배포 업데이트
```bash
# Backend 업데이트
cd ~/workspace/cloud-doctor-mvp/patient-aws/backend
docker build -t $ECR_URI:latest .
docker push $ECR_URI:latest
aws ecs update-service \
  --cluster patient-zone-cluster \
  --service patient-zone-service \
  --force-new-deployment \
  --region ap-northeast-2

# Frontend 업데이트
cd ~/workspace/cloud-doctor-mvp/patient-aws/frontend
npm run build
aws s3 sync out/ s3://cloud-doctor-patient-frontend-joon234/ --delete
aws cloudfront create-invalidation \
  --distribution-id E3TGIUAI1WR54Q \
  --paths "/*"

# Doctor Zone 업데이트
cd ~/workspace/cloud-doctor-mvp/doctor-gcp
./deploy.sh
```

---

## ⚠️ 주의사항

### 보안
1. **RDS 비밀번호**: Production에서는 AWS Secrets Manager 사용 권장
2. **JWT Secret**: 안전한 랜덤 문자열 사용
3. **API Keys**: 코드에 하드코딩하지 말고 환경 변수 사용
4. **IAM 권한**: 최소 권한 원칙 적용

### 비용
1. **NAT Gateway**: 가장 비용이 많이 드는 리소스 ($35/월)
2. **RDS Multi-AZ**: Production용 (비용 2배)
3. **Cloud Run min-instances**: 0으로 설정하여 비용 절감

### 백업
1. **RDS 자동 백업**: 7일 보관 설정됨
2. **S3 버전 관리**: 필요시 활성화
3. **CloudWatch Logs**: 보관 기간 설정 확인

---

## 📚 참고 문서

- [GETTING_STARTED.md](./GETTING_STARTED.md): Terraform 배포 가이드
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md): 문제 해결 가이드
- [SLACK_BOT_IMPLEMENTATION.md](./SLACK_BOT_IMPLEMENTATION.md): Slack Bot 상세 가이드

---

## ❓ 문제 발생 시

트러블슈팅은 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) 참고:
- Frontend 라우팅 오류
- Mixed Content 보안 오류
- 회원가입 502 오류
- Slack Bot 타임아웃
- AWS Credentials 오류
- 메모리 부족 문제

---

**배포 완료를 축하합니다! 🎉**
