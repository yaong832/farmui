"""
작물별 최적 환경 조건 설정 파일
새로운 작물을 추가하거나 기존 작물의 최적 조건을 수정할 수 있습니다.
"""

# 작물별 최적 환경 조건 정의
CROP_OPTIMAL_CONDITIONS = {
    '사과': {
        'humidity': {
            'optimal_min': 60,  # 생육기 최적 최소값
            'optimal_max': 80,  # 생육기 최적 최대값
            'acceptable_min': 30,  # 허용 가능 최소값
            'acceptable_max': 80,  # 허용 가능 최대값
            'critical_min': 20,  # 위험 최소값
            'critical_max': 90,  # 위험 최대값
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 15,  # 생육기 최적 최소값
            'optimal_max': 25,  # 생육기 최적 최대값
            'acceptable_min': 0,  # 허용 가능 최소값
            'acceptable_max': 35,  # 허용 가능 최대값
            'critical_min': -5,  # 위험 최소값 (동해)
            'critical_max': 40,  # 위험 최대값 (열 스트레스)
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 60,  # 최적 최소값
            'optimal_max': 80,  # 최적 최대값
            'acceptable_min': 50,  # 허용 가능 최소값
            'acceptable_max': 80,  # 허용 가능 최대값
            'critical_min': 30,  # 위험 최소값
            'critical_max': 100,  # 위험 최대값
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 40,  # 최적 최소값
            'optimal_max': 60,  # 최적 최대값
            'acceptable_min': 20,  # 허용 가능 최소값
            'acceptable_max': 60,  # 허용 가능 최대값
            'critical_min': 10,  # 위험 최소값
            'critical_max': 80,  # 위험 최대값
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 50,  # 나무당 기본 생산량 (kg)
        'description': '사과 재배 - 생육기 최적 온도 15-25℃, 습도 60-80%'
    },
    
    '토마토': {
        'humidity': {
            'optimal_min': 50,
            'optimal_max': 70,
            'acceptable_min': 40,
            'acceptable_max': 80,
            'critical_min': 30,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 20,
            'optimal_max': 25,
            'acceptable_min': 15,
            'acceptable_max': 30,
            'critical_min': 10,
            'critical_max': 35,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 70,
            'optimal_max': 90,
            'acceptable_min': 60,
            'acceptable_max': 95,
            'critical_min': 40,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 50,
            'optimal_max': 70,
            'acceptable_min': 40,
            'acceptable_max': 80,
            'critical_min': 20,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 10,  # 식물당 기본 생산량 (kg)
        'description': '토마토 재배 - 최적 온도 20-25℃, 습도 50-70%'
    },
    
    '상추': {
        'humidity': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 18,
            'optimal_max': 22,
            'acceptable_min': 10,
            'acceptable_max': 25,
            'critical_min': 5,
            'critical_max': 30,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 60,
            'optimal_max': 80,
            'acceptable_min': 50,
            'acceptable_max': 85,
            'critical_min': 30,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 50,
            'optimal_max': 70,
            'acceptable_min': 40,
            'acceptable_max': 80,
            'critical_min': 20,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 0.5,  # 식물당 기본 생산량 (kg)
        'description': '상추 재배 - 최적 온도 18-22℃, 습도 60-75%'
    },
    
    '딸기': {
        'humidity': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 18,
            'optimal_max': 22,
            'acceptable_min': 10,
            'acceptable_max': 25,
            'critical_min': 5,
            'critical_max': 30,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 65,
            'optimal_max': 85,
            'acceptable_min': 55,
            'acceptable_max': 90,
            'critical_min': 40,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 30,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 2,  # 식물당 기본 생산량 (kg)
        'description': '딸기 재배 - 최적 온도 18-22℃, 습도 60-75%, 채광 65-85%'
    },
    
    '오이': {
        'humidity': {
            'optimal_min': 70,
            'optimal_max': 85,
            'acceptable_min': 60,
            'acceptable_max': 90,
            'critical_min': 50,
            'critical_max': 95,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 22,
            'optimal_max': 28,
            'acceptable_min': 18,
            'acceptable_max': 32,
            'critical_min': 15,
            'critical_max': 35,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 70,
            'optimal_max': 90,
            'acceptable_min': 60,
            'acceptable_max': 95,
            'critical_min': 50,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 70,
            'optimal_max': 85,
            'acceptable_min': 60,
            'acceptable_max': 90,
            'critical_min': 50,
            'critical_max': 95,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 15,  # 식물당 기본 생산량 (kg)
        'description': '오이 재배 - 최적 온도 22-28℃, 습도 70-85%, 토양습도 70-85%'
    },
    
    '고추': {
        'humidity': {
            'optimal_min': 50,
            'optimal_max': 70,
            'acceptable_min': 40,
            'acceptable_max': 80,
            'critical_min': 30,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 25,
            'optimal_max': 30,
            'acceptable_min': 20,
            'acceptable_max': 32,
            'critical_min': 15,
            'critical_max': 35,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 75,
            'optimal_max': 90,
            'acceptable_min': 65,
            'acceptable_max': 95,
            'critical_min': 50,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 8,  # 식물당 기본 생산량 (kg)
        'description': '고추 재배 - 최적 온도 25-30℃, 습도 50-70%, 채광 75-90%'
    },
    
    '배추': {
        'humidity': {
            'optimal_min': 65,
            'optimal_max': 80,
            'acceptable_min': 55,
            'acceptable_max': 85,
            'critical_min': 45,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 15,
            'optimal_max': 20,
            'acceptable_min': 10,
            'acceptable_max': 25,
            'critical_min': 5,
            'critical_max': 28,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 90,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 65,
            'optimal_max': 80,
            'acceptable_min': 55,
            'acceptable_max': 85,
            'critical_min': 45,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 3,  # 식물당 기본 생산량 (kg)
        'description': '배추 재배 - 최적 온도 15-20℃, 습도 65-80%, 토양습도 65-80%'
    },
    
    '시금치': {
        'humidity': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 85,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 15,
            'optimal_max': 20,
            'acceptable_min': 10,
            'acceptable_max': 22,
            'critical_min': 5,
            'critical_max': 25,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 55,
            'optimal_max': 70,
            'acceptable_min': 45,
            'acceptable_max': 75,
            'critical_min': 35,
            'critical_max': 85,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 85,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 0.3,  # 식물당 기본 생산량 (kg)
        'description': '시금치 재배 - 최적 온도 15-20℃, 습도 60-75%, 채광 55-70%'
    },
    
    '파프리카': {
        'humidity': {
            'optimal_min': 55,
            'optimal_max': 70,
            'acceptable_min': 45,
            'acceptable_max': 75,
            'critical_min': 35,
            'critical_max': 85,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 23,
            'optimal_max': 27,
            'acceptable_min': 20,
            'acceptable_max': 30,
            'critical_min': 18,
            'critical_max': 32,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 75,
            'optimal_max': 90,
            'acceptable_min': 65,
            'acceptable_max': 95,
            'critical_min': 55,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 65,
            'optimal_max': 75,
            'acceptable_min': 55,
            'acceptable_max': 80,
            'critical_min': 45,
            'critical_max': 85,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 12,  # 식물당 기본 생산량 (kg)
        'description': '파프리카 재배 - 최적 온도 23-27℃, 습도 55-70%, 채광 75-90%'
    },
    
    '가지': {
        'humidity': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 85,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 22,
            'optimal_max': 28,
            'acceptable_min': 18,
            'acceptable_max': 30,
            'critical_min': 15,
            'critical_max': 32,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 70,
            'optimal_max': 85,
            'acceptable_min': 60,
            'acceptable_max': 90,
            'critical_min': 50,
            'critical_max': 95,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 65,
            'optimal_max': 80,
            'acceptable_min': 55,
            'acceptable_max': 85,
            'critical_min': 45,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 10,  # 식물당 기본 생산량 (kg)
        'description': '가지 재배 - 최적 온도 22-28℃, 습도 60-75%, 채광 70-85%'
    },
    
    '무': {
        'humidity': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 85,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 18,
            'optimal_max': 22,
            'acceptable_min': 12,
            'acceptable_max': 25,
            'critical_min': 8,
            'critical_max': 28,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 60,
            'optimal_max': 75,
            'acceptable_min': 50,
            'acceptable_max': 80,
            'critical_min': 40,
            'critical_max': 85,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 70,
            'optimal_max': 85,
            'acceptable_min': 60,
            'acceptable_max': 90,
            'critical_min': 50,
            'critical_max': 95,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 1.5,  # 식물당 기본 생산량 (kg)
        'description': '무 재배 - 최적 온도 18-22℃, 습도 60-75%, 토양습도 70-85%'
    },
    
    '브로콜리': {
        'humidity': {
            'optimal_min': 65,
            'optimal_max': 80,
            'acceptable_min': 55,
            'acceptable_max': 85,
            'critical_min': 45,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 16,
            'optimal_max': 20,
            'acceptable_min': 12,
            'acceptable_max': 22,
            'critical_min': 8,
            'critical_max': 25,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 65,
            'optimal_max': 80,
            'acceptable_min': 55,
            'acceptable_max': 85,
            'critical_min': 45,
            'critical_max': 90,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 65,
            'optimal_max': 80,
            'acceptable_min': 55,
            'acceptable_max': 85,
            'critical_min': 45,
            'critical_max': 90,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 1,  # 식물당 기본 생산량 (kg)
        'description': '브로콜리 재배 - 최적 온도 16-20℃, 습도 65-80%, 채광 65-80%'
    },
    
    '기본': {  # 작물 정보가 없을 때 사용할 기본값
        'humidity': {
            'optimal_min': 50,
            'optimal_max': 70,
            'acceptable_min': 30,
            'acceptable_max': 80,
            'critical_min': 20,
            'critical_max': 90,
            'unit': '%',
            'name': '습도'
        },
        'temperature': {
            'optimal_min': 18,
            'optimal_max': 25,
            'acceptable_min': 10,
            'acceptable_max': 30,
            'critical_min': 5,
            'critical_max': 35,
            'unit': '℃',
            'name': '온도'
        },
        'light': {
            'optimal_min': 60,
            'optimal_max': 80,
            'acceptable_min': 50,
            'acceptable_max': 85,
            'critical_min': 30,
            'critical_max': 100,
            'unit': '%',
            'name': '채광'
        },
        'soil_moisture': {
            'optimal_min': 40,
            'optimal_max': 60,
            'acceptable_min': 30,
            'acceptable_max': 70,
            'critical_min': 20,
            'critical_max': 80,
            'unit': '%',
            'name': '토양습도'
        },
        'base_production_per_tree': 10,
        'description': '일반 작물 재배 기준'
    }
}

def get_crop_conditions(crop_name: str) -> tuple:
    """
    작물 이름에 따라 최적 조건을 반환
    
    Args:
        crop_name: 작물 이름 (예: '사과', '토마토', '상추')
    
    Returns:
        (최적 조건 딕셔너리, 찾은 작물 이름, 작물이 존재하는지 여부) 튜플
        작물이 없으면 '기본' 조건 반환
    """
    if not crop_name or crop_name.strip() == '':
        return CROP_OPTIMAL_CONDITIONS['기본'], '기본', False
    
    crop_name_clean = crop_name.strip()
    
    # 정확히 일치하는 경우
    if crop_name_clean in CROP_OPTIMAL_CONDITIONS and crop_name_clean != '기본':
        return CROP_OPTIMAL_CONDITIONS[crop_name_clean], crop_name_clean, True
    
    # 작물 이름 매칭 (부분 일치 지원)
    for crop_key, conditions in CROP_OPTIMAL_CONDITIONS.items():
        if crop_key != '기본' and (crop_key in crop_name_clean or crop_name_clean in crop_key):
            return conditions, crop_key, True
    
    # 기본값 반환 (작물이 없음)
    return CROP_OPTIMAL_CONDITIONS['기본'], '기본', False

def add_crop(crop_name: str, conditions: dict):
    """
    새로운 작물 추가
    
    Args:
        crop_name: 작물 이름
        conditions: 최적 조건 딕셔너리
    """
    CROP_OPTIMAL_CONDITIONS[crop_name] = conditions

def list_available_crops() -> list:
    """사용 가능한 작물 목록 반환"""
    return [crop for crop in CROP_OPTIMAL_CONDITIONS.keys() if crop != '기본']

