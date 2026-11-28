// 접근 키 입력칸
// 1. 키가 없으면 입력칸을, 저장돼 있으면 "저장됨 ••••끝4자리" 와 변경 버튼을 보여줌
// 2. 사이드바와, 401 오류가 났을 때 오류 알림 아래에 같이 쓰임
// 3. 입력한 키는 이 브라우저에만 저장됨 (lib/accessKey.ts)
"use client";

import { KeyRound, Check } from "lucide-react";
import { useState, useSyncExternalStore } from "react";
import { accessKey } from "@/lib/accessKey";

export function AccessKeyBox({ onSaved, highlight = false }: { onSaved?: () => void; highlight?: boolean }) {
  const saved = useSyncExternalStore(accessKey.subscribe, accessKey.get, accessKey.getServerSnapshot);
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");

  const save = () => {
    if (!value.trim()) return;
    accessKey.set(value);
    setValue("");
    setEditing(false);
    onSaved?.();
  };

  if (saved && !editing && !highlight) {
    return (
      <div className="flex items-center gap-2 rounded-stage bg-inset px-3 py-2.5 text-[12px]">
        <KeyRound size={13} className="shrink-0 text-safe" />
        <span className="flex-1 text-muted">
          접근 키 <span className="font-mono text-faint">••••{saved.slice(-4)}</span>
        </span>
        <button onClick={() => setEditing(true)} className="text-faint transition-colors hover:text-text">
          변경
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save();
      }}
      className={`rounded-stage p-3 ${highlight ? "bg-white/[0.06]" : "bg-inset"}`}
    >
      <p className="flex items-center gap-1.5 text-[12px] font-medium">
        <KeyRound size={13} /> 접근 키
      </p>
      <p className="mt-1 text-[11px] text-faint">팀에서 받은 키를 입력하세요</p>
      <div className="mt-2.5 flex gap-1.5">
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="접근 키"
          autoComplete="off"
          className="h-8 min-w-0 flex-1 rounded-card bg-white/[0.06] px-2.5 font-mono text-[12px] outline-none placeholder:font-sans placeholder:text-faint focus:bg-white/[0.1]"
        />
        <button
          type="submit"
          disabled={!value.trim()}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-card bg-white text-black disabled:bg-white/10 disabled:text-faint"
          aria-label="접근 키 저장"
        >
          <Check size={14} />
        </button>
      </div>
      {editing && (
        <button type="button" onClick={() => setEditing(false)} className="mt-2 text-[11px] text-faint hover:text-text">
          취소
        </button>
      )}
    </form>
  );
}
