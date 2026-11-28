# 공용 서버 업데이트 (PR 이 main 에 병합된 뒤 실행)
# 1. 켜져 있는 공용 서버(8000, 3000)를 끄고
# 2. git pull 로 main 최신 코드를 받고, 바뀐 패키지만 설치, 프론트를 다시 빌드한 뒤
# 3. start-server 로 다시 켬. DB·학습 데이터·.env 는 그대로 유지됨
. (Join-Path $PSScriptRoot 'common.ps1')

Say '== 공용 서버 업데이트 =='
Test-Tools -NeedTailscale

$branch = (& git -C $Root branch --show-current)
if ($branch -ne 'main') { Fail "공용 서버 폴더는 main 브랜치여야 합니다. (현재: $branch)" }

Say '[1/4] 켜져 있는 서버 끄기'
Stop-Port $ServerBackendPort
Stop-Port $ServerFrontendPort

Say '[2/4] 최신 코드 받기 (git pull)'
& git -C $Root pull --ff-only
if ($LASTEXITCODE -ne 0) {
    Fail "git pull 에 실패했습니다. 공용 서버 폴더에서 코드를 직접 고친 적이 있으면 그 변경 때문일 수 있습니다.`n       공용 서버 폴더에서는 코드를 고치지 마세요. (git status 로 확인)"
}

Say '[3/4] 패키지 확인 + 프론트 다시 빌드'
Initialize-Backend | Out-Null
Initialize-Frontend
Push-Location $Frontend
Remove-Item Env:BACKEND_URL -ErrorAction SilentlyContinue
& npm run build
$code = $LASTEXITCODE
Pop-Location
if ($code -ne 0) { Fail '프론트 빌드에 실패했습니다. main 의 최신 코드에 문제가 있을 수 있으니 팀에 알려주세요.' }

Say '[4/4] 서버 다시 켜기'
& (Join-Path $PSScriptRoot 'start-server.ps1')
Say '이전 SERVER-backend / SERVER-frontend 창은 닫아도 됩니다.' 'Yellow'
