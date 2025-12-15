/**
 * 장애 시나리오 #3: 메모리 누수 (Memory Leak)
 *
 * 시나리오: 메모리 사용량 지속 증가로 OOM 발생
 * 원인: 캐싱 미제거, 이벤트 리스너 누적, 큰 객체 보관
 * 로그 패턴: JavaScript heap out of memory, FATAL ERROR
 */

function triggerMemoryLeak(durationSeconds = 30) {
  console.log(`\n🔥 [CHAOS] Triggering Memory Leak for ${durationSeconds} seconds...\n`);

  const leakedData = [];
  const startMemory = process.memoryUsage();
  let interval;

  // 메모리 모니터링
  const monitorInterval = setInterval(() => {
    const memUsage = process.memoryUsage();
    const heapUsedMB = (memUsage.heapUsed / 1024 / 1024).toFixed(2);
    const heapTotalMB = (memUsage.heapTotal / 1024 / 1024).toFixed(2);
    const usagePercent = ((memUsage.heapUsed / memUsage.heapTotal) * 100).toFixed(2);

    console.log(`[MEMORY USAGE] Heap: ${heapUsedMB}MB / ${heapTotalMB}MB (${usagePercent}%)`);

    // 임계값 경고
    if (usagePercent > 80) {
      console.error('[MEMORY WARNING] Heap usage exceeds 80%:', {
        timestamp: new Date().toISOString(),
        heapUsed: `${heapUsedMB}MB`,
        heapTotal: `${heapTotalMB}MB`,
        usagePercent: `${usagePercent}%`
      });
    }

    if (usagePercent > 90) {
      console.error('[MEMORY CRITICAL] Heap usage exceeds 90% - OOM risk:', {
        timestamp: new Date().toISOString(),
        heapUsed: `${heapUsedMB}MB`,
        heapTotal: `${heapTotalMB}MB`,
        usagePercent: `${usagePercent}%`
      });
    }
  }, 2000);

  // 의도적으로 메모리 누수 발생
  interval = setInterval(() => {
    // 큰 배열을 계속 생성하여 메모리 점유
    const chunk = new Array(100000).fill('x'.repeat(100));
    leakedData.push(chunk);

    console.log(`   Leaked data size: ${leakedData.length} chunks`);
  }, 500);

  // 지정 시간 후 정리
  setTimeout(() => {
    clearInterval(interval);
    clearInterval(monitorInterval);

    const endMemory = process.memoryUsage();
    const memoryIncrease = ((endMemory.heapUsed - startMemory.heapUsed) / 1024 / 1024).toFixed(2);

    console.log('\n📊 Memory Leak Report:');
    console.log(`   Start: ${(startMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
    console.log(`   End: ${(endMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
    console.log(`   Increase: +${memoryIncrease}MB`);

    console.error('\n🩺 Doctor should diagnose:');
    console.error('   - Root Cause: Memory leak detected - heap usage continuously increasing');
    console.error('   - Recommendation: Review code for unreleased references or caching issues');
    console.error('   - Terraform Fix: Increase ECS task memory from 512MB to 1GB\n');

    // 정리
    leakedData.length = 0;

    if (require.main === module) {
      process.exit(0);
    }
  }, durationSeconds * 1000);
}

if (require.main === module) {
  triggerMemoryLeak(30);
}

module.exports = { triggerMemoryLeak };
