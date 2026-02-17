#!/usr/bin/env python3
"""
세법 기준 설정 다이얼로그
연도별 세법 기준을 UI로 편집할 수 있는 팝업 다이얼로그
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QDoubleSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QMessageBox, QGroupBox, QFormLayout,
    QSpinBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from tax_law_manager import TaxLawManager


class TaxLawSettingsDialog(QDialog):
    """세법 기준 설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tax_manager = TaxLawManager()
        self.current_year = None

        self.setWindowTitle("세법 기준 관리")
        self.setModal(True)
        self.resize(800, 700)

        self.setup_ui()
        self.load_years()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 상단 제어 영역
        control_layout = QHBoxLayout()

        # 연도 선택 콤보박스
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("연도:"))
        self.year_combo = QComboBox()
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        year_layout.addWidget(self.year_combo)

        # 연도 추가 버튼
        add_year_btn = QPushButton("연도 추가")
        add_year_btn.clicked.connect(self.add_year)
        year_layout.addWidget(add_year_btn)

        # 연도 삭제 버튼
        remove_year_btn = QPushButton("연도 삭제")
        remove_year_btn.setStyleSheet("QPushButton { color: red; }")
        remove_year_btn.clicked.connect(self.remove_year)
        year_layout.addWidget(remove_year_btn)

        control_layout.addLayout(year_layout)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 하단 버튼 영역
        button_layout = QHBoxLayout()

        save_btn = QPushButton("저장")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save_current_year)
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def load_years(self):
        """연도 목록 로드"""
        self.year_combo.clear()
        years = self.tax_manager.get_available_years()
        self.year_combo.addItems(years)

        if years:
            self.year_combo.setCurrentText(years[-1])  # 가장 최근 연도 선택

    def on_year_changed(self, year):
        """연도 변경 시 탭 로드"""
        if not year:
            return

        self.current_year = year
        self.load_year_tab(year)

    def load_year_tab(self, year):
        """특정 연도의 탭 로드"""
        standards = self.tax_manager.get_standards_for_year(year)

        # 기존 탭 제거
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # 기본 설정 탭
        self.create_basic_settings_tab(standards)

        # 4대보험 탭
        self.create_insurance_tab(standards)

        # 소득세 탭
        self.create_income_tax_tab(standards)

        # 비대상자 탭
        self.create_non_eligible_tab(standards)

    def create_basic_settings_tab(self, standards):
        """기본 설정 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 근로시간 설정 그룹
        time_group = QGroupBox("근로시간 설정")
        time_layout = QFormLayout(time_group)

        self.holiday_hours_spin = QSpinBox()
        self.holiday_hours_spin.setRange(1, 50)
        self.holiday_hours_spin.setValue(standards.get("holiday_allowance_hours", 15))
        time_layout.addRow("주휴수당 기준 시간:", self.holiday_hours_spin)

        self.daily_hours_spin = QSpinBox()
        self.daily_hours_spin.setRange(1, 24)
        self.daily_hours_spin.setValue(standards.get("daily_standard_hours", 8))
        time_layout.addRow("일일 표준 근로시간:", self.daily_hours_spin)

        self.weekly_hours_spin = QSpinBox()
        self.weekly_hours_spin.setRange(1, 168)
        self.weekly_hours_spin.setValue(standards.get("weekly_standard_hours", 40))
        time_layout.addRow("주간 표준 근로시간:", self.weekly_hours_spin)

        self.overtime_multiplier_spin = QDoubleSpinBox()
        self.overtime_multiplier_spin.setRange(1.0, 3.0)
        self.overtime_multiplier_spin.setSingleStep(0.1)
        self.overtime_multiplier_spin.setValue(standards.get("overtime_multiplier", 1.5))
        time_layout.addRow("연장 근로 배수:", self.overtime_multiplier_spin)

        self.minimum_wage_spin = QSpinBox()
        self.minimum_wage_spin.setRange(0, 100000)
        self.minimum_wage_spin.setSingleStep(10)
        self.minimum_wage_spin.setValue(standards.get("minimum_wage", 10030))
        time_layout.addRow("최저임금:", self.minimum_wage_spin)

        layout.addWidget(time_group)

        # 기초 공제
        deduction_group = QGroupBox("기초 공제")
        deduction_layout = QFormLayout(deduction_group)

        self.basic_deduction_edit = QLineEdit()
        self.basic_deduction_edit.setText(str(standards.get("basic_deduction", 1500000)))
        deduction_layout.addRow("기초 공제액:", self.basic_deduction_edit)

        layout.addWidget(deduction_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "기본 설정")

    def create_insurance_tab(self, standards):
        """4대보험 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        insurance_rates = standards.get("insurance_rates", {})

        form_layout = QFormLayout()

        self.national_pension_edit = QLineEdit()
        self.national_pension_edit.setText(str(insurance_rates.get("national_pension", 0.045)))
        form_layout.addRow("국민연금 세율:", self.national_pension_edit)

        self.health_insurance_edit = QLineEdit()
        self.health_insurance_edit.setText(str(insurance_rates.get("health_insurance", 0.03545)))
        form_layout.addRow("건강보험 세율:", self.health_insurance_edit)

        self.long_term_care_edit = QLineEdit()
        self.long_term_care_edit.setText(str(insurance_rates.get("long_term_care", 0.1281)))
        form_layout.addRow("장기요양보험 세율:", self.long_term_care_edit)

        self.employment_insurance_edit = QLineEdit()
        self.employment_insurance_edit.setText(str(insurance_rates.get("employment_insurance", 0.009)))
        form_layout.addRow("고용보험 세율:", self.employment_insurance_edit)

        layout.addLayout(form_layout)
        layout.addStretch()

        self.tab_widget.addTab(tab, "4대보험")

    def create_income_tax_tab(self, standards):
        """소득세 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 설명
        info_label = QLabel("💡 소득세 누진세율표를 설정하세요")
        info_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 테이블 생성
        self.income_tax_table = QTableWidget()
        self.income_tax_table.setColumnCount(4)
        self.income_tax_table.setHorizontalHeaderLabels([
            "과세표준 최소액", "과세표준 최대액", "세율", "누진공제액"
        ])

        # 데이터 로드
        tax_brackets = standards.get("income_tax_brackets", [])
        self.income_tax_table.setRowCount(len(tax_brackets))

        for row, bracket in enumerate(tax_brackets):
            self.income_tax_table.setItem(row, 0, QTableWidgetItem(str(bracket.get("min", 0))))
            max_val = bracket.get("max", "")
            if max_val == float('inf'):
                max_val = "무제한"
            self.income_tax_table.setItem(row, 1, QTableWidgetItem(str(max_val)))
            self.income_tax_table.setItem(row, 2, QTableWidgetItem(str(bracket.get("rate", 0))))
            self.income_tax_table.setItem(row, 3, QTableWidgetItem(str(bracket.get("deduction", 0))))

        # 컬럼 너비 설정
        self.income_tax_table.setColumnWidth(0, 120)
        self.income_tax_table.setColumnWidth(1, 120)
        self.income_tax_table.setColumnWidth(2, 80)
        self.income_tax_table.setColumnWidth(3, 100)

        layout.addWidget(self.income_tax_table)

        self.tab_widget.addTab(tab, "소득세")

    def create_non_eligible_tab(self, standards):
        """비대상자 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        non_eligible_rates = standards.get("non_eligible_rates", {})

        form_layout = QFormLayout()

        self.non_eligible_income_tax_edit = QLineEdit()
        self.non_eligible_income_tax_edit.setText(str(non_eligible_rates.get("income_tax", 0.03)))
        form_layout.addRow("소득세 세율:", self.non_eligible_income_tax_edit)

        self.non_eligible_local_tax_edit = QLineEdit()
        self.non_eligible_local_tax_edit.setText(str(non_eligible_rates.get("local_income_tax", 0.003)))
        form_layout.addRow("지방소득세 세율:", self.non_eligible_local_tax_edit)

        layout.addLayout(form_layout)
        layout.addStretch()

        self.tab_widget.addTab(tab, "비대상자")

    def add_year(self):
        """새 연도 추가"""
        try:
            # 새 연도 입력 받기
            from PyQt6.QtWidgets import QInputDialog
            year, ok = QInputDialog.getText(self, "연도 추가", "추가할 연도를 입력하세요 (예: 2027):")

            if ok and year:
                # 템플릿 연도 선택
                available_years = self.tax_manager.get_available_years()
                template_year, ok2 = QInputDialog.getItem(
                    self, "템플릿 선택",
                    "기준이 될 연도를 선택하세요:",
                    available_years, len(available_years) - 1, False
                )

                if ok2:
                    self.tax_manager.add_year(year, template_year)
                    self.load_years()
                    self.year_combo.setCurrentText(year)
                    QMessageBox.information(self, "성공", f"{year}년 세법 기준이 추가되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "오류", f"연도 추가 실패: {str(e)}")

    def remove_year(self):
        """연도 삭제"""
        if not self.current_year:
            QMessageBox.warning(self, "경고", "삭제할 연도를 선택해주세요.")
            return

        reply = QMessageBox.question(
            self, "연도 삭제",
            f"{self.current_year}년 세법 기준을 삭제하시겠습니까?\n\n⚠️ 이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.tax_manager.remove_year(self.current_year)
                self.load_years()
                QMessageBox.information(self, "성공", f"{self.current_year}년 세법 기준이 삭제되었습니다.")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"연도 삭제 실패: {str(e)}")

    def save_current_year(self):
        """현재 연도의 설정 저장"""
        if not self.current_year:
            QMessageBox.warning(self, "경고", "저장할 연도를 선택해주세요.")
            return

        try:
            # 데이터 수집
            standards = {
                "name": f"{self.current_year}년 세법 기준",
                "holiday_allowance_hours": self.holiday_hours_spin.value(),
                "daily_standard_hours": self.daily_hours_spin.value(),
                "weekly_standard_hours": self.weekly_hours_spin.value(),
                "overtime_multiplier": self.overtime_multiplier_spin.value(),
                "minimum_wage": self.minimum_wage_spin.value(),
                "basic_deduction": int(self.basic_deduction_edit.text().replace(",", "")),
                "insurance_rates": {
                    "national_pension": float(self.national_pension_edit.text()),
                    "health_insurance": float(self.health_insurance_edit.text()),
                    "long_term_care": float(self.long_term_care_edit.text()),
                    "employment_insurance": float(self.employment_insurance_edit.text())
                },
                "income_tax_brackets": [],
                "non_eligible_rates": {
                    "income_tax": float(self.non_eligible_income_tax_edit.text()),
                    "local_income_tax": float(self.non_eligible_local_tax_edit.text())
                }
            }

            # 소득세 누진세율표 수집
            for row in range(self.income_tax_table.rowCount()):
                min_val = int(self.income_tax_table.item(row, 0).text().replace(",", ""))
                max_text = self.income_tax_table.item(row, 1).text()
                if max_text == "무제한":
                    max_val = float('inf')
                else:
                    max_val = int(max_text.replace(",", ""))
                rate = float(self.income_tax_table.item(row, 2).text())
                deduction = int(self.income_tax_table.item(row, 3).text().replace(",", ""))

                standards["income_tax_brackets"].append({
                    "min": min_val,
                    "max": max_val,
                    "rate": rate,
                    "deduction": deduction
                })

            # 유효성 검증
            if self.tax_manager.validate_standards(standards):
                self.tax_manager.set_standards_for_year(self.current_year, standards)
                QMessageBox.information(self, "성공", f"{self.current_year}년 세법 기준이 저장되었습니다.")
            else:
                QMessageBox.warning(self, "유효성 오류", "세법 기준 데이터가 올바르지 않습니다.")

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"저장 중 오류가 발생했습니다: {str(e)}")


def show_tax_law_settings(parent=None):
    """세법 기준 설정 다이얼로그 표시"""
    dialog = TaxLawSettingsDialog(parent)
    dialog.exec()
