# Patient Backend Dockerfile
# Multi-stage build for production optimization

# ===== Stage 1: Dependencies =====
FROM node:18-alpine AS deps

WORKDIR /app

# 패키지 파일만 먼저 복사 (캐싱 최적화)
COPY package*.json ./

# Production dependencies만 설치
RUN npm install --omit=dev && \
    npm cache clean --force

# ===== Stage 2: Builder =====
FROM node:18-alpine AS builder

WORKDIR /app

# Dependencies 복사
COPY --from=deps /app/node_modules ./node_modules

# 소스 코드 복사
COPY . .

# ===== Stage 3: Runner =====
FROM node:18-alpine AS runner

# 보안: root 사용자가 아닌 별도 사용자로 실행
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Production dependencies 복사
COPY --from=deps /app/node_modules ./node_modules

# 소스 코드 복사
COPY --chown=nodejs:nodejs . .

# 비root 사용자로 전환
USER nodejs

# 환경변수
ENV NODE_ENV=production \
    PORT=3000

# 포트 노출
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# 서버 시작
CMD ["node", "src/index.js"]
