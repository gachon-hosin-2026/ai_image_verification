# 실행 스크립트들이 같이 쓰는 공통 함수
# 1. 폴더 위치, 포트 번호, 공용 서버 주소를 한 곳에서 정함. 그래서 바꿀 때 여기만 고치면 됨
# 2. Python·Node·Git 설치 여부를 검사하고, 없으면 설치 방법을 한국어로 알려줌
# 3. 패키지는 requirements.txt / package-lock.json 이 바뀌었을 때만 다시 설치함. 그래서 두 번째 실행부터는 빠름
# 4. Windows 기본 PowerShell 5.1 기준으로 작성 (?? 같은 최신 문법 사용 안 함)

$ErrorActionPreference = 'Continue'   # 외부 프로그램 경고 때문에 멈추지 않게 하고, 종료 코드로 직접 확인
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$Root     = Split-Path -Parent $PSScriptRoot
$Backend  = Join-Path $Root 'backend'
$Frontend = Join-Path $Root 'frontend'

# 포트: 공용 서버와 개인 개발 서버가 한 PC 에서 같이 켜져도 부딪히지 않게 나눔
$ServerBackendPort  = 8000
$ServerFrontendPort = 3000
$DevBackendPort     = 8001
$DevFrontendPort    = 3001

# 공용 서버 주소 (Tailscale Funnel 고정 주소)
$PublicServerUrl = 'https://xodus217.taile57f46.ts.net'

function Say([string]$msg, [string]$color = 'Cyan') { Write-Host $msg -ForegroundColor $color }
function Warn([string]$msg) { Write-Host "[주의] $msg" -ForegroundColor Yellow }
function Fail([string]$msg) {
    Write-Host ''
    Write-Host "[오류] $msg" -ForegroundColor Red
    Write-Host ''
    exit 1
}

# Python 찾기: py 런처(-3) → python 순서
function Get-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) { return @{ Exe = 'py'; Args = @('-3') } }
    if (Get-Command python -ErrorAction SilentlyContinue) { return @{ Exe = 'python'; Args = @() } }
    Fail 'Python 이 없습니다. 설치 후 터미널을 다시 여세요:  winget install Python.Python.3.12'
}

function Test-Tools([switch]$NeedTailscale) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Fail 'Git 이 없습니다:  winget install --id Git.Git' }
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { Fail 'Node.js 가 없습니다:  winget install OpenJS.NodeJS.LTS' }
    $nodeVer = [version]((& node -v).TrimStart('v'))
    if ($nodeVer -lt [version]'20.9.0') { Fail "Node.js 버전이 낮습니다 (현재 $nodeVer). 22 이상으로 업데이트하세요:  winget upgrade OpenJS.NodeJS.LTS" }
    if ($NeedTailscale -and -not (Get-Command tailscale -ErrorAction SilentlyContinue)) {
        Fail 'Tailscale 이 없습니다:  winget install --id Tailscale.Tailscale  (설치 후 로그인)'
    }
}

# 두 파일 내용이 같은지 (설치 기록 비교용)
function Test-SameFile([string]$a, [string]$b) {
    if (-not (Test-Path $a) -or -not (Test-Path $b)) { return $false }
    return (Get-FileHash $a).Hash -eq (Get-FileHash $b).Hash
}

# 백엔드 준비: 가상환경 + 패키지
function Initialize-Backend {
    $venvPy = Join-Path $Backend '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPy)) {
        Say '[백엔드] 가상환경(.venv) 만드는 중...'
        $py = Get-Python
        $pyArgs = $py.Args
        # 주의: 함수 안의 외부 명령 출력은 | Out-Host 로 화면에만 보냄 (반환값에 섞이지 않게)
        & $py.Exe @pyArgs -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' | Out-Host
        if ($LASTEXITCODE -ne 0) { Fail 'Python 3.11 이상이 필요합니다:  winget install Python.Python.3.12' }
        & $py.Exe @pyArgs -m venv (Join-Path $Backend '.venv') | Out-Host
        if ($LASTEXITCODE -ne 0) { Fail '가상환경을 만들지 못했습니다.' }
    }
    $req   = Join-Path $Backend 'requirements.txt'
    $stamp = Join-Path $Backend '.venv\installed-requirements.txt'
    if (-not (Test-SameFile $req $stamp)) {
        Say '[백엔드] 패키지 설치 중... (처음에는 몇 분 걸립니다)'
        & $venvPy -m pip install --disable-pip-version-check -q -r $req | Out-Host
        if ($LASTEXITCODE -ne 0) { Fail '백엔드 패키지 설치에 실패했습니다. 위 오류 메시지를 확인하세요.' }
        Copy-Item $req $stamp -Force
    }
    return $venvPy
}

# 프론트 준비: node_modules
function Initialize-Frontend {
    $lock  = Join-Path $Frontend 'package-lock.json'
    $stamp = Join-Path $Frontend 'node_modules\.installed-package-lock.json'
    if (-not (Test-SameFile $lock $stamp)) {
        Say '[프론트] 패키지 설치 중... (처음에는 몇 분 걸립니다)'
        Push-Location $Frontend
        & npm ci --no-audit --no-fund | Out-Host
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -ne 0) { Fail '프론트 패키지 설치에 실패했습니다. 위 오류 메시지를 확인하세요.' }
        Copy-Item $lock $stamp -Force
    }
}

# .env 에서 값 하나 읽기 (같은 이름이 여러 번 있으면 마지막 줄 기준 — 서버와 같은 규칙)
function Get-EnvValue([string]$file, [string]$name) {
    if (-not (Test-Path $file)) { return '' }
    $line = Get-Content $file -Encoding UTF8 | Where-Object { $_ -match "^\s*$name\s*=" } | Select-Object -Last 1
    if (-not $line) { return '' }
    return ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
}

function Test-PortBusy([int]$port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

# 포트를 쓰고 있는 프로그램 종료 (업데이트·중지용)
function Stop-Port([int]$port) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object {
            $p = Get-Process -Id $_ -ErrorAction SilentlyContinue
            if ($p) { Say "  포트 $port 사용 중인 $($p.ProcessName) (PID $_) 종료"; Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
        }
}

# 새 창을 열어 명령 실행 (창 제목은 영어: cmd 창 제목의 한글 깨짐 방지)
function Start-Window([string]$title, [string]$dir, [string]$command) {
    Start-Process -FilePath 'cmd.exe' -WorkingDirectory $dir -ArgumentList '/k', "title $title & $command"
}
