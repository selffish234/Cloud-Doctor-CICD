/**
 * 장애 시나리오 #2: DB Connection Pool 고갈
 *
 * 시나리오: 동시 요청 폭주로 커넥션 풀 고갈
 * 원인: 트래픽 급증, Pool 크기 부족, 연결 미반환
 * 로그 패턴: ResourceRequest timed out, SequelizeConnectionAcquireTimeoutError
 */

const { sequelize } = require('../config/database');

async function triggerPoolExhaustion() {
  console.log('\n🔥 [CHAOS] Triggering Connection Pool Exhaustion...\n');

  const connections = [];
  const poolSize = 10; // 현재 pool.max 설정값
  const overloadFactor = 3; // 3배 초과 요청

  try {
    // Pool 크기의 3배 연결 시도
    for (let i = 0; i < poolSize * overloadFactor; i++) {
      console.log(`   Creating connection ${i + 1}/${poolSize * overloadFactor}...`);

      const promise = sequelize.query('SELECT SLEEP(5) as result')
        .then(() => console.log(`   ✓ Connection ${i + 1} completed`))
        .catch(error => {
          console.error(`[POOL ERROR] Connection ${i + 1} failed:`, {
            timestamp: new Date().toISOString(),
            error: error.message,
            errorName: error.name,
            connectionNumber: i + 1,
            poolMax: poolSize
          });
        });

      connections.push(promise);

      // 짧은 간격으로 연결 시도
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // 모든 연결 완료 대기
    await Promise.allSettled(connections);

  } catch (error) {
    console.error('[POOL EXHAUSTION ERROR] Connection pool overwhelmed:', {
      timestamp: new Date().toISOString(),
      error: error.message,
      errorName: error.name,
      totalAttempts: poolSize * overloadFactor,
      poolMax: poolSize
    });

    console.error('\n🩺 Doctor should diagnose:');
    console.error('   - Root Cause: Connection pool exhausted under heavy load');
    console.error('   - Recommendation: Increase ECS task count or DB pool size');
    console.error('   - Terraform Fix: Update pool.max in database config\n');

    return {
      scenario: 'Pool Exhaustion',
      error: error.message,
      poolSize,
      attempts: poolSize * overloadFactor
    };
  }
}

if (require.main === module) {
  triggerPoolExhaustion()
    .then(() => console.log('✅ Chaos scenario executed'))
    .catch(err => console.error('❌ Chaos scenario failed:', err))
    .finally(() => process.exit(0));
}

module.exports = { triggerPoolExhaustion };
