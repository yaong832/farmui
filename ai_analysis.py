import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from data_manager import DataManager
from collections import defaultdict
from crop_config import get_crop_conditions, CROP_OPTIMAL_CONDITIONS
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

class AIAnalysis:
    """AI 분석 클래스 - 작물별 특화 평균 데이터 분석, 이상징후 감지, 생산량 예측, AI 기반 자동 제어"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def _get_crop_conditions(self, farm_id: Optional[int] = None) -> tuple:
        """
        농장 ID에 따라 작물 최적 조건 가져오기
        
        Args:
            farm_id: 농장 ID (None이면 현재 농장의 작물 정보 사용)
        
        Returns:
            (조건 딕셔너리, 작물 이름) 튜플
        """
        try:
            # 농장 정보 가져오기
            farm_data = self.data_manager.get_farm_data()
            
            # farm_id가 None이면 현재 농장 사용
            if farm_id is None:
                farm_id = farm_data.get('currentFarm', 1)
            
            # 해당 농장의 작물 정보 찾기
            farms = farm_data.get('farms', [])
            crop_name = None
            
            for farm in farms:
                if farm.get('id') == farm_id:
                    crop_name = farm.get('cropName', '')
                    break
            
            # 작물 이름이 없으면 기본값 (스마트팜 1은 사과)
            if not crop_name or crop_name.strip() == '':
                if farm_id == 1:
                    crop_name = '사과'  # 스마트팜 1번 기본값
                else:
                    crop_name = '기본'  # 다른 농장은 기본값
            
            # 작물 조건 가져오기 (3개 값 반환: conditions, found_crop_name, found)
            conditions, found_crop_name, crop_exists = get_crop_conditions(crop_name)
            # 찾은 작물 이름이 있으면 사용, 없으면 원래 crop_name 사용
            return conditions, found_crop_name if found_crop_name else crop_name, crop_exists
        except Exception as e:
            logger.error(f"작물 조건 가져오기 오류: {e}", exc_info=True)
            # 오류 시 기본값 반환 (작물 없음으로 표시)
            return CROP_OPTIMAL_CONDITIONS.get('기본', {}), '기본', False
    
    def analyze_average_data(self, days: int = 7, farm_id: Optional[int] = None, 
                            sensor_data_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        평균 데이터 분석 - 작물별 재배 최적 조건과 비교
        
        Args:
            days: 분석할 기간 (일)
            farm_id: 농장 ID (None이면 현재 농장)
            sensor_data_list: 직접 제공된 센서 데이터 리스트 (로그 기반 분석용)
        
        Returns:
            평균 데이터 분석 결과
        """
        try:
            # 작물 정보 가져오기
            crop_conditions, crop_name, crop_exists = self._get_crop_conditions(farm_id)
            
            # 로그 기반 분석인 경우 제공된 데이터 사용, 아니면 데이터베이스에서 가져오기
            if sensor_data_list is not None:
                sensor_data = sensor_data_list
            else:
                sensor_data = self.data_manager.get_sensor_data_history(days=days, farm_id=farm_id)
            
            if not sensor_data:
                return {
                    "success": False,
                    "message": "분석할 데이터가 없습니다",
                    "period_days": days,
                    "data_count": 0,
                    "crop_type": crop_name
                }
            
            # 센서별 데이터 수집
            humidity_values = []
            temperature_values = []
            light_values = []
            soil_moisture_values = []
            
            for data in sensor_data:
                if data.get('humidity') is not None:
                    humidity_values.append(data['humidity'])
                if data.get('temperature') is not None:
                    temperature_values.append(data['temperature'])
                if data.get('light') is not None:
                    light_values.append(data['light'])
                if data.get('soil_moisture') is not None:
                    soil_moisture_values.append(data['soil_moisture'])
            
            # 통계 계산 및 최적 조건 비교
            result = {
                "success": True,
                "period_days": days,
                "data_count": len(sensor_data),
                "analysis_date": datetime.now().isoformat(),
                "crop_type": crop_name,
                "crop_exists": crop_exists,  # 작물 정보 존재 여부
                "humidity": self._calculate_statistics_with_optimal(humidity_values, 'humidity', crop_conditions),
                "temperature": self._calculate_statistics_with_optimal(temperature_values, 'temperature', crop_conditions),
                "light": self._calculate_statistics_with_optimal(light_values, 'light', crop_conditions),
                "soil_moisture": self._calculate_statistics_with_optimal(soil_moisture_values, 'soil_moisture', crop_conditions),
                "overall_score": 0.0,
                "recommendations": []
            }
            
            # 작물 정보가 없으면 경고 메시지 추가
            if not crop_exists and crop_name and crop_name.strip() != '':
                result["warning"] = f"⚠️ '{crop_name}' 작물 정보가 없어 기본 조건을 사용합니다. 정확한 분석을 위해 작물 정보를 추가해주세요."
            
            # 전체 환경 점수 계산
            scores = []
            for sensor_type in ['humidity', 'temperature', 'light', 'soil_moisture']:
                sensor_data = result.get(sensor_type, {})
                if sensor_data.get('optimal_score') is not None:
                    scores.append(sensor_data['optimal_score'])
            
            result['overall_score'] = float(np.mean(scores)) if scores else 0.0
            
            # 작물별 특화 추천사항 생성
            recommendations = self._generate_recommendations(result, crop_conditions, crop_name)
            result["recommendations"] = recommendations
            
            return result
        except Exception as e:
            crop_conditions, crop_name, crop_exists = self._get_crop_conditions(farm_id)
            return {
                "success": False,
                "error": str(e),
                "period_days": days,
                "crop_type": crop_name,
                "crop_exists": crop_exists
            }
    
    def _calculate_statistics_with_optimal(self, values: List[float], sensor_type: str, 
                                           crop_conditions: dict) -> Dict[str, Any]:
        """통계 계산 및 최적 조건 비교"""
        conditions = crop_conditions.get(sensor_type, {})
        
        if not values:
            return {
                "name": conditions.get('name', sensor_type),
                "unit": conditions.get('unit', ''),
                "count": 0,
                "average": 0,
                "min": 0,
                "max": 0,
                "std": 0,
                "median": 0,
                "status": "데이터 없음",
                "optimal_score": 0.0,
                "optimal_range": f"{conditions.get('optimal_min', 0)}-{conditions.get('optimal_max', 0)}{conditions.get('unit', '')}"
            }
        
        values_array = np.array(values)
        avg = float(np.mean(values_array))
        min_val = float(np.min(values_array))
        max_val = float(np.max(values_array))
        std_val = float(np.std(values_array))
        median_val = float(np.median(values_array))
        
        # 최적 점수 계산 (0~1)
        optimal_score = self._calculate_optimal_score(
            avg, 
            conditions.get('optimal_min', 0),
            conditions.get('optimal_max', 100),
            conditions.get('acceptable_min', 0),
            conditions.get('acceptable_max', 100)
        )
        
        # 상태 판정
        status = self._determine_status(
            avg,
            conditions.get('optimal_min', 0),
            conditions.get('optimal_max', 100),
            conditions.get('acceptable_min', 0),
            conditions.get('acceptable_max', 100),
            conditions.get('critical_min', -10),
            conditions.get('critical_max', 110)
        )
        
        return {
            "name": conditions.get('name', sensor_type),
            "unit": conditions.get('unit', ''),
            "count": len(values),
            "average": avg,
            "min": min_val,
            "max": max_val,
            "std": std_val,
            "median": median_val,
            "status": status,
            "optimal_score": optimal_score,
            "optimal_range": f"{conditions.get('optimal_min', 0)}-{conditions.get('optimal_max', 0)}{conditions.get('unit', '')}",
            "current_avg": avg
        }
    
    def _calculate_optimal_score(self, value: float, opt_min: float, opt_max: float, 
                                 acc_min: float, acc_max: float) -> float:
        """최적 점수 계산 (0~1, 1이 최적)"""
        if opt_max <= opt_min:
            return 0.5
        
        # 최적 범위 내
        if opt_min <= value <= opt_max:
            return 1.0
        # 허용 범위 내
        elif acc_min <= value < opt_min:
            distance = opt_min - value
            range_size = opt_max - opt_min
            return max(0.6, 1.0 - (distance / range_size) * 0.4)
        elif opt_max < value <= acc_max:
            distance = value - opt_max
            range_size = opt_max - opt_min
            return max(0.6, 1.0 - (distance / range_size) * 0.4)
        else:
            # 허용 범위 밖
            if value < acc_min:
                distance = acc_min - value
            else:
                distance = value - acc_max
            range_size = opt_max - opt_min
            return max(0.2, 0.6 - (distance / range_size) * 0.4)
    
    def _determine_status(self, value: float, opt_min: float, opt_max: float,
                          acc_min: float, acc_max: float, crit_min: float, crit_max: float) -> str:
        """상태 판정"""
        if opt_min <= value <= opt_max:
            return "최적"
        elif acc_min <= value <= acc_max:
            return "양호"
        elif crit_min <= value < acc_min or acc_max < value <= crit_max:
            return "주의"
        else:
            return "위험"
    
    def _generate_recommendations(self, analysis_result: Dict[str, Any], 
                                  crop_conditions: dict, crop_name: str) -> List[str]:
        """작물별 특화 추천사항 생성"""
        recommendations = []
        
        # 센서별 추천
        for sensor_key, sensor_data_key in [('humidity', 'humidity'), ('temperature', 'temperature'), 
                                             ('light', 'light'), ('soil_moisture', 'soil_moisture')]:
            sensor_data = analysis_result.get(sensor_data_key, {})
            if sensor_data.get('average', 0) > 0:
                conditions = crop_conditions.get(sensor_key, {})
                avg_value = sensor_data['average']
                opt_min = conditions.get('optimal_min', 0)
                opt_max = conditions.get('optimal_max', 100)
                unit = conditions.get('unit', '')
                sensor_name = conditions.get('name', sensor_key)
                
                if avg_value < opt_min:
                    recommendations.append(f"{sensor_name}가 평균 {avg_value:.1f}{unit}로 낮습니다. {crop_name} 재배 최적 {sensor_name}({opt_min}-{opt_max}{unit})를 위해 조절을 권장합니다.")
                elif avg_value > opt_max:
                    recommendations.append(f"{sensor_name}가 평균 {avg_value:.1f}{unit}로 높습니다. {crop_name} 재배 최적 범위를 위해 조절을 권장합니다.")
        
        # 전체 환경 점수 기반 추천
        overall_score = analysis_result.get('overall_score', 0.5)
        if overall_score >= 0.9:
            recommendations.insert(0, f"✅ 현재 환경 조건이 {crop_name} 재배에 매우 우수합니다. 현재 상태를 유지하세요.")
        elif overall_score >= 0.7:
            recommendations.insert(0, f"✅ 현재 환경 조건이 {crop_name} 재배에 양호합니다.")
        elif overall_score < 0.5:
            recommendations.insert(0, f"⚠️ 현재 환경 조건이 {crop_name} 재배에 부적합합니다. 위 항목을 개선해주세요.")
        
        if not recommendations:
            recommendations.append("데이터 분석 중입니다...")
        
        return recommendations
    
    def detect_anomalies(self, days: int = 7, farm_id: Optional[int] = None, 
                        threshold_std: float = 2.0, 
                        sensor_data_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        이상징후 감지 - 작물별 재배에 부적합한 조건 감지
        
        Args:
            days: 분석할 기간 (일)
            farm_id: 농장 ID
            threshold_std: 이상치 감지 기준 (표준편차 배수)
            sensor_data_list: 직접 제공된 센서 데이터 리스트 (로그 기반 분석용)
        
        Returns:
            이상징후 감지 결과
        """
        try:
            # 작물 정보 가져오기
            crop_conditions, crop_name, crop_exists = self._get_crop_conditions(farm_id)
            
            # 로그 기반 분석인 경우 제공된 데이터 사용, 아니면 데이터베이스에서 가져오기
            if sensor_data_list is not None:
                sensor_data = sensor_data_list
            else:
                sensor_data = self.data_manager.get_sensor_data_history(days=days, farm_id=farm_id)
            
            if not sensor_data:
                return {
                    "success": False,
                    "message": "분석할 데이터가 없습니다",
                    "period_days": days,
                    "anomalies": [],
                    "crop_type": crop_name,
                    "crop_exists": crop_exists
                }
            
            # 센서별 데이터 수집
            humidity_values = []
            temperature_values = []
            light_values = []
            soil_moisture_values = []
            timestamps = []
            
            for data in sensor_data:
                timestamps.append(data['timestamp'])
                humidity_values.append(data.get('humidity'))
                temperature_values.append(data.get('temperature'))
                light_values.append(data.get('light'))
                soil_moisture_values.append(data.get('soil_moisture'))
            
            anomalies = []
            
            # 각 센서별 이상치 감지 및 작물 재배 최적 조건과 비교
            anomalies.extend(self._detect_sensor_anomalies_with_optimal(
                "습도", humidity_values, timestamps, 'humidity', threshold_std, crop_conditions, crop_name
            ))
            anomalies.extend(self._detect_sensor_anomalies_with_optimal(
                "온도", temperature_values, timestamps, 'temperature', threshold_std, crop_conditions, crop_name
            ))
            anomalies.extend(self._detect_sensor_anomalies_with_optimal(
                "채광", light_values, timestamps, 'light', threshold_std, crop_conditions, crop_name
            ))
            anomalies.extend(self._detect_sensor_anomalies_with_optimal(
                "토양습도", soil_moisture_values, timestamps, 'soil_moisture', threshold_std, crop_conditions, crop_name
            ))
            
            # 이상치를 시간순으로 정렬
            anomalies.sort(key=lambda x: x.get('timestamp', ''))
            
            # 심각도별 분류
            critical_anomalies = [a for a in anomalies if a.get('severity') == '높음']
            warning_anomalies = [a for a in anomalies if a.get('severity') == '중간']
            
            result = {
                "success": True,
                "period_days": days,
                "analysis_date": datetime.now().isoformat(),
                "threshold_std": threshold_std,
                "total_anomalies": len(anomalies),
                "critical_count": len(critical_anomalies),
                "warning_count": len(warning_anomalies),
                "anomalies": anomalies[:100],
                "crop_type": crop_name,
                "crop_exists": crop_exists,
                "summary": {
                    "humidity_anomalies": len([a for a in anomalies if a['sensor'] == '습도']),
                    "temperature_anomalies": len([a for a in anomalies if a['sensor'] == '온도']),
                    "light_anomalies": len([a for a in anomalies if a['sensor'] == '채광']),
                    "soil_moisture_anomalies": len([a for a in anomalies if a['sensor'] == '토양습도'])
                }
            }
            
            # 작물 정보가 없으면 경고 메시지 추가
            if not crop_exists and crop_name and crop_name.strip() != '':
                result["warning"] = f"⚠️ '{crop_name}' 작물 정보가 없어 기본 조건을 사용합니다. 정확한 이상 감지를 위해 작물 정보를 추가해주세요."
            
            return result
        except Exception as e:
            crop_conditions, crop_name, crop_exists = self._get_crop_conditions(farm_id)
            return {
                "success": False,
                "error": str(e),
                "period_days": days,
                "anomalies": [],
                "crop_type": crop_name,
                "crop_exists": crop_exists
            }
    
    def _detect_sensor_anomalies_with_optimal(self, sensor_name: str, values: List[Optional[float]], 
                                              timestamps: List[str], sensor_type: str,
                                              threshold_std: float, crop_conditions: dict,
                                              crop_name: str) -> List[Dict[str, Any]]:
        """센서별 이상치 감지 (최적 조건과 비교)"""
        anomalies = []
        conditions = crop_conditions.get(sensor_type, {})
        
        # None 값 제거하고 유효한 값만 사용
        valid_values = [v for v in values if v is not None]
        valid_indices = [i for i, v in enumerate(values) if v is not None]
        
        if len(valid_values) < 3:
            return anomalies
        
        values_array = np.array(valid_values)
        mean = np.mean(values_array)
        std = np.std(values_array)
        
        if std == 0:
            return anomalies
        
        # 최적 조건 범위
        opt_min = conditions.get('optimal_min', 0)
        opt_max = conditions.get('optimal_max', 100)
        acc_min = conditions.get('acceptable_min', 0)
        acc_max = conditions.get('acceptable_max', 100)
        crit_min = conditions.get('critical_min', -10)
        crit_max = conditions.get('critical_max', 110)
        unit = conditions.get('unit', '')
        
        # Z-score 기반 이상치 감지 및 최적 조건 위반 감지
        for idx in valid_indices:
            value = values[idx]
            if value is None:
                continue
            
            z_score = abs((value - mean) / std) if std > 0 else 0
            
            # 이상치 조건: Z-score가 높거나 최적 조건을 벗어남
            is_anomaly = False
            anomaly_reason = ""
            severity = "중간"
            
            # 위험 범위 밖
            if value < crit_min or value > crit_max:
                is_anomaly = True
                severity = "높음"
                if value < crit_min:
                    anomaly_reason = f"위험 범위 이하 ({crit_min}{unit} 미만)"
                else:
                    anomaly_reason = f"위험 범위 초과 ({crit_max}{unit} 초과)"
            # 허용 범위 밖
            elif value < acc_min or value > acc_max:
                is_anomaly = True
                severity = "높음"
                if value < acc_min:
                    anomaly_reason = f"허용 범위 이하 ({crop_name} 재배 최소값 {acc_min}{unit} 미만)"
                else:
                    anomaly_reason = f"허용 범위 초과 ({crop_name} 재배 최대값 {acc_max}{unit} 초과)"
            # 최적 범위 밖
            elif value < opt_min or value > opt_max:
                if z_score > threshold_std:
                    is_anomaly = True
                    severity = "중간"
                    if value < opt_min:
                        anomaly_reason = f"최적 범위 이하 ({crop_name} 재배 최적값 {opt_min}{unit} 미만)"
                    else:
                        anomaly_reason = f"최적 범위 초과 ({crop_name} 재배 최적값 {opt_max}{unit} 초과)"
            # 통계적 이상치
            elif z_score > threshold_std * 1.5:
                is_anomaly = True
                severity = "중간"
                anomaly_reason = f"통계적 이상치 (평균에서 {z_score:.2f} 표준편차 벗어남)"
            
            if is_anomaly:
                anomaly_type = "낮음" if value < opt_min else "높음"
                if z_score > threshold_std * 2:
                    severity = "높음"
                
                anomalies.append({
                    "sensor": sensor_name,
                    "timestamp": timestamps[idx],
                    "value": float(value),
                    "mean": float(mean),
                    "std": float(std),
                    "z_score": float(z_score),
                    "anomaly_type": anomaly_type,
                    "severity": severity,
                    "optimal_min": opt_min,
                    "optimal_max": opt_max,
                    "reason": anomaly_reason,
                    "message": f"{sensor_name} 값 {value:.1f}{unit}: {anomaly_reason}"
                })
        
        return anomalies
    
    def predict_production(self, days: int = 7, farm_id: Optional[int] = None, 
                          prediction_days: int = 7,
                          sensor_data_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        생산량 예측 - 작물별 생산량 예측
        
        Args:
            days: 분석할 기간 (일)
            farm_id: 농장 ID
            prediction_days: 예측할 기간 (일)
            sensor_data_list: 직접 제공된 센서 데이터 리스트 (로그 기반 분석용)
        
        Returns:
            생산량 예측 결과
        """
        try:
            # 작물 정보 가져오기
            crop_conditions, crop_name, crop_exists = self._get_crop_conditions(farm_id)
            
            # 로그 기반 분석인 경우 제공된 데이터 사용, 아니면 데이터베이스에서 가져오기
            if sensor_data_list is not None:
                sensor_data = sensor_data_list
            else:
                sensor_data = self.data_manager.get_sensor_data_history(days=days, farm_id=farm_id)
            
            if not sensor_data:
                return {
                    "success": False,
                    "message": "예측할 데이터가 없습니다",
                    "period_days": days,
                    "prediction_days": prediction_days,
                    "crop_type": crop_name,
                    "crop_exists": crop_exists
                }
            
            # 센서 데이터를 일별로 집계
            daily_data = self._aggregate_daily_data(sensor_data)
            
            if len(daily_data) < 2:
                return {
                    "success": False,
                    "message": "예측을 위한 충분한 데이터가 없습니다 (최소 2일 필요)",
                    "period_days": days,
                    "prediction_days": prediction_days,
                    "crop_type": crop_name
                }
            
            # 작물별 최적 범위를 기반으로 환경 점수 계산
            optimal_ranges = {
                'humidity': (
                    crop_conditions.get('humidity', {}).get('optimal_min', 50),
                    crop_conditions.get('humidity', {}).get('optimal_max', 70)
                ),
                'temperature': (
                    crop_conditions.get('temperature', {}).get('optimal_min', 18),
                    crop_conditions.get('temperature', {}).get('optimal_max', 25)
                ),
                'light': (
                    crop_conditions.get('light', {}).get('optimal_min', 60),
                    crop_conditions.get('light', {}).get('optimal_max', 80)
                ),
                'soil_moisture': (
                    crop_conditions.get('soil_moisture', {}).get('optimal_min', 40),
                    crop_conditions.get('soil_moisture', {}).get('optimal_max', 60)
                )
            }
            
            # 최근 환경 점수 계산
            recent_scores = []
            for day_data in daily_data[-min(7, len(daily_data)):]:  # 최근 7일
                score = self._calculate_environment_score(day_data, optimal_ranges)
                recent_scores.append(score)
            
            avg_score = np.mean(recent_scores) if recent_scores else 0.5
            
            # 작물별 생산량 예측 모델
            base_production_per_tree = crop_conditions.get('base_production_per_tree', 10)
            num_trees = 100  # 가정, 실제로는 농장 정보에서 가져와야 함
            base_production = base_production_per_tree * num_trees
            
            # 환경 점수 기반 생산량 조정
            production_multiplier = 0.6 + (avg_score * 0.6)  # 0.6 ~ 1.2
            predicted_production = base_production * production_multiplier
            
            # 예측 기간 조정
            daily_production = predicted_production / 365
            predicted_production_for_period = daily_production * prediction_days
            
            # 예측 상한/하한
            confidence_level = 0.7 + (avg_score * 0.2)  # 0.7 ~ 0.9
            confidence_interval = predicted_production_for_period * (1 - confidence_level)
            lower_bound = max(0, predicted_production_for_period - confidence_interval)
            upper_bound = predicted_production_for_period + confidence_interval
            
            result = {
                "success": True,
                "analysis_date": datetime.now().isoformat(),
                "period_days": days,
                "prediction_days": prediction_days,
                "crop_type": crop_name,
                "prediction": {
                    "predicted_production": float(predicted_production_for_period),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "unit": "kg",
                    "confidence": confidence_level,
                    "environment_score": float(avg_score),
                    "base_production": float(base_production),
                    "production_multiplier": float(production_multiplier)
                },
                "recommendations": self._generate_production_recommendations(
                    avg_score, daily_data[-1] if daily_data else {}, crop_conditions, crop_name
                )
            }
            
            # 작물 정보가 없으면 경고 메시지 추가
            if not crop_exists and crop_name and crop_name.strip() != '':
                result["warning"] = f"⚠️ '{crop_name}' 작물 정보가 없어 기본 조건을 사용합니다. 정확한 생산량 예측을 위해 작물 정보를 추가해주세요."
            
            return result
        except Exception as e:
            crop_conditions, crop_name, crop_exists = self._get_crop_conditions(farm_id)
            return {
                "success": False,
                "error": str(e),
                "period_days": days,
                "prediction_days": prediction_days,
                "crop_type": crop_name,
                "crop_exists": crop_exists
            }
    
    def _aggregate_daily_data(self, sensor_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """센서 데이터를 일별로 집계"""
        daily_data = defaultdict(lambda: {
            'humidity': [],
            'temperature': [],
            'light': [],
            'soil_moisture': [],
            'timestamp': None
        })
        
        for data in sensor_data:
            try:
                if isinstance(data.get('timestamp'), str):
                    date_str = data['timestamp'].split('T')[0] if 'T' in data['timestamp'] else data['timestamp'].split(' ')[0]
                else:
                    date_str = datetime.now().strftime("%Y-%m-%d")
            except:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            if data.get('humidity') is not None:
                daily_data[date_str]['humidity'].append(data['humidity'])
            if data.get('temperature') is not None:
                daily_data[date_str]['temperature'].append(data['temperature'])
            if data.get('light') is not None:
                daily_data[date_str]['light'].append(data['light'])
            if data.get('soil_moisture') is not None:
                daily_data[date_str]['soil_moisture'].append(data['soil_moisture'])
            
            daily_data[date_str]['timestamp'] = date_str
        
        # 일별 평균 계산
        result = []
        for date_str, day_data in sorted(daily_data.items()):
            result.append({
                'date': date_str,
                'humidity': np.mean(day_data['humidity']) if day_data['humidity'] else None,
                'temperature': np.mean(day_data['temperature']) if day_data['temperature'] else None,
                'light': np.mean(day_data['light']) if day_data['light'] else None,
                'soil_moisture': np.mean(day_data['soil_moisture']) if day_data['soil_moisture'] else None
            })
        
        return result
    
    def _calculate_environment_score(self, day_data: Dict[str, Any], 
                                     optimal_ranges: Dict[str, tuple]) -> float:
        """작물 재배 환경 점수 계산 (0~1, 1이 최적)"""
        scores = []
        
        for sensor, (min_val, max_val) in optimal_ranges.items():
            value = day_data.get(sensor)
            if value is None:
                continue
            
            # 최적 범위 내이면 1.0, 범위 밖이면 거리에 따라 감소
            if min_val <= value <= max_val:
                score = 1.0
            else:
                # 범위 밖일 때 거리 계산
                if value < min_val:
                    distance = min_val - value
                else:
                    distance = value - max_val
                range_size = max_val - min_val
                if range_size > 0:
                    # 거리에 따른 점수 감소 (최대 0.3까지 감소)
                    score = max(0.3, 1.0 - (distance / range_size) * 0.7)
                else:
                    score = 0.5
            scores.append(score)
        
        # 평균 점수 반환
        return np.mean(scores) if scores else 0.5
    
    def _generate_production_recommendations(self, environment_score: float, 
                                            last_day_data: Dict[str, Any],
                                            crop_conditions: dict, crop_name: str) -> List[str]:
        """생산량 예측 기반 추천사항 생성"""
        recommendations = []
        
        if environment_score < 0.6:
            recommendations.append(f"⚠️ 환경 점수가 낮습니다. 현재 환경 조건에서는 {crop_name} 생산량이 예상보다 낮을 수 있습니다.")
        elif environment_score >= 0.9:
            recommendations.append(f"✅ 환경 조건이 매우 우수합니다. 현재 상태를 유지하면 {crop_name}의 품질과 수확량이 최대화될 것입니다.")
        elif environment_score >= 0.7:
            recommendations.append(f"✅ 환경 조건이 양호합니다. 약간의 개선만으로도 생산량을 더 높일 수 있습니다.")
        else:
            recommendations.append(f"환경 조건을 개선하면 {crop_name} 생산량이 증가할 수 있습니다.")
        
        # 개별 센서 추천
        if last_day_data:
            for sensor_key, sensor_name_key in [('humidity', '습도'), ('temperature', '온도'),
                                                ('light', '채광'), ('soil_moisture', '토양습도')]:
                conditions = crop_conditions.get(sensor_key, {})
                value = last_day_data.get(sensor_key)
                opt_min = conditions.get('optimal_min', 0)
                opt_max = conditions.get('optimal_max', 100)
                unit = conditions.get('unit', '')
                
                if value and (value < opt_min or value > opt_max):
                    recommendations.append(f"{sensor_name_key}({value:.1f}{unit})를 {opt_min}-{opt_max}{unit} 범위로 조정하면 {crop_name} 생산량 향상에 도움이 됩니다.")
        
        return recommendations
    
    def generate_control_commands(self, sensor_data: Dict[str, Any], farm_id: Optional[int] = None, ml_trainer=None) -> List[Dict[str, Any]]:
        """
        현재 센서 데이터를 분석하여 AI 기반 제어 명령 생성 (ML 모델 활용)
        
        Args:
            sensor_data: 현재 센서 데이터 딕셔너리
                - sensors: 센서 데이터 리스트 [{"name": "습도", "value": 45.0}, ...]
                - 또는 humidity, temperature, light, soil_moisture 필드 직접 포함
            farm_id: 농장 ID (None이면 현재 농장)
            ml_trainer: MLTrainer 인스턴스 (ML 모델 활용 시 필요)
        
        Returns:
            제어 명령 리스트 [{"sensor_index": 1, "action": "increase", "offset": 10.0, "reason": "..."}, ...]
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 작물 최적 조건 가져오기
        try:
            conditions, crop_name, _ = self._get_crop_conditions(farm_id)
        except Exception as e:
            logger.error(f"작물 조건 가져오기 오류: {e}", exc_info=True)
            return []
        
        commands = []
        
        # 센서 데이터 추출 및 검증 (타입 안전성 강화)
        sensors_dict = {}
        
        def safe_float(value, default=0.0):
            """안전하게 float로 변환"""
            try:
                if value is None:
                    return default
                if isinstance(value, str):
                    # 문자열에서 숫자만 추출
                    cleaned = ''.join(c for c in value if c.isdigit() or c == '.' or c == '-')
                    return float(cleaned) if cleaned else default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        if 'sensors' in sensor_data:
            # C#에서 전송한 형식: {"sensors": [{"name": "습도", "value": 45.0}, ...]}
            # 센서 매핑: 습도(습도)=1, 온도(온도)=2, 채광(압력)=3, 토양습도(진동)=4
            logger.info(f"🔍 Flask 서버 센서 데이터 수신: sensors={sensor_data.get('sensors', [])}")
            for sensor in sensor_data['sensors']:
                name = sensor.get('name', '')
                original_name = name  # 원본 이름 보존
                name_lower = name.lower()
                # rawValue 우선, 없으면 value 사용
                value = sensor.get('rawValue') or sensor.get('value', 0.0)
                value = safe_float(value, 0.0)
                
                # 디버깅: 각 센서 매칭 과정 로그
                logger.debug(f"🔍 센서 매칭: 원본이름='{original_name}', 값={value}")
                
                # 토양습도를 먼저 체크 (토양습도에 "습도"가 포함되어 있으므로)
                if '토양' in name_lower or 'soil' in name_lower or '진동' in name_lower or 'vibration' in name_lower:
                    sensors_dict['soil_moisture'] = value
                    logger.debug(f"  → 토양습도로 매핑됨")
                # 채광/압력 (습도보다 먼저 체크하여 "압력"이 "습도"로 오인되지 않도록)
                elif '채광' in name_lower or 'light' in name_lower or '압력' in name_lower or 'pressure' in name_lower:
                    sensors_dict['light'] = value
                    logger.debug(f"  → 채광/압력으로 매핑됨")
                # 습도 (토양습도가 아닌 경우)
                elif '습도' in name_lower or 'humidity' in name_lower:
                    sensors_dict['humidity'] = value
                    logger.debug(f"  → 습도로 매핑됨")
                # 온도
                elif '온도' in name_lower or 'temperature' in name_lower:
                    sensors_dict['temperature'] = value
                    logger.debug(f"  → 온도로 매핑됨")
                else:
                    logger.warning(f"  ⚠️ 알 수 없는 센서 이름: '{original_name}'")
        else:
            # 직접 필드 형식
            sensors_dict = {
                'humidity': safe_float(sensor_data.get('humidity', 0.0)),
                'temperature': safe_float(sensor_data.get('temperature', 0.0)),
                'light': safe_float(sensor_data.get('light', 0.0)),
                'soil_moisture': safe_float(sensor_data.get('soil_moisture', 0.0))
            }
        
        # 센서 데이터 검증
        valid_ranges = {
            'humidity': (0, 100),
            'temperature': (-10, 50),
            'light': (0, 100),
            'soil_moisture': (0, 100)
        }
        
        for key, (min_val, max_val) in valid_ranges.items():
            value = sensors_dict.get(key)
            if value is not None:
                # 타입 확인 및 변환
                value = safe_float(value, 0.0)
                if value < min_val or value > max_val:
                    logger.warning(f"{key} 값이 범위를 벗어났습니다: {value} (범위: {min_val}-{max_val})")
                    # 범위를 벗어난 값은 클리핑
                    sensors_dict[key] = max(min_val, min(max_val, value))
                else:
                    sensors_dict[key] = value
        
        # ML 모델로 이상 징후 예측 (ML 모델이 학습되어 있고 제공된 경우)
        ml_anomaly_prediction = None
        ml_confidence = 0.5
        if ml_trainer is not None and ml_trainer.is_trained:
            try:
                ml_result = ml_trainer.predict_anomaly(
                    sensors_dict.get('humidity', 50.0),
                    sensors_dict.get('temperature', 20.0),
                    sensors_dict.get('light', 50.0),
                    sensors_dict.get('soil_moisture', 50.0)
                )
                ml_anomaly_prediction = ml_result.get('is_anomaly', False)
                ml_confidence = ml_result.get('confidence', 0.5)
                logger.info(f"ML 예측: 이상 징후={ml_anomaly_prediction}, 신뢰도={ml_confidence:.2f}")
            except Exception as e:
                logger.warning(f"ML 모델 예측 오류: {e}")
        
        # 센서별 제어 명령 생성
        # 센서 매핑: 습도(습도)=1, 온도(온도)=2, 채광(압력)=3, 토양습도(진동)=4
        sensor_configs = [
            (1, 'humidity', '습도', ['가습기', '환기']),
            (2, 'temperature', '온도', ['히터', '냉방']),
            (3, 'light', '채광', ['LED 조명', 'LED 조명 끄기']),  # 채광 = 압력 센서 (감소용: LED 조명 끄기)
            (4, 'soil_moisture', '토양습도', ['급수', '배수'])  # 토양습도 = 진동 센서
        ]
        
        for sensor_index, sensor_key, sensor_name, control_devices in sensor_configs:
            # 센서 데이터 추출 (rawValue 또는 value 사용)
            # 센서 매핑: 습도(습도)=1, 온도(온도)=2, 채광(압력)=3, 토양습도(진동)=4
            current_value = None
            matched_sensor_name = None
            if 'sensors' in sensor_data:
                for sensor in sensor_data['sensors']:
                    name = sensor.get('name', '')
                    original_name = name  # 원본 이름 보존
                    name_lower = name.lower()
                    
                    # 디버깅: 센서 매칭 과정 로그
                    logger.debug(f"🔍 제어 명령 생성 - 센서 매칭: 찾는센서키={sensor_key}, 수신센서이름='{original_name}'")
                    
                    # 토양습도를 먼저 체크 (토양습도에 "습도"가 포함되어 있으므로)
                    if ('토양' in name_lower or 'soil' in name_lower or '진동' in name_lower or 'vibration' in name_lower) and sensor_key == 'soil_moisture':
                        current_value = sensor.get('rawValue', sensor.get('value', 0.0))
                        if isinstance(current_value, str):
                            current_value = float(current_value.replace('%', '').replace('℃', ''))
                        matched_sensor_name = original_name
                        logger.debug(f"  → 토양습도 매칭 성공: 값={current_value}")
                        break
                    # 채광/압력 (습도보다 먼저 체크하여 "압력"이 "습도"로 오인되지 않도록)
                    elif ('채광' in name_lower or 'light' in name_lower or '압력' in name_lower or 'pressure' in name_lower) and sensor_key == 'light':
                        current_value = sensor.get('rawValue', sensor.get('value', 0.0))
                        if isinstance(current_value, str):
                            current_value = float(current_value.replace('%', '').replace('℃', ''))
                        matched_sensor_name = original_name
                        logger.debug(f"  → 채광/압력 매칭 성공: 값={current_value}")
                        break
                    # 습도 (토양습도가 아닌 경우, 채광/압력도 아닌 경우)
                    elif ('습도' in name_lower or 'humidity' in name_lower) and sensor_key == 'humidity' and '토양' not in name_lower and '압력' not in name_lower and 'pressure' not in name_lower:
                        current_value = sensor.get('rawValue', sensor.get('value', 0.0))
                        if isinstance(current_value, str):
                            current_value = float(current_value.replace('%', '').replace('℃', ''))
                        matched_sensor_name = original_name
                        logger.debug(f"  → 습도 매칭 성공: 값={current_value}")
                        break
                    # 온도
                    elif ('온도' in name_lower or 'temperature' in name_lower) and sensor_key == 'temperature':
                        current_value = sensor.get('rawValue', sensor.get('value', 0.0))
                        if isinstance(current_value, str):
                            current_value = float(current_value.replace('%', '').replace('℃', ''))
                        matched_sensor_name = original_name
                        logger.debug(f"  → 온도 매칭 성공: 값={current_value}")
                        break
            
            if current_value is None:
                current_value = sensors_dict.get(sensor_key, 0.0)
            
            # current_value를 float로 강제 변환 (타입 안전성)
            try:
                if isinstance(current_value, str):
                    # 문자열에서 숫자만 추출
                    current_value = float(''.join(c for c in current_value if c.isdigit() or c == '.' or c == '-'))
                else:
                    current_value = float(current_value) if current_value is not None else 0.0
            except (ValueError, TypeError):
                logger.warning(f"{sensor_name} 센서 값 변환 실패: {current_value}, 기본값 0.0 사용")
                current_value = 0.0
            
            if current_value == 0.0 and sensor_key not in sensors_dict and current_value is None:
                continue  # 센서 데이터가 없으면 스킵
            
            condition = conditions.get(sensor_key, {})
            # 최적 범위 값들을 float로 강제 변환 (타입 안전성)
            try:
                optimal_min = float(condition.get('optimal_min', 50))
                optimal_max = float(condition.get('optimal_max', 80))
                acceptable_min = float(condition.get('acceptable_min', 30))
                acceptable_max = float(condition.get('acceptable_max', 80))
            except (ValueError, TypeError) as e:
                logger.warning(f"{sensor_name} 최적 범위 값 변환 실패: {e}, 기본값 사용")
                optimal_min = 50.0
                optimal_max = 80.0
                acceptable_min = 30.0
                acceptable_max = 80.0
            
            # 허용 오차 설정 (최적 범위 경계 근처에서 오실레이션 방지)
            tolerance = (optimal_max - optimal_min) * 0.05  # 최적 범위의 5% 오차 허용
            
            # 디버깅: 채광/압력 센서의 경우 상세 로그 출력
            if sensor_key == 'light':
                logger.info(f"🔍 채광 센서 범위 체크: 현재값={current_value:.1f}, 최적범위={optimal_min:.1f}-{optimal_max:.1f}, 허용오차={tolerance:.1f}, 범위체크={(optimal_min - tolerance):.1f} <= {current_value:.1f} <= {(optimal_max + tolerance):.1f}")
            
            # 최적 범위 내에 있고 허용 오차 범위 내면 제어 불필요
            if (optimal_min - tolerance) <= current_value <= (optimal_max + tolerance):
                if sensor_key == 'light':
                    logger.info(f"✅ 채광 센서: 범위 내에 있어 제어 불필요 (현재값={current_value:.1f}, 범위={optimal_min - tolerance:.1f}-{optimal_max + tolerance:.1f})")
                continue
            
            # 최적 범위를 벗어난 경우 제어 명령 생성
            if current_value < optimal_min:
                # 값이 낮음 → 최적 범위 중간값까지 조정 (최적값에 최대한 가깝게)
                # 목표값: 최적 범위 중간값 (optimal_min과 optimal_max의 중간)
                target_value = (optimal_min + optimal_max) / 2
                
                # 최적값까지 바로 조정 (3초마다 체크하므로 빠르게 조정)
                offset_needed = target_value - current_value
                base_offset = abs(offset_needed)
                
                # 3초마다 빠르게 반응하기 위해 더 적극적으로 조정
                if ml_anomaly_prediction and ml_confidence > 0.7:
                    # ML이 확신할 때는 100% 조정
                    offset = base_offset * 1.0
                    ml_info = f" (ML 이상 징후 감지, 신뢰도: {ml_confidence:.1%})"
                elif ml_anomaly_prediction and ml_confidence > 0.5:
                    # ML이 약간 확신할 때는 95% 정도
                    offset = base_offset * 0.95
                    ml_info = f" (ML 이상 징후 가능, 신뢰도: {ml_confidence:.1%})"
                else:
                    # 규칙 기반: 90% 조정 (최적값에 가깝게)
                    offset = base_offset * 0.9
                    ml_info = " (규칙 기반 분석)" if ml_trainer is None else f" (ML 정상 예측, 신뢰도: {ml_confidence:.1%})"
                
                # 디버깅: 센서 인덱스와 이름 로그 출력 (특히 채광/압력 센서)
                logger.info(f"🔍 Flask 서버 제어 명령 생성: 센서인덱스={sensor_index}, 센서이름='{sensor_name}', 센서키={sensor_key}, 매칭된센서이름='{matched_sensor_name}', 현재값={current_value:.1f}, 목표값={target_value:.1f}")
                
                # 센서 이름이 명확하게 설정되었는지 확인
                final_sensor_name = sensor_name
                if sensor_key == 'light' and matched_sensor_name:
                    # 채광/압력 센서의 경우, 매칭된 이름이 있으면 그것을 사용
                    if '채광' in matched_sensor_name or '압력' in matched_sensor_name or 'light' in matched_sensor_name.lower() or 'pressure' in matched_sensor_name.lower():
                        final_sensor_name = '채광'
                    else:
                        final_sensor_name = '채광'  # 기본값
                        logger.warning(f"⚠️ 채광 센서 이름 불일치: 매칭된이름='{matched_sensor_name}', 기본값 '채광' 사용")
                
                commands.append({
                    "sensor_index": sensor_index,
                    "sensor_name": final_sensor_name,
                    "current_value": current_value,
                    "target_value": target_value,
                    "action": "increase",
                    "offset": round(offset, 1),
                    "device": control_devices[0],  # 첫 번째 장치 (증가용)
                    "reason": f"{final_sensor_name}가 최적 범위({optimal_min}-{optimal_max})보다 낮습니다. {control_devices[0]} 작동이 필요합니다.{ml_info}",
                    "ml_anomaly": ml_anomaly_prediction if ml_trainer is not None else None,
                    "ml_confidence": ml_confidence if ml_trainer is not None else None
                })
            elif current_value > optimal_max:
                # 값이 높음 → 감소 필요
                # 목표값: 최적 범위 중간값 (optimal_min과 optimal_max의 중간)
                target_value = (optimal_min + optimal_max) / 2
                
                # 최적값까지 바로 조정 (3초마다 체크하므로 빠르게 조정)
                offset_needed = current_value - target_value
                base_offset = abs(offset_needed)
                
                # 3초마다 빠르게 반응하기 위해 더 적극적으로 조정
                if ml_anomaly_prediction and ml_confidence > 0.7:
                    # ML이 확신할 때는 100% 조정
                    offset = base_offset * 1.0
                    ml_info = f" (ML 이상 징후 감지, 신뢰도: {ml_confidence:.1%})"
                elif ml_anomaly_prediction and ml_confidence > 0.5:
                    # ML이 약간 확신할 때는 95% 정도
                    offset = base_offset * 0.95
                    ml_info = f" (ML 이상 징후 가능, 신뢰도: {ml_confidence:.1%})"
                else:
                    # 규칙 기반: 90% 조정 (최적값에 가깝게)
                    offset = base_offset * 0.9
                    ml_info = " (규칙 기반 분석)" if ml_trainer is None else f" (ML 정상 예측, 신뢰도: {ml_confidence:.1%})"
                
                if control_devices[1]:  # 감소용 장치가 있으면
                    # 디버깅: 센서 인덱스와 이름 로그 출력 (특히 채광/압력 센서)
                    logger.info(f"🔍 Flask 서버 제어 명령 생성: 센서인덱스={sensor_index}, 센서이름='{sensor_name}', 센서키={sensor_key}, 매칭된센서이름='{matched_sensor_name}', 현재값={current_value:.1f}, 목표값={target_value:.1f}")
                    
                    # 센서 이름이 명확하게 설정되었는지 확인
                    final_sensor_name = sensor_name
                    if sensor_key == 'light' and matched_sensor_name:
                        # 채광/압력 센서의 경우, 매칭된 이름이 있으면 그것을 사용
                        if '채광' in matched_sensor_name or '압력' in matched_sensor_name or 'light' in matched_sensor_name.lower() or 'pressure' in matched_sensor_name.lower():
                            final_sensor_name = '채광'
                        else:
                            final_sensor_name = '채광'  # 기본값
                            logger.warning(f"⚠️ 채광 센서 이름 불일치: 매칭된이름='{matched_sensor_name}', 기본값 '채광' 사용")
                    
                    commands.append({
                        "sensor_index": sensor_index,
                        "sensor_name": final_sensor_name,
                        "current_value": current_value,
                        "target_value": target_value,
                        "action": "decrease",
                        "offset": round(offset, 1),
                        "device": control_devices[1],  # 두 번째 장치 (감소용)
                        "reason": f"{final_sensor_name}가 최적 범위({optimal_min}-{optimal_max})보다 높습니다. {control_devices[1]} 작동이 필요합니다.{ml_info}",
                        "ml_anomaly": ml_anomaly_prediction if ml_trainer is not None else None,
                        "ml_confidence": ml_confidence if ml_trainer is not None else None
                    })
        
        return commands
