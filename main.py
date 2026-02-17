import copy
import os
import pandas as pd
import openpyxl
from datetime import datetime, timedelta
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- 상수 정의 ---
# TypeScript 스크립트의 상수들을 여기에 정의합니다.
HEADER_ROW_COUNT = 2
HOLIDAY_ALLOWANCE_HOURS = 15
WEEKLY_STANDARD_HOURS = 40
DAILY_STANDARD_HOURS = 8
OVERTIME_MULTIPLIER = 1.5

# --- 헬퍼 함수 ---
def parse_work_hours(value):
    """
    다양한 형태의 근무시간 값을 분(minute) 단위로 변환합니다.
    - 숫자 (0~1 사이): 엑셀 시간 서식으로 간주 (예: 0.5 -> 12시간 -> 720분)
    - 숫자 (1 이상): 분(minute)으로 간주
    - 문자열 ('HH:MM'): 시간:분 형식으로 간주
    """
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        if 0 < value < 1:
            return round(value * 1440)
        return round(value)
    if isinstance(value, str):
        parts = value.strip().split(":")
        hours = int(parts[0]) if parts[0] else 0
        minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        return hours * 60 + minutes
    if isinstance(value, datetime.time):
        return value.hour * 60 + value.minute
    return 0

def get_start_of_week(date):
    """
    주어진 날짜의 해당 주의 시작일(월요일)을 반환합니다.
    """
    start_of_week = date - timedelta(days=date.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

# --- 1단계: 엑셀 파일 로드 및 전처리 ---
def load_and_preprocess_data(file_path, target_month=None):
    """
    엑셀 파일을 로드하고 기본적인 전처리를 수행합니다.
    - target_month가 주어지면 해당 월의 시트만 처리합니다.
    - target_month가 없으면 모든 월 시트를 처리합니다.
    """
    print(f"'{file_path}' 파일 로딩 중...")
    try:
        xls = pd.ExcelFile(file_path)
        all_dfs = []
        
        # 월별 시트 이름 패턴
        month_sheet_pattern = r'^(\d{1,2}월|\d{4}년 \d{1,2}월)$'
        
        # 처리할 시트 목록 결정
        sheets_to_process = []
        for sheet_name in xls.sheet_names:
            if pd.Series([sheet_name]).str.match(month_sheet_pattern).any():
                # 시트 이름에서 숫자 부분만 추출하여 월로 사용 (예: "11월" -> 11, "2025년 12월" -> 12)
                month_str = ''.join(filter(str.isdigit, sheet_name))
                if len(month_str) > 2: # "202512" 같은 경우 마지막 두자리만
                    sheet_month = int(month_str[-2:])
                else:
                    sheet_month = int(month_str)
                
                if target_month is None or sheet_month == target_month:
                    sheets_to_process.append(sheet_name)

        if not sheets_to_process:
            if target_month:
                print(f"오류: '{file_path}'에서 '{target_month}월'에 해당하는 시트를 찾을 수 없습니다.")
            else:
                print(f"오류: '{file_path}'에서 처리할 월별 시트를 찾을 수 없습니다.")
            return None

        print(f"다음 시트를 처리합니다: {', '.join(sheets_to_process)}")

        for sheet_name in sheets_to_process:
            df = xls.parse(sheet_name, header=HEADER_ROW_COUNT - 1)
            
            # DataFrame의 실제 열 이름을 확인하고 누락된 부분을 채웁니다.
            try:
                # xls.parse로 시트별 첫 행을 다시 읽어 헤더로 사용
                first_row_df = xls.parse(sheet_name, header=None, nrows=1)
                new_headers = [str(h) if pd.notna(h) else '' for h in first_row_df.iloc[0]]
                
                final_headers = []
                for i, col in enumerate(df.columns):
                    if 'Unnamed' in str(col) and i < len(new_headers) and new_headers[i]:
                        final_headers.append(new_headers[i])
                    else:
                        final_headers.append(str(col))
                
                df.columns = final_headers
            except Exception as e:
                print(f"추가 헤더 처리 중 오류 발생 (무시하고 진행): {e}")
            
            all_dfs.append(df)
            print(f"시트 '{sheet_name}' 로드 완료.")

        final_df = pd.concat(all_dfs, ignore_index=True)
        print("모든 시트 데이터 결합 완료. 데이터 샘플:")
        print(final_df.head())
        return final_df
    except FileNotFoundError:
        print(f"오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"오류: 파일을 읽는 중 문제가 발생했습니다 - {e}")
        return None


# --- 2단계: 급여 계산 로직 ---
def calculate_salary(df):
    """
    DataFrame을 입력받아 주휴수당 및 각종 급여를 계산합니다.
    """
    print("급여 계산 로직 실행 중...")

    # 데이터 타입 변환 및 정리
    # '근무일자'가 날짜 형식이 아닐 경우를 대비하여 에러 핸들링 추가
    df['근무일자'] = pd.to_datetime(df['근무일자'], errors='coerce')
    df.dropna(subset=['근무일자', '사용자아이디'], inplace=True) # 날짜나 사용자 ID 없는 행 제거
    
    # 시간 관련 컬럼들을 분 단위로 변환
    time_cols = ['근무시간', '연장시간', '심야시간']
    for col in time_cols:
        # 해당 컬럼이 존재할 경우에만 변환 수행
        if col in df.columns:
            df[col + '_분'] = df[col].apply(parse_work_hours)
        else:
            df[col + '_분'] = 0 # 컬럼이 없으면 0으로 초기화
            
    # 시급금액을 숫자로 변환
    df['시급금액'] = pd.to_numeric(df['시급금액'], errors='coerce').fillna(0)

    # 주별 그룹화를 위해 '주 시작일' 컬럼 추가
    df['주_시작일'] = df['근무일자'].apply(get_start_of_week)

    # 새로운 결과 컬럼 초기화
    df['주휴시간(분단위)'] = 0
    df['주휴수당'] = 0.0

    # 사용자별로 그룹화하여 계산
    for user_id, user_df in df.groupby('사용자아이디'):
        # 주별로 다시 그룹화
        for week_start, week_df in user_df.groupby('주_시작일'):
            # 주간 총 근무시간 (분)
            total_minutes = week_df['근무시간_분'].sum()
            total_hours = total_minutes / 60.0

            # 주휴수당 발생 조건 확인
            if total_hours >= HOLIDAY_ALLOWANCE_HOURS:
                # 주휴수당으로 지급될 총 시간 (주간 근무시간 / 40 * 8)
                paid_hours = (total_hours / WEEKLY_STANDARD_HOURS) * DAILY_STANDARD_HOURS
                total_holiday_minutes = round(paid_hours * 60)

                # 해당 주의 각 근무일에 비례하여 주휴시간 배분
                for index, row in week_df.iterrows():
                    daily_minutes = row['근무시간_분']
                    if total_minutes > 0:
                        ratio = daily_minutes / total_minutes
                        prorated_holiday_minutes = round(total_holiday_minutes * ratio)
                        prorated_holiday_pay = paid_hours * row['시급금액'] * ratio
                        
                        # 원본 DataFrame에 결과 업데이트
                        df.loc[index, '주휴시간(분단위)'] = prorated_holiday_minutes
                        df.loc[index, '주휴수당'] = prorated_holiday_pay

    # 기본급, 연장수당, 심야수당, 최종 급여 계산
    df['기본급'] = (df['근무시간_분'] / 60) * df['시급금액']
    df['연장수당'] = (df['연장시간_분'] / 60) * df['시급금액'] * OVERTIME_MULTIPLIER
    df['심야수당'] = (df['심야시간_분'] / 60) * df['시급금액'] * OVERTIME_MULTIPLIER
    
    # '예상급여금액'은 기본급 + 연장수당 + 심야수당
    df['예상급여금액'] = df['기본급'] + df['연장수당'] + df['심야수당']

    # '총급여액'은 예상급여금액 + 주휴수당
    df['총급여액'] = df['예상급여금액'] + df['주휴수당']

    print("급여 계산 완료.")
    return df

# --- 3단계: 사용자별 합계 생성 ---
def create_user_summaries(df):
    """
    사용자별로 급여 정보를 집계하여 요약본을 생성합니다.
    """
    print("사용자별 합계 생성 중...")
    
    # 집계할 컬럼 정의
    agg_dict = {
        '성명': 'first', # 그룹의 첫 번째 이름을 사용
        '예상급여금액': 'sum',
        '주휴시간(분단위)': 'sum',
        '주휴수당': 'sum',
        '총급여액': 'sum',
        '기본급': 'sum',
        '연장수당': 'sum',
        '심야수당': 'sum',
        '연장시간_분': 'sum',
        '심야시간_분': 'sum',
        '시급금액': 'first', # 통상시급으로 사용
        '근무시간_분': 'sum' # 기본급 산출식에 사용
    }
    
    # 사용자아이디로 그룹화하고 집계
    user_summaries = df.groupby('사용자아이디').agg(agg_dict).reset_index()
    
    print("사용자별 합계 생성 완료.")
    return user_summaries

# --- 4단계: 급여명세서 생성 ---
def generate_payslips(summaries_df, template_path="급여명세서.xlsx", output_filename="급여명세서_결과.xlsx", data_month=None, company_name=""):
    """
    v2 분석 기반, 템플릿의 셀을 명시적으로 복사한 후 데이터를 채워넣어
    최종 급여명세서 파일을 생성합니다.
    """
    print("템플릿 셀 명시적 복사 후 최종 급여명세서 생성 중...")
    
    try:
        # 템플릿 워크북을 로드합니다 (수식 유지를 위해 data_only=False)
        template_wb = openpyxl.load_workbook(template_path, data_only=False)
        template_sheet = template_wb['명세서'] # '명세서' 시트를 템플릿으로 명시적 지정
    except FileNotFoundError:
        print(f"오류: 템플릿 파일 '{template_path}'을(를) 찾을 수 없습니다.")
        return
    except KeyError:
        print(f"오류: 템플릿 파일에서 '명세서' 시트를 찾을 수 없습니다.")
        return

    # 결과를 저장할 새로운 워크북 생성
    result_wb = openpyxl.Workbook()
    if "Sheet" in result_wb.sheetnames:
        result_wb.remove(result_wb["Sheet"]) # 기본 시트 제거

    for index, user_summary in summaries_df.iterrows():
        sheet_name = ''.join(c for c in user_summary['성명'] if c.isalnum())
        new_ws = result_wb.create_sheet(title=sheet_name)

        # 1. 템플릿 시트의 모든 셀 값, 스타일, 병합 범위, 행/열 크기 복사
        for row in template_sheet.iter_rows():
            for cell in row:
                new_cell = new_ws[cell.coordinate]
                new_cell.value = cell.value
                
                # 스타일 직접 할당 (copy.copy() 사용)
                if cell.has_style:
                    new_cell.font = copy.copy(cell.font)
                    new_cell.alignment = copy.copy(cell.alignment)
                    new_cell.border = copy.copy(cell.border)
                    new_cell.fill = copy.copy(cell.fill)
                    new_cell.number_format = cell.number_format # number_format은 직접 할당
                    new_cell.protection = copy.copy(cell.protection) # 보호 설정 복사

        # 병합된 셀 범위 복사 (기존 코드 유지)
        for merged_range in template_sheet.merged_cells.ranges:
            new_ws.merge_cells(str(merged_range))

        # 행 높이 및 열 너비 복사 (속성 개별 복사, customHeight/Width는 추론됨)
        for row_idx, row_dim in template_sheet.row_dimensions.items():
            new_dim = new_ws.row_dimensions[row_idx]
            if row_dim.height is not None: # 높이가 명시적으로 설정된 경우만 복사
                new_dim.height = row_dim.height
            new_dim.hidden = row_dim.hidden
            new_dim.outlineLevel = row_dim.outlineLevel
            new_dim.collapsed = row_dim.collapsed
            # customHeight는 height가 설정되면 openpyxl에서 자동으로 관리함
        for col_idx, col_dim in template_sheet.column_dimensions.items():
            new_dim = new_ws.column_dimensions[col_idx]
            if col_dim.width is not None: # 너비가 명시적으로 설정된 경우만 복사
                new_dim.width = col_dim.width
            new_dim.hidden = col_dim.hidden
            new_dim.bestFit = col_dim.bestFit
            new_dim.outlineLevel = col_dim.outlineLevel
            new_dim.collapsed = col_dim.collapsed
            # customWidth는 width가 설정되면 openpyxl에서 자동으로 관리함

        # 2. 동적 데이터 채우기 (새 시트 new_ws에 적용)
        
        # --- 기본 정보 채우기 (v2 분석 기준) ---
        new_ws['C2'] = f"({data_month})월 급여명세서"
        new_ws['D4'] = user_summary['성명']
        new_ws['G4'] = user_summary['사용자아이디'] 
        new_ws['D3'] = company_name # 회사명 (D3에 값 입력)
        new_ws['D3'].data_type = 's' # 명시적으로 문자열 타입 지정
        
        # 추가 기본 정보 필드 (데이터가 없으므로 빈 문자열)
        new_ws['D5'] = "" # 부서 (C5 옆)
        new_ws['G5'] = "" # 직급 (F5 옆)
        new_ws['D6'] = "" # 입사일 (C6 옆)
        new_ws['G6'] = "" # 지급일 (F6 옆)
        
        # --- 계산 영역 (H열)에 데이터 채우기 ---
        new_ws['H26'] = user_summary.get('기본급', 0)
        new_ws['H27'] = user_summary.get('주휴수당', 0)
        new_ws['H28'] = user_summary.get('심야수당', 0)
        new_ws['H29'] = 0 # 휴일근로수당
        new_ws['H30'] = user_summary.get('연장수당', 0)

        # --- 공제 항목 값 채우기 (H열) ---
        new_ws['H11'] = 0 # 국민연금
        new_ws['H12'] = 0 # 건강보험
        new_ws['H13'] = 0 # 고용보험
        new_ws['H14'] = 0 # 장기요양보험
        new_ws['H15'] = 0 # 소득세
        new_ws['H16'] = 0 # 지방소득세
        
        # --- 세부 지급 항목 표시 영역 (D열)에 직접 값 채우기 ---
        new_ws['D11'] = user_summary.get('기본급', 0) # 기본급
        new_ws['D13'] = user_summary.get('연장수당', 0) # 연장근로수당
        new_ws['D14'] = user_summary.get('심야수당', 0) # 야간근로수당
        new_ws['D15'] = 0 # 휴일근로수당 (현재 로직에 없으므로 0)
        new_ws['D17'] = 0 # 직급수당 (현재 로직에 없으므로 0)
        new_ws['D18'] = 0 # 기타수당 (현재 로직에 없으므로 0)
        
        # D16 (주휴수당)은 수식(=H27)이 있으므로 직접 건드리지 않습니다.

        # --- 합계 및 실수령액 직접 계산 및 입력 ---
        total_payment = user_summary['총급여액']
        new_ws['D20'] = total_payment

        total_deduction = sum([new_ws[f'H{i}'].value for i in range(11, 17) if new_ws[f'H{i}'].value is not None])
        new_ws['H20'] = total_deduction
        
        net_pay = total_payment - total_deduction
        new_ws['D21'] = net_pay

        # --- 연장/야간/휴일 근로시간 합계 입력 (C23, D23, E23) ---
        new_ws['C23'] = user_summary.get('연장시간_분', 0)
        new_ws['D23'] = user_summary.get('심야시간_분', 0)
        new_ws['E23'] = 0

        # --- 통상시급 시급 값 저장 (G23) ---
        new_ws['G23'] = user_summary.get('시급금액', 0)

        # --- 항목별 계산 방법 (D26:D30) ---
        new_ws['D26'] = f"(총 {user_summary.get('근무시간_분', 0)}분 / 60) * {int(user_summary.get('시급금액', 0))}원"
        new_ws['D27'] = f"주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무 시: 주간 근무 비례, 1일 {DAILY_STANDARD_HOURS}시간분 시급 {int(user_summary.get('시급금액', 0))}원 지급"
        new_ws['D27'].alignment = Alignment(wrap_text=True)
        new_ws.row_dimensions[27].height = 40
        new_ws['D28'] = f"(총 {user_summary.get('심야시간_분', 0)}분 / 60) * {int(user_summary.get('시급금액', 0))}원 * {OVERTIME_MULTIPLIER}배"
        new_ws['D29'] = "해당없음 (0)"
        new_ws['D30'] = f"(총 {user_summary.get('연장시간_분', 0)}분 / 60) * {int(user_summary.get('시급금액', 0))}원 * {OVERTIME_MULTIPLIER}배"
    
    # 최종 워크북 저장
    try:
        result_wb.save(output_filename)
        print(f"급여명세서가 '{output_filename}' 파일로 최종 저장되었습니다.")
    except Exception as e:
        print(f"파일 저장 중 오류가 발생했습니다: {e}")


import argparse
# --- 메인 실행 함수 ---
def main():
    """
    프로그램의 전체 실행 흐름을 제어합니다.
    """
    parser = argparse.ArgumentParser(description="급여 명세서 생성 프로그램")
    parser.add_argument('--file', type=str, required=True, help='처리할 입력 엑셀 파일 경로 (예: "전체근태.xlsx")')
    parser.add_argument('--month', type=int, help='처리할 월 (예: 11). 지정하지 않으면 모든 월 시트 처리.')
    args = parser.parse_args()

    print("급여 계산 프로그램을 시작합니다.")
    
    # input_file 변수를 명령줄 인자에서 가져오도록 변경
    input_file = args.file
    
    # 파일명에서 회사명 추출 (확장자 제외)
    company_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # 1. 데이터 로드 및 전처리
    # load_and_preprocess_data 함수에 month 인자 전달
    df = load_and_preprocess_data(input_file, target_month=args.month)
    
    if df is None or df.empty:
        print("데이터 로딩에 실패했거나 처리할 데이터가 없어 프로그램을 종료합니다.")
        return

    # 2. 급여 계산
    df_calculated = calculate_salary(df)
    
    print("계산 완료 후 데이터 샘플 (새 컬럼 추가):")
    print(df_calculated.head())

    # 3. 사용자별 합계
    summaries = create_user_summaries(df_calculated)
    
    # 4. 급여명세서 생성 전, 데이터의 월 추출
    # 처리된 데이터의 첫 번째 근무일자에서 월을 추출 (모든 데이터가 같은 월이라고 가정)
    data_month = df_calculated['근무일자'].dt.month.iloc[0]
    
    print("사용자별 급여 요약:")
    print(summaries)

    # 4. 급여명세서 생성
    generate_payslips(summaries, data_month=data_month)
    
    print("모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
