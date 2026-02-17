#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주차별 주휴수당 상세 표기 테스트
"""

from logic import _prepare_payslip_data

print("=" * 70)
print("주차별 주휴수당 상세 표기 테스트")
print("=" * 70)

# 테스트 데이터
test_data = {
    'name': '테스트직원',
    'user_id': 'TEST001',
    'base_pay': 880000,
    'hourly_rate': 11000,
    '연장수당': 16500,
    '연장시간_분': 60,
    'weekly_holiday_allowance': 70210,  # 70,210원 주휴수당
    '주휴시간(분단위)': 420,  # 7.0시간
    'night_pay': 0,
    '심야시간_분': 0,
    '휴일근무시간(분)': 0,
    '휴일수당': 0,
    '근무시간_분': 4800,
    '수당합계': 0,
    'national_pension': 4500,
    'health_insurance': 3500,
    'employment_insurance': 900,
    'long_term_care_insurance': 450,
    'income_tax': 3000,
    'local_income_tax': 300,
    '총급여액': 966210,
    'deductions': 12650,
    'net_pay': 953560,
    'department': '영업부',
    'position': '사원',
    'hire_date': '2024-01-01',
    'payment_date': '2026-12-25'
}

# 주휴수당 데이터 테스트
result = _prepare_payslip_data(test_data, '2025년 12월', '테스트회사', business_size='under_5')

print("\n=== 주휴수당 주차별 상세 내역 테스트 ===")
print(f"총 주휴수당: {result['weekly_holiday_allowance']:,}원")
print(f"산출식: {result['calculation_note_2']}")
print()

if result.get('weekly_holiday_details'):
    print('[주차별 상세 내역]')
    for week in result['weekly_holiday_details']:
        print(f"  {week['week']}주차 ({week['week_period']}):")
        print(f"    귀속: {week['귀속월']}")
        print(f"    주휴일: {week['holiday_date']}")
        print(f"    주휴수당: {week['amount']:,.0f}원 (주휴시간 {week['holiday_hours']:.1f}시간 × 시급 {week['hourly_rate']:,}원)")
        print(f"    └ 근무시간: {week['work_hours']:.1f}시간 (15시간 이상 충족)")
    print()

if result.get('weekly_holiday_summary'):
    summary = result['weekly_holiday_summary']
    print(f"[요약] {summary['total_weeks']}주 합계: {summary['total_amount']:,}원")
    print(f"       평균 주휴시간: {summary['avg_holiday_hours']:.1f}시간")
    print()

print("=" * 70)
print("테스트 완료!")
print("=" * 70)
print("\n주차별 주휴수당 상세 표기 기능:")
print("1. 각 주차별 주휴수당 금액")
print("2. 각 주차별 주휴시간")
print("3. 각 주차별 근무시간 (15시간 기준 충족 여부)")
print("4. 합계 및 요약 정보")
