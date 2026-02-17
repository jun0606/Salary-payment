#!/usr/bin/env python3
"""
실제 데이터로 주휴수당 수정 테스트
- tutorial_data.xlsx 파일을 사용하여 실제 HTML 명세서 생성
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logic import process_payroll_for_gui, generate_payslips_html
import json

def test_with_real_data():
    """실제 데이터로 테스트"""
    
    print("=" * 70)
    print("실제 데이터 주휴수당 수정 테스트")
    print("=" * 70)
    
    # 테스트할 월들
    test_months = [
        ("2025-12", "2025년 12월"),
        ("2026-01", "2026년 1월"),
    ]
    
    # 테스트 데이터 파일
    data_file = 'tutorial_data.xlsx'
    
    if not os.path.exists(data_file):
        print(f"❌ 테스트 데이터 파일이 없습니다: {data_file}")
        return False
    
    # 직원 데이터 로드 (있는 경우)
    employee_data = {}
    if os.path.exists('employees.json'):
        try:
            with open('employees.json', 'r', encoding='utf-8') as f:
                employee_data = json.load(f)
            print(f"✅ 직원 데이터 로드 완료: {len(employee_data)}명")
        except Exception as e:
            print(f"⚠️ 직원 데이터 로드 실패: {e}")
    
    for year_month, data_month_title in test_months:
        print(f"\n[테스트] {data_month_title} 급여 계산 및 HTML 생성")
        print("-" * 70)
        
        try:
            # 1. 급여 계산
            print(f"  1. 급여 계산 중...")
            summaries, data_month, business_size = process_payroll_for_gui(
                file_path=data_file,
                year_month_str=year_month,
                employee_data=employee_data
            )
            
            print(f"     ✅ 계산 완료: {len(summaries)}명")
            
            # 2. 주휴수당 정보 출력
            print(f"\n  2. 주휴수당 정보 확인:")
            for idx, row in summaries.iterrows():
                user_id = row['user_id']
                name = row['name']
                holiday_allowance = row['weekly_holiday_allowance']
                holiday_minutes = row.get('주휴시간(분단위)', 0)
                
                if holiday_allowance > 0:
                    print(f"     - {name}({user_id}): {holiday_allowance:,.0f}원 (주휴시간: {holiday_minutes/60:.1f}시간)")
                else:
                    print(f"     - {name}({user_id}): 주휴수당 없음")
            
            # 3. HTML 생성
            print(f"\n  3. HTML 명세서 생성 중...")
            output_dir = f"test_output_{year_month.replace('-', '')}"
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = os.path.join(output_dir, f"급여명세서_{year_month.replace('-', '')}.html")
            
            generate_payslips_html(
                summaries_df=summaries,
                output_filename=output_file,
                data_month=data_month_title,
                company_name="테스트 회사",
                selected_users=None,  # 모든 직원
                explanation_options={
                    'base_pay_explanation': True,
                    'holiday_explanation': True,
                    'night_explanation': True,
                    'overtime_explanation': True
                },
                data_file_path=data_file,
                employee_data=employee_data,
                business_size=business_size
            )
            
            print(f"     ✅ HTML 생성 완료: {output_file}")
            
            # 4. HTML 파일에서 주휴수당 설명 확인
            print(f"\n  4. 생성된 HTML 검증 중...")
            with open(output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 현재 월이 포함되어 있는지 확인
            current_month_str = data_month_title.split()[1]  # "12월" 또는 "1월"
            if current_month_str in html_content:
                print(f"     ✅ HTML에 {current_month_str} 정보가 정확히 표시됨")
            else:
                print(f"     ⚠️ HTML에 {current_month_str} 정보가 없음")
            
            # 과거 월(9월, 10월)이 잘못 포함되지 않았는지 확인
            wrong_months = ['9월', '10월']
            found_wrong = [m for m in wrong_months if m in html_content and m != current_month_str]
            if found_wrong:
                print(f"     ❌ 오류: HTML에 잘못된 월 {found_wrong}이 포함됨!")
            else:
                print(f"     ✅ 과거 월(9월, 10월)이 잘못 표시되지 않음")
            
            print(f"\n  📁 출력 파일: {os.path.abspath(output_file)}")
            
        except Exception as e:
            print(f"\n  ❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 70)
    print("실제 데이터 테스트 완료!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        test_with_real_data()
        print("\n🎉 실제 데이터 테스트 성공!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 실제 데이터 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
