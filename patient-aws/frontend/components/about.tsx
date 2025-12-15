import { Card } from "@/components/ui/card"
import { Code2, Cloud, Database, Shield, GraduationCap } from "lucide-react"

export function About() {
  const skills = [
    {
      icon: Cloud,
      title: "Cloud Platforms",
      description: "AWS, Azure 클라우드 플랫폼 경험",
    },
    {
      icon: Database,
      title: "Data & Analytics",
      description: "데이터 분석 및 비즈니스 인텔리전스",
    },
    {
      icon: Code2,
      title: "Infrastructure as Code",
      description: "인프라 자동화 및 코드형 관리",
    },
    {
      icon: Shield,
      title: "Security",
      description: "클라우드 보안 및 컴플라이언스",
    },
  ]

  const exchanges = [
    {
      university: "Rijksuniversiteit Groningen",
      location: "네덜란드",
      program: "Economics and Business Exchange",
      year: "2024",
    },
    {
      university: "亞洲大學 (Asia University)",
      location: "대만 타이중",
      program: "Language & Culture Summer Course",
      year: "2019",
    },
  ]

  return (
    <section id="about" className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-foreground mb-4 text-center">소개</h2>
        <p className="text-lg text-muted-foreground text-center mb-16 max-w-3xl mx-auto leading-relaxed">
          아주대학교에서 비즈니스 인텔리전스, 인공지능 융합, 경영학을 전공하고 클라우드 융합 보안 마이크로 디그리를
          이수하며 다양한 분야의 지식을 융합하는 능력을 키웠습니다. 현재는 클라우드 시스템 엔지니어로의 커리어를 위해
          메가존 클라우드에서 실무 중심의 교육을 받고 있습니다.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {skills.map((skill) => (
            <Card key={skill.title} className="p-6 hover:shadow-lg transition-shadow">
              <skill.icon className="h-10 w-10 text-primary mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">{skill.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{skill.description}</p>
            </Card>
          ))}
        </div>

        <div className="mt-20">
          <div className="flex items-center justify-center gap-2 mb-8">
            <GraduationCap className="h-8 w-8 text-primary" />
            <h3 className="text-3xl font-bold text-foreground text-center">교환학생 경험</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {exchanges.map((exchange) => (
              <Card key={exchange.university} className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start gap-3 mb-3">
                  <GraduationCap className="h-6 w-6 text-primary mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-foreground mb-1 leading-tight">{exchange.university}</h4>
                    <p className="text-sm text-muted-foreground mb-2">{exchange.location}</p>
                    <p className="text-sm text-foreground leading-relaxed">{exchange.program}</p>
                    <p className="text-xs text-muted-foreground mt-2">{exchange.year}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
