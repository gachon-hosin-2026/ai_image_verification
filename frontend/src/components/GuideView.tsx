// 점수 읽는 법 화면 (발표·처음 쓰는 사용자용 설명)
// 1. 점수 방향, 4등급, 각 분석 방법이 무엇을 보는지 짧게 안내
// TODO: 발표 자료가 정리되면 문구를 팀 공식 설명으로 교체
"use client";

import { Brain, FileText, Layers, AudioWaveform } from "lucide-react";
import { motion } from "motion/react";
import { GRADE_INFO } from "@/lib/grade";
import type { Grade } from "@/lib/types";
import { Card, CardFooter, Stage } from "./ui";

const METHODS = [
  { title: "딥러닝 시각 패턴", icon: Brain, text: "AI 모델이 생성형 이미지 특유의 텍스처·경계 왜곡을 찾습니다. Grad-CAM 으로 어디를 봤는지 보여줍니다." },
  { title: "FFT 주파수 분석", icon: AudioWaveform, text: "이미지를 주파수로 바꿔 생성 모델이 남기는 고주파 이상 패턴을 찾습니다." },
  { title: "ELA 압축 잔차", icon: Layers, text: "JPEG 를 다시 저장했을 때 생기는 오차를 비교해 부분 합성·편집 영역을 찾습니다." },
  { title: "EXIF 메타데이터", icon: FileText, text: "촬영 기기·편집 프로그램 정보를 봅니다. 카톡·인스타는 EXIF 를 지우므로, 없으면 감점하지 않고 중립 처리합니다." },
];

export function GuideView() {
  return (
    <ul className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-2">
      <Card wide>
        <Stage minH="min-h-[240px]" className="px-6">
          <div className="w-full max-w-2xl">
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              className="h-3 origin-left rounded-full"
              style={{ background: "linear-gradient(90deg, var(--color-danger), var(--color-warning), var(--color-caution), var(--color-safe))" }}
            />
            <div className="mt-2 flex justify-between font-mono text-[12px] text-muted">
              <span>0 · AI 생성</span>
              <span>100 · 실제 촬영</span>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {(Object.keys(GRADE_INFO) as Grade[]).map((g) => (
                <div key={g} className="rounded-stage bg-inset p-3">
                  <span className="inline-block size-2 rounded-full" style={{ background: GRADE_INFO[g].color }} />
                  <p className="mt-2 text-[13px] font-medium">{GRADE_INFO[g].label}</p>
                  <p className="font-mono text-[11px] text-faint">{GRADE_INFO[g].range}점</p>
                </div>
              ))}
            </div>
          </div>
        </Stage>
        <CardFooter title="점수 방향" sub="높을수록 실제 촬영, 낮을수록 AI 생성 · 55–79점은 편집·재압축 회색지대" />
      </Card>
      {METHODS.map((m, i) => (
        <Card key={m.title}>
          <Stage minH="min-h-[150px]" className="p-5">
            <div className="flex size-full items-end justify-between self-stretch">
              <span className="font-mono text-[40px] leading-none text-faint">0{i + 1}</span>
              <div className="lift flex size-12 items-center justify-center rounded-[14px] bg-chip-on">
                <m.icon size={20} strokeWidth={1.7} />
              </div>
            </div>
          </Stage>
          <CardFooter title={m.title} />
          <p className="px-3 pb-3 text-[13px] leading-relaxed text-muted">{m.text}</p>
        </Card>
      ))}
    </ul>
  );
}
