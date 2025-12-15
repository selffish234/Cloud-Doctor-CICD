/**
 * Cloud Doctor API Client - Backend API 호출 유틸리티
 *
 * Backend (CloudFront → ALB) 연동을 위한 Fetch Wrapper
 */

// CloudFront에서 /api/* 경로를 ALB로 프록시하므로 빈 문자열 사용 (same-origin)
const API_URL = '';

/**
 * API 응답 타입
 */
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

/**
 * 사용자 타입
 */
export interface User {
  id: number;
  email: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * 게시글 타입
 */
export interface Post {
  id: number;
  user_id: number;
  title: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  author?: User;
}

/**
 * 인증 응답 타입
 */
export interface AuthResponse {
  message: string;
  token: string;
  user: User;
}

/**
 * 게시글 목록 응답 타입
 */
export interface PostsResponse {
  posts: Post[];
  count: number;
  queryTime?: string;
}

/**
 * Fetch Wrapper - 공통 에러 처리
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_URL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        error: data.error || 'Request failed',
        status: response.status,
      };
    }

    return {
      data,
      status: response.status,
    };
  } catch (error) {
    console.error('API Error:', error);
    return {
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * ===== 인증 API =====
 */

/**
 * 회원가입
 */
export async function register(
  email: string,
  password: string,
  name: string
): Promise<ApiResponse<{ message: string; user: User }>> {
  return fetchAPI('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });
}

/**
 * 로그인
 */
export async function login(
  email: string,
  password: string
): Promise<ApiResponse<AuthResponse>> {
  return fetchAPI('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

/**
 * 토큰 검증
 */
export async function verifyToken(
  token: string
): Promise<ApiResponse<{ valid: boolean; user: any }>> {
  return fetchAPI('/api/auth/verify', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

/**
 * ===== 게시글 API =====
 */

/**
 * 게시글 목록 조회
 */
export async function getPosts(
  limit = 10,
  offset = 0
): Promise<ApiResponse<PostsResponse>> {
  return fetchAPI(`/api/posts?limit=${limit}&offset=${offset}`);
}

/**
 * 게시글 상세 조회
 */
export async function getPost(id: number): Promise<ApiResponse<Post>> {
  return fetchAPI(`/api/posts/${id}`);
}

/**
 * 게시글 작성 (인증 필요)
 */
export async function createPost(
  title: string,
  content: string,
  token: string
): Promise<ApiResponse<Post>> {
  return fetchAPI('/api/posts', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ title, content }),
  });
}

/**
 * 게시글 삭제 (인증 필요)
 */
export async function deletePost(
  id: number,
  token: string
): Promise<ApiResponse<{ message: string }>> {
  return fetchAPI(`/api/posts/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

/**
 * ===== 헬스체크 API =====
 */

/**
 * 헬스체크
 */
export async function checkHealth(): Promise<ApiResponse<any>> {
  return fetchAPI('/health');
}

/**
 * ===== 로컬 스토리지 유틸 =====
 */

/**
 * 토큰 저장
 */
export function saveToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('auth_token', token);
  }
}

/**
 * 토큰 가져오기
 */
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('auth_token');
  }
  return null;
}

/**
 * 토큰 삭제 (로그아웃)
 */
export function removeToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token');
  }
}

/**
 * 사용자 정보 저장
 */
export function saveUser(user: User) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('user', JSON.stringify(user));
  }
}

/**
 * 사용자 정보 가져오기
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }
  return null;
}

/**
 * 사용자 정보 삭제
 */
export function removeUser() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('user');
  }
}

/**
 * 로그아웃 (토큰 + 사용자 정보 삭제)
 */
export function logout() {
  removeToken();
  removeUser();
}
