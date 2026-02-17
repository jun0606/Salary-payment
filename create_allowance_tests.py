from logic import generate_allowance_specific_payslip, create_user_summaries, calculate_salary, load_and_preprocess_data
import json

# 오수민 데이터 로드 및 요약 생성
employee_data = json.load(open('employees.json', 'r', encoding='utf-8'))['employees']
df = load_and_preprocess_data('tutorial_data-편집버전.xlsx', target_month=12)
df_calculated = calculate_salary(df, employee_data)
summaries = create_user_summaries(df_calculated, employee_data)

# 각 수당별 명세서 생성
allowances = [
    {'name': '교통비', 'amount': 200000},
    {'name': '식대', 'amount': 150000},
    {'name': '부장 수당', 'amount': 150000}
]

for allowance in allowances:
    filename = f'test_payslip_{allowance["name"].replace(" ", "_")}.xlsx'
    try:
        generate_allowance_specific_payslip(
            summaries_df=summaries,
            template_path='급여명세서.xlsx',
            output_filename=filename,
            data_month='2026년 12월',
            company_name='테스트 회사',
            specific_allowance=allowance,
            employee_data=employee_data
        )
        print(f'{allowance["name"]} 명세서 생성 완료: {filename}')
    except Exception as e:
        print(f'{allowance["name"]} 명세서 생성 실패: {e}')

print('모든 수당별 명세서 생성 시도 완료')