import copy
import pandas as pd
import openpyxl
from datetime import datetime, timedelta
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import logging
import os
import shutil
from openpyxl.styles import Font, Alignment, Border, Side

from jinja2 import Template

# --- 로깅 설정 (보안 강화) ---
log_format = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'

# 민감한 정보를 필터링하는 로거 클래스
class SecureLogger:
    def __init__(self):
        self.logger = logging.getLogger('secure_logger')
        self.logger.setLevel(logging.INFO)  # DEBUG 레벨 제거

        # 핸들러가 이미 추가되었는지 확인
        if not self.logger.handlers:
            handler = logging.FileHandler('debug.log', mode='w', encoding='utf-8')
            handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(handler)

    def _filter_sensitive_info(self, message):
        """민감한 정보를 필터링하거나 마스킹"""
        import re

        # HW ID 해시 패턴 마스킹 (64자 해시)
        message = re.sub(r'\b[a-f0-9]{64}\b', '[HW_ID_MASKED]', message)

        # 라이선스 파일 경로 마스킹
        message = re.sub(r'C:\\ProgramData\\PayslipApp\\license\\[^\\]+\.dat',
                        '[LICENSE_FILE_PATH_MASKED]', message)

        # 기타 민감한 경로 정보 마스킹
        message = re.sub(r'C:\\[^\\]*\\[^\\]*\\[^\\]*', '[PATH_MASKED]', message)

        # 라이선스 데이터 마스킹
        message = re.sub(r'hw_id:[^|]+', 'hw_id:[MASKED]', message)
        message = re.sub(r'expires:[^|]+', 'expires:[MASKED]', message)

        return message

    def debug(self, message, *args, **kwargs):
        """DEBUG 레벨 - 프로덕션에서 비활성화"""
        # 프로덕션 환경에서는 DEBUG 로깅을 하지 않음 (보안 강화)
        pass

    def info(self, message, *args, **kwargs):
        """INFO 레벨 로깅"""
        filtered_message = self._filter_sensitive_info(message)
        self.logger.info(filtered_message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """WARNING 레벨 로깅"""
        filtered_message = self._filter_sensitive_info(message)
        self.logger.warning(filtered_message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """ERROR 레벨 로깅"""
        filtered_message = self._filter_sensitive_info(message)
        self.logger.error(filtered_message, *args, **kwargs)

# 전역 로거 인스턴스 생성
logging = SecureLogger()


# --- Constants ---
HEADER_ROW_COUNT = 2
HOLIDAY_ALLOWANCE_HOURS = 15
WEEKLY_STANDARD_HOURS = 40
DAILY_STANDARD_HOURS = 8
OVERTIME_MULTIPLIER = 1.5

# --- Helper Functions ---
def parse_work_hours(value):
    """Converts various work hour formats to minutes."""
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        if 0 < value < 1:
            return round(value * 1440)
        return round(value)
    if isinstance(value, str):
        try:
            parts = value.strip().split(":")
            hours = int(parts[0]) if parts[0] else 0
            minutes = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return hours * 60 + minutes
        except (ValueError, IndexError):
             return 0
    if isinstance(value, datetime.time):
        return value.hour * 60 + value.minute
    return 0

def get_start_of_week(date):
    """Returns the start of the week (Monday) for a given date."""
    start_of_week = date - timedelta(days=date.weekday())
    return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

def calculate_holiday_week_rate(user_data, user_id):
    """주휴수당 발생 주의 시급들을 계산합니다.

    실제 시스템 로직에 따라 주휴수당 해당 날짜를 그룹화하고,
    해당 그룹의 시급들만 반환합니다.

    Args:
        user_data: 사용자의 근무 데이터 (DataFrame)
        user_id: 사용자 ID

    Returns:
        list: 주휴수당 발생 주의 시급 리스트 (중복 제거, 정렬)
    """
    if user_data is None or user_data.empty:
        print(f"DEBUG: user_data is None or empty")
        return []

    # 해당 사용자의 데이터만 필터링
    user_specific_data = user_data[user_data['Unnamed: 1'] == user_id].copy()
    print(f"DEBUG: user_id={user_id}, user_specific_data.shape={user_specific_data.shape}")

    if user_specific_data.empty:
        print(f"DEBUG: user_specific_data is empty for user_id={user_id}")
        return []

    # 주별로 그룹화하여 주휴수당 발생 주 찾기
    user_specific_data['근무일자'] = pd.to_datetime(user_specific_data['Unnamed: 3'], errors='coerce')
    user_specific_data['주_시작일'] = user_specific_data['근무일자'].apply(get_start_of_week)

    print(f"DEBUG: user_specific_data columns: {user_specific_data.columns.tolist()}")
    print(f"DEBUG: unique weeks: {user_specific_data['주_시작일'].unique()}")

    holiday_week_rates = []

    for week_start, week_df in user_specific_data.groupby('주_시작일'):
        print(f"DEBUG: processing week {week_start}, week_df.shape={week_df.shape}")

        # 해당 주의 총 근무시간 계산 (실제 시스템과 동일하게)
        total_minutes = 0
        for idx, row in week_df.iterrows():
            # 실제 시스템에서는 시작시간과 종료시간으로 근무시간 계산
            start_time_str = str(row['시간'])
            end_time_str = str(row['시간.1'])

            work_minutes = 0
            if ':' in start_time_str and ':' in end_time_str:
                try:
                    start_hour, start_min = map(int, start_time_str.split(':'))
                    end_hour, end_min = map(int, end_time_str.split(':'))

                    start_total_min = start_hour * 60 + start_min
                    end_total_min = end_hour * 60 + end_min

                    # 종료시간이 시작시간보다 작은 경우 (다음날로 넘어가는 경우)
                    if end_total_min < start_total_min:
                        end_total_min += 24 * 60  # 24시간 추가

                    work_minutes = end_total_min - start_total_min
                except (ValueError, IndexError):
                    work_minutes = 0

            total_minutes += work_minutes

        total_hours = total_minutes / 60.0
        print(f"DEBUG: week {week_start}, total_hours={total_hours}")

        # 주휴수당 발생 조건 확인 (15시간 이상)
        if total_hours >= HOLIDAY_ALLOWANCE_HOURS:
            print(f"DEBUG: 주휴수당 발생! week={week_start}, total_hours={total_hours}")
            # 해당 주의 시급들을 모두 수집 (중복 제거)
            week_rates = week_df['Unnamed: 12'].dropna().unique()
            holiday_week_rates = sorted(list(week_rates))
            print(f"DEBUG: holiday_week_rates={holiday_week_rates}")
            break  # 첫 번째로 발견된 주휴수당 발생 주 사용

    print(f"DEBUG: final holiday_week_rates={holiday_week_rates}")
    return holiday_week_rates

# --- Core Logic Functions ---

def load_and_preprocess_data(file_path, target_month=None):
    """Loads and preprocesses data from the Excel file."""
    logging.info(f"--- Starting load_and_preprocess_data for file: {file_path}, month: {target_month} ---")
    try:
        xls = pd.ExcelFile(file_path)
        all_dfs = []
        
        month_sheet_pattern = r'^(\d{1,2}월|\d{4}년 \d{1,2}월)$'
        
        sheets_to_process = []
        logging.info(f"Available sheets: {xls.sheet_names}")
        for sheet_name in xls.sheet_names:
            if pd.Series([sheet_name]).str.match(month_sheet_pattern).any():
                month_str = ''.join(filter(str.isdigit, sheet_name))
                sheet_month = int(month_str[-2:]) if len(month_str) > 2 else int(month_str)
                
                if target_month is None or sheet_month == target_month:
                    sheets_to_process.append(sheet_name)
        
        logging.info(f"Sheets to process: {sheets_to_process}")

        if not sheets_to_process:
            error_msg = f"'{file_path}'에서 '{target_month}월'에 해당하는 시트를 찾을 수 없습니다." if target_month else f"'{file_path}'에서 처리할 월별 시트를 찾을 수 없습니다."
            logging.error(error_msg)
            raise ValueError(error_msg)

        for sheet_name in sheets_to_process:
            logging.debug(f"Parsing sheet: {sheet_name}")
            df = xls.parse(sheet_name, header=HEADER_ROW_COUNT - 1)
            logging.debug(f"Initial columns for sheet '{sheet_name}': {df.columns.to_list()}")
            
            # 헤더 처리 생략 - 원본 Unnamed 컬럼명 유지
            # 데이터 구조 보존을 위해 헤더 변경하지 않음
            logging.debug(f"Columns for sheet '{sheet_name}': {df.columns.to_list()}")
            
            all_dfs.append(df)

        final_df = pd.concat(all_dfs, ignore_index=True)
        logging.info(f"Data loaded successfully. Shape: {final_df.shape}, Columns: {final_df.columns.to_list()}")
        return final_df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
    except Exception as e:
        logging.error(f"Error reading file: {e}", exc_info=True)
        raise Exception(f"파일을 읽는 중 문제가 발생했습니다: {e}")


def calculate_salary(df):
    """
    Calculates salaries, allowances, and deductions.

    수당 계산 규칙:
    - 휴일근로수당: 일요일, 공휴일에 근무한 경우 8시간까지는 1.5배, 8시간 초과는 2배 지급
    - 각종수당: 5인미만 사업장은 연장,휴일,야간수당 지급의무가 없음
    - 야근근로시간: 22~06중 근무한 시간 기재
    - 연장근로시간: 하루 8시간 기본근로시간을 초과해서 근무하는 시간 기재
    - 연장,야근 중복시: 연장근로시간은 야간 근로시간 포함해서 기재하고 야근 근로시간은 야근근로시간만 기재

    계산 방식:
    - 기본급: (근무시간_분 / 60) * 시급금액
    - 연장수당: (연장시간_분 / 60) * 시급금액 * 1.5배
    - 야간수당: (심야시간_분 / 60) * 시급금액 * 1.5배
    - 주휴수당: 주 15시간 이상 근무 시 주간 근무시간 비례 계산
    """
    logging.info(f"--- Starting calculate_salary. Input df shape: {df.shape} ---")
    
    df['근무일자'] = pd.to_datetime(df['Unnamed: 3'], errors='coerce')
    df.dropna(subset=['근무일자', 'Unnamed: 1'], inplace=True)
    logging.debug(f"Shape after dropping NA in date/user_id: {df.shape}")
    
    # 실제 데이터 컬럼 매핑 (J열=근무시간, K열=연장시간, L열=심야시간)
    time_col_mapping = {
        '근무시간': 'Unnamed: 9',  # J열: 실제 근무시간 (휴식시간 제외)
        '연장시간': 'Unnamed: 10', # K열: 연장시간
        '심야시간': 'Unnamed: 11'  # L열: 심야시간
    }

    for logic_col, actual_col in time_col_mapping.items():
        if actual_col in df.columns:
            df[logic_col + '_분'] = df[actual_col].apply(parse_work_hours)
        else:
            df[logic_col + '_분'] = 0
            logging.warning(f"Column '{actual_col}' not found in DataFrame. Initializing '{logic_col}_분' to 0.")
            
    df['시급금액'] = pd.to_numeric(df['Unnamed: 12'], errors='coerce').fillna(0)
    df['주_시작일'] = df['근무일자'].apply(get_start_of_week)

    df['주휴시간(분단위)'] = 0
    df['주휴수당'] = 0.0

    # 주간 총 근무시간을 저장할 딕셔너리
    weekly_hours_dict = {}

    for user_id, user_df in df.groupby('Unnamed: 1'):
        user_weekly_hours = []
        for week_start, week_df in user_df.groupby('주_시작일'):
            total_minutes = week_df['근무시간_분'].sum()
            total_hours = total_minutes / 60.0
            user_weekly_hours.append(total_hours)

            if total_hours >= HOLIDAY_ALLOWANCE_HOURS:
                # 고용노동부 기준: 주 단위 독립 계산 + 전체 일괄 지급
                paid_hours = (total_hours / WEEKLY_STANDARD_HOURS) * DAILY_STANDARD_HOURS
                if total_hours > WEEKLY_STANDARD_HOURS:
                    paid_hours = DAILY_STANDARD_HOURS

                # 시급 변동 시 가중평균 시급 적용 (고용노동부 권장)
                week_rates = week_df['시급금액'].dropna().unique()
                if len(week_rates) > 1:
                    # 가중평균 시급 계산: (총 근무임금 ÷ 총 근무시간)
                    total_week_pay = sum(row['근무시간_분'] / 60 * row['시급금액'] for _, row in week_df.iterrows())
                    weighted_average_rate = total_week_pay / total_hours if total_hours > 0 else week_rates[0]
                else:
                    weighted_average_rate = week_rates[0] if week_rates else 0

                # 주휴수당 전체 금액 계산
                weekly_holiday_total = paid_hours * weighted_average_rate

                # 고용노동부 기준: 개근 주에 대해 1일분 임금을 한 번에 전체 지급
                # 주의 첫 번째 날짜(월요일)에 전체 금액 지급
                first_day_idx = week_df.index[0]
                df.loc[first_day_idx, '주휴시간(분단위)'] = round(paid_hours * 60)
                df.loc[first_day_idx, '주휴수당'] = weekly_holiday_total

                # 나머지 날짜들은 0으로 설정 (전체 일괄 지급 방식)
                for idx in week_df.index[1:]:
                    df.loc[idx, '주휴시간(분단위)'] = 0
                    df.loc[idx, '주휴수당'] = 0

        # 주간 총 근무시간의 최대값을 대표값으로 저장 (설명을 위한 값)
        if user_weekly_hours:
            weekly_hours_dict[user_id] = max(user_weekly_hours)  # 가장 많은 근무시간을 한 주를 대표로 사용
        else:
            weekly_hours_dict[user_id] = 0

    # 주간 총 근무시간을 df에 추가
    df['주_총근무시간'] = df['Unnamed: 1'].map(weekly_hours_dict)

    df['기본급'] = (df['근무시간_분'] / 60) * df['시급금액']
    df['연장수당'] = (df['연장시간_분'] / 60) * df['시급금액'] * OVERTIME_MULTIPLIER
    df['night_pay'] = (df['심야시간_분'] / 60) * df['시급금액'] * OVERTIME_MULTIPLIER  # 야간수당

    df['예상급여금액'] = df['기본급'] + df['연장수당'] + df['night_pay']
    df['총급여액'] = df['예상급여금액'] + df['주휴수당']

    logging.info(f"--- Finished calculate_salary. Output df shape: {df.shape} ---")
    return df

def create_user_summaries(df, employee_data=None):
    """Creates a summary DataFrame for each user."""
    logging.info(f"--- Starting create_user_summaries. Input df shape: {df.shape} ---")
    if df.empty:
        logging.warning("Input DataFrame is empty. Returning empty summary.")
        return pd.DataFrame()

    agg_dict = {
        'Unnamed: 2': 'first',  # 성명
        '예상급여금액': 'sum',
        '주휴시간(분단위)': 'sum',
        '주휴수당': 'sum',
        '총급여액': 'sum',
        '기본급': 'sum',
        '연장수당': 'sum',
        'night_pay': 'sum',  # 야간수당 직접 사용
        '연장시간_분': 'sum',
        '심야시간_분': 'sum',
        '시급금액': 'first',
        '근무시간_분': 'sum',
        '주_총근무시간': 'first'  # 주간 총 근무시간 추가
    }

    user_summaries = df.groupby('Unnamed: 1').agg(agg_dict).reset_index()

    user_summaries.rename(columns={
        'Unnamed: 2': 'name',
        'Unnamed: 1': 'user_id',
        '기본급': 'base_pay',
        '주휴수당': 'weekly_holiday_allowance',
        '시급금액': 'hourly_rate',  # 시급 정보 추가
    }, inplace=True)

    user_summaries['overtime_pay'] = user_summaries['연장수당']  # 연장수당 명확히
    user_summaries['extra_pay'] = user_summaries['연장수당'] + user_summaries['night_pay']  # 기존 호환성 유지

    # 기본 정보 설정
    user_summaries['department'] = ''
    user_summaries['position'] = ''
    user_summaries['hire_date'] = ''
    user_summaries['payment_date'] = ''

    # 4대보험 및 세금 계산 초기화
    user_summaries['national_pension'] = 0
    user_summaries['health_insurance'] = 0
    user_summaries['employment_insurance'] = 0
    user_summaries['long_term_care_insurance'] = 0
    user_summaries['income_tax'] = 0
    user_summaries['local_income_tax'] = 0

    # 직원 데이터가 제공된 경우 세금 계산 수행
    if employee_data:
        for index, row in user_summaries.iterrows():
            user_id = str(row['user_id'])
            if user_id in employee_data:
                employee = employee_data[user_id]

                # 직원 기본 정보 복사
                user_summaries.loc[index, 'department'] = employee.get('department', '')
                user_summaries.loc[index, 'position'] = employee.get('position', '')
                user_summaries.loc[index, 'hire_date'] = employee.get('hire_date', '')

                # 4대보험 대상자 여부 확인
                insurance_eligible = employee.get('insurance_eligible', True)

                # 총급여액
                total_pay = row['총급여액']

                if insurance_eligible:
                    # 4대보험 대상자: 기존 복잡한 계산 방식 적용
                    # 국민연금 (4.5%)
                    national_pension_rate = 0.045
                    national_pension = total_pay * national_pension_rate
                    user_summaries.loc[index, 'national_pension'] = national_pension

                    # 건강보험 (3.545%)
                    health_insurance_rate = 0.03545
                    health_insurance = total_pay * health_insurance_rate
                    user_summaries.loc[index, 'health_insurance'] = health_insurance

                    # 장기요양보험 (건강보험의 12.81%)
                    long_term_care_rate = 0.1281
                    long_term_care_insurance = health_insurance * long_term_care_rate
                    user_summaries.loc[index, 'long_term_care_insurance'] = long_term_care_insurance

                    # 고용보험 (0.9%)
                    employment_insurance_rate = 0.009
                    employment_insurance = total_pay * employment_insurance_rate
                    user_summaries.loc[index, 'employment_insurance'] = employment_insurance

                    # 소득세 계산 (간이 계산)
                    # 과세표준 = 총급여액 - 4대보험 공제액
                    taxable_income = total_pay - national_pension - health_insurance - long_term_care_insurance - employment_insurance

                    # 기본 공제 150만원 적용
                    basic_deduction = 1500000
                    taxable_income = max(0, taxable_income - basic_deduction)

                    # 누진세율 적용 (2024년 기준)
                    if taxable_income <= 12000000:  # 1,200만원 이하
                        tax_rate = 0.06
                        deduction = 0
                    elif taxable_income <= 46000000:  # 4,600만원 이하
                        tax_rate = 0.15
                        deduction = 1080000
                    elif taxable_income <= 88000000:  # 8,800만원 이하
                        tax_rate = 0.24
                        deduction = 5220000
                    elif taxable_income <= 150000000:  # 1억5천만원 이하
                        tax_rate = 0.35
                        deduction = 14900000
                    elif taxable_income <= 300000000:  # 3억원 이하
                        tax_rate = 0.38
                        deduction = 19400000
                    elif taxable_income <= 500000000:  # 5억원 이하
                        tax_rate = 0.40
                        deduction = 25400000
                    else:  # 5억원 초과
                        tax_rate = 0.42
                        deduction = 35400000

                    income_tax = taxable_income * tax_rate - deduction
                    income_tax = max(0, income_tax)  # 음수 방지
                    income_tax = int(income_tax)  # 원단위 절사

                    # 지방소득세 (소득세의 10%)
                    local_income_tax = income_tax * 0.1
                    local_income_tax = int(local_income_tax)  # 원단위 절사

                    user_summaries.loc[index, 'income_tax'] = income_tax
                    user_summaries.loc[index, 'local_income_tax'] = local_income_tax

                else:
                    # 4대보험 비대상자: 간단한 세금 계산
                    # 4대보험 항목들은 모두 0원
                    user_summaries.loc[index, 'national_pension'] = 0
                    user_summaries.loc[index, 'health_insurance'] = 0
                    user_summaries.loc[index, 'employment_insurance'] = 0
                    user_summaries.loc[index, 'long_term_care_insurance'] = 0

                    # 소득세: 지급합계의 3% (원단위 절사)
                    income_tax = int(total_pay * 0.03)
                    user_summaries.loc[index, 'income_tax'] = income_tax

                    # 지방소득세: 지급합계의 0.3% (원단위 절사)
                    local_income_tax = int(total_pay * 0.003)
                    user_summaries.loc[index, 'local_income_tax'] = local_income_tax

    # 공제액 합계 및 실지급액 계산
    user_summaries['deductions'] = (
        user_summaries['national_pension'] +
        user_summaries['health_insurance'] +
        user_summaries['employment_insurance'] +
        user_summaries['long_term_care_insurance'] +
        user_summaries['income_tax'] +
        user_summaries['local_income_tax']
    )
    user_summaries['net_pay'] = user_summaries['총급여액'] - user_summaries['deductions']

    logging.info(f"--- Finished create_user_summaries. Output summary shape: {user_summaries.shape} ---")
    return user_summaries


def generate_payslips(summaries_df, template_path, output_filename, data_month, company_name="", selected_users=None, explanation_options=None):
    """Generates the final payslip Excel file from a template.

    explanation_options: dict with keys:
        - 'base_pay_explanation': bool - 기본급 산출식 표시 (D26)
        - 'holiday_explanation': bool - 주휴수당 산출식 표시 (D27)
        - 'night_explanation': bool - 야간수당 산출식 표시 (D28)
        - 'holiday_work_explanation': bool - 휴일근로수당 산출식 표시 (D29)
        - 'overtime_explanation': bool - 연장수당 산출식 표시 (D30)
    """
    logging.info(f"--- Starting generate_payslips for {len(summaries_df)} users ---")

    # 기본값 설정
    if explanation_options is None:
        explanation_options = {
            'base_pay_explanation': True,
            'holiday_explanation': True,
            'night_explanation': True,
            'holiday_work_explanation': True,
            'overtime_explanation': True
        }

    if selected_users:
        summaries_df = summaries_df[summaries_df['user_id'].isin(selected_users)]
        logging.info(f"Filtered to {len(summaries_df)} selected users")

    try:
        # Load template workbook
        template_wb = openpyxl.load_workbook(template_path, data_only=False)
        template_sheet = template_wb['명세서']
    except FileNotFoundError:
        logging.error(f"Template file not found: {template_path}")
        raise FileNotFoundError(f"오류: 템플릿 파일 '{template_path}'을(를) 찾을 수 없습니다.")
    except KeyError:
        logging.error("Sheet '명세서' not found in template.")
        raise KeyError("오류: 템플릿 파일에서 '명세서' 시트를 찾을 수 없습니다.")

    # Create result workbook by copying template
    result_wb = openpyxl.Workbook()
    # Remove default sheet
    if "Sheet" in result_wb.sheetnames:
        result_wb.remove(result_wb["Sheet"])

    # Process each user
    for index, user_summary in summaries_df.iterrows():
        # 모든 시트를 사용자 이름으로 생성 (일관성 유지)
        sheet_name = ''.join(c for c in user_summary['name'] if c.isalnum())

        # Create new worksheet by copying all cells from template
        ws = result_wb.create_sheet(title=sheet_name)

        # Copy all cells, styles, and formatting from template
        for row in template_sheet.iter_rows():
            for cell in row:
                new_cell = ws[cell.coordinate]
                new_cell.value = cell.value
                if cell.has_style:
                    new_cell.font = copy.copy(cell.font)
                    new_cell.alignment = copy.copy(cell.alignment)
                    new_cell.border = copy.copy(cell.border)
                    new_cell.fill = copy.copy(cell.fill)
                    new_cell.number_format = cell.number_format
                    new_cell.protection = copy.copy(cell.protection)

        # Copy merged cells
        for merged_range in template_sheet.merged_cells.ranges:
            ws.merge_cells(str(merged_range))

        # Copy row dimensions
        for row_idx, row_dim in template_sheet.row_dimensions.items():
            if row_dim.height is not None:
                ws.row_dimensions[row_idx].height = row_dim.height

        # Copy column dimensions
        for col_idx, col_dim in template_sheet.column_dimensions.items():
            if col_dim.width is not None:
                ws.column_dimensions[col_idx].width = col_dim.width

        logging.debug(f"Processing sheet for user: {user_summary['name']} ({sheet_name})")

        # Fill in the data
        ws['C2'] = f"{data_month} 급여명세서"
        ws['D4'] = user_summary['name']
        ws['G4'] = user_summary.get('user_id', '')
        ws['D3'] = company_name

        ws['D5'] = user_summary.get('department', '')
        ws['G5'] = user_summary.get('position', '')
        ws['D6'] = user_summary.get('hire_date', '')
        ws['G6'] = user_summary.get('payment_date', '')

        # 금액 값들을 숫자로 설정하고 포맷 적용
        ws['H26'] = float(user_summary.get('base_pay', 0))
        ws['H27'] = float(user_summary.get('weekly_holiday_allowance', 0))
        ws['H28'] = float(user_summary.get('night_pay', 0))
        ws['H29'] = 0.0
        ws['H30'] = float(user_summary.get('연장수당', 0))

        ws['H11'] = float(user_summary.get('national_pension', 0))
        ws['H12'] = float(user_summary.get('health_insurance', 0))
        ws['H13'] = float(user_summary.get('employment_insurance', 0))
        ws['H14'] = float(user_summary.get('long_term_care_insurance', 0))
        ws['H15'] = float(user_summary.get('income_tax', 0))
        ws['H16'] = float(user_summary.get('local_income_tax', 0))

        total_deduction_calculated = sum([
            float(user_summary.get('national_pension', 0)), float(user_summary.get('health_insurance', 0)),
            float(user_summary.get('employment_insurance', 0)), float(user_summary.get('long_term_care_insurance', 0)),
            float(user_summary.get('income_tax', 0)), float(user_summary.get('local_income_tax', 0))
        ])
        ws['H20'] = float(total_deduction_calculated)

        total_payment = (float(user_summary.get('base_pay', 0)) +
                        float(user_summary.get('weekly_holiday_allowance', 0)) +
                        float(user_summary.get('extra_pay', 0)))
        ws['D20'] = float(total_payment)

        net_pay = total_payment - total_deduction_calculated
        ws['D21'] = float(net_pay)

        ws['D11'] = float(user_summary.get('base_pay', 0))
        ws['D13'] = float(user_summary.get('연장수당', 0))
        ws['D14'] = float(user_summary.get('night_pay', 0))

        ws['C23'] = int(user_summary.get('연장시간_분', 0))
        ws['D23'] = int(user_summary.get('심야시간_분', 0))
        ws['E23'] = 0
        # 시급 표시 개선 (시급 변경이 있는 경우 범위 표시)
        df = pd.read_excel('tutorial_data.xlsx', sheet_name='11월', header=1)
        user_data = df[df['Unnamed: 1'] == user_summary['user_id']]

        if not user_data.empty:
            unique_rates = sorted(user_data['Unnamed: 12'].dropna().unique())
            if len(unique_rates) > 1:
                # 시급 변경이 있는 경우: 시급들을 나열
                rate_strings = [f"{int(rate):,}원" for rate in unique_rates]
                ws['G23'] = ', '.join(rate_strings)
            else:
                # 시급 일관성 유지
                ws['G23'] = float(unique_rates[0]) if unique_rates else float(user_summary.get('hourly_rate', 0))
        else:
            ws['G23'] = float(user_summary.get('hourly_rate', 0))

        # 숫자 포맷 적용 (쉼표 구분 및 소수점)
        number_format = '#,##0'
        for cell_ref in ['H26', 'H27', 'H28', 'H29', 'H30', 'H11', 'H12', 'H13', 'H14', 'H15', 'H16', 'H20', 'D20', 'D21', 'D11', 'D13', 'D14']:
            if cell_ref in ws:
                ws[cell_ref].number_format = number_format

        # 조건부 설명 표시 및 행 삭제를 위한 정보 수집
        rows_to_delete = []

        if explanation_options.get('base_pay_explanation', True):
            # 시급 변경 내역 분석 및 표시
            df = pd.read_excel('tutorial_data.xlsx', sheet_name='11월', header=1)
            user_data = df[df['Unnamed: 1'] == user_summary['user_id']]

            if not user_data.empty:
                # 시급별 근무일수와 총 근무시간 계산
                hourly_rate_groups = {}
                for idx, row in user_data.iterrows():
                    rate = row['Unnamed: 12']
                    # 근무시간을 분 단위로 변환 (HH:MM 형식 파싱)
                    work_minutes = 0
                    if pd.notna(row['Unnamed: 9']):  # Unnamed: 9 (J열: 실제 근무시간)
                        work_time_str = str(row['Unnamed: 9']).strip()
                        if ':' in work_time_str:
                            try:
                                hours, minutes = work_time_str.split(':')
                                work_minutes = int(hours) * 60 + int(minutes)
                            except (ValueError, IndexError):
                                work_minutes = 0
                        else:
                            # 숫자인 경우 그대로 사용
                            try:
                                work_minutes = float(work_time_str)
                            except (ValueError, TypeError):
                                work_minutes = 0

                    hours = work_minutes / 60.0 if work_minutes > 0 else 0
                    if pd.notna(rate) and rate > 0:
                        if rate not in hourly_rate_groups:
                            hourly_rate_groups[rate] = {'days': 0, 'hours': 0}
                        hourly_rate_groups[rate]['days'] += 1
                        hourly_rate_groups[rate]['hours'] += hours

                if len(hourly_rate_groups) > 1:
                    # 시급 변경이 있는 경우 - 총 근무시간으로 계산 표시
                    calculation_parts = []
                    total_amount = 0

                    for rate in sorted(hourly_rate_groups.keys()):
                        days = hourly_rate_groups[rate]['days']
                        total_hours = hourly_rate_groups[rate]['hours']  # 총 근무시간 사용
                        amount = rate * total_hours
                        total_amount += amount
                        calculation_parts.append(f"{days}일({int(rate):,}원 × {total_hours:.1f}시간)")

                    calculation_str = " + ".join(calculation_parts)
                    result_str = f"{calculation_str} = {total_amount:,.0f}원"
                    ws['D26'] = result_str

                    # 긴 텍스트를 위한 행 높이 동적 조정
                    ws['D26'].alignment = Alignment(wrap_text=True, vertical='top')
                    text_length = len(result_str)
                    if text_length > 60:
                        ws.row_dimensions[26].height = 75  # 매우 긴 텍스트
                    elif text_length > 40:
                        ws.row_dimensions[26].height = 60  # 긴 텍스트
                    else:
                        ws.row_dimensions[26].height = 45  # 중간 텍스트
                else:
                    # 시급 일관성 유지
                    ws['D26'] = f"(총 {user_summary.get('근무시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원"
                    ws.row_dimensions[26].height = 30  # 기본 높이
            else:
                ws['D26'] = f"(총 {user_summary.get('근무시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원"
        else:
            rows_to_delete.append(26)

        if explanation_options.get('holiday_explanation', True):
            # 주휴수당 상세 계산 과정 표시
            weekly_allowance = float(user_summary.get('weekly_holiday_allowance', 0))

            if weekly_allowance == 0:
                # 주휴수당이 발생하지 않은 경우
                weekly_hours = user_summary.get('주_총근무시간', 0)
                ws['D27'] = f"주휴수당 해당없음\n주간총근무시간: {weekly_hours:.1f}시간 (기준: {HOLIDAY_ALLOWANCE_HOURS}시간)"
            else:
                # 주휴수당이 발생한 경우 - 주별 상세 내역 표시
                df = pd.read_excel('tutorial_data.xlsx', sheet_name='11월', header=1)
                user_data = df[df['Unnamed: 1'] == user_summary['user_id']].copy()

                if not user_data.empty:
                    user_data['근무일자'] = pd.to_datetime(user_data['Unnamed: 3'], errors='coerce')
                    user_data['주_시작일'] = user_data['근무일자'].dt.to_period('W').apply(lambda r: r.start_time)

                    # 주별 근무시간 및 주휴수당 계산
                    holiday_details = []
                    total_holiday_pay = 0

                    for week_start, week_df in user_data.groupby('주_시작일'):
                        # 해당 주의 총 근무시간 계산
                        total_minutes = 0
                        for _, row in week_df.iterrows():
                            work_time_str = str(row['Unnamed: 9'])
                            if ':' in work_time_str:
                                try:
                                    h, m = work_time_str.split(':')
                                    total_minutes += int(h) * 60 + int(m)
                                except (ValueError, IndexError):
                                    pass
                        total_hours = total_minutes / 60.0

                        if total_hours >= HOLIDAY_ALLOWANCE_HOURS:
                            # 시급 계산 (해당 주의 시급들)
                            week_rates = week_df['Unnamed: 12'].dropna().unique()
                            if len(week_rates) > 1:
                                # 가중평균 시급 계산: (총 근무임금 ÷ 총 근무시간)
                                total_week_pay = 0
                                for _, row in week_df.iterrows():
                                    work_time_str = str(row['Unnamed: 9'])
                                    hourly_rate = row['Unnamed: 12']
                                    if pd.notna(hourly_rate) and work_time_str:
                                        if ':' in work_time_str:
                                            try:
                                                h, m = work_time_str.split(':')
                                                work_hours = int(h) + int(m)/60.0
                                                total_week_pay += work_hours * hourly_rate
                                            except (ValueError, IndexError):
                                                pass
                                weighted_rate = total_week_pay / total_hours if total_hours > 0 else week_rates[0]
                            else:
                                weighted_rate = week_rates[0] if week_rates else 0

                            # 주휴시간 및 금액 계산
                            paid_hours = (total_hours / WEEKLY_STANDARD_HOURS) * DAILY_STANDARD_HOURS
                            if total_hours > WEEKLY_STANDARD_HOURS:
                                paid_hours = DAILY_STANDARD_HOURS

                            holiday_pay = paid_hours * weighted_rate
                            total_holiday_pay += holiday_pay

                            # 주 표시 형식 (예: 11월 3주)
                            week_date = week_start.date()
                            month = week_date.month
                            week_info = f"{month}월 {(week_date.day - 1) // 7 + 1}주차"

                            holiday_details.append(
                                f"• {week_info}: {total_hours:.1f}시간 → {paid_hours:.1f}시간 × {weighted_rate:,.0f}원 = {holiday_pay:,.0f}원"
                            )

                    # 최종 표시 형식
                    if holiday_details:
                        details_text = "\n".join(holiday_details)
                        ws['D27'] = f"주휴수당 상세 내역:\n\n{details_text}\n\n💰 총 주휴수당: {weekly_allowance:,.0f}원\n\n(기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무 시 주휴수당 발생)"
                    else:
                        ws['D27'] = f"주휴수당 해당없음\n(기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무)"
                else:
                    ws['D27'] = f"주휴수당 해당없음\n(기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무)"

            ws['D27'].alignment = Alignment(wrap_text=True, vertical='top')
            ws.row_dimensions[27].height = 200  # 여러 줄 표시를 위해 높이 증가
        else:
            rows_to_delete.append(27)

        if explanation_options.get('night_explanation', True):
            ws['D28'] = f"(총 {user_summary.get('심야시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원 * {OVERTIME_MULTIPLIER}배"
        else:
            rows_to_delete.append(28)

        if explanation_options.get('holiday_work_explanation', True):
            ws['D29'] = "해당없음 (0)"
        else:
            rows_to_delete.append(29)

        if explanation_options.get('overtime_explanation', True):
            ws['D30'] = f"(총 {user_summary.get('연장시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원 * {OVERTIME_MULTIPLIER}배"
        else:
            rows_to_delete.append(30)

        # 삭제할 행들을 뒤에서부터 앞으로 삭제 (행 번호 변경 방지)
        for row_num in sorted(rows_to_delete, reverse=True):
            ws.delete_rows(row_num)

    try:
        result_wb.save(output_filename)
        logging.info(f"Successfully generated payslips at '{output_filename}'")
    except Exception as e:
        logging.error(f"Error saving file: {e}", exc_info=True)
        raise Exception(f"파일 저장 중 오류가 발생했습니다: {e}")



def generate_payslips_html(summaries_df, output_filename, data_month, company_name="", selected_users=None, explanation_options=None):
    """Generates HTML payslip files using the external template file."""
    logging.info(f"--- Starting generate_payslips_html for {len(summaries_df)} users ---")

    if selected_users:
        summaries_df = summaries_df[summaries_df['user_id'].isin(selected_users)]
        logging.info(f"Filtered to {len(summaries_df)} selected users")

    # Load HTML template
    template_path = os.path.join(os.path.dirname(__file__), 'payslip_template.html')
    logging.debug(f"Looking for template at: {template_path}")

    if not os.path.exists(template_path):
        logging.error(f"Template file does not exist: {template_path}")
        raise FileNotFoundError(f"HTML 템플릿 파일을 찾을 수 없습니다: {template_path}")

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        logging.error(f"Error reading template: {e}")
        raise Exception(f"HTML 템플릿 파일을 읽을 수 없습니다: {e}")

    template = Template(template_content)

    if selected_users is None:
        # Single file for all users - create HTML with multiple payslips
        # 파일 경로 검증 및 보정
        if os.path.isdir(output_filename):
            # 디렉토리인 경우 기본 파일명 추가
            safe_data_month = data_month.replace(' ', '_').replace('년', 'year').replace('월', 'month')
            output_filename = os.path.join(output_filename, f"{safe_data_month}_급여명세서_모음.html")

        # 확장자 확인 및 추가
        if not output_filename.lower().endswith('.html'):
            output_filename += '.html'

        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{data_month} 급여명세서 모음</title>
</head>
<body>
    <div class="container">
"""

        for index, user_summary in summaries_df.iterrows():
            if index > 0:
                html_content += '<div class="page-break"></div>'

            payslip_data = _prepare_payslip_data(user_summary, data_month, company_name, explanation_options)
            html_content += template.render(**payslip_data)

        html_content += """
    </div>
</body>
</html>"""

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"Generated HTML file: {output_filename}")
        except Exception as e:
            logging.error(f"Error writing HTML file: {e}")
            raise Exception(f"HTML 파일 생성 실패: {e}")
    else:
        # Individual files for each user
        output_dir = os.path.dirname(output_filename)
        base_name = os.path.splitext(os.path.basename(output_filename))[0]

        for index, user_summary in summaries_df.iterrows():
            user_name = user_summary['name']
            safe_name = ''.join(c for c in user_name if c.isalnum() or c in ' _-')
            individual_filename = os.path.join(output_dir, f"{safe_name}_{base_name}.html")

            payslip_data = _prepare_payslip_data(user_summary, data_month, company_name, explanation_options)

            html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{data_month} 급여명세서 - {user_name}</title>
</head>
<body>
"""

            html_content += template.render(**payslip_data)
            html_content += """
</body>
</html>"""

            try:
                with open(individual_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logging.info(f"Generated HTML for {user_name}: {individual_filename}")
            except Exception as e:
                logging.error(f"Error writing HTML file for {user_name}: {e}")
                raise Exception(f"HTML 파일 생성 실패 ({user_name}): {e}")

    logging.info(f"--- Finished generate_payslips_html ---")

def _generate_single_payslip_html(payslip_data):
    """Generate HTML content for a single payslip."""
    return f"""
    <div class="payslip">
        <div class="header">
            <h1>{payslip_data['data_month']} 급여명세서</h1>
        </div>

        <table class="info-table">
            <tr>
                <td class="empty"></td>
                <td class="label">회사명</td>
                <td colspan="4">{payslip_data['company_name']}</td>
            </tr>
            <tr>
                <td class="empty"></td>
                <td class="label">성  명</td>
                <td colspan="2">{payslip_data['name']}</td>
                <td class="label">사  번</td>
                <td colspan="2">{payslip_data['user_id']}</td>
            </tr>
            <tr>
                <td class="empty"></td>
                <td class="label">부  서</td>
                <td colspan="2">{payslip_data['department']}</td>
                <td class="label">직  급</td>
                <td colspan="2">{payslip_data['position']}</td>
            </tr>
            <tr>
                <td class="empty"></td>
                <td class="label">입사일</td>
                <td colspan="2">{payslip_data['hire_date']}</td>
                <td class="label">지급일</td>
                <td colspan="2">{payslip_data['payment_date']}</td>
            </tr>
        </table>

        <table class="salary-table">
            <thead>
                <tr>
                    <th style="width: 20%;">지급항목</th>
                    <th style="width: 15%;">금액</th>
                    <th style="width: 20%;">공제항목</th>
                    <th style="width: 15%;">금액</th>
                    <th style="width: 30%;">비고</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>기본급</td>
                    <td class="amount">{payslip_data['base_pay']:,.0f}원</td>
                    <td>국민연금</td>
                    <td class="amount">{payslip_data['national_pension']:,.0f}원</td>
                    <td rowspan="6">{payslip_data['calculation_note_1']}</td>
                </tr>
                <tr>
                    <td>주휴수당</td>
                    <td class="amount">{payslip_data['weekly_holiday_allowance']:,.0f}원</td>
                    <td>건강보험</td>
                    <td class="amount">{payslip_data['health_insurance']:,.0f}원</td>
                </tr>
                <tr>
                    <td>연장수당</td>
                    <td class="amount">{payslip_data['extra_pay']:,.0f}원</td>
                    <td>고용보험</td>
                    <td class="amount">{payslip_data['employment_insurance']:,.0f}원</td>
                </tr>
                <tr>
                    <td>야간수당</td>
                    <td class="amount">{payslip_data['night_pay']:,.0f}원</td>
                    <td>장기요양보험</td>
                    <td class="amount">{payslip_data['long_term_care_insurance']:,.0f}원</td>
                </tr>
                <tr>
                    <td></td>
                    <td></td>
                    <td>소득세</td>
                    <td class="amount">{payslip_data['income_tax']:,.0f}원</td>
                </tr>
                <tr>
                    <td></td>
                    <td></td>
                    <td>지방소득세</td>
                    <td class="amount">{payslip_data['local_income_tax']:,.0f}원</td>
                </tr>
                <tr class="total-row">
                    <td>합계</td>
                    <td class="amount">{payslip_data['total_payment']:,.0f}원</td>
                    <td>합계</td>
                    <td class="amount">{payslip_data['total_deduction']:,.0f}원</td>
                    <td></td>
                </tr>
                <tr class="net-pay-row">
                    <td colspan="2" style="text-align: center;">실지급액</td>
                    <td class="amount" colspan="2">{payslip_data['net_pay']:,.0f}원</td>
                    <td></td>
                </tr>
            </tbody>
        </table>

        <div class="calculation-notes">
            <p><strong>기본급 산출식:</strong> {payslip_data['calculation_note_1']}</p>
            <p><strong>주휴수당 산출식:</strong> {payslip_data['calculation_note_2']}</p>
            <p><strong>연장수당 산출식:</strong> {payslip_data['calculation_note_3']}</p>
            <p><strong>시급:</strong> {payslip_data['hourly_rate']:,.0f}원</p>
        </div>
    </div>
"""

def _prepare_payslip_data(user_summary, data_month, company_name, explanation_options=None):
    """Prepares data for HTML template rendering."""
    # 기본값 설정
    if explanation_options is None:
        explanation_options = {
            'base_pay_explanation': True,
            'holiday_explanation': True,
            'night_explanation': True,
            'holiday_work_explanation': True,
            'overtime_explanation': True
        }

    # Calculate totals
    total_payment = (user_summary.get('base_pay', 0) +
                    user_summary.get('weekly_holiday_allowance', 0) +
                    user_summary.get('연장수당', 0) +
                    user_summary.get('night_pay', 0))
    total_deduction = sum([
        user_summary.get('national_pension', 0),
        user_summary.get('health_insurance', 0),
        user_summary.get('employment_insurance', 0),
        user_summary.get('long_term_care_insurance', 0),
        user_summary.get('income_tax', 0),
        user_summary.get('local_income_tax', 0)
    ])
    net_pay = total_payment - total_deduction

    # 주휴수당 상세 계산 과정 생성 (Excel 버전과 동일한 로직)
    weekly_allowance = float(user_summary.get('weekly_holiday_allowance', 0))

    if weekly_allowance == 0:
        holiday_calculation_note = f"주휴수당 해당없음 (기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무)"
    else:
        # 주별 상세 내역 계산 (Excel 버전과 동일한 로직)
        df = pd.read_excel('tutorial_data.xlsx', sheet_name='11월', header=1)
        user_data = df[df['Unnamed: 1'] == user_summary['user_id']].copy()

        if not user_data.empty:
            user_data['근무일자'] = pd.to_datetime(user_data['Unnamed: 3'], errors='coerce')
            user_data['주_시작일'] = user_data['근무일자'].dt.to_period('W').apply(lambda r: r.start_time)

            holiday_details = []

            for week_start, week_df in user_data.groupby('주_시작일'):
                total_minutes = 0
                for _, row in week_df.iterrows():
                    work_time_str = str(row['Unnamed: 9'])
                    if ':' in work_time_str:
                        try:
                            h, m = work_time_str.split(':')
                            total_minutes += int(h) * 60 + int(m)
                        except (ValueError, IndexError):
                            pass
                total_hours = total_minutes / 60.0

                if total_hours >= HOLIDAY_ALLOWANCE_HOURS:
                    week_rates = week_df['Unnamed: 12'].dropna().unique()
                    if len(week_rates) > 1:
                        total_week_pay = 0
                        for _, row in week_df.iterrows():
                            work_time_str = str(row['Unnamed: 9'])
                            hourly_rate = row['Unnamed: 12']
                            if pd.notna(hourly_rate) and work_time_str:
                                if ':' in work_time_str:
                                    try:
                                        h, m = work_time_str.split(':')
                                        work_hours = int(h) + int(m)/60.0
                                        total_week_pay += work_hours * hourly_rate
                                    except (ValueError, IndexError):
                                        pass
                        weighted_rate = total_week_pay / total_hours if total_hours > 0 else week_rates[0]
                    else:
                        weighted_rate = week_rates[0] if week_rates else 0

                    paid_hours = (total_hours / WEEKLY_STANDARD_HOURS) * DAILY_STANDARD_HOURS
                    if total_hours > WEEKLY_STANDARD_HOURS:
                        paid_hours = DAILY_STANDARD_HOURS

                    holiday_pay = paid_hours * weighted_rate

                    week_date = week_start.date()
                    month = week_date.month
                    week_info = f"{month}월 {(week_date.day - 1) // 7 + 1}주차"

                    holiday_details.append(
                        f"• {week_info}: {total_hours:.1f}시간 → {paid_hours:.1f}시간 × {weighted_rate:,.0f}원 = {holiday_pay:,.0f}원"
                    )

            if holiday_details:
                details_html = "<br>".join(holiday_details)
                holiday_calculation_note = f"주휴수당 상세 내역:<br><br>{details_html}<br><br>💰 총 주휴수당: {weekly_allowance:,.0f}원<br><br>(기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무 시 주휴수당 발생)"
            else:
                holiday_calculation_note = f"주휴수당 해당없음 (기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무)"
        else:
            holiday_calculation_note = f"주휴수당 해당없음 (기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무)"

    return {
        'data_month': data_month,
        'company_name': company_name,
        'name': user_summary['name'],
        'user_id': str(user_summary.get('user_id', '')),
        'department': user_summary.get('department', ''),
        'position': user_summary.get('position', ''),
        'hire_date': user_summary.get('hire_date', ''),
        'payment_date': user_summary.get('payment_date', ''),
        'base_pay': user_summary.get('base_pay', 0),
        'weekly_holiday_allowance': user_summary.get('weekly_holiday_allowance', 0),
        'extra_pay': user_summary.get('연장수당', 0),
        'night_pay': user_summary.get('night_pay', 0),
        'national_pension': user_summary.get('national_pension', 0),
        'health_insurance': user_summary.get('health_insurance', 0),
        'employment_insurance': user_summary.get('employment_insurance', 0),
        'long_term_care_insurance': user_summary.get('long_term_care_insurance', 0),
        'income_tax': user_summary.get('income_tax', 0),
        'local_income_tax': user_summary.get('local_income_tax', 0),
        'total_payment': total_payment,
        'total_deduction': total_deduction,
        'net_pay': net_pay,
        'hourly_rate': user_summary.get('hourly_rate', 0),
        'calculation_note_1': f"(총 {user_summary.get('근무시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원",
        'calculation_note_2': holiday_calculation_note,  # 개선된 주휴수당 산출식
        'calculation_note_3': f"(총 {user_summary.get('연장시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원 * {OVERTIME_MULTIPLIER}배",
        # HTML 템플릿 조건부 렌더링 옵션들
        'show_base_pay_note': explanation_options.get('base_pay_explanation', True),
        'show_holiday_note': explanation_options.get('holiday_explanation', True),
        'show_overtime_note': explanation_options.get('overtime_explanation', True),
        'show_hourly_rate': True,  # 시급은 항상 표시 (필요시 옵션으로 변경 가능)
    }



def validate_month_input(month_str):
    """
    월 입력 검증 및 정규화 함수
    다양한 입력 형식을 지원: YYYY-MM, MM, YYYY/MM 등
    """
    if not month_str or not month_str.strip():
        raise ValueError("월을 입력해주세요")

    month_str = month_str.strip()

    # YYYY-MM 형식 (기본)
    if '-' in month_str:
        parts = month_str.split('-')
        if len(parts) == 2:
            year_str, month_str_part = parts
            try:
                year = int(year_str)
                month = int(month_str_part)
                if not (1 <= month <= 12):
                    raise ValueError
                if not (2000 <= year <= 2100):
                    raise ValueError
                return year, month
            except (ValueError, TypeError):
                pass

    # YYYY/MM 형식
    if '/' in month_str:
        parts = month_str.split('/')
        if len(parts) == 2:
            year_str, month_str_part = parts
            try:
                year = int(year_str)
                month = int(month_str_part)
                if not (1 <= month <= 12):
                    raise ValueError
                if not (2000 <= year <= 2100):
                    raise ValueError
                return year, month
            except (ValueError, TypeError):
                pass

    # MM 형식만 입력된 경우 (현재 연도 가정)
    if month_str.isdigit():
        month = int(month_str)
        if 1 <= month <= 12:
            current_year = datetime.now().year
            return current_year, month

    # 기타 형식 시도
    try:
        # YYYYMM 형식
        if len(month_str) == 6 and month_str.isdigit():
            year = int(month_str[:4])
            month = int(month_str[4:])
            if 1 <= month <= 12 and 2000 <= year <= 2100:
                return year, month
    except (ValueError, IndexError):
        pass

    raise ValueError(f"올바르지 않은 월 형식입니다: '{month_str}'\n지원 형식: YYYY-MM, MM, YYYYMM")


def process_payroll_for_gui(file_path, year_month_str, employee_data=None):
    """
    Orchestrates the payroll processing for the GUI.
    Loads data, calculates salary, creates summaries, and returns them.
    """
    logging.info(f"--- Starting process_payroll_for_gui ---")
    logging.debug(f"Input year_month_str: '{year_month_str}'")

    # Validate and parse year-month format
    try:
        year, month = validate_month_input(year_month_str)
        target_month = month
        data_month_for_title = f"{year}년 {month}월"

        logging.debug(f"Parsed year: {year}, month: {month}, target_month: {target_month}")

    except ValueError as e:
        logging.error(f"Invalid year-month format: '{year_month_str}' - {e}")
        raise ValueError(str(e))

    df = load_and_preprocess_data(file_path, target_month=target_month)

    if df is None or df.empty:
        raise ValueError("데이터 로딩에 실패했거나 처리할 데이터가 없습니다.")

    df_calculated = calculate_salary(df)
    summaries = create_user_summaries(df_calculated, employee_data)

    logging.info(f"--- Finished process_payroll_for_gui successfully ---")
    return summaries, data_month_for_title
