// 메인 화면 (사이드바 + 가운데 패널 + 하단 URL 입력창)
// 1. view 값으로 가운데 패널 내용을 바꿈: 분석하기 / 분석 기록 / 점수 읽는 법
// 2. 분석 흐름: 파일 선택·URL 입력 → API 호출 → result 저장 → 결과 카드 표시 + 기록에 추가
// 3. 결과 카드는 상단 칩(전체/점수/근거/검증)으로 걸러볼 수 있음
// 4. 접근 키 오류(401)가 나면 오류 알림 아래에 키 입력칸을 바로 띄움 (모바일에서도 입력 가능)
"use client";

import { RotateCcw, TriangleAlert, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useState, useSyncExternalStore } from "react";
import { AuthError, analyzeImage, analyzeUrl, assetUrl } from "@/lib/api";
import { history, type HistoryItem } from "@/lib/history";
import type { AnalysisResult } from "@/lib/types";
import { AccessKeyBox } from "./AccessKeyBox";
import { GuideView } from "./GuideView";
import { HistoryView } from "./HistoryView";
import { BreakdownCard } from "./result/BreakdownCard";
import { EvidenceCard } from "./result/EvidenceCard";
import { FeedbackCard } from "./result/FeedbackCard";
import { MetricsCard } from "./result/MetricsCard";
import { RecompressCard } from "./result/RecompressCard";
import { ScoreCard } from "./result/ScoreCard";
import { Logo, Sidebar, type View } from "./Sidebar";
import { Card, CardFooter, Chip, NewBadge } from "./ui";
import { UploadStage } from "./UploadStage";
import { UrlBar } from "./UrlBar";

type Filter = "all" | "score" | "evidence" | "verify";
const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "전체" },
  { id: "score", label: "점수" },
  { id: "evidence", label: "근거" },
  { id: "verify", label: "검증" },
];

const HEAD: Record<View, { title: string; desc: string }> = {
  analyze: {
    title: "이 이미지, 진짜일까?",
    desc: "사진을 올리거나 기사 URL을 붙여넣으면 실제 촬영인지 AI 생성인지 0–100점과 근거로 보여드립니다.",
  },
  history: { title: "분석 기록", desc: "이 브라우저에서 분석한 이미지 목록입니다." },
  guide: { title: "점수 읽는 법", desc: "점수와 등급, 각 분석 방법이 무엇을 보는지 설명합니다." },
};

export function Home() {
  const [view, setViewState] = useState<View>("analyze");
  // 메뉴 바꿀 때 맨 위로 스크롤
  const setView = (v: View) => {
    setViewState(v);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [source, setSource] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needKey, setNeedKey] = useState(false);
  const [filter, setFilter] = useState<Filter>("all");
  const items = useSyncExternalStore(history.subscribe, history.getSnapshot, history.getServerSnapshot);

  // 공통 분석 실행
  const run = async (job: () => Promise<AnalysisResult>, label: string) => {
    setView("analyze");
    setLoading(true);
    setError(null);
    setNeedKey(false);
    setResult(null);
    setFilter("all");
    try {
      const r = await job();
      setResult(r);
      setSource(label);
      setPreview(assetUrl(r.visual_artifacts.original_url));
      history.add(r, label);
    } catch (e) {
      setError((e as Error).message);
      setNeedKey(e instanceof AuthError);
    } finally {
      setLoading(false);
    }
  };

  const onFile = (file: File) => {
    if (preview?.startsWith("blob:")) URL.revokeObjectURL(preview);
    setPreview(URL.createObjectURL(file));
    run(() => analyzeImage(file), file.name);
  };

  const onUrl = (url: string) => {
    setPreview(null);
    run(() => analyzeUrl(url), url.replace(/^https?:\/\//, ""));
  };

  const reset = () => {
    setResult(null);
    setPreview(null);
    setError(null);
  };

  const openHistory = (h: HistoryItem) => {
    setResult(h.result);
    setSource(h.source);
    setPreview(assetUrl(h.result.visual_artifacts.original_url));
    setFilter("all");
    setView("analyze");
  };

  const show = (f: Filter) => filter === "all" || filter === f;

  return (
    <div className="flex min-h-screen gap-4 p-4 pb-24">
      <Sidebar view={view} onChange={setView} historyCount={items.length} />

      <main className="w-full min-w-0 flex-1 rounded-panel bg-panel p-5 md:p-6">
        {/* 모바일 로고 (사이드바가 숨겨지는 좁은 화면용) */}
        <div className="mb-6 flex items-center gap-2 lg:hidden">
          <Logo size={26} />
          <span className="text-[15px] font-semibold">진위판별</span>
          <div className="ml-auto flex gap-1">
            {(["analyze", "history", "guide"] as View[]).map((v) => (
              <Chip key={v} group="mobile-nav" label={{ analyze: "분석", history: "기록", guide: "안내" }[v]} active={view === v} onClick={() => setView(v)} />
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div key={view} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }}>
            <h1 className="text-3xl font-semibold tracking-[-0.02em] md:text-4xl">{HEAD[view].title}</h1>
            <p className="mt-3 max-w-2xl text-base leading-relaxed text-muted">{HEAD[view].desc}</p>

            {view === "history" && <HistoryView items={items} onOpen={openHistory} onClear={history.clear} />}
            {view === "guide" && <GuideView />}

            {view === "analyze" && (
              <>
                {/* 필터 칩 + 새 분석 버튼 */}
                <div className="mt-6 flex items-center gap-1.5 overflow-x-auto pb-1">
                  {FILTERS.map((f) => (
                    <Chip key={f.id} group="result" label={f.label} active={filter === f.id} onClick={() => setFilter(f.id)} />
                  ))}
                  {(result || error) && (
                    <button
                      onClick={reset}
                      className="ml-auto flex h-7 shrink-0 items-center gap-1.5 rounded-full bg-white px-3 text-[13px] font-medium text-black"
                    >
                      <RotateCcw size={13} /> 새 이미지 분석
                    </button>
                  )}
                </div>

                {/* 오류 알림 */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 flex items-center gap-2.5 rounded-stage bg-danger/10 px-4 py-3 text-[13px] text-danger">
                        <TriangleAlert size={15} className="shrink-0" />
                        <span className="flex-1">{error}</span>
                        <button onClick={() => setError(null)} aria-label="닫기">
                          <X size={14} />
                        </button>
                      </div>
                      {needKey && (
                        <div className="mt-2 max-w-sm">
                          <AccessKeyBox
                            highlight
                            onSaved={() => {
                              setError(null);
                              setNeedKey(false);
                            }}
                          />
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>

                <ul className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
                  <AnimatePresence mode="popLayout">
                    {!result && (
                      <Card key="upload" wide>
                        <UploadStage
                          previewUrl={preview}
                          loading={loading}
                          onFile={onFile}
                          onError={setError}
                        />
                        <CardFooter
                          title="이미지 업로드"
                          sub="원본 화질 그대로 분석합니다 · 업로드한 이미지는 분석에만 사용됩니다"
                          right={<NewBadge />}
                        />
                      </Card>
                    )}
                    {result && show("score") && <ScoreCard key={`score-${result.analysis_id}`} result={result} source={source} />}
                    {result && show("evidence") && <EvidenceCard key={`ev-${result.analysis_id}`} result={result} />}
                    {result && show("evidence") && <BreakdownCard key={`bd-${result.analysis_id}`} result={result} />}
                    {result && show("evidence") && <MetricsCard key={`mt-${result.analysis_id}`} result={result} />}
                    {result && show("verify") && <RecompressCard key={`rc-${result.analysis_id}`} result={result} />}
                    {result && show("verify") && <FeedbackCard key={`fb-${result.analysis_id}`} result={result} />}
                  </AnimatePresence>
                </ul>
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      <UrlBar loading={loading} onSubmit={onUrl} />
    </div>
  );
}
