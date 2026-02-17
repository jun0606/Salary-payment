import openpyxl
import pandas as pd

def fix_excel_structure_approach():
    """근본적인 Excel 구조 문제 해결 방안"""

    print("=== 근본적인 Excel 구조 문제 해결 방안 ===\n")

    # 1. 템플릿 분석
    print("1. 템플릿 구조 심층 분석:")
    template_wb = openpyxl.load_workbook('급여명세서.xlsx', data_only=False)
    template_ws = template_wb['명세서']

    print(f"템플릿 최대 행: {template_ws.max_row}")
    print(f"템플릿 최대 열: {template_ws.max_column}")

    # 병합 셀 정보 출력
    print("\n병합 셀 정보:")
    try:
        for merged_range in template_ws.merged_cells.ranges:
            print(f"  {merged_range}")
    except:
        print("  병합 셀 정보 확인 불가")

    # 각 행의 실제 데이터 구조 출력
    print("\n각 행 데이터 구조:")
    for row in range(9, 21):  # 데이터 영역
        row_data = {}
        for col in range(3, 9):  # C부터 H까지 (1=C, 2=D, 3=E, 4=F, 5=G, 6=H)
            cell = template_ws.cell(row=row, column=col)
            row_data[chr(65 + col - 1)] = cell.value  # A=65, B=66, C=67...
        print(f"행{row}: {row_data}")

    template_wb.close()

    print("\n2. 근본적 해결 방안:")
    print("방안 1: 템플릿 복사 + 값 교체만 수행")
    print("방안 2: 병합 셀 완전 해제 + 개별 셀 데이터 입력")
    print("방안 3: 템플릿을 DataFrame으로 변환 후 재생성")
    print("방안 4: xlwings 라이브러리 사용 검토")

    print("\n3. 권장 접근법:")
    print("- 현재: 방안 2 (병합 셀 해제 + 개별 셀 입력) 이미 시도")
    print("- 다음: 방안 1 (완전 복사 + 최소 값 교체) 시도")
    print("- 최종: 방안 3 (DataFrame 기반 재생성) 고려")

def implement_fix_approach_1():
    """방안 1: 템플릿 완전 복사 + 값 교체만 수행"""

    print("\n=== 방안 1 구현: 템플릿 완전 복사 + 값 교체만 ===")

    try:
        # 템플릿 복사
        import shutil
        shutil.copy2('급여명세서.xlsx', 'test_fixed_structure.xlsx')

        # 복사된 파일 열기
        wb = openpyxl.load_workbook('test_fixed_structure.xlsx', data_only=False)
        ws = wb['명세서']

        # 데이터 영역 값 교체 (병합 셀 건드리지 않음)
        # 행10: 기본급
        # 병합 셀에 속한 셀들은 수정하지 말고, 병합 셀의 시작 셀만 수정
        if 'C10' in [cell.coordinate for merged_range in ws.merged_cells.ranges for cell in merged_range.cells]:
            print("행10 C열은 병합 셀에 속함 - 수정하지 않음")
        else:
            ws['C10'] = "기본급"
            ws['D10'] = 660000  # 기본급 금액

        wb.save('test_fixed_structure.xlsx')
        wb.close()

        print("방안 1 테스트 파일 생성 완료: test_fixed_structure.xlsx")

    except Exception as e:
        print(f"방안 1 실패: {e}")

if __name__ == "__main__":
    fix_excel_structure_approach()
    implement_fix_approach_1()