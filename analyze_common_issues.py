import openpyxl
import pandas as pd

def analyze_template_vs_generated():
    """템플릿과 생성된 파일들을 비교해서 공통 문제점 분석"""

    print("=== 템플릿 vs 생성된 파일 공통 문제점 분석 ===\n")

    # 템플릿 읽기
    print("1. 템플릿 구조 분석:")
    df_template = pd.read_excel('급여명세서.xlsx', sheet_name='명세서', header=None)

    template_structure = {}
    for i in range(9, 21):  # 행9부터 행20까지
        row_data = {}
        # 실제 템플릿 열: 인덱스2(C열 영역)=임금항목, 3(D)=지급금액, 4(E)=공제항목, 7(H)=공제금액
        for col_idx, col_name in [(2, 'C'), (3, 'D'), (4, 'E'), (7, 'H')]:
            value = df_template.iloc[i, col_idx]
            row_data[col_name] = str(value) if pd.notna(value) else ''
        template_structure[i] = row_data
        print(f"행{i}: {row_data}")

    print("\n2. 생성된 파일들 비교:")

    # 생성된 파일들
    generated_files = [
        'test_payslip_with_allowances.xlsx',
        'test_payslip_교통비.xlsx',
        'test_payslip_식대.xlsx',
        'test_payslip_부장_수당.xlsx'
    ]

    common_issues = {
        'structure_mismatch': [],
        'value_errors': [],
        'formatting_issues': []
    }

    for file in generated_files:
        try:
            print(f"\n--- {file} 분석 ---")
            wb = openpyxl.load_workbook(file, data_only=True)
            ws = wb['오수민']

            file_issues = []

            # 행별 비교
            for row in range(9, 21):
                template_row = template_structure[row]
                generated_row = {}

                # 생성된 파일의 열: C, D, E, H (템플릿과 동일하게)
                for col in ['C', 'D', 'E', 'H']:
                    cell_value = ws[f'{col}{row}'].value
                    generated_row[col] = str(cell_value) if cell_value is not None else ''

                # 차이점 분석
                differences = []
                for col in ['C', 'D', 'E', 'H']:
                    template_val = template_row[col]
                    generated_val = generated_row[col]
                    if template_val != generated_val:
                        differences.append(f'{col}:{template_val}→{generated_val}')

                if differences:
                    file_issues.append(f"행{row}: {', '.join(differences)}")

                # 공통 패턴 분석
                if row == 9 and generated_row['D'] != '임금항목':
                    common_issues['structure_mismatch'].append(f"{file}: 헤더 불일치")
                if row == 10 and generated_row['D'] != '기본급':
                    common_issues['structure_mismatch'].append(f"{file}: 기본급 항목명 불일치")
                if row >= 11 and row <= 16 and generated_row['E'] == '':
                    common_issues['value_errors'].append(f"{file} 행{row}: 금액 빈 값")

            if file_issues:
                print(f"발견된 문제점들:")
                for issue in file_issues[:5]:  # 처음 5개만 표시
                    print(f"  - {issue}")
                if len(file_issues) > 5:
                    print(f"  ... 및 {len(file_issues) - 5}개 더")
            else:
                print("특별한 문제점 없음")

            wb.close()

        except Exception as e:
            print(f"{file} 분석 실패: {e}")

    print("\n3. 공통 문제점 요약:")
    print(f"- 구조 불일치: {len(set(common_issues['structure_mismatch']))}개 파일")
    print(f"- 값 오류: {len(set(common_issues['value_errors']))}개 파일")
    print(f"- 포맷 문제: {len(set(common_issues['formatting_issues']))}개 파일")

    if common_issues['structure_mismatch']:
        print("\n구조 불일치 상세:")
        for issue in set(common_issues['structure_mismatch']):
            print(f"  - {issue}")

    if common_issues['value_errors']:
        print("\n값 오류 상세:")
        for issue in set(common_issues['value_errors'][:3]):  # 처음 3개만
            print(f"  - {issue}")

    print("\n4. 근본 원인 분석:")
    print("- 템플릿 복사 시 행 구조 변경")
    print("- 데이터 입력 위치 계산 오류")
    print("- 병합 셀 처리 불완전")
    print("- 항목명과 금액의 행 매핑 불일치")

if __name__ == "__main__":
    analyze_template_vs_generated()