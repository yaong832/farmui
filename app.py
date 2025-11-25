from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import sqlite3
import logging
from datetime import datetime
from data_manager import DataManager
from ai_analysis import AIAnalysis
from ml_trainer import MLTrainer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flask_server.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)  # CORS 활성화

# 데이터 관리자 및 AI 분석 인스턴스
# DB 사용 안 함 (메모리 모드)
use_database = False
data_manager = DataManager(use_db=use_database)
ai_analysis = AIAnalysis(data_manager)

# MLTrainer 인스턴스 생성
ml_trainer = MLTrainer(model_dir="models")
# 저장된 모델이 있으면 불러오기
ml_trainer.load_models()

@app.route('/')
@app.route('/index.html')
def index():
    """메인 웹 페이지"""
    return send_from_directory('templates', 'index.html')

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """로그 데이터 API (GET 요청)"""
    try:
        logs = data_manager.get_logs(limit=500)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensors', methods=['GET'])
def get_sensors():
    """센서 데이터 API (현재 농장의 최신 데이터만 반환)"""
    try:
        # 현재 농장 정보 가져오기
        farm_data = data_manager.get_farm_data()
        current_farm_id = farm_data.get('currentFarm', 1)
        
        # 현재 농장의 최신 센서 데이터만 가져오기 (농장별 데이터 구분)
        sensor_data = data_manager.get_latest_sensor_data(farm_id=current_farm_id)
        
        # 현재 농장 정보를 센서 데이터에 포함
        sensor_data['currentFarm'] = current_farm_id
        sensor_data['farms'] = farm_data.get('farms', [])
        
        # 디버깅: 데이터 상태 로그 (주기적으로만)
        if not sensor_data.get('sensors') or len(sensor_data.get('sensors', [])) == 0:
            app.logger.debug(f"센서 데이터 요청 (농장 {current_farm_id}): 데이터가 없습니다. C# UI가 실행 중인지 확인하세요.")
        
        return jsonify(sensor_data)
    except Exception as e:
        app.logger.error(f"센서 데이터 조회 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/farm', methods=['GET'])
def get_farm():
    """팜 데이터 API"""
    try:
        farm_data = data_manager.get_farm_data()
        return jsonify(farm_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save-logs', methods=['POST'])
def save_logs():
    """로그 파일 저장 API"""
    try:
        data = request.get_json()
        file_path = data.get('filePath', '') if isinstance(data, dict) else ''
        
        if not file_path:
            # 파일 경로가 없으면 기본 경로 사용
            file_path = os.path.join('logs', f'SmartFarm_Logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        
        logs = data.get('logs', []) if isinstance(data, dict) else []
        
        success = data_manager.save_logs_to_file(file_path, logs)
        
        if success:
            return jsonify({"success": True, "message": "로그 저장 완료"})
        else:
            return jsonify({"success": False, "message": "로그 저장 실패"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load-logs-file', methods=['POST'])
def load_logs_file():
    """로그 파일 불러오기 API"""
    try:
        content = request.get_data(as_text=True)
        
        # 파일 내용인지 파일 경로인지 확인
        if '\n' in content or len(content) > 260:
            # 파일 내용으로 처리
            logs = data_manager.parse_logs_from_content(content)
        else:
            # 파일 경로로 처리
            file_path = content.strip().strip('"\'')
            logs = data_manager.load_logs_from_file(file_path)
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/add-logs', methods=['POST'])
def add_logs():
    """로그 추가 API"""
    try:
        logs_json = request.get_data(as_text=True)
        success = data_manager.add_logs_from_json(logs_json)
        
        if success:
            return jsonify({"success": True, "message": "로그 추가 완료"})
        else:
            return jsonify({"success": False, "message": "로그 추가 실패"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/load-logs', methods=['GET'])
def load_logs():
    """로그 데이터만 반환"""
    try:
        logs = data_manager.get_logs(limit=500)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """C# 애플리케이션에서 센서 데이터를 받는 엔드포인트"""
    try:
        data = request.get_json()
        
        if not data:
            app.logger.warning("센서 데이터 수신: 데이터가 없습니다")
            return jsonify({"error": "데이터가 없습니다"}), 400
        
        # 센서 데이터를 DB에 저장
        sensor_data = {
            'currentFarm': data.get('currentFarm', 1),
            'powerOn': data.get('powerOn', False),
            'connected': data.get('connected', False),
            'lastUpdate': data.get('lastUpdate', datetime.now().isoformat()),
            'sensors': data.get('sensors', [])
        }
        
        # farms 정보도 포함 (작물 정보 동기화용)
        if 'farms' in data:
            sensor_data['farms'] = data.get('farms', [])
        
        data_manager.save_sensor_data(sensor_data)
        
        # 디버깅: 첫 번째 센서 데이터만 로그 기록
        sensors = data.get('sensors', [])
        if sensors:
            first_sensor = sensors[0]
            app.logger.debug(f"센서 데이터 수신: 농장 {sensor_data['currentFarm']}, 센서 {len(sensors)}개")
        
        return jsonify({"success": True, "message": "센서 데이터 수신 완료"})
    except Exception as e:
        app.logger.error(f"센서 데이터 수신 오류: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze():
    """AI 분석 API - 평균 데이터 분석, 이상징후 감지, 생산량 예측"""
    try:
        data = request.get_json()
        
        # 분석할 기간 설정 (기본값: 최근 7일)
        days = data.get('days', 7) if isinstance(data, dict) else 7
        
        # 평균 데이터 분석
        avg_analysis = ai_analysis.analyze_average_data(days=days)
        
        # 이상징후 감지
        anomaly_detection = ai_analysis.detect_anomalies(days=days)
        
        # 생산량 예측
        production_prediction = ai_analysis.predict_production(days=days)
        
        result = {
            "success": True,
            "analysis_date": datetime.now().isoformat(),
            "period_days": days,
            "average_analysis": avg_analysis,
            "anomaly_detection": anomaly_detection,
            "production_prediction": production_prediction
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500

@app.route('/api/ai/average', methods=['GET', 'POST'])
def ai_average():
    """평균 데이터 분석 API"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            days = data.get('days', 7)
            use_logs = data.get('use_logs', False)
            log_data = data.get('log_data', None)
            farm_id = data.get('farm_id', None)
        else:
            days = int(request.args.get('days', 7))
            use_logs = False
            log_data = None
            farm_id = None
        
        # 로그 기반 분석인 경우 (농장별 필터링)
        sensor_data_list = None
        if use_logs and log_data:
            logs = data_manager.parse_logs_from_content(log_data)
            sensor_data_list = data_manager.extract_sensor_data_from_logs(logs, farm_id=farm_id)
        
        result = ai_analysis.analyze_average_data(days=days, farm_id=farm_id, sensor_data_list=sensor_data_list)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/anomaly', methods=['GET', 'POST'])
def ai_anomaly():
    """이상징후 감지 API"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            days = data.get('days', 7)
            use_logs = data.get('use_logs', False)
            log_data = data.get('log_data', None)
            farm_id = data.get('farm_id', None)
        else:
            days = int(request.args.get('days', 7))
            use_logs = False
            log_data = None
            farm_id = None
        
        # 로그 기반 분석인 경우 (농장별 필터링)
        sensor_data_list = None
        if use_logs and log_data:
            logs = data_manager.parse_logs_from_content(log_data)
            sensor_data_list = data_manager.extract_sensor_data_from_logs(logs, farm_id=farm_id)
        
        result = ai_analysis.detect_anomalies(days=days, farm_id=farm_id, sensor_data_list=sensor_data_list)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/prediction', methods=['GET', 'POST'])
def ai_prediction():
    """생산량 예측 API"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            days = data.get('days', 7)
            use_logs = data.get('use_logs', False)
            log_data = data.get('log_data', None)
            farm_id = data.get('farm_id', None)
        else:
            days = int(request.args.get('days', 7))
            use_logs = False
            log_data = None
            farm_id = None
        
        # 로그 기반 분석인 경우 (농장별 필터링)
        sensor_data_list = None
        if use_logs and log_data:
            logs = data_manager.parse_logs_from_content(log_data)
            sensor_data_list = data_manager.extract_sensor_data_from_logs(logs, farm_id=farm_id)
        
        result = ai_analysis.predict_production(days=days, farm_id=farm_id, sensor_data_list=sensor_data_list)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crops', methods=['GET'])
def get_available_crops():
    """사용 가능한 작물 목록 API"""
    try:
        from crop_config import list_available_crops, CROP_OPTIMAL_CONDITIONS
        
        crops = list_available_crops()
        crop_list = []
        
        for crop_name in crops:
            crop_info = CROP_OPTIMAL_CONDITIONS.get(crop_name, {})
            crop_list.append({
                "name": crop_name,
                "description": crop_info.get('description', ''),
                "conditions": {
                    "humidity": f"{crop_info.get('humidity', {}).get('optimal_min', 0)}-{crop_info.get('humidity', {}).get('optimal_max', 0)}{crop_info.get('humidity', {}).get('unit', '')}",
                    "temperature": f"{crop_info.get('temperature', {}).get('optimal_min', 0)}-{crop_info.get('temperature', {}).get('optimal_max', 0)}{crop_info.get('temperature', {}).get('unit', '')}",
                    "light": f"{crop_info.get('light', {}).get('optimal_min', 0)}-{crop_info.get('light', {}).get('optimal_max', 0)}{crop_info.get('light', {}).get('unit', '')}",
                    "soil_moisture": f"{crop_info.get('soil_moisture', {}).get('optimal_min', 0)}-{crop_info.get('soil_moisture', {}).get('optimal_max', 0)}{crop_info.get('soil_moisture', {}).get('unit', '')}"
                }
            })
        
        return jsonify({
            "success": True,
            "crops": crop_list,
            "total": len(crop_list)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crops/<crop_name>', methods=['GET'])
def get_crop_info(crop_name):
    """특정 작물의 상세 정보 API (C# UI에서 작물 자동 설정용)"""
    try:
        from crop_config import get_crop_conditions, CROP_OPTIMAL_CONDITIONS
        
        conditions, found_crop_name, found = get_crop_conditions(crop_name)
        crop_info = CROP_OPTIMAL_CONDITIONS.get(found_crop_name, {})
        
        if not found:
            return jsonify({
                "success": False,
                "error": f"작물 '{crop_name}'를 찾을 수 없습니다.",
                "crop_name": found_crop_name  # 기본 작물로 대체됨
            }), 404
        
        return jsonify({
            "success": True,
            "crop_name": found_crop_name,
            "description": crop_info.get('description', ''),
            "base_production": crop_info.get('base_production_per_tree', 0),
            "conditions": {
                "humidity": {
                    "optimal_min": conditions.get('humidity', {}).get('optimal_min', 0),
                    "optimal_max": conditions.get('humidity', {}).get('optimal_max', 0),
                    "acceptable_min": conditions.get('humidity', {}).get('acceptable_min', 0),
                    "acceptable_max": conditions.get('humidity', {}).get('acceptable_max', 0),
                    "unit": conditions.get('humidity', {}).get('unit', '%')
                },
                "temperature": {
                    "optimal_min": conditions.get('temperature', {}).get('optimal_min', 0),
                    "optimal_max": conditions.get('temperature', {}).get('optimal_max', 0),
                    "acceptable_min": conditions.get('temperature', {}).get('acceptable_min', 0),
                    "acceptable_max": conditions.get('temperature', {}).get('acceptable_max', 0),
                    "unit": conditions.get('temperature', {}).get('unit', '℃')
                },
                "light": {
                    "optimal_min": conditions.get('light', {}).get('optimal_min', 0),
                    "optimal_max": conditions.get('light', {}).get('optimal_max', 0),
                    "acceptable_min": conditions.get('light', {}).get('acceptable_min', 0),
                    "acceptable_max": conditions.get('light', {}).get('acceptable_max', 0),
                    "unit": conditions.get('light', {}).get('unit', '%')
                },
                "soil_moisture": {
                    "optimal_min": conditions.get('soil_moisture', {}).get('optimal_min', 0),
                    "optimal_max": conditions.get('soil_moisture', {}).get('optimal_max', 0),
                    "acceptable_min": conditions.get('soil_moisture', {}).get('acceptable_min', 0),
                    "acceptable_max": conditions.get('soil_moisture', {}).get('acceptable_max', 0),
                    "unit": conditions.get('soil_moisture', {}).get('unit', '%')
                }
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/crops', methods=['POST'])
def add_new_crop():
    """새 작물 추가 API"""
    try:
        from crop_config import add_crop, CROP_OPTIMAL_CONDITIONS
        
        data = request.get_json() or {}
        crop_name = data.get('name', '').strip()
        
        if not crop_name:
            return jsonify({
                "success": False,
                "error": "작물 이름이 제공되지 않았습니다."
            }), 400
        
        # 이미 존재하는 작물인지 확인
        if crop_name in CROP_OPTIMAL_CONDITIONS:
            return jsonify({
                "success": False,
                "error": f"작물 '{crop_name}'는 이미 존재합니다."
            }), 400
        
        # 작물 조건 추출
        conditions = {
            'humidity': {
                'optimal_min': data.get('conditions', {}).get('humidity', {}).get('optimal_min', 50),
                'optimal_max': data.get('conditions', {}).get('humidity', {}).get('optimal_max', 70),
                'acceptable_min': data.get('conditions', {}).get('humidity', {}).get('acceptable_min', 30),
                'acceptable_max': data.get('conditions', {}).get('humidity', {}).get('acceptable_max', 80),
                'critical_min': data.get('conditions', {}).get('humidity', {}).get('critical_min', 20),
                'critical_max': data.get('conditions', {}).get('humidity', {}).get('critical_max', 90),
                'unit': '%',
                'name': '습도'
            },
            'temperature': {
                'optimal_min': data.get('conditions', {}).get('temperature', {}).get('optimal_min', 20),
                'optimal_max': data.get('conditions', {}).get('temperature', {}).get('optimal_max', 25),
                'acceptable_min': data.get('conditions', {}).get('temperature', {}).get('acceptable_min', 15),
                'acceptable_max': data.get('conditions', {}).get('temperature', {}).get('acceptable_max', 30),
                'critical_min': data.get('conditions', {}).get('temperature', {}).get('critical_min', 10),
                'critical_max': data.get('conditions', {}).get('temperature', {}).get('critical_max', 35),
                'unit': '℃',
                'name': '온도'
            },
            'light': {
                'optimal_min': data.get('conditions', {}).get('light', {}).get('optimal_min', 60),
                'optimal_max': data.get('conditions', {}).get('light', {}).get('optimal_max', 80),
                'acceptable_min': data.get('conditions', {}).get('light', {}).get('acceptable_min', 50),
                'acceptable_max': data.get('conditions', {}).get('light', {}).get('acceptable_max', 80),
                'critical_min': data.get('conditions', {}).get('light', {}).get('critical_min', 30),
                'critical_max': data.get('conditions', {}).get('light', {}).get('critical_max', 100),
                'unit': '%',
                'name': '채광'
            },
            'soil_moisture': {
                'optimal_min': data.get('conditions', {}).get('soil_moisture', {}).get('optimal_min', 50),
                'optimal_max': data.get('conditions', {}).get('soil_moisture', {}).get('optimal_max', 70),
                'acceptable_min': data.get('conditions', {}).get('soil_moisture', {}).get('acceptable_min', 40),
                'acceptable_max': data.get('conditions', {}).get('soil_moisture', {}).get('acceptable_max', 80),
                'critical_min': data.get('conditions', {}).get('soil_moisture', {}).get('critical_min', 20),
                'critical_max': data.get('conditions', {}).get('soil_moisture', {}).get('critical_max', 90),
                'unit': '%',
                'name': '토양습도'
            },
            'base_production_per_tree': data.get('base_production', 50),
            'description': data.get('description', f'{crop_name} 재배 - 최적 환경 조건 설정됨')
        }
        
        # 작물 추가
        add_crop(crop_name, conditions)
        
        # 성공 응답 (추가된 작물 정보 반환)
        crop_info = CROP_OPTIMAL_CONDITIONS.get(crop_name, {})
        return jsonify({
            "success": True,
            "message": f"작물 '{crop_name}'가 성공적으로 추가되었습니다.",
            "crop": {
                "name": crop_name,
                "description": crop_info.get('description', ''),
                "base_production": crop_info.get('base_production_per_tree', 50),
                "conditions": {
                    "humidity": {
                        "optimal_min": conditions['humidity']['optimal_min'],
                        "optimal_max": conditions['humidity']['optimal_max'],
                        "acceptable_min": conditions['humidity']['acceptable_min'],
                        "acceptable_max": conditions['humidity']['acceptable_max'],
                        "unit": "%"
                    },
                    "temperature": {
                        "optimal_min": conditions['temperature']['optimal_min'],
                        "optimal_max": conditions['temperature']['optimal_max'],
                        "acceptable_min": conditions['temperature']['acceptable_min'],
                        "acceptable_max": conditions['temperature']['acceptable_max'],
                        "unit": "℃"
                    },
                    "light": {
                        "optimal_min": conditions['light']['optimal_min'],
                        "optimal_max": conditions['light']['optimal_max'],
                        "acceptable_min": conditions['light']['acceptable_min'],
                        "acceptable_max": conditions['light']['acceptable_max'],
                        "unit": "%"
                    },
                    "soil_moisture": {
                        "optimal_min": conditions['soil_moisture']['optimal_min'],
                        "optimal_max": conditions['soil_moisture']['optimal_max'],
                        "acceptable_min": conditions['soil_moisture']['acceptable_min'],
                        "acceptable_max": conditions['soil_moisture']['acceptable_max'],
                        "unit": "%"
                    }
                }
            }
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ml/train', methods=['POST'])
def ml_train():
    """머신러닝 모델 훈련 API (로그 파일 또는 실시간 데이터)"""
    try:
        data = request.get_json() or {}
        log_data = data.get('log_data', None)
        use_realtime = data.get('use_realtime', False)
        
        # 실시간 데이터 사용 (현재 농장 데이터만 사용)
        if use_realtime:
            # 현재 농장 정보 가져오기
            farm_data = data_manager.get_farm_data()
            current_farm_id = farm_data.get('currentFarm', 1)
            # 현재 농장의 실시간 센서 데이터만 가져오기 (농장별 데이터 구분)
            sensor_data = data_manager.get_sensor_data_history(days=7, farm_id=current_farm_id)  # 최근 7일 데이터
            
            if not sensor_data or len(sensor_data) < 10:
                return jsonify({
                    "success": False,
                    "error": f"농장 {current_farm_id}의 실시간 센서 데이터가 부족합니다. (필요: 최소 10개, 현재: {len(sensor_data) if sensor_data else 0}개)\n\nC# UI가 실행 중이고 데이터가 수집되고 있는지 확인하세요."
                }), 400
            
            # 실시간 센서 데이터로 모델 훈련
            result = ml_trainer.train_models(sensor_data=sensor_data)
            result["data_source"] = f"실시간 센서 데이터 (농장 {current_farm_id})"
            result["data_count"] = len(sensor_data)
            return jsonify(result)
        
        # 로그 파일 사용 (현재 농장 데이터만 사용)
        elif log_data:
            # 현재 농장 정보 가져오기
            farm_data = data_manager.get_farm_data()
            current_farm_id = farm_data.get('currentFarm', 1)
            # 로그 데이터 파싱
            logs = data_manager.parse_logs_from_content(log_data)
            
            if not logs:
                return jsonify({
                    "success": False,
                    "error": "로그 데이터를 파싱할 수 없습니다."
                }), 400
            
            # 현재 농장의 로그 데이터만 추출 (농장별 데이터 구분)
            sensor_data_from_logs = data_manager.extract_sensor_data_from_logs(logs, farm_id=current_farm_id)
            
            if not sensor_data_from_logs or len(sensor_data_from_logs) < 10:
                return jsonify({
                    "success": False,
                    "error": f"농장 {current_farm_id}의 로그 데이터가 부족합니다. (필요: 최소 10개, 현재: {len(sensor_data_from_logs) if sensor_data_from_logs else 0}개)"
                }), 400
            
            # 로그에서 추출한 센서 데이터로 모델 훈련
            result = ml_trainer.train_models(sensor_data=sensor_data_from_logs)
            result["data_source"] = f"로그 파일 (농장 {current_farm_id})"
            result["data_count"] = len(sensor_data_from_logs)
            return jsonify(result)
        
        else:
            return jsonify({
                "success": False,
                "error": "학습 데이터가 제공되지 않았습니다. 로그 데이터 또는 실시간 데이터를 선택해주세요."
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ml/predict-anomaly', methods=['POST'])
def ml_predict_anomaly():
    """이상 징후 예측 API"""
    try:
        data = request.get_json() or {}
        humidity = data.get('humidity')
        temperature = data.get('temperature')
        light = data.get('light')
        soil_moisture = data.get('soil_moisture')
        
        if any(x is None for x in [humidity, temperature, light, soil_moisture]):
            return jsonify({
                "success": False,
                "error": "모든 센서 데이터가 필요합니다."
            }), 400
        
        result = ml_trainer.predict_anomaly(
            float(humidity),
            float(temperature),
            float(light),
            float(soil_moisture)
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ml/predict-score', methods=['POST'])
def ml_predict_score():
    """상태 점수 예측 API"""
    try:
        data = request.get_json() or {}
        humidity = data.get('humidity')
        temperature = data.get('temperature')
        light = data.get('light')
        soil_moisture = data.get('soil_moisture')
        
        if any(x is None for x in [humidity, temperature, light, soil_moisture]):
            return jsonify({
                "success": False,
                "error": "모든 센서 데이터가 필요합니다."
            }), 400
        
        result = ml_trainer.predict_condition_score(
            float(humidity),
            float(temperature),
            float(light),
            float(soil_moisture)
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ml/status', methods=['GET'])
def ml_status():
    """ML 모델 상태 확인 API"""
    try:
        import os
        import json
        
        # 모델 파일 존재 여부 확인
        model_dir = ml_trainer.model_dir
        model_files = {
            "anomaly_classifier": os.path.exists(os.path.join(model_dir, "anomaly_classifier.pkl")),
            "condition_predictor": os.path.exists(os.path.join(model_dir, "condition_predictor.pkl")),
            "scaler": os.path.exists(os.path.join(model_dir, "scaler.pkl")),
            "metadata": os.path.exists(os.path.join(model_dir, "metadata.json"))
        }
        
        # 메타데이터 읽기
        metadata_info = None
        metadata_path = os.path.join(model_dir, "metadata.json")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata_info = json.load(f)
            except:
                pass
        
        return jsonify({
            "success": True,
            "is_trained": ml_trainer.is_trained,
            "has_classifier": ml_trainer.anomaly_classifier is not None,
            "has_predictor": ml_trainer.condition_predictor is not None,
            "model_files": model_files,
            "model_dir": os.path.abspath(model_dir),
            "metadata": metadata_info
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ai/control', methods=['POST'])
def ai_control():
    """AI 기반 자동 제어 명령 생성 API"""
    try:
        data = request.get_json() or {}
        sensor_data = data.get('sensor_data', {})
        farm_id = data.get('farm_id', None)
        
        if not sensor_data:
            return jsonify({
                "success": False,
                "error": "센서 데이터가 제공되지 않았습니다."
            }), 400
        
        # farm_id가 None이면 현재 농장 정보 가져오기
        if farm_id is None:
            try:
                farm_data = data_manager.get_farm_data()
                farm_id = farm_data.get('currentFarm', 1)
            except Exception as farm_ex:
                app.logger.warning(f"농장 정보 가져오기 실패: {farm_ex}, 기본값 1 사용")
                farm_id = 1
        
        # AI 분석을 통해 제어 명령 생성 (ML 모델 활용)
        try:
            commands = ai_analysis.generate_control_commands(sensor_data, farm_id, ml_trainer=ml_trainer)
        except Exception as gen_ex:
            app.logger.error(f"제어 명령 생성 오류: {gen_ex}", exc_info=True)
            return jsonify({
                "success": False,
                "error": f"제어 명령 생성 중 오류가 발생했습니다: {str(gen_ex)}"
            }), 500
        
        return jsonify({
            "success": True,
            "commands": commands,
            "command_count": len(commands),
            "ml_enabled": ml_trainer.is_trained if ml_trainer else False,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"AI 제어 API 오류: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    import webbrowser
    import threading
    import time
    
    # 필요한 디렉토리 생성
    os.makedirs('logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    print("💾 메모리 모드로 실행 중... (DB 사용 안 함)")
    
    # Flask 서버 시작 전 브라우저 열기 함수
    def open_browser():
        """서버 시작 후 브라우저 자동 열기"""
        time.sleep(1.5)  # 서버가 완전히 시작될 때까지 대기
        url = 'http://localhost:5000'
        print(f"\n🌐 브라우저를 엽니다: {url}")
        webbrowser.open(url)
    
    # 브라우저를 별도 스레드에서 열기
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Flask 서버 시작
    print("\n" + "="*50)
    print("Flask 웹 서버를 시작합니다...")
    print("서버 주소: http://localhost:5000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

