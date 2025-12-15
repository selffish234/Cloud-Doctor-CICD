/**
 * 장애 시나리오 #5: 외부 API 타임아웃
 *
 * 시나리오: 외부 서비스 지연으로 요청 타임아웃
 * 원인: 외부 API 응답 지연, 네트워크 레이턴시, 타임아웃 설정 미흡
 * 로그 패턴: ETIMEDOUT, ESOCKETTIMEDOUT, timeout of Xms exceeded
 */

const https = require('https');

function triggerAPITimeout() {
  console.log('\n🔥 [CHAOS] Triggering API Timeout...\n');

  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    // 느린 외부 API 시뮬레이션 (실제로는 존재하지 않는 엔드포인트)
    const req = https.get('https://httpstat.us/200?sleep=10000', {
      timeout: 3000 // 3초 타임아웃
    }, (res) => {
      let data = '';

      res.on('data', chunk => {
        data += chunk;
      });

      res.on('end', () => {
        const responseTime = Date.now() - startTime;
        console.log(`[API] Response received: ${responseTime}ms`);
        resolve({ data, responseTime });
      });
    });

    req.on('timeout', () => {
      const responseTime = Date.now() - startTime;

      console.error('[API TIMEOUT ERROR] External API request timed out:', {
        timestamp: new Date().toISOString(),
        url: 'https://httpstat.us/200?sleep=10000',
        timeout: '3000ms',
        elapsed: `${responseTime}ms`,
        errorType: 'ETIMEDOUT'
      });

      console.error('\n🩺 Doctor should diagnose:');
      console.error('   - Root Cause: External API not responding within timeout period');
      console.error('   - Recommendation: Increase timeout or implement retry logic');
      console.error('   - Code Fix: Add circuit breaker pattern or fallback mechanism\n');

      req.destroy();
      resolve({
        scenario: 'API Timeout',
        timeout: '3000ms',
        elapsed: `${responseTime}ms`
      });
    });

    req.on('error', (error) => {
      const responseTime = Date.now() - startTime;

      console.error('[API ERROR] External API request failed:', {
        timestamp: new Date().toISOString(),
        error: error.message,
        code: error.code,
        elapsed: `${responseTime}ms`
      });

      resolve({
        scenario: 'API Error',
        error: error.message,
        code: error.code
      });
    });
  });
}

if (require.main === module) {
  triggerAPITimeout()
    .then(() => console.log('✅ Chaos scenario executed'))
    .catch(err => console.error('❌ Chaos scenario failed:', err))
    .finally(() => process.exit(0));
}

module.exports = { triggerAPITimeout };
