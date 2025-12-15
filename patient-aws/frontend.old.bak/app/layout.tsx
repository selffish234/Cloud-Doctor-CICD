'use client'

import Link from 'next/link'
import './globals.css'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16 items-center">
              <div className="flex items-center">
                <Link href="/" className="text-xl font-bold text-blue-600">
                  🩺 Patient Board
                </Link>
              </div>
              <div className="flex space-x-4">
                <Link href="/posts" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md">
                  게시판
                </Link>
                <Link href="/login" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md">
                  로그인
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main>{children}</main>
        <footer className="bg-white border-t mt-12">
          <div className="max-w-7xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
            Cloud Doctor Patient Zone - Made for Megazone Cloud
          </div>
        </footer>
      </body>
    </html>
  )
}
