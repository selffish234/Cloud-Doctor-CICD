'use client'

import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export function CloudDoctorSection() {
  return (
    <section className="py-20 px-4" id="cloud-doctor">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">
            🩺 Cloud Doctor MVP
          </h2>
          <p className="text-muted-foreground text-lg">
            AI 기반 하이브리드 클라우드 모니터링 시스템 (실제 작동 데모)
          </p>
        </div>

        <Card className="p-8 mb-8 bg-gradient-to-br from-blue-50 to-green-50 dark:from-blue-950 dark:to-green-950">
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-xl font-semibold mb-4">프로젝트 개요</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Megazone Cloud 최종 프로젝트로 개발한 AWS + GCP 하이브리드 클라우드 모니터링 시스템입니다.
                AI를 활용하여 장애를 자동 감지하고 Terraform 코드를 생성하여 자동 복구를 수행합니다.
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>✅ AWS 3-Tier 아키텍처 (CloudFront, ECS, RDS)</li>
                <li>✅ Terraform IaC 모듈화 구조</li>
                <li>✅ Vertex AI Gemini 로그 분석</li>
                <li>✅ Claude AI Terraform 코드 생성</li>
                <li>✅ 7가지 실제 장애 시나리오 구현</li>
              </ul>
            </div>
            <div>
              <h3 className="text-xl font-semibold mb-4">기술 스택</h3>
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="bg-white dark:bg-gray-800 rounded p-3">
                  <div className="text-xs font-semibold text-blue-600 mb-1">Patient Zone (AWS)</div>
                  <div className="text-xs text-muted-foreground">Next.js, Express, MySQL, ECS, CloudFront</div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded p-3">
                  <div className="text-xs font-semibold text-green-600 mb-1">Doctor Zone (GCP)</div>
                  <div className="text-xs text-muted-foreground">FastAPI, Vertex AI, Cloud Run</div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded p-3">
                  <div className="text-xs font-semibold text-purple-600 mb-1">IaC</div>
                  <div className="text-xs text-muted-foreground">Terraform, Modules</div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded p-3">
                  <div className="text-xs font-semibold text-orange-600 mb-1">AI</div>
                  <div className="text-xs text-muted-foreground">Gemini 2.0, Claude Sonnet 4.5</div>
                </div>
              </div>
              <div className="flex gap-4">
                <Link href="/cloud-doctor" className="flex-1">
                  <Button variant="default" className="w-full">
                    상세 설명 보기
                  </Button>
                </Link>
                <Link href="/cloud-doctor/posts" className="flex-1">
                  <Button variant="outline" className="w-full">
                    데모 체험하기
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </Card>

        <div className="grid md:grid-cols-3 gap-6">
          <Card className="p-6">
            <h4 className="font-semibold mb-2">🏗️ Infrastructure as Code</h4>
            <p className="text-sm text-muted-foreground">
              Terraform으로 모듈화된 AWS 3-Tier 인프라를 코드로 관리하고 재현 가능한 배포를 구현했습니다.
            </p>
          </Card>
          <Card className="p-6">
            <h4 className="font-semibold mb-2">🤖 AI 자동화</h4>
            <p className="text-sm text-muted-foreground">
              Gemini AI로 CloudWatch 로그를 분석하고, Claude AI로 Terraform 복구 코드를 자동 생성합니다.
            </p>
          </Card>
          <Card className="p-6">
            <h4 className="font-semibold mb-2">🔄 Hybrid Cloud</h4>
            <p className="text-sm text-muted-foreground">
              AWS (Patient Zone)와 GCP (Doctor Zone)를 연동한 하이브리드 클라우드 아키텍처를 구현했습니다.
            </p>
          </Card>
        </div>
      </div>
    </section>
  )
}
