// 분석 기록 화면 (이 브라우저에서 분석한 결과 목록)
// 1. 카드를 누르면 그 결과를 다시 열어봄 (서버에 다시 요청하지 않음)
// 2. 등급 칩으로 걸러보기 가능
"use client";

import { AnimatePresence } from "motion/react";
import { useState } from "react";
import { assetUrl } from "@/lib/api";
import { GRADE_INFO } from "@/lib/grade";
import type { HistoryItem } from "@/lib/history";
import type { Grade } from "@/lib/types";
import { ActionButton, Card, CardFooter, Chip, Stage } from "./ui";

const FILTERS: { id: "ALL" | Grade; label: string }[] = [
  { id: "ALL", label: "전체" },
  { id: "SAFE_LIKELY_REAL", label: "실사 유력" },
  { id: "CAUTION_EDITED_OR_RECOMPRESSED", label: "편집 의심" },
  { id: "WARNING_AI_SUSPECTED", label: "AI 의심" },
  { id: "DANGER_HIGHLY_LIKELY_AI", label: "AI 유력" },
];

export function HistoryView({ items, onOpen, onClear }: { items: HistoryItem[]; onOpen: (h: HistoryItem) => void; onClear: () => void }) {
  const [filter, setFilter] = useState<"ALL" | Grade>("ALL");
  const shown = filter === "ALL" ? items : items.filter((h) => h.result.grade === filter);

  return (
    <>
      <div className="mt-6 flex items-center gap-1.5 overflow-x-auto pb-1">
        {FILTERS.map((f) => (
          <Chip key={f.id} group="history" label={f.label} active={filter === f.id} onClick={() => setFilter(f.id)} />
        ))}
        {items.length > 0 && (
          <button onClick={onClear} className="ml-auto shrink-0 text-[12px] text-faint transition-colors hover:text-danger">
            기록 지우기
          </button>
        )}
      </div>

      {shown.length === 0 ? (
        <div className="mt-5 flex h-[300px] items-center justify-center rounded-panel bg-box text-[14px] text-muted">
          {items.length === 0 ? "아직 분석한 이미지가 없습니다" : "이 등급의 기록이 없습니다"}
        </div>
      ) : (
        <ul className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <AnimatePresence mode="popLayout">
            {shown.map((h) => {
              const g = GRADE_INFO[h.result.grade];
              return (
                <Card key={h.result.analysis_id}>
                  <Stage minH="min-h-[200px]" className="bg-black/30">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={assetUrl(h.result.visual_artifacts.original_url)} alt="" className="absolute inset-0 size-full object-cover opacity-80" />
                    <span
                      className="lift absolute bottom-3 left-3 inline-flex h-8 items-center gap-2 rounded-full bg-black/70 px-3 font-mono text-[14px] backdrop-blur"
                      style={{ color: g.color }}
                    >
                      {h.result.authenticity_score}
                      <span className="font-sans text-[12px]">{g.label}</span>
                    </span>
                  </Stage>
                  <CardFooter title={h.source} sub={new Date(h.at).toLocaleString("ko-KR")} />
                  <div className="flex gap-1.5">
                    <ActionButton onClick={() => onOpen(h)}>결과 다시 보기</ActionButton>
                  </div>
                </Card>
              );
            })}
          </AnimatePresence>
        </ul>
      )}
    </>
  );
}
