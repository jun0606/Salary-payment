#!/usr/bin/env python3
"""
주휴수당 수정 테스트 스크립트
- _prepare_payslip_data 함수의 주휴수당 계산 로직 테스트
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logic import _prepare_payslip_data

def test_holiday_allowance_calculation():
    """주휴수당 계산 테스트"""
    
    print("=" * 60)
    print("주휴수당 계산 로직 테스트")
    print("=" * 60)
    
    # 테스트 케이스 1: 주휴수당이 있는 경우
    print("\n[테스트 1] 주휴수당이 있는 경우 (2025년 12월)")
    user_summary_1 = {
        'user_id': 'EMP001',
        'name': '홍길동',
        'department': '개발팀',
        'position': '대리',
        'hire_date': '2024-01-15',
        'payment_date': '2025-12-25',
        'base_pay': 2500000,
        'weekly_holiday_allowance': 150000,  # 주휴수당 있음
        '주휴시간(분단위)': 480,  # 8시간
        '연장수당': 100000,
        'night_pay': 50000,
        'national_pension': 112500,
        'health_insurance': 87500,
        'employment_insurance': 22500,
        'long_term_care_insurance': 11200,
        'income_tax': 50000,
        'local_income_tax': 5000,
        'hourly_rate': 15000,
        '근무시간_분': 9600,  # 160시간
        '연장시간_분': 600,   # 10시간
        '심야시간_분': 300,   # 5시간
    }
    
    employee_data_1 = {
        'EMP001': {
            'name': '홍길동',
            'department': '개발팀',
            'position': '대리',
            'allowances': {
                'recurring': [],
                'one_time': []
            }
        }
    }
    
    result_1 = _prepare_payslip_data(
        user_summary_1, 
        '2025년 12월', 
        '테스트회사',
        explanation_options={
            'base_pay_explanation': True,
            'holiday_explanation': True,
            'night_explanation': True,
            'overtime_explanation': True
        },
        employee_data=employee_data_1
    )
    
    print(f"  - 주휴수당: {result_1['weekly_holiday_allowance']:,}원")
    print(f"  - 주휴수당 설명: {result_1['calculation_note_2']}")
    
    # 검증: 주휴수당 설명에 현재 월(12월)이 포함되어야 함
    assert '12월' in result_1['calculation_note_2'] or '2025년' in result_1['calculation_note_2'], \
        "❌ 주휴수당 설명에 현재 월이 없습니다!"
    
    # 검증: 9월, 10월 같은 과거 월이 포함되면 안 됨
    assert '9월' not in result_1['calculation_note_2'], \
        "❌ 주휴수당 설명에 9월이 잘못 포함되었습니다!"
    assert '10월' not in result_1['calculation_note_2'], \
        "❌ 주휴수당 설명에 10월이 잘못 포함되었습니다!"
    
    print("  ✅ 테스트 1 통과")
    
    # 테스트 케이스 2: 주휴수당이 0원인 경우
    print("\n[테스트 2] 주휴수당이 0원인 경우")
    user_summary_2 = {
        'user_id': 'EMP002',
        'name': '김철수',
        'department': '영업팀',
        'position': '사원',
        'hire_date': '2024-03-01',
        'payment_date': '2025-12-25',
        'base_pay': 2000000,
        'weekly_holiday_allowance': 0,  # 주휴수당 없음
        '주휴시간(분단위)': 0,
        '연장수당': 0,
        'night_pay': 0,
        'national_pension': 90000,
        'health_insurance': 70000,
        'employment_insurance': 18000,
        'long_term_care_insurance': 9000,
        'income_tax': 40000,
        'local_income_tax': 4000,
        'hourly_rate': 12000,
        '근무시간_분': 9600,
        '연장시간_분': 0,
        '심야시간_분': 0,
    }
    
    employee_data_2 = {
        'EMP002': {
            'name': '김철수',
            'department': '영업팀',
            'position': '사원',
            'allowances': {
                'recurring': [],
                'one_time': []
            }
        }
    }
    
    result_2 = _prepare_payslip_data(
        user_summary_2, 
        '2025년 12월', 
        '테스트회사',
        explanation_options={
            'base_pay_explanation': True,
            'holiday_explanation': True,
            'night_explanation': True,
            'overtime_explanation': True
        },
        employee_data=employee_data_2
    )
    
    print(f"  - 주휴수당: {result_2['weekly_holiday_allowance']:,}원")
    print(f"  - 주휴수당 설명: {result_2['calculation_note_2']}")
    
    # 검증: "해당없음" 메시지가 있어야 함
    assert '해당없음' in result_2['calculation_note_2'], \
        "❌ 주휴수당이 0일 때 '해당없음' 메시지가 없습니다!"
    
    print("  ✅ 테스트 2 통과")
    
    # 테스트 케이스 3: 월경계 주 테스트 (1월)
    print("\n[테스트 3] 월경계 주 테스트 (2026년 1월)")
    user_summary_3 = {
        'user_id': 'EMP003',
        'name': '이영희',
        'department': '인사팀',
        'position': '과장',
        'hire_date': '2023-06-01',
        'payment_date': '2026-01-25',
        'base_pay': 3000000,
        'weekly_holiday_allowance': 180000,  # 1월 귀속 주휴수당
        '주휴시간(분단위)': 480,
        '연장수당': 150000,
        'night_pay': 80000,
        'national_pension': 135000,
        'health_insurance': 105000,
        'employment_insurance': 27000,
        'long_term_care_insurance': 13500,
        'income_tax': 60000,
        'local_income_tax': 6000,
        'hourly_rate': 18000,
        '근무시간_분': 9600,
        '연장시간_분': 900,
        '심야시간_분': 480,
    }
    
    employee_data_3 = {
        'EMP003': {
            'name': '이영희',
            'department': '인사팀',
            'position': '과장',
            'allowances': {
                'recurring': [],
                'one_time': []
            }
        }
    }
    
    result_3 = _prepare_payslip_data(
        user_summary_3, 
        '2026년 1월', 
        '테스트회사',
        explanation_options={
            'base_pay_explanation': True,
            'holiday_explanation': True,
            'night_explanation': True,
            'overtime_explanation': True
        },
        employee_data=employee_data_3
    )
    
    print(f"  - 주휴수당: {result_3['weekly_holiday_allowance']:,}원")
    print(f"  - 주휴수당 설명: {result_3['calculation_note_2']}")
    
    # 검증: 주휴수당 설명에 1월이 포함되어야 함
    assert '1월' in result_3['calculation_note_2'] or '2026년' in result_3['calculation_note_2'], \
        "❌ 주휴수당 설명에 현재 월(1월)이 없습니다!"
    
    print("  ✅ 테스트 3 통과")
    
    print("\n" + "=" * 60)
    print("모든 테스트 통과! ✅")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_holiday_allowance_calculation()
        print("\n🎉 테스트 성공! 수정이 정상적으로 작동합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
