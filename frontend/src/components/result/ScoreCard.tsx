// 진위 점수 카드 (원형 게이지 + 숫자 카운트업 + 등급)
// 1. 점수만큼 원이 채워지고 숫자가 0 → 점수로 올라감
// 2. 색은 등급 색 (초록=실사, 빨강=AI)
// 3. 조작 범위(전체 AI / 부분 편집 / 실사)를 아래 알약으로 표시
"use client";

import { Check, Copy, Zap } from "lucide-react";
import { animate, motion, useMotionValue, useTransform } from "motion/react";
import { useEffect, useState } from "react";
import { GRADE_INFO, SCOPE_INFO } from "@/lib/grade";
import type { AnalysisResult } from "@/lib/types";
import { ActionButton, Card, CardFooter, Pill, Stage } from "../ui";

const R = 92;
const C = 2 * Math.PI * R;

export function ScoreCard({ result, source }: { result: AnalysisResult; source: string }) {
  const grade = GRADE_INFO[result.grade];
  const scope = SCOPE_INFO[result.manipulation_scope];
  const value = useMotionValue(0);
  const shown = useTransform(value, (v) => Math.round(v));
  const dash = useTransform(value, (v) => C - (C * v) / 100);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    value.set(0);
    const ctrl = animate(value, result.authenticity_score, { duration: 1.4, ease: [0.16, 1, 0.3, 1] });
    return () => ctrl.stop();
  }, [result.analysis_id, result.authenticity_score, value]);

  const copy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Card>
      <Stage>
        <div className="flex flex-col items-center">
          <div className="relative size-[230px]">
            <svg viewBox="0 0 220 220" className="size-full -rotate-90 overflow-visible">
              <circle cx="110" cy="110" r={R} fill="none" stroke="rgb(255 255 255 / 0.06)" strokeWidth="14" />
              <motion.circle
                cx="110"
                cy="110"
                r={R}
                fill="none"
                stroke={grade.color}
                strokeWidth="14"
                strokeLinecap="round"
                strokeDasharray={C}
                style={{ strokeDashoffset: dash, filter: `drop-shadow(0 0 12px ${grade.color})` }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <motion.span className="font-mono text-[64px] font-medium leading-none tracking-tighter">{shown}</motion.span>
              <span className="mt-1 text-xs text-muted">/ 100</span>
            </div>
          </div>
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.9 }} className="mt-5 flex flex-wrap justify-center gap-2">
            <Pill color={grade.color}>
              <span className="size-2 rounded-full" style={{ background: grade.color }} />
              {grade.label} · {grade.short}
            </Pill>
            <Pill>{scope.label}</Pill>
          </motion.div>
        </div>
      </Stage>
      <CardFooter
        title="진위 점수"
        sub={`높을수록 실제 촬영에 가까움 · ${source}`}
        right={
          <span className="flex shrink-0 items-center gap-1 font-mono text-[11px] text-faint">
            {result.cached && <Zap size={11} className="text-caution" />}
            {result.cached ? "캐시" : `${result.latency_ms}ms`}
          </span>
        }
      />
      <div className="flex gap-1.5">
        <ActionButton onClick={copy}>
          {copied ? <Check size={13} /> : <Copy size={13} />}
          {copied ? "복사됨" : "결과 JSON 복사"}
        </ActionButton>
      </div>
    </Card>
  );
}
