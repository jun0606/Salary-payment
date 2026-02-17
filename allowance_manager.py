#!/usr/bin/env python3
"""
PyQt6 기반 수당 관리 팝업
직원별 수당 관리와 회사별 직책 수당 설정 기능

기능:
- 탭 기반 UI (일반 수당, 직책 수당 설정, 수당 템플릿)
- 직원별 수당 추가/수정/삭제
- 단발성 수당과 지속적 수당 구분
- 회사별 직책 수당 커스텀 설정
- 자동 연동 기능
"""

import sys
import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QTextEdit, QGroupBox, QMessageBox,
    QCheckBox, QDateEdit, QRadioButton, QButtonGroup,
    QSplitter, QScrollArea, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

class AllowanceManager(QDialog):
    """
    수당 관리 팝업 클래스
    """

    def __init__(self, parent, app_instance):
        super().__init__(parent)
        self.app = app_instance

        self.setWindowTitle("수당 관리")
        self.setModal(True)
        self.resize(1000, 700)

        # 데이터 로드
        self.load_data()

        # 템플릿 데이터 초기화 (먼저 초기화해야 함)
        self.current_template_id = None
        self.templates = self.config_data.get('allowance_templates', {})

        self.setup_ui()
        self.load_allowance_data()

    def load_data(self):
        """필요한 데이터 로드"""
        try:
            # 직원 데이터
            if os.path.exists('employees.json'):
                with open('employees.json', 'r', encoding='utf-8') as f:
                    employee_data = json.load(f)
                    self.employee_data = employee_data.get('employees', {})
            else:
                self.employee_data = {}

            # 설정 데이터
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            else:
                self.config_data = {}

        except Exception as e:
            QMessageBox.critical(self, "데이터 로드 오류", f"데이터를 로드할 수 없습니다:\n{str(e)}")
            self.employee_data = {}
            self.config_data = {}

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 탭 위젯
        self.tab_widget = QTabWidget()

        # 탭 생성
        self.setup_general_allowance_tab()
        self.setup_position_allowance_tab()
        self.setup_template_tab()

        layout.addWidget(self.tab_widget)

        # 버튼 그룹
        self.setup_buttons(layout)

    def setup_general_allowance_tab(self):
        """일반 수당 관리 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 직원 선택
        employee_layout = QHBoxLayout()
        employee_layout.addWidget(QLabel("직원 선택:"))

        self.employee_combo = QComboBox()
        self.employee_combo.currentTextChanged.connect(self.on_employee_selected)
        employee_layout.addWidget(self.employee_combo)

        employee_layout.addStretch()
        layout.addLayout(employee_layout)

        # 수당 목록과 설정 영역
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 수당 목록
        self.setup_allowance_list(splitter)

        # 우측: 수당 설정
        self.setup_allowance_settings(splitter)

        layout.addWidget(splitter)

        self.tab_widget.addTab(tab, "일반 수당")

    def setup_allowance_list(self, parent):
        """수당 목록 영역"""
        group = QGroupBox("수당 목록")
        layout = QVBoxLayout(group)

        # 수당 타입 선택
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("수당 타입:"))

        self.allowance_type_combo = QComboBox()
        self.allowance_type_combo.addItems(["지속적 수당", "단발성 수당"])
        self.allowance_type_combo.currentTextChanged.connect(self.update_allowance_list)
        type_layout.addWidget(self.allowance_type_combo)

        type_layout.addStretch()
        layout.addLayout(type_layout)

        # 수당 테이블
        self.allowance_table = QTableWidget()
        self.allowance_table.setColumnCount(4)
        self.allowance_table.setHorizontalHeaderLabels(["수당명", "금액", "적용 기간", "세금 적용"])
        self.allowance_table.horizontalHeader().setStretchLastSection(True)
        self.allowance_table.itemSelectionChanged.connect(self.on_allowance_selected)

        layout.addWidget(self.allowance_table)

        # 버튼 그룹
        button_layout = QHBoxLayout()

        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_allowance)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("수정")
        edit_btn.clicked.connect(self.edit_allowance)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_allowance)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        parent.addWidget(group)

    def setup_allowance_settings(self, parent):
        """수당 설정 영역"""
        group = QGroupBox("수당 설정")
        layout = QFormLayout(group)

        # 수당명
        self.allowance_name_edit = QLineEdit()
        layout.addRow("수당명:", self.allowance_name_edit)

        # 금액
        self.allowance_amount_edit = QLineEdit()
        self.allowance_amount_edit.setPlaceholderText("숫자만 입력")
        layout.addRow("금액:", self.allowance_amount_edit)

        # 수당 타입
        type_layout = QHBoxLayout()
        self.recurring_radio = QRadioButton("지속적 수당")
        self.one_time_radio = QRadioButton("단발성 수당")
        self.recurring_radio.setChecked(True)

        type_group = QButtonGroup()
        type_group.addButton(self.recurring_radio)
        type_group.addButton(self.one_time_radio)

        # 수당 타입 변경 시 UI 업데이트
        self.recurring_radio.toggled.connect(self.update_apply_date_ui)
        self.one_time_radio.toggled.connect(self.update_apply_date_ui)

        type_layout.addWidget(self.recurring_radio)
        type_layout.addWidget(self.one_time_radio)
        type_layout.addStretch()
        layout.addRow("수당 타입:", type_layout)

        # 적용 기간 (단발성 수당용)
        self.apply_date_edit = QDateEdit()
        self.apply_date_edit.setDate(QDate.currentDate())
        self.apply_date_edit.setEnabled(False)  # 기본적으로 비활성화
        layout.addRow("적용 일자:", self.apply_date_edit)

        # 세금 적용
        self.tax_check = QCheckBox("세금 적용")
        self.tax_check.setChecked(True)
        layout.addRow("", self.tax_check)

        # 적용 버튼
        apply_btn = QPushButton("적용")
        apply_btn.clicked.connect(self.apply_allowance_settings)
        layout.addRow("", apply_btn)

        parent.addWidget(group)

    def setup_position_allowance_tab(self):
        """직책 수당 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 회사 선택
        company_layout = QHBoxLayout()
        company_layout.addWidget(QLabel("회사 선택:"))

        self.company_combo = QComboBox()
        self.company_combo.currentTextChanged.connect(self.load_position_allowances)
        company_layout.addWidget(self.company_combo)

        company_layout.addStretch()
        layout.addLayout(company_layout)

        # 직책 수당 테이블
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(3)
        self.position_table.setHorizontalHeaderLabels(["직급", "현재 금액", "수정 금액"])
        self.position_table.horizontalHeader().setStretchLastSection(True)

        # 기본 직급 추가
        default_positions = [
            "사장", "부장", "과장", "대리", "주임", "사원", "계약직", "아르바이트"
        ]

        self.position_table.setRowCount(len(default_positions))
        for i, position in enumerate(default_positions):
            self.position_table.setItem(i, 0, QTableWidgetItem(position))
            self.position_table.setItem(i, 1, QTableWidgetItem("0"))
            self.position_table.setItem(i, 2, QTableWidgetItem("0"))

        layout.addWidget(self.position_table)

        # 저장 버튼
        save_btn = QPushButton("직책 수당 설정 저장")
        save_btn.clicked.connect(self.save_position_allowances)
        layout.addWidget(save_btn)

        self.tab_widget.addTab(tab, "직책 수당 설정")

    def setup_template_tab(self):
        """수당 템플릿 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 템플릿 목록과 설정 영역
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 템플릿 목록
        self.setup_template_list(splitter)

        # 우측: 템플릿 설정
        self.setup_template_settings(splitter)

        layout.addWidget(splitter)

        self.tab_widget.addTab(tab, "수당 템플릿")

    def setup_template_list(self, parent):
        """템플릿 목록 영역"""
        group = QGroupBox("수당 템플릿 목록")
        layout = QVBoxLayout(group)

        # 템플릿 테이블
        self.template_table = QTableWidget()
        self.template_table.setColumnCount(3)
        self.template_table.setHorizontalHeaderLabels(["템플릿명", "적용 대상", "수당 개수"])
        self.template_table.horizontalHeader().setStretchLastSection(True)
        self.template_table.itemSelectionChanged.connect(self.on_template_selected)

        layout.addWidget(self.template_table)

        # 버튼 그룹
        button_layout = QHBoxLayout()

        add_btn = QPushButton("새 템플릿")
        add_btn.clicked.connect(self.add_template)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton("수정")
        edit_btn.clicked.connect(self.edit_template)
        button_layout.addWidget(edit_btn)

        delete_btn = QPushButton("삭제")
        delete_btn.clicked.connect(self.delete_template)
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        parent.addWidget(group)

    def setup_template_settings(self, parent):
        """템플릿 설정 영역"""
        group = QGroupBox("템플릿 설정")
        layout = QFormLayout(group)

        # 템플릿명
        self.template_name_edit = QLineEdit()
        layout.addRow("템플릿명:", self.template_name_edit)

        # 설명
        self.template_desc_edit = QTextEdit()
        self.template_desc_edit.setMaximumHeight(60)
        layout.addRow("설명:", self.template_desc_edit)

        # 적용 대상
        target_layout = QVBoxLayout()
        target_layout.addWidget(QLabel("적용 대상 조건:"))

        self.position_checkboxes = {}
        positions = ["사장", "부장", "과장", "대리", "주임", "사원", "계약직", "아르바이트"]

        for position in positions:
            checkbox = QCheckBox(position)
            self.position_checkboxes[position] = checkbox
            target_layout.addWidget(checkbox)

        layout.addRow(target_layout)

        # 자동 적용 옵션
        self.auto_apply_check = QCheckBox("직원 등록 시 자동 적용")
        layout.addRow("", self.auto_apply_check)

        # 수당 목록 표시
        allowance_label = QLabel("포함된 수당:")
        layout.addRow(allowance_label)

        self.template_allowance_table = QTableWidget()
        self.template_allowance_table.setColumnCount(3)
        self.template_allowance_table.setHorizontalHeaderLabels(["수당명", "금액", "타입"])
        self.template_allowance_table.setMaximumHeight(150)
        layout.addRow(self.template_allowance_table)

        # 적용 버튼
        apply_btn = QPushButton("템플릿 저장")
        apply_btn.clicked.connect(self.save_template)
        layout.addRow("", apply_btn)

        parent.addWidget(group)

    def setup_buttons(self, parent_layout):
        """하단 버튼 그룹"""
        button_layout = QHBoxLayout()

        save_all_btn = QPushButton("전체 저장")
        save_all_btn.clicked.connect(self.save_all_data)
        button_layout.addWidget(save_all_btn)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        parent_layout.addLayout(button_layout)

    def load_allowance_data(self):
        """수당 데이터 로드"""
        # 직원 목록 업데이트
        self.employee_combo.clear()
        for emp_id, emp_data in self.employee_data.items():
            name = emp_data.get('name', emp_id)
            self.employee_combo.addItem(f"{name} ({emp_id})", emp_id)

        # 회사 목록 업데이트
        self.company_combo.clear()
        companies = self.config_data.get('companies', {})
        for company_id, company_info in companies.items():
            company_name = company_info.get('name', company_id)
            self.company_combo.addItem(company_name, company_id)

        # 템플릿 목록 업데이트
        self.load_template_list()

        # 기본 선택
        if self.employee_combo.count() > 0:
            self.employee_combo.setCurrentIndex(0)

        if self.company_combo.count() > 0:
            self.company_combo.setCurrentIndex(0)
            self.load_position_allowances()

    def on_employee_selected(self):
        """직원 선택 시 수당 목록 업데이트"""
        self.update_allowance_list()

    def update_allowance_list(self):
        """수당 목록 업데이트"""
        current_employee = self.employee_combo.currentData()
        allowance_type = self.allowance_type_combo.currentText()

        if not current_employee:
            return

        # 직원 수당 데이터 가져오기
        employee_allowances = self.employee_data.get(current_employee, {}).get('allowances', {})

        # 수당 타입에 따라 데이터 필터링
        if allowance_type == "지속적 수당":
            allowances = employee_allowances.get('recurring', [])
        else:
            allowances = employee_allowances.get('one_time', [])

        # 테이블 업데이트
        self.allowance_table.setRowCount(len(allowances))
        for i, allowance in enumerate(allowances):
            name = allowance.get('name', '')
            amount = allowance.get('amount', 0)
            taxable = "과세" if allowance.get('taxable', True) else "비과세"

            if allowance_type == "단발성 수당":
                apply_date = allowance.get('date', '미정')
                period = apply_date
            else:
                period = "매월"

            self.allowance_table.setItem(i, 0, QTableWidgetItem(name))
            self.allowance_table.setItem(i, 1, QTableWidgetItem(f"{amount:,}원"))
            self.allowance_table.setItem(i, 2, QTableWidgetItem(period))
            self.allowance_table.setItem(i, 3, QTableWidgetItem(taxable))

    def on_allowance_selected(self):
        """수당 선택 시 설정 영역 업데이트"""
        current_row = self.allowance_table.currentRow()
        if current_row < 0:
            return

        current_employee = self.employee_combo.currentData()
        allowance_type = self.allowance_type_combo.currentText()

        if not current_employee:
            return

        employee_allowances = self.employee_data.get(current_employee, {}).get('allowances', {})

        if allowance_type == "지속적 수당":
            allowances = employee_allowances.get('recurring', [])
        else:
            allowances = employee_allowances.get('one_time', [])

        if current_row < len(allowances):
            allowance = allowances[current_row]

            # 설정 영역 업데이트
            self.allowance_name_edit.setText(allowance.get('name', ''))
            self.allowance_amount_edit.setText(str(allowance.get('amount', 0)))

            if allowance_type == "지속적 수당":
                self.recurring_radio.setChecked(True)
                self.apply_date_edit.setEnabled(False)
            else:
                self.one_time_radio.setChecked(True)
                self.apply_date_edit.setEnabled(True)
                apply_date_str = allowance.get('date', '')
                if apply_date_str:
                    try:
                        apply_date = QDate.fromString(apply_date_str, "yyyy-MM-dd")
                        self.apply_date_edit.setDate(apply_date)
                    except:
                        self.apply_date_edit.setDate(QDate.currentDate())

            self.tax_check.setChecked(allowance.get('taxable', True))

    def add_allowance(self):
        """수당 추가"""
        self.allowance_name_edit.clear()
        self.allowance_amount_edit.clear()
        self.recurring_radio.setChecked(True)
        self.update_apply_date_ui()  # UI 상태 업데이트
        self.tax_check.setChecked(True)

        self.allowance_table.clearSelection()

    def update_apply_date_ui(self):
        """적용 일자 UI 상태 업데이트"""
        if self.one_time_radio.isChecked():
            # 단발성 수당: 적용 일자 활성화 및 강조
            self.apply_date_edit.setEnabled(True)
            self.apply_date_edit.setStyleSheet("""
                QDateEdit {
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
                    padding: 4px;
                    background-color: white;
                }
                QDateEdit:disabled {
                    background-color: #f0f0f0;
                    border: 1px solid #cccccc;
                }
            """)

            # 기본값: 현재 월의 마지막 날
            current_date = QDate.currentDate()
            last_day = QDate(current_date.year(), current_date.month(),
                           current_date.daysInMonth())
            self.apply_date_edit.setDate(last_day)

        else:
            # 지속적 수당: 적용 일자 비활성화
            self.apply_date_edit.setEnabled(False)
            self.apply_date_edit.setStyleSheet("""
                QDateEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 4px;
                    color: #6c757d;
                }
                QDateEdit:disabled {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    color: #6c757d;
                }
            """)

    def edit_allowance(self):
        """수당 수정"""
        current_row = self.allowance_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "수정할 수당을 선택해주세요.")
            return

        # 현재 선택된 수당 정보를 설정 영역에 로드
        self.on_allowance_selected()

    def delete_allowance(self):
        """수당 삭제"""
        current_row = self.allowance_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "삭제할 수당을 선택해주세요.")
            return

        current_employee = self.employee_combo.currentData()
        allowance_type = self.allowance_type_combo.currentText()

        if not current_employee:
            return

        reply = QMessageBox.question(
            self, "수당 삭제 확인",
            "선택된 수당을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            employee_allowances = self.employee_data.get(current_employee, {}).get('allowances', {})

            if allowance_type == "지속적 수당":
                allowances = employee_allowances.get('recurring', [])
            else:
                allowances = employee_allowances.get('one_time', [])

            if current_row < len(allowances):
                allowances.pop(current_row)
                self.update_allowance_list()
                QMessageBox.information(self, "삭제 완료", "수당이 삭제되었습니다.\n전체 저장 버튼을 눌러 저장하세요.")

    def apply_allowance_settings(self):
        """수당 설정 적용"""
        name = self.allowance_name_edit.text().strip()
        amount_text = self.allowance_amount_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "입력 오류", "수당명을 입력해주세요.")
            return

        try:
            amount = int(amount_text.replace(',', ''))
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "금액은 숫자로 입력해주세요.")
            return

        current_employee = self.employee_combo.currentData()
        allowance_type = "recurring" if self.recurring_radio.isChecked() else "one_time"

        if not current_employee:
            return

        # 직원 수당 데이터 초기화
        if 'allowances' not in self.employee_data[current_employee]:
            self.employee_data[current_employee]['allowances'] = {
                'recurring': [],
                'one_time': []
            }

        # 수당 데이터 생성
        allowance_data = {
            'name': name,
            'amount': amount,
            'taxable': self.tax_check.isChecked()
        }

        if allowance_type == "one_time":
            apply_date = self.apply_date_edit.date().toString("yyyy-MM-dd")
            allowance_data['date'] = apply_date

        # 기존 수당 수정 또는 새 수당 추가
        current_row = self.allowance_table.currentRow()
        allowances = self.employee_data[current_employee]['allowances'][allowance_type]

        if current_row >= 0 and current_row < len(allowances):
            # 기존 수당 수정
            allowances[current_row] = allowance_data
        else:
            # 새 수당 추가
            allowances.append(allowance_data)

        self.update_allowance_list()
        QMessageBox.information(self, "적용 완료", "수당이 적용되었습니다.\n전체 저장 버튼을 눌러 저장하세요.")

    def load_position_allowances(self):
        """직책 수당 로드"""
        current_company = self.company_combo.currentData()
        if not current_company:
            return

        companies = self.config_data.get('companies', {})
        company_info = companies.get(current_company, {})
        position_allowances = company_info.get('position_allowances', {})

        # 테이블 업데이트
        for i in range(self.position_table.rowCount()):
            position_item = self.position_table.item(i, 0)
            if position_item:
                position = position_item.text()
                current_amount = position_allowances.get(position, 0)
                self.position_table.item(i, 1).setText(f"{current_amount:,}")
                self.position_table.item(i, 2).setText(f"{current_amount:,}")

    def save_position_allowances(self):
        """직책 수당 설정 저장"""
        current_company = self.company_combo.currentData()
        if not current_company:
            QMessageBox.warning(self, "회사 선택", "회사를 선택해주세요.")
            return

        position_allowances = {}

        # 테이블에서 데이터 수집
        for i in range(self.position_table.rowCount()):
            position_item = self.position_table.item(i, 0)
            amount_item = self.position_table.item(i, 2)

            if position_item and amount_item:
                position = position_item.text()
                try:
                    amount = int(amount_item.text().replace(',', ''))
                    position_allowances[position] = amount
                except ValueError:
                    continue

        # 설정에 저장
        if 'companies' not in self.config_data:
            self.config_data['companies'] = {}

        if current_company not in self.config_data['companies']:
            self.config_data['companies'][current_company] = {}

        self.config_data['companies'][current_company]['position_allowances'] = position_allowances

        # 설정 파일 저장
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "저장 완료", "직책 수당 설정이 저장되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"설정을 저장할 수 없습니다:\n{str(e)}")

    def save_all_data(self):
        """모든 데이터 저장"""
        try:
            # 직원 데이터 저장
            employee_data_to_save = {"employees": self.employee_data}
            with open('employees.json', 'w', encoding='utf-8') as f:
                json.dump(employee_data_to_save, f, ensure_ascii=False, indent=4)

            # 설정 데이터 저장
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)

            QMessageBox.information(self, "저장 완료", "모든 수당 데이터가 저장되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"데이터를 저장할 수 없습니다:\n{str(e)}")

    def load_template_list(self):
        """템플릿 목록 로드"""
        self.template_table.setRowCount(len(self.templates))

        for i, (template_id, template) in enumerate(self.templates.items()):
            name = template.get('name', template_id)
            target_criteria = template.get('target_criteria', {})

            # 적용 대상 표시
            targets = []
            if target_criteria.get('position'):
                targets.extend(target_criteria['position'])
            target_text = ", ".join(targets) if targets else "모두"

            # 수당 개수 계산
            allowances = template.get('allowances', {})
            recurring_count = len(allowances.get('recurring', []))
            one_time_count = len(allowances.get('one_time', []))
            total_count = recurring_count + one_time_count

            self.template_table.setItem(i, 0, QTableWidgetItem(name))
            self.template_table.setItem(i, 1, QTableWidgetItem(target_text))
            self.template_table.setItem(i, 2, QTableWidgetItem(str(total_count)))

    def on_template_selected(self):
        """템플릿 선택 시 설정 영역 업데이트"""
        current_row = self.template_table.currentRow()
        if current_row < 0:
            return

        template_ids = list(self.templates.keys())
        if current_row < len(template_ids):
            template_id = template_ids[current_row]
            template = self.templates[template_id]

            # 설정 영역 업데이트
            self.current_template_id = template_id
            self.template_name_edit.setText(template.get('name', ''))
            self.template_desc_edit.setPlainText(template.get('description', ''))

            # 적용 대상 체크박스 업데이트
            target_criteria = template.get('target_criteria', {})
            target_positions = target_criteria.get('position', [])

            for position, checkbox in self.position_checkboxes.items():
                checkbox.setChecked(position in target_positions)

            # 자동 적용 옵션
            self.auto_apply_check.setChecked(template.get('auto_apply', False))

            # 수당 목록 표시
            allowances = template.get('allowances', {})
            all_allowances = allowances.get('recurring', []) + allowances.get('one_time', [])

            self.template_allowance_table.setRowCount(len(all_allowances))
            for i, allowance in enumerate(all_allowances):
                name = allowance.get('name', '')
                amount = allowance.get('amount', 0)
                allowance_type = "지속적" if allowance in allowances.get('recurring', []) else "단발성"

                self.template_allowance_table.setItem(i, 0, QTableWidgetItem(name))
                self.template_allowance_table.setItem(i, 1, QTableWidgetItem(f"{amount:,}원"))
                self.template_allowance_table.setItem(i, 2, QTableWidgetItem(allowance_type))

    def add_template(self):
        """새 템플릿 추가"""
        self.current_template_id = None
        self.template_name_edit.clear()
        self.template_desc_edit.clear()

        # 모든 체크박스 해제
        for checkbox in self.position_checkboxes.values():
            checkbox.setChecked(False)

        self.auto_apply_check.setChecked(False)
        self.template_allowance_table.setRowCount(0)

    def edit_template(self):
        """템플릿 수정"""
        current_row = self.template_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "수정할 템플릿을 선택해주세요.")
            return

        # 현재 선택된 템플릿 정보를 설정 영역에 로드
        self.on_template_selected()

    def delete_template(self):
        """템플릿 삭제"""
        current_row = self.template_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "삭제할 템플릿을 선택해주세요.")
            return

        template_ids = list(self.templates.keys())
        if current_row < len(template_ids):
            template_id = template_ids[current_row]
            template_name = self.templates[template_id].get('name', template_id)

            reply = QMessageBox.question(
                self, "템플릿 삭제 확인",
                f"'{template_name}' 템플릿을 삭제하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                del self.templates[template_id]
                self.load_template_list()

    def save_template(self):
        """템플릿 저장"""
        name = self.template_name_edit.text().strip()
        description = self.template_desc_edit.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "입력 오류", "템플릿명을 입력해주세요.")
            return

        # 적용 대상 수집
        target_positions = []
        for position, checkbox in self.position_checkboxes.items():
            if checkbox.isChecked():
                target_positions.append(position)

        # 템플릿 데이터 생성
        template_data = {
            'name': name,
            'description': description,
            'target_criteria': {
                'position': target_positions
            },
            'allowances': {
                'recurring': [],
                'one_time': []
            },
            'auto_apply': self.auto_apply_check.isChecked(),
            'created_date': QDate.currentDate().toString("yyyy-MM-dd"),
            'last_modified': QDate.currentDate().toString("yyyy-MM-dd")
        }

        # 기존 템플릿 수정 또는 새 템플릿 추가
        if self.current_template_id:
            # 기존 템플릿 수정
            self.templates[self.current_template_id] = template_data
        else:
            # 새 템플릿 추가 (UUID 생성)
            import uuid
            template_id = str(uuid.uuid4())
            self.templates[template_id] = template_data

        self.load_template_list()
        QMessageBox.information(self, "저장 완료", "수당 템플릿이 저장되었습니다.")

    def apply_position_allowance_to_employee(self, employee_id):
        """직원에게 직책 수당 자동 적용"""
        if employee_id not in self.employee_data:
            return

        employee = self.employee_data[employee_id]
        position = employee.get('position', '')
        company_id = employee.get('company_id', '')

        if not position or not company_id:
            return

        # 회사 직책 수당 확인
        companies = self.config_data.get('companies', {})
        company_info = companies.get(company_id, {})
        position_allowances = company_info.get('position_allowances', {})

        allowance_amount = position_allowances.get(position, 0)

        if allowance_amount > 0:
            # 수당 데이터 초기화
            if 'allowances' not in employee:
                employee['allowances'] = {'recurring': [], 'one_time': []}

            # 기존 직급 수당이 있는지 확인
            existing_position_allowance = None
            for allowance in employee['allowances']['recurring']:
                if allowance.get('name') == f'{position} 수당':
                    existing_position_allowance = allowance
                    break

            if existing_position_allowance:
                # 기존 수당 업데이트
                existing_position_allowance['amount'] = allowance_amount
            else:
                # 새 수당 추가
                employee['allowances']['recurring'].append({
                    'name': f'{position} 수당',
                    'amount': allowance_amount,
                    'taxable': True,
                    'auto': True  # 자동 적용 표시
                })


def show_allowance_manager(parent, app_instance):
    """
    수당 관리 팝업을 표시하는 함수
    """
    dialog = AllowanceManager(parent, app_instance)
    result = dialog.exec()
    return result == QDialog.DialogCode.Accepted
