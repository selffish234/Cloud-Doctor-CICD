# Cloud Doctor MVP - 웹 콘솔(GUI) 완전 정복 가이드

이 가이드는 **터미널 명령어(CLI)를 최소화**하고, 대부분의 작업을 **AWS 및 GCP 웹 콘솔(마우스 클릭)**으로 수행하여 전체 시스템을 구축하는 방법을 설명합니다.

**포함된 내용**:
- AWS: VPC, RDS, ECS, ALB(HTTPS), **Client VPN**, **Route 53(도메인)**
- GCP: Cloud Run, Artifact Registry
- DevOps: GitHub Actions 연동을 위한 IAM 설정

---

## 📋 목차
1. [Step 1: AWS 네트워크(VPC) 구성](#step-1-aws-네트워크vpc-구성)
2. [Step 2: 보안 인증서(SSL) 및 도메인 준비](#step-2-보안-인증서ssl-및-도메인-준비)
3. [Step 3: 데이터베이스(RDS) 생성](#step-3-데이터베이스rds-생성)
4. [Step 4: 보안 접속(Client VPN) 설정](#step-4-보안-접속client-vpn-설정)
5. [Step 5: 백엔드 서버(ECS) 배포](#step-5-백엔드-서버ecs-배포)
6. [Step 6: 로드밸런서(ALB) 및 도메인 연결](#step-6-로드밸런서alb-및-도메인-연결)
7. [Step 7: 프론트엔드 배포(S3+CloudFront)](#step-7-프론트엔드-배포s3cloudfront)
8. [Step 8: GCP 의사(Cloud Run) 배포](#step-8-gcp-의사cloud-run-배포)

---

## Step 1: AWS 네트워크(VPC) 구성

### 1-1. VPC 생성
1. AWS 콘솔 상단 검색창에 **VPC** 검색 > **VPC** 대시보드로 이동.
2. **"Create VPC"** 버튼 클릭.
3. **VPC settings**:
   - Resources to create: **VPC and more** (이 기능을 쓰면 한 방에 다 만들어줍니다!)
   - Name tag: `patient-zone`
   - IPv4 CIDR block: `10.0.0.0/16`
   - Number of Availability Zones (AZs): **2** (`ap-northeast-2a`, `2c` 선택)
   - Number of public subnets: **2**
   - Number of private subnets: **2**
   - NAT gateways: **1 per AZ** (비용 아끼려면 "1 in 1 AZ" 선택, 운영용은 "1 per AZ")
   - VPC endpoints: **None**
4. **"Create VPC"** 클릭. (약 3분 소요)

### 1-2. DB용 서브넷 추가 (필수)
"VPC and more"는 DB 전용 서브넷을 따로 안 만들어주므로 수동으로 추가합니다.
1. 왼쪽 메뉴 **Subnets** > **Create subnet**.
2. VPC ID: 방금 만든 `patient-zone-vpc` 선택.
3. Subnet settings:
   - **Subnet 1**: `patient-zone-db-1` / AZ `2a` / CIDR `10.0.21.0/24`
   - **Subnet 2**: `patient-zone-db-2` / AZ `2c` / CIDR `10.0.22.0/24`
4. **Create subnet** 클릭.

### 1-3. 보안 그룹(Security Group) 미리 만들기
이후 단계들을 편하게 하기 위해 미리 뼈대를 만듭니다.
1. 왼쪽 메뉴 **Security groups** > **Create security group**.
2. **ALB용 (웹 진입)**
   - Name: `patient-zone-alb-sg`
   - Inbound: `HTTP (80) - Anywhere`, `HTTPS (443) - Anywhere`
3. **VPN용 (관리자 진입)**
   - Name: `patient-zone-vpn-sg`
   - Inbound: `UDP (443) - Anywhere` (VPN 포트)
4. **ECS용 (백엔드)**
   - Name: `patient-zone-ecs-sg`
   - Inbound: `Custom TCP (3000)` - Source: `patient-zone-alb-sg` (ALB에서만 허용)
   - Inbound: `All traffic` - Source: `patient-zone-vpn-sg` (VPN 관리자 허용)
5. **RDS용 (DB)**
   - Name: `patient-zone-rds-sg`
   - Inbound: `MySQL (3306)` - Source: `patient-zone-ecs-sg` (서버 접속)
   - Inbound: `MySQL (3306)` - Source: `patient-zone-vpn-sg` (관리자 접속)

---

## Step 2: 보안 인증서(SSL) 및 도메인 준비

### 2-1. ACM 인증서 발급 (서울 리전 - ALB용)
1. **Certificate Manager** 검색 > **Request a certificate**.
2. **Request a public certificate** 선택 > Next.
3. Domain names: `selffish234.cloud` 및 `*.selffish234.cloud`.
4. Validation method: **DNS validation**.
5. **Request** 클릭.
6. 목록에서 생성된 인증서 ID 클릭 > **"Create records in Route 53"** 버튼 클릭 > **Create records**. (자동으로 도메인 연결됨)

### 2-2. ACM 인증서 발급 (미국 동부 버지니아 - CloudFront용)
1. 콘솔 우측 상단 리전을 **US East (N. Virginia) us-east-1**으로 변경. (필수!)
2. 위와 똑같이 `selffish234.cloud`, `*.selffish234.cloud` 로 인증서를 요청하고 Route 53 레코드를 생성합니다.
3. 완료 후 다시 **Seoul (ap-northeast-2)** 리전으로 복귀.

---

## Step 3: 데이터베이스(RDS) 생성

1. **RDS** 검색 > **Databases** > **Create database**.
2. **Standard create** > **MySQL**.
3. **Templates**: `Free tier` (비용 절약) 또는 `Production`.
4. **Settings**:
   - Identifier: `patient-zone-mysql`
   - Master username: `admin`
   - Master password: (강력한 암호 입력)
5. **Instance config**: `db.t3.micro`.
6. **Connectivity**:
   - VPC: `patient-zone-vpc`
   - Public access: **No**
   - Security group: `patient-zone-rds-sg` 선택 (Default 제거).
7. **"Create database"**.

---

## Step 4: 보안 접속(Client VPN) 설정

VPN은 인증서 생성 때문에 **AWS CloudShell**(웹에서 쓰는 터미널)을 '도구'로써 잠깐 활용해야 합니다.

### 4-1. 인증서 생성 (CloudShell)
1. 콘솔 상단 아이콘 중 `>_` 모양(**CloudShell**) 클릭.
2. 아래 명령어 복사 붙여넣기 (인증서 자동 생성 스크립트):
   ```bash
   git clone https://github.com/OpenVPN/easy-rsa.git
   cd easy-rsa/easyrsa3
   ./easyrsa init-pki
   ./easyrsa build-ca nopass
   ./easyrsa build-server-full server nopass
   ./easyrsa build-client-full client1.domain.tld nopass
   mkdir ~/certs
   cp pki/ca.crt ~/certs/
   cp pki/issued/server.crt ~/certs/
   cp pki/private/server.key ~/certs/
   cp pki/issued/client1.domain.tld.crt ~/certs/
   cp pki/private/client1.domain.tld.key ~/certs/
   cd ~/certs
   aws acm import-certificate --certificate fileb://server.crt --private-key fileb://server.key --certificate-chain fileb://ca.crt
   aws acm import-certificate --certificate fileb://client1.domain.tld.crt --private-key fileb://client1.domain.tld.key --certificate-chain fileb://ca.crt
   ```
   이러면 ACM에 `server`, `client1...` 두 개의 인증서가 등록됩니다.

### 4-2. Client VPN Endpoint 생성
1. **VPC** 콘솔 > **Client VPN Endpoints** > **Create client VPN endpoint**.
2. 설정:
   - Client IPv4 CIDR: `10.100.0.0/22` (VPC랑 안 겹치는 대역 아무거나)
   - Server certificate: `server` (방금 등록한 것)
   - Authentication options: **Use mutual authentication** -> `client1.domain.tld` 선택.
   - **Split-tunnel**: Enable (체크 필수!)
   - VPC ID: `patient-zone-vpc`
   - Security Group: `patient-zone-vpn-sg`
3. **Create**.

### 4-3. VPN 연결 및 승인
1. 생성된 VPN 클릭 > **Target network associations** 탭 > **Associate target network**.
   - VPC의 Private Subnet 중 하나를 선택해서 연결 (약 5분 소요).
2. **Authorization rules** 탭 > **Add authorization rule**.
   - Destination: `10.0.0.0/16` (VPC 전체)
   - Access: **Allow access to all users**.
3. **Download Client Configuration** 버튼 눌러서 `.ovpn` 파일 다운로드.
4. `.ovpn` 파일을 메모장으로 열고 `<cert>...</cert>`와 `<key>...</key>` 부분을 CloudShell에서 `cat client1.domain.tld.crt` 등으로 확인한 값으로 채워 넣음.
5. OpenVPN Client 앱으로 접속 테스트.

---

## Step 5: 백엔드 서버(ECS) 배포

### 5-1. ECR 생성 및 이미지 푸시 (로컬 PC에서 수행)
1. **ECR** 콘솔 > **Repositories** > **Create repository**.
2. 이름: `patient-zone-backend`.
3. **"View push commands"** 버튼을 눌러 나오는 명령어 4개를 로컬 터미널(Docker 있는 곳)에서 실행하여 이미지 업로드.

### 5-2. Task Definition (작업 정의)
1. **ECS** 콘솔 > **Task definitions** > **Create new task definition**.
2. 설정:
   - Family: `patient-zone-task`
   - Launch type: **AWS Fargate**
   - CPU/Memory: `.25 vCPU / .5 GB` (최소 사양)
   - Container - Image URI: 방금 ECR 주소 넣기.
   - Container Port: `3000`
   - Environment variables: `DB_HOST`(RDS 엔드포인트), `DB_USER` 등 입력.
3. **Create**.

### 5-3. Cluster 생성
1. **Clusters** > **Create cluster** > 이름 `patient-zone-cluster` > Fargate 선택 > Create.

---

## Step 6: 로드밸런서(ALB) 및 도메인 연결

### 6-1. Target Group
1. **EC2** 콘솔 > **Target groups** > **Create target group**.
2. Type: **IP addresses**.
3. Port: `3000`, VPC: `patient-zone-vpc`.
4. Health check path: `/health`.
5. Next > Register targets는 그냥 Skip (ECS가 알아서 함) > Create.

### 6-2. Application Load Balancer
1. **Load Balancers** > **Create** > ALB.
2. Network mapping: VPC 및 **Public Subnet 2개** 선택.
3. Security, groups: `patient-zone-alb-sg`.
4. Listeners:
   - **HTTP:80** -> Action: Redirect to HTTPS 443.
   - **HTTPS:443** -> Action: Forward to Target Group.
   - Secure Listener settings: ACM 인증서(`selffish234.cloud`) 선택.
5. **Create**.

### 6-3. ECS Service 생성 (연결)
1. ECS 클러스터 > **Services** > **Create**.
2. Family: `patient-zone-task`.
3. Service name: `patient-zone-service`.
4. Networking: **Private Subnet 2개** 선택, SG는 `patient-zone-ecs-sg`.
5. Load balancing: **Application Load Balancer** 선택 > Use existing (`patient-zone-alb`).
6. Container to load balance: `3000:3000` > Target Group 선택.
7. **Create**.

### 6-4. Route 53 연결
1. **Route 53** > Hosted zones > 도메인 클릭.
2. **Create record**.
3. Record name: `api` (즉 `api.selffish234.cloud`가 됨).
4. **Alias** 스위치 켜기.
5. Route traffic to: **Alias to Application and Classic Load Balancer** > Seoul region > 아까 만든 ALB 선택.
6. **Create records**.

---

## Step 7: 프론트엔드 배포(S3+CloudFront)

### 7-1. S3 버킷
1. **S3** > **Create bucket** > 고유한 이름.
2. 모든 설정 기본값 (Public Access 차단됨).
3. 로컬에서 `npm run build` 한 `out` 폴더 내용물을 몽땅 업로드.

### 7-2. CloudFront
1. **CloudFront** > **Create distribution**.
2. Origin domain: 생성한 S3 버킷 선택.
   - **Origin access control settings**: "Origin access control settings (recommended)" 선택 > **Create control setting**.
3. Viewer protocol policy: **Redirect HTTP to HTTPS**.
4. Settings:
   - Alternate domain name (CNAME): `patient.selffish234.cloud`
   - Custom SSL certificate: `us-east-1`에서 만든 인증서 선택.
   - Default root object: `index.html`.
5. **Create**.
6. 생성 후 상단에 뜨는 파란 박스 **"Copy permissions"** 버튼 클릭 > **Go to S3 bucket policy** > 붙여넣고 저장. (S3 권한 허용)

### 7-3. Route 53 연결
1. Route 53 > 레코드 생성.
2. 이름: `patient` (즉 `patient.selffish234.cloud`).
3. Alias 켜기 > **Alias to CloudFront distribution** > 배포한 CloudFront 선택.
4. Create.

---

## Step 8: GCP 의사(Cloud Run) 배포

### 8-1. Docker 이미지
1. **Google Cloud Console** > **Artifact Registry**.
2. 리포지토리 생성 (`cloud-doctor-repo` / Docker / Seoul).
3. "설정 안내 보기"를 눌러 로컬 터미널 인증 후 `doctor-gcp` 폴더 내용 빌드 & 푸시.

### 8-2. Cloud Run
1. **Cloud Run** > **서비스 만들기**.
2. 컨테이너 이미지: 업로드한 이미지 선택.
3. 서비스 이름: `doctor-zone`.
4. 리전: `asia-northeast3` (서울).
5. 인증: **인증되지 않은 호출 허용**. (Slack용)
6. **환경 변수** (컨테이너 탭):
   - `AWS_ACCESS_KEY_ID`: (IAM에서 만든 키)
   - `AWS_SECRET_ACCESS_KEY`: (IAM에서 만든 키)
   - `AWS_REGION`: `ap-northeast-2`
   - `LOG_GROUP_NAME`: `/ecs/patient-zone`
7. **만들기**.

수고하셨습니다! 이제 `https://patient.selffish234.cloud` 에 접속하면 서비스가 실행됩니다.
