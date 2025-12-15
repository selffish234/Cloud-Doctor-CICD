/**
 * 장애 시나리오 #1: DB 연결 실패
 *
 * 시나리오: 잘못된 RDS 엔드포인트 설정
 * 원인: 환경변수 오타, RDS 인스턴스 중지, 보안 그룹 차단
 * 로그 패턴: SequelizeConnectionError, ECONNREFUSED, ETIMEDOUT
 */

const { Sequelize } = require('sequelize');

async function triggerDBFailure() {
  console.log('\n🔥 [CHAOS] Triggering DB Connection Failure...\n');

  try {
    // 의도적으로 잘못된 DB 호스트로 연결 시도
    const fakeSequelize = new Sequelize('fake_db', 'admin', 'password', {
      host: 'wrong-db-endpoint.xxxx.eu-west-1.rds.amazonaws.com',
      port: 3306,
      dialect: 'mysql',
      pool: {
        max: 5,
        min: 0,
        acquire: 5000, // 5초 후 타임아웃
        idle: 1000
      },
      logging: false
    });

    await fakeSequelize.authenticate();

  } catch (error) {
    // 이 에러가 CloudWatch Logs에 기록됨
    console.error('[DB CONNECTION ERROR] Failed to connect to database:', {
      timestamp: new Date().toISOString(),
      error: error.message,
      errorName: error.name,
      code: error.parent?.code || 'UNKNOWN',
      errno: error.parent?.errno || 'N/A',
      sqlState: error.parent?.sqlState || 'N/A',
      host: 'wrong-db-endpoint.xxxx.eu-west-1.rds.amazonaws.com',
      port: 3306
    });

    console.error('\n🩺 Doctor should diagnose:');
    console.error('   - Root Cause: Invalid RDS endpoint or network issue');
    console.error('   - Recommendation: Check DB_HOST environment variable');
    console.error('   - Action: Verify RDS instance is running and security groups allow access\n');

    return {
      scenario: 'DB Connection Failure',
      error: error.message,
      code: error.parent?.code
    };
  }
}

// CLI에서 직접 실행 가능
if (require.main === module) {
  triggerDBFailure()
    .then(() => console.log('✅ Chaos scenario executed'))
    .catch(err => console.error('❌ Chaos scenario failed:', err))
    .finally(() => process.exit(0));
}

module.exports = { triggerDBFailure };
