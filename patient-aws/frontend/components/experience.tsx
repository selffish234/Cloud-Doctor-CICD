import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Briefcase, GraduationCap } from "lucide-react"

export function Experience() {
  return (
    <section id="experience" className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-foreground mb-16 text-center">경력 및 교육</h2>

        <div className="space-y-8">
          {/* Current Training */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <Briefcase className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-xl font-semibold text-foreground">MSP 클라우드 솔루션 아키텍트 과정</h3>
                    <p className="text-muted-foreground">메가존 클라우드</p>
                  </div>
                  <Badge variant="secondary">진행 중</Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-3 leading-relaxed">
                  클라우드 인프라 설계, MSP 운영, 아키텍처 구축 등 실무 중심의 종합 교육 프로그램 참여 중
                </p>
              </div>
            </div>
          </Card>

          {/* Previous Work Experience */}
          <Card className="p-6">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-secondary/10 p-3">
                <Briefcase className="h-6 w-6 text-secondary" />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-xl font-semibold text-foreground">영어 강사</h3>
                    <p className="text-muted-foreground">Wise Reader</p>
                  </div>
                  <span className="text-sm text-muted-foreground">2023.03 - 2025.02</span>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  효과적인 커뮤니케이션과 교육 방법론 경험
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-secondary/10 p-3">
                <Briefcase className="h-6 w-6 text-secondary" />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-xl font-semibold text-foreground">HR/보상 사무 보조</h3>
                    <p className="text-muted-foreground">NEXON KOREA</p>
                  </div>
                  <span className="text-sm text-muted-foreground">2022.12 - 2023.02</span>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">인사 및 보상 업무 지원</p>
              </div>
            </div>
          </Card>

          {/* Education */}
          <Card className="p-6 bg-primary/5">
            <div className="flex items-start gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <GraduationCap className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <h3 className="text-xl font-semibold text-foreground">아주대학교</h3>
                    <p className="text-muted-foreground">비즈니스 인텔리전스 / 인공지능 융합 / 경영학</p>
                  </div>
                  <span className="text-sm text-muted-foreground">2019 - 2025</span>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  <Badge>비즈니스 인텔리전스</Badge>
                  <Badge>인공지능 융합</Badge>
                  <Badge>경영학</Badge>
                  <Badge variant="secondary">클라우드 융합 보안 (마이크로 디그리)</Badge>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  )
}
