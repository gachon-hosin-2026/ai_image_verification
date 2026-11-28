# 공용 서버 끄기 + 외부 공개(Funnel) 닫기
# 1. 공용 서버 포트(8000, 3000)를 쓰는 프로그램을 종료
# 2. 실행 중인 tailscale funnel 명령을 종료해서 공개 주소를 닫음 (Tailscale 앱 자체는 그대로)
. (Join-Path $PSScriptRoot 'common.ps1')

Say '== 공용 서버 끄기 =='
Stop-Port $ServerBackendPort
Stop-Port $ServerFrontendPort
Get-Process -Name 'tailscale' -ErrorAction SilentlyContinue | ForEach-Object {
    Say "  Funnel 종료 (PID $($_.Id))"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Say '공용 서버를 껐습니다. 남은 SERVER-... 창은 닫아도 됩니다.' 'Green'
