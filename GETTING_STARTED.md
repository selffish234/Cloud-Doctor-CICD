# Cloud Doctor MVP - 완전 상세 시작 가이드

**난이도:** 초급 ~ 중급
**소요 시간:** 약 1-2시간
**목표:** AWS Patient Zone + GCP Doctor Zone 완전 구축 및 동작 확인

---

## 📚 목차

1. [사전 준비 (필수)](#step-0-사전-준비-15분)
2. [AWS Patient Zone 인프라 구축](#step-1-aws-patient-zone-인프라-구축-20분)
3. [Patient Zone 애플리케이션 배포](#step-2-patient-zone-애플리케이션-배포-25분)
4. [GCP Doctor Zone 배포](#step-3-gcp-doctor-zone-배포-20분)
5. [전체 시스템 테스트](#step-4-전체-시스템-테스트-15분)
6. [리소스 정리](#step-5-리소스-정리-10분)

---

## Step 0: 사전 준비 (15분)

### 0-1. 필수 도구 설치 확인

#### ✅ Terraform 설치

```bash
terraform version
```

**예상 출력:**
```
Terraform v1.6.0
on linux_amd64
```

**✗ 설치 안 되어 있다면:**
```bash
# Ubuntu/WSL
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
terraform version
```

#### ✅ AWS CLI 설치

```bash
aws --version
```

**예상 출력:**
```
aws-cli/2.13.0 Python/3.11.0 Linux/5.10.0 source/x86_64
```

**✗ 설치 안 되어 있다면:**
```bash
# Ubuntu/WSL
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

#### ✅ Docker 설치

```bash
docker --version
```

**예상 출력:**
```
Docker version 24.0.0, build abc123
```

**✗ 설치 안 되어 있다면:**
```bash
# Ubuntu
sudo apt-get update
sudo apt-get install docker.io -y
sudo usermod -aG docker $USER
newgrp docker
docker --version
```

#### ✅ Node.js 설치

```bash
node --version
npm --version
```

**예상 출력:**
```
v18.17.0
9.6.7
```

**✗ 설치 안 되어 있다면:**
```bash
# Ubuntu/WSL
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
node --version
```

#### ✅ Google Cloud SDK 설치

```bash
gcloud --version
```

**예상 출력:**
```
Google Cloud SDK 450.0.0
```

**✗ 설치 안 되어 있다면:**
```bash
# Ubuntu/WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

---

### 0-2. AWS 자격증명 설정

#### Step A: AWS Access Key 발급

1. **AWS Console 접속**: https://console.aws.amazon.com
2. **우측 상단 계정 클릭** → **"Security credentials"**
3. **"Access keys" 섹션** → **"Create access key"** 클릭
4. **Use case 선택**: "Command Line Interface (CLI)"
5. **"I understand..." 체크** → **"Next"**
6. **Description (선택)**: "Cloud Doctor MVP"
7. **"Create access key"** 클릭
8. **⚠️ 중요**: Access Key ID와 Secret Access Key를 **메모장에 저장**

**스크린샷 위치**: `docs/screenshots/01-aws-access-key.png`

#### Step B: AWS CLI 설정

```bash
aws configure
```

**입력 프롬프트 (각 줄마다 Enter):**
```
AWS Access Key ID [None]: AKIA...  ← 위에서 복사한 Access Key ID
AWS Secret Access Key [None]: wJalr...  ← 위에서 복사한 Secret Access Key
Default region name [None]: ap-northeast-2  ← 서울 리전
Default output format [None]: json  ← JSON 형식
```

#### Step C: 설정 확인

```bash
aws sts get-caller-identity
```

**예상 출력:**
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

**✅ 성공**: Account ID가 표시되면 성공
**✗ 실패**: `Unable to locate credentials` → Step A, B 다시 확인

---

### 0-3. GCP 프로젝트 설정

#### Step A: GCP Console에서 프로젝트 확인

1. **GCP Console 접속**: https://console.cloud.google.com
2. **상단 프로젝트 선택 드롭다운** 클릭
3. **현재 활성화된 프로젝트 ID 확인** (예: `my-project-12345`)

**스크린샷 위치**: `docs/screenshots/02-gcp-project-id.png`

#### Step B: 프로젝트 ID 환경변수 설정

```bash
export GCP_PROJECT_ID="your-project-id"  # 위에서 확인한 프로젝트 ID로 변경
echo $GCP_PROJECT_ID  # 확인
```

**예상 출력:**
```
your-project-id
```

#### Step C: gcloud CLI 인증

```bash
gcloud auth login
```

**동작:**
- 브라우저가 열리면서 Google 로그인 화면 표시
- 계정 선택 → "Allow" 클릭

**예상 출력:**
```
You are now logged in as [your-email@gmail.com]
```

#### Step D: gcloud 프로젝트 설정

```bash
gcloud config set project $GCP_PROJECT_ID
```

**예상 출력:**
```
Updated property [core/project].
```

#### Step E: 필요한 GCP API 활성화

```bash
gcloud services enable aiplatform.googleapis.com  # Vertex AI
gcloud services enable run.googleapis.com         # Cloud Run
gcloud services enable artifactregistry.googleapis.com  # Artifact Registry
```

**예상 출력 (각 API마다):**
```
Operation "operations/acat..." finished successfully.
```

**⏱️ 소요 시간**: 각 API당 10-20초

---

### 0-4. API 키 발급

#### Option A: GCP 크레딧 사용 (Vertex AI) ✅ **권장**

**장점:**
- ✅ GCP 크레딧 사용 가능
- ✅ 프로덕션급 안정성
- ✅ 높은 요청 한도

**필요한 것:**
- GCP 프로젝트 ID (위에서 설정 완료)
- Vertex AI API 활성화 (위에서 완료)

**별도 API Key 불필요!** GCP Application Default Credentials 사용

```bash
# 로컬 테스트용 Application Default Credentials 설정
gcloud auth application-default login
```

**브라우저에서 인증 → 완료**

#### Option B: Google AI Studio (무료) ⚠️ **테스트용**

**장점:**
- 간단한 설정
- 무료 (월 1500 요청)

**단점:**
- GCP 크레딧 사용 불가
- 프로덕션 부적합

**발급 방법:**
1. https://aistudio.google.com/app/apikey 접속
2. "Create API Key" 클릭
3. 프로젝트 선택
4. API Key 복사 (예: `AIzaSy...`)

```bash
export GEMINI_API_KEY="AIzaSy..."  # AI Studio 사용 시에만
```

#### ✅ Claude API Key 발급 (필수)

1. https://console.anthropic.com/ 접속
2. 계정 생성 (신용카드 등록 필요, $5 무료 크레딧 제공)
3. "API Keys" → "Create Key" 클릭
4. Name: "Cloud Doctor"
5. **API Key 복사** (예: `sk-ant-api03-...`)

```bash
export CLAUDE_API_KEY="sk-ant-api03-..."
```

#### ⚠️ Slack Webhook URL (선택사항)

**필요하다면:**
1. https://api.slack.com/messaging/webhooks 접속
2. "Create your Slack app" 클릭
3. Workspace 선택 → 채널 지정
4. Webhook URL 복사 (예: `https://hooks.slack.com/services/T.../B.../xyz`)

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

**필요 없다면 건너뛰어도 됨!** (Slack 알림만 안 됨)

---

### 0-5. 환경변수 영구 저장 (선택)

매번 export 하기 귀찮다면 `~/.bashrc`에 추가:

```bash
vi ~/.bashrc
```

**맨 아래에 추가:**
```bash
# Cloud Doctor MVP
export GCP_PROJECT_ID="your-project-id"
export CLAUDE_API_KEY="sk-ant-api03-..."
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."  # 선택
```

**적용:**
```bash
source ~/.bashrc
```

---

## Step 1: AWS Patient Zone 인프라 구축 (20분)

### 1-1. 작업 디렉토리 이동

```bash
cd ~/workspace/cloud-doctor-mvp/terraform/patient-aws
pwd
```

**예상 출력:**
```
/home/selffish234/workspace/cloud-doctor-mvp/terraform/patient-aws
```

### 1-2. Terraform 변수 파일 생성

```bash
cp terraform.tfvars.example terraform.tfvars
ls -la terraform.tfvars
```

**예상 출력:**
```
-rw-r--r-- 1 user user 456 Dec 10 14:30 terraform.tfvars
```

### 1-3. 변수 파일 편집

```bash
vi terraform.tfvars
```

**또는 VS Code 사용:**
```bash
code terraform.tfvars
```

**필수 변경 항목 (3개):**

```hcl
# 1. 데이터베이스 비밀번호 (8자 이상, 특수문자 포함 권장)
db_password = "MySecurePassword123!"

# 2. JWT 비밀키 (32자 이상 권장, 랜덤 문자열)
jwt_secret = "my-super-secret-jwt-key-change-this-to-random-string"

# 3. S3 버킷명 (전역 고유해야 함! 본인 이름이나 날짜 추가)
frontend_bucket_name = "cloud-doctor-patient-frontend-yourname-20241210"
```

**💡 Tip: 랜덤 문자열 생성**
```bash
# JWT 비밀키 생성
openssl rand -base64 32

# 출력 예: xK8Pq2mZ...
```

**✅ 저장 확인:**
```bash
cat terraform.tfvars | grep -E "db_password|jwt_secret|frontend_bucket_name"
```

**예상 출력:**
```
db_password = "MySecurePassword123!"
jwt_secret = "xK8Pq2mZ..."
frontend_bucket_name = "cloud-doctor-patient-frontend-yourname-20241210"
```

### 1-4. Terraform 초기화

```bash
terraform init
```

**예상 출력:**
```
Initializing the backend...
Initializing modules...
- network in modules/network
- database in modules/database
- app_cluster in modules/app_cluster
- static_site in modules/static_site

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.30.0...
- Installed hashicorp/aws v5.30.0

Terraform has been successfully initialized!
```

**✅ 성공 표시**: `Terraform has been successfully initialized!`
**✗ 실패**: `Error: ...` → 오류 메시지 확인 후 수정

### 1-5. 실행 계획 확인 (DRY RUN)

```bash
terraform plan
```

**예상 출력 (중요 부분):**
```
Terraform will perform the following actions:

  # module.network.aws_vpc.this will be created
  + resource "aws_vpc" "this" {
      + cidr_block           = "10.0.0.0/16"
      ...
    }

  # module.database.aws_db_instance.this will be created
  + resource "aws_db_instance" "this" {
      + engine               = "mysql"
      + engine_version       = "8.0"
      ...
    }

  # 총 약 50-52개 리소스

Plan: 52 to add, 0 to change, 0 to destroy.
```

**✅ 확인 사항:**
- `Plan: XX to add, 0 to change, 0 to destroy` 표시되면 OK
- 예상 리소스 개수: **50-52개**

**⚠️ 오류 발생 시:**

**오류 1: S3 bucket already exists**
```
Error: creating S3 Bucket (cloud-doctor-patient-frontend): BucketAlreadyExists
```
**해결:** `terraform.tfvars`의 `frontend_bucket_name`을 다른 이름으로 변경

**오류 2: Invalid credentials**
```
Error: error configuring Terraform AWS Provider: no valid credentials sources found
```
**해결:** Step 0-2 AWS 자격증명 다시 확인

### 1-6. 인프라 생성 실행

```bash
terraform apply
```

**프롬프트:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
```

**"yes" 입력 후 Enter**

**⏱️ 소요 시간: 약 12-15분**

**진행 상황 (실시간 출력):**
```
module.network.aws_vpc.this: Creating...
module.network.aws_vpc.this: Creation complete after 2s
module.network.aws_internet_gateway.this: Creating...
module.network.aws_subnet.public[0]: Creating...
...
module.database.aws_db_instance.this: Still creating... [5m0s elapsed]
module.database.aws_db_instance.this: Still creating... [10m0s elapsed]
module.database.aws_db_instance.this: Creation complete after 12m34s
...

Apply complete! Resources: 52 added, 0 changed, 0 destroyed.

Outputs:

alb_dns_name = "patient-zone-alb-1234567890.ap-northeast-2.elb.amazonaws.com"
cloudfront_url = "https://d1234567890abc.cloudfront.net"
db_endpoint = <sensitive>
ecr_repository_url = "123456789.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend"
ecs_cluster_name = "patient-zone-cluster"
ecs_service_name = "patient-zone-service"
s3_bucket_name = "cloud-doctor-patient-frontend-yourname-20241210"
cloudfront_distribution_id = "E12345ABCDEF"

deployment_instructions = <<EOT
...
(배포 가이드 출력)
...
EOT
```

**✅ 성공 표시**: `Apply complete! Resources: 52 added`

**스크린샷 위치**: `docs/screenshots/03-terraform-apply-success.png`

### 1-7. 출력값 저장 (매우 중요!)

```bash
# 환경변수로 저장 (다음 단계에서 사용)
export ALB_URL=$(terraform output -raw alb_dns_name)
export ECR_BACKEND=$(terraform output -raw ecr_repository_url)
export S3_BUCKET=$(terraform output -raw s3_bucket_name)
export CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
export CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)
export ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
export ECS_SERVICE=$(terraform output -raw ecs_service_name)

# 확인
echo "ALB URL: $ALB_URL"
echo "ECR: $ECR_BACKEND"
echo "S3: $S3_BUCKET"
echo "CloudFront: $CLOUDFRONT_URL"
```

**예상 출력:**
```
ALB URL: patient-zone-alb-1234567890.ap-northeast-2.elb.amazonaws.com
ECR: 123456789.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend
S3: cloud-doctor-patient-frontend-yourname-20241210
CloudFront: https://d1234567890abc.cloudfront.net
```

**💡 Tip: 나중에 다시 사용하려면**
```bash
# 저장
terraform output > ~/terraform-outputs.txt
cat ~/terraform-outputs.txt
```

---

## Step 2: Patient Zone 애플리케이션 배포 (25분)

### 2-1. Backend 배포 준비

#### Step A: 작업 디렉토리 이동

```bash
cd ~/workspace/cloud-doctor-mvp/patient-aws/backend
pwd
ls -la
```

**예상 출력:**
```
/home/selffish234/workspace/cloud-doctor-mvp/patient-aws/backend
total 32
drwxr-xr-x 4 user user 4096 Dec 10 14:00 .
-rw-r--r-- 1 user user 1234 Dec 10 14:00 Dockerfile
-rw-r--r-- 1 user user  567 Dec 10 14:00 package.json
drwxr-xr-x 5 user user 4096 Dec 10 14:00 src
```

#### Step B: ECR 로그인

```bash
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin $ECR_BACKEND
```

**예상 출력:**
```
WARNING! Your password will be stored unencrypted in /home/user/.docker/config.json.
Configure a credential helper to remove this warning.

Login Succeeded
```

**✅ 성공**: `Login Succeeded`
**✗ 실패**: `Error response from daemon: Get https://...` → AWS 자격증명 확인

### 2-2. Docker 이미지 빌드

```bash
docker build -t $ECR_BACKEND:latest .
```

**예상 출력 (약 3-5분 소요):**
```
[+] Building 234.5s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [1/6] FROM docker.io/library/node:18-alpine
 => [2/6] WORKDIR /app
 => [3/6] COPY package*.json ./
 => [4/6] RUN npm ci --only=production
 => [5/6] COPY --chown=nodejs:nodejs . .
 => [6/6] USER nodejs
 => exporting to image
 => => writing image sha256:abc123...
 => => naming to 123456789.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend:latest
```

**✅ 성공**: `naming to ...backend:latest`
**⏱️ 소요 시간**: 첫 빌드 3-5분, 이후 1분 이내

**확인:**
```bash
docker images | grep patient-zone-backend
```

**예상 출력:**
```
123456789.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend   latest   abc123def456   2 minutes ago   150MB
```

### 2-3. ECR에 이미지 푸시

```bash
docker push $ECR_BACKEND:latest
```

**예상 출력 (약 2-3분 소요):**
```
The push refers to repository [123456789.dkr.ecr.ap-northeast-2.amazonaws.com/patient-zone-backend]
abc123: Pushed
def456: Pushed
...
latest: digest: sha256:abcdef123456... size: 2345
```

**✅ 성공**: `latest: digest: sha256:...`

**확인 (AWS Console에서):**
1. ECR Console: https://console.aws.amazon.com/ecr
2. Repositories → `patient-zone-backend` 클릭
3. Images 탭 → `latest` 태그 확인

**스크린샷 위치**: `docs/screenshots/04-ecr-image-pushed.png`

### 2-4. ECS 서비스 업데이트 (새 이미지 배포)

```bash
aws ecs update-service \
  --cluster $ECS_CLUSTER \
  --service $ECS_SERVICE \
  --force-new-deployment \
  --region ap-northeast-2
```

**예상 출력:**
```json
{
    "service": {
        "serviceName": "patient-zone-service",
        "clusterArn": "arn:aws:ecs:ap-northeast-2:123456789:cluster/patient-zone-cluster",
        "status": "ACTIVE",
        "desiredCount": 2,
        "runningCount": 2,
        ...
    }
}
```

**✅ 성공**: `"status": "ACTIVE"`

### 2-5. 배포 상태 확인 (2-3분 대기)

```bash
# 실시간 상태 확인 (30초마다 자동 새로고침)
watch -n 30 'aws ecs describe-services \
  --cluster $ECS_CLUSTER \
  --services $ECS_SERVICE \
  --region ap-northeast-2 \
  --query "services[0].deployments[*].[id,status,runningCount,desiredCount]" \
  --output table'
```

**예상 출력 (초기):**
```
---------------------------------------------
|           DescribeServices              |
+------------------+---------+-----+------+
|  deployment-id   | PRIMARY |  1  |  2   |
|  deployment-id   | ACTIVE  |  1  |  0   |  ← 이전 버전 종료 중
+------------------+---------+-----+------+
```

**예상 출력 (완료):**
```
---------------------------------------------
|           DescribeServices              |
+------------------+---------+-----+------+
|  deployment-id   | PRIMARY |  2  |  2   |  ← 새 버전 2개 실행 중
+------------------+---------+-----+------+
```

**✅ 완료 조건**: `runningCount = desiredCount = 2`

**Ctrl+C로 종료**

### 2-6. Backend Health Check

```bash
curl http://$ALB_URL/health
```

**예상 출력:**
```json
{
  "status": "ok",
  "database": {
    "connected": true
  },
  "memory": {
    "used": "45.67MB"
  },
  "timestamp": "2024-12-10T14:45:23.456Z"
}
```

**✅ 성공**: `"status": "ok"`, `"connected": true`
**✗ 실패**:
- `Connection refused` → ECS 태스크가 아직 시작 안 됨 (1분 후 재시도)
- `Service Unavailable` → DB 연결 실패 (환경변수 확인)

**스크린샷 위치**: `docs/screenshots/05-backend-health-check.png`

---

### 2-7. Frontend 배포

#### Step A: 작업 디렉토리 이동

```bash
cd ~/workspace/cloud-doctor-mvp/patient-aws/frontend
pwd
```

**예상 출력:**
```
/home/selffish234/workspace/cloud-doctor-mvp/patient-aws/frontend
```

#### Step B: 의존성 설치

```bash
npm install
```

**⏱️ 소요 시간**: 약 2-3분

**예상 출력:**
```
added 234 packages in 2m

5 packages are looking for funding
  run `npm fund` for details
```

#### Step C: 프로덕션 빌드

```bash
npm run build
```

**💡 참고**: API_URL은 빈 문자열(`''`)로 설정되어 있어, CloudFront가 `/api/*` 경로를 ALB로 자동 프록시합니다. 이 방식으로 Mixed Content 보안 오류를 방지합니다.

**⏱️ 소요 시간**: 약 1-2분

**예상 출력:**
```
   ▲ Next.js 16.0.3
   - Environments: .env.local

   Creating an optimized production build ...
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (5/5)
✓ Collecting build traces
✓ Finalizing page optimization

Route (app)                              Size     First Load JS
┌ ○ /                                    1.2 kB         80 kB
├ ○ /login                               2.3 kB         82 kB
├ ○ /posts                               3.4 kB         83 kB
└ ○ /posts/new                           2.1 kB         82 kB

○  (Static)  prerendered as static content

Export successful. Files written to /home/.../out
```

**✅ 성공**: `Export successful`

**확인:**
```bash
ls -la out/
```

**예상 출력:**
```
drwxr-xr-x  6 user user 4096 Dec 10 15:00 out
-rw-r--r--  1 user user 5678 Dec 10 15:00 out/index.html
drwxr-xr-x  2 user user 4096 Dec 10 15:00 out/_next
```

#### Step D: S3에 업로드

```bash
aws s3 sync out/ s3://$S3_BUCKET/ --delete
```

**예상 출력:**
```
upload: out/index.html to s3://cloud-doctor-patient-frontend-yourname-20241210/index.html
upload: out/_next/static/chunks/123.js to s3://...
upload: out/_next/static/css/456.css to s3://...
...
```

**✅ 성공**: 여러 파일이 `upload:` 로 표시됨

**확인:**
```bash
aws s3 ls s3://$S3_BUCKET/ --recursive
```

#### Step E: CloudFront 캐시 무효화

```bash
aws cloudfront create-invalidation \
  --distribution-id $CLOUDFRONT_ID \
  --paths "/*"
```

**예상 출력:**
```json
{
    "Location": "https://cloudfront.amazonaws.com/2020-05-31/distribution/E12345/invalidation/I2ABCDEF",
    "Invalidation": {
        "Id": "I2ABCDEF",
        "Status": "InProgress",
        "CreateTime": "2024-12-10T15:05:00Z",
        "InvalidationBatch": {
            "Paths": {
                "Quantity": 1,
                "Items": ["/*"]
            }
        }
    }
}
```

**✅ 성공**: `"Status": "InProgress"`

**⏱️ 캐시 무효화 완료**: 약 3-5분 소요

### 2-8. Frontend 접속 확인

```bash
echo "Frontend URL: $CLOUDFRONT_URL"
```

**예상 출력:**
```
Frontend URL: https://d1234567890abc.cloudfront.net
```

**브라우저에서 접속:**

1. **위 URL 복사 → 브라우저에 붙여넣기**
2. **홈페이지 표시 확인:**
   - 제목: "🩺 Cloud Doctor Patient Zone"
   - 시스템 구조 표시
   - "📝 게시판 바로가기" 버튼
   - "🔐 로그인 / 회원가입" 버튼

**스크린샷 위치**: `docs/screenshots/06-frontend-home.png`

#### 회원가입 테스트

1. **"🔐 로그인 / 회원가입" 클릭**
2. **하단 "계정이 없으신가요? 회원가입" 클릭**
3. **정보 입력:**
   - 이메일: `test@example.com`
   - 이름: `Test User`
   - 비밀번호: `test1234`
4. **"회원가입" 클릭**
5. **자동 로그인 → 게시판으로 이동**

**스크린샷 위치**: `docs/screenshots/07-frontend-signup.png`

#### 게시글 작성 테스트

1. **"글쓰기" 버튼 클릭**
2. **제목**: `Test Post`
3. **내용**: `Hello World from Cloud Doctor!`
4. **"게시글 등록" 클릭**
5. **게시판 목록에서 확인**

**스크린샷 위치**: `docs/screenshots/08-frontend-post-created.png`

**✅ Patient Zone 배포 완료!**

---

## Step 3: GCP Doctor Zone 배포 (20분)

### 3-1. GCP 프로젝트 설정 확인

```bash
echo $GCP_PROJECT_ID
```

**예상 출력:**
```
your-project-id
```

**✗ 비어 있다면:**
```bash
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID
```

### 3-2. 작업 디렉토리 이동

```bash
cd ~/workspace/cloud-doctor-mvp/doctor-gcp
pwd
ls -la
```

**예상 출력:**
```
/home/selffish234/workspace/cloud-doctor-mvp/doctor-gcp
total 64
-rw-r--r-- 1 user user  1234 Dec 10 14:00 Dockerfile
-rw-r--r-- 1 user user  5678 Dec 10 14:00 main_vertex.py
-rw-r--r-- 1 user user  3456 Dec 10 14:00 log_analyzer_vertex.py
...
```

### 3-3. 환경변수 준비

```bash
# GCP 관련 (이미 설정됨)
echo "GCP_PROJECT_ID: $GCP_PROJECT_ID"

# Claude API Key (Step 0-4에서 설정)
echo "CLAUDE_API_KEY: ${CLAUDE_API_KEY:0:10}..."  # 앞 10자만 표시

# Slack (선택) - ⚠️ 주의: URL 앞뒤에 < > 없이 설정!
echo "SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:0:30}..."  # 앞 30자만 표시

# AWS 자격증명 (CloudWatch Logs 조회용)
export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)

# CloudWatch Log Group 이름
export LOG_GROUP_NAME="/ecs/patient-zone"

# 확인
echo "AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "LOG_GROUP_NAME: $LOG_GROUP_NAME"
```

**예상 출력:**
```
GCP_PROJECT_ID: your-project-id
CLAUDE_API_KEY: sk-ant-api...
SLACK_WEBHOOK_URL: https://hooks.slack.com/servic...
AWS_ACCESS_KEY_ID: AKIA...
LOG_GROUP_NAME: /ecs/patient-zone
```

### 3-4. GCP Application Default Credentials 설정

```bash
gcloud auth application-default login
```

**동작:**
- 브라우저가 열림
- 계정 선택 → "Allow" 클릭

**예상 출력:**
```
Credentials saved to file: [/home/user/.config/gcloud/application_default_credentials.json]

These credentials will be used by any library that requests Application Default Credentials (ADC).
```

**✅ 성공**: `Credentials saved to file`

### 3-5. 자동 배포 스크립트 실행

**💡 참고:** Dockerfile은 이미 올바르게 설정되어 있습니다 (`COPY *.py .`로 모든 Python 파일 자동 복사). 별도 수정 불필요!

```bash
chmod +x deploy.sh
./deploy.sh
```

**⏱️ 소요 시간**: 약 10-15분

**💡 중요:**
- **Cloud Run 리전**: asia-northeast3 (서울) - 서버 배포 위치
- **Vertex AI 리전**: us-central1 (자동 설정됨) - Gemini 2.0 Flash 모델 사용

**예상 출력 (단계별):**

**1단계: 환경 확인**
```
========================================
Cloud Doctor - Doctor Zone Deployment
========================================

Checking prerequisites...
✓ GCP Project: your-project-id
✓ Region: asia-northeast3
✓ Service: doctor-zone
✓ All required variables set
```

**2단계: Artifact Registry 설정**
```
Setting up Artifact Registry...
✓ Repository already exists
Configuring Docker authentication...
✓ Docker authenticated
```

**3단계: Docker 빌드**
```
Building Docker image...
[+] Building 123.4s (15/15) FINISHED
...
✓ Image built successfully
```

**4단계: 이미지 푸시**
```
Pushing image to Artifact Registry...
The push refers to repository [asia-northeast3-docker.pkg.dev/your-project-id/cloud-doctor/doctor-zone]
abc123: Pushed
...
✓ Image pushed successfully
```

**5단계: Cloud Run 배포**
```
Deploying to Cloud Run...
Deploying container to Cloud Run service [doctor-zone] in project [your-project-id] region [asia-northeast3]
✓ Deploying new service... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [doctor-zone] revision [doctor-zone-00001-abc] has been deployed and is serving 100 percent of traffic.
✓ Deployment successful
```

**6단계: 헬스 체크**
```
Testing deployment...
✓ Health check passed
```

**최종 출력:**
```
========================================
Deployment Complete!
========================================

Service URL: https://doctor-zone-abc123-an.a.run.app

Test endpoints:
  Health Check:  https://doctor-zone-abc123-an.a.run.app/health
  Analyze Logs:  https://doctor-zone-abc123-an.a.run.app/analyze
  Test Slack:    https://doctor-zone-abc123-an.a.run.app/slack/test

Example usage:
  curl -X POST https://doctor-zone-abc123-an.a.run.app/analyze \
    -H 'Content-Type: application/json' \
    -d '{"time_range_minutes":30,"generate_terraform":true}'

========================================
```

**✅ 성공**: `Deployment Complete!`

### 3-7. Doctor Zone URL 저장

```bash
export DOCTOR_URL=$(gcloud run services describe doctor-zone \
  --region asia-northeast3 \
  --format 'value(status.url)')

echo "Doctor Zone URL: $DOCTOR_URL"
```

**예상 출력:**
```
Doctor Zone URL: https://doctor-zone-abc123-an.a.run.app
```

### 3-8. Health Check

```bash
curl $DOCTOR_URL/health
```

**예상 출력:**
```json
{
  "status": "ok"
}
```

**더 자세한 정보:**
```bash
curl $DOCTOR_URL/
```

**예상 출력:**
```json
{
  "service": "Cloud Doctor Enhanced (Vertex AI)",
  "status": "healthy",
  "timestamp": "2024-12-10T15:30:00.123Z",
  "version": "2.1.0",
  "features": {
    "log_analysis": "Vertex AI Gemini 2.0 Flash",
    "terraform_generation": "Claude Sonnet 4.5",
    "slack_notifications": true,
    "uses_gcp_credits": true
  }
}
```

**✅ 성공 확인:**
- `"log_analysis": "Vertex AI Gemini 2.0 Flash"` ← Gemini 2.0 사용!
- `"uses_gcp_credits": true` ← GCP 크레딧 사용 중!

**스크린샷 위치**: `docs/screenshots/09-doctor-zone-deployed.png`

---

## Step 4: 전체 시스템 테스트 (15분)

### 4-1. Slack 연동 테스트 (선택)

**Slack Webhook을 설정했다면:**

```bash
curl -X POST $DOCTOR_URL/slack/test
```

**예상 출력:**
```json
{
  "status": "success",
  "message": "Test message sent to Slack"
}
```

**Slack 채널 확인:**
```
✅ Slack 연동 테스트

이 메시지가 보인다면, Slack Webhook이 정상 작동합니다!

다음 단계:
1. Doctor Zone이 CloudWatch Logs를 모니터링합니다
2. Gemini AI가 장애 로그를 분석합니다
3. Claude AI가 Terraform 수정 코드를 생성합니다
4. 알림이 이 채널로 전송됩니다
```

**스크린샷 위치**: `docs/screenshots/10-slack-test-message.png`

### 4-2. 장애 시나리오 트리거

#### Scenario 1: Slow Query (N+1 문제)

```bash
curl -X POST http://$ALB_URL/api/chaos/slow-query
```

**예상 출력:**
```json
{
  "scenario": "slow-query",
  "status": "triggered",
  "message": "N+1 query scenario activated. Check CloudWatch Logs in 1 minute.",
  "logs_will_appear_in": "60 seconds"
}
```

**1분 대기...**

#### Scenario 2: Memory Leak

```bash
curl -X POST http://$ALB_URL/api/chaos/memory-leak
```

**예상 출력:**
```json
{
  "scenario": "memory-leak",
  "status": "triggered",
  "message": "Memory leak scenario activated...",
  "duration_seconds": 60
}
```

#### Scenario 3: DB Connection Failure

```bash
curl -X POST http://$ALB_URL/api/chaos/db-fail
```

**예상 출력:**
```json
{
  "scenario": "db-failure",
  "status": "triggered",
  "message": "Database connection failure simulated..."
}
```

### 4-3. CloudWatch Logs 확인

```bash
# 실시간 로그 스트리밍 (Ctrl+C로 종료)
aws logs tail /ecs/patient-zone --follow
```

**예상 출력 (Slow Query):**
```
2024-12-10T15:35:12.345Z [SLOW QUERY] Fetching author for post 1
2024-12-10T15:35:12.456Z [SLOW QUERY] Fetching author for post 2
2024-12-10T15:35:12.567Z [SLOW QUERY] Fetching author for post 3
...
2024-12-10T15:35:15.123Z [PERFORMANCE] N+1 query detected: 50 posts = 50 DB queries
```

**예상 출력 (Memory Leak):**
```
2024-12-10T15:36:10.123Z [MEMORY MONITOR] Heap: 125MB / 512MB (24%)
2024-12-10T15:36:20.234Z [MEMORY MONITOR] Heap: 250MB / 512MB (48%)
2024-12-10T15:36:30.345Z [MEMORY MONITOR] Heap: 375MB / 512MB (73%)
2024-12-10T15:36:40.456Z [MEMORY CRITICAL] Heap usage exceeds 90% - OOM risk
```

**스크린샷 위치**: `docs/screenshots/11-cloudwatch-logs-errors.png`

### 4-4. Doctor Zone 로그 분석 실행

```bash
curl -X POST $DOCTOR_URL/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "time_range_minutes": 30,
    "max_logs": 100,
    "generate_terraform": true,
    "send_to_slack": true
  }'
```

**⏱️ 소요 시간**: 약 15-30초

**예상 출력 (긴 JSON 응답):**
```json
{
  "status": "success",
  "timestamp": "2024-12-10T15:37:00.123Z",
  "summary": {
    "total_logs_analyzed": 1,
    "time_range_minutes": 30,
    "log_group": "/ecs/patient-zone",
    "ai_engine": "Vertex AI Gemini 2.0 Flash"
  },
  "analysis": {
    "detected_issues": [
      "slow-query"
    ],
    "severity": "warning",
    "summary": "N+1 쿼리 문제가 백엔드 애플리케이션에서 감지되었습니다. 성능 저하를 유발하고 있습니다.",
    "recommendations": [
      "백엔드 로그에서 느린 쿼리를 식별하세요",
      "EXPLAIN을 사용하여 쿼리 실행 계획을 분석하고 누락된 인덱스나 비효율적인 조인을 찾으세요",
      "RDS MySQL 테이블에 적절한 인덱스를 추가하여 쿼리를 최적화하세요",
      "N+1 쿼리 패턴을 피하도록 코드를 리팩토링하세요 (배칭 또는 eager loading 기법 사용)"
    ],
    "affected_resources": [
      "ECS Task: (ECS 로그에서 특정 태스크 ID 확인)",
      "RDS Instance: (RDS 로그에서 특정 인스턴스 이름 확인)"
    ]
  },
  "terraform": {
    "terraform_code": "# RDS 성능 최적화를 위한 변수\nvariable \"rds_performance_insights_enabled\" {\n  description = \"Enable Performance Insights for RDS\"\n  type        = bool\n  default     = true\n}\n\n# RDS Parameter Group for MySQL optimization\nresource \"aws_db_parameter_group\" \"patient_zone_mysql_params\" {\n  family = \"mysql8.0\"\n  name   = \"patient-zone-mysql-performance\"\n\n  parameter {\n    name  = \"slow_query_log\"\n    value = \"1\"\n  }\n\n  parameter {\n    name  = \"long_query_time\"\n    value = \"1\"\n  }\n  ...\n}",
    "explanation": "이 코드는 N+1 쿼리 성능 문제를 해결하기 위해 포괄적인 데이터베이스 모니터링과 쿼리 최적화를 구현합니다: 1. **Performance Insights**: AWS RDS Performance Insights를 활성화하여 느린 쿼리와 N+1 쿼리 패턴을 실시간으로 식별 2. **Slow Query Logging**: 1초 이상 걸리는 쿼리와 인덱스를 사용하지 않는 쿼리를 로깅하도록 MySQL 설정 3. **Enhanced Monitoring**: 60초 단위로 상세한 데이터베이스 메트릭 제공 4. **Query Cache Optimization**: 반복되는 쿼리의 성능을 향상시키기 위해 쿼리 캐시 크기 증가",
    "apply_instructions": [
      "생성된 Terraform 코드 검토",
      "terraform 디렉터리에 .tf 파일로 저장",
      "terraform plan을 실행하여 변경사항 확인",
      "적용 전 현재 태스크 정의 백업",
      "terraform apply로 적용",
      "배포 중 ECS 서비스 모니터링"
    ]
  },
  "slack_sent": true
}
```

**✅ 성공 확인:**
- `"status": "success"` - 분석 성공
- `"ai_engine": "Vertex AI Gemini 2.0 Flash"` - Gemini 2.0 사용
- `"detected_issues": ["slow-query"]` - 문제 감지됨
- `"summary"`: 한국어로 요약
- `"recommendations"`: 한국어로 권장사항
- `"explanation"`: 한국어로 설명
- `"slack_sent": true` - Slack 알림 전송 성공 (Slack 설정 시)

**스크린샷 위치**: `docs/screenshots/12-analysis-result.png`

### 4-5. Slack 알림 확인 (Webhook 설정한 경우)

**Slack 채널에서 다음과 같은 메시지 확인:**

```
⚠️ Cloud Doctor 알림 - 경고

요약
N+1 쿼리 문제가 백엔드 애플리케이션에서 감지되었습니다. 성능 저하를 유발하고 있습니다.

감지된 문제
• slow-query

영향받은 리소스
• ECS Task: arn:aws:ecs:...
• RDS Instance: patient-zone-mysql

권장사항
1. 백엔드 로그에서 느린 쿼리를 식별하세요
2. EXPLAIN을 사용하여 쿼리 실행 계획을 분석하세요
3. RDS MySQL 테이블에 적절한 인덱스를 추가하세요
4. N+1 쿼리 패턴을 피하도록 코드를 리팩토링하세요 (배칭 또는 eager loading 사용)

──────────────────────────────────

🔧 Terraform 수정 코드 생성됨

설명
이 코드는 N+1 쿼리 성능 문제를 해결하기 위해 포괄적인 데이터베이스 모니터링과 쿼리 최적화를 구현합니다:
1. RDS Performance Insights를 활성화하여 느린 쿼리와 N+1 쿼리 패턴을 실시간으로 식별
2. 1초 이상 걸리는 쿼리와 인덱스를 사용하지 않는 쿼리를 로깅하도록 MySQL 설정
3. 60초 단위로 상세한 데이터베이스 메트릭을 제공하는 Enhanced Monitoring 활성화
...

Terraform 코드
```hcl
resource "aws_db_parameter_group" "patient_zone_mysql_params" {
  family = "mysql8.0"
  name   = "patient-zone-mysql-performance"

  parameter {
    name  = "slow_query_log"
    value = "1"
  }
  ...
}
```
(축약됨 - 전체 코드는 API 응답 확인)

적용 방법
1. Backup Current Configuration
2. Plan the Changes
3. Apply in Stages
...

──────────────────────────────────
🩺 Cloud Doctor MVP | Powered by Gemini + Claude
```

**스크린샷 위치**: `docs/screenshots/13-slack-alert-with-terraform.png`

**✅ 전체 시스템 테스트 완료!**

---

## Step 5: 리소스 정리 (10분)

**⚠️ 중요: 테스트 완료 후 비용 절감을 위해 리소스를 정리하세요!**

### 5-1. Doctor Zone 삭제 (GCP)

```bash
# Cloud Run 서비스 삭제
gcloud run services delete doctor-zone \
  --region asia-northeast3 \
  --quiet
```

**예상 출력:**
```
Deleting [doctor-zone]...done.
Deleted service [doctor-zone].
```

### 5-2. Docker 이미지 삭제 (GCP)

```bash
gcloud artifacts docker images delete \
  asia-northeast3-docker.pkg.dev/$GCP_PROJECT_ID/cloud-doctor/doctor-zone:latest \
  --quiet
```

**예상 출력:**
```
Deleted [asia-northeast3-docker.pkg.dev/your-project-id/cloud-doctor/doctor-zone:latest].
```

### 5-3. Patient Zone 삭제 (AWS)

#### Step A: S3 버킷 비우기 (필수!)

```bash
# CloudFront OAC 때문에 terraform destroy 전에 수동 삭제 필요
aws s3 rm s3://$S3_BUCKET --recursive
```

**예상 출력:**
```
delete: s3://cloud-doctor-patient-frontend-yourname-20241210/index.html
delete: s3://cloud-doctor-patient-frontend-yourname-20241210/_next/...
...
```

#### Step B: ECR 이미지 삭제

```bash
aws ecr batch-delete-image \
  --repository-name patient-zone-backend \
  --image-ids imageTag=latest \
  --region ap-northeast-2
```

**예상 출력:**
```json
{
    "imageIds": [
        {
            "imageDigest": "sha256:abc123...",
            "imageTag": "latest"
        }
    ],
    "failures": []
}
```

#### Step C: Terraform destroy

```bash
cd ~/workspace/cloud-doctor-mvp/terraform/patient-aws

terraform destroy
```

**프롬프트:**
```
Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value:
```

**"yes" 입력 후 Enter**

**⏱️ 소요 시간**: 약 10-12분 (RDS 삭제가 가장 오래 걸림)

**예상 출력:**
```
module.static_site.aws_cloudfront_distribution.frontend: Destroying...
module.app_cluster.aws_ecs_service.this: Destroying...
module.database.aws_db_instance.this: Destroying...
...
module.database.aws_db_instance.this: Still destroying... [5m0s elapsed]
module.database.aws_db_instance.this: Still destroying... [10m0s elapsed]
module.database.aws_db_instance.this: Destruction complete after 10m34s
...

Destroy complete! Resources: 52 destroyed.
```

**✅ 성공**: `Destroy complete! Resources: 52 destroyed`

### 5-4. 최종 확인

```bash
# ECS 클러스터 확인 (비어있어야 함)
aws ecs list-clusters --region ap-northeast-2

# S3 버킷 확인 (비어있어야 함)
aws s3 ls | grep cloud-doctor

# CloudFront 배포 확인 (비어있어야 함)
aws cloudfront list-distributions --query 'DistributionList.Items[*].Aliases.Items' --output text
```

**예상 출력 (모두 비어있거나 해당 리소스 없음):**
```
{
    "clusterArns": []
}
```

**✅ 정리 완료!**

---

## 🎯 트러블슈팅

### 문제 1: `terraform apply` 실패 - S3 bucket already exists

**오류:**
```
Error: creating S3 Bucket (cloud-doctor-patient-frontend): BucketAlreadyExists
```

**원인:** S3 버킷명이 전역적으로 중복됨

**해결:**
```bash
vi terraform.tfvars
# frontend_bucket_name을 고유한 이름으로 변경
# 예: cloud-doctor-patient-frontend-yourname-20241210-v2

terraform apply
```

### 문제 2: ECS 태스크가 계속 재시작됨

**증상:**
```bash
aws ecs describe-services --cluster patient-zone-cluster --services patient-zone-service
# desiredCount: 2, runningCount: 0
```

**확인:**
```bash
# ECS 태스크 로그 확인
aws logs tail /ecs/patient-zone --follow
```

**자주 발생하는 오류:**

**A) DB 연결 실패**
```
Error: SequelizeConnectionError: connect ETIMEDOUT
```
**해결:** RDS 엔드포인트가 정확한지 확인, Security Group 확인

**B) ECR 이미지 없음**
```
Error: CannotPullContainerError
```
**해결:** Step 2-3 ECR 푸시 다시 실행

**C) 메모리 부족**
```
Error: OutOfMemoryError
```
**해결:** Task Definition의 memory를 1024로 증가

### 문제 3: Frontend에서 Backend API 호출 실패

**증상:** 브라우저 콘솔에 `CORS error` 또는 `Network Error`

**확인:**
```bash
# ALB URL 확인
echo $ALB_URL

# Health check 테스트
curl http://$ALB_URL/health
```

**해결:**
1. ALB URL이 올바른지 확인
2. Frontend 재빌드:
```bash
cd ~/workspace/cloud-doctor-mvp/patient-aws/frontend
npm run build
aws s3 sync out/ s3://$S3_BUCKET/ --delete
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_ID --paths "/*"
```

**참고**: API_URL은 빈 문자열로 설정되어 CloudFront가 자동 프록시합니다.

### 문제 4: Doctor Zone에서 "GCP credentials not found"

**오류:**
```
Error: DefaultCredentialsError: Could not automatically determine credentials.
```

**해결:**
```bash
# Application Default Credentials 재설정
gcloud auth application-default login

# Doctor Zone 재배포
cd ~/workspace/cloud-doctor-mvp/doctor-gcp
./deploy.sh
```

### 문제 5: CloudWatch Logs에 아무것도 없음

**확인:**
```bash
# Log Group 존재 확인
aws logs describe-log-groups --log-group-name-prefix /ecs/patient-zone

# ECS 태스크가 실행 중인지 확인
aws ecs list-tasks --cluster patient-zone-cluster
```

**해결:**
- ECS 태스크가 실행 중이 아니면 Step 2-4 다시 확인
- Log Group이 없으면 Terraform 출력 확인

---

## 📝 다음 단계

1. **포트폴리오 문서 작성** → `ARCHITECTURE.md`, `IMPLEMENTATION.md` 작성
2. **다이어그램 제작** → draw.io로 아키텍처 다이어그램 그리기
3. **스크린샷 정리** → `docs/screenshots/` 폴더에 캡처 이미지 저장
4. **GitHub 업로드** → 전체 프로젝트를 GitHub에 푸시

**메가존클라우드 지원 화이팅!** 🚀
