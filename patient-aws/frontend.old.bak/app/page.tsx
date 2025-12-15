'use client'

/**
 * Home Page - 메인 페이지
 */

import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🩺 Cloud Doctor Patient Zone
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          AWS 3-Tier Architecture Board Application
        </p>

        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-4">시스템 구조</h2>
          <div className="text-left space-y-2 text-gray-700">
            <p>📍 <strong>Frontend:</strong> Next.js 15 (CloudFront + S3)</p>
            <p>📍 <strong>Backend:</strong> Node.js + Express (ECS Fargate)</p>
            <p>📍 <strong>Database:</strong> MySQL 8.0 (RDS)</p>
            <p>📍 <strong>Monitoring:</strong> CloudWatch Logs</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Link
            href="/posts"
            className="block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg transition"
          >
            📝 게시판 바로가기
          </Link>
          <Link
            href="/login"
            className="block bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-6 rounded-lg transition"
          >
            🔐 로그인 / 회원가입
          </Link>
        </div>

        <div className="mt-12 p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="text-lg font-semibold text-yellow-800 mb-2">
            ⚠️ 장애 시뮬레이션 환경
          </h3>
          <p className="text-yellow-700">
            이 애플리케이션은 Cloud Doctor가 분석할 장애 로그를 생성하기 위한 테스트 환경입니다.
            <br />
            실제 운영 환경에서는 의도적인 에러가 발생하지 않습니다.
          </p>
        </div>
      </div>
    </div>
  )
}
