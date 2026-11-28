// 왼쪽 사이드바 (로고, 메뉴, 서버 상태, 등급 안내)
// 1. 메뉴를 누르면 Home 의 view 값이 바뀜 → 가운데 패널 내용이 바뀜
// 2. 10초마다 /health 를 호출해 서버 연결 상태와 Mock/Production 모드를 표시
// 3. 아래쪽에 접근 키 입력칸 (키가 있어야 분석 가능)
"use client";

import { Clock3, ScanSearch, BookOpen } from "lucide-react";
import { useEffect, useState } from "react";
import { API_BASE, getHealth } from "@/lib/api";
import { GRADE_INFO } from "@/lib/grade";
import type { Grade, Health } from "@/lib/types";
import { AccessKeyBox } from "./AccessKeyBox";
import { NewBadge } from "./ui";

export type View = "analyze" | "history" | "guide";

const MENU: { id: View; label: string; icon: typeof ScanSearch; badge?: string }[] = [
  { id: "analyze", label: "분석하기", icon: ScanSearch },
  { id: "history", label: "분석 기록", icon: Clock3 },
  { id: "guide", label: "점수 읽는 법", icon: BookOpen, badge: "new" },
];

export function Sidebar({ view, onChange, historyCount }: { view: View; onChange: (v: View) => void; historyCount: number }) {
  const [health, setHealth] = useState<Health | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let alive = true;
    const check = () =>
      getHealth()
        .then((h) => alive && (setHealth(h), setOffline(false)))
        .catch(() => alive && setOffline(true));
    check();
    const timer = setInterval(check, 10_000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <aside className="sticky top-4 hidden self-start h-[calc(100vh-2rem)] w-[220px] shrink-0 flex-col overflow-y-auto rounded-panel bg-panel p-4 lg:flex">
      {/* 로고 */}
      <div className="flex items-center gap-2.5 px-1">
        <Logo />
        <div className="leading-[1.05]">
          <p className="text-[15px] font-semibold tracking-tight">진위판별</p>
          <p className="text-[11px] text-muted">AI Image Fact-Check</p>
        </div>
      </div>

      {/* 메뉴 */}
      <p className="mt-8 px-1 text-xs text-muted">메뉴</p>
      <nav className="mt-2 flex flex-col gap-0.5">
        {MENU.map(({ id, label, icon: Icon, badge }) => (
          <button
            key={id}
            onClick={() => onChange(id)}
            className={`flex h-8 items-center gap-2 rounded-card px-2 text-left text-[13px] transition-colors ${
              view === id ? "bg-white/[0.06] text-text" : "text-muted hover:text-text"
            }`}
          >
            <Icon size={15} strokeWidth={1.8} />
            <span className="flex-1">{label}</span>
            {id === "history" && historyCount > 0 && <span className="font-mono text-[11px] text-faint">{historyCount}</span>}
            {badge && <NewBadge text={badge} />}
          </button>
        ))}
      </nav>

      {/* 등급 범례 */}
      <p className="mt-8 px-1 text-xs text-muted">등급 기준</p>
      <ul className="mt-2 flex flex-col gap-1.5 px-1">
        {(Object.keys(GRADE_INFO) as Grade[]).map((g) => (
          <li key={g} className="flex items-center gap-2 text-[12px]">
            <span className="size-2 rounded-full" style={{ background: GRADE_INFO[g].color }} />
            <span className="flex-1 text-muted">{GRADE_INFO[g].label}</span>
            <span className="font-mono text-[11px] text-faint">{GRADE_INFO[g].range}</span>
          </li>
        ))}
      </ul>

      {/* 접근 키 + 서버 상태 */}
      <div className="mt-auto">
        <AccessKeyBox />
      </div>
      <div className="mt-2 rounded-stage bg-inset p-3">
        <div className="flex items-center gap-2 text-[12px]">
          <span className="relative flex size-2">
            {!offline && health && <span className="absolute inline-flex size-full animate-ping rounded-full bg-safe opacity-60" />}
            <span className={`relative inline-flex size-2 rounded-full ${offline ? "bg-danger" : health ? "bg-safe" : "bg-faint"}`} />
          </span>
          <span className="font-medium">{offline ? "서버 연결 안 됨" : health ? "서버 연결됨" : "확인 중…"}</span>
          {health?.mode === "mock" && !offline && (
            <span className="ml-auto rounded-full bg-caution/15 px-1.5 font-mono text-[10px] text-caution">MOCK</span>
          )}
        </div>
        <p className="mt-1.5 truncate font-mono text-[10px] text-faint" title={API_BASE}>
          {API_BASE.replace(/^https?:\/\//, "")}
        </p>
      </div>
    </aside>
  );
}

// 로고: 돋보기 안에 반쪽 픽셀 (실사 vs AI)
export function Logo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden>
      <rect width="32" height="32" rx="8" fill="white" />
      <circle cx="14" cy="14" r="7" stroke="black" strokeWidth="2.4" />
      <path d="M14 7a7 7 0 0 0 0 14z" fill="black" />
      <path d="M19.2 19.2 25 25" stroke="black" strokeWidth="2.6" strokeLinecap="round" />
    </svg>
  );
}
