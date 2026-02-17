#!/usr/bin/env python3
"""
급여대장 생성 모듈
데이터베이스에서 급여 데이터를 조회하여 엑셀 형식의 급여대장 생성
"""

import os
import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from database_manager import get_database
from bs4 import BeautifulSoup


def generate_payroll_register(company_name: str, year: str) -> Optional[str]:
    """
    급여대장을 생성하여 엑셀 파일로 저장

    Args:
        company_name: 회사명
        year: 대상 연도 (YYYY)

    Returns:
        Optional[str]: 생성된 파일 경로 (실패 시 None)
    """
    try:
        print(f"급여대장 생성 시작: {company_name}, {year}년")

        # 1. 데이터베이스에서 급여 데이터 조회
        payroll_data = get_yearly_payroll_data(company_name, year)
        if not payroll_data:
            print(f"급여 데이터가 없습니다: {company_name}, {year}년")
            return None

        # 2. 데이터 집계 및 구조화
        register_data = process_payroll_data(payroll_data, year)

        # 3. 엑셀 파일 생성
        file_path = create_payroll_register_excel(register_data, company_name, year)

        print(f"급여대장 생성 완료: {file_path}")
        return file_path

    except Exception as e:
        print(f"급여대장 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_yearly_payroll_data(company_name: str, year: str) -> List[Dict]:
    """
    데이터베이스에서 특정 회사/연도의 급여 데이터를 조회

    Args:
        company_name: 회사명
        year: 연도 (YYYY)

    Returns:
        List[Dict]: 급여 데이터 리스트
    """
    try:
        db = get_database()

        # 해당 연도의 모든 월별 데이터 조회
        filters = {
            'company_name': company_name,
            'year': year
        }

        records = db.get_payslip_records(filters=filters, limit=1000)
        print(f"데이터베이스 조회 결과: {len(records)}건")

        # 조회된 데이터 구조 확인
        if records:
            print(f"샘플 데이터 구조: {records[0].keys()}")
            print(f"샘플 회사명: {records[0].get('company_name')}")
            print(f"샘플 연월: {records[0].get('pay_month')}")
            html_content = records[0].get('html_content') or ''
            print(f"HTML 내용 길이: {len(html_content)}")

        return records

    except Exception as e:
        print(f"급여 데이터 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        return []


def process_payroll_data(records: List[Dict], year: str) -> Dict:
    """
    급여 데이터를 처리하여 급여대장 형식으로 구조화

    Args:
        records: 데이터베이스에서 조회한 급여 기록들
        year: 대상 연도

    Returns:
        Dict: 구조화된 급여대장 데이터
    """
    # 직원별 월별 데이터 집계
    employee_data = {}

    for record in records:
        try:
            # HTML 콘텐츠 가져오기 (데이터베이스에서 별도로 조회)
            html_content = record.get('html_content')
            if not html_content:
                # html_content가 없으면 get_payslip_content로 조회
                from database_manager import get_database
                db = get_database()
                html_content = db.get_payslip_content(record['id'])

            if not html_content:
                print(f"HTML 콘텐츠를 찾을 수 없음: {record.get('employee_name', 'Unknown')}")
                continue

            # HTML에서 급여 데이터 추출
            payslip_info = parse_payslip_html(html_content)
            if not payslip_info:
                print(f"HTML 파싱 실패: {record.get('employee_name', 'Unknown')}")
                continue

            employee_id = record['employee_id']
            employee_name = record['employee_name']
            pay_month = record['pay_month']  # "YYYY-MM" 형식

            # 직원 정보 초기화
            if employee_id not in employee_data:
                employee_data[employee_id] = {
                    'name': employee_name,
                    'id': employee_id,
                    'yearly_payment_total': 0,
                    'yearly_deduction_total': 0,
                    'monthly_data': {}
                }

            # 월별 데이터 저장
            month_num = int(pay_month.split('-')[1])  # MM 추출
            employee_data[employee_id]['monthly_data'][month_num] = {
                'payment': payslip_info.get('total_payment', 0),
                'deduction': payslip_info.get('total_deduction', 0)
            }

        except Exception as e:
            print(f"급여 데이터 처리 오류 (직원: {record.get('employee_name', 'Unknown')}): {e}")
            continue

    # 연간 합계 계산
    for employee_id, data in employee_data.items():
        yearly_payment = 0
        yearly_deduction = 0

        for month in range(1, 13):
            monthly = data['monthly_data'].get(month, {})
            yearly_payment += monthly.get('payment', 0)
            yearly_deduction += monthly.get('deduction', 0)

        data['yearly_payment_total'] = yearly_payment
        data['yearly_deduction_total'] = yearly_deduction

    return {
        'year': year,
        'employees': list(employee_data.values())
    }


def parse_payslip_html(html_content: str) -> Optional[Dict]:
    """
    HTML 급여명세서에서 급여 데이터를 추출

    Args:
        html_content: HTML 문자열

    Returns:
        Optional[Dict]: 추출된 급여 데이터
    """
    try:
        # 입력 검증
        if not html_content or not isinstance(html_content, str):
            print(f"HTML 파싱 오류: 유효하지 않은 HTML 내용 (type: {type(html_content)})")
            return None

        soup = BeautifulSoup(html_content, 'html.parser')

        data = {
            'total_payment': 0,
            'total_deduction': 0
        }

        # 급여 테이블 찾기
        salary_table = soup.find('table', class_='salary-table')
        if not salary_table:
            print("HTML 파싱 오류: salary-table을 찾을 수 없음")
            return None

        # 테이블의 모든 행 찾기
        rows = salary_table.find_all('tr')
        if not rows or len(rows) < 2:
            print(f"HTML 파싱 오류: 테이블 행이 부족함 (rows: {len(rows) if rows else 0})")
            return None

        # 합계 행 찾기 (total-row 클래스)
        total_row = None
        for row in rows:
            if row and 'total-row' in row.get('class', []):
                total_row = row
                break

        if not total_row:
            print("HTML 파싱 오류: total-row를 찾을 수 없음")
            return None

        # 합계 행의 셀들 찾기
        cells = total_row.find_all('td')
        if not cells or len(cells) < 4:
            print(f"HTML 파싱 오류: 합계 행 셀이 부족함 (cells: {len(cells) if cells else 0})")
            return None

        # 지급 합계와 공제 합계 추출 (인덱스 1과 3)
        if len(cells) > 1:
            payment_text = cells[1].get_text(strip=True).replace(',', '').replace('원', '')
            try:
                data['total_payment'] = int(payment_text) if payment_text.isdigit() else 0
            except (ValueError, AttributeError) as e:
                print(f"지급 합계 파싱 오류: {e}")
                data['total_payment'] = 0

        if len(cells) > 3:
            deduction_text = cells[3].get_text(strip=True).replace(',', '').replace('원', '')
            try:
                data['total_deduction'] = int(deduction_text) if deduction_text.isdigit() else 0
            except (ValueError, AttributeError) as e:
                print(f"공제 합계 파싱 오류: {e}")
                data['total_deduction'] = 0

        print(f"HTML 파싱 성공: 지급={data['total_payment']}, 공제={data['total_deduction']}")
        return data

    except Exception as e:
        print(f"HTML 파싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_payroll_register_excel(register_data: Dict, company_name: str, year: str) -> str:
    """
    급여대장 데이터를 엑셀 파일로 생성

    Args:
        register_data: 구조화된 급여대장 데이터
        company_name: 회사명
        year: 연도

    Returns:
        str: 생성된 파일 경로
    """
    try:
        # 워크북 생성
        wb = Workbook()
        ws = wb.active
        ws.title = f"{year}년_급여대장"

        # 스타일 정의
        header_font = Font(bold=True, size=12)
        normal_font = Font(size=10)
        title_font = Font(bold=True, size=14)

        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        header_fill = PatternFill(start_color="FFE6E6FA", end_color="FFE6E6FA", fill_type="solid")

        # 제목 행
        ws['A1'] = f"{company_name} {year}년 급여대장"
        ws['A1'].font = title_font
        ws.merge_cells('A1:AC1')  # A부터 AC까지 병합 (29열)
        ws['A1'].alignment = Alignment(horizontal='center')

        # 헤더 행 (3행)
        headers = [
            "직원이름", "사용자ID", "년지급총액", "년공제총액"
        ]

        # 월별 헤더 추가
        for month in range(1, 13):
            headers.extend([f"{month}월급여", f"{month}월공제"])

        # 헤더 작성
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col_num)
            cell.value = header
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
            cell.fill = header_fill

        # 데이터 행 작성
        row_num = 4  # 4행부터 데이터
        employees = register_data.get('employees', [])

        for employee in employees:
            # 기본 정보
            ws.cell(row=row_num, column=1).value = employee['name']
            ws.cell(row=row_num, column=2).value = employee['id']
            ws.cell(row=row_num, column=3).value = employee['yearly_payment_total']
            ws.cell(row=row_num, column=4).value = employee['yearly_deduction_total']

            # 월별 데이터
            monthly_data = employee.get('monthly_data', {})
            for month in range(1, 13):
                payment_col = 4 + (month - 1) * 2 + 1  # 5, 7, 9, ... 열
                deduction_col = payment_col + 1         # 6, 8, 10, ... 열

                monthly = monthly_data.get(month, {})
                payment = monthly.get('payment', 0)
                deduction = monthly.get('deduction', 0)

                ws.cell(row=row_num, column=payment_col).value = payment
                ws.cell(row=row_num, column=deduction_col).value = deduction

            # 행 스타일 적용
            for col in range(1, 29):  # A부터 AC까지 (28열)
                cell = ws.cell(row=row_num, column=col)
                cell.font = normal_font
                cell.border = border
                cell.alignment = Alignment(horizontal='right') if col > 2 else Alignment(horizontal='center')

                # 금액 셀에 숫자 포맷 적용
                if col >= 3:
                    cell.number_format = '#,##0'

            row_num += 1

        # 열 너비 설정
        from openpyxl.utils import get_column_letter

        for col in range(1, 29):
            col_letter = get_column_letter(col)
            ws.column_dimensions[col_letter].width = 12

        # 특정 열 너비 조정
        ws.column_dimensions['A'].width = 15  # 직원이름
        ws.column_dimensions['B'].width = 12  # 사용자ID

        # 파일 저장
        output_dir = "급여대장_생성본"
        year_dir = os.path.join(output_dir, f"{year}년")
        os.makedirs(year_dir, exist_ok=True)

        safe_company_name = company_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
        filename = f"{safe_company_name}_{year}년_급여대장.xlsx"
        file_path = os.path.join(year_dir, filename)

        wb.save(file_path)
        wb.close()

        return file_path

    except Exception as e:
        print(f"엑셀 파일 생성 오류: {e}")
        raise