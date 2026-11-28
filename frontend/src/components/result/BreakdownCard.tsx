// 점수 근거 카드 (신용점수 내역처럼 항목별 가감점 표시)
// 1. 100점에서 시작해 각 분석 항목이 몇 점을 깎았는지(또는 더했는지) 막대로 보여줌
// 2. 0점 항목(예: EXIF 없음)은 '중립'으로 회색 표시. 그래서 EXIF 가 없어도 감점이 아님을 사용자가 알 수 있음
"use client";

import { motion } from "motion/react";
import type { AnalysisResult } from "@/lib/types";
import { Card, CardFooter, Stage } from "../ui";

export function BreakdownCard({ result }: { result: AnalysisResult }) {
  const maxAbs = Math.max(10, ...result.breakdown.map((b) => Math.abs(b.delta)));

  return (
    <Card>
      <Stage className="items-stretch p-5">
        <div className="flex w-full flex-col justify-center gap-4">
          <div className="flex items-baseline justify-between border-b border-line pb-3 font-mono text-[13px] text-muted">
            <span>기준 점수</span>
            <span className="text-text">100</span>
          </div>
          {result.breakdown.map((b, i) => {
            const neutral = b.delta === 0;
            const color = neutral ? "var(--color-faint)" : b.delta < 0 ? "var(--color-danger)" : "var(--color-safe)";
            return (
              <motion.div
                key={b.factor}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.08 }}
              >
                <div className="flex items-baseline justify-between gap-3">
                  <span className="text-[14px] font-medium">{b.factor}</span>
                  <span className="shrink-0 font-mono text-[14px]" style={{ color }}>
                    {neutral ? "±0" : b.delta > 0 ? `+${b.delta}` : b.delta}
                  </span>
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-white/[0.05]">
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: color }}
                    initial={{ width: 0 }}
                    animate={{ width: neutral ? "3%" : `${(Math.abs(b.delta) / maxAbs) * 100}%` }}
                    transition={{ delay: 0.25 + i * 0.08, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
                <p className="mt-1.5 text-xs text-muted">{b.detail}</p>
              </motion.div>
            );
          })}
          <div className="flex items-baseline justify-between border-t border-line pt-3 font-mono text-[13px]">
            <span className="text-muted">최종 점수</span>
            <span className="text-[15px] text-text">{result.authenticity_score}</span>
          </div>
        </div>
      </Stage>
      <CardFooter title="점수 근거" sub="항목별 가감점 내역" />
    </Card>
  );
}
