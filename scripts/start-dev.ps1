# 개인 개발 서버 실행 (팀원 모두 사용)
# 1. 처음 실행이면 가상환경·패키지·.env 를 자동으로 준비함
# 2. 백엔드(8001) + 프론트(3001) 를 각각 새 창으로 띄우고 브라우저를 엶
# 3. 개발용이라 Mock 모드 · 접근 키 없음 · 내 PC 전용 DB 사용. 그래서 공용 서버의 학습 데이터와 섞이지 않음
# 4. -UsePublicServer 를 붙이면 내 백엔드 대신 공용 서버에 연결 (프론트만 개발할 때)
param([switch]$UsePublicServer)

. (Join-Path $PSScriptRoot 'common.ps1')

Say '== 개인 개발 서버 시작 =='
Test-Tools

$ports = @($DevFrontendPort)
if (-not $UsePublicServer) { $ports += $DevBackendPort }
foreach ($port in $ports) {
    if (Test-PortBusy $port) { Fail "포트 $port 가 이미 사용 중입니다. 이미 켜진 개발 서버 창을 닫고 다시 실행하세요." }
}

if ($UsePublicServer) {
    $backendUrl = $PublicServerUrl
    Say "[백엔드] 공용 서버에 연결합니다: $backendUrl"
} else {
    $venvPy = Initialize-Backend
    $envFile = Join-Path $Backend '.env'
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $Backend '.env.example') $envFile
        Say '[백엔드] .env 가 없어서 .env.example 로 만들었습니다. (개발용: Mock 모드, 접근 키 없음)'
    }
    $backendUrl = "http://127.0.0.1:$DevBackendPort"
    Start-Window 'DEV-backend' $Backend "`"$venvPy`" -m uvicorn app.main:app --host 127.0.0.1 --port $DevBackendPort --reload"
}

Initialize-Frontend
Start-Window 'DEV-frontend' $Frontend "set `"BACKEND_URL=$backendUrl`" & npm run dev -- -p $DevFrontendPort"

Say ''
Say "개발 서버를 켰습니다. 잠시 후 브라우저가 열립니다: http://localhost:$DevFrontendPort" 'Green'
Say '  - 코드를 고치면 자동으로 다시 읽습니다.'
Say '  - 끝낼 때는 DEV-backend / DEV-frontend 창을 닫으세요.'
if ($UsePublicServer) { Say '  - 공용 서버를 쓰는 중이라 사이드바에 접근 키를 입력해야 분석됩니다.' 'Yellow' }
Start-Sleep -Seconds 6
Start-Process "http://localhost:$DevFrontendPort"
