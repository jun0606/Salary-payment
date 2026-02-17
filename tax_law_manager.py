#!/usr/bin/env python3
"""
세법 기준 관리 모듈
연도별 세법 기준을 관리하고 계산에 사용합니다.
"""

import json
import os
import logging
from typing import Dict, Any, Optional

class TaxLawManager:
    """세법 기준 관리 클래스"""

    # 기본 세법 기준 데이터 (2024-2026년)
    DEFAULT_TAX_LAW_STANDARDS = {
        "2024": {
            "name": "2024년 세법 기준",
            "holiday_allowance_hours": 15,
            "daily_standard_hours": 8,
            "weekly_standard_hours": 40,
            "overtime_multiplier": 1.5,
            "minimum_wage": 9860,
            "insurance_rates": {
                "national_pension": 0.045,
                "health_insurance": 0.03545,
                "long_term_care": 0.1281,
                "employment_insurance": 0.009
            },
            "income_tax_brackets": [
                {"min": 0, "max": 12000000, "rate": 0.06, "deduction": 0},
                {"min": 12000000, "max": 46000000, "rate": 0.15, "deduction": 1080000},
                {"min": 46000000, "max": 88000000, "rate": 0.24, "deduction": 5220000},
                {"min": 88000000, "max": 150000000, "rate": 0.35, "deduction": 14900000},
                {"min": 150000000, "max": 300000000, "rate": 0.38, "deduction": 19400000},
                {"min": 300000000, "max": 500000000, "rate": 0.40, "deduction": 25400000},
                {"min": 500000000, "max": float('inf'), "rate": 0.42, "deduction": 35400000}
            ],
            "non_eligible_rates": {
                "income_tax": 0.03,
                "local_income_tax": 0.003
            },
            "basic_deduction": 1500000
        },
        "2025": {
            "name": "2025년 세법 기준",
            "holiday_allowance_hours": 15,
            "daily_standard_hours": 8,
            "weekly_standard_hours": 40,
            "overtime_multiplier": 1.5,
            "minimum_wage": 10030,
            "insurance_rates": {
                "national_pension": 0.045,
                "health_insurance": 0.03545,
                "long_term_care": 0.1281,
                "employment_insurance": 0.009
            },
            "income_tax_brackets": [
                {"min": 0, "max": 12000000, "rate": 0.06, "deduction": 0},
                {"min": 12000000, "max": 46000000, "rate": 0.15, "deduction": 1080000},
                {"min": 46000000, "max": 88000000, "rate": 0.24, "deduction": 5220000},
                {"min": 88000000, "max": 150000000, "rate": 0.35, "deduction": 14900000},
                {"min": 150000000, "max": 300000000, "rate": 0.38, "deduction": 19400000},
                {"min": 300000000, "max": 500000000, "rate": 0.40, "deduction": 25400000},
                {"min": 500000000, "max": float('inf'), "rate": 0.42, "deduction": 35400000}
            ],
            "non_eligible_rates": {
                "income_tax": 0.03,
                "local_income_tax": 0.003
            },
            "basic_deduction": 1500000
        },
        "2026": {
            "name": "2026년 세법 기준",
            "holiday_allowance_hours": 15,
            "daily_standard_hours": 8,
            "weekly_standard_hours": 40,
            "overtime_multiplier": 1.5,
            "minimum_wage": 10320,
            "insurance_rates": {
                "national_pension": 0.0475,
                "health_insurance": 0.03595,
                "long_term_care": 0.1281,
                "employment_insurance": 0.009
            },
            "income_tax_brackets": [
                {"min": 0, "max": 12000000, "rate": 0.06, "deduction": 0},
                {"min": 12000000, "max": 46000000, "rate": 0.15, "deduction": 1080000},
                {"min": 46000000, "max": 88000000, "rate": 0.24, "deduction": 5220000},
                {"min": 88000000, "max": 150000000, "rate": 0.35, "deduction": 14900000},
                {"min": 150000000, "max": 300000000, "rate": 0.38, "deduction": 19400000},
                {"min": 300000000, "max": 500000000, "rate": 0.40, "deduction": 25400000},
                {"min": 500000000, "max": float('inf'), "rate": 0.42, "deduction": 35400000}
            ],
            "non_eligible_rates": {
                "income_tax": 0.03,
                "local_income_tax": 0.003
            },
            "basic_deduction": 1500000
        }
    }

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.standards = {}
        self.load_standards()

    def load_standards(self):
        """설정 파일에서 세법 기준 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.standards = config.get("tax_law_standards", {})
            else:
                logging.warning(f"설정 파일이 존재하지 않습니다: {self.config_file}")
                self.standards = {}
        except Exception as e:
            logging.error(f"세법 기준 로드 실패: {e}")
            self.standards = {}

        # 기본값으로 초기화되지 않은 연도가 있다면 추가
        for year, default_data in self.DEFAULT_TAX_LAW_STANDARDS.items():
            if year not in self.standards:
                self.standards[year] = default_data.copy()

        self.save_standards()

    def save_standards(self):
        """세법 기준을 설정 파일에 저장"""
        try:
            # 기존 설정 로드
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 세법 기준 업데이트
            config["tax_law_standards"] = self.standards

            # 저장
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logging.info("세법 기준 저장 완료")
        except Exception as e:
            logging.error(f"세법 기준 저장 실패: {e}")
            raise

    def get_standards_for_year(self, year: str) -> Dict[str, Any]:
        """특정 연도의 세법 기준 반환"""
        if year in self.standards:
            return self.standards[year].copy()
        else:
            # 존재하지 않는 연도라면 가장 가까운 연도의 데이터를 반환
            available_years = sorted(self.standards.keys(), key=int)
            for available_year in reversed(available_years):
                if int(available_year) <= int(year):
                    logging.warning(f"연도 {year}의 세법 기준이 없어 {available_year}년 기준을 사용합니다.")
                    return self.standards[available_year].copy()

            # 아무것도 없으면 기본값 사용
            logging.warning(f"사용 가능한 세법 기준이 없어 기본값을 사용합니다.")
            return self.DEFAULT_TAX_LAW_STANDARDS["2026"].copy()

    def set_standards_for_year(self, year: str, standards: Dict[str, Any]):
        """특정 연도의 세법 기준 설정"""
        self.standards[year] = standards.copy()
        self.save_standards()

    def get_available_years(self) -> list:
        """사용 가능한 연도 목록 반환"""
        return sorted(self.standards.keys(), key=int)

    def add_year(self, year: str, template_year: Optional[str] = None):
        """새 연도 추가"""
        if year in self.standards:
            raise ValueError(f"연도 {year}는 이미 존재합니다.")

        # 템플릿 연도가 지정되지 않았다면 가장 최근 연도를 템플릿으로 사용
        if template_year is None:
            available_years = self.get_available_years()
            template_year = available_years[-1] if available_years else "2026"

        if template_year not in self.standards:
            raise ValueError(f"템플릿 연도 {template_year}가 존재하지 않습니다.")

        # 템플릿 복사
        new_standards = self.standards[template_year].copy()
        new_standards["name"] = f"{year}년 세법 기준"

        self.standards[year] = new_standards
        self.save_standards()

    def remove_year(self, year: str):
        """연도 삭제"""
        if year not in self.standards:
            raise ValueError(f"연도 {year}가 존재하지 않습니다.")

        if len(self.standards) <= 1:
            raise ValueError("최소 하나의 연도 데이터는 유지해야 합니다.")

        del self.standards[year]
        self.save_standards()

    def validate_standards(self, standards: Dict[str, Any]) -> bool:
        """세법 기준 데이터 유효성 검증"""
        required_keys = [
            "holiday_allowance_hours", "daily_standard_hours", "weekly_standard_hours",
            "overtime_multiplier", "minimum_wage", "insurance_rates", "income_tax_brackets",
            "non_eligible_rates", "basic_deduction"
        ]

        for key in required_keys:
            if key not in standards:
                return False

        # insurance_rates 검증
        required_insurance = ["national_pension", "health_insurance", "long_term_care", "employment_insurance"]
        for rate_key in required_insurance:
            if rate_key not in standards["insurance_rates"]:
                return False

        return True
