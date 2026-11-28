// 세부 지표 카드 (딥러닝·FFT·ELA·EXIF 원시 수치)
// 1. 발표·디버깅용으로 백엔드 metrics 값을 그대로 보여줌
// TODO: AI 팀이 각 지표의 정상 범위를 정하면, 범위를 벗어난 값에 색을 입히기
"use client";

import type { AnalysisResult } from "@/lib/types";
import { Card, CardFooter, Stage } from "../ui";

const ROWS: { key: keyof AnalysisResult["metrics"]; label: string; group: string; digits: number }[] = [
  { key: "dl_human_prob", label: "실사 확률", group: "딥러닝", digits: 2 },
  { key: "fft_hf_ratio", label: "고주파 비율", group: "FFT", digits: 3 },
  { key: "fft_slope", label: "스펙트럼 기울기", group: "FFT", digits: 2 },
  { key: "ela_mean", label: "잔차 평균", group: "ELA", digits: 1 },
  { key: "ela_std", label: "잔차 표준편차", group: "ELA", digits: 1 },
  { key: "ela_top5_concentration", label: "상위 5% 집중도", group: "ELA", digits: 2 },
  { key: "meta_status_code", label: "메타데이터 상태", group: "EXIF", digits: 0 },
];

export function MetricsCard({ result }: { result: AnalysisResult }) {
  const m = result.metrics;
  return (
    <Card>
      <Stage className="items-stretch p-5">
        <div className="grid w-full grid-cols-2 content-center gap-2">
          {ROWS.map((r) => (
            <div key={r.key} className={`rounded-stage bg-inset p-3.5 ${r.key === "dl_human_prob" ? "col-span-2" : ""}`}>
              <p className="text-[11px] text-faint">{r.group}</p>
              <p className="mt-0.5 text-[12px] text-muted">{r.label}</p>
              <p className="mt-2 font-mono text-[22px] leading-none tracking-tight">
                {r.key === "dl_human_prob" ? `${Math.round(m.dl_human_prob * 100)}%` : m[r.key].toFixed(r.digits)}
              </p>
              {r.key === "dl_human_prob" && (
                <div className="mt-3 h-1 overflow-hidden rounded-full bg-white/[0.06]">
                  <div className="h-full rounded-full bg-white" style={{ width: `${m.dl_human_prob * 100}%` }} />
                </div>
              )}
              {r.key === "meta_status_code" && m.meta_status_code === 0 && <p className="mt-1.5 text-[11px] text-faint">정보 없음 · 중립</p>}
            </div>
          ))}
        </div>
      </Stage>
      <CardFooter title="세부 지표" sub="분석 엔진이 계산한 원시 수치" />
    </Card>
  );
}
