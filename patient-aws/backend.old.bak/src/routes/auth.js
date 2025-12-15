/**
 * Authentication Routes - 로그인/회원가입 API
 *
 * JWT 기반 인증 시스템
 */

const express = require('express');
const jwt = require('jsonwebtoken');
const { User } = require('../models');

const router = express.Router();

/**
 * POST /api/auth/register
 * 회원가입
 */
router.post('/register', async (req, res) => {
  const startTime = Date.now();

  try {
    const { email, password, name } = req.body;

    // 입력 검증
    if (!email || !password) {
      return res.status(400).json({
        error: 'Email and password are required'
      });
    }

    // 사용자 생성
    const user = await User.create({
      email,
      password,
      name: name || 'Anonymous'
    });

    const responseTime = Date.now() - startTime;
    console.log(`[AUTH] User registered: ${email} (${responseTime}ms)`);

    res.status(201).json({
      message: 'User created successfully',
      user: user.toSafeJSON()
    });

  } catch (error) {
    const responseTime = Date.now() - startTime;

    // 중복 이메일 에러
    if (error.name === 'SequelizeUniqueConstraintError') {
      console.error(`[AUTH ERROR] Duplicate email: ${req.body.email} (${responseTime}ms)`);
      return res.status(409).json({
        error: 'Email already exists'
      });
    }

    // Validation 에러
    if (error.name === 'SequelizeValidationError') {
      console.error(`[AUTH ERROR] Validation failed: ${error.message} (${responseTime}ms)`);
      return res.status(400).json({
        error: error.errors.map(e => e.message).join(', ')
      });
    }

    // DB 연결 에러 (Doctor가 분석할 로그)
    console.error('[DB ERROR] Registration failed:', {
      timestamp: new Date().toISOString(),
      error: error.message,
      code: error.parent?.code,
      responseTime: `${responseTime}ms`
    });

    res.status(500).json({
      error: 'Failed to create user'
    });
  }
});

/**
 * POST /api/auth/login
 * 로그인
 */
router.post('/login', async (req, res) => {
  const startTime = Date.now();

  try {
    const { email, password } = req.body;

    // 입력 검증
    if (!email || !password) {
      return res.status(400).json({
        error: 'Email and password are required'
      });
    }

    // 사용자 조회
    const user = await User.findOne({ where: { email } });

    if (!user) {
      const responseTime = Date.now() - startTime;
      console.error(`[AUTH ERROR] User not found: ${email} (${responseTime}ms)`);

      return res.status(401).json({
        error: 'Invalid email or password'
      });
    }

    // 비밀번호 검증
    const isValid = await user.validatePassword(password);

    if (!isValid) {
      const responseTime = Date.now() - startTime;
      console.error(`[AUTH ERROR] Invalid password for user: ${email} (${responseTime}ms)`);

      return res.status(401).json({
        error: 'Invalid email or password'
      });
    }

    // JWT 토큰 생성
    const token = jwt.sign(
      {
        id: user.id,
        email: user.email
      },
      process.env.JWT_SECRET,
      {
        expiresIn: '24h' // 장애 시나리오: 짧게 설정하면 토큰 만료 에러 유발
      }
    );

    const responseTime = Date.now() - startTime;
    console.log(`[AUTH] User logged in: ${email} (${responseTime}ms)`);

    res.json({
      message: 'Login successful',
      token,
      user: user.toSafeJSON()
    });

  } catch (error) {
    const responseTime = Date.now() - startTime;

    console.error('[AUTH ERROR] Login failed:', {
      timestamp: new Date().toISOString(),
      error: error.message,
      responseTime: `${responseTime}ms`
    });

    res.status(500).json({
      error: 'Login failed'
    });
  }
});

/**
 * GET /api/auth/verify
 * 토큰 검증
 */
router.get('/verify', async (req, res) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({
        error: 'No token provided'
      });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    res.json({
      valid: true,
      user: decoded
    });

  } catch (error) {
    // JWT 만료 에러 (장애 시나리오)
    if (error.name === 'TokenExpiredError') {
      console.error('[JWT ERROR] Token expired:', {
        timestamp: new Date().toISOString(),
        expiredAt: error.expiredAt
      });

      return res.status(401).json({
        error: 'Token expired',
        expiredAt: error.expiredAt
      });
    }

    console.error('[JWT ERROR] Token verification failed:', error.message);

    res.status(401).json({
      error: 'Invalid token'
    });
  }
});

module.exports = router;
