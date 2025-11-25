# PyCharm에서 Flask 서버 실행하기

## 설정 방법

### 1. PyCharm 프로젝트 열기
1. PyCharm 실행
2. `File` → `Open` → `C:\farmui` 폴더 선택

### 2. Python 인터프리터 설정
1. `File` → `Settings` (또는 `Ctrl+Alt+S`)
2. `Project: farmui` → `Python Interpreter`
3. 가상환경 생성:
   - `Add Interpreter` → `New environment` → `venv` 폴더 선택
   - 또는 기존 가상환경 사용: `Existing environment` → `venv\Scripts\python.exe` 선택

### 3. 패키지 설치
1. PyCharm 하단의 `Terminal` 탭 열기
2. 다음 명령어 실행:
   ```bash
   pip install -r requirements.txt
   ```

### 4. Run Configuration 설정
1. `Run` → `Edit Configurations...`
2. `+` 버튼 클릭 → `Python` 선택
3. 설정:
   - **Name**: `Flask Server`
   - **Script path**: `C:\farmui\app.py` 파일 선택
   - **Working directory**: `C:\farmui` 선택
   - **Python interpreter**: 위에서 설정한 인터프리터 선택

### 5. Flask 서버 실행
1. 상단 메뉴에서 `Flask Server` 선택
2. 실행 버튼 클릭 (▶️) 또는 `Shift+F10`
3. 서버가 시작되면 자동으로 브라우저가 열립니다: `http://localhost:5000`

## 실행 확인

서버가 정상적으로 시작되면:
- PyCharm 콘솔에 다음 메시지가 표시됩니다:
  ```
  💾 메모리 모드로 실행 중... (DB 사용 안 함)
  ==================================================
  Flask 웹 서버를 시작합니다...
  서버 주소: http://localhost:5000
  ==================================================
  🌐 브라우저를 엽니다: http://localhost:5000
  * Running on http://0.0.0.0:5000
  ```

## 문제 해결

### 브라우저가 자동으로 열리지 않는 경우
- 수동으로 브라우저에서 `http://localhost:5000` 접속

### 포트가 이미 사용 중인 경우
- `app.py`의 `port=5000` 부분을 다른 포트로 변경 (예: `port=5001`)
- 또는 다른 프로그램이 5000 포트를 사용 중인지 확인

### 패키지가 설치되지 않은 경우
- PyCharm 하단의 `Terminal` 탭 열기
- `pip install -r requirements.txt` 실행

### C# 애플리케이션과 연결
- C# 애플리케이션의 "웹 연결" 버튼을 클릭하면 Flask 서버와 자동으로 연결됩니다
- Flask 서버 주소: `http://localhost:5000`

