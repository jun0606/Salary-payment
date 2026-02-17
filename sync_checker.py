#!/usr/bin/env python3
"""
템플릿과 로직 간 변수 동기화를 검증하는 시스템
"""

import re
import os
from jinja2 import Environment, DictLoader
from logic import _prepare_payslip_data

class TemplateLogicSyncChecker:
    """템플릿과 로직 간 변수 동기화 검증"""
    
    def __init__(self):
        self.template_vars = self._extract_template_variables()
        self.logic_vars = self._extract_logic_variables()
    
    def _extract_template_variables(self):
        """템플릿에서 사용되는 모든 변수 추출 (개선된 버전)"""
        template_path = os.path.join(os.path.dirname(__file__), 'payslip_template.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        template_vars = set()
        
        # 패턴 1: 기본 Jinja2 변수 {{ variable }}
        basic_pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        matches = re.findall(basic_pattern, content)
        template_vars.update(matches)
        
        # 패턴 2: format() 메서드 내 변수 "{:,.0f}".format(base_pay)
        format_pattern = r'\.format\(([a-zA-Z_][a-zA-Z0-9_]*)\)'
        format_matches = re.findall(format_pattern, content)
        template_vars.update(format_matches)
        
        # 패턴 3: 조걶문 내 변수 {% if variable > 0 %}
        if_pattern = r'\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        if_matches = re.findall(if_pattern, content)
        template_vars.update(if_matches)
        
        # 패턴 4: for 반복문의 리스트 변수 {% for item in allowance_items %}
        for_list_pattern = r'\{%\s*for\s+[a-zA-Z_][a-zA-Z0-9_]*\s+in\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        for_list_matches = re.findall(for_list_pattern, content)
        template_vars.update(for_list_matches)
        
        # 패턴 5: 비교/연산 내 변수
        expr_pattern = r'\{\{\s*[a-zA-Z_][a-zA-Z0-9_]*\s*(?:>|<|==|!=|>=|<=)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        expr_matches = re.findall(expr_pattern, content)
        template_vars.update(expr_matches)
        
        # 제외할 키워드 (Jinja2 예약어 및 for 루프 임시 변수)
        exclude_keywords = {'true', 'false', 'none', 'and', 'or', 'not', 'in', 'item'}
        template_vars = template_vars - exclude_keywords
        
        return template_vars
    
    def _extract_logic_variables(self):
        """로직에서 전달하는 변수 추출"""
        # 샘플 데이터로 _prepare_payslip_data 호출
        sample_summary = {
            'name': '테스트',
            'user_id': '001',
            'department': '테스트',
            'position': '테스트',
            'hire_date': '2024-01-01',
            'payment_date': '2025-12-25',
            'base_pay': 2000000,
            'weekly_holiday_allowance': 100000,
            '연장수당': 50000,
            'night_pay': 30000,
            'national_pension': 90000,
            'health_insurance': 70000,
            'employment_insurance': 18000,
            'long_term_care_insurance': 9000,
            'income_tax': 150000,
            'local_income_tax': 15000,
            'hourly_rate': 12000,
            '근무시간_분': 1600,
            '연장시간_분': 200,
            '심야시간_분': 120,
            '주휴시간(분단위)': 480
        }
        
        payslip_data = _prepare_payslip_data(
            sample_summary,
            "2025년 12월",
            "테스트회사",
            {'night_explanation': True},
            None,
            {},
            2025,
            'under_5'
        )
        
        return set(payslip_data.keys())
    
    def validate_sync(self):
        """동기화 검증"""
        missing_in_template = self.logic_vars - self.template_vars
        missing_in_logic = self.template_vars - self.logic_vars
        
        errors = []
        
        if missing_in_template:
            errors.append(f"템플릿에 누락된 변수: {missing_in_template}")
        
        if missing_in_logic:
            errors.append(f"로직에 누락된 변수: {missing_in_logic}")
        
        if errors:
            raise SyncError("템플릿-로직 동기화 오류:\n" + "\n".join(errors))
        
        return True
    
    def get_sync_report(self):
        """동기화 보고서 생성"""
        return {
            'template_variables': sorted(list(self.template_vars)),
            'logic_variables': sorted(list(self.logic_vars)),
            'missing_in_template': sorted(list(self.logic_vars - self.template_vars)),
            'missing_in_logic': sorted(list(self.template_vars - self.logic_vars)),
            'sync_status': len(self.logic_vars - self.template_vars) == 0 and len(self.template_vars - self.logic_vars) == 0
        }

class SyncError(Exception):
    """동기화 검증 오류"""
    pass

if __name__ == "__main__":
    # 테스트 실행
    checker = TemplateLogicSyncChecker()
    
    print("=== 템플릿-로직 동기화 검증 ===")
    print(f"템플릿 변수 수: {len(checker.template_vars)}")
    print(f"로직 변수 수: {len(checker.logic_vars)}")
    
    try:
        checker.validate_sync()
        print("✅ 동기화 검증 통과")
    except SyncError as e:
        print(f"❌ 동기화 검증 실패: {e}")
    
    report = checker.get_sync_report()
    print(f"\n=== 상세 보고서 ===")
    print(f"템플릿 변수: {report['template_variables']}")
    print(f"로직 변수: {report['logic_variables']}")
    print(f"템플릿에 누락: {report['missing_in_template']}")
    print(f"로직에 누락: {report['missing_in_logic']}")
    print(f"동기화 상태: {'✅ 정상' if report['sync_status'] else '❌ 불일치'}")