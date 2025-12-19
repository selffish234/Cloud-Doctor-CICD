'use client'

/**
 * Cloud Doctor Demo - 소개 페이지
 */

import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function CloudDoctorPage() {
  return (
    <div className="min-h-screen bg-background py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            🩺 Cloud Doctor MVP
          </h1>
          <p className="text-xl text-muted-foreground mb-8">
            AWS + GCP Hybrid Cloud Monitoring System
          </p>
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            AI 기반 하이브리드 클라우드 모니터링 및 자동화 시스템 - 비용 최적화된 듀얼 AI 아키텍처
          </p>
        </div>

        {/* Architecture */}
        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-6">시스템 아키텍처</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-blue-600 mb-3">
                Patient Zone (AWS)
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>📍 <strong>Frontend:</strong> Next.js 15 (CloudFront + S3)</li>
                <li>📍 <strong>Backend:</strong> Node.js + Express (ECS Fargate)</li>
                <li>📍 <strong>Database:</strong> MySQL 8.0 (RDS)</li>
                <li>📍 <strong>Monitoring:</strong> CloudWatch Logs</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-green-600 mb-3">
                Doctor Zone (GCP)
              </h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>🔍 <strong>AI Analysis:</strong> Vertex AI Gemini 2.0 (GCP 크레딧)</li>
                <li>🛠️ <strong>IaC Generation:</strong> AWS Bedrock Claude Sonnet 4 (AWS 예산)</li>
                <li>📢 <strong>ChatOps:</strong> Slack Webhook + Slash Commands</li>
                <li>☁️ <strong>Platform:</strong> Cloud Run (Serverless)</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Features */}
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-3">🔥 장애 시뮬레이션</h3>
            <p className="text-sm text-muted-foreground">
              7가지 실제 운영 장애 시나리오를 구현하여 AI 분석 및 자동화 테스트
            </p>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-3">💰 비용 최적화 AI</h3>
            <p className="text-sm text-muted-foreground">
              GCP 크레딧(Gemini) + AWS 예산(Bedrock Claude) 활용. API Key 불필요!
            </p>
          </Card>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-3">🏗️ CI/CD 자동화</h3>
            <p className="text-sm text-muted-foreground">
              GitHub Actions로 Terraform + ECS + S3 배포 완전 자동화
            </p>
          </Card>
        </div>

        {/* Demo Sections */}
        <Card className="p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-6">데모 체험하기</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-3">게시판 기능</h3>
              <p className="text-sm text-muted-foreground mb-4">
                3-Tier 아키텍처로 구현된 게시판 앱을 체험해보세요.
                회원가입, 로그인, 게시글 작성 등 기본 CRUD 기능을 제공합니다.
              </p>
              <Link href="/cloud-doctor/posts">
                <Button className="w-full">게시판 바로가기</Button>
              </Link>
            </div>
            <div className="border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-3">장애 시뮬레이션</h3>
              <p className="text-sm text-muted-foreground mb-4">
                의도적인 장애를 발생시켜 CloudWatch Logs를 생성하고,
                Doctor Zone에서 AI 분석 및 자동 복구를 테스트합니다.
              </p>
              <Button variant="outline" className="w-full" disabled>
                준비 중
              </Button>
            </div>
          </div>
        </Card>

        {/* Tech Stack */}
        <Card className="p-8">
          <h2 className="text-2xl font-semibold mb-6">기술 스택</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm font-semibold mb-1">Frontend</div>
              <div className="text-xs text-muted-foreground">Next.js, TypeScript</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-semibold mb-1">Backend</div>
              <div className="text-xs text-muted-foreground">Express, Sequelize</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-semibold mb-1">Infrastructure</div>
              <div className="text-xs text-muted-foreground">Terraform, GitHub Actions</div>
            </div>
            <div className="text-center">
              <div className="text-sm font-semibold mb-1">AI/ML</div>
              <div className="text-xs text-muted-foreground">Vertex AI, Bedrock</div>
            </div>
          </div>
        </Card>

        {/* Back Button */}
        <div className="text-center mt-8">
          <Link href="/">
            <Button variant="outline">← 포트폴리오 홈으로</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
