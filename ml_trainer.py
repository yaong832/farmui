"""
머신러닝 모델 훈련 및 예측 모듈
로그 데이터 또는 실시간 센서 데이터에서 센서 데이터와 상태를 학습하여 예측 모델 생성
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import os
import pickle
from collections import defaultdict

try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn이 설치되지 않았습니다. AI 학습 기능을 사용하려면 'pip install scikit-learn'을 실행하세요.")


class MLTrainer:
    """머신러닝 모델 훈련 클래스"""
    
    def __init__(self, model_dir: str = "models"):
        """
        Args:
            model_dir: 모델 저장 디렉토리
        """
        self.model_dir = model_dir
        self.scaler = None
        self.anomaly_classifier = None  # 이상 징후 분류 모델
        self.condition_predictor = None  # 상태 점수 예측 모델
        self.is_trained = False
        
        # 모델 디렉토리 생성
        os.makedirs(model_dir, exist_ok=True)
    
    def extract_training_data_from_sensor_data(self, sensor_data_list: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[int], List[float]]:
        """실시간 센서 데이터에서 학습 데이터 추출"""
        try:
            from crop_config import get_crop_conditions
        except ImportError:
            # crop_config가 없으면 기본값 사용
            def get_crop_conditions(farm_id):
                default_conditions = {
                    'humidity': {'optimal': (50, 80)},
                    'temperature': {'optimal': (15, 25)},
                    'light': {'optimal': (50, 80)},
                    'soil_moisture': {'optimal': (40, 60)}
                }
                return default_conditions, '기본', False
        
        features = []  # [humidity, temperature, light, soil_moisture]
        labels = []  # 0: 정상, 1: 이상
        scores = []  # 0.0 ~ 1.0
        
        for data in sensor_data_list:
            humidity = data.get('humidity')
            temperature = data.get('temperature')
            light = data.get('light')
            soil_moisture = data.get('soil_moisture')
            
            # 4개 센서 데이터가 모두 있어야 학습 데이터로 사용
            if any(x is None for x in [humidity, temperature, light, soil_moisture]):
                continue
            
            # 특징 벡터 생성 [습도, 온도, 채광, 토양습도]
            feature = [humidity, temperature, light, soil_moisture]
            features.append(feature)
            
            # 레이블 및 점수 계산 (실시간 데이터는 상태 정보가 없으므로 값 범위로 판단)
            # 작물 최적 조건 기준으로 정상/이상 판단
            crop_conditions, _, _ = get_crop_conditions(farm_id=data.get('farm_id', 1))
            
            # 정상 범위 확인
            humidity_optimal = crop_conditions.get('humidity', {}).get('optimal', (50, 80))
            temp_optimal = crop_conditions.get('temperature', {}).get('optimal', (15, 25))
            light_optimal = crop_conditions.get('light', {}).get('optimal', (50, 80))
            soil_optimal = crop_conditions.get('soil_moisture', {}).get('optimal', (40, 60))
            
            # 정상 범위 내에 있는지 확인
            is_normal = (
                humidity_optimal[0] <= humidity <= humidity_optimal[1] and
                temp_optimal[0] <= temperature <= temp_optimal[1] and
                light_optimal[0] <= light <= light_optimal[1] and
                soil_optimal[0] <= soil_moisture <= soil_optimal[1]
            )
            
            if is_normal:
                labels.append(0)  # 정상
                # 정상 범위 내에 있으면 높은 점수
                score = 0.9
                # 최적 값에 가까울수록 높은 점수
                if (humidity_optimal[0] + 5 <= humidity <= humidity_optimal[1] - 5 and
                    temp_optimal[0] + 2 <= temperature <= temp_optimal[1] - 2 and
                    light_optimal[0] + 5 <= light <= light_optimal[1] - 5 and
                    soil_optimal[0] + 5 <= soil_moisture <= soil_optimal[1] - 5):
                    score = 0.95
                scores.append(score)
            else:
                labels.append(1)  # 이상
                # 이상 정도에 따라 점수 조정
                score = 0.5
                
                # 각 센서별로 이상 정도 계산
                deviations = []
                if humidity < humidity_optimal[0] or humidity > humidity_optimal[1]:
                    deviations.append(abs(humidity - (humidity_optimal[0] + humidity_optimal[1]) / 2))
                if temperature < temp_optimal[0] or temperature > temp_optimal[1]:
                    deviations.append(abs(temperature - (temp_optimal[0] + temp_optimal[1]) / 2))
                if light < light_optimal[0] or light > light_optimal[1]:
                    deviations.append(abs(light - (light_optimal[0] + light_optimal[1]) / 2))
                if soil_moisture < soil_optimal[0] or soil_moisture > soil_optimal[1]:
                    deviations.append(abs(soil_moisture - (soil_optimal[0] + soil_optimal[1]) / 2))
                
                if deviations:
                    avg_deviation = sum(deviations) / len(deviations)
                    if avg_deviation > 20:
                        score = 0.3
                    elif avg_deviation > 10:
                        score = 0.4
                
                scores.append(score)
        
        return features, labels, scores
    
    def extract_training_data_from_logs(self, logs: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[int], List[float]]:
        """
        로그에서 학습 데이터 추출
        
        Args:
            logs: 로그 리스트
            
        Returns:
            (features, labels, scores) 튜플
            - features: 센서 데이터 리스트 [[습도, 온도, 채광, 토양습도], ...]
            - labels: 이상 징후 레이블 [0=정상, 1=이상]
            - scores: 상태 점수 [0.0~1.0]
        """
        import re
        
        features = []
        labels = []
        scores = []
        
        for log in logs:
            message = log.get('message', '')
            
            # 센서 데이터 추출
            sensor_data = {
                'humidity': None,
                'temperature': None,
                'light': None,
                'soil_moisture': None
            }
            
            # 형식 1: 웹 표준 형식 우선 파싱: "센서데이터 습도:55.2% 온도:22.1℃ 채광:65.3% 토양습도:48.5%"
            if '센서데이터' in message:
                # 새 형식: 습도:값% 온도:값℃ 채광:값% 토양습도:값%
                humidity_match = re.search(r'습도:(\d+\.?\d*)\s*%', message)
                if humidity_match:
                    sensor_data['humidity'] = float(humidity_match.group(1))
                
                temp_match = re.search(r'온도:(\d+\.?\d*)\s*[℃°C]', message)
                if temp_match:
                    sensor_data['temperature'] = float(temp_match.group(1))
                
                light_match = re.search(r'채광:(\d+\.?\d*)\s*%', message)
                if light_match:
                    sensor_data['light'] = float(light_match.group(1))
                
                # 토양습도: 공백 포함/미포함 모두 지원
                soil_match = re.search(r'토양\s*습도:(\d+\.?\d*)\s*%', message)
                if soil_match:
                    sensor_data['soil_moisture'] = float(soil_match.group(1))
            # 형식 2: 실시간 데이터 저장 형식: "온도: 21.8°C습도: 26.7%채광: 1.3%토양 습도: 0.1%"
            elif '온도:' in message and '습도:' in message and ('채광:' in message or '토양' in message):
                # 실시간 데이터 형식: 온도:값°C습도:값%채광:값%토양 습도:값%
                temp_match = re.search(r'온도:\s*(\d+\.?\d*)\s*[℃°C]', message)
                if temp_match:
                    sensor_data['temperature'] = float(temp_match.group(1))
                
                humidity_match = re.search(r'습도:\s*(\d+\.?\d*)\s*%', message)
                if humidity_match:
                    sensor_data['humidity'] = float(humidity_match.group(1))
                
                light_match = re.search(r'채광:\s*(\d+\.?\d*)\s*%', message)
                if light_match:
                    sensor_data['light'] = float(light_match.group(1))
                
                # 토양 습도: 공백 포함/미포함 모두 지원
                soil_match = re.search(r'토양\s*습도:\s*(\d+\.?\d*)\s*%', message)
                if soil_match:
                    sensor_data['soil_moisture'] = float(soil_match.group(1))
            else:
                # 기존 형식 지원 (하위 호환성)
                humidity_match = re.search(r'습도[^()]*\([^)]*?(\d+\.?\d*)\s*%', message)
                if humidity_match:
                    sensor_data['humidity'] = float(humidity_match.group(1))
                
                temp_match = re.search(r'온도[^()]*?\([^)]*?(\d+\.?\d*)\s*℃', message)
                if temp_match:
                    sensor_data['temperature'] = float(temp_match.group(1))
                
                light_match = re.search(r'채광[^()]*?\([^)]*?(\d+\.?\d*)\s*%', message)
                if light_match:
                    sensor_data['light'] = float(light_match.group(1))
                
                soil_match = re.search(r'토양습도[^()]*?\([^)]*?(\d+\.?\d*)\s*%', message)
                if soil_match:
                    sensor_data['soil_moisture'] = float(soil_match.group(1))
            
            # 4개 센서 데이터가 모두 있어야 학습 데이터로 사용
            if all([sensor_data['humidity'] is not None,
                   sensor_data['temperature'] is not None,
                   sensor_data['light'] is not None,
                   sensor_data['soil_moisture'] is not None]):
                
                # 특징 벡터 생성 [습도, 온도, 채광, 토양습도]
                feature = [
                    sensor_data['humidity'],
                    sensor_data['temperature'],
                    sensor_data['light'],
                    sensor_data['soil_moisture']
                ]
                features.append(feature)
                
                # 레이블 추출 (⚠️ = 이상, ✅ = 정상)
                # 새 형식 우선: "상태:정상" 또는 "상태:이상"
                status_match = re.search(r'상태:(\w+)', message)
                score = 0.85  # 기본값
                
                if status_match:
                    # 새 형식 사용
                    status = status_match.group(1)
                    if status == '이상':
                        labels.append(1)  # 이상 징후
                        score = 0.5  # 기본값
                        
                        # 값 범위에 따라 점수 조정
                        if sensor_data.get('humidity', 50) < 30 or sensor_data.get('temperature', 20) < 5 or \
                           sensor_data.get('humidity', 50) > 90 or sensor_data.get('temperature', 20) > 40:
                            score = 0.3
                        elif sensor_data.get('humidity', 50) < 40 or sensor_data.get('temperature', 20) < 10 or \
                             sensor_data.get('humidity', 50) > 80 or sensor_data.get('temperature', 20) > 35:
                            score = 0.4
                    else:
                        labels.append(0)  # 정상
                        # 정상 범위 내에 있으면 높은 점수
                        if (50 <= sensor_data.get('humidity', 50) <= 80 and
                            15 <= sensor_data.get('temperature', 20) <= 30 and
                            50 <= sensor_data.get('light', 50) <= 80 and
                            40 <= sensor_data.get('soil_moisture', 50) <= 60):
                            score = 0.95
                    
                    scores.append(score)
                elif '⚠️' in message or '경고' in message or '값 낮음' in message or '값 높음' in message:
                    # 기존 형식 지원 (하위 호환성)
                    labels.append(1)  # 이상 징후
                    score = 0.5  # 기본값
                    
                    # 낮음/높음 정도에 따라 점수 조정
                    if '값 낮음' in message:
                        if sensor_data.get('humidity', 50) < 30 or sensor_data.get('temperature', 20) < 5:
                            score = 0.3
                        elif sensor_data.get('humidity', 50) < 40 or sensor_data.get('temperature', 20) < 10:
                            score = 0.4
                    elif '값 높음' in message:
                        if sensor_data.get('humidity', 50) > 90 or sensor_data.get('temperature', 20) > 40:
                            score = 0.3
                        elif sensor_data.get('humidity', 50) > 80 or sensor_data.get('temperature', 20) > 35:
                            score = 0.4
                    
                    scores.append(score)
                elif '✅' in message or '정상' in message:
                    # 기존 형식 지원 (하위 호환성)
                    labels.append(0)  # 정상
                    score = 0.85  # 기본값
                    
                    # 정상 범위 내에 있으면 높은 점수
                    if '현재값:' in message or '센서데이터' in message:
                        if (50 <= sensor_data.get('humidity', 50) <= 80 and
                            15 <= sensor_data.get('temperature', 20) <= 30 and
                            50 <= sensor_data.get('light', 50) <= 80 and
                            40 <= sensor_data.get('soil_moisture', 50) <= 60):
                            score = 0.95
                        elif (50 <= sensor_data.get('humidity', 50) <= 80 and
                              15 <= sensor_data.get('temperature', 20) <= 30):
                            score = 0.90
                    
                    scores.append(score)
                else:
                    # 레이블이 명확하지 않은 경우 기본값 (정상으로 간주)
                    labels.append(0)
                    scores.append(0.7)
        
        return features, labels, scores
    
    def train_models(self, logs: Optional[List[Dict[str, Any]]] = None, 
                     sensor_data: Optional[List[Dict[str, Any]]] = None,
                     test_size: float = 0.2) -> Dict[str, Any]:
        """
        로그 데이터 또는 실시간 센서 데이터로 모델 훈련
        
        Args:
            logs: 로그 리스트 (로그 기반 학습 시)
            sensor_data: 실시간 센서 데이터 리스트 (실시간 데이터 기반 학습 시)
            test_size: 테스트 데이터 비율
            
        Returns:
            훈련 결과 딕셔너리
        """
        if not SKLEARN_AVAILABLE:
            return {
                "success": False,
                "error": "scikit-learn이 설치되지 않았습니다. 'pip install scikit-learn'을 실행하세요."
            }
        
        # 학습 데이터 추출 (로그 또는 실시간 데이터)
        if sensor_data is not None:
            # 실시간 센서 데이터 사용
            features, labels, scores = self.extract_training_data_from_sensor_data(sensor_data)
        elif logs is not None:
            # 로그 데이터 사용
            features, labels, scores = self.extract_training_data_from_logs(logs)
        else:
            return {
                "success": False,
                "error": "학습 데이터가 제공되지 않았습니다. 로그 데이터 또는 실시간 센서 데이터를 제공해주세요."
            }
        
        if len(features) < 10:
            return {
                "success": False,
                "error": f"학습 데이터가 부족합니다. (필요: 최소 10개, 현재: {len(features)}개)"
            }
        
        # numpy 배열로 변환
        X = np.array(features)
        y_labels = np.array(labels)
        y_scores = np.array(scores)
        
        # 데이터 스케일링
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # 훈련/테스트 데이터 분리
        X_train, X_test, y_train_labels, y_test_labels, y_train_scores, y_test_scores = train_test_split(
            X_scaled, y_labels, y_scores, test_size=test_size, random_state=42
        )
        
        # 1. 이상 징후 분류 모델 훈련
        self.anomaly_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.anomaly_classifier.fit(X_train, y_train_labels)
        
        # 분류 정확도 평가
        y_pred_labels = self.anomaly_classifier.predict(X_test)
        accuracy = accuracy_score(y_test_labels, y_pred_labels)
        
        # 2. 상태 점수 예측 모델 훈련
        self.condition_predictor = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.condition_predictor.fit(X_train, y_train_scores)
        
        # 회귀 점수 평가
        y_pred_scores = self.condition_predictor.predict(X_test)
        score_mae = np.mean(np.abs(y_test_scores - y_pred_scores))
        score_r2 = 1 - (np.sum((y_test_scores - y_pred_scores) ** 2) / 
                       np.sum((y_test_scores - np.mean(y_test_scores)) ** 2))
        
        self.is_trained = True
        
        # 모델 저장
        self.save_models()
        
        return {
            "success": True,
            "training_samples": len(features),
            "test_samples": len(X_test),
            "anomaly_classifier": {
                "accuracy": float(accuracy),
                "model_type": "RandomForestClassifier"
            },
            "condition_predictor": {
                "mae": float(score_mae),
                "r2": float(score_r2),
                "model_type": "RandomForestRegressor"
            },
            "message": f"모델 훈련 완료! 이상 징후 분류 정확도: {accuracy:.2%}"
        }
    
    def predict_anomaly(self, humidity: float, temperature: float, 
                       light: float, soil_moisture: float) -> Dict[str, Any]:
        """
        이상 징후 예측
        
        Args:
            humidity: 습도 (%)
            temperature: 온도 (℃)
            light: 채광 (%)
            soil_moisture: 토양습도 (%)
            
        Returns:
            예측 결과 딕셔너리
        """
        if not self.is_trained or self.anomaly_classifier is None:
            return {
                "success": False,
                "error": "모델이 훈련되지 않았습니다. 먼저 학습 데이터로 훈련하세요."
            }
        
        if not SKLEARN_AVAILABLE:
            return {
                "success": False,
                "error": "scikit-learn이 설치되지 않았습니다."
            }
        
        # 특징 벡터 생성
        feature = np.array([[humidity, temperature, light, soil_moisture]])
        
        # 스케일링
        feature_scaled = self.scaler.transform(feature)
        
        # 예측
        prediction = self.anomaly_classifier.predict(feature_scaled)[0]
        probability = self.anomaly_classifier.predict_proba(feature_scaled)[0]
        
        return {
            "success": True,
            "is_anomaly": bool(prediction),
            "anomaly_probability": float(probability[1]),
            "normal_probability": float(probability[0])
        }
    
    def predict_condition_score(self, humidity: float, temperature: float,
                               light: float, soil_moisture: float) -> Dict[str, Any]:
        """
        상태 점수 예측
        
        Args:
            humidity: 습도 (%)
            temperature: 온도 (℃)
            light: 채광 (%)
            soil_moisture: 토양습도 (%)
            
        Returns:
            예측 점수 (0.0~1.0)
        """
        if not self.is_trained or self.condition_predictor is None:
            return {
                "success": False,
                "error": "모델이 훈련되지 않았습니다."
            }
        
        if not SKLEARN_AVAILABLE:
            return {
                "success": False,
                "error": "scikit-learn이 설치되지 않았습니다."
            }
        
        # 특징 벡터 생성
        feature = np.array([[humidity, temperature, light, soil_moisture]])
        
        # 스케일링
        feature_scaled = self.scaler.transform(feature)
        
        # 예측
        score = self.condition_predictor.predict(feature_scaled)[0]
        score = max(0.0, min(1.0, score))  # 0~1 범위로 제한
        
        return {
            "success": True,
            "score": float(score),
            "score_percentage": float(score * 100)
        }
    
    def save_models(self):
        """모델 저장"""
        if not self.is_trained:
            return
        
        try:
            # 모델 저장
            if self.anomaly_classifier:
                with open(os.path.join(self.model_dir, "anomaly_classifier.pkl"), "wb") as f:
                    pickle.dump(self.anomaly_classifier, f)
            
            if self.condition_predictor:
                with open(os.path.join(self.model_dir, "condition_predictor.pkl"), "wb") as f:
                    pickle.dump(self.condition_predictor, f)
            
            if self.scaler:
                with open(os.path.join(self.model_dir, "scaler.pkl"), "wb") as f:
                    pickle.dump(self.scaler, f)
            
            # 메타데이터 저장
            metadata = {
                "trained_at": datetime.now().isoformat(),
                "is_trained": self.is_trained
            }
            with open(os.path.join(self.model_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"모델 저장 오류: {e}", exc_info=True)
            raise  # 예외를 다시 발생시켜서 호출자가 알 수 있도록
    
    def load_models(self) -> bool:
        """
        저장된 모델 불러오기
        
        Returns:
            True: 모델 불러오기 성공
            False: 모델 파일이 없거나 불러오기 실패
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # 모델 디렉토리 확인
            if not os.path.exists(self.model_dir):
                os.makedirs(self.model_dir, exist_ok=True)
                logger.info(f"모델 디렉토리 생성: {self.model_dir}")
                logger.info("⚠️ 모델 파일이 없습니다. AI 학습을 통해 모델을 생성하세요.")
                return False
            
            # 메타데이터 확인
            metadata_path = os.path.join(self.model_dir, "metadata.json")
            if not os.path.exists(metadata_path):
                logger.info(f"모델 메타데이터 파일이 없습니다: {metadata_path}")
                return False
            
            # 메타데이터 읽기
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                logger.info(f"모델 메타데이터 불러오기 성공 (학습 시간: {metadata.get('trained_at', 'N/A')})")
            except Exception as e:
                logger.warning(f"메타데이터 읽기 오류: {e}")
            
            # 모델 불러오기
            loaded_count = 0
            classifier_path = os.path.join(self.model_dir, "anomaly_classifier.pkl")
            predictor_path = os.path.join(self.model_dir, "condition_predictor.pkl")
            scaler_path = os.path.join(self.model_dir, "scaler.pkl")
            
            if os.path.exists(classifier_path):
                with open(classifier_path, "rb") as f:
                    self.anomaly_classifier = pickle.load(f)
                loaded_count += 1
                logger.info(f"이상 징후 분류 모델 불러오기 성공: {classifier_path}")
            
            if os.path.exists(predictor_path):
                with open(predictor_path, "rb") as f:
                    self.condition_predictor = pickle.load(f)
                loaded_count += 1
                logger.info(f"상태 점수 예측 모델 불러오기 성공: {predictor_path}")
            
            if os.path.exists(scaler_path):
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
                loaded_count += 1
                logger.info(f"데이터 스케일러 불러오기 성공: {scaler_path}")
            
            if loaded_count > 0:
                self.is_trained = True
                logger.info(f"모델 불러오기 완료: {loaded_count}개 파일 불러옴")
                return True
            else:
                logger.warning("불러올 모델 파일이 없습니다.")
                return False
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"모델 불러오기 오류: {e}", exc_info=True)
            return False

