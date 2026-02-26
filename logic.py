import copy
import pandas as pd
import openpyxl
import json
from datetime import datetime, timedelta
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import logging
import os
import shutil
from openpyxl.styles import Font, Alignment, Border, Side

from jinja2 import Template

# 세법 기준 관리 시스템
from tax_law_manager import TaxLawManager

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
def round_down_to_10_won(amount):
    """10원 단위로 절사 (10원 이하 절사)"""
    return int(amount / 10) * 10

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

def load_and_preprocess_data(file_path, target_month=None, target_year=None):
    """
    Excel 파일에서 데이터를 로드하고 전처리합니다.
    target_year와 target_month가 주어지면 해당 월과 전월의 데이터를 함께 로드합니다.
    (주휴수당의 월 경계 누락 방지 목적)
    """
    logging.info(f"--- Starting load_and_preprocess_data for file: {file_path}, period: {target_year}-{target_month} ---")
    try:
        xls = pd.ExcelFile(file_path)
        all_dfs = []
        
        # 처리할 대상 월 리스트 생성 (당월 + 전월)
        target_periods = []
        if target_year and target_month:
            # 당월
            target_periods.append((target_year, target_month))
            # 전월 계산
            if target_month == 1:
                prev_year, prev_month = target_year - 1, 12
            else:
                prev_year, prev_month = target_year, target_month - 1
            target_periods.append((prev_year, prev_month))
        
        logging.info(f"Target periods to search: {target_periods}")

        # 시트 이름 패턴: "2025년11월", "2025년 11월", "11월", "2025-11" 등 대응
        for sheet_name in xls.sheet_names:
            matched = False
            
            # 각 대상 기간(당월, 전월)에 대해 시트 이름 매칭 시도
            for y, m in target_periods:
                # 패턴 1: "2025년 11월" 또는 "2025년11월"
                if f"{y}년" in sheet_name and f"{m}월" in sheet_name:
                    matched = True
                # 패턴 2: 연도 정보 없이 "11월"만 있는 경우 (전월은 찾기 힘들 수 있으므로 주의)
                elif sheet_name == f"{m}월":
                    # 연도 정보가 없는 시트는 현재 연도라고 가정하거나, 그냥 매칭
                    matched = True
                # 패턴 3: "2025-11"
                elif f"{y}-{str(m).zfill(2)}" in sheet_name:
                    matched = True
                
                if matched:
                    logging.info(f"Matched sheet '{sheet_name}' for period {y}-{m}")
                    df = xls.parse(sheet_name, header=HEADER_ROW_COUNT - 1)
                    # 시트로부터 연/월 정보 주입 (나중에 필터링 시 활용)
                    df['_sheet_year'] = y
                    df['_sheet_month'] = m
                    all_dfs.append(df)
                    break # 한 시트가 여러 기간에 매칭될 리는 없으나 안전하게

        if not all_dfs:
            if target_year and target_month:
                error_msg = f"'{file_path}'에서 '{target_year}년 {target_month}월' 시트를 찾을 수 없습니다."
            else:
                error_msg = f"'{file_path}'에서 처리할 시트를 찾을 수 없습니다."
            logging.error(error_msg)
            raise ValueError(error_msg)

        final_df = pd.concat(all_dfs, ignore_index=True)
        # 파일 경로 저장 (필요 시)
        final_df._file_path = file_path
        
        logging.info(f"Data loaded successfully. Total rows: {len(final_df)}")
        return final_df
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"오류: 파일 '{file_path}'을(를) 찾을 수 없습니다.")
    except Exception as e:
        logging.error(f"Error reading file: {e}", exc_info=True)
        raise Exception(f"파일을 읽는 중 문제가 발생했습니다: {e}")


def calculate_salary(df, employee_data=None, target_year_month=None):
    """
    Calculates salaries, allowances, and deductions.
    ... (중략) ...
    """
    logging.info(f"--- Starting calculate_salary for {target_year_month}. Input df shape: {df.shape} ---")
    
    df['근무일자'] = pd.to_datetime(df['Unnamed: 3'], errors='coerce')
    df.dropna(subset=['근무일자', 'Unnamed: 1'], inplace=True)
    
    time_col_mapping = {
        '근무시간': 'Unnamed: 9',
        '연장시간': 'Unnamed: 10',
        '심야시간': 'Unnamed: 11'
    }

    # 설정 로드 (기본값 및 회사 정보)
    global_business_size = 'over_5'
    companies_info = {}
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                global_business_size = config_data.get('business_size', 'over_5')
                companies_info = config_data.get('companies', {})
                logging.info(f"Loaded config: global_size={global_business_size}, companies_count={len(companies_info)}")
    except Exception as e:
        logging.warning(f"Failed to load global config: {e}")

    def get_business_size(u_id):
        """사용자별 사업장 규모 결정 (회사 기준 우선)"""
        b_size = global_business_size
        if employee_data and str(u_id) in employee_data:
            emp = employee_data[str(u_id)]
            # 회사 정보가 없으면 기본 회사(company_001)로 간주 (시스템 설계 의도)
            c_id = emp.get('company_id', 'company_001')
            if c_id in companies_info:
                b_size = companies_info[c_id].get('business_size', global_business_size)
        return b_size

    for logic_col, actual_col in time_col_mapping.items():
        if actual_col in df.columns:
            df[logic_col + '_분'] = df[actual_col].apply(parse_work_hours)
        else:
            df[logic_col + '_분'] = 0
            
    df['시급금액'] = pd.to_numeric(df['Unnamed: 12'], errors='coerce').fillna(0)
    df['주_시작일'] = df['근무일자'].apply(get_start_of_week)

    # 주휴수당 관련 컬럼 초기화
    df['주휴시간(분단위)'] = 0
    df['주휴수당'] = 0.0
    df['주휴지급일'] = pd.NaT  # KeyError 방지를 위해 초기화

    # P열(휴일근무) 처리 - 관리자가 추가하는 컬럼
    # P열이 있고 값이 있으면 휴일근무, 없거나 P열이 없으면 일반근무
    p_column = None
    for col in df.columns:
        if col == 'Unnamed: 15' or '휴일' in str(col):
            p_column = col
            break
    
    if p_column and p_column in df.columns:
        # 값이 있는지 확인 (어떤 값이든 비어있지 않으면 휴일근무)
        df['is_holiday_work'] = (
            df[p_column].notna() & 
            (df[p_column].astype(str).str.strip() != '')
        )
        logging.info(f"P열(휴일근무) 발견: {p_column}, 휴일근무 행 수: {df['is_holiday_work'].sum()}")
    else:
        # P열이 없으면 모두 일반근무
        df['is_holiday_work'] = False
        logging.info("P열(휴일근무) 없음: 모든 행을 일반근무로 처리")

    # 휴일근무 관련 컬럼 초기화
    df['휴일근무시간(분)'] = 0
    df['휴일수당'] = 0.0

    # 주간 총 근무시간을 저장할 딕셔너리
    weekly_hours_dict = {}
    
    # 주별 주휴수당 상세 정보를 저장할 딕셔너리 (사용자별)
    weekly_holiday_details_dict = {}
    
    # 주별 정보를 DataFrame에 저장할 컬럼 초기화
    df['주별_주휴_정보'] = None

    for user_id, user_df in df.groupby('Unnamed: 1'):
        user_id_str = str(user_id)
        # 퇴사일 정보 확인
        resignation_date = None
        if employee_data and user_id_str in employee_data:
            res_date_str = employee_data[user_id_str].get('resignation_date')
            if res_date_str:
                try:
                    resignation_date = pd.to_datetime(res_date_str)
                except:
                    logging.warning(f"Invalid resignation date format for user {user_id}: {res_date_str}")

        user_weekly_hours = []
        user_weekly_holiday_details = []  # 주별 상세 정보 저장
        
        for week_start, week_df in user_df.groupby('주_시작일'):
            total_minutes = week_df['근무시간_분'].sum()
            total_hours = total_minutes / 60.0
            user_weekly_hours.append(total_hours)

            # 주휴수당 발생 요건 확인 (15시간 이상)
            if total_hours >= HOLIDAY_ALLOWANCE_HOURS:
                # [퇴사자 체크] 해당 주의 일요일(주휴일)까지 근로관계가 유지되는지 확인
                # 주 시작일이 월요일이므로 일요일은 +6일
                sunday_of_week = week_start + timedelta(days=6)
                
                # 퇴사일이 일요일보다 이전이면 주휴수당 미지급 (근로관계 비존속)
                is_skipped = False
                skip_reason = None
                if resignation_date and resignation_date < sunday_of_week:
                    is_skipped = True
                    skip_reason = f"퇴사일({resignation_date.strftime('%Y-%m-%d')})이 주휴일({sunday_of_week.strftime('%Y-%m-%d')})보다 이전"
                    logging.info(f"User {user_id} resigned on {resignation_date}. Holiday allowance skipped for week starting {week_start} (Sunday: {sunday_of_week})")

                paid_hours = min((total_hours / WEEKLY_STANDARD_HOURS) * DAILY_STANDARD_HOURS, DAILY_STANDARD_HOURS)

                # 고용노동부 규칙: 해당 근로자의 시간급 임금 사용 (가중평균 사용 금지)
                # 주휴수당 = 1일 소정근로시간 × 시간급 임금
                week_rates = week_df['시급금액'].dropna().unique()
                if len(week_rates) > 0:
                    # 해당 주의 마지막 근무일 시급 사용 (최신 시급)
                    hourly_rate = week_df['시급금액'].iloc[-1]
                else:
                    hourly_rate = 0

                weekly_holiday_total = paid_hours * hourly_rate if not is_skipped else 0

                # 주별 상세 정보 저장
                user_weekly_holiday_details.append({
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'week_end': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
                    'holiday_date': sunday_of_week.strftime('%Y-%m-%d'),
                    'work_hours': round(total_hours, 1),
                    'holiday_hours': round(paid_hours, 1) if not is_skipped else 0,
                    'hourly_rate': int(hourly_rate),
                    'amount': int(weekly_holiday_total),
                    'is_skipped': is_skipped,
                    'skip_reason': skip_reason
                })

                # [일요일 귀속 원칙] 주휴수당의 날짜를 해당 주의 일요일로 설정
                first_day_idx = week_df.index[0]
                df.loc[first_day_idx, '주휴시간(분단위)'] = round(paid_hours * 60) if not is_skipped else 0
                df.loc[first_day_idx, '주휴수당'] = weekly_holiday_total
                df.loc[first_day_idx, '주휴지급일'] = sunday_of_week # 귀속 기준일 설정
            else:
                # 15시간 미만인 경우 - 주별 정볼도 저장 (미발생 사유)
                sunday_of_week = week_start + timedelta(days=6)
                user_weekly_holiday_details.append({
                    'week_start': week_start.strftime('%Y-%m-%d'),
                    'week_end': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
                    'holiday_date': sunday_of_week.strftime('%Y-%m-%d'),
                    'work_hours': round(total_hours, 1),
                    'holiday_hours': 0,
                    'hourly_rate': 0,
                    'amount': 0,
                    'is_skipped': True,
                    'skip_reason': f'주 {HOLIDAY_ALLOWANCE_HOURS}시간 미만 근무 ({round(total_hours, 1)}시간)'
                })
                for idx in week_df.index:
                    df.loc[idx, '주휴수당'] = 0

        if user_weekly_hours:
            weekly_hours_dict[user_id] = max(user_weekly_hours)
        
        # 사용자별 주별 상세 정보 저장
        if user_weekly_holiday_details:
            weekly_holiday_details_dict[user_id_str] = user_weekly_holiday_details
    
    # 지급 필터링 로직: target_year_month에 해당하는 항목만 합산
    # 기본급, 연장, 야간은 '근무일자' 기준
    # 주휴수당은 '주휴지급일' 기준
    
    def is_in_target_month(date, target_ym):
        if pd.isna(date) or target_ym is None: return True # 필터링 인자 없으면 통과
        return date.strftime('%Y-%m') == target_ym

    # 각 항목별로 당월 귀속 여부에 따라 금액 조정 (Summary 생성 전단계)
    # 실제 Summary 단계에서 필터링하기 위해 '당월_귀속' 플래그 추가
    df['당월_귀속_일반'] = df['근무일자'].apply(lambda x: is_in_target_month(x, target_year_month))
    df['당월_귀속_주휴'] = df['주휴지급일'].apply(lambda x: is_in_target_month(x, target_year_month))
    
    # 휴일근무 계산 (사용자별, 월별) - 당월_귀속_일반 생성 후에 실행
    for user_id in df['Unnamed: 1'].unique():
        user_mask = df['Unnamed: 1'] == user_id
        holiday_mask = user_mask & df['is_holiday_work'] & df['당월_귀속_일반']
        holiday_rows = df[holiday_mask]
        
        if len(holiday_rows) > 0:
            # 휴일근무 시간 합산
            total_holiday_minutes = holiday_rows['근무시간_분'].sum()
            total_holiday_hours = total_holiday_minutes / 60.0
            
            # 사용자별 사업장 규모 결정
            business_size = get_business_size(user_id)
            
            # 휴일근무 8시간 기준 분기 계산
            if business_size == 'under_5':
                # 5인 미만: 가산 없음 (1.0배)
                df.loc[holiday_mask, '휴일근무시간(분)'] = df.loc[holiday_mask, '근무시간_분']
                df.loc[holiday_mask, '휴일수당'] = (df.loc[holiday_mask, '근무시간_분'] / 60) * df.loc[holiday_mask, '시급금액']
            else:
                # 5인 이상: 8시간 이내 1.5배, 초과 2.0배
                if total_holiday_hours <= 8:
                    # 전체 1.5배
                    df.loc[holiday_mask, '휴일근무시간(분)'] = df.loc[holiday_mask, '근무시간_분']
                    df.loc[holiday_mask, '휴일수당'] = (df.loc[holiday_mask, '근무시간_분'] / 60) * df.loc[holiday_mask, '시급금액'] * 1.5
                else:
                    # 8시간까지 1.5배, 초과분 2.0배
                    # 각 행에 비율 분배
                    remaining_hours = 8.0
                    for idx in holiday_rows.index:
                        row_hours = df.loc[idx, '근무시간_분'] / 60
                        
                        if remaining_hours > 0:
                            # 8시간 이내 분
                            under_8_hours = min(row_hours, remaining_hours)
                            over_8_hours = row_hours - under_8_hours
                            
                            # 1.5배 적용
                            df.loc[idx, '휴일근무시간(분)'] = df.loc[idx, '근무시간_분']
                            df.loc[idx, '휴일수당'] = (under_8_hours * df.loc[idx, '시급금액'] * 1.5) + (over_8_hours * df.loc[idx, '시급금액'] * 2.0)
                            
                            remaining_hours -= under_8_hours
                        else:
                            # 8시간 초과분 (2.0배)
                            df.loc[idx, '휴일근무시간(분)'] = df.loc[idx, '근무시간_분']
                            df.loc[idx, '휴일수당'] = (df.loc[idx, '근무시간_분'] / 60) * df.loc[idx, '시급금액'] * 2.0
            
            logging.info(f"User {user_id}: 휴일근무 {total_holiday_hours:.1f}시간, 휴일수당 {df.loc[holiday_mask, '휴일수당'].sum():,.0f}원")

    # 당월 귀속이 아닌 금액은 계산용 복사본에서 0으로 처리 (최종 합산 시 누락 방지)
    df['기본급'] = 0.0
    for user_id in df['Unnamed: 1'].unique():
        user_mask = df['Unnamed: 1'] == user_id
        # 기본급 등은 당월 귀속일 때만 계산
        current_month_mask = user_mask & df['당월_귀속_일반']
        
        # 사용자별 사업장 규모 결정
        business_size = get_business_size(user_id)

        if business_size == 'under_5':
            df.loc[current_month_mask, '기본급'] = ((df.loc[current_month_mask, '근무시간_분'] + df.loc[current_month_mask, '연장시간_분']) / 60) * df.loc[current_month_mask, '시급금액']
            df.loc[current_month_mask, '연장수당'] = 0.0
        else:
            df.loc[current_month_mask, '기본급'] = (df.loc[current_month_mask, '근무시간_분'].clip(upper=DAILY_STANDARD_HOURS * 60) / 60) * df.loc[current_month_mask, '시급금액']
            df.loc[current_month_mask, '연장수당'] = (df.loc[current_month_mask, '연장시간_분'] / 60) * df.loc[current_month_mask, '시급금액'] * OVERTIME_MULTIPLIER

        # 야간수당 필터링
        df.loc[user_mask, 'night_pay'] = 0.0
        df.loc[current_month_mask, 'night_pay'] = (df.loc[current_month_mask, '심야시간_분'] / 60) * df.loc[current_month_mask, '시급금액'] * OVERTIME_MULTIPLIER

    # 주휴수당 필터링: 당월 귀속 주휴만 남김
    df.loc[~df['당월_귀속_주휴'], '주휴수당'] = 0.0
    df.loc[~df['당월_귀속_주휴'], '주휴시간(분단위)'] = 0

    # ... 이하 수당합계 등 기존 로직 유지 ...
    df['수당합계'] = 0.0
    for user_id in df['Unnamed: 1'].unique():
        user_mask = df['Unnamed: 1'] == user_id
        if employee_data and str(user_id) in employee_data:
            employee = employee_data[str(user_id)]
            allowances = employee.get('allowances', {})
            recurring_total = sum(a.get('amount', 0) for a in allowances.get('recurring', []))
            one_time_total = sum(a.get('amount', 0) for a in allowances.get('one_time', []) if a.get('date', '').startswith(target_year_month or ""))
            df.loc[user_mask, '수당합계'] = (recurring_total + one_time_total)

    df['예상급여금액'] = df['기본급'].fillna(0) + df['연장수당'].fillna(0) + df['night_pay'].fillna(0) + df['수당합계'].fillna(0)
    df['총급여액'] = df['예상급여금액'] + df['주휴수당'].fillna(0) + df['휴일수당'].fillna(0)
    df['주_총근무시간'] = df['Unnamed: 1'].map(weekly_hours_dict)
    
    # 주별 주휴수당 상세 정보를 DataFrame에 저장 (create_user_summaries에서 사용)
    for user_id_str, weekly_details in weekly_holiday_details_dict.items():
        user_mask = df['Unnamed: 1'].astype(str) == user_id_str
        if user_mask.any():
            # 해당 사용자의 첫 번째 행에 주별 정보 저장
            first_idx = df[user_mask].index[0]
            df.loc[first_idx, '주별_주휴_정보'] = json.dumps(weekly_details, ensure_ascii=False)
    
    # 주별_주휴_정보 컬럼을 모든 행에 채우기 (groupby agg에서 사용하기 위해)
    df['주별_주휴_정보'] = df.groupby('Unnamed: 1')['주별_주휴_정보'].transform('first')

    logging.info(f"--- Finished calculate_salary. Output df rows (target month): {len(df[df['당월_귀속_일반'] | df['당월_귀속_주휴']])} ---")
    return df

def create_user_summaries(df, employee_data=None, tax_year=None):
    """Creates a summary DataFrame for each user."""
    logging.info(f"--- Starting create_user_summaries. Input df shape: {df.shape}, tax_year: {tax_year} ---")
    if df.empty:
        logging.warning("Input DataFrame is empty. Returning empty summary.")
        return pd.DataFrame()

    # 세법 기준 관리 시스템에서 해당 연도의 세법 기준 및 사업장 규모 로드
    tax_manager = TaxLawManager()
    business_size = 'under_5' # 기본값
    if os.path.exists(tax_manager.config_file):
        try:
            with open(tax_manager.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                business_size = config_data.get('business_size', 'under_5')
        except:
            pass

    if tax_year:
        tax_standards = tax_manager.get_standards_for_year(str(tax_year))
    else:
        # 연도가 지정되지 않은 경우 현재 연도 사용
        current_year = datetime.now().year
        tax_standards = tax_manager.get_standards_for_year(str(current_year))
        logging.info(f"Tax year not specified, using current year {current_year}")

    logging.info(f"Using tax standards for year {tax_year or current_year}: {tax_standards.get('name', 'Unknown')}")

    agg_dict = {
        'Unnamed: 2': 'first',  # 성명
        '예상급여금액': 'sum',
        '주휴시간(분단위)': 'sum',
        '주휴수당': 'sum',
        '휴일근무시간(분)': 'sum',  # 휴일근무시간 추가
        '휴일수당': 'sum',  # 휴일수당 추가
        '총급여액': 'sum',
        '기본급': 'sum',
        '연장수당': 'sum',
        'night_pay': 'sum',  # 야간수당 직접 사용
        '수당합계': 'sum',  # 수당합계 추가
        '시급금액': 'last',  # 마지막 시급 사용 (주휴수당 계산과 일치)
        '주_총근무시간': 'first'  # 주간 총 근무시간 추가
        # 참고: '근무시간_분', '연장시간_분', '심야시간_분'은 당월 귀속 필터 적용 후 별도 계산
    }

    user_summaries = df.groupby('Unnamed: 1').agg(agg_dict).reset_index()

    # 당월 귀속 시간 데이터 별도 계산 (11월+12월 합산 문제 해결)
    # '당월_귀속_일반' 필터가 있는 경우에만 당월 데이터로 제한
    if '당월_귀속_일반' in df.columns:
        current_month_only = df[df['당월_귀속_일반'] == True]
        current_month_hours = current_month_only.groupby('Unnamed: 1').agg({
            '근무시간_분': 'sum',
            '연장시간_분': 'sum',
            '심야시간_분': 'sum'
        }).reset_index()
        # 병합 (suffixes 없이 직접 병합 후 컬럼명 변경)
        user_summaries = user_summaries.merge(
            current_month_hours,
            on='Unnamed: 1',
            how='left'
        )
        # 당월 데이터로 업데이트 (x는 기존 agg_dict의 결과, y는 current_month_hours)
        # 기존에 컬럼이 없으면 그냥 새로 생성됨
        if '근무시간_분_x' in user_summaries.columns:
            user_summaries['근무시간_분'] = user_summaries['근무시간_분_y'].fillna(0)
            user_summaries['연장시간_분'] = user_summaries['연장시간_분_y'].fillna(0)
            user_summaries['심야시간_분'] = user_summaries['심야시간_분_y'].fillna(0)
            # 임시 컬럼 제거
            user_summaries.drop(columns=[
                '근무시간_분_x', '근무시간_분_y',
                '연장시간_분_x', '연장시간_분_y',
                '심야시간_분_x', '심야시간_분_y'
            ], inplace=True, errors='ignore')
        else:
            # 기존 컬럼이 없는 경우 (정상)
            user_summaries['근무시간_분'] = user_summaries['근무시간_분'].fillna(0)
            user_summaries['연장시간_분'] = user_summaries['연장시간_분'].fillna(0)
            user_summaries['심야시간_분'] = user_summaries['심야시간_분'].fillna(0)
    else:
        # 필터가 없는 경우 (하위호환): 기존 방식으로 계산
        hours_summary = df.groupby('Unnamed: 1').agg({
            '근무시간_분': 'sum',
            '연장시간_분': 'sum',
            '심야시간_분': 'sum'
        }).reset_index()
        user_summaries = user_summaries.merge(
            hours_summary,
            on='Unnamed: 1',
            how='left'
        )

    user_summaries.rename(columns={
        'Unnamed: 2': 'name',
        'Unnamed: 1': 'user_id',
        '기본급': 'base_pay',
        '주휴수당': 'weekly_holiday_allowance',
        '시급금액': 'hourly_rate',  # 시급 정보 추가
    }, inplace=True)

    # 주별 주휴수당 상세 정보 집계 및 추가
    if '주별_주휴_정보' in df.columns:
        # 사용자별 주별 정보 집계
        weekly_info_by_user = df.groupby('Unnamed: 1')['주별_주휴_정보'].first().to_dict()
        user_summaries['weekly_holiday_details_json'] = user_summaries['user_id'].astype(str).map(weekly_info_by_user)
        
        # JSON 문자열을 파싱하여 리스트로 변환하는 함수
        def parse_weekly_details(json_str):
            if pd.isna(json_str) or json_str is None:
                return []
            try:
                return json.loads(json_str)
            except:
                return []
        
        user_summaries['weekly_holiday_details'] = user_summaries['weekly_holiday_details_json'].apply(parse_weekly_details)
    else:
        user_summaries['weekly_holiday_details'] = [[] for _ in range(len(user_summaries))]

    # 퇴사일 정보 추가 (직원 데이터에서 가져오기)
    user_summaries['resignation_date'] = ''
    if employee_data:
        for index, row in user_summaries.iterrows():
            user_id = str(row['user_id'])
            if user_id in employee_data:
                employee = employee_data[user_id]
                res_date = employee.get('resignation_date', '')
                user_summaries.loc[index, 'resignation_date'] = res_date

    user_summaries['overtime_pay'] = user_summaries['연장수당']  # 연장수당 명확히
    user_summaries['extra_pay'] = user_summaries['연장수당'] + user_summaries['night_pay']  # 기존 호환성 유지
    # 수당합계: 각 사용자별로 합산된 수당 금액
    allowance_totals = df.groupby('Unnamed: 1')['수당합계'].sum()
    user_summaries['수당합계'] = user_summaries['user_id'].map(allowance_totals)

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
        # 세법 기준에서 필요한 값들 추출
        insurance_rates = tax_standards.get('insurance_rates', {})
        minimum_wage = tax_standards.get('minimum_wage', 10320)
        non_eligible_rates = tax_standards.get('non_eligible_rates', {})
        income_tax_brackets = tax_standards.get('income_tax_brackets', [])
        basic_deduction = tax_standards.get('basic_deduction', 1500000)

        for index, row in user_summaries.iterrows():
            user_id = str(row['user_id'])
            if user_id in employee_data:
                employee = employee_data[user_id]

                # (2026 보완) 최저임금 위반 여부 확인
                hourly_rate = row['hourly_rate']
                if hourly_rate < minimum_wage:
                    logging.warning(f"User {user_id} ({row['name']}) 시급({hourly_rate:,}원)이 최저임금({minimum_wage:,}원)에 미달합니다.")

                # (2026 보완) 주간 근로시간 한도 확인 (주 52시간) - 5인 이상 사업장만 해당
                if business_size != 'under_5':
                    weekly_max = row.get('주_총근무시간', 0)
                    if weekly_max > 52:
                        logging.warning(f"User {user_id} ({row['name']}) 주간 근로시간({weekly_max:.1f}h)이 52시간 한도를 초과했습니다.")
                else:
                    # 5인 미만 사업장은 법적 한도는 없으나 건강권을 위해 안내 로깅만 수행
                    weekly_max = row.get('주_총근무시간', 0)
                    if weekly_max > 60:
                        logging.info(f"User {user_id} ({row['name']}) 주간 근로시간({weekly_max:.1f}h)이 매우 높습니다. (5인 미만 예외 적용 중)")

                # 직원 기본 정보 복사
                user_summaries.loc[index, 'department'] = employee.get('department', '')
                user_summaries.loc[index, 'position'] = employee.get('position', '')
                user_summaries.loc[index, 'hire_date'] = employee.get('hire_date', '')

                # 4대보험 대상자 여부 확인
                insurance_eligible = employee.get('insurance_eligible', True)

                # 총급여액
                total_pay = row['총급여액']

                if insurance_eligible:
                    # 4대보험 대상자: 세법 기준에 따른 계산
                    # 국민연금
                    national_pension_rate = insurance_rates.get('national_pension', 0.045)
                    national_pension = round_down_to_10_won(total_pay * national_pension_rate)
                    user_summaries.loc[index, 'national_pension'] = national_pension

                    # 건강보험
                    health_insurance_rate = insurance_rates.get('health_insurance', 0.03545)
                    health_insurance = round_down_to_10_won(total_pay * health_insurance_rate)
                    user_summaries.loc[index, 'health_insurance'] = health_insurance

                    # 장기요양보험 (건강보험의 일정 비율)
                    long_term_care_rate = insurance_rates.get('long_term_care', 0.1281)
                    long_term_care_insurance = round_down_to_10_won(health_insurance * long_term_care_rate)
                    user_summaries.loc[index, 'long_term_care_insurance'] = long_term_care_insurance

                    # 고용보험
                    employment_insurance_rate = insurance_rates.get('employment_insurance', 0.009)
                    employment_insurance = round_down_to_10_won(total_pay * employment_insurance_rate)
                    user_summaries.loc[index, 'employment_insurance'] = employment_insurance

                    # 소득세 계산
                    # 과세표준 = 총급여액 - 4대보험 공제액 - 기본공제
                    taxable_income = total_pay - national_pension - health_insurance - long_term_care_insurance - employment_insurance
                    taxable_income = max(0, taxable_income - basic_deduction)

                    # 누진세율표 적용
                    income_tax = 0
                    for bracket in income_tax_brackets:
                        min_income = bracket.get('min', 0)
                        max_income = bracket.get('max', float('inf'))
                        rate = bracket.get('rate', 0)
                        deduction = bracket.get('deduction', 0)

                        if taxable_income > min_income:
                            bracket_income = min(taxable_income, max_income) - min_income
                            if bracket_income > 0:
                                income_tax += bracket_income * rate - deduction

                    income_tax = max(0, income_tax)  # 음수 방지
                    income_tax = round_down_to_10_won(income_tax)  # 10원 단위 절사
                    user_summaries.loc[index, 'income_tax'] = income_tax

                    # 지방소득세 (소득세의 10%)
                    local_income_tax = income_tax * 0.1
                    local_income_tax = round_down_to_10_won(local_income_tax)  # 10원 단위 절사
                    user_summaries.loc[index, 'local_income_tax'] = local_income_tax

                else:
                    # 4대보험 비대상자: 간단한 세금 계산
                    # 4대보험 항목들은 모두 0원
                    user_summaries.loc[index, 'national_pension'] = 0
                    user_summaries.loc[index, 'health_insurance'] = 0
                    user_summaries.loc[index, 'employment_insurance'] = 0
                    user_summaries.loc[index, 'long_term_care_insurance'] = 0

                    # 소득세: 세법 기준에 따른 비대상자 세율
                    income_tax_rate = non_eligible_rates.get('income_tax', 0.03)
                    income_tax = round_down_to_10_won(total_pay * income_tax_rate)
                    user_summaries.loc[index, 'income_tax'] = income_tax

                    # 지방소득세: 세법 기준에 따른 비대상자 세율
                    local_income_tax_rate = non_eligible_rates.get('local_income_tax', 0.003)
                    local_income_tax = round_down_to_10_won(total_pay * local_income_tax_rate)
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

    logging.info(f"--- Finished create_user_summaries. Used tax standards: {tax_standards.get('name', 'Unknown')} ---")
    return user_summaries


def generate_payslips(summaries_df, template_path, output_filename, data_month, company_name="", selected_users=None, explanation_options=None, data_file_path=None, employee_data=None):
    """템플릿과 100% 구조 일치하는 급여명세서 생성 - 완전 재설계"""

    logging.info(f"--- Starting generate_payslips for {len(summaries_df)} users ---")

    if selected_users:
        summaries_df = summaries_df[summaries_df['user_id'].isin(selected_users)]
        logging.info(f"Filtered to {len(summaries_df)} selected users")

    # 템플릿 파일 로드 (급여명세서.xlsx)
    template_filename = '급여명세서.xlsx'
    template_path = os.path.join(os.path.dirname(__file__), template_filename)

    if not os.path.exists(template_path):
        logging.error(f"Template file not found: {template_path}")
        # 템플릿이 없을 경우의 폴백은 생략하고 에러 발생 (사용자가 템플릿 사용을 명시했으므로)
        raise FileNotFoundError(f"템플릿 파일 '{template_filename}'을(를) 찾을 수 없습니다.")

    try:
        # 템플릿 워크북 로드
        result_wb = openpyxl.load_workbook(template_path)
        source_sheet = result_wb.active
        
        # 템플릿 시트 이름 변경 (임시)
        source_sheet.title = "Template_Temp"
    except Exception as e:
        logging.error(f"Error loading template: {e}")
        raise Exception(f"템플릿 파일을 로드하는 중 오류가 발생했습니다: {e}")

    for index, user_summary in summaries_df.iterrows():
        # 시트 이름 생성 (특수문자 제거)
        sheet_name = ''.join(c for c in user_summary['name'] if c.isalnum())
        
        # 템플릿 복사하여 새 시트 생성
        ws = result_wb.copy_worksheet(source_sheet)
        ws.title = sheet_name

        # 수당 계산 (Block 2 및 전체 로직에서 사용하기 위해 상단으로 이동)
        current_month = data_month.split()[1].replace('월', '')
        allowance_totals = {'position': 0, 'other': 0, 'special': 0}

        if employee_data and str(user_summary['user_id']) in employee_data:
            employee = employee_data[str(user_summary['user_id'])]
            allowances = employee.get('allowances', {})

            recurring = allowances.get('recurring', [])
            for allowance in recurring:
                if '직급' in allowance.get('name', ''):
                    allowance_totals['position'] += allowance.get('amount', 0)
                else:
                    allowance_totals['other'] += allowance.get('amount', 0)

            # 현재 월 (YYYY-MM 형식) 추출
            current_date_prefix = ""
            if data_month:
                # "2026년 12월" -> "2026-12"
                try:
                    parts = data_month.split()
                    if len(parts) >= 2:
                        y = parts[0].replace('년', '')
                        m = parts[1].replace('월', '').zfill(2)
                        current_date_prefix = f"{y}-{m}"
                except:
                    pass

            for allowance in allowances.get('one_time', []):
                apply_date = allowance.get('date', '')
                if apply_date and current_date_prefix and apply_date.startswith(current_date_prefix):
                    allowance_totals['special'] += allowance.get('amount', 0)

        # 템플릿 구조와 정확히 일치하는 데이터 입력
        base_pay_total = float(user_summary.get('base_pay', 0)) + float(allowance_totals['special'])

        logging.debug(f"Processing sheet for user: {user_summary['name']} ({sheet_name})")

        # ===========================================
        # 템플릿 데이터 입력 (서식 보존)
        # ===========================================

        # 헤더 정보 입력 (병합 셀의 첫 번째 셀에만 값 입력)
        # 템플릿의 기존 서식을 유지하기 위해 값만 업데이트
        ws['A1'] = f"{data_month} 급여명세서"
        ws['C2'] = company_name
        ws['D3'] = user_summary['name']
        ws['D4'] = user_summary.get('department', '')
        ws['D5'] = user_summary.get('hire_date', '')

        # 급여 내역 입력
        
        # 행11: 기본급 + 국민연금
        ws['D11'] = base_pay_total
        ws['H11'] = float(user_summary.get('national_pension', 0))

        # 행12: 건강보험
        ws['H12'] = float(user_summary.get('health_insurance', 0))

        # 행13: 연장근로수당 + 고용보험
        ws['D13'] = float(user_summary.get('연장수당', 0))
        ws['H13'] = float(user_summary.get('employment_insurance', 0))

        # 행14: 야간근로수당 + 장기요양보험
        ws['D14'] = float(user_summary.get('night_pay', 0))
        ws['H14'] = float(user_summary.get('long_term_care_insurance', 0))

        # 행15: 휴일근로수당 + 소득세
        ws['D15'] = 0.0  # 휴일수당 (현재 로직상 0)
        ws['H15'] = float(user_summary.get('income_tax', 0))

        # 행16: 주휴수당 + 지방소득세
        ws['D16'] = float(user_summary.get('weekly_holiday_allowance', 0))
        ws['H16'] = float(user_summary.get('local_income_tax', 0))

        # 행17: 직급수당
        ws['D17'] = float(allowance_totals['position'])

        # 행18: 기타수당
        ws['D18'] = float(allowance_totals['other'])

        # 합계 계산
        total_payment = (
            base_pay_total +
            float(user_summary.get('연장수당', 0)) +
            float(user_summary.get('night_pay', 0)) +
            float(user_summary.get('weekly_holiday_allowance', 0)) +
            float(allowance_totals['position']) +
            float(allowance_totals['other'])
        )

        total_deduction = (
            float(user_summary.get('national_pension', 0)) +
            float(user_summary.get('health_insurance', 0)) +
            float(user_summary.get('employment_insurance', 0)) +
            float(user_summary.get('long_term_care_insurance', 0)) +
            float(user_summary.get('income_tax', 0)) +
            float(user_summary.get('local_income_tax', 0))
        )

        # 행20: 지급합계 / 공제합계 / 실수령액
        # 템플릿상 위치: 지급합계(D20 or D19?), 공제합계(H20 or H19?)
        # 기존 코드 기준 Row 20
        ws['D20'] = total_payment # 지급 합계
        ws['H20'] = total_deduction # 공제 합계
        
        # 실수령액 (템플릿 하단, 예: D21 or specific cell)
        # 기존 코드에선 명시적인 실수령액 셀 위치가 'C20'='실수령액', 'D20'=NetPay 였는데,
        # 위에서 D20을 Total Payment로 썼음. 
        # 템플릿을 확인 못하므로 기존 로직(Row 20 for Totals)을 따르되, 
        # 실수령액은 보통 그 아래나 별도 공간에 있음.
        # Let's assume Row 21 is for Net Pay based on typical layouts or previous hints.
        ws['D21'] = total_payment - total_deduction # 실수령액

        # 설명/주석 데이터 (C23, D23, G23 etc from previous code)
        ws['C23'] = int(user_summary.get('연장시간_분', 0))
        ws['D23'] = int(user_summary.get('심야시간_분', 0))
        
        # 시급 정보
        ws['G23'] = float(user_summary.get('hourly_rate', 0))
        
        # 상세 계산식 설명 (Row 26+)
        # 기존 로직 유지 (설명 옵션 처리)
        if explanation_options.get('base_pay_explanation', True):
             ws['D26'] = f"(총 {user_summary.get('근무시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원"
        
        if explanation_options.get('holiday_explanation', True):
            weekly_allowance = float(user_summary.get('weekly_holiday_allowance', 0))
            if weekly_allowance > 0:
                 ws['D27'] = f"주휴수당 발생 ({weekly_allowance:,.0f}원)"
            else:
                 ws['D27'] = "주휴수당 해당없음"

        if explanation_options.get('night_explanation', True):
            ws['D28'] = f"(총 {user_summary.get('심야시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원 * {OVERTIME_MULTIPLIER}배"

        if explanation_options.get('overtime_explanation', True):
            ws['D30'] = f"(총 {user_summary.get('연장시간_분', 0)}분 / 60) * {int(user_summary.get('hourly_rate', 0))}원 * {OVERTIME_MULTIPLIER}배"

    # 템플릿 원본 시트 삭제
    if "Template_Temp" in result_wb.sheetnames:
        result_wb.remove(result_wb["Template_Temp"])

    try:
        result_wb.save(output_filename)
        logging.info(f"Successfully generated payslips at '{output_filename}' using template")
    except Exception as e:
        logging.error(f"Error saving file: {e}", exc_info=True)
        raise Exception(f"파일 저장 중 오류가 발생했습니다: {e}")



def generate_payslips_html(summaries_df, output_filename, data_month, company_name="", selected_users=None, explanation_options=None, data_file_path=None, employee_data=None, business_size='under_5'):
    """Generates HTML payslip files using the external template file."""
    logging.info(f"--- Starting generate_payslips_html for {len(summaries_df)} users ---")

    # 연도 추출 (산출식 상세 표기용)
    try:
        tax_year = int(data_month.split()[0].replace('년', ''))
    except:
        tax_year = datetime.now().year

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
        # 통합 모드: 모든 직원의 급여명세서를 하나의 HTML 파일로 생성
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

            payslip_data = _prepare_payslip_data(user_summary, data_month, company_name, explanation_options, data_file_path, employee_data, tax_year=tax_year, business_size=business_size)
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

    elif isinstance(selected_users, list) and len(selected_users) > 0:
        # 선택 모드: 선택된 직원들만 개별 파일로 생성 (모음 파일 생성 안 함)
        output_dir = output_filename if os.path.isdir(output_filename) else os.path.dirname(output_filename)
        base_name = os.path.splitext(os.path.basename(output_filename))[0] if not os.path.isdir(output_filename) else f"급여명세서_{data_month.replace(' ', '_').replace('년', 'year').replace('월', 'month')}"

        for index, user_summary in summaries_df.iterrows():
            user_name = user_summary['name']
            safe_name = ''.join(c for c in user_name if c.isalnum() or c in ' _-')
            individual_filename = os.path.join(output_dir, f"{safe_name}_{base_name}.html")

            payslip_data = _prepare_payslip_data(user_summary, data_month, company_name, explanation_options, data_file_path, employee_data, tax_year=tax_year, business_size=business_size)

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

    else:
        # 개별(모든직원) 모드: 모든 직원을 개별 파일로 생성
        output_dir = output_filename if os.path.isdir(output_filename) else os.path.dirname(output_filename)
        base_name = os.path.splitext(os.path.basename(output_filename))[0] if not os.path.isdir(output_filename) else f"급여명세서_{data_month.replace(' ', '_').replace('년', 'year').replace('월', 'month')}"

        for index, user_summary in summaries_df.iterrows():
            user_name = user_summary['name']
            safe_name = ''.join(c for c in user_name if c.isalnum() or c in ' _-')
            individual_filename = os.path.join(output_dir, f"{safe_name}_{base_name}.html")

            payslip_data = _prepare_payslip_data(user_summary, data_month, company_name, explanation_options, data_file_path, employee_data, tax_year=tax_year, business_size=business_size)

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

def _prepare_payslip_data(user_summary, data_month, company_name, explanation_options=None, data_file_path=None, employee_data=None, tax_year=None, business_size='under_5'):
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

    # 퇴사일 정보 가져오기 (함수 시작 부분에서 정의)
    # user_summary에서 먼저 확인 (employee_data에서 가져오는 것보다 우선)
    resignation_date = user_summary.get('resignation_date')
    if not resignation_date and employee_data and str(user_summary.get('user_id', '')) in employee_data:
        employee = employee_data[str(user_summary.get('user_id', ''))]
        res_date_str = employee.get('resignation_date')
        if res_date_str:
            try:
                res_date = datetime.strptime(res_date_str, '%Y-%m-%d')
                resignation_date = res_date.strftime('%Y-%m-%d')
            except:
                resignation_date = res_date_str

    # Calculate totals - try to use pre-calculated values from summary_df if available
    total_payment = user_summary.get('총급여액') or user_summary.get('total_payment')
    if total_payment is None:
        total_payment = (user_summary.get('base_pay', 0) +
                        user_summary.get('weekly_holiday_allowance', 0) +
                        user_summary.get('연장수당', 0) +
                        user_summary.get('night_pay', 0) +
                        user_summary.get('수당합계', 0))
    
    total_deduction = user_summary.get('deductions') or user_summary.get('total_deduction')
    if total_deduction is None:
        total_deduction = sum([
            user_summary.get('national_pension', 0),
            user_summary.get('health_insurance', 0),
            user_summary.get('employment_insurance', 0),
            user_summary.get('long_term_care_insurance', 0),
            user_summary.get('income_tax', 0),
            user_summary.get('local_income_tax', 0)
        ])
        
    net_pay = user_summary.get('net_pay')
    if net_pay is None:
        net_pay = total_payment - total_deduction

    # 수당 항목 개별 추출 (동적 표시용) - 모든 지급 항목 포함
    allowance_items = []

    # 세법 기준 로드 (배수 등 확인용)
    tax_manager = TaxLawManager()
    if tax_year:
        tax_standards = tax_manager.get_standards_for_year(str(tax_year))
    else:
        try:
            year_val = int(data_month.split()[0].replace('년', ''))
            tax_standards = tax_manager.get_standards_for_year(str(year_val))
        except:
            tax_standards = tax_manager.get_standards_for_year(str(datetime.now().year))

    ot_multiplier = tax_standards.get('overtime_multiplier', 1.5)
    # 5인 미만 사업장은 법적으로 가산 의무가 없으므로 문구 조정 가능
    premium_label = "배"
    if business_size == 'under_5' and ot_multiplier == 1.5:
        premium_label = "배 (5인미만 가산의무 없음)"
        # 5인 미만 사업장은 가산 의무 없음 - 산출식용 배수를 1.0으로 변경
        ot_multiplier = 1.0

    hourly_rate = int(user_summary.get('hourly_rate', 0))

    # 기본급 추가 (항상 포함 - HTML과 구조 일치)
    base_pay_amount = user_summary.get('base_pay', 0)
    work_minutes = user_summary.get('근무시간_분', 0)
    work_hours = work_minutes / 60.0
    
    # 기본급 상세 메시지 생성
    if base_pay_amount > 0:
        base_detail = f"{work_hours:.1f}시간 * {hourly_rate:,}원"
    else:
        base_detail = "근무시간 없음"
    
    allowance_items.append({
        'name': '기본급',
        'amount': base_pay_amount,
        'detail': base_detail,
        'type': 'base_pay'
    })

    # 주휴수당 추가 (항상 포함 - HTML과 구조 일치)
    weekly_allowance = user_summary.get('weekly_holiday_allowance', 0)
    holiday_minutes = user_summary.get('주휴시간(분단위)', 0)
    
    # 주휴수당 상세 메시지 생성
    if weekly_allowance > 0:
        holiday_detail = f"주휴시간 총 {holiday_minutes/60:.1f}시간 * {hourly_rate:,}원"
    else:
        holiday_detail = "주휴수당 해당없음 (주 15시간 미만 근무)"
    
    allowance_items.append({
        'name': '주휴수당',
        'amount': weekly_allowance,
        'detail': holiday_detail,
        'type': 'holiday'
    })

    # 연장수당 추가
    overtime_pay = user_summary.get('연장수당', 0)
    if True:  # 연장수당 항상 추가
        ot_minutes = user_summary.get('연장시간_분', 0)
        ot_hours = ot_minutes / 60.0
        # 연장수당은 가산 배수(ot_multiplier) 반영
        allowance_items.append({
            'name': '연장수당',
            'amount': overtime_pay,
            'detail': f"{ot_hours:.1f}시간 * {hourly_rate:,}원 * {ot_multiplier}{premium_label}",
            'type': 'overtime'
        })

    # 야간수당 추가 (고용노동부 지침 준수)
    night_pay = user_summary.get('night_pay', 0)
    night_minutes = user_summary.get('심야시간_분', 0)
    night_hours = night_minutes / 60.0
    
    # 야간수당 배수: 5인 미만은 가산 의무 없음 (1.0배), 5인 이상은 1.5배
    if business_size == 'under_5':
        night_multiplier = 1.0  # 기본만 지급
        display_multiplier = 1.0
    else:
        night_multiplier = 1.5  # 야간가산 0.5 포함
        display_multiplier = 1.5
    
    # 계산된 값이 없으면 재계산 (일관성 확보)
    if night_pay == 0 and night_hours > 0:
        night_pay = night_hours * hourly_rate * night_multiplier
    
    allowance_items.append({
        'name': '야간수당',
        'amount': night_pay,
        'detail': f"{night_hours:.1f}시간 * {hourly_rate:,}원 * {display_multiplier}배" if business_size != 'under_5' else f"{night_hours:.1f}시간 * {hourly_rate:,}원 (5인미만)",
        'type': 'night'
    })

    # 추가 수당 항목들 (직원별 수당 데이터)
    allowances = {}  # 초기화 추가
    if employee_data and str(user_summary['user_id']) in employee_data:
        employee = employee_data[str(user_summary['user_id'])]
        allowances = employee.get('allowances', {})

        print(f"DEBUG: employee allowances = {allowances}")

        # 지속적 수당 추가
        for allowance in allowances.get('recurring', []):
            # 수당별 상세 내역 생성
            detail_text = f"월 {allowance['amount']:,}원"
            allowance_items.append({
                'name': allowance['name'],
                'amount': allowance['amount'],
                'detail': detail_text,
                'type': 'recurring'
            })

    # 해당 월 단발성 수당 추가 (시간적 유효성 검증)
    current_month = data_month.split()[1].replace('월', '')  # "12월" -> "12"
    current_year = data_month.split()[0].replace('년', '')   # "2026년" -> "2026"
    target_date = f"{current_year}-{current_month.zfill(2)}"  # "2026-12"

    print(f"DEBUG: current_month = {current_month}, target_date = {target_date}")

    for allowance in allowances.get('one_time', []):
        apply_date = allowance.get('date', '')
        applied = allowance.get('applied', False)  # 적용 여부 확인

        print(f"DEBUG: allowance date = {apply_date}, applied = {applied}")

        # 시간적 유효성 검증: 해당 월이고 아직 적용되지 않은 경우만
        if apply_date.startswith(target_date) and not applied:
                # 단발성 수당 상세 내역 생성
                year_month = apply_date.replace('-', '년 ') + '월'
                detail_text = f"{year_month} 특별 지급"
                allowance_items.append({
                    'name': allowance['name'],
                    'amount': allowance['amount'],
                    'detail': detail_text,
                    'type': 'one_time'
                })

                # 적용 후 플래그 설정 (중복 적용 방지)
                allowance['applied'] = True
                print(f"DEBUG: 수당 '{allowance['name']}' 적용됨, applied = True")

        print(f"DEBUG: final allowance_items = {allowance_items}")

    # =========================================================
    # 주휴수당 계산 설명 - 주차별 상세 분석 (실제 데이터 사용)
    # =========================================================
    weekly_allowance = float(user_summary.get('weekly_holiday_allowance', 0))
    holiday_minutes = user_summary.get('주휴시간(분단위)', 0)
    
    # 실제 주차별 주휴수당 상세 데이터 사용 (calculate_salary에서 계산된 데이터)
    weekly_holiday_details = user_summary.get('weekly_holiday_details', [])
    
    # 주차별 데이터 형식 변환 (템플릿 호환성)
    formatted_weekly_details = []
    total_calculated = 0
    
    if weekly_holiday_details and len(weekly_holiday_details) > 0:
        # 현재 월에 귀속되는 주차만 필터링
        current_year = data_month.split()[0].replace('년', '')
        current_month = data_month.split()[1].replace('월', '')
        
        for week_data in weekly_holiday_details:
            # 날짜 형식 변환 (YYYY-MM-DD -> M/D)
            week_start = week_data.get('week_start', '')
            week_end = week_data.get('week_end', '')
            holiday_date = week_data.get('holiday_date', '')
            
            try:
                dt_start = datetime.strptime(week_start, '%Y-%m-%d')
                dt_end = datetime.strptime(week_end, '%Y-%m-%d')
                dt_holiday = datetime.strptime(holiday_date, '%Y-%m-%d')
                
                week_period = f"{dt_start.month}/{dt_start.day}~{dt_end.month}/{dt_end.day}"
                holiday_day_formatted = f"{dt_holiday.month}/{dt_holiday.day}"
                week_귀속월 = f"{dt_holiday.year}년 {dt_holiday.month}월"

                # 현재 월에 귀속되는 주차만 포함
                if week_귀속월 == f"{current_year}년 {current_month}월":
                    amount = week_data.get('amount', 0)
                    if not week_data.get('is_skipped', False):
                        total_calculated += amount
                    
                    formatted_weekly_details.append({
                        'week': len(formatted_weekly_details) + 1,
                        'week_period': week_period,
                        'holiday_date': holiday_day_formatted,
                        '귀속월': week_귀속월,
                        'work_hours': week_data.get('work_hours', 0),
                        'holiday_hours': week_data.get('holiday_hours', 0),
                        'hourly_rate': week_data.get('hourly_rate', 0),
                        'amount': amount,
                        'is_skipped': week_data.get('is_skipped', False),
                        'skip_reason': week_data.get('skip_reason', '')
                    })
            except:
                # 날짜 파싱 실패 시 기본 처리 (하위호환)
                week_period = f"{week_start}~{week_end}"
                holiday_day_formatted = holiday_date
                week_귀속월 = data_month

                # 기본 월 비교 (연도 정보 없을 경우)
                if week_귀속월 == data_month:
                    amount = week_data.get('amount', 0)
                    if not week_data.get('is_skipped', False):
                        total_calculated += amount
                    
                    formatted_weekly_details.append({
                        'week': len(formatted_weekly_details) + 1,
                        'week_period': week_period,
                        'holiday_date': holiday_day_formatted,
                        '귀속월': week_귀속월,
                        'work_hours': week_data.get('work_hours', 0),
                        'holiday_hours': week_data.get('holiday_hours', 0),
                        'hourly_rate': week_data.get('hourly_rate', 0),
                        'amount': amount,
                        'is_skipped': week_data.get('is_skipped', False),
                        'skip_reason': week_data.get('skip_reason', '')
                    })
    
    if not formatted_weekly_details:
        # 실제 데이터가 없는 경우 (하위호환)
        if weekly_allowance == 0 and not resignation_date:
            holiday_calculation_note = (
                f"주휴수당 해당없음 (기준: 주 {HOLIDAY_ALLOWANCE_HOURS}시간 이상 근무)"
            )
            weekly_holiday_summary = None
        else:
            holiday_calculation_note = f"주휴수당: {weekly_allowance:,.0f}원"
            weekly_holiday_summary = {
                'total_weeks': 0,
                'total_amount': weekly_allowance,
                'avg_holiday_hours': 0,
                'hourly_rate': int(user_summary.get('hourly_rate', 0))
            }
    else:
        holiday_hours = holiday_minutes / 60.0
        hourly_rate = int(user_summary.get('hourly_rate', 0))
        
        # 상세 산출식
        holiday_calculation_note = f"주휴수당: {weekly_allowance:,.0f}원 ({len(formatted_weekly_details)}주 합산)"
        
        # 주차별 요약 정보
        weekly_holiday_summary = {
            'total_weeks': len(formatted_weekly_details),
            'total_amount': weekly_allowance,
            'avg_holiday_hours': holiday_hours / len(formatted_weekly_details) if formatted_weekly_details else 0,
            'hourly_rate': hourly_rate
        }
    
    weekly_holiday_details = formatted_weekly_details

    # 수식 표현 개선 (시간 단위로 변환하여 친숙하게 표현)
    hourly_rate = int(user_summary.get('hourly_rate', 0))
    base_pay_amount = user_summary.get('base_pay', 0)

    # 기본급 계산 설명 (시간 단위로 변환)
    total_minutes = user_summary.get('근무시간_분', 0)
    total_hours = total_minutes / 60.0

    if explanation_options.get('base_pay_explanation', True):
        calculation_note_1 = f"근무시간 {total_hours:.1f}시간 × 시급 {hourly_rate:,}원 = {base_pay_amount:,.0f}원"
    else:
        calculation_note_1 = f"근무시간 {total_hours:.1f}시간에 시급 적용"

    # 연장수당 계산 설명
    overtime_minutes = user_summary.get('연장시간_분', 0)
    overtime_hours = overtime_minutes / 60.0
    overtime_pay = user_summary.get('연장수당', 0)

    if explanation_options.get('overtime_explanation', True):
        calculation_note_3 = f"연장근무 {overtime_hours:.1f}시간 × 시급 {hourly_rate:,}원 × {ot_multiplier}{premium_label} = {overtime_pay:,.0f}원"
    else:
        calculation_note_3 = f"연장근무 {overtime_hours:.1f}시간에 가산 적용"

    # 야간수당 계산 설명 추가
    night_minutes = user_summary.get('심야시간_분', 0)
    night_hours = night_minutes / 60.0
    night_pay_amount = user_summary.get('night_pay', 0)

    if explanation_options.get('night_explanation', True):
        calculation_note_night = f"야간근무 {night_hours:.1f}시간 × 시급 {hourly_rate:,}원 × {display_multiplier}배 = {night_pay_amount:,.0f}원"
    else:
        calculation_note_night = f"야간근무 {night_hours:.1f}시간에 가산 적용"

    # 휴일수당 계산 설명 추가 (8시간 초과분 2.0배 반영)
    holiday_minutes = user_summary.get('휴일근무시간(분)', 0)
    holiday_hours = holiday_minutes / 60.0
    holiday_pay_amount = user_summary.get('휴일수당', 0)
    
    # 휴일수당 배수: 5인 미만은 가산 없음 (1.0배), 5인 이상은 8시간 이내 1.5배, 초과 2.0배
    if business_size == 'under_5':
        # 5인 미만: 모든 시간 1.0배
        if explanation_options.get('holiday_work_explanation', True):
            if holiday_hours > 0:
                calculation_note_holiday_work = f"휴일근무 {holiday_hours:.1f}시간 × 시급 {hourly_rate:,}원 (5인미만 가산의무 없음) = {holiday_pay_amount:,.0f}원"
            else:
                calculation_note_holiday_work = "휴일근무 없음"
        else:
            calculation_note_holiday_work = f"휴일근무 {holiday_hours:.1f}시간에 가산 적용"
    else:
        # 5인 이상: 8시간 이내 1.5배, 초과 2.0배
        if explanation_options.get('holiday_work_explanation', True):
            if holiday_hours > 0:
                if holiday_hours <= 8:
                    # 8시간 이하: 전체 1.5배
                    calculation_note_holiday_work = f"휴일근무 {holiday_hours:.1f}시간 × 시급 {hourly_rate:,}원 × 1.5배 = {holiday_pay_amount:,.0f}원"
                else:
                    # 8시간 초과: 8시간까지 1.5배, 초과분 2.0배
                    over_8_hours = holiday_hours - 8
                    under_8_pay = 8 * hourly_rate * 1.5
                    over_8_pay = over_8_hours * hourly_rate * 2.0
                    calculation_note_holiday_work = (
                        f"휴일근무 {holiday_hours:.1f}시간 = "
                        f"8시간×1.5배({under_8_pay:,.0f}원) + "
                        f"{over_8_hours:.1f}시간×2.0배({over_8_pay:,.0f}원) = "
                        f"{holiday_pay_amount:,.0f}원"
                    )
            else:
                calculation_note_holiday_work = "휴일근무 없음"
        else:
            calculation_note_holiday_work = f"휴일근무 {holiday_hours:.1f}시간에 가산 적용"

    return {
        'data_month': data_month,
        'company_name': company_name,
        'name': user_summary['name'],
        'user_id': str(user_summary.get('user_id', '')),
        'department': user_summary.get('department', ''),
        'position': user_summary.get('position', ''),
        'hire_date': user_summary.get('hire_date', ''),
        'resignation_date': resignation_date,
        'payment_date': user_summary.get('payment_date', ''),
        'base_pay': base_pay_amount,
        'weekly_holiday_allowance': user_summary.get('weekly_holiday_allowance', 0),
        'extra_pay': overtime_pay,
        'night_pay': night_pay_amount,
        'holiday_pay': holiday_pay_amount,  # 휴일수당 금액 추가
        'allowance_total': user_summary.get('수당합계', 0),  # 수당 합계 추가
        'allowance_items': allowance_items,  # 동적 수당 항목 리스트
        'national_pension': user_summary.get('national_pension', 0),
        'health_insurance': user_summary.get('health_insurance', 0),
        'employment_insurance': user_summary.get('employment_insurance', 0),
        'long_term_care_insurance': user_summary.get('long_term_care_insurance', 0),
        'income_tax': user_summary.get('income_tax', 0),
        'local_income_tax': user_summary.get('local_income_tax', 0),
        'total_payment': total_payment,
        'total_deduction': total_deduction,
        'net_pay': net_pay,
        'hourly_rate': hourly_rate,
        'calculation_note_1': calculation_note_1,  # 개선된 기본급 산출식
        'calculation_note_2': holiday_calculation_note,  # 개선된 주휴수당 산출식
        'calculation_note_3': calculation_note_3,  # 개선된 연장수당 산출식
        'calculation_note_night': calculation_note_night,  # 야간수당 산출식 추가
        'calculation_note_holiday_work': calculation_note_holiday_work,  # 휴일수당 산출식 추가
        # 주차별 주휴수당 상세 데이터 추가
        'weekly_holiday_details': weekly_holiday_details,
        'weekly_holiday_summary': weekly_holiday_summary,
        # HTML 템플릿 조걶부 렌더링 옵션들
        'show_base_pay_note': explanation_options.get('base_pay_explanation', True),
        'show_holiday_note': explanation_options.get('holiday_explanation', True),
        'show_overtime_note': explanation_options.get('overtime_explanation', True),
        'show_night_note': explanation_options.get('night_explanation', True),
        'show_holiday_work_note': explanation_options.get('holiday_work_explanation', True),  # 휴일근무 표시 옵션
        'show_hourly_rate': True,  # 시급은 항상 표시 (필요시 옵션으로 변경 가능)
        'rowspan': 6,  # 공제 항목 6개에 맞는 rowspan 값
        # 추가된 변수들
        'allowance_name': '',  # 템플릿에 존재하는 변수
        'allowance_detail': '',  # 템플릿에 존재하는 변수
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

    df = load_and_preprocess_data(file_path, target_year=year, target_month=month)

    if df is None or df.empty:
        raise ValueError("데이터 로딩에 실패했거나 처리할 데이터가 없습니다.")

    # target_year_month를 'YYYY-MM' 형식으로 준비
    target_year_month = f"{year}-{str(month).zfill(2)}"

    df_calculated = calculate_salary(df, employee_data, target_year_month=target_year_month)
    summaries = create_user_summaries(df_calculated, employee_data, tax_year=year)

    # 사업장 규모 정보 가져오기 (HTML 명세서 전달용)
    business_size = 'under_5'
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                business_size = config_data.get('business_size', 'under_5')
    except:
        pass

    logging.info(f"--- Finished process_payroll_for_gui successfully ---")
    return summaries, data_month_for_title, business_size


def generate_individual_allowance_excels(employee_data, target_employee_id, data_month, output_dir="allowance_files"):
    """
    특정 직원의 각 수당별로 개별 엑셀 파일을 생성합니다.

    Args:
        employee_data: 직원 데이터 딕셔너리
        target_employee_id: 대상 직원 ID
        data_month: 데이터 월 (예: "2026년 12월")
        output_dir: 출력 디렉토리

    Returns:
        생성된 파일들의 리스트
    """
    logging.info(f"--- Starting generate_individual_allowance_excels for employee {target_employee_id} ---")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if target_employee_id not in employee_data:
        raise ValueError(f"직원 ID '{target_employee_id}'을(를) 찾을 수 없습니다.")

    employee = employee_data[target_employee_id]
    employee_name = employee.get('name', 'Unknown')
    allowances = employee.get('allowances', {})

    generated_files = []

    # 지속적 수당 처리
    recurring_allowances = allowances.get('recurring', [])
    for allowance in recurring_allowances:
        try:
            file_path = create_allowance_excel_file(
                employee_name=employee_name,
                allowance_name=allowance['name'],
                allowance_amount=allowance['amount'],
                allowance_type='지속적',
                data_month=data_month,
                output_dir=output_dir,
                taxable=allowance.get('taxable', True)
            )
            generated_files.append(file_path)
            logging.info(f"Created recurring allowance file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to create file for recurring allowance {allowance['name']}: {e}")

    # 단발성 수당 처리
    one_time_allowances = allowances.get('one_time', [])
    for allowance in one_time_allowances:
        try:
            # 해당 월의 단발성 수당만 처리
            current_month = data_month.split()[1].replace('월', '')
            allowance_date = allowance.get('date', '')
            if allowance_date and allowance_date.endswith(f'-{current_month}'):
                file_path = create_allowance_excel_file(
                    employee_name=employee_name,
                    allowance_name=allowance['name'],
                    allowance_amount=allowance['amount'],
                    allowance_type='단발성',
                    data_month=data_month,
                    output_dir=output_dir,
                    taxable=allowance.get('taxable', True),
                    apply_date=allowance_date
                )
                generated_files.append(file_path)
                logging.info(f"Created one-time allowance file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to create file for one-time allowance {allowance['name']}: {e}")

    logging.info(f"--- Finished generate_individual_allowance_excels. Created {len(generated_files)} files ---")
    return generated_files


def create_allowance_excel_file(employee_name, allowance_name, allowance_amount, allowance_type, data_month, output_dir, taxable=True, apply_date=None):
    """
    개별 수당에 대한 엑셀 파일을 생성합니다.

    Args:
        employee_name: 직원명
        allowance_name: 수당명
        allowance_amount: 수당 금액
        allowance_type: 수당 유형 ('지속적' 또는 '단발성')
        data_month: 데이터 월
        output_dir: 출력 디렉토리
        taxable: 과세 여부
        apply_date: 적용 날짜 (단발성 수당의 경우)

    Returns:
        생성된 파일 경로
    """
    # 파일명 생성 (한글 포함 가능하도록 안전한 이름으로 변환)
    safe_employee_name = ''.join(c for c in employee_name if c.isalnum() or c in ' _-')
    safe_allowance_name = ''.join(c for c in allowance_name if c.isalnum() or c in ' _-')
    month_short = data_month.replace('년 ', '').replace('월', '')

    filename = f"{safe_employee_name}_{safe_allowance_name}_{month_short}.xlsx"
    file_path = os.path.join(output_dir, filename)

    # 새로운 워크북 생성
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{employee_name}_{allowance_name}"

    # 스타일 설정
    header_font = Font(bold=True, size=12)
    normal_font = Font(size=10)
    amount_font = Font(size=10, bold=True)

    # 제목
    ws['A1'] = f"{data_month} {allowance_name} 수당 명세서"
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:E1')

    # 기본 정보
    ws['A3'] = "직원명"
    ws['B3'] = employee_name
    ws['A4'] = "수당명"
    ws['B4'] = allowance_name
    ws['A5'] = "수당 유형"
    ws['B5'] = allowance_type
    ws['A6'] = "금액"
    ws['B6'] = f"{allowance_amount:,}원"
    ws['A7'] = "과세 여부"
    ws['B7'] = "과세" if taxable else "비과세"

    if apply_date:
        ws['A8'] = "적용 날짜"
        ws['B8'] = apply_date

    # 헤더 스타일 적용
    for row in range(3, 9):
        if ws[f'A{row}'].value:
            ws[f'A{row}'].font = header_font
            ws[f'B{row}'].font = normal_font

    ws['B6'].font = amount_font

    # 열 너비 조정
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 15

    # 테두리 추가
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                        top=Side(style='thin'), bottom=Side(style='thin'))

    for row in range(1, 9):
        for col in ['A', 'B', 'C', 'D', 'E']:
            cell = ws[f'{col}{row}']
            if cell.value is not None:
                cell.border = thin_border

    # 숫자 포맷 적용
    if ws['B6'].value and '원' in str(ws['B6'].value):
        # 금액 셀에 숫자 포맷 적용 (텍스트이므로 별도 처리)
        pass

    # 파일 저장
    wb.save(file_path)
    wb.close()

    return file_path


def generate_allowance_specific_payslip(summaries_df, template_path, output_filename, data_month, company_name="", selected_users=None, specific_allowance=None, employee_data=None):
    """특정 수당만 적용하여 급여명세서를 생성합니다.

    specific_allowance: {'name': '수당명', 'amount': 금액} 형태의 딕셔너리
    """
    logging.info(f"--- Starting generate_allowance_specific_payslip for allowance: {specific_allowance} ---")

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

        # Create new worksheet by copying template sheet directly
        ws = result_wb.create_sheet(title=sheet_name)

        # Copy entire template sheet to maintain exact structure
        for row_idx in range(1, template_sheet.max_row + 1):
            for col_idx in range(1, template_sheet.max_column + 1):
                source_cell = template_sheet.cell(row=row_idx, column=col_idx)
                target_cell = ws.cell(row=row_idx, column=col_idx)

                # Copy value
                target_cell.value = source_cell.value

                # Copy all formatting
                if source_cell.has_style:
                    target_cell.font = copy.copy(source_cell.font)
                    target_cell.alignment = copy.copy(source_cell.alignment)
                    target_cell.border = copy.copy(source_cell.border)
                    target_cell.fill = copy.copy(source_cell.fill)
                    target_cell.number_format = source_cell.number_format
                    target_cell.protection = copy.copy(source_cell.protection)

        # Copy merged cells exactly as in template
        for merged_range in template_sheet.merged_cells.ranges:
            try:
                ws.merge_cells(str(merged_range))
            except ValueError:
                # 이미 병합된 경우 무시
                pass

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
        ws['C2'] = f"{data_month} {specific_allowance['name']} 수당 명세서"
        ws['D4'] = user_summary['name']
        ws['G4'] = user_summary.get('user_id', '')
        ws['D3'] = company_name

        ws['D5'] = user_summary.get('department', '')
        ws['G5'] = user_summary.get('position', '')
        ws['D6'] = user_summary.get('hire_date', '')
        ws['G6'] = user_summary.get('payment_date', '')

        # 병합 셀들을 먼저 해제하고 값을 설정
        try:
            ws.unmerge_cells('C9:D9')  # 기본급 병합 해제
            ws.unmerge_cells('E9:H9')  # 국민연금 병합 해제
            ws.unmerge_cells('E10:H10')  # 건강보험 병합 해제
            ws.unmerge_cells('C11:D11')  # 연장근로수당 병합 해제
            ws.unmerge_cells('E11:H11')  # 고용보험 병합 해제
            ws.unmerge_cells('C12:D12')  # 야간근로수당 병합 해제
            ws.unmerge_cells('E12:H12')  # 장기요양보험 병합 해제
            ws.unmerge_cells('C13:D13')  # 휴일근로수당 병합 해제
            ws.unmerge_cells('E13:H13')  # 소득세 병합 해제
            ws.unmerge_cells('C14:D14')  # 주휴수당 병합 해제
            ws.unmerge_cells('E14:H14')  # 지방소득세 병합 해제
            ws.unmerge_cells('C15:D15')  # 직급수당 병합 해제
            ws.unmerge_cells('C16:D16')  # 기타수당 병합 해제
            ws.unmerge_cells('C17:D17')  # 지급합계 병합 해제
            ws.unmerge_cells('E17:H17')  # 공제합계 병합 해제
            ws.unmerge_cells('C18:D18')  # 실수령액 병합 해제
        except ValueError:
            pass  # 이미 병합 해제된 경우

        # 특정 수당만 적용 (기본급 + 특정 수당)
        base_pay = float(user_summary.get('base_pay', 0))
        overtime_pay = float(user_summary.get('연장수당', 0))
        night_pay = float(user_summary.get('night_pay', 0))
        holiday_pay = float(user_summary.get('weekly_holiday_allowance', 0))
        specific_allowance_amount = float(specific_allowance['amount'])

        # 기본급과 고정 수당들만 적용
        ws['D9'] = base_pay  # 기본급
        ws['D11'] = overtime_pay  # 연장근로수당
        ws['D12'] = night_pay  # 야간근로수당
        ws['D13'] = 0.0  # 휴일근로수당
        ws['D14'] = holiday_pay  # 주휴수당
        ws['D15'] = 0  # 직급수당 (0)
        ws['D16'] = specific_allowance_amount  # 특정 수당만 기타수당으로

        # 공제 항목 설정 (기본 공제만 적용)
        ws['H9'] = 0  # 국민연금
        ws['H10'] = 0  # 건강보험
        ws['H11'] = 0  # 고용보험
        ws['H12'] = 0  # 장기요양보험
        ws['H13'] = 0  # 소득세
        ws['H14'] = 0  # 지방소득세

        # 총 공제액
        total_deduction = 0
        ws['H17'] = total_deduction  # 공제합계

        # 총 지급액 계산
        total_payment = base_pay + overtime_pay + night_pay + holiday_pay + specific_allowance_amount
        ws['D17'] = total_payment  # 지급합계

        # 실지급액 계산
        net_pay = total_payment - total_deduction
        ws['D18'] = net_pay  # 실지급액

        # 추가 정보 설정
        ws['C23'] = int(user_summary.get('연장시간_분', 0))
        ws['D23'] = int(user_summary.get('심야시간_분', 0))
        ws['E23'] = 0

        # 시급 표시
        unique_rates = [user_summary.get('hourly_rate', 0)]
        if len(unique_rates) > 1:
            rate_strings = [f"{int(rate):,}원" for rate in unique_rates]
            ws['G23'] = ', '.join(rate_strings)
        else:
            ws['G23'] = float(unique_rates[0]) if unique_rates else 0

    try:
        result_wb.save(output_filename)
        logging.info(f"Successfully generated allowance-specific payslip at '{output_filename}'")
    except Exception as e:
        logging.error(f"Error saving file: {e}", exc_info=True)
        raise Exception(f"파일 저장 중 오류가 발생했습니다: {e}")
