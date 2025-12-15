/**
 * Posts Routes - 게시판 CRUD API
 *
 * 간단한 게시판 기능 구현
 * 여기에 의도적인 성능 문제(N+1 쿼리 등)를 심어 장애 시나리오 생성
 */

const express = require('express');
const { Post, User } = require('../models');
const jwt = require('jsonwebtoken');

const router = express.Router();

/**
 * JWT 인증 미들웨어
 */
function authenticate(req, res, next) {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();

  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      console.error('[JWT ERROR] Token expired at:', error.expiredAt);
    }
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

/**
 * GET /api/posts
 * 게시글 목록 조회
 *
 * 장애 시나리오: N+1 쿼리 문제 (CHAOS_MODE=true 시)
 */
router.get('/', async (req, res) => {
  const startTime = Date.now();

  try {
    const { limit = 10, offset = 0 } = req.query;

    // CHAOS_MODE: 의도적으로 N+1 쿼리 발생 (성능 저하)
    if (process.env.CHAOS_MODE === 'true') {
      console.warn('[CHAOS] N+1 Query scenario enabled');

      // 나쁜 예: 각 Post마다 User 조회 (N+1 문제)
      const posts = await Post.findAll({
        limit: parseInt(limit),
        offset: parseInt(offset),
        order: [['created_at', 'DESC']]
      });

      // 각 게시글마다 작성자 정보 따로 조회
      const postsWithAuthors = await Promise.all(
        posts.map(async (post) => {
          const author = await User.findByPk(post.user_id);
          const queryTime = Date.now() - startTime;

          console.log(`[SLOW QUERY] Fetching author for post ${post.id}: ${queryTime}ms`);

          return {
            ...post.toJSON(),
            author: author?.toSafeJSON()
          };
        })
      );

      const totalTime = Date.now() - startTime;
      console.warn(`[PERFORMANCE WARNING] Total query time: ${totalTime}ms (N+1 detected)`);

      return res.json({
        posts: postsWithAuthors,
        count: postsWithAuthors.length,
        queryTime: `${totalTime}ms`
      });
    }

    // 정상 케이스: JOIN으로 한 번에 조회
    const posts = await Post.findAll({
      include: [{
        model: User,
        as: 'author',
        attributes: ['id', 'email', 'name']
      }],
      limit: parseInt(limit),
      offset: parseInt(offset),
      order: [['created_at', 'DESC']]
    });

    const responseTime = Date.now() - startTime;
    console.log(`[API] GET /api/posts - ${posts.length} posts (${responseTime}ms)`);

    res.json({
      posts,
      count: posts.length,
      queryTime: `${responseTime}ms`
    });

  } catch (error) {
    const responseTime = Date.now() - startTime;

    console.error('[DB ERROR] Failed to fetch posts:', {
      timestamp: new Date().toISOString(),
      error: error.message,
      code: error.parent?.code,
      responseTime: `${responseTime}ms`
    });

    res.status(500).json({
      error: 'Failed to fetch posts'
    });
  }
});

/**
 * GET /api/posts/:id
 * 게시글 상세 조회
 */
router.get('/:id', async (req, res) => {
  const startTime = Date.now();

  try {
    const post = await Post.findByPk(req.params.id, {
      include: [{
        model: User,
        as: 'author',
        attributes: ['id', 'email', 'name']
      }]
    });

    if (!post) {
      return res.status(404).json({
        error: 'Post not found'
      });
    }

    const responseTime = Date.now() - startTime;
    console.log(`[API] GET /api/posts/${req.params.id} (${responseTime}ms)`);

    res.json(post);

  } catch (error) {
    console.error('[DB ERROR] Failed to fetch post:', error.message);
    res.status(500).json({
      error: 'Failed to fetch post'
    });
  }
});

/**
 * POST /api/posts
 * 게시글 작성 (인증 필요)
 */
router.post('/', authenticate, async (req, res) => {
  const startTime = Date.now();

  try {
    const { title, content } = req.body;

    if (!title) {
      return res.status(400).json({
        error: 'Title is required'
      });
    }

    const post = await Post.create({
      user_id: req.user.id,
      title,
      content: content || ''
    });

    const responseTime = Date.now() - startTime;
    console.log(`[API] POST /api/posts - Created post ${post.id} (${responseTime}ms)`);

    res.status(201).json(post);

  } catch (error) {
    console.error('[DB ERROR] Failed to create post:', {
      timestamp: new Date().toISOString(),
      error: error.message,
      userId: req.user?.id
    });

    res.status(500).json({
      error: 'Failed to create post'
    });
  }
});

/**
 * DELETE /api/posts/:id
 * 게시글 삭제 (본인만 가능)
 */
router.delete('/:id', authenticate, async (req, res) => {
  try {
    const post = await Post.findByPk(req.params.id);

    if (!post) {
      return res.status(404).json({
        error: 'Post not found'
      });
    }

    // 본인 확인
    if (post.user_id !== req.user.id) {
      return res.status(403).json({
        error: 'Forbidden: You can only delete your own posts'
      });
    }

    await post.destroy();

    console.log(`[API] DELETE /api/posts/${req.params.id} - Deleted by user ${req.user.id}`);

    res.json({
      message: 'Post deleted successfully'
    });

  } catch (error) {
    console.error('[DB ERROR] Failed to delete post:', error.message);
    res.status(500).json({
      error: 'Failed to delete post'
    });
  }
});

module.exports = router;
