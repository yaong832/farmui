# AI 학습 전략 및 자동 제어 구현 방안

## 현재 AI의 학습 방식

### ❌ 현재 상태: 학습하지 않음
현재 AI 시스템은 **규칙 기반 시스템(Rule-based System)**입니다.

**동작 방식:**
1. **미리 정의된 규칙 사용**: `crop_config.py`에 정의된 최적 조건 사용
2. **통계적 분석**: 평균, 표준편차, Z-score 등 통계 수치 사용
3. **임계값 비교**: 고정된 최적/허용/위험 범위와 비교

**장점:**
- 즉시 사용 가능
- 안정적이고 예측 가능
- 특별한 학습 데이터 불필요

**단점:**
- 실제 농장 환경에 맞게 개선되지 않음
- 경험 데이터를 활용하지 못함
- 자동 제어 불가능

---

## 향후 학습 및 자동 제어 방안

### 1. 로그 데이터 기반 학습 전략

#### A. 강화학습 (Reinforcement Learning) ⭐ 추천

**개념:**
- AI가 환경(센서 데이터)을 관찰하고 행동(제어 명령)을 선택
- 결과(로그에서 경고/복귀 상태)를 보고 학습
- 시행착오를 통해 최적 정책 학습

**구조:**
```
환경 (Environment)
  ↓ [관찰] 센서 데이터, 현재 상태
AI 에이전트 (Agent)
  ↓ [행동] 온도 증가, 습도 감소 등 제어 명령
PLC 제어 시스템
  ↓ [결과] 센서 변화, 경고 해소/발생
환경 → [보상] 로그 분석 (경고 해소 = +보상, 경고 발생 = -보상)
```

**필요한 데이터:**
1. **상태 (State)**: 센서 데이터 (습도, 온도, 채광, 토양습도)
2. **행동 (Action)**: 제어 명령 (온도+5℃, 습도-10% 등)
3. **보상 (Reward)**: 로그에서 추출
   - 경고 해소: +10점
   - 정상 상태 유지: +1점
   - 경고 발생: -5점
   - 위험 상태: -20점

**학습 데이터 수집:**
```python
# 학습 데이터 구조
{
    "state": {
        "humidity": 65.3,
        "temperature": 22.1,
        "light": 70.5,
        "soil_moisture": 45.2,
        "time_of_day": 14,  # 시간대
        "day_of_year": 120  # 연중 일수
    },
    "action": {
        "type": "temperature_adjust",
        "value": +3,  # 3℃ 증가
        "timestamp": "2025-11-03 14:30:00"
    },
    "reward": 5,  # 경고 해소로 +5점
    "next_state": {
        "humidity": 65.1,
        "temperature": 25.1,  # 온도 증가됨
        "light": 70.3,
        "soil_moisture": 45.0
    },
    "done": False  # 에피소드 종료 여부
}
```

**구현 방법:**
```python
# 예시: DQN (Deep Q-Network) 사용
import torch
import torch.nn as nn
import numpy as np

class FarmControlAgent(nn.Module):
    """농장 제어 강화학습 에이전트"""
    
    def __init__(self, state_size=4, action_size=8):
        super().__init__()
        # 상태: 습도, 온도, 채광, 토양습도
        # 행동: 온도+/-5℃, 습도+/-10%, 채광+/-10%, 토양습도+/-10%
        
        self.fc1 = nn.Linear(state_size, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, action_size)
    
    def forward(self, state):
        x = torch.relu(self.fc1(state))
        x = torch.relu(self.fc2(x))
        return self.fc3(x)
```

---

#### B. 행동-결과 매핑 학습 (Supervised Learning)

**개념:**
- 로그에서 사용자의 제어 행동과 결과를 추출
- "이 상황에서는 이 행동이 좋았다" 학습
- 분류 또는 회귀 모델 사용

**학습 데이터 수집:**
```python
# 로그에서 추출한 학습 데이터 예시
logs = [
    "⚠️ 습도가 25%로 낮습니다. (목표: 30-80%)",
    # ... 시간 경과 ...
    "[사용자가 가습기 조절]",
    "✅ 습도가 65%로 정상 복귀했습니다."
]

# 추출된 학습 데이터
training_data = {
    "input": {
        "humidity": 25.0,  # 경고 발생 시 센서값
        "temperature": 22.0,
        "light": 70.0,
        "soil_moisture": 45.0,
        "warning_type": "humidity_low"  # 경고 유형
    },
    "output": {
        "action": "increase_humidity",  # 취한 행동
        "amount": +40,  # 증가량
        "success": True  # 성공 여부 (복귀 로그 있음)
    }
}
```

**구현 방법:**
```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

class ActionPredictor:
    """행동 예측 모델"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.trained = False
    
    def train_from_logs(self, logs):
        """로그에서 학습 데이터 추출 및 학습"""
        training_data = []
        
        for i, log in enumerate(logs):
            # 경고 발생 로그 찾기
            if "⚠️" in log.message:
                warning_type = self._extract_warning_type(log.message)
                sensor_values = self._extract_sensor_values(log.message)
                
                # 이후 로그에서 복귀 확인
                recovery_log = self._find_recovery_log(logs[i:])
                if recovery_log:
                    action = self._infer_action(sensor_values, recovery_log)
                    training_data.append({
                        **sensor_values,
                        "warning_type": warning_type,
                        "recommended_action": action,
                        "success": True
                    })
        
        if training_data:
            df = pd.DataFrame(training_data)
            X = df.drop(['recommended_action', 'success'], axis=1)
            y = df['recommended_action']
            
            self.model.fit(X, y)
            self.trained = True
    
    def predict_action(self, sensor_data, warning_type):
        """상황에 맞는 행동 예측"""
        if not self.trained:
            return None
        
        features = {
            **sensor_data,
            "warning_type": warning_type
        }
        return self.model.predict([features])[0]
```

---

#### C. 시계열 예측 모델 (Time Series Forecasting)

**개념:**
- 과거 센서 데이터 패턴 학습
- 미래 센서값 예측
- 예측 기반으로 사전 제어

**구현 방법:**
```python
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

class SensorForecaster:
    """센서값 예측 모델"""
    
    def __init__(self, sequence_length=60):  # 60분 데이터로 예측
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler()
    
    def prepare_data(self, sensor_history):
        """시계열 데이터 준비"""
        # 센서 데이터를 시퀀스로 변환
        X, y = [], []
        
        for i in range(len(sensor_history) - self.sequence_length):
            seq = sensor_history[i:i+self.sequence_length]
            target = sensor_history[i+self.sequence_length]
            
            X.append(seq)
            y.append(target)
        
        return np.array(X), np.array(y)
    
    def train(self, sensor_history):
        """모델 학습"""
        X, y = self.prepare_data(sensor_history)
        
        # 정규화
        X_scaled = self.scaler.fit_transform(X.reshape(-1, 4)).reshape(X.shape)
        y_scaled = self.scaler.transform(y)
        
        # LSTM 모델 구축
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(self.sequence_length, 4)),
            LSTM(50, return_sequences=False),
            Dense(25),
            Dense(4)  # 4개 센서값 예측
        ])
        
        self.model.compile(optimizer='adam', loss='mse')
        self.model.fit(X_scaled, y_scaled, epochs=50, batch_size=32, verbose=0)
    
    def predict_next(self, recent_data):
        """다음 센서값 예측"""
        if self.model is None:
            return None
        
        # 최근 데이터로 예측
        seq = np.array([recent_data[-self.sequence_length:]])
        seq_scaled = self.scaler.transform(seq.reshape(-1, 4)).reshape(seq.shape)
        
        prediction = self.model.predict(seq_scaled, verbose=0)
        prediction = self.scaler.inverse_transform(prediction)
        
        return prediction[0]
```

---

### 2. 로그 데이터 활용 방법

#### A. 로그 파싱 및 데이터 추출

```python
class LogParser:
    """로그에서 학습 데이터 추출"""
    
    def parse_warning_logs(self, logs):
        """경고 로그 파싱"""
        warnings = []
        
        for log in logs:
            if "⚠️" in log['message']:
                # 센서값 추출
                sensor_data = self._extract_sensor_values(log['message'])
                sensor_data['timestamp'] = log['timestamp']
                sensor_data['message'] = log['message']
                
                # 경고 유형 분류
                sensor_data['warning_type'] = self._classify_warning(log['message'])
                
                warnings.append(sensor_data)
        
        return warnings
    
    def parse_recovery_logs(self, logs):
        """복귀 로그 파싱"""
        recoveries = []
        
        for log in logs:
            if "✅" in log['message'] or "정상 복귀" in log['message']:
                sensor_data = self._extract_sensor_values(log['message'])
                sensor_data['timestamp'] = log['timestamp']
                sensor_data['recovered'] = True
                
                recoveries.append(sensor_data)
        
        return recoveries
    
    def extract_action_patterns(self, logs):
        """행동 패턴 추출"""
        patterns = []
        
        # 경고 → 복귀 패턴 찾기
        warnings = self.parse_warning_logs(logs)
        recoveries = self.parse_recovery_logs(logs)
        
        for warning in warnings:
            # 경고 후 일정 시간 내 복귀 찾기
            recovery = self._find_recovery(warning, recoveries, time_window=3600)  # 1시간 내
            
            if recovery:
                # 센서값 변화 분석
                change = {
                    'humidity': recovery.get('humidity', 0) - warning.get('humidity', 0),
                    'temperature': recovery.get('temperature', 0) - warning.get('temperature', 0),
                    'light': recovery.get('light', 0) - warning.get('light', 0),
                    'soil_moisture': recovery.get('soil_moisture', 0) - warning.get('soil_moisture', 0)
                }
                
                patterns.append({
                    'initial_state': warning,
                    'change': change,
                    'final_state': recovery,
                    'time_taken': (recovery['timestamp'] - warning['timestamp']).total_seconds()
                })
        
        return patterns
```

---

### 3. 자동 제어 구현 구조

```python
class AutoController:
    """AI 기반 자동 제어 시스템"""
    
    def __init__(self, learning_model, forecast_model):
        self.learning_model = learning_model  # 강화학습 또는 행동 예측 모델
        self.forecast_model = forecast_model  # 시계열 예측 모델
        self.action_history = []  # 행동 이력
    
    def decide_action(self, current_sensor_data, logs):
        """현재 상황에 맞는 제어 행동 결정"""
        
        # 1. 경고 상태 확인
        warnings = self._check_warnings(current_sensor_data)
        
        if warnings:
            # 2. 학습된 모델로 행동 예측
            action = self.learning_model.predict_action(
                current_sensor_data, 
                warnings[0]['type']
            )
            
            # 3. 예측 모델로 행동 후 결과 예측
            if action:
                predicted_result = self._predict_action_result(
                    current_sensor_data, 
                    action
                )
                
                # 4. 예측 결과가 좋으면 실행
                if predicted_result['score'] > 0.7:
                    return action
        
        # 5. 예방적 제어 (경고 전 미리 조절)
        if self.forecast_model:
            future_state = self.forecast_model.predict_next(current_sensor_data)
            if self._will_be_warning(future_state):
                preventive_action = self._suggest_preventive_action(
                    current_sensor_data, 
                    future_state
                )
                return preventive_action
        
        return None  # 조치 불필요
    
    def execute_action(self, action):
        """PLC에 제어 명령 전송"""
        # C# UI와 통신하여 제어 명령 전송
        # HTTP POST to C# application
        
        command = {
            'type': action['type'],  # 'temperature', 'humidity', etc.
            'value': action['value'],  # 조절량
            'timestamp': datetime.now().isoformat()
        }
        
        # Flask에서 C#로 명령 전송 (역방향 통신)
        # 또는 C#가 Flask를 폴링하여 명령 확인
    
    def learn_from_result(self, action, result_logs):
        """행동 결과를 보고 학습"""
        # 행동 후 로그 분석
        success = self._analyze_action_result(result_logs)
        
        # 강화학습 모델에 경험 추가
        if self.learning_model:
            experience = {
                'state': action['initial_state'],
                'action': action,
                'reward': 10 if success else -5,
                'next_state': action['final_state']
            }
            self.learning_model.add_experience(experience)
```

---

### 4. 학습 데이터 수집 전략

#### 즉시 가능한 방법:

1. **로그에서 경고-복귀 패턴 추출**
   - 경고 발생 시 센서값
   - 복귀 시 센서값
   - 시간 차이 분석

2. **센서 데이터 시계열 저장**
   - 주기적으로 센서 데이터 저장
   - 정상/경고 상태 레이블링

3. **행동-결과 매핑 수집**
   - 사용자가 수동 조절한 경우 로그
   - 조절 후 결과 확인

#### 개선이 필요한 방법:

1. **실제 생산량 데이터 수집**
   - 수확 시 생산량 기록
   - 재배 기간 동안 센서 데이터와 매핑

2. **제어 이력 저장**
   - 사용자가 취한 모든 제어 행동 기록
   - 제어 전/후 센서값 비교

---

### 5. 구현 단계

#### Phase 1: 데이터 수집 시스템 구축
- 로그 파싱 모듈 구현
- 센서 데이터 저장 강화
- 행동-결과 매핑 데이터 수집

#### Phase 2: 기초 학습 모델 구현
- 행동 예측 모델 (Supervised Learning)
- 간단한 규칙 기반 자동 제어

#### Phase 3: 고급 학습 모델 구현
- 강화학습 에이전트
- 시계열 예측 모델

#### Phase 4: 자동 제어 시스템 통합
- AI 결정을 PLC 제어로 변환
- 안전장치 및 승인 시스템

---

## 결론

**현재:**
- ❌ 학습하지 않는 규칙 기반 시스템
- ✅ 로그 데이터 수집 가능
- ✅ 센서 데이터 수집 가능

**향후:**
- ✅ 로그에서 행동-결과 패턴 학습
- ✅ 강화학습으로 최적 제어 정책 학습
- ✅ 시계열 예측으로 예방적 제어
- ✅ 자동 제어 시스템 구현

**필요한 작업:**
1. 로그 파싱 및 데이터 추출 모듈 구현
2. 학습 데이터 저장 시스템 구축
3. 기초 학습 모델 구현 및 테스트
4. 자동 제어 API 구현 (Flask → C# 통신)

