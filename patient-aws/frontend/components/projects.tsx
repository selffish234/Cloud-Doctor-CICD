import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Server,
  Eye,
  Route,
  Briefcase,
  Activity,
  Shield,
  Zap,
  Users,
  Database,
  Figma,
  BarChart3,
  Brain,
  Apple,
} from "lucide-react"

export function Projects() {
  const projects = [
    {
      icon: Server,
      title: "Spike in Traffic 대응 3 + α Tier 아키텍처",
      description:
        "트래픽 급증에 대응하기 위한 온프레미스 3-Tier 아키텍처 설계 및 구현. 로드 밸런싱, 캐싱, 데이터베이스 최적화를 통한 고가용성 시스템 구축.",
      period: "2024 - 2025",
      tags: ["Architecture", "On-Premise", "Load Balancing", "High Availability"],
      status: "중간 프로젝트 완료",
      highlights: ["고가용성", "성능 최적화", "보안 강화"],
      icons: [Activity, Zap, Shield],
    },
    {
      icon: Eye,
      title: "EyeCanTouch - 아이트래킹 키오스크",
      description:
        "시선 추적 기술과 얼굴 인식 기반의 접근성 개선 키오스크 시스템. Beam Eye Tracker SDK를 활용한 실시간 시선 추적과 OpenCV 기반 자동 UI 전환 기능 구현으로 장애인과 휠체어 사용자의 키오스크 접근성을 획기적으로 개선.",
      period: "2025.01 - 2025.06",
      tags: ["AI", "Accessibility", "Eye-Tracking", "OpenCV", "Python", "Flask"],
      status: "완료 (AI융합캡스톤디자인2)",
      highlights: ["PM 역할", "아이트래킹 구현", "UI/UX 설계"],
      icons: [Users, Eye, Figma],
      details: [
        "Beam Eye Tracker SDK를 활용한 실시간 시선 추적 시스템 구현",
        "PyAutoGUI 기반 Dwell Time 클릭 기능 개발",
        "OpenCV를 이용한 얼굴 인식 기반 자동 UI 모드 전환 로직 구현",
        "Flask 기반 웹 키오스크 인터페이스 개발 (HTML/CSS)",
        "전체 시스템 통합 및 실행 파이프라인 구축",
      ],
    },
    {
      icon: Route,
      title: "러닝 타임 - AI 기반 러닝 경로 추천 앱",
      description:
        "K-means 클러스터링과 KNN 알고리즘을 활용한 위치 기반 러닝 코스 추천 서비스의 전체 시스템 기획, 분석 및 설계. 사용자 시나리오 분석부터 아키텍처 설계, 알고리즘 설계까지 전 과정을 수행.",
      period: "2024.09 - 2024.12",
      tags: ["System Design", "Algorithm Design", "K-means", "KNN", "A* Algorithm", "UML"],
      status: "완료 (AI융합캡스톤디자인1)",
      highlights: ["전체 시스템 설계", "알고리즘 설계", "UML 모델링"],
      icons: [Activity, Server, Database],
      details: [
        "디자인 씽킹 기법을 활용한 문제 정의 및 사용자 니즈 분석",
        "K-means 클러스터링 기반 경로 추천 알고리즘 설계",
        "KNN 협업 필터링을 활용한 맞춤형 추천 시스템 설계",
        "A* 알고리즘을 이용한 최적 경로 탐색 로직 설계",
        "유즈케이스, 액티비티, 클래스, 시퀀스 다이어그램 작성",
        "Google Maps/T-Map API 연동 아키텍처 설계",
      ],
    },
    {
      icon: Briefcase,
      title: "파피팰리스 IT 시스템 구축 프로젝트",
      description:
        "반려견 엔터테인먼트 기업의 디지털 전환 프로젝트. PM으로서 전체 프로젝트 기획, 비즈니스 분석, UI/UX 설계를 담당하며 오프라인 중심 업무를 웹 기반 시스템으로 전환.",
      period: "2025.03 - 2025.06",
      tags: ["PM", "UI/UX", "Figma", "Business Analysis", "Database Design"],
      status: "완료 (e-비즈니스 캡스톤디자인)",
      highlights: ["PM 역할", "비즈니스 케이스 분석", "전체 프로세스 설계"],
      icons: [Users, Figma, Database],
      details: [
        "프로젝트 전체 일정 및 범위 관리 (WBS 작성)",
        "비즈니스 케이스 분석 및 투자 대비 효과 산출",
        "유즈케이스 및 프로세스 다이어그램 작성",
        "Figma를 활용한 고객용/직원용 웹사이트 UI 디자인",
        "DB팀과 UI팀 간 협업 조율 및 데이터 연동 설계",
      ],
    },
    {
      icon: BarChart3,
      title: "Spotify 차트 스트리밍 요인 분석",
      description:
        "다중 회귀 분석을 통한 한국 & 글로벌 Spotify 주간 상위 200위 차트의 스트리밍 횟수 영향 요인 비교 분석. R을 활용하여 두 차트 간 스트리밍 성공 요인의 상대적 차이를 통계적으로 규명.",
      period: "2024.09 - 2024.12",
      tags: ["R", "Data Analysis", "Multiple Regression", "Statistical Analysis", "Spotify API"],
      status: "완료 (데이터 애널리틱스)",
      highlights: ["통계 분석", "API 활용", "데이터 시각화"],
      icons: [BarChart3, Database, Activity],
      details: [
        "Spotify API를 활용한 음악 메타데이터 수집 및 전처리",
        "K-means 클러스터링과 다중 회귀 분석 모델 구축",
        "글로벌 차트: popularity, artist_popularity, speechiness가 주요 영향 요인으로 도출",
        "한국 차트: popularity, energy, speechiness, label_country가 유의미한 변수로 확인",
        "두 시장 간 음악 청취 패턴의 명확한 차이 발견",
      ],
    },
    {
      icon: Brain,
      title: "자폐 스펙트럼 장애 예측 모델",
      description:
        "머신러닝을 활용한 자폐 스펙트럼 장애(ASD) 조기 진단 예측 모델 개발. Stepwise Selection, 릿지/라쏘 회귀, PCA 등 다양한 기법을 적용하여 최적 모델을 도출하고 AUC 1.0을 달성.",
      period: "2024.12",
      tags: ["R", "Machine Learning", "Lasso Regression", "PCA", "AUC Optimization"],
      status: "완료 (데이터 애널리틱스 기말)",
      highlights: ["모델 최적화", "AUC 1.0 달성", "통계적 검증"],
      icons: [Brain, BarChart3, Shield],
      details: [
        "A1~A10 Score 변수 기반 로지스틱 회귀 모델 구축",
        "stepAIC를 통한 최적 독립변수 선택 (AIC 20 달성)",
        "K-Fold 교차 검증으로 모델 신뢰성 확보 (오차율 4.45%)",
        "릿지(AUC 0.983), 라쏘(AUC 1.0), PCA(AUC 1.0) 회귀 모델 비교 분석",
        "해석 가능성을 고려하여 라쏘 회귀를 최종 모델로 선정",
      ],
    },
    {
      icon: Apple,
      title: "스마트팜 고당도 사과 생산 및 신선도 분류",
      description:
        "XAI 기반 스마트팜 환경 변수 최적화와 CV 기반 과일 신선도 분류 시스템 개발. XGBoost + SHAP/LIME으로 당도 예측 모델을 구축하고, CNN으로 신선도 분류 모델을 활용하여 농업의 디지털 전환 사례를 제시.",
      period: "2024.11 - 2024.12",
      tags: ["XAI", "XGBoost", "SHAP", "CNN", "Computer Vision", "Smart Farm"],
      status: "완료 (인공지능기초 기말)",
      highlights: ["XAI 적용", "CV 모델 활용", "농업 AI"],
      icons: [Apple, Brain, Activity],
      details: [
        "AI Hub 장수 사과 품질 데이터 기반 XGBoost 모델 구축 (정확도 0.87)",
        "SHAP와 LIME을 활용한 XAI 적용으로 토양 습도, 일조시간 등 핵심 변수 도출",
        "Kaggle 신선도 데이터셋 10,901장 기반 CNN 모델 활용",
        "훈련 95%, 검증 92%, 테스트 90% 정확도 달성",
        "Streamlit 웹 기반 신선도 분류 서비스 구현 및 시연",
        "경험재를 탐색재로 전환하는 혁신적 접근법 제시",
      ],
    },
  ]

  return (
    <section id="projects" className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-foreground mb-4 text-center">프로젝트</h2>
        <p className="text-lg text-muted-foreground text-center mb-16 max-w-3xl mx-auto leading-relaxed">
          클라우드 아키텍처 설계부터 AI/ML 기반 데이터 분석, PM 경험까지
          <br />
          다양한 도메인에서 실전 프로젝트를 수행했습니다.
        </p>

        <div className="grid grid-cols-1 gap-8">
          {projects.map((project) => (
            <Card key={project.title} className="p-8 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4 mb-4">
                <div className="rounded-lg bg-primary/10 p-3">
                  <project.icon className="h-8 w-8 text-primary" />
                </div>
                <div className="flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                    <h3 className="text-2xl font-semibold text-foreground text-balance">{project.title}</h3>
                    <Badge variant="secondary">{project.status}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">{project.period}</p>
                </div>
              </div>

              <p className="text-muted-foreground mb-4 leading-relaxed">{project.description}</p>

              {project.details && (
                <div className="mb-6 space-y-2">
                  <p className="text-sm font-semibold text-foreground mb-2">주요 성과:</p>
                  <ul className="space-y-1">
                    {project.details.map((detail, index) => (
                      <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span className="leading-relaxed">{detail}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex flex-wrap gap-2 mb-6">
                {project.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {project.highlights.map((highlight, index) => (
                  <div key={highlight} className="flex items-center gap-3">
                    {project.icons[index] && (
                      <>
                        {(() => {
                          const IconComponent = project.icons[index]
                          return <IconComponent className="h-5 w-5 text-primary" />
                        })()}
                      </>
                    )}
                    <span className="text-sm text-muted-foreground">{highlight}</span>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
