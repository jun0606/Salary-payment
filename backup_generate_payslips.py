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