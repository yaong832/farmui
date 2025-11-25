# Flask 서버 패키지 설치 스크립트

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Flask 서버 패키지 설치" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 가상환경 경로 (사용자 환경에 맞게 수정)
$venvPath = "C:\venvs\myproject"

# 가상환경 활성화
if (Test-Path "$venvPath\Scripts\Activate.ps1") {
    Write-Host "가상환경 활성화 중..." -ForegroundColor Green
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "가상환경을 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "가상환경 경로를 확인하세요: $venvPath" -ForegroundColor Yellow
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}

Write-Host ""
Write-Host "패키지 설치 중..." -ForegroundColor Green
python -m pip install --upgrade pip
python -m pip install Flask flask-cors numpy Werkzeug

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "패키지 설치 완료!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "계속하려면 Enter를 누르세요"

