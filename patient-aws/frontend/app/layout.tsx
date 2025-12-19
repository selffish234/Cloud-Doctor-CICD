import type React from "react"
import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"

const _geist = Geist({ subsets: ["latin"] })
const _geistMono = Geist_Mono({ subsets: ["latin"] })

// <CHANGE> SEO 메타데이터를 클라우드 엔지니어 포트폴리오에 맞게 업데이트
export const metadata: Metadata = {
  title: "김서준 - Cloud System Engineer Portfolio | Cloud Doctor MVP",
  description: "AWS + GCP 하이브리드 클라우드 모니터링 시스템. Vertex AI Gemini와 AWS Bedrock Claude를 활용한 비용 최적화 AI 아키텍처.",
  generator: "v0.app",
  keywords: ["Cloud Engineer", "AWS", "GCP", "Hybrid Cloud", "AI Monitoring", "Terraform", "클라우드 엔지니어", "김서준", "Cloud Doctor"],
  authors: [{ name: "김서준 (Seojoon Kim)" }],
  icons: {
    icon: [
      {
        url: "/icon-light-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/icon-dark-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/icon.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/apple-icon.png",
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body className={`font-sans antialiased`}>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
