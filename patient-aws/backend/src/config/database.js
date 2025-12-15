/**
 * Database Configuration - RDS MySQL Connection
 *
 * Sequelize ORM을 사용하여 RDS MySQL에 연결합니다.
 * Connection Pool 설정으로 성능 최적화 및 장애 대응
 */

const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
  process.env.DB_NAME,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT || 3306,
    dialect: 'mysql',

    // Connection Pool 설정 (중요!)
    pool: {
      max: 10,        // 최대 연결 수
      min: 2,         // 최소 연결 수
      acquire: 30000, // 연결 획득 타임아웃 (30초)
      idle: 10000     // 유휴 연결 유지 시간 (10초)
    },

    // 로깅 설정
    logging: process.env.NODE_ENV === 'development' ? console.log : false,

    // Timezone 설정
    timezone: '+09:00',

    // 재시도 설정
    retry: {
      max: 3,
      match: [
        /SequelizeConnectionError/,
        /SequelizeConnectionRefusedError/,
        /SequelizeHostNotFoundError/,
        /SequelizeHostNotReachableError/,
        /SequelizeInvalidConnectionError/,
        /SequelizeConnectionTimedOutError/
      ]
    },

    // 성능 최적화
    define: {
      charset: 'utf8mb4',
      collate: 'utf8mb4_unicode_ci',
      timestamps: true,
      underscored: true // snake_case 컬럼명 사용
    }
  }
);

/**
 * 데이터베이스 연결 테스트
 */
async function testConnection() {
  try {
    await sequelize.authenticate();
    console.log('✅ Database connection established successfully.');
    console.log(`   Host: ${process.env.DB_HOST}`);
    console.log(`   Database: ${process.env.DB_NAME}`);
    return true;
  } catch (error) {
    console.error('❌ Unable to connect to the database:', error.message);
    console.error('   Error Code:', error.parent?.code || 'UNKNOWN');
    console.error('   Error Number:', error.parent?.errno || 'N/A');

    // CloudWatch Logs에 기록될 에러 로그 (Doctor가 분석할 데이터)
    console.error('[DB CONNECTION ERROR]', {
      timestamp: new Date().toISOString(),
      host: process.env.DB_HOST,
      error: error.message,
      code: error.parent?.code,
      errno: error.parent?.errno
    });

    return false;
  }
}

/**
 * 데이터베이스 초기화 (테이블 생성)
 */
async function initDatabase() {
  try {
    // 모델 동기화 (테이블이 없으면 생성)
    await sequelize.sync({ alter: false }); // Production에서는 alter: false
    console.log('✅ Database tables synchronized.');
  } catch (error) {
    console.error('❌ Failed to sync database:', error.message);
    throw error;
  }
}

module.exports = {
  sequelize,
  testConnection,
  initDatabase
};
