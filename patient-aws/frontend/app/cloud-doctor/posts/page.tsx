'use client'

/**
 * Posts List Page - 게시글 목록 페이지
 */

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getPosts, getToken, getUser, logout, type Post } from '@/lib/cloud-doctor-api'

export default function PostsPage() {
  const router = useRouter()
  const [posts, setPosts] = useState<Post[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    // 사용자 정보 확인
    const currentUser = getUser()
    setUser(currentUser)

    // 게시글 목록 로드
    loadPosts()
  }, [])

  const loadPosts = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await getPosts(20, 0)

      if (response.error) {
        setError(response.error)
        return
      }

      if (response.data) {
        setPosts(response.data.posts)
      }
    } catch (err) {
      setError('게시글을 불러오는 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    setUser(null)
    router.push('/')
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* 헤더 */}
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">게시판</h1>

        <div className="flex items-center space-x-4">
          {user ? (
            <>
              <span className="text-gray-600">
                환영합니다, <strong>{user.name}</strong>님
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition"
              >
                로그아웃
              </button>
              <button
                onClick={() => router.push('/cloud-doctor/posts/new')}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
              >
                글쓰기
              </button>
            </>
          ) : (
            <button
              onClick={() => router.push('/cloud-doctor/login')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
            >
              로그인
            </button>
          )}
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* 로딩 */}
      {loading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">게시글을 불러오는 중...</p>
        </div>
      )}

      {/* 게시글 목록 */}
      {!loading && posts.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow-md">
          <p className="text-gray-600">아직 게시글이 없습니다.</p>
          {user && (
            <button
              onClick={() => router.push('/cloud-doctor/posts/new')}
              className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
            >
              첫 게시글 작성하기
            </button>
          )}
        </div>
      )}

      {!loading && posts.length > 0 && (
        <div className="space-y-4">
          {posts.map((post) => (
            <div
              key={post.id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition cursor-pointer"
              onClick={() => router.push(`/cloud-doctor/posts/${post.id}`)}
            >
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                {post.title}
              </h2>
              <p className="text-gray-600 line-clamp-2 mb-3">
                {post.content || '내용 없음'}
              </p>
              <div className="flex justify-between items-center text-sm text-gray-500">
                <span>
                  작성자: {post.author?.name || '익명'}
                </span>
                <span>
                  {post.createdAt ? new Date(post.createdAt).toLocaleDateString('ko-KR') : '날짜 없음'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
