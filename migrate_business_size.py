#!/usr/bin/env python3
"""
직원 데이터에 사업장 규모 정보 일괄 적용 스크립트
config.json의 business_size 설정에 따라 모든 직원 데이터 업데이트
"""

import json
import os

def migrate_employee_business_size():
    """직원 데이터에 사업장 규모 정보 일괄 적용"""

    # config.json에서 사업장 규모 설정 읽기
    config_file = 'config.json'
    employees_file = 'employees.json'

    if not os.path.exists(config_file):
        print("config.json 파일이 존재하지 않습니다.")
        return False

    if not os.path.exists(employees_file):
        print("employees.json 파일이 존재하지 않습니다.")
        return False

    # 설정 파일 로드
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    # 사업장 규모 설정 확인 (기본값: over_5)
    business_size_value = config_data.get('business_size', 'over_5')
    print(f"설정된 사업장 규모: {business_size_value}")

    # 직원 데이터 로드
    with open(employees_file, 'r', encoding='utf-8') as f:
        employees_data = json.load(f)

    # 모든 직원에 사업장 규모 적용
    updated_count = 0
    for emp_id, emp_info in employees_data.get('employees', {}).items():
        if isinstance(emp_info, dict):
            current_size = emp_info.get('business_size', 'not_set')
            if current_size != business_size_value:
                emp_info['business_size'] = business_size_value
                updated_count += 1
                print(f"직원 {emp_id}({emp_info.get('name', 'Unknown')}): {current_size} → {business_size_value}")

    # 변경사항이 있으면 파일 저장
    if updated_count > 0:
        with open(employees_file, 'w', encoding='utf-8') as f:
            json.dump(employees_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {updated_count}명의 직원 데이터가 업데이트되었습니다.")
        print(f"모든 직원의 사업장 규모: {business_size_value}")
        return True
    else:
        print("\nℹ️ 모든 직원 데이터가 이미 최신 상태입니다.")
        return True

if __name__ == "__main__":
    print("직원 데이터 사업장 규모 마이그레이션 시작...")
    success = migrate_employee_business_size()
    if success:
        print("✅ 마이그레이션 완료")
    else:
        print("❌ 마이그레이션 실패")
