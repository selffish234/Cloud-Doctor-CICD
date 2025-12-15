"""
AWS Client - Cross-Cloud Authentication & Log Fetching
GCP에서 AWS AssumeRole을 통해 CloudWatch Logs를 수집합니다.
메가존클라우드 채용 포인트: Hybrid Cloud Security 구현
"""

import boto3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class AWSLogFetcher:
    """
    AWS CloudWatch Logs를 안전하게 수집하는 클래스

    특징:
    - AssumeRole을 통한 임시 자격증명 사용 (장기 키 노출 방지)
    - Cross-Account/Cross-Cloud 접근 지원
    - 자동 재시도 및 에러 핸들링
    """

    def __init__(
        self,
        role_arn: str,
        region: str = "ap-northeast-2",
        session_name: str = "CloudDoctorSession"
    ):
        """
        Args:
            role_arn: AWS IAM Role ARN (예: arn:aws:iam::123456789012:role/CloudDoctorRole)
            region: AWS 리전
            session_name: STS 세션 이름 (CloudTrail 로그에 표시됨)
        """
        self.role_arn = role_arn
        self.region = region
        self.session_name = session_name
        self._logs_client = None
        self._credentials_expire_at = None

    def _get_gcp_identity_token(self) -> str:
        """
        GCP Service Account의 OIDC ID 토큰 획득
        Cloud Run에서 실행 시 메타데이터 서버에서 가져옴
        """
        import requests

        try:
            # Cloud Run 메타데이터 서버에서 ID 토큰 가져오기
            metadata_server = "http://metadata.google.internal/computeMetadata/v1/"
            token_url = metadata_server + "instance/service-accounts/default/identity?audience=accounts.google.com"

            headers = {"Metadata-Flavor": "Google"}
            response = requests.get(token_url, headers=headers, timeout=5)

            if response.status_code == 200:
                logger.info("✅ GCP OIDC token obtained from metadata server")
                return response.text
            else:
                raise Exception(f"Failed to get GCP token: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ Failed to get GCP OIDC token: {str(e)}")
            raise

    def _assume_role(self) -> Dict[str, str]:
        """
        AWS STS AssumeRoleWithWebIdentity를 통해 임시 자격증명 획득

        메가존클라우드 채용 포인트:
        - GCP Service Account의 OIDC 토큰을 사용한 Keyless 인증
        - 장기 Access Key 대신 임시 보안 토큰 사용 (보안 모범 사례)

        Returns:
            임시 자격증명 딕셔너리
        """
        try:
            logger.info(f"🔐 Assuming AWS Role: {self.role_arn}")

            # GCP OIDC 토큰 획득
            gcp_token = self._get_gcp_identity_token()

            # STS 클라이언트 생성 (자격증명 없이)
            sts_client = boto3.client('sts', region_name=self.region)

            # AssumeRoleWithWebIdentity 호출
            response = sts_client.assume_role_with_web_identity(
                RoleArn=self.role_arn,
                RoleSessionName=self.session_name,
                WebIdentityToken=gcp_token,
                DurationSeconds=3600  # 1시간 유효
            )

            credentials = response['Credentials']
            self._credentials_expire_at = credentials['Expiration']

            logger.info(f"✅ Role assumed successfully with GCP OIDC token")
            logger.info(f"   Session expires at: {self._credentials_expire_at}")

            return {
                'aws_access_key_id': credentials['AccessKeyId'],
                'aws_secret_access_key': credentials['SecretAccessKey'],
                'aws_session_token': credentials['SessionToken']
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']

            if error_code == 'AccessDenied':
                logger.error(f"❌ Access Denied: {error_msg}")
                logger.error("   Check if the Trust Relationship is configured correctly")
            else:
                logger.error(f"❌ STS AssumeRoleWithWebIdentity failed: {error_code} - {error_msg}")

            raise Exception(f"Failed to assume role: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Unexpected error during AssumeRole: {str(e)}")
            raise

    def _get_logs_client(self):
        """
        CloudWatch Logs 클라이언트를 가져옵니다.
        자격증명이 만료되었으면 자동으로 갱신합니다.
        """
        now = datetime.now(self._credentials_expire_at.tzinfo if self._credentials_expire_at else None)

        # 자격증명이 없거나 5분 이내 만료 예정이면 갱신
        if not self._logs_client or not self._credentials_expire_at or \
           (self._credentials_expire_at - now).total_seconds() < 300:

            credentials = self._assume_role()
            self._logs_client = boto3.client(
                'logs',
                region_name=self.region,
                **credentials
            )

        return self._logs_client

    async def fetch_error_logs(
        self,
        log_group_name: str,
        time_range_minutes: int = 30,
        max_results: int = 50,
        filter_pattern: str = "?ERROR ?Error ?error ?CRITICAL ?FATAL"
    ) -> List[Dict[str, Any]]:
        """
        CloudWatch Logs에서 에러 로그를 수집합니다.

        Args:
            log_group_name: CloudWatch Log Group 이름
            time_range_minutes: 검색할 시간 범위 (분)
            max_results: 최대 결과 개수
            filter_pattern: CloudWatch Logs Insights 필터 패턴

        Returns:
            로그 이벤트 리스트 [{"timestamp": ..., "message": ...}, ...]
        """
        try:
            logs_client = self._get_logs_client()

            # 시간 범위 계산 (밀리초 단위)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_range_minutes)

            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)

            logger.info(f"📊 Fetching logs from CloudWatch...")
            logger.info(f"   Log Group: {log_group_name}")
            logger.info(f"   Time Range: {start_time.isoformat()} ~ {end_time.isoformat()}")
            logger.info(f"   Filter: {filter_pattern}")

            # CloudWatch Logs 쿼리
            response = logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern=filter_pattern,
                limit=max_results
            )

            events = response.get('events', [])

            # 로그 이벤트 변환
            logs = []
            for event in events:
                logs.append({
                    'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                    'message': event['message'].strip(),
                    'log_stream': event.get('logStreamName', 'unknown')
                })

            logger.info(f"✅ Fetched {len(logs)} log events")

            return logs

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']

            if error_code == 'ResourceNotFoundException':
                logger.error(f"❌ Log Group not found: {log_group_name}")
                raise Exception(f"Log group '{log_group_name}' does not exist")
            else:
                logger.error(f"❌ CloudWatch Logs API error: {error_code} - {error_msg}")
                raise Exception(f"Failed to fetch logs: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Unexpected error while fetching logs: {str(e)}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """
        AWS 연결 테스트 (헬스체크용)

        Returns:
            연결 상태 정보
        """
        try:
            credentials = self._assume_role()

            # STS GetCallerIdentity로 현재 자격증명 확인
            sts_client = boto3.client(
                'sts',
                region_name=self.region,
                aws_access_key_id=credentials['aws_access_key_id'],
                aws_secret_access_key=credentials['aws_secret_access_key'],
                aws_session_token=credentials['aws_session_token']
            )

            identity = sts_client.get_caller_identity()

            return {
                "status": "success",
                "account_id": identity['Account'],
                "user_id": identity['UserId'],
                "arn": identity['Arn'],
                "credentials_expire_at": self._credentials_expire_at.isoformat()
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


# 사용 예시 (테스트용)
if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        fetcher = AWSLogFetcher(
            role_arn=os.getenv("AWS_ROLE_ARN", "arn:aws:iam::123456789012:role/TestRole"),
            region="ap-northeast-2"
        )

        # 연결 테스트
        print("Testing AWS connection...")
        result = await fetcher.test_connection()
        print(result)

        # 로그 수집 테스트
        if result['status'] == 'success':
            print("\nFetching error logs...")
            logs = await fetcher.fetch_error_logs(
                log_group_name="/aws/ec2/chaos-app",
                time_range_minutes=30,
                max_results=10
            )
            for log in logs:
                print(f"[{log['timestamp']}] {log['message'][:100]}...")

    asyncio.run(test())


class AWSClientDirect:
    """
    Direct AWS authentication using Access Key/Secret Key
    Simple version for Cloud Run deployment without AssumeRole complexity
    """

    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str = "ap-northeast-2"
    ):
        """
        Args:
            aws_access_key_id: AWS Access Key ID
            aws_secret_access_key: AWS Secret Access Key
            region: AWS Region
        """
        self.region = region
        self.logs_client = boto3.client(
            'logs',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        logger.info(f"✅ AWS CloudWatch Logs client initialized (region: {region})")

    def get_error_logs(
        self,
        log_group_name: str,
        minutes: int = 30,
        max_logs: int = 100,
        filter_pattern: str = "?ERROR ?Error ?error ?CRITICAL ?FATAL ?WARNING ?Warning"
    ) -> List[Dict[str, Any]]:
        """
        Fetch error logs from CloudWatch Logs

        Args:
            log_group_name: CloudWatch Log Group name
            minutes: Time range in minutes
            max_logs: Maximum number of logs to fetch
            filter_pattern: CloudWatch Logs filter pattern

        Returns:
            List of log events with timestamp and message
        """
        try:
            # Calculate time range (milliseconds)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=minutes)

            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)

            logger.info(f"📊 Fetching logs from CloudWatch...")
            logger.info(f"   Log Group: {log_group_name}")
            logger.info(f"   Time Range: {start_time.isoformat()} ~ {end_time.isoformat()}")
            logger.info(f"   Filter: {filter_pattern}")

            # Query CloudWatch Logs
            response = self.logs_client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_ms,
                endTime=end_ms,
                filterPattern=filter_pattern,
                limit=max_logs
            )

            events = response.get('events', [])

            # Convert log events
            logs = []
            for event in events:
                logs.append({
                    'timestamp': datetime.fromtimestamp(event['timestamp'] / 1000).isoformat(),
                    'message': event['message'].strip(),
                    'log_stream': event.get('logStreamName', 'unknown')
                })

            logger.info(f"✅ Fetched {len(logs)} log events")

            return logs

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']

            if error_code == 'ResourceNotFoundException':
                logger.error(f"❌ Log Group not found: {log_group_name}")
                raise Exception(f"Log group '{log_group_name}' does not exist")
            else:
                logger.error(f"❌ CloudWatch Logs API error: {error_code} - {error_msg}")
                raise Exception(f"Failed to fetch logs: {error_msg}")

        except Exception as e:
            logger.error(f"❌ Unexpected error while fetching logs: {str(e)}")
            raise
