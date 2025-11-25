@echo off
echo ========================================
echo Flask 서버 패키지 설치
echo ========================================
echo.

REM 가상환경 활성화 (경로는 사용자 환경에 맞게 수정)
if exist "C:\venvs\myproject\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call C:\venvs\myproject\Scripts\activate.bat
) else (
    echo 가상환경을 찾을 수 없습니다!
    echo 가상환경 경로를 확인하세요: C:\venvs\myproject
    pause
    exit /b 1
)

echo.
echo 패키지 설치 중...
python -m pip install --upgrade pip
python -m pip install Flask flask-cors numpy Werkzeug

echo.
echo ========================================
echo 패키지 설치 완료!
echo ========================================
echo.
pause

