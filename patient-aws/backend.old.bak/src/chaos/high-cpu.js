/**
 * 장애 시나리오 #7: 높은 CPU 사용률
 *
 * 시나리오: 무한 루프 또는 비효율적인 알고리즘으로 CPU 100%
 * 원인: 잘못된 코드 로직, 대용량 데이터 처리, 동기 블로킹
 * 로그 패턴: CPU usage: XX%, Event loop blocked
 */

function cpuIntensiveTask(iterations = 10000000) {
  console.log(`   Running CPU-intensive calculation (${iterations} iterations)...`);

  let result = 0;
  for (let i = 0; i < iterations; i++) {
    // 복잡한 계산 (CPU 집약적)
    result += Math.sqrt(i) * Math.sin(i) * Math.cos(i);

    // 매 100만 번마다 진행 상황 출력
    if (i % 1000000 === 0 && i > 0) {
      console.log(`   Progress: ${((i / iterations) * 100).toFixed(1)}%`);
    }
  }

  return result;
}

function triggerHighCPU(durationSeconds = 30) {
  console.log(`\n🔥 [CHAOS] Triggering High CPU Usage for ${durationSeconds} seconds...\n`);

  const startTime = Date.now();
  let taskCount = 0;

  // CPU 모니터링
  const monitorInterval = setInterval(() => {
    const cpuUsage = process.cpuUsage();
    const elapsedTime = (Date.now() - startTime) / 1000;

    console.log(`[CPU USAGE] Elapsed: ${elapsedTime.toFixed(1)}s | Tasks completed: ${taskCount}`);

    // 높은 CPU 사용 경고
    console.warn('[CPU WARNING] High CPU usage detected:', {
      timestamp: new Date().toISOString(),
      elapsedTime: `${elapsedTime.toFixed(1)}s`,
      userCPU: `${(cpuUsage.user / 1000000).toFixed(2)}s`,
      systemCPU: `${(cpuUsage.system / 1000000).toFixed(2)}s`,
      tasksCompleted: taskCount
    });

  }, 2000);

  // CPU 집약적 작업 반복
  const cpuInterval = setInterval(() => {
    const result = cpuIntensiveTask(5000000);
    taskCount++;

    console.error('[PERFORMANCE ERROR] CPU-intensive task completed:', {
      timestamp: new Date().toISOString(),
      taskNumber: taskCount,
      result: result.toFixed(2),
      warning: 'Blocking event loop'
    });

  }, 1000);

  // 지정 시간 후 종료
  setTimeout(() => {
    clearInterval(cpuInterval);
    clearInterval(monitorInterval);

    const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);

    console.log(`\n📊 CPU Load Report:`);
    console.log(`   Duration: ${totalTime}s`);
    console.log(`   Tasks completed: ${taskCount}`);

    console.error('\n🩺 Doctor should diagnose:');
    console.error('   - Root Cause: CPU usage at 100% - inefficient algorithm or blocking operation');
    console.error('   - Recommendation: Optimize code or move to worker threads');
    console.error('   - Terraform Fix: Increase ECS task CPU allocation\n');

    if (require.main === module) {
      process.exit(0);
    }
  }, durationSeconds * 1000);
}

if (require.main === module) {
  triggerHighCPU(30);
}

module.exports = { triggerHighCPU };
