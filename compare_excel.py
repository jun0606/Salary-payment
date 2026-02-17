import pandas as pd
import openpyxl

def normalize_value(val):
    """값을 정규화하여 비교하기 쉽게 함"""
    if val is None or str(val).strip() == '':
        return ''
    return str(val).strip()

print('=== 원본 템플릿 vs 생성된 파일 비교 ===')

# 원본 템플릿 읽기
print('\n--- 원본 템플릿 (급여명세서.xlsx) ---')
template_data = {}
df = pd.read_excel('급여명세서.xlsx', sheet_name='명세서', header=None)
for i in range(9, 21):  # 행9부터 행20까지
    c_val = normalize_value(df.iloc[i, 2])  # C열
    d_val = normalize_value(df.iloc[i, 3])  # D열
    e_val = normalize_value(df.iloc[i, 4])  # E열
    h_val = normalize_value(df.iloc[i, 7])  # H열
    template_data[i] = {'C': c_val, 'D': d_val, 'E': e_val, 'H': h_val}
    print(f'행{i}: C="{c_val}", D="{d_val}", E="{e_val}", H="{h_val}"')

# 생성된 파일 읽기
print('\n--- 생성된 파일 (test_payslip_with_allowances.xlsx) ---')
generated_data = {}
wb = openpyxl.load_workbook('test_payslip_with_allowances.xlsx', data_only=True)
ws = wb['오수민']
for i in range(9, 21):  # 행9부터 행20까지 (템플릿과 동일 범위)
    c_val = normalize_value(ws[f'C{i}'].value)
    d_val = normalize_value(ws[f'D{i}'].value)
    e_val = normalize_value(ws[f'E{i}'].value)
    h_val = normalize_value(ws[f'H{i}'].value)
    generated_data[i] = {'C': c_val, 'D': d_val, 'E': e_val, 'H': h_val}
    print(f'행{i}: C="{c_val}", D="{d_val}", E="{e_val}", H="{h_val}"')

wb.close()

print('\n=== 상세 비교 분석 ===')
print('행 | 템플릿 → 생성본 | 상태')
print('---|------------------|------')

differences_found = False
for row in range(9, 21):
    template_row = template_data[row]
    generated_row = generated_data[row]

    row_differences = []
    for col in ['C', 'D', 'E', 'H']:
        template_val = template_row[col]
        generated_val = generated_row[col]
        if template_val != generated_val:
            row_differences.append(f'{col}:{template_val}→{generated_val}')

    if row_differences:
        differences_found = True
        status = '차이있음'
        diff_str = ', '.join(row_differences)
    else:
        status = '일치'
        diff_str = '동일'

    print(f'{row:2d} | {diff_str} | {status}')

print('\n=== 요약 ===')
if differences_found:
    print('템플릿과 생성된 파일 간 차이점이 발견되었습니다.')
    print('이는 데이터 입력 위치나 값이 템플릿 구조와 일치하지 않음을 의미합니다.')
else:
    print('템플릿과 생성된 파일이 완전히 일치합니다!')

print('\n=== 템플릿 구조 설명 ===')
print('행9: 헤더 (임금항목, 지급금액, 공제항목, 공제금액)')
print('행10: 기본급 + 국민연금')
print('행11: 연장근로수당 + 건강보험')
print('행12: 야간근로수당 + 고용보험')
print('행13: 휴일근로수당 + 장기요양보험')
print('행14: 주휴수당 + 소득세')
print('행15: 직급수당 + 지방소득세')
print('행16: 기타수당')
print('행17: 지급합계 + 공제합계')
print('행18: 실수령액')
print('행19-20: 추가 정보')
