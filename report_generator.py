#!/usr/bin/env python3
"""
급여 보고서 생성기
회사별/사업장별 급여 통계 및 보고서 생성
"""

import json
import pandas as pd
from datetime import datetime
import os
from typing import Dict, List, Any
from logic import load_and_preprocess_data, calculate_salary, create_user_summaries


class PayrollReportGenerator:
    """급여 보고서 생성기 클래스"""

    def __init__(self):
        self.company_data = {}
        self.employee_data = {}
        self.load_base_data()

    def load_base_data(self):
        """기본 데이터 로드"""
        try:
            # config.json에서 회사 정보 로드
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.company_data = config_data.get('companies', {})

            # employees.json에서 직원 정보 로드
            if os.path.exists('employees.json'):
                with open('employees.json', 'r', encoding='utf-8') as f:
                    employee_data = json.load(f)
                self.employee_data = employee_data.get('employees', {})

        except Exception as e:
            print(f"기본 데이터 로드 오류: {e}")

    def generate_company_report(self, file_path: str, year_month: str) -> Dict[str, Any]:
        """회사별 급여 보고서 생성"""
        try:
            # 데이터 로드 및 계산
            year_val = int(year_month.split('-')[0])
            month_val = int(year_month.split('-')[1])
            df = load_and_preprocess_data(file_path, target_month=month_val, target_year=year_val)
            df_calculated = calculate_salary(df, self.employee_data, target_year_month=year_month)
            summaries = create_user_summaries(df_calculated, self.employee_data)

            # 회사별 그룹화
            company_reports = {}

            for _, employee in summaries.iterrows():
                emp_id = str(employee['user_id'])
                company_id = None

                # 직원 회사 정보 찾기
                if emp_id in self.employee_data:
                    company_id = self.employee_data[emp_id].get('company_id', 'company_001')

                # 회사 정보가 없으면 기본 회사 사용
                if not company_id or company_id not in self.company_data:
                    company_id = 'company_001'

                if company_id not in company_reports:
                    company_info = self.company_data.get(company_id, {})
                    company_reports[company_id] = {
                        'company_info': company_info,
                        'employees': [],
                        'totals': {
                            'total_pay': 0,
                            'overtime_pay': 0,
                            'night_pay': 0,
                            'holiday_pay': 0,
                            'deductions': 0,
                            'net_pay': 0,
                            'employee_count': 0
                        }
                    }

                # 직원 정보 추가
                company_reports[company_id]['employees'].append({
                    'name': employee['name'],
                    'base_pay': employee.get('base_pay', 0),
                    'overtime_pay': employee.get('연장수당', 0),
                    'night_pay': employee.get('night_pay', 0),
                    'holiday_pay': employee.get('weekly_holiday_allowance', 0),
                    'total_pay': employee.get('총급여액', 0),
                    'deductions': employee.get('deductions', 0),
                    'net_pay': employee.get('net_pay', 0)
                })

                # 합계 계산
                totals = company_reports[company_id]['totals']
                totals['total_pay'] += employee.get('총급여액', 0)
                totals['overtime_pay'] += employee.get('연장수당', 0)
                totals['night_pay'] += employee.get('night_pay', 0)
                totals['holiday_pay'] += employee.get('weekly_holiday_allowance', 0)
                totals['deductions'] += employee.get('deductions', 0)
                totals['net_pay'] += employee.get('net_pay', 0)
                totals['employee_count'] += 1

            return {
                'success': True,
                'report_date': year_month,
                'company_reports': company_reports,
                'summary': self._generate_summary(company_reports)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'report_date': year_month
            }

    def generate_business_size_report(self, file_path: str, year_month: str) -> Dict[str, Any]:
        """사업장 규모별 급여 보고서 생성"""
        try:
            # 데이터 로드 및 계산
            year_val = int(year_month.split('-')[0])
            month_val = int(year_month.split('-')[1])
            df = load_and_preprocess_data(file_path, target_month=month_val, target_year=year_val)
            df_calculated = calculate_salary(df, self.employee_data, target_year_month=year_month)
            summaries = create_user_summaries(df_calculated, self.employee_data)

            # 사업장 규모별 그룹화
            business_size_reports = {
                'over_5': {'name': '5인 이상 사업장', 'employees': [], 'totals': self._init_totals()},
                'under_5': {'name': '5인 미만 사업장', 'employees': [], 'totals': self._init_totals()}
            }

            for _, employee in summaries.iterrows():
                emp_id = str(employee['user_id'])
                business_size = 'over_5'  # 기본값

                # 직원 사업장 규모 정보 찾기
                if emp_id in self.employee_data:
                    emp_info = self.employee_data[emp_id]
                    # 회사 정보를 통해 사업장 규모 확인
                    company_id = emp_info.get('company_id')
                    if company_id and company_id in self.company_data:
                        business_size = self.company_data[company_id].get('business_size', 'over_5')
                    else:
                        business_size = emp_info.get('business_size', 'over_5')

                # 직원 정보 추가
                employee_data = {
                    'name': employee['name'],
                    'company': self._get_employee_company_name(emp_id),
                    'base_pay': employee.get('base_pay', 0),
                    'overtime_pay': employee.get('연장수당', 0),
                    'night_pay': employee.get('night_pay', 0),
                    'holiday_pay': employee.get('weekly_holiday_allowance', 0),
                    'total_pay': employee.get('총급여액', 0),
                    'deductions': employee.get('deductions', 0),
                    'net_pay': employee.get('net_pay', 0)
                }

                business_size_reports[business_size]['employees'].append(employee_data)

                # 합계 계산
                totals = business_size_reports[business_size]['totals']
                totals['total_pay'] += employee.get('총급여액', 0)
                totals['overtime_pay'] += employee.get('연장수당', 0)
                totals['night_pay'] += employee.get('night_pay', 0)
                totals['holiday_pay'] += employee.get('weekly_holiday_allowance', 0)
                totals['deductions'] += employee.get('deductions', 0)
                totals['net_pay'] += employee.get('net_pay', 0)
                totals['employee_count'] += 1

            return {
                'success': True,
                'report_date': year_month,
                'business_size_reports': business_size_reports,
                'summary': self._generate_business_size_summary(business_size_reports)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'report_date': year_month
            }

    def _init_totals(self) -> Dict[str, float]:
        """합계 초기화"""
        return {
            'total_pay': 0,
            'overtime_pay': 0,
            'night_pay': 0,
            'holiday_pay': 0,
            'deductions': 0,
            'net_pay': 0,
            'employee_count': 0
        }

    def _get_employee_company_name(self, emp_id: str) -> str:
        """직원 회사명 조회"""
        if emp_id in self.employee_data:
            company_id = self.employee_data[emp_id].get('company_id')
            if company_id and company_id in self.company_data:
                return self.company_data[company_id].get('name', '미지정')
        return '미지정'

    def _generate_summary(self, company_reports: Dict) -> Dict[str, Any]:
        """회사별 보고서 요약 생성"""
        total_employees = 0
        total_payroll = 0
        total_deductions = 0
        total_net_pay = 0

        for company_report in company_reports.values():
            totals = company_report['totals']
            total_employees += totals['employee_count']
            total_payroll += totals['total_pay']
            total_deductions += totals['deductions']
            total_net_pay += totals['net_pay']

        return {
            'total_companies': len(company_reports),
            'total_employees': total_employees,
            'total_payroll': total_payroll,
            'total_deductions': total_deductions,
            'total_net_pay': total_net_pay,
            'average_payroll_per_employee': total_payroll / total_employees if total_employees > 0 else 0
        }

    def _generate_business_size_summary(self, business_size_reports: Dict) -> Dict[str, Any]:
        """사업장 규모별 보고서 요약 생성"""
        summary = {}

        for size_key, report in business_size_reports.items():
            totals = report['totals']
            summary[size_key] = {
                'name': report['name'],
                'employee_count': totals['employee_count'],
                'total_payroll': totals['total_pay'],
                'overtime_pay': totals['overtime_pay'],
                'average_overtime_pay': totals['overtime_pay'] / totals['employee_count'] if totals['employee_count'] > 0 else 0
            }

        return summary

    def export_report_to_excel(self, report_data: Dict, filename: str) -> bool:
        """보고서를 Excel 파일로 내보내기"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 회사별 보고서
                if 'company_reports' in report_data:
                    for company_id, company_data in report_data['company_reports'].items():
                        company_name = company_data['company_info'].get('name', company_id)

                        # 직원별 상세
                        employees_df = pd.DataFrame(company_data['employees'])
                        employees_df.to_excel(writer, sheet_name=f'{company_name[:10]}', index=False)

                        # 회사 합계
                        totals_df = pd.DataFrame([company_data['totals']])
                        totals_df.to_excel(writer, sheet_name=f'{company_name[:10]}_합계', index=False)

                # 사업장 규모별 보고서
                elif 'business_size_reports' in report_data:
                    for size_key, size_data in report_data['business_size_reports'].items():
                        size_name = size_data['name']

                        # 직원별 상세
                        employees_df = pd.DataFrame(size_data['employees'])
                        employees_df.to_excel(writer, sheet_name=f'{size_name}', index=False)

                        # 규모별 합계
                        totals_df = pd.DataFrame([size_data['totals']])
                        totals_df.to_excel(writer, sheet_name=f'{size_name}_합계', index=False)

                # 요약 시트
                if 'summary' in report_data:
                    summary_df = pd.DataFrame([report_data['summary']])
                    summary_df.to_excel(writer, sheet_name='요약', index=False)

            return True

        except Exception as e:
            print(f"Excel 내보내기 오류: {e}")
            return False


# 테스트 함수
def test_reports():
    """보고서 생성 테스트"""
    generator = PayrollReportGenerator()

    # 회사별 보고서 테스트
    company_report = generator.generate_company_report('tutorial_data-편집버전.xlsx', '2025-10')
    print("=== 회사별 보고서 ===")
    print(f"성공: {company_report['success']}")
    if company_report['success']:
        print(f"회사 수: {len(company_report['company_reports'])}")
        for company_id, data in company_report['company_reports'].items():
            print(f"회사: {data['company_info'].get('name', company_id)}")
            print(f"직원 수: {data['totals']['employee_count']}")
            print(f"총 급여: {data['totals']['total_pay']:,.0f}원")

    # 사업장 규모별 보고서 테스트
    business_report = generator.generate_business_size_report('tutorial_data-편집버전.xlsx', '2025-10')
    print("\n=== 사업장 규모별 보고서 ===")
    print(f"성공: {business_report['success']}")
    if business_report['success']:
        for size_key, data in business_report['business_size_reports'].items():
            print(f"규모: {data['name']}")
            print(f"직원 수: {data['totals']['employee_count']}")
            print(f"연장수당 합계: {data['totals']['overtime_pay']:,.0f}원")


if __name__ == "__main__":
    test_reports()
