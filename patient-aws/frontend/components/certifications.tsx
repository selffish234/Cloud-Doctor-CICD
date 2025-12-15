import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Award, ExternalLink } from "lucide-react"

export function Certifications() {
  const certifications = [
    {
      name: "AWS Certified Cloud Practitioner",
      issuer: "Amazon Web Services (AWS)",
      date: "2025.02",
      credential: "https://www.credly.com/badges/58633a7b-7117-424d-a51f-aa9cb507fb79/public_url",
      category: "Cloud",
    },
    {
      name: "Microsoft Certified: Azure Fundamentals",
      issuer: "Microsoft",
      date: "2024.08",
      credential: "https://learn.microsoft.com/api/credentials/share/ko-kr/SeojoonKim-1367/B3660077E944544",
      category: "Cloud",
    },
    {
      name: "데이터 분석 준전문가 (ADsP)",
      issuer: "한국데이터산업진흥원",
      date: "2023.11",
      category: "Data",
    },
    {
      name: "SQL 개발자 (SQLD)",
      issuer: "한국데이터산업진흥원",
      date: "2023.07",
      category: "Data",
    },
    {
      name: "Google Analytics Certification",
      issuer: "Google",
      date: "2024.08",
      credential: "https://skillshop.credential.net/1493d9ea-8e2f-42de-b0c5-1533ca506e15",
      category: "Analytics",
    },
  ]

  return (
    <section id="certifications" className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-4xl font-bold text-foreground mb-4 text-center">자격증</h2>
        <p className="text-lg text-muted-foreground text-center mb-16 max-w-3xl mx-auto leading-relaxed">
          클라우드, 데이터 분석, 보안 등 다양한 분야의 전문 자격증을 보유하고 있습니다.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {certifications.map((cert) => (
            <Card key={cert.name} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start gap-4">
                <div className="rounded-lg bg-primary/10 p-3">
                  <Award className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-foreground">{cert.name}</h3>
                    <Badge>{cert.category}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-1">{cert.issuer}</p>
                  <p className="text-sm text-muted-foreground mb-3">{cert.date}</p>
                  {cert.credential && (
                    <a
                      href={cert.credential}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                    >
                      자격증 확인
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  )
}
