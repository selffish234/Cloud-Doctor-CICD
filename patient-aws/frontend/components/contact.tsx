import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Linkedin, Github, MapPin, Languages } from "lucide-react"

export function Contact() {
  return (
    <section id="contact" className="py-24 px-4 sm:px-6 lg:px-8 bg-muted/30">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-4xl font-bold text-foreground mb-4 text-center">연락하기</h2>
        <p className="text-lg text-muted-foreground text-center mb-16 max-w-2xl mx-auto leading-relaxed">
          클라우드 프로젝트나 협업 기회에 관심이 있으시다면 언제든 연락 주세요.
        </p>

        <Card className="p-8">
          <div className="space-y-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <MapPin className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">위치</p>
                <p className="text-sm text-muted-foreground">화성, 경기도, 대한민국</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-primary/10 p-3">
                <Languages className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">언어</p>
                <p className="text-sm text-muted-foreground">한국어 (원어민), 영어 (전문가 수준)</p>
              </div>
            </div>

            <div className="pt-6 border-t border-border">
              <div className="flex flex-wrap gap-4">
                <Button asChild className="flex-1 min-w-[200px]">
                  <a href="https://www.linkedin.com/in/selffish234" target="_blank" rel="noopener noreferrer">
                    <Linkedin className="h-4 w-4 mr-2" />
                    LinkedIn
                  </a>
                </Button>
                <Button asChild variant="outline" className="flex-1 min-w-[200px] bg-transparent">
                  <a href="https://github.com/selffish234" target="_blank" rel="noopener noreferrer">
                    <Github className="h-4 w-4 mr-2" />
                    GitHub
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </Card>

        <div className="mt-12 text-center">
          <p className="text-sm text-muted-foreground">© 2025 Seojoon Kim. All rights reserved.</p>
        </div>
      </div>
    </section>
  )
}
