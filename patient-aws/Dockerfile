# Chaos App Dockerfile for AWS ECR
# 메가존클라우드 포트폴리오 - Patient Zone

FROM python:3.11-slim

# 메타데이터
LABEL maintainer="Cloud Doctor MVP"
LABEL description="Chaos engineering app that generates intentional error logs"
LABEL aws.service="ECR"

# 작업 디렉토리 설정
WORKDIR /app

# requirements.txt 복사 및 의존성 설치
# Docker 레이어 캐싱을 위해 먼저 requirements만 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app.py .

# 헬스체크 설정 (선택사항 - ECS/K8s에서 유용)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "print('healthy')" || exit 1

# 비root 사용자로 실행 (보안 모범 사례)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Python 버퍼링 비활성화 (로그 실시간 출력을 위해)
ENV PYTHONUNBUFFERED=1

# 컨테이너 시작 시 실행할 명령
CMD ["python", "app.py"]
