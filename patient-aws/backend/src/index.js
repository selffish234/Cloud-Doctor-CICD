/**
 * Patient Backend Server - Main Entry Point
 *
 * Cloud Doctor Patient Zone
 * 3-Tier Architecture Backend API (Express + MySQL)
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const { testConnection, initDatabase } = require('./models');
const authRoutes = require('./routes/auth');
const postsRoutes = require('./routes/posts');

const app = express();
const PORT = process.env.PORT || 3000;

// ===== 미들웨어 설정 =====

// 보안 헤더
app.use(helmet());

// CORS 설정
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Body 파서
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// HTTP 로깅 (Morgan)
if (process.env.NODE_ENV === 'development') {
  app.use(morgan('dev'));
} else {
  // Production: 간결한 로그
  app.use(morgan('combined', {
    skip: (req) => req.url === '/health' // Health check는 로그 제외
  }));
}

// ===== 라우트 설정 =====

/**
 * GET /
 * 루트 엔드포인트 - 헬스체크
 */
app.get('/', (req, res) => {
  res.status(200).json({
    service: 'Cloud Doctor Patient Backend',
    status: 'healthy',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
});

/**
 * GET /health
 * 상세 헬스체크 (ALB Target Health Check용)
 */
app.get('/health', async (req, res) => {
  const startTime = Date.now();

  try {
    // DB 연결 상태 확인
    const dbConnected = await testConnection();

    const responseTime = Date.now() - startTime;

    res.status(200).json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      database: {
        connected: dbConnected,
        host: process.env.DB_HOST
      },
      memory: {
        used: `${(process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2)}MB`,
        total: `${(process.memoryUsage().heapTotal / 1024 / 1024).toFixed(2)}MB`
      },
      responseTime: `${responseTime}ms`
    });

  } catch (error) {
    console.error('[HEALTH CHECK ERROR]', error.message);

    res.status(503).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * GET /api/metrics
 * 메트릭 엔드포인트 (모니터링용)
 */
app.get('/api/metrics', (req, res) => {
  const mem = process.memoryUsage();

  res.json({
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: {
      rss: `${(mem.rss / 1024 / 1024).toFixed(2)}MB`,
      heapTotal: `${(mem.heapTotal / 1024 / 1024).toFixed(2)}MB`,
      heapUsed: `${(mem.heapUsed / 1024 / 1024).toFixed(2)}MB`,
      external: `${(mem.external / 1024 / 1024).toFixed(2)}MB`
    },
    cpu: process.cpuUsage(),
    env: {
      nodeVersion: process.version,
      platform: process.platform,
      nodeEnv: process.env.NODE_ENV
    }
  });
});

/**
 * POST /api/chaos/*
 * 장애 시나리오 트리거 엔드포인트 (테스트용)
 */
app.post('/api/chaos/db-fail', async (req, res) => {
  try {
    const { triggerDBFailure } = require('./chaos/db-failure');
    const result = await triggerDBFailure();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chaos/pool-exhaustion', async (req, res) => {
  try {
    const { triggerPoolExhaustion } = require('./chaos/pool-exhaustion');
    const result = await triggerPoolExhaustion();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chaos/memory-leak', (req, res) => {
  const { triggerMemoryLeak } = require('./chaos/memory-leak');
  triggerMemoryLeak(30); // 30초 동안 메모리 누수
  res.json({ message: 'Memory leak triggered for 30 seconds' });
});

app.post('/api/chaos/slow-query', async (req, res) => {
  try {
    const { triggerSlowQuery } = require('./chaos/slow-query');
    const result = await triggerSlowQuery();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chaos/api-timeout', async (req, res) => {
  try {
    const { triggerAPITimeout } = require('./chaos/api-timeout');
    const result = await triggerAPITimeout();
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chaos/jwt-expiry', (req, res) => {
  const { triggerJWTExpiry } = require('./chaos/jwt-expiry');
  triggerJWTExpiry();
  res.json({ message: 'JWT expiry scenario triggered' });
});

app.post('/api/chaos/high-cpu', (req, res) => {
  const { triggerHighCPU } = require('./chaos/high-cpu');
  triggerHighCPU(30); // 30초 동안 CPU 100%
  res.json({ message: 'High CPU load triggered for 30 seconds' });
});

// API 라우트
app.use('/api/auth', authRoutes);
app.use('/api/posts', postsRoutes);

// ===== 에러 핸들링 =====

/**
 * 404 Not Found
 */
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    path: req.path,
    method: req.method
  });
});

/**
 * 전역 에러 핸들러
 */
app.use((err, req, res, next) => {
  console.error('[SERVER ERROR]', {
    timestamp: new Date().toISOString(),
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method
  });

  res.status(err.status || 500).json({
    error: err.message || 'Internal Server Error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});

// ===== 서버 시작 =====

async function startServer() {
  try {
    console.log('\n🩺 Cloud Doctor Patient Backend Starting...\n');

    // DB 연결 테스트
    console.log('1. Testing database connection...');
    const dbConnected = await testConnection();

    if (!dbConnected) {
      console.error('❌ Failed to connect to database. Exiting...\n');
      process.exit(1);
    }

    // DB 초기화 (테이블 생성)
    console.log('\n2. Initializing database...');
    await initDatabase();

    // 서버 시작
    console.log('\n3. Starting HTTP server...');
    app.listen(PORT, '0.0.0.0', () => {
      console.log(`\n✅ Server running on port ${PORT}`);
      console.log(`   Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`   Database: ${process.env.DB_HOST}`);
      console.log(`   Chaos Mode: ${process.env.CHAOS_MODE || 'false'}`);
      console.log('\n📡 Endpoints:');
      console.log(`   GET  /health`);
      console.log(`   GET  /api/metrics`);
      console.log(`   POST /api/auth/register`);
      console.log(`   POST /api/auth/login`);
      console.log(`   GET  /api/posts`);
      console.log(`   POST /api/posts`);
      console.log(`   POST /api/chaos/* (7 scenarios)`);
      console.log('\n');
    });

  } catch (error) {
    console.error('❌ Failed to start server:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Graceful Shutdown
process.on('SIGTERM', () => {
  console.log('\n🛑 SIGTERM received. Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('\n🛑 SIGINT received. Shutting down gracefully...');
  process.exit(0);
});

// 서버 시작
if (require.main === module) {
  startServer();
}

module.exports = app;
