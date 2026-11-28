// 이미지 업로드 영역 (드래그&드롭 + 클릭해서 선택)
// 1. 파일을 고르면 미리보기를 띄우고 바로 onFile 로 넘겨 분석 시작
// 2. 분석 중에는 미리보기 위에 스캔 라인 애니메이션을 표시
// 3. 형식·용량은 화면에서 먼저 한 번 걸러줌 (최종 검사는 백엔드가 다시 함)
"use client";

import { ImageUp } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useRef, useState } from "react";

const MAX_MB = 20;
const ACCEPT = ["image/jpeg", "image/png", "image/webp"];

export function UploadStage({
  previewUrl,
  loading,
  onFile,
  onError,
}: {
  previewUrl: string | null;
  loading: boolean;
  onFile: (file: File) => void;
  onError: (msg: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const pick = (file?: File) => {
    if (!file) return;
    if (!ACCEPT.includes(file.type)) return onError("JPEG, PNG, WEBP 이미지만 분석할 수 있습니다.");
    if (file.size > MAX_MB * 1024 * 1024) return onError(`파일 크기가 너무 큽니다. 최대 ${MAX_MB}MB까지 업로드할 수 있습니다.`);
    onFile(file);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        pick(e.dataTransfer.files[0]);
      }}
      onClick={() => !loading && inputRef.current?.click()}
      className={`dot-grid group relative flex h-[420px] w-full cursor-pointer items-center justify-center overflow-hidden rounded-stage transition-colors ${
        dragging ? "bg-white/[0.06]" : ""
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT.join(",")}
        className="hidden"
        onChange={(e) => {
          pick(e.target.files?.[0]);
          e.target.value = "";
        }}
      />

      <AnimatePresence mode="wait">
        {previewUrl ? (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.94, filter: "blur(8px)" }}
            animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0, scale: 0.96 }}
            className="relative max-h-[360px] max-w-[85%] overflow-hidden rounded-stage"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={previewUrl} alt="업로드한 이미지" className="max-h-[360px] w-auto object-contain" />
            {loading && (
              <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute inset-0 bg-black/35" />
                <div className="scan-line absolute inset-x-0 h-1/3 bg-gradient-to-b from-transparent via-white/25 to-transparent" />
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="flex flex-col items-center text-center"
          >
            <motion.div
              animate={dragging ? { scale: 1.12, rotate: -6 } : { scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 18 }}
              className="lift flex size-16 items-center justify-center rounded-[18px] bg-chip-on"
            >
              <ImageUp size={26} strokeWidth={1.6} />
            </motion.div>
            <p className="mt-5 text-[17px] font-medium">{dragging ? "여기에 놓으세요" : "이미지를 끌어다 놓거나 클릭해서 선택"}</p>
            <p className="mt-1.5 text-[13px] text-muted">JPEG · PNG · WEBP, 최대 {MAX_MB}MB</p>
          </motion.div>
        )}
      </AnimatePresence>

      {loading && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
          <span className="lift inline-flex h-8 items-center gap-2 rounded-full bg-chip-on px-3.5 text-[13px]">
            <span className="size-3 animate-spin rounded-full border-2 border-white/25 border-t-white" />
            분석 중…
          </span>
        </div>
      )}
    </div>
  );
}
