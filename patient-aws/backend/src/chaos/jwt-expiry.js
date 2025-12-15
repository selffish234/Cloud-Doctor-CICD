/**
 * 장애 시나리오 #6: JWT 토큰 만료
 *
 * 시나리오: 짧은 토큰 수명으로 인한 인증 실패
 * 원인: expiresIn 설정 오류, 시간 동기화 문제
 * 로그 패턴: JsonWebTokenError: jwt expired, TokenExpiredError
 */

const jwt = require('jsonwebtoken');

function triggerJWTExpiry() {
  console.log('\n🔥 [CHAOS] Triggering JWT Expiry...\n');

  const JWT_SECRET = process.env.JWT_SECRET || 'test-secret';

  try {
    // 1초 만에 만료되는 토큰 생성
    const shortLivedToken = jwt.sign(
      {
        id: 1,
        email: 'test@example.com'
      },
      JWT_SECRET,
      { expiresIn: '1s' } // 매우 짧은 수명
    );

    console.log('   Token created with 1 second expiry');
    console.log(`   Token: ${shortLivedToken.substring(0, 50)}...`);

    // 2초 대기 (토큰 만료 유도)
    console.log('   Waiting 2 seconds for token to expire...\n');

    setTimeout(() => {
      try {
        // 만료된 토큰 검증 시도
        const decoded = jwt.verify(shortLivedToken, JWT_SECRET);
        console.log('   ✓ Token verified (unexpected):', decoded);

      } catch (error) {
        // TokenExpiredError 발생
        console.error('[JWT ERROR] Token verification failed:', {
          timestamp: new Date().toISOString(),
          error: error.message,
          errorName: error.name,
          expiredAt: error.expiredAt,
          tokenAge: error.expiredAt ? `Expired ${Math.floor((Date.now() - new Date(error.expiredAt).getTime()) / 1000)}s ago` : 'N/A'
        });

        console.error('\n🩺 Doctor should diagnose:');
        console.error('   - Root Cause: JWT token expired - expiresIn too short');
        console.error('   - Recommendation: Increase token lifetime to 24h or implement refresh tokens');
        console.error('   - Code Fix: Change expiresIn from "1s" to "24h" in auth route\n');

        if (require.main === module) {
          process.exit(0);
        }
      }
    }, 2000);

  } catch (error) {
    console.error('[CHAOS ERROR] Failed to trigger JWT expiry:', error.message);
    throw error;
  }
}

if (require.main === module) {
  triggerJWTExpiry();
}

module.exports = { triggerJWTExpiry };
