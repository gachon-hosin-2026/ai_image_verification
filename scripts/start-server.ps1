# 공용 서버 실행 (공용 서버 관리자만 사용)
# 1. 반드시 main 브랜치 + 접근 키가 설정된 상태에서만 실행됨. 아니면 이유를 알려주고 멈춤
# 2. 백엔드(8000) → 프론트 운영 빌드(3000) → Tailscale Funnel 순서로 각각 새 창에 띄움
# 3. 방문자는 공용 주소 하나로 웹사이트·API 를 모두 사용 (프론트가 /api 요청을 백엔드로 전달)
# 4. 둘 다 127.0.0.1 로만 열어서, 외부에서는 Funnel 을 통해서만 들어올 수 있음
. (Join-Path $PSScriptRoot 'common.ps1')

Say '== 공용 서버 시작 =='
Test-Tools -NeedTailscale

$branch = (& git -C $Root branch --show-current)
if ($branch -ne 'main') {
    Fail "공용 서버는 main 브랜치에서만 실행합니다. (현재: $branch)`n       공용 서버 전용 폴더(예: C:\Dev\p-project-server)에서 실행하세요."
}

$envFile = Join-Path $Backend '.env'
if (-not (Test-Path $envFile)) { Fail "backend\.env 가 없습니다. backend\.env.example 을 복사해 만들고 ACCESS_KEY 를 넣으세요." }
if (-not (Get-EnvValue $envFile 'ACCESS_KEY')) {
    Fail "backend\.env 의 ACCESS_KEY 가 비어 있습니다. 외부에 공개되는 서버라 접근 키가 꼭 필요합니다.`n       키 만들기:  python -c `"import secrets; print(secrets.token_urlsafe(24))`""
}
if (Test-Path (Join-Path $Frontend '.env.local')) {
    Warn 'frontend\.env.local 이 있습니다. 공용 서버 폴더에서는 지우는 것을 권장합니다. (프록시 주소가 바뀔 수 있음)'
}

foreach ($port in @($ServerBackendPort, $ServerFrontendPort)) {
    if (Test-PortBusy $port) { Fail "포트 $port 가 이미 사용 중입니다. 서버가 이미 켜져 있으면 update-server 또는 stop-server 를 사용하세요." }
}

$venvPy = Initialize-Backend
Initialize-Frontend
if (-not (Test-Path (Join-Path $Frontend '.next\BUILD_ID'))) {
    Say '[프론트] 운영용 빌드가 없어서 빌드합니다...'
    Push-Location $Frontend
    Remove-Item Env:BACKEND_URL -ErrorAction SilentlyContinue   # 기본 주소(127.0.0.1:8000)로 빌드
    & npm run build
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Fail '프론트 빌드에 실패했습니다.' }
}

Start-Window 'SERVER-backend' $Backend "`"$venvPy`" -m uvicorn app.main:app --host 127.0.0.1 --port $ServerBackendPort"
Start-Window 'SERVER-frontend' $Frontend "npm run start -- -H 127.0.0.1 -p $ServerFrontendPort"

$funnelStatus = (& tailscale funnel status 2>&1 | Out-String)
if ($funnelStatus -match "127\.0\.0\.1:$ServerFrontendPort") {
    Say '[Funnel] 이미 켜져 있습니다.'
} else {
    Start-Window 'SERVER-funnel' $Root "tailscale funnel $ServerFrontendPort"
}

Say ''
Say "공용 서버를 켰습니다: $PublicServerUrl" 'Green'
Say '  - SERVER-backend / SERVER-frontend / SERVER-funnel 창 3개가 켜져 있어야 접속됩니다.'
Say '  - 공개를 멈추려면 stop-server 를 실행하세요.'
