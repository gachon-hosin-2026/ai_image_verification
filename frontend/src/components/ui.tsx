// 여러 화면에서 같이 쓰는 기본 부품 (카드, 칩, 버튼, NEW 배지)
// 1. 참고 사이트 카드 구조: 바깥 카드(둥근 20px) → 안쪽 무대(stage) → 아래 제목줄 → 버튼 줄
// 2. 모양을 바꾸고 싶으면 여기만 고치면 모든 카드에 같이 적용됨
"use client";

import { motion } from "motion/react";
import type { ReactNode } from "react";

// 카드 전체 틀
export function Card({ children, className = "", wide = false }: { children: ReactNode; className?: string; wide?: boolean }) {
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ type: "spring", stiffness: 260, damping: 28 }}
      className={`flex min-w-0 flex-col rounded-panel bg-box p-2 ${wide ? "md:col-span-2" : ""} ${className}`}
    >
      {children}
    </motion.li>
  );
}

// 카드 안쪽 '무대' (그림·그래프가 들어가는 영역)
// 1. minH 로 최소 높이 지정 (기본 340px)
export function Stage({
  children,
  className = "",
  badge,
  minH = "min-h-[340px]",
}: {
  children: ReactNode;
  className?: string;
  badge?: ReactNode;
  minH?: string;
}) {
  return (
    <div className={`relative flex items-center justify-center overflow-hidden rounded-stage ${minH} ${className}`}>
      {badge && <div className="absolute left-4 top-4 z-10">{badge}</div>}
      {children}
    </div>
  );
}

// 카드 아래 제목줄
export function CardFooter({ title, sub, right }: { title: string; sub?: string; right?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3 px-3 pb-2 pt-3">
      <div className="min-w-0">
        <p className="truncate text-[14px] font-medium">{title}</p>
        {sub && <p className="truncate text-xs text-muted">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

// 카드 맨 아래 작은 버튼
export function ActionButton({
  children,
  onClick,
  disabled,
  active,
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  active?: boolean;
}) {
  return (
    <motion.button
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      disabled={disabled}
      className={`flex h-9 flex-1 items-center justify-center gap-1.5 rounded-card text-xs font-medium transition-colors ${
        active ? "bg-white text-black" : "bg-inset text-muted hover:bg-white/[0.07] hover:text-text disabled:opacity-40"
      }`}
    >
      {children}
    </motion.button>
  );
}

// 알약 모양 필터 칩. 선택된 칩의 배경이 미끄러지듯 이동함(layoutId)
export function Chip({ label, active, onClick, group }: { label: string; active: boolean; onClick: () => void; group: string }) {
  return (
    <button
      onClick={onClick}
      className={`relative flex h-7 shrink-0 items-center rounded-full px-3 text-[13px] transition-colors ${
        active ? "text-text" : "bg-chip text-muted hover:text-text"
      }`}
    >
      {active && (
        <motion.span
          layoutId={`chip-${group}`}
          className="lift absolute inset-0 rounded-full bg-chip-on"
          transition={{ type: "spring", stiffness: 400, damping: 32 }}
        />
      )}
      <span className="relative">{label}</span>
    </button>
  );
}

// 손글씨 느낌의 'new' 배지 (참고 사이트 스타일)
export function NewBadge({ text = "new" }: { text?: string }) {
  return (
    <span className="inline-flex h-5 -rotate-3 items-center rounded-[50%] border border-white/70 px-2 font-mono text-[10px] italic leading-none text-white/90">
      {text}
    </span>
  );
}

// 상태 알약 (예: "분석 완료", "캐시됨")
export function Pill({ children, color }: { children: ReactNode; color?: string }) {
  return (
    <span
      className="lift inline-flex h-8 items-center gap-2 rounded-full bg-chip-on px-3.5 text-[13px] font-medium"
      style={color ? { color } : undefined}
    >
      {children}
    </span>
  );
}
