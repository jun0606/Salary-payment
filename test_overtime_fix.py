#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연장수당 산출식 수정 테스트
5인 미만 사업장의 연장수당 산출식이 올바르게 표기되는지 확인
"""

from logic import _prepare_payslip_data

# 테스트용 데이터 생성
user_summary = {
    'name': '테스트직원',
    'user_id': 'TEST001',
    'base_pay': 100000,
    'hourly_rate': 11000,
    '연장수당': 0,  # 5인 미만은 0
    '연장시간_분': 60,  # 1시간
    'weekly_holiday_allowance': 0,
    'night_pay': 0,
    '심야시간_분': 0,
    '근무시간_분': 480,  # 8시간
    '수당합계': 0,
    'national_pension': 4500,
    'health_insurance': 3500,
    'employment_insurance': 900,
    'long_term_care_insurance': 450,
    'income_tax': 3000,
    'local_income_tax': 300,
    '총급여액': 100000,
    'deductions': 12650,
    'net_pay': 87350,
    'department': '영업부',
    'position': '사원',
    'hire_date': '2024-01-01',
    'payment_date': '2026-12-25'
}

print("=" * 60)
print("연장수당 산출식 수정 테스트")
print("=" * 60)

# 5인 미만 사업장으로 테스트
print("\n[5인 미만 사업장 테스트]")
data = _prepare_payslip_data(
    user_summary, 
    '2026년 12월', 
    '테스트회사', 
    business_size='under_5'
)

print(f"연장수당 산출식: {data['calculation_note_3']}")
print(f"연장수당 금액: {data['extra_pay']:,}원")

# 5인 이상 사업장 테스트
print("\n[5인 이상 사업장 테스트 - 비교용]")
user_summary_over5 = user_summary.copy()
user_summary_over5['연장수당'] = 16500  # 5인 이상은 1.5배 적용 (11,000 * 1.5 = 16,500)

data2 = _prepare_payslip_data(
    user_summary_over5,
    '2026년 12월', 
    '테스트회사', 
    business_size='over_5'
)

print(f"연장수당 산출식: {data2['calculation_note_3']}")
print(f"연장수당 금액: {data2['extra_pay']:,}원")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
