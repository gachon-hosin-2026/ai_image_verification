// 백엔드 API 응답 형식 (backend/app/schemas/analysis.py 와 1:1 대응)
// 1. 백엔드 스키마가 바뀌면 여기도 같이 바꿔야 함. 안 바꾸면 화면에서 값이 비어 보임

export type Grade =
  | "SAFE_LIKELY_REAL"
  | "CAUTION_EDITED_OR_RECOMPRESSED"
  | "WARNING_AI_SUSPECTED"
  | "DANGER_HIGHLY_LIKELY_AI";

export type Scope = "LIKELY_AUTHENTIC" | "LOCAL_EDIT_SUSPECTED" | "GLOBAL_AI_GENERATED";

export type UserLabel = "REAL" | "AI" | "CORRECT";

export interface Metrics {
  dl_human_prob: number;
  fft_hf_ratio: number;
  fft_slope: number;
  ela_mean: number;
  ela_std: number;
  ela_top5_concentration: number;
  meta_status_code: number;
}

export interface BreakdownItem {
  factor: string;
  delta: number;
  detail: string;
}

export interface AnalysisResult {
  analysis_id: string;
  cached: boolean;
  authenticity_score: number; // 높을수록 실사, 낮을수록 AI
  grade: Grade;
  manipulation_scope: Scope;
  latency_ms: number;
  metrics: Metrics;
  breakdown: BreakdownItem[];
  visual_artifacts: {
    original_url: string;
    gradcam_url: string;
    ela_url: string;
  };
}

export interface RecompressResult {
  analysis_id: string;
  original_score: number;
  recompressed_score: number;
  score_diff: number;
  original: AnalysisResult;
  recompressed: AnalysisResult;
}

export interface Health {
  status: string;
  mode: "mock" | "production";
  version: string;
}
