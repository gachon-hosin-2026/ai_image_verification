// Next.js 설정 — 프론트와 백엔드를 주소 하나로 묶는 프록시 포함
// 1. 브라우저가 /api, /static, /docs, /health 로 요청하면 Next 서버가 백엔드(BACKEND_URL)로 대신 전달함
//    그래서 방문자는 주소 하나만 알면 되고, 프론트·백엔드 주소가 달라서 생기는 CORS 문제도 없음
// 2. BACKEND_URL 기본값은 같은 PC 의 백엔드(127.0.0.1:8000)
//    다른 백엔드(예: 공용 서버)를 쓰려면 frontend/.env.local 에 BACKEND_URL=주소 를 넣고 다시 실행
// 3. 주의: npm run build 할 때의 BACKEND_URL 값이 빌드 결과에 고정됨 (바꾸면 다시 빌드)
// 4. 프록시는 기본적으로 요청 본문을 10MB 까지만 넘겨줌 → 백엔드 업로드 한도(20MB)보다 조금 크게 늘림
//    분석이 오래 걸려도 끊기지 않게 대기 시간도 2분으로 늘림
import type { NextConfig } from "next";

const BACKEND_URL = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

// 백엔드로 넘길 경로 목록
const PROXY_PATHS = ["/api/:path*", "/static/:path*", "/docs", "/openapi.json", "/health"];

const nextConfig: NextConfig = {
  cacheComponents: true,
  experimental: {
    proxyClientMaxBodySize: "22mb", // 백엔드 MAX_UPLOAD_MB(20) + multipart 여유분
    proxyTimeout: 120_000, // ms
  },
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return PROXY_PATHS.map((source) => ({ source, destination: `${BACKEND_URL}${source}` }));
  },
};

export default nextConfig;
