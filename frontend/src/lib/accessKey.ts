// 접근 키 저장 코드
// 1. 팀에서 받은 접근 키를 이 브라우저(localStorage)에 저장. 그래서 한 번 입력하면 새로고침해도 유지됨
// 2. 키는 코드나 .env 에 넣지 않음. 프론트 코드는 누구나 볼 수 있어서, 넣으면 키가 공개되는 것과 같음
// 3. api.ts 가 모든 분석 요청에 X-Access-Key 헤더로 붙여 보냄

const KEY = "jinwi-access-key";
const listeners = new Set<() => void>();
let cache: string | null = null;

function read(): string {
  if (cache !== null) return cache;
  try {
    cache = localStorage.getItem(KEY) ?? "";
  } catch {
    cache = "";
  }
  return cache;
}

export const accessKey = {
  subscribe(fn: () => void) {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
  get: read,
  getServerSnapshot: () => "",
  set(value: string) {
    cache = value.trim();
    try {
      if (cache) localStorage.setItem(KEY, cache);
      else localStorage.removeItem(KEY);
    } catch {
      /* 시크릿 모드 등 저장 불가 시 메모리에만 보관 */
    }
    listeners.forEach((fn) => fn());
  },
};
