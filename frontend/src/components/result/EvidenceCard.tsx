// 시각 증거 카드 (원본 / Grad-CAM 히트맵 / ELA 를 탭으로 전환)
// 1. 아래 버튼으로 이미지를 바꾸면 부드럽게 교차 전환됨
// 2. 이미지 주소는 백엔드가 준 /static/results/... 경로에 서버 주소를 붙여서 사용
"use client";

import { Download } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { assetUrl } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";
import { ActionButton, Card, CardFooter, Stage } from "../ui";

const TABS = [
  { key: "original_url", label: "원본", desc: "업로드한 이미지 그대로" },
  { key: "gradcam_url", label: "Grad-CAM", desc: "AI 모델이 주목한 영역 (빨강일수록 강함)" },
  { key: "ela_url", label: "ELA", desc: "압축 오차 분포 (밝을수록 편집 의심)" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

export function EvidenceCard({ result }: { result: AnalysisResult }) {
  const [tab, setTab] = useState<TabKey>("gradcam_url");
  const current = TABS.find((t) => t.key === tab)!;
  const src = assetUrl(result.visual_artifacts[tab]);

  return (
    <Card>
      <Stage className="bg-black/30">
        <AnimatePresence mode="popLayout">
          <motion.img
            key={src}
            src={src}
            alt={current.label}
            initial={{ opacity: 0, scale: 1.03 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            className="absolute inset-0 size-full object-contain p-3"
          />
        </AnimatePresence>
      </Stage>
      <CardFooter
        title={`시각 증거 · ${current.label}`}
        sub={current.desc}
        right={
          <a href={src} target="_blank" rel="noreferrer" className="text-muted transition-colors hover:text-text" aria-label="새 창에서 열기">
            <Download size={15} />
          </a>
        }
      />
      <div className="flex gap-1.5">
        {TABS.map((t) => (
          <ActionButton key={t.key} active={tab === t.key} onClick={() => setTab(t.key)}>
            {t.label}
          </ActionButton>
        ))}
      </div>
    </Card>
  );
}
