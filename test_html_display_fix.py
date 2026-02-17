#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 표기 개선 테스트
사업장 형태와 4대보험 여부에 따른 표기 확인
"""

from logic import _prepare_payslip_data

# 테스트용 기본 데이터
base_user_summary = {
    'name': '테스트직원',
    'user_id': 'TEST001',
    'base_pay': 100000,
    'hourly_rate': 11000,
    '연장수당': 0,
    '연장시간_분': 60,  # 1시간
    'weekly_holiday_allowance': 0,
    'night_pay': 0,
    '심야시간_분': 0,
    '휴일근무시간(분)': 120,  # 2시간 휴일근무
    '휴일수당': 0,  # 5인 미만은 0
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

print("=" * 70)
print("HTML 표기 개선 테스트")
print("=" * 70)

# 테스트 1: 5인 미만 + 4대보험 적용
print("\n[테스트 1] 5인 미만 사업장 + 4대보험 적용")
print("-" * 70)
data1 = _prepare_payslip_data(
    base_user_summary.copy(),
    '2026년 12월',
    '테스트회사',
    business_size='under_5'
)
print(f"연장수당 산출식: {data1['calculation_note_3']}")
print(f"야간수당 산출식: {data1['calculation_note_night']}")
print(f"휴일수당 산출식: {data1['calculation_note_holiday_work']}")
print(f"4대보험: 국민연금 {data1['national_pension']:,}원, 건강보험 {data1['health_insurance']:,}원")
print("→ 5인 미만 안내 메시지 표시 예상 (노란색)")
print("→ 4대보험 금액 표시됨")

# 테스트 2: 5인 미만 + 4대보험 미적용
print("\n[테스트 2] 5인 미만 사업장 + 4대보험 미적용")
print("-" * 70)
user_summary_4 = base_user_summary.copy()
user_summary_4['national_pension'] = 0
user_summary_4['health_insurance'] = 0
user_summary_4['employment_insurance'] = 0
user_summary_4['long_term_care_insurance'] = 0
user_summary_4['income_tax'] = 3000  # 소득세는 적용
user_summary_4['local_income_tax'] = 300
user_summary_4['deductions'] = 3300
user_summary_4['net_pay'] = 100000 - 3300

data2 = _prepare_payslip_data(
    user_summary_4,
    '2026년 12월',
    '테스트회사',
    business_size='under_5'
)
print(f"국민연금: {data2['national_pension']:,}원")
print(f"건강보험: {data2['health_insurance']:,}원")
print(f"고용보험: {data2['employment_insurance']:,}원")
print(f"장기요양보험: {data2['long_term_care_insurance']:,}원")
print("→ 5인 미만 안내 메시지 표시 예상 (노란색)")
print("→ 4대보험 비대상자 안내 메시지 표시 예상 (파란색)")

# 테스트 3: 5인 이상 + 4대보험 적용
print("\n[테스트 3] 5인 이상 사업장 + 4대보험 적용")
print("-" * 70)
user_summary_over5 = base_user_summary.copy()
user_summary_over5['연장수당'] = 16500  # 11,000 * 1.5
user_summary_over5['night_pay'] = 16500
user_summary_over5['휴일수당'] = 33000  # 11,000 * 2 * 2시간 (8시간 초과 가정)

data3 = _prepare_payslip_data(
    user_summary_over5,
    '2026년 12월',
    '테스트회사',
    business_size='over_5'
)
print(f"연장수당 산출식: {data3['calculation_note_3']}")
print(f"야간수당 산출식: {data3['calculation_note_night']}")
print(f"휴일수당 산출식: {data3['calculation_note_holiday_work']}")
print("→ 5인 미만 안내 메시지 미표시 예상")
print("→ 4대보험 금액 표시됨")

print("\n" + "=" * 70)
print("테스트 완료!")
print("=" * 70)
print("\nHTML 템플릿에 추가된 기능:")
print("1. 휴일수당 산출식 표시 (calculation_note_holiday_work)")
print("2. 4대보험 비대상자 안내 메시지 (4대보험 모두 0원일 때 표시)")
print("3. 5인 미만 사업장 안내 문구에 '휴일' 추가")
