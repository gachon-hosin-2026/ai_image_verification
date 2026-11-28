// 화면 아래 떠 있는 URL 입력창 (참고 사이트 하단 검색바 스타일)
// 1. 뉴스·커뮤니티 기사 주소나 이미지 주소를 붙여넣고 Enter → onSubmit 으로 URL 분석 시작
// 2. http(s) 로 시작하지 않으면 https:// 를 자동으로 붙임
"use client";

import { ArrowUp, Link2 } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";

export function UrlBar({ loading, onSubmit }: { loading: boolean; onSubmit: (url: string) => void }) {
  const [value, setValue] = useState("");
  const ready = value.trim().length > 3 && !loading;

  const submit = () => {
    if (!ready) return;
    const v = value.trim();
    onSubmit(/^https?:\/\//i.test(v) ? v : `https://${v}`);
  };

  return (
    <motion.form
      initial={{ y: 40, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 220, damping: 24, delay: 0.2 }}
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className="lift fixed bottom-5 left-1/2 z-40 flex h-12 w-[min(560px,calc(100vw-2rem))] -translate-x-1/2 items-center gap-2 rounded-full border border-line bg-[#1c1c1e]/90 pl-4 pr-1.5 backdrop-blur-xl lg:left-[calc(50%+118px)]"
    >
      <Link2 size={16} className="shrink-0 text-muted" />
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="기사·게시글 URL을 붙여넣으면 대표 이미지를 분석합니다"
        className="h-full min-w-0 flex-1 bg-transparent text-[14px] outline-none placeholder:text-faint"
      />
      <motion.button
        type="submit"
        whileTap={{ scale: 0.9 }}
        disabled={!ready}
        className={`flex size-9 shrink-0 items-center justify-center rounded-full transition-colors ${
          ready ? "bg-white text-black" : "bg-white/10 text-faint"
        }`}
        aria-label="URL 분석"
      >
        {loading ? <span className="size-3.5 animate-spin rounded-full border-2 border-white/25 border-t-white" /> : <ArrowUp size={17} />}
      </motion.button>
    </motion.form>
  );
}
