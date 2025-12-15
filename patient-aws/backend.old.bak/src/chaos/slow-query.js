/**
 * 장애 시나리오 #4: 느린 쿼리 (Slow Query)
 *
 * 시나리오: N+1 문제 또는 인덱스 미사용으로 쿼리 지연
 * 원인: JOIN 누락, 인덱스 없음, 대용량 테이블 Full Scan
 * 로그 패턴: Query execution time: XXXXms, Slow query detected
 */

const { sequelize, Post, User } = require('../models');

async function triggerSlowQuery() {
  console.log('\n🔥 [CHAOS] Triggering Slow Query (N+1 Problem)...\n');

  try {
    // 먼저 테스트 데이터 생성
    console.log('   Creating test data...');
    const testUser = await User.findOne() || await User.create({
      email: `chaos-test-${Date.now()}@example.com`,
      password: 'password123',
      name: 'Chaos Test User'
    });

    // 100개 게시글 생성
    for (let i = 0; i < 100; i++) {
      await Post.create({
        user_id: testUser.id,
        title: `Test Post ${i + 1}`,
        content: `This is test content ${i + 1}`
      });
    }

    console.log('   Test data created. Starting N+1 query...\n');

    // N+1 쿼리 문제 발생
    const startTime = Date.now();
    const posts = await Post.findAll({ limit: 100 });

    console.log(`[QUERY] Initial query completed: ${Date.now() - startTime}ms`);

    // 각 게시글마다 작성자 조회 (N+1 문제)
    for (const post of posts) {
      const queryStart = Date.now();
      const author = await User.findByPk(post.user_id);
      const queryTime = Date.now() - queryStart;

      if (queryTime > 100) {
        console.error(`[SLOW QUERY] Author fetch for post ${post.id}: ${queryTime}ms`, {
          timestamp: new Date().toISOString(),
          queryTime: `${queryTime}ms`,
          postId: post.id,
          userId: post.user_id
        });
      }
    }

    const totalTime = Date.now() - startTime;

    console.error('[PERFORMANCE ERROR] N+1 Query detected:', {
      timestamp: new Date().toISOString(),
      totalQueries: posts.length + 1,
      totalTime: `${totalTime}ms`,
      avgTimePerQuery: `${(totalTime / posts.length).toFixed(2)}ms`,
      recommendation: 'Use JOIN or include in Sequelize'
    });

    console.error('\n🩺 Doctor should diagnose:');
    console.error('   - Root Cause: N+1 query problem - fetching related data in loop');
    console.error('   - Recommendation: Use Sequelize include to JOIN tables');
    console.error('   - Code Fix: Post.findAll({ include: [{ model: User, as: "author" }] })\n');

    return {
      scenario: 'Slow Query (N+1)',
      totalQueries: posts.length + 1,
      totalTime: `${totalTime}ms`
    };

  } catch (error) {
    console.error('[CHAOS ERROR] Failed to trigger slow query:', error.message);
    throw error;
  }
}

if (require.main === module) {
  triggerSlowQuery()
    .then(() => console.log('✅ Chaos scenario executed'))
    .catch(err => console.error('❌ Chaos scenario failed:', err))
    .finally(() => process.exit(0));
}

module.exports = { triggerSlowQuery };
