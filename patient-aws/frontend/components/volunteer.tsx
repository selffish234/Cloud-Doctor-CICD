import { Card } from "@/components/ui/card"
import { Heart, Code, Users } from "lucide-react"

export function Volunteer() {
  return (
    <section id="volunteer" className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-foreground mb-4 text-center">봉사 활동</h2>
        <p className="text-lg text-muted-foreground text-center mb-16 max-w-3xl mx-auto leading-relaxed">
          교육을 통한 사회 기여 활동
        </p>

        <Card className="p-8 hover:shadow-lg transition-shadow">
          <div className="flex items-start gap-4">
            <div className="rounded-lg bg-primary/10 p-3">
              <Code className="h-8 w-8 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="text-2xl font-semibold text-foreground mb-2">고등학생 대상 Python 튜터링</h3>
              <div className="flex items-center gap-2 mb-4">
                <p className="text-sm text-muted-foreground">아주대학교</p>
                <span className="text-sm text-muted-foreground">•</span>
                <p className="text-sm text-muted-foreground">2025.03 - 2025.07 • 5개월</p>
              </div>
              <p className="text-muted-foreground leading-relaxed mb-6">
                고등학생들을 대상으로 Python 프로그래밍의 기초를 가르치는 교육 봉사 활동을 수행했습니다. 핵심 개념
                설명과 실습 중심의 코딩 연습을 통해 학생들의 프로그래밍 역량 향상을 지원했습니다.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3">
                  <Heart className="h-5 w-5 text-primary" />
                  <span className="text-sm text-muted-foreground">교육 봉사</span>
                </div>
                <div className="flex items-center gap-3">
                  <Code className="h-5 w-5 text-primary" />
                  <span className="text-sm text-muted-foreground">Python 기초</span>
                </div>
                <div className="flex items-center gap-3">
                  <Users className="h-5 w-5 text-primary" />
                  <span className="text-sm text-muted-foreground">실습 지도</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </section>
  )
}
