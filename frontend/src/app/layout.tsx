// 모든 페이지를 감싸는 기본 틀 (폰트·제목·언어 설정)
// 1. 본문은 Pretendard(한글 + Inter 계열 영문), 숫자·지표는 Geist Mono 사용
// 2. 두 폰트 모두 npm 패키지로 내장. 그래서 인터넷 없이도 폰트가 깨지지 않음
// 3. 여기서 정한 폰트 변수는 globals.css 의 --font-sans / --font-mono 로 연결됨
import type { Metadata } from "next";
import { GeistMono } from "geist/font/mono";
import "pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "진위판별 — AI 이미지 팩트체크",
  description: "이미지가 실제 촬영인지 AI 생성인지 점수와 근거로 보여주는 팩트체크 도우미",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className={`${GeistMono.variable} h-full`}>
      <body className="min-h-full">{children}</body>
    </html>
  );
}
