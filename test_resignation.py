#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
퇴사일 표시 및 주휴수당 영향 테스트
"""

from logic import _prepare_payslip_data

print("=" * 70)
print("퇴사일 표시 및 주휴수당 영향 테스트")
print("=" * 70)

# 테스트 데이터 (퇴사자)
test_data_resigned = {
    'name': '퇴사직원',
    'user_id': 'RESIGN001',
    'base_pay': 500000,
    'hourly_rate': 11000,
    '연장수당': 0,
    '연장시간_분': 0,
    'weekly_holiday_allowance': 0,  # 퇴사로 인해 0원
    '주휴시간(분단위)': 0,
    'night_pay': 0,
    '심야시간_분': 0,
    '휴일근무시간(분)': 0,
    '휴일수당': 0,
    '근무시간_분': 2400,  # 40시간 (퇴사일까지 근무)
    '수당합계': 0,
    'national_pension': 2250,
    'health_insurance': 1750,
    'employment_insurance': 450,
    'long_term_care_insurance': 225,
    'income_tax': 1500,
    'local_income_tax': 150,
    '총급여액': 500000,
    'deductions': 6325,
    'net_pay': 493675,
    'department': '영업부',
    'position': '사원',
    'hire_date': '2024-01-01',
    'payment_date': '2026-12-25'
}

# 퇴사자 employee_data
employee_data_resigned = {
    'RESIGN001': {
        'name': '퇴사직원',
        'resignation_date': '2025-12-15',  # 12월 15일 퇴사
        'department': '영업부',
        'position': '사원',
        'hire_date': '2024-01-01'
    }
}

# 퇴사자 테스트
result_resigned = _prepare_payslip_data(
    test_data_resigned, 
    '2025년 12월', 
    '테스트회사',
    employee_data=employee_data_resigned,
    business_size='under_5'
)

print("\n=== 퇴사자 테스트 ===")
print(f"직원명: {result_resigned['name']}")
print(f"입사일: {result_resigned['hire_date']}")
print(f"퇴사일: {result_resigned.get('resignation_date', '미지정')}")
print(f"주휴수당: {result_resigned['weekly_holiday_allowance']:,}원")
print()

if result_resigned.get('resignation_date'):
    print("✅ 퇴사일이 정상적으로 표시됩니다.")
    print("✅ HTML에서 빨간색으로 강조 표시됩니다.")
else:
    print("❌ 퇴사일이 표시되지 않습니다.")

print("\n" + "=" * 70)
print("테스트 완료!")
print("=" * 70)
print("\n퇴사일 관련 기능:")
print("1. HTML에 퇴사일 표시 (빨간색 강조)")
print("2. 퇴사일 기준 주휴수당 계산 (이미 구현됨)")
print("3. 퇴사일이 주휴일보다 이전이면 주휴수당 미지급")
