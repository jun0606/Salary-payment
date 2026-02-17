#!/usr/bin/env python3
"""
PyQt6 기반 급여대장 생성 다이얼로그
회사와 년도를 선택하여 급여대장을 생성하는 팝업 창
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QDialogButtonBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import datetime
import os
import json


class PayrollRegisterDialog(QDialog):
    """
    급여대장 생성을 위한 회사/년도 선택 다이얼로그
    """

    def __init__(self, app_instance, parent=None):
        super().__init__(parent)
        self.app = app_instance

        self.setWindowTitle("급여대장 생성")
        self.setModal(True)
        self.setFixedSize(450, 320)  # 대화상자 크기 증가

        # 선택된 옵션 저장
        self.selected_company = ""
        self.selected_year = ""

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # 제목
        title_label = QLabel("급여대장 생성 옵션")
        title_label.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 회사 선택 그룹
        company_group = QGroupBox("회사 선택")
        company_layout = QVBoxLayout(company_group)

        self.company_combo = QComboBox()
        self.company_combo.setMinimumWidth(300)  # 너비 증가
        self.company_combo.setMinimumHeight(40)  # 높이 증가
        self.company_combo.setFont(QFont("맑은 고딕", 12))  # 폰트 크기 증가
        self.company_combo.setStyleSheet("""
            QComboBox {
                min-height: 30px;
                font-size: 11px;
            }
        """)
        self.load_available_companies()
        company_layout.addWidget(self.company_combo)

        layout.addWidget(company_group)

        # 년도 선택 그룹
        year_group = QGroupBox("년도 선택")
        year_layout = QVBoxLayout(year_group)

        self.year_combo = QComboBox()
        self.year_combo.setMinimumWidth(300)  # 너비 증가
        self.year_combo.setMinimumHeight(40)  # 높이 증가
        self.year_combo.setFont(QFont("맑은 고딕", 12))  # 폰트 크기 증가
        self.year_combo.setStyleSheet("""
            QComboBox {
                min-height: 30px;
                font-size: 11px;
            }
        """)
        self.load_available_years()
        year_layout.addWidget(self.year_combo)

        layout.addWidget(year_group)

        # 설명 텍스트
        description_label = QLabel(
            "선택된 회사와 년도의 급여 데이터를 기반으로\n"
            "엑셀 형식의 급여대장을 생성합니다."
        )
        description_label.setStyleSheet("color: #666; font-size: 11px;")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label)

        # 버튼 박스
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)



    def load_available_companies(self):
        """설정 파일에서 회사 목록 로드"""
        try:
            companies = []

            # config.json에서 회사 정보 로드
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                company_data = config_data.get('companies', {})
                for company_id, company_info in company_data.items():
                    company_name = company_info.get("name", company_id)
                    if company_name:
                        companies.append(company_name)

            # 회사 목록이 없으면 기본 회사 추가
            if not companies:
                companies = ["기본 회사"]

            # 콤보박스에 추가
            self.company_combo.clear()
            self.company_combo.addItems(companies)

            # 현재 선택된 회사가 있으면 선택
            current_company = self.app.config_data.get("company_name", "")
            if current_company and current_company in companies:
                self.company_combo.setCurrentText(current_company)
            else:
                # 기본 선택 (첫 번째 항목)
                if companies:
                    self.company_combo.setCurrentIndex(0)

        except Exception as e:
            print(f"회사 목록 로드 오류: {e}")
            self.company_combo.clear()
            self.company_combo.addItem("기본 회사")

    def load_available_years(self):
        """사용 가능한 년도 목록 로드 (데이터베이스의 실제 연도)"""
        try:
            # 데이터베이스에서 실제 저장된 연도들 조회
            from database_manager import get_database
            db = get_database()

            # 모든 급여 기록에서 연도 추출 (제한 없이)
            records = db.get_payslip_records(limit=10000)  # 충분히 큰 limit
            years = set()

            for record in records:
                pay_month = record.get('pay_month', '')
                if pay_month and '-' in pay_month:
                    year_part = pay_month.split('-')[0]
                    if year_part.isdigit():
                        years.add(int(year_part))

            # 연도를 정렬해서 콤보박스에 추가 (최신 연도가 먼저)
            sorted_years = sorted(years, reverse=True)
            self.year_combo.clear()

            if sorted_years:
                self.year_combo.addItems([str(year) for year in sorted_years])
                # 기본 선택: 가장 최신 연도
                self.year_combo.setCurrentText(str(sorted_years[0]))
                print(f"년도 로드 완료: {sorted_years} (기본 선택: {sorted_years[0]})")
            else:
                # 데이터가 없는 경우 현재 연도 표시
                current_year = datetime.datetime.now().year
                self.year_combo.clear()
                self.year_combo.addItem(str(current_year))
                self.year_combo.setCurrentText(str(current_year))
                print(f"년도 데이터 없음: 현재 연도 {current_year} 표시")

        except Exception as e:
            print(f"년도 목록 로드 오류: {e}")
            import traceback
            traceback.print_exc()

            # 오류 시 현재 연도만 표시
            current_year = datetime.datetime.now().year
            self.year_combo.clear()
            self.year_combo.addItem(str(current_year))
            self.year_combo.setCurrentText(str(current_year))



    def get_selected_options(self):
        """선택된 회사와 년도를 반환"""
        self.selected_company = self.company_combo.currentText()
        self.selected_year = self.year_combo.currentText()
        return self.selected_company, self.selected_year

    def accept(self):
        """확인 버튼 클릭 시 선택 값 검증"""
        company = self.company_combo.currentText()
        year = self.year_combo.currentText()

        if not company:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "입력 오류", "회사를 선택해주세요.")
            return

        if not year:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "입력 오류", "년도를 선택해주세요.")
            return

        # 선택 값 저장
        self.selected_company = company
        self.selected_year = year

        super().accept()
