// SNS 재압축 테스트 카드
// 1. 버튼을 누르면 백엔드가 원본을 50% 축소 + JPEG 75 로 재압축해 다시 분석
// 2. 원본 점수 → 재압축 점수를 나란히 보여줌. 그래서 카톡·인스타로 퍼진 뒤에도 판정이 유지되는지 확인 가능
"use client";

import { ArrowRight, Repeat2 } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import { recompressTest } from "@/lib/api";
import { GRADE_INFO } from "@/lib/grade";
import type { AnalysisResult, RecompressResult } from "@/lib/types";
import { ActionButton, Card, CardFooter, Stage } from "../ui";

// 점수 하나 (원본 / 재압축 후)
function Score({ label, score, grade }: { label: string; score: number; grade: AnalysisResult["grade"] }) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-xs text-muted">{label}</span>
      <span className="mt-2 font-mono text-[44px] leading-none" style={{ color: GRADE_INFO[grade].color }}>
        {score}
      </span>
      <span className="mt-2 text-[12px] text-muted">{GRADE_INFO[grade].label}</span>
    </div>
  );
}

export function RecompressCard({ result }: { result: AnalysisResult }) {
  const [data, setData] = useState<RecompressResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await recompressTest(result.analysis_id));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Stage>
        {data ? (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center">
            <div className="flex items-center gap-8">
              <Score label="원본" score={data.original_score} grade={data.original.grade} />
              <ArrowRight className="text-faint" />
              <Score label="재압축 후" score={data.recompressed_score} grade={data.recompressed.grade} />
            </div>
            <span className="lift mt-6 inline-flex h-8 items-center rounded-full bg-chip-on px-3.5 font-mono text-[13px]">
              변화 {data.score_diff > 0 ? `+${data.score_diff}` : data.score_diff}점
            </span>
          </motion.div>
        ) : (
          <div className="flex flex-col items-center px-8 text-center">
            <motion.div
              animate={loading ? { rotate: 360 } : { rotate: 0 }}
              transition={loading ? { repeat: Infinity, duration: 1, ease: "linear" } : {}}
              className="lift flex size-14 items-center justify-center rounded-[16px] bg-chip-on"
            >
              <Repeat2 size={22} strokeWidth={1.7} />
            </motion.div>
            <p className="mt-4 text-[15px] font-medium">카톡·인스타로 공유되면 어떻게 될까?</p>
            <p className="mt-1 text-[13px] text-muted">50% 축소 + JPEG 품질 75로 재압축 후 다시 분석합니다</p>
            {error && <p className="mt-3 text-[12px] text-danger">{error}</p>}
          </div>
        )}
      </Stage>
      <CardFooter title="SNS 재압축 테스트" sub="판정이 재압축에도 버티는지 확인" />
      <div className="flex gap-1.5">
        <ActionButton onClick={run} disabled={loading}>
          {loading ? "테스트 중…" : data ? "다시 테스트" : "테스트 실행"}
        </ActionButton>
      </div>
    </Card>
  );
}
