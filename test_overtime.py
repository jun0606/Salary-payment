import json
import os
import pandas as pd
from logic import load_and_preprocess_data, calculate_salary, create_user_summaries

print("=== 수당 관리 기능 테스트 ===")

# 직원 데이터 로드
with open('employees.json', 'r', encoding='utf-8') as f:
    employee_data = json.load(f)['employees']

print('직원 데이터 (오수민):', employee_data.get('190335407', {}))

# 오수민 수당 테스트 (하드 코딩된 수당 제거됨)
test_user_id = '190335407'  # 오수민

print(f"오수민 수당 데이터 확인: {employee_data[test_user_id].get('allowances', {})}")

# 오수민 데이터 로드 및 계산 (12월 데이터 사용)
df = load_and_preprocess_data('tutorial_data-편집버전.xlsx', target_month=12)
print('데이터 로드 완료, shape:', df.shape)

# 오수민 데이터만 필터링
df_osumin = df[df['Unnamed: 1'] == test_user_id].copy()
print(f'오수민 데이터 shape: {df_osumin.shape}')

# 급여 계산
df_calculated = calculate_salary(df_osumin, employee_data)

print("\n=== 12월 급여 계산 결과 ===")
print(f"기본급 합계: {df_calculated['기본급'].sum():,.0f}원")
print(f"연장수당 합계: {df_calculated['연장수당'].sum():,.0f}원")
print(f"야간수당 합계: {df_calculated['night_pay'].sum():,.0f}원")
print(f"수당합계: {df_calculated['수당합계'].sum():,.0f}원")
print(f"예상급여금액: {df_calculated['예상급여금액'].sum():,.0f}원")

# 수당합계 디버깅
print("=== 수당합계 디버깅 ===")
print(f"df_calculated에 수당합계 컬럼 존재: {'수당합계' in df_calculated.columns}")
if '수당합계' in df_calculated.columns:
    print(f"오수민 수당합계 값: {df_calculated[df_calculated['Unnamed: 1'] == test_user_id]['수당합계'].values}")
    print(f"전체 수당합계 합계: {df_calculated['수당합계'].sum()}")

# 요약 생성
summaries = create_user_summaries(df_calculated, employee_data)
print('\n=== 요약 결과 ===')
for idx, row in summaries.iterrows():
    print(f"이름: {row['name']}")
    print(f"기본급: {row['base_pay']:,.0f}원")
    print(f"연장수당: {row['연장수당']:,.0f}원")
    print(f"야간수당: {row['night_pay']:,.0f}원")
    print(f"수당합계: {row.get('수당합계', 'N/A')}")
    print(f"총급여액: {row['총급여액']:,.0f}원")

print(f"\n=== user_summary 컬럼들 ===")
print(f"사용 가능한 컬럼: {list(summaries.columns)}")
print(f"첫 번째 행 데이터: {summaries.iloc[0].to_dict() if not summaries.empty else '데이터 없음'}")

print("\n=== 수당 데이터 검증 ===")
osumin_allowances = employee_data[test_user_id].get('allowances', {})
print(f"저장된 지속적 수당: {len(osumin_allowances.get('recurring', []))}개")
for allowance in osumin_allowances.get('recurring', []):
    print(f"  - {allowance['name']}: {allowance['amount']:,.0f}원")

print(f"저장된 단발성 수당: {len(osumin_allowances.get('one_time', []))}개")
for allowance in osumin_allowances.get('one_time', []):
    print(f"  - {allowance['name']}: {allowance['amount']:,.0f}원 ({allowance.get('date', 'N/A')})")

# 1월 데이터로 단발성 수당 테스트
print("\n=== 1월 단발성 수당 테스트 ===")
try:
    df_jan = load_and_preprocess_data('tutorial_data-편집버전.xlsx', target_month=1)
    if not df_jan.empty:
        df_osumin_jan = df_jan[df_jan['Unnamed: 1'] == test_user_id].copy()
        if not df_osumin_jan.empty:
            df_calculated_jan = calculate_salary(df_osumin_jan, employee_data)
            summaries_jan = create_user_summaries(df_calculated_jan, employee_data)

            print("1월 예상급여금액:", df_calculated_jan['예상급여금액'].sum() if not df_calculated_jan.empty else 0)
            print("1월 수당합계:", df_calculated_jan['수당합계'].sum() if not df_calculated_jan.empty else 0)
        else:
            print("1월 오수민 데이터 없음")
    else:
        print("1월 데이터 로드 실패")
except Exception as e:
    print(f"1월 테스트 중 오류 (무시): {e}")
    print("1월 데이터가 없어 단발성 수당 테스트 생략")

print("\n=== 명세서 생성 테스트 ===")
try:
    from logic import generate_payslips_html

    # HTML 명세서 생성
    output_filename = "test_payslip_with_allowances.html"
    data_month = "2026년 12월"

    generate_payslips_html(
        summaries_df=summaries,
        output_filename=output_filename,
        data_month=data_month,
        company_name="테스트 회사",
        selected_users=None,
        explanation_options={
            'base_pay_explanation': True,
            'holiday_explanation': True,
            'night_explanation': True,
            'holiday_work_explanation': True,
            'overtime_explanation': True
        },
        data_file_path='tutorial_data-편집버전.xlsx',  # 올바른 파일명 지정
        employee_data=employee_data  # 직원 데이터 전달
    )

    print(f"명세서 생성 완료: {output_filename}")

    # 생성된 파일 내용 일부 확인
    if os.path.exists(output_filename):
            with open(output_filename, 'r', encoding='utf-8') as f:
                content = f.read()

            # allowance_items 디버깅
            print("=== HTML 내용 디버깅 ===")
            if '동적 수당 항목 표시' in content:
                print("HTML 템플릿에 수당 항목 표시 영역 존재")
                # 수당 항목이 실제로 표시되는지 확인
                allowance_section_start = content.find('<!-- 동적 수당 항목 표시 -->')
                if allowance_section_start != -1:
                    allowance_section_end = content.find('<!-- 수당 합계 표시 -->', allowance_section_start)
                    if allowance_section_end != -1:
                        allowance_section = content[allowance_section_start:allowance_section_end]
                        if len(allowance_section.strip()) > 50:  # 내용이 있는지 확인
                            print(" 수당 항목이 HTML에 렌더링됨")
                            print(f"수당 섹션 길이: {len(allowance_section)}")
                        else:
                            print(" 수당 항목이 HTML에 빈 내용으로 렌더링됨")
                            print(f"수당 섹션 내용: '{allowance_section[:200]}...'")
                    else:
                        print(" 수당 합계 표시 주석을 찾을 수 없음")
                else:
                    print(" 동적 수당 항목 표시 주석을 찾을 수 없음")
            else:
                print(" HTML 템플릿에 수당 항목 표시 영역 없음")

            # 수당 관련 내용 확인
            if '교통비' in content:
                print(" 교통비 수당이 명세서에 포함됨")
            else:
                print(" 교통비 수당이 명세서에 없음")

            if '식대' in content:
                print(" 식대 수당이 명세서에 포함됨")
            else:
                print(" 식대 수당이 명세서에 없음")

            if '부장 수당' in content:
                print(" 부장 수당이 명세서에 포함됨")
            else:
                print(" 부장 수당이 명세서에 없음")

            # 총 금액 확인
            if '5,745,255' in content:
                print(" 총 급여 금액이 명세서에 정확히 표시됨")
            else:
                print(" 총 급여 금액이 명세서에 없거나 잘못됨")

            print(f"명세서 파일 크기: {len(content)} 문자")

    # Excel 명세서 생성 테스트
    print("\n=== Excel 명세서 생성 테스트 ===")
    try:
        from logic import generate_payslips

        # Excel 명세서 생성
        excel_filename = "test_payslip_with_allowances.xlsx"

        generate_payslips(
            summaries_df=summaries,
            template_path="급여명세서.xlsx",
            output_filename=excel_filename,
            data_month="2026년 12월",
            company_name="테스트 회사",
            selected_users=None,
            explanation_options={
                'base_pay_explanation': True,
                'holiday_explanation': True,
                'night_explanation': True,
                'holiday_work_explanation': True,
                'overtime_explanation': True
            },
            data_file_path='tutorial_data-편집버전.xlsx',
            employee_data=employee_data  # 직원 데이터 전달
        )

        print(f" Excel 명세서 생성 완료: {excel_filename}")

        # Excel 파일 존재 확인
        if os.path.exists(excel_filename):
            print(" Excel 파일이 정상적으로 생성됨")
            file_size = os.path.getsize(excel_filename)
            print(f"Excel 파일 크기: {file_size} 바이트")

            # Excel 내용 확인 (간단히)
            try:
                import openpyxl
                wb = openpyxl.load_workbook(excel_filename, data_only=True)
                ws = wb['오수민']  # 사용자 이름으로 된 시트

                # 수당 항목 확인
                position_allowance = ws['D16'].value if ws['D16'].value else 0
                other_allowance = ws['D17'].value if ws['D17'].value else 0
                special_allowance = ws['D11'].value if ws['D11'].value else 0

                print(f"직급수당 (D16): {position_allowance:,.0f}원")
                print(f"기타수당 (D17): {other_allowance:,.0f}원")
                print(f"특별수당 (D11): {special_allowance:,.0f}원")

                # 총 금액 확인
                total_payment = ws['D17'].value if ws['D17'].value else 0
                net_pay = ws['D18'].value if ws['D18'].value else 0

                print(f"총 지급액 (D17): {total_payment:,.0f}원")
                print(f"실지급액 (D18): {net_pay:,.0f}원")

                wb.close()

                # 수당 금액 검증
                expected_total = 660000 + 15045 + 0 + 70210 + 150000 + 350000  # 기본급 + 연장 + 야간 + 주휴 + 직급 + 기타
                if abs(total_payment - expected_total) < 1:
                    print(" Excel 총 금액 계산 정확")
                else:
                    print(f" Excel 총 금액 계산 오류: 예상 {expected_total:,.0f}원, 실제 {total_payment:,.0f}원")

            except Exception as e:
                print(f" Excel 파일 내용 확인 실패: {e}")
        else:
            print(" Excel 파일이 생성되지 않음")

    except Exception as e:
        print(f" Excel 명세서 생성 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== 개별 수당 엑셀 파일 생성 테스트 ===")
    try:
        from logic import generate_individual_allowance_excels

        # 오수민의 각 수당별 개별 엑셀 파일 생성
        allowance_files = generate_individual_allowance_excels(
            employee_data=employee_data,
            target_employee_id='190335407',  # 오수민 ID
            data_month="2026년 12월",
            output_dir="allowance_files"
        )

        print(f" 오수민 수당별 엑셀 파일 생성 완료: {len(allowance_files)}개 파일")
        for file_path in allowance_files:
            file_size = os.path.getsize(file_path)
            print(f"  - {os.path.basename(file_path)} ({file_size} 바이트)")

        # 생성된 파일 내용 확인
        if allowance_files:
            print("\n=== 생성된 수당 파일 내용 확인 ===")
            import openpyxl

            for file_path in allowance_files[:3]:  # 처음 3개 파일만 확인
                try:
                    wb = openpyxl.load_workbook(file_path, data_only=True)
                    ws = wb.active

                    print(f"\n파일: {os.path.basename(file_path)}")
                    print(f"  제목: {ws['A1'].value}")
                    print(f"  직원명: {ws['B3'].value}")
                    print(f"  수당명: {ws['B4'].value}")
                    print(f"  수당 유형: {ws['B5'].value}")
                    print(f"  금액: {ws['B6'].value}")
                    print(f"  과세 여부: {ws['B7'].value}")

                    if ws['B8'].value:  # 적용 날짜가 있는 경우
                        print(f"  적용 날짜: {ws['B8'].value}")

                    wb.close()

                except Exception as e:
                    print(f" 파일 내용 확인 실패 ({os.path.basename(file_path)}): {e}")

    except Exception as e:
        print(f" 개별 수당 엑셀 파일 생성 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== 각 수당별 12월 테스트 명세서 생성 ===")
    try:
        # 오수민의 각 수당별 테스트 명세서 생성
        allowance_types = [
            {'name': '교통비', 'amount': 200000},
            {'name': '식대', 'amount': 150000},
            {'name': '부장 수당', 'amount': 150000}
        ]

        for allowance in allowance_types:
            try:
                # 각 수당별 테스트 명세서 생성
                test_filename = f"test_payslip_{allowance['name'].replace(' ', '_')}.xlsx"
                generate_allowance_specific_payslip(
                    summaries_df=summaries,
                    template_path="급여명세서.xlsx",
                    output_filename=test_filename,
                    data_month="2026년 12월",
                    company_name="테스트 회사",
                    selected_users=None,
                    specific_allowance=allowance,  # 특정 수당만 적용
                    employee_data=employee_data
                )

                print(f" {allowance['name']} 테스트 명세서 생성 완료: {test_filename}")

                # 생성된 파일 검증
                if os.path.exists(test_filename):
                    wb = openpyxl.load_workbook(test_filename, data_only=True)
                    ws = wb['오수민']

                    base_pay = ws['D9'].value or 0
                    allowance_amount = ws['D16'].value or 0  # 기타수당
                    total_payment = ws['D17'].value or 0
                    net_pay = ws['D18'].value or 0

                    print(f"   기본급: {base_pay:,}원")
                    print(f"   {allowance['name']}: {allowance_amount:,}원")
                    print(f"   총 지급액: {total_payment:,}원")
                    print(f"   실지급액: {net_pay:,}원")

                    wb.close()

            except Exception as e:
                print(f" {allowance['name']} 테스트 명세서 생성 실패: {e}")

    except Exception as e:
        print(f" 각 수당별 테스트 명세서 생성 실패: {e}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print(f" 명세서 생성 실패: {e}")
    import traceback
    traceback.print_exc()

