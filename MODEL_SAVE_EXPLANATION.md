# AI 모델 저장 및 불러오기 설명

## 📌 질문: 학습한 모델이 프로그램을 꺼도 유지되나요?

**답변: 네, 유지됩니다!** 학습한 모델은 파일로 저장되어 프로그램을 꺼도 유지됩니다.

---

## 💾 모델 저장 방식

### 1. 저장 위치
- **폴더 경로**: `C:\farmui\models\`
- **자동 생성**: 프로그램 시작 시 자동으로 폴더가 생성됩니다.

### 2. 저장되는 파일들
학습이 완료되면 다음 파일들이 자동으로 저장됩니다:

1. **`anomaly_classifier.pkl`**
   - 이상 징후 분류 모델 (RandomForestClassifier)
   - 센서 데이터를 보고 정상/이상을 판단하는 모델

2. **`condition_predictor.pkl`**
   - 상태 점수 예측 모델 (RandomForestRegressor)
   - 센서 데이터를 보고 상태 점수(0.0~1.0)를 예측하는 모델

3. **`scaler.pkl`**
   - 데이터 스케일러 (StandardScaler)
   - 센서 데이터를 정규화하는 데 사용

4. **`metadata.json`**
   - 모델 메타데이터
   - 학습 시간, 학습 여부 등 정보 저장

---

## 🔄 동작 방식

### 학습 시 (`/api/ml/train` 호출 시)

```
1. 웹에서 "AI 학습 (로그 파일)" 또는 "AI 학습 (실시간 데이터)" 버튼 클릭
   ↓
2. 학습 데이터로 모델 훈련
   ↓
3. 학습 완료 후 자동으로 save_models() 호출
   ↓
4. models 폴더에 4개 파일 저장:
   - anomaly_classifier.pkl
   - condition_predictor.pkl
   - scaler.pkl
   - metadata.json
```

### 프로그램 시작 시 (`app.py` 실행 시)

```
1. Flask 서버 시작
   ↓
2. MLTrainer 인스턴스 생성
   ↓
3. 자동으로 load_models() 호출
   ↓
4. models 폴더에서 저장된 모델 파일 불러오기
   ↓
5. 모델이 있으면 is_trained = True로 설정
   - AI 자동제어에서 ML 모델 활용 가능
```

---

## 📂 models 폴더가 비어있는 이유

### 현재 비어있는 경우

**가능한 이유**:
1. **아직 한 번도 학습하지 않음**
   - 웹에서 "AI 학습" 버튼을 클릭하지 않았을 때

2. **학습은 했지만 저장 실패**
   - 파일 쓰기 권한 문제
   - 디스크 공간 부족
   - 예외 발생

### 확인 방법

1. **웹에서 학습 후 확인**:
   ```
   학습 완료 후 → models 폴더 확인
   ```

2. **프로그램 로그 확인**:
   - `flask_server.log` 파일 확인
   - "모델 저장 오류" 메시지 확인

3. **수동 확인**:
   ```powershell
   cd C:\farmui\models
   dir
   ```
   - 파일이 4개 있어야 정상

---

## ✅ 모델 저장 확인

### 학습 성공 시 출력 예시

**웹 UI에서**:
```
🧠 AI 학습 완료!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 학습 통계:
  데이터 소스: 로그 파일
  학습 데이터: 150개
  테스트 데이터: 30개

🔍 이상 징후 분류 모델:
  정확도: 85.23%
  모델 타입: RandomForestClassifier

📈 상태 점수 예측 모델:
  평균 절대 오차: 0.0523
  결정 계수 (R²): 92.45%
  모델 타입: RandomForestRegressor

✅ 모델이 성공적으로 학습되었고 저장되었습니다.
```

**models 폴더 확인**:
```
C:\farmui\models\
  ├── anomaly_classifier.pkl  (약 100KB~500KB)
  ├── condition_predictor.pkl (약 100KB~500KB)
  ├── scaler.pkl              (약 1KB~5KB)
  └── metadata.json           (약 100B~500B)
```

---

## 🔍 모델이 저장되었는지 확인하는 방법

### 1. 파일 시스템 확인
```powershell
# PowerShell에서
cd C:\farmui
Get-ChildItem models
```

**정상 출력 예시**:
```
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a----        2025-11-19   오후 5:30        123456 anomaly_classifier.pkl
-a----        2025-11-19   오후 5:30        234567 condition_predictor.pkl
-a----        2025-11-19   오후 5:30         2345 scaler.pkl
-a----        2025-11-19   오후 5:30          256 metadata.json
```

### 2. 웹 API 확인
```
GET http://localhost:5000/api/ml/status
```

**응답 예시**:
```json
{
  "success": true,
  "is_trained": true,
  "has_classifier": true,
  "has_predictor": true
}
```

- `is_trained: true` → 모델이 학습되어 있음
- `has_classifier: true` → 이상 징후 분류 모델 있음
- `has_predictor: true` → 상태 점수 예측 모델 있음

### 3. 메타데이터 확인
```powershell
cd C:\farmui\models
Get-Content metadata.json
```

**출력 예시**:
```json
{
  "trained_at": "2025-11-19T17:30:45.123456",
  "is_trained": true
}
```

---

## ⚠️ 주의사항

### 1. 파일 삭제 시
- `models` 폴더의 파일을 삭제하면 → 모델이 사라집니다
- 프로그램을 다시 시작하면 → `is_trained = false` 상태가 됩니다
- 다시 학습해야 합니다

### 2. 백업 권장
- 중요한 모델은 별도로 백업하세요
- `models` 폴더 전체를 복사하면 됩니다

### 3. 파일 크기
- 각 모델 파일은 약 100KB~500KB 정도입니다
- 총 약 300KB~1.5MB 정도 차지합니다

---

## 🔧 문제 해결

### 모델이 저장되지 않는 경우

#### 1. 권한 문제
```powershell
# 관리자 권한으로 실행
# 또는 C:\farmui\models 폴더에 쓰기 권한 확인
```

#### 2. 디스크 공간 확인
```powershell
Get-PSDrive C | Select-Object Used,Free
```

#### 3. 로그 확인
```powershell
cd C:\farmui
Get-Content flask_server.log -Tail 50
# "모델 저장 오류" 메시지 확인
```

#### 4. 수동 저장 테스트
Python 인터프리터에서:
```python
import os
test_file = os.path.join("models", "test.txt")
with open(test_file, "w") as f:
    f.write("test")
# 성공하면 파일 쓰기 권한 정상
```

---

## 📝 요약

### ✅ 네, 학습한 모델은 저장됩니다!

1. **학습 시**: `models` 폴더에 4개 파일 자동 저장
2. **프로그램 시작 시**: 저장된 모델 자동 불러오기
3. **프로그램 종료 후**: 모델 파일은 그대로 유지됨
4. **다음 실행 시**: 자동으로 모델을 불러와서 사용

### 🔍 models 폴더가 비어있는 이유

- **아직 학습하지 않음** (가장 가능성 높음)
- **학습 실패**
- **저장 실패** (권한 문제 등)

### ✅ 확인 방법

1. 웹에서 학습 실행
2. `C:\farmui\models` 폴더 확인
3. 4개 파일이 있으면 정상 저장됨

---

**결론**: 학습한 모델은 파일로 저장되어 프로그램을 꺼도 유지됩니다! 🎯

