// 사용자 피드백 카드 ("맞아요" / "실제 사진이에요" / "AI 이미지예요")
// 1. 선택하면 백엔드 /api/v1/feedback 에 저장. 나중에 모델 재학습 데이터로 사용
// 2. 한 번 보내면 버튼이 잠기고 감사 메시지가 나옴
"use client";

import { CheckCheck } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { sendFeedback } from "@/lib/api";
import type { AnalysisResult, UserLabel } from "@/lib/types";
import { ActionButton, Card, CardFooter, Stage } from "../ui";

const OPTIONS: { label: UserLabel; text: string }[] = [
  { label: "CORRECT", text: "판정이 맞아요" },
  { label: "REAL", text: "실제 사진이에요" },
  { label: "AI", text: "AI 이미지예요" },
];

export function FeedbackCard({ result }: { result: AnalysisResult }) {
  const [sent, setSent] = useState<UserLabel | null>(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const send = async (label: UserLabel) => {
    setError(null);
    try {
      await sendFeedback(result.analysis_id, label, comment || undefined);
      setSent(label);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <Card>
      <Stage className="px-6">
        <AnimatePresence mode="wait">
          {sent ? (
            <motion.div key="done" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex flex-col items-center">
              <span className="lift inline-flex h-10 items-center gap-2 rounded-full bg-chip-on px-4 text-[14px] font-medium">
                <CheckCheck size={16} className="text-safe" />
                피드백이 저장되었습니다
              </span>
              <p className="mt-3 text-[13px] text-muted">모델 개선에 사용됩니다. 감사합니다!</p>
            </motion.div>
          ) : (
            <motion.div key="form" exit={{ opacity: 0 }} className="flex w-full max-w-sm flex-col items-center text-center">
              <p className="text-[15px] font-medium">이 판정, 맞나요?</p>
              <p className="mt-1 text-[13px] text-muted">알고 계신 정답을 알려주시면 다음 학습에 반영합니다</p>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                maxLength={2000}
                placeholder="출처나 근거가 있다면 남겨주세요 (선택)"
                className="mt-5 h-24 w-full resize-none rounded-stage bg-inset p-3 text-[13px] outline-none placeholder:text-faint focus:bg-white/[0.06]"
              />
              {error && <p className="mt-2 text-[12px] text-danger">{error}</p>}
            </motion.div>
          )}
        </AnimatePresence>
      </Stage>
      <CardFooter title="피드백" sub="사용자 정답 수집 (Active Learning)" />
      <div className="flex gap-1.5">
        {OPTIONS.map((o) => (
          <ActionButton key={o.label} onClick={() => send(o.label)} disabled={sent !== null} active={sent === o.label}>
            {o.text}
          </ActionButton>
        ))}
      </div>
    </Card>
  );
}
