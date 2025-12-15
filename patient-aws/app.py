"""
Chaos App - Patient (AWS)
이 앱은 의도적으로 다양한 에러 로그를 생성하여 CloudWatch로 전송합니다.
메가존클라우드 포트폴리오용 MVP 프로젝트
"""

import time
import random
import logging
import sys
from datetime import datetime

# CloudWatch Logs 전송을 위한 설정
# 실제 환경에서는 boto3로 CloudWatch에 직접 전송하지만,
# MVP에서는 stdout으로 출력하면 Docker 로그가 자동으로 CloudWatch로 전달됩니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ChaosGenerator:
    """다양한 장애 상황을 시뮬레이션하는 클래스"""

    def __init__(self):
        self.error_types = [
            self.database_connection_error,
            self.memory_overflow_error,
            self.api_timeout_error,
            self.disk_full_error,
            self.network_unreachable_error,
            self.authentication_failed_error,
            self.null_pointer_error,
            self.rate_limit_exceeded_error
        ]

    def database_connection_error(self):
        """데이터베이스 연결 실패 시뮬레이션"""
        db_hosts = ["10.0.2.55", "db-primary.internal", "postgres-master:5432"]
        host = random.choice(db_hosts)
        logger.error(f"[DB ERROR] Connection refused: Could not connect to database at {host}")
        logger.error(f"[DB ERROR] Error code: SQLSTATE[HY000] [2002] Connection timed out after 30s")

    def memory_overflow_error(self):
        """메모리 부족 에러 시뮬레이션"""
        usage = random.randint(85, 99)
        logger.error(f"[MEMORY ERROR] OutOfMemoryError: Java heap space exceeded")
        logger.error(f"[MEMORY ERROR] Current usage: {usage}% | Available: {100-usage}MB")
        logger.warning(f"[MEMORY WARN] GC overhead limit exceeded, application may crash soon")

    def api_timeout_error(self):
        """외부 API 타임아웃 시뮬레이션"""
        apis = [
            "https://api.payment-gateway.com/v1/charge",
            "https://auth.oauth-provider.com/token",
            "https://api.third-party-service.io/data"
        ]
        api = random.choice(apis)
        logger.error(f"[API ERROR] Request timeout: Failed to reach {api}")
        logger.error(f"[API ERROR] ReadTimeout: HTTPSConnectionPool read timed out after 60.0s")

    def disk_full_error(self):
        """디스크 용량 부족 시뮬레이션"""
        usage = random.randint(95, 100)
        logger.error(f"[DISK ERROR] No space left on device: /var/log/app")
        logger.error(f"[DISK ERROR] Disk usage: {usage}% on /dev/sda1")
        logger.critical(f"[DISK CRITICAL] Unable to write logs, storage critically low")

    def network_unreachable_error(self):
        """네트워크 연결 불가 시뮬레이션"""
        logger.error("[NETWORK ERROR] Network is unreachable: No route to host 172.31.45.8")
        logger.error("[NETWORK ERROR] Failed to establish connection to Redis cluster")
        logger.warning("[NETWORK WARN] Packet loss detected: 45% packet loss to upstream")

    def authentication_failed_error(self):
        """인증 실패 시뮬레이션"""
        users = ["admin", "service-account", "api-client-7721"]
        user = random.choice(users)
        logger.error(f"[AUTH ERROR] Authentication failed for user: {user}")
        logger.error(f"[AUTH ERROR] Invalid credentials or token expired")
        logger.warning(f"[AUTH WARN] Multiple failed login attempts detected from IP: 203.0.113.42")

    def null_pointer_error(self):
        """Null 참조 에러 시뮬레이션"""
        modules = ["PaymentProcessor", "UserSessionManager", "OrderValidator"]
        module = random.choice(modules)
        line = random.randint(100, 999)
        logger.error(f"[APP ERROR] NullPointerException in {module}.java:{line}")
        logger.error(f"[APP ERROR] Attempted to invoke method on null object reference")

    def rate_limit_exceeded_error(self):
        """Rate Limit 초과 시뮬레이션"""
        current_rate = random.randint(1000, 5000)
        logger.error(f"[RATE LIMIT ERROR] Too many requests: {current_rate} req/min exceeds limit of 1000")
        logger.error(f"[RATE LIMIT ERROR] HTTP 429: Rate limit exceeded, retry after 60 seconds")
        logger.warning(f"[RATE LIMIT WARN] Client throttled, requests being dropped")

    def generate_random_error(self):
        """랜덤한 에러 생성"""
        error_func = random.choice(self.error_types)
        error_func()

    def generate_normal_log(self):
        """정상 로그도 가끔 생성 (현실감)"""
        normal_messages = [
            "Application started successfully on port 8080",
            "Health check passed: All systems operational",
            "Request processed successfully in 234ms",
            "Cache hit ratio: 87.5%",
            "Background job completed: data-sync-job",
            "User session created: session-id-x7k92jf"
        ]
        logger.info(random.choice(normal_messages))


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("🏥 Chaos App Started - Patient Zone (AWS)")
    logger.info("=" * 60)
    logger.info("Purpose: Generate error logs for Cloud Doctor MVP")
    logger.info("Target: CloudWatch Logs → GCP AI Analysis")
    logger.info("=" * 60)

    chaos = ChaosGenerator()
    iteration = 0

    try:
        while True:
            iteration += 1
            logger.info(f"--- Iteration #{iteration} ---")

            # 80% 확률로 에러 생성, 20% 확률로 정상 로그
            if random.random() < 0.8:
                chaos.generate_random_error()
            else:
                chaos.generate_normal_log()

            # 10~30초 간격으로 에러 생성 (데모용)
            # 실제 운영 환경에서는 더 긴 간격 권장
            sleep_time = random.randint(10, 30)
            logger.info(f"Next error in {sleep_time} seconds...\n")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Chaos App Stopped by User")
        logger.info(f"Total iterations: {iteration}")
        logger.info("=" * 60)
    except Exception as e:
        logger.critical(f"[FATAL ERROR] Chaos App crashed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
