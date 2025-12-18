# 🚀 CI/CD Setup Guide (GitHub Actions)

이 가이드는 **Cloud Doctor MVP**의 배포 과정을 **GitHub Actions**를 통해 자동화하는 방법을 설명합니다.
이 설정이 완료되면 로컬에서 `terraform apply`를 수동으로 실행할 필요 없이, 코드를 GitHub에 Push하는 것만으로 배포가 이루어집니다.

---

## 📋 사전 요구사항

1.  **AWS OIDC Provider 설정**: GitHub Actions가 AWS 리소스에 접근할 수 있도록 OIDC Provider가 설정되어 있어야 합니다. (이미 Terraform에 포함되어 있을 수 있으나, 없다면 추가 설정이 필요합니다.)
2.  **GitHub Repository**: 코드가 GitHub에 업로드되어 있어야 합니다.

---

## Step 1: GitHub 환경변수 설정 (필수!)

GitHub Repository > **Settings** > **Secrets and variables** > **Actions** 메뉴에서 다음 값들을 등록해야 합니다.

### 1-1. Secrets (비밀 값)
**New repository secret** 버튼을 눌러 등록하세요.

| Name | Value 예시 | 설명 |
| :--- | :--- | :--- |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/CloudDoctorRole` | 배포에 사용할 IAM Role ARN (OIDC Trust가 설정된 Role) |
| `TF_VAR_DB_PASSWORD` | `SuperSecret123!` | RDS 데이터베이스 비밀번호 |
| `TF_VAR_JWT_SECRET` | `MyLongSecretString...` | 백엔드 인증용 JWT 시크릿 |
| `ALARM_EMAIL` | `youremail@example.com` | (선택) 알람 받을 이메일 주소 |

### 1-2. Variables (공개 값)
**Variables** 탭으로 이동하여 **New repository variable** 버튼을 눌러 등록하세요.

| Name | Value 예시 | 설명 |
| :--- | :--- | :--- |
| `DOMAIN_NAME` | `selffish234.cloud` | 구매한 도메인 이름 (없으면 비워두거나 생략) |
| `FRONTEND_BUCKET_NAME`| `joon-cloud-doctor234` | 프론트엔드용 S3 버킷 이름 (`terraform output`으로 확인 가능) |
| `CLOUDFRONT_DISTRIBUTION_ID` | `E1A2B3C4D5E6F` | CloudFront ID (`terraform output`으로 확인 가능) |
| `NEXT_PUBLIC_API_URL` | `https://api.selffish234.cloud` | 프론트엔드가 접속할 백엔드 API 주소 |
| `ECR_REPOSITORY_URL` | `patient-zone-backend` | ECR 리포지토리 이름 (URL 아님, 이름만) |
| `ECS_CLUSTER_NAME` | `patient-zone-cluster` | ECS 클러스터 이름 |
| `ECS_SERVICE_NAME` | `patient-zone-service` | ECS 서비스 이름 |

---

## Step 2: 배포 파이프라인 확인

설정이 완료되면 코드를 `main` 브랜치에 Push 할 때마다 변경된 부분에 맞춰 자동으로 배포가 실행됩니다.

### 🔄 1. Frontend 배포 (`cd-frontend.yml`)
- **트리거**: `patient-aws/frontend/` 폴더 내 파일 변경 시
- **동작**:
    1. Node.js 설치 및 빌드 (`npm run build`)
    2. 결과물(`out/`)을 S3 버킷에 동기화
    3. CloudFront 캐시 무효화 (즉시 반영)

### 🐳 2. Backend 배포 (`cd-backend.yml`)
- **트리거**: `patient-aws/backend/` 폴더 내 파일 변경 시
- **동작**:
    1. Docker 이미지 빌드
    2. Amazon ECR에 Push
    3. ECS Service 강제 업데이트 (`--force-new-deployment`) → 새 이미지로 컨테이너 교체

### 🏗️ 3. 인프라 배포 (`cd-infra.yml`)
- **트리거**: `terraform/` 폴더 내 파일 변경 시
- **동작**:
    1. Terraform Init
    2. Terraform Apply (`-auto-approve`) → 인프라 변경 사항 즉시 적용

---

## Step 3: 배포 실행 (Git Push)

모든 설정이 끝났으면, 만든 파일들을 GitHub에 올려서 배포를 시작합니다. 터미널에서 아래 명령어를 입력하세요.

```bash
# 1. 파일 상태 확인
git status

# 2. 모든 변경사항 스테이징
git add .

# 3. 커밋 메시지 작성 (이 메시지가 GitHub Actions에 표시됨)
git commit -m "Setup CI/CD pipelines"

# 4. Main 브랜치로 푸시 (배포 트리거 🚀)
git push origin main
```

---

## ⚠️ 주의사항

1.  **Terraform State Lock**: 여러 명이 동시에 배포하면 충돌이 날 수 있습니다. DynamoDB Lock이 설정되어 있는지 확인하세요.
2.  **초기 배포**: 인프라가 아예 없는 상태라면 로컬에서 최초 1회 `terraform apply`를 해주는 것이 안전할 수 있습니다. (GitHub Actions가 실패할 경우 디버깅이 어렵기 때문)
3.  **OIDC 설정**: 만약 `AWS_ROLE_ARN` 관련 에러가 난다면, AWS IAM에서 "GitHub OIDC Provider"가 생성되어 있고, 해당 Role의 Trust Relationship에 GitHub 저장소가 등록되어 있는지 확인해야 합니다.

---

**🎉 이제 GitHub Actions 탭에서 배포가 초록색(성공)으로 뜨는지 확인해 보세요!**
