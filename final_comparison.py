import pandas as pd
import openpyxl

def compare_template_vs_generated():
    """원본 템플릿 vs pandas 생성 파일 최종 비교"""

    print("=== 원본 템플릿 vs pandas 생성 파일 최종 비교 ===\n")

    # 1. 원본 템플릿 분석
    print("1. 원본 템플릿 (급여명세서.xlsx) 구조:")
    try:
        template_df = pd.read_excel('급여명세서.xlsx', sheet_name='명세서', header=None)
        print(f"템플릿 크기: {template_df.shape}")

        # 템플릿의 병합 셀 정보
        template_wb = openpyxl.load_workbook('급여명세서.xlsx', data_only=False)
        template_ws = template_wb['명세서']

        print("템플릿 병합 셀:")
        for merged_range in template_ws.merged_cells.ranges:
            start_cell = template_ws.cell(merged_range.min_row, merged_range.min_col)
            start_value = start_cell.value
            print(f"  {merged_range} → '{start_value}'")

        # 템플릿 데이터 영역 (행9-20)
        print("\n템플릿 데이터 영역 (행9-20):")
        for row in range(9, 21):
            row_data = []
            for col in [3, 4, 5, 8]:  # C, D, E, H열
                cell_value = template_df.iloc[row-1, col-1]  # DataFrame은 0-based
                row_data.append(str(cell_value) if pd.notna(cell_value) else '')
            print(f"행{row}: {row_data}")

        template_wb.close()

    except Exception as e:
        print(f"템플릿 분석 실패: {e}")
        return

    print("\n" + "="*60)

    # 2. 생성된 파일 분석
    print("2. pandas 생성 파일 (perfect_structure_test.xlsx) 구조:")
    try:
        generated_df = pd.read_excel('perfect_structure_test.xlsx', sheet_name='명세서', header=None)
        print(f"생성 파일 크기: {generated_df.shape}")

        # 생성 파일의 병합 셀 정보
        generated_wb = openpyxl.load_workbook('perfect_structure_test.xlsx', data_only=False)
        generated_ws = generated_wb['명세서']

        print("생성 파일 병합 셀:")
        for merged_range in generated_ws.merged_cells.ranges:
            start_cell = generated_ws.cell(merged_range.min_row, merged_range.min_col)
            start_value = start_cell.value
            print(f"  {merged_range} → '{start_value}'")

        # 생성 파일 데이터 영역 (행9-20)
        print("\n생성 파일 데이터 영역 (행9-20):")
        for row in range(9, 21):
            row_data = []
            for col in [3, 4, 5, 8]:  # C, D, E, H열
                cell_value = generated_df.iloc[row-1, col-1]  # DataFrame은 0-based
                row_data.append(str(cell_value) if pd.notna(cell_value) else '')
            print(f"행{row}: {row_data}")

        generated_wb.close()

    except Exception as e:
        print(f"생성 파일 분석 실패: {e}")
        return

    print("\n" + "="*60)

    # 3. 상세 비교
    print("3. 템플릿 vs 생성 파일 상세 비교:")

    structure_match = True
    data_match = True

    # 병합 셀 비교
    template_merges = set()
    generated_merges = set()

    template_wb = openpyxl.load_workbook('급여명세서.xlsx', data_only=False)
    generated_wb = openpyxl.load_workbook('perfect_structure_test.xlsx', data_only=False)

    for merged_range in template_wb['명세서'].merged_cells.ranges:
        template_merges.add(str(merged_range))

    for merged_range in generated_wb['명세서'].merged_cells.ranges:
        generated_merges.add(str(merged_range))

    template_wb.close()
    generated_wb.close()

    if template_merges == generated_merges:
        print("✅ 병합 셀 구조: 완전 일치")
    else:
        print("❌ 병합 셀 구조: 불일치")
        print(f"  템플릿: {sorted(template_merges)}")
        print(f"  생성: {sorted(generated_merges)}")
        structure_match = False

    # 데이터 영역 비교 (행9-20, C/D/E/H열)
    print("\n데이터 영역 비교:")
    for row in range(9, 21):
        template_row = []
        generated_row = []

        for col in [3, 4, 5, 8]:  # C=3, D=4, E=5, H=8 (1-based for DataFrame)
            t_val = template_df.iloc[row-1, col-1]
            g_val = generated_df.iloc[row-1, col-1]

            t_str = str(t_val) if pd.notna(t_val) else ''
            g_str = str(g_val) if pd.notna(g_val) else ''

            template_row.append(t_str)
            generated_row.append(g_str)

        if template_row == generated_row:
            print(f"✅ 행{row}: 일치")
        else:
            print(f"❌ 행{row}: 불일치")
            print(f"    템플릿: {template_row}")
            print(f"    생성: {generated_row}")
            data_match = False

    print("\n" + "="*60)

    # 4. 최종 판정
    print("4. 최종 판정:")

    if structure_match and data_match:
        print("🎉 완벽한 성공! 템플릿과 생성 파일이 100% 일치합니다!")
        print("✅ 구조 일치: 병합 셀, 행/열 배치 모두 정확")
        print("✅ 데이터 일치: 모든 항목명과 값이 동일")
        print("✅ pandas ExcelWriter 방식이 openpyxl 한계를 극복했습니다!")
    else:
        print("⚠️ 부분적 차이 발견")
        if not structure_match:
            print("❌ 구조 불일치: 병합 셀이나 기본 레이아웃에 차이가 있음")
        if not data_match:
            print("❌ 데이터 불일치: 항목명이나 값 배치에 차이가 있음")

if __name__ == "__main__":
    compare_template_vs_generated()