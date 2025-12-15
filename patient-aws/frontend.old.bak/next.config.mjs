/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',

  // CloudFront + S3 배포를 위한 설정
  images: {
    unoptimized: true // S3에서는 이미지 최적화 비활성화
  },

  // 환경변수 노출 (클라이언트 사이드)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || ''  // CloudFront same-origin 요청
  }
};

export default nextConfig;
