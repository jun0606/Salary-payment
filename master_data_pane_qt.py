#!/usr/bin/env python3
"""
PyQt6 기반 직원 관리 패널
tkinter master_data_pane.py의 PyQt6 버전

기능:
- 직원 정보 입력 폼
- 직원 목록 표시 (테이블)
- 날짜 선택 기능
- CRUD 작업
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor

import date_utils


class MasterDataPaneQt(QWidget):
    """
    PyQt6 기반 직원 관리 패널 클래스
    """

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance

        # 폼 데이터 초기화
        self.form_fields = {
            "user_id": "",
            "name": "",
            "department": "",
            "position": "",
            "hire_date": "",
            "resignation_date": "",  # 퇴사일 추가
            "individual_payment_date": "",
            "insurance_eligible": True  # 4대보험 대상자 여부 (기본값: 대상자)
        }

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 입력 폼 그룹
        self.setup_input_form(layout)

        # 버튼 그룹
        self.setup_buttons(layout)

        # 직원 목록 테이블
        self.setup_employee_table(layout)

        # 4대보험 일괄 관리 그룹
        self.setup_bulk_insurance_management(layout)

    def setup_bulk_insurance_management(self, parent_layout):
        """4대보험 일괄 관리 그룹 설정"""
        bulk_group = QGroupBox("4대보험 일괄 관리")
        bulk_layout = QVBoxLayout(bulk_group)

        # 설명 레이블
        info_label = QLabel("💡 4대보험 미대상자가 많은 경우 일괄 관리를 사용하세요")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        bulk_layout.addWidget(info_label)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 전체 대상자 활성화 버튼
        enable_all_btn = QPushButton("✅ 전체 대상자 활성화")
        enable_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        enable_all_btn.clicked.connect(self.bulk_insurance_enable_all)
        button_layout.addWidget(enable_all_btn)

        # 전체 비대상자 비활성화 버튼
        disable_all_btn = QPushButton("❌ 전체 비대상자 비활성화")
        disable_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        disable_all_btn.clicked.connect(self.bulk_insurance_disable_all)
        button_layout.addWidget(disable_all_btn)

        bulk_layout.addLayout(button_layout)

        # 선택된 직원 관리 버튼 레이아웃
        selected_layout = QHBoxLayout()

        # 선택된 직원 대상자 전환 버튼
        enable_selected_btn = QPushButton("🔄 선택 대상자로 전환")
        enable_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        enable_selected_btn.clicked.connect(lambda: self.bulk_insurance_toggle_selected(True))
        selected_layout.addWidget(enable_selected_btn)

        # 선택된 직원 비대상자 전환 버튼
        disable_selected_btn = QPushButton("🔄 선택 비대상자로 전환")
        disable_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        disable_selected_btn.clicked.connect(lambda: self.bulk_insurance_toggle_selected(False))
        selected_layout.addWidget(disable_selected_btn)

        bulk_layout.addLayout(selected_layout)

        # 사용법 안내
        usage_label = QLabel("📖 사용법: 테이블에서 직원을 선택(Ctrl+클릭)한 후 원하는 버튼을 클릭하세요")
        usage_label.setWordWrap(True)
        usage_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 5px;")
        bulk_layout.addWidget(usage_label)

        parent_layout.addWidget(bulk_group)

    def setup_input_form(self, parent_layout):
        """입력 폼 설정"""
        form_group = QGroupBox("직원 정보 입력")
        form_layout = QVBoxLayout(form_group)

        # 그리드 레이아웃으로 폼 필드 배치
        grid_frame = QWidget()
        grid_layout = QVBoxLayout(grid_frame)

        # 사용자 ID
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("사용자ID:"))
        self.user_id_entry = QLineEdit()
        self.user_id_entry.setPlaceholderText("예: EMP001")
        id_layout.addWidget(self.user_id_entry)
        grid_layout.addLayout(id_layout)

        # 이름
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("이름:"))
        self.name_entry = QLineEdit()
        self.name_entry.setPlaceholderText("예: 홍길동")
        name_layout.addWidget(self.name_entry)
        grid_layout.addLayout(name_layout)

        # 부서
        dept_layout = QHBoxLayout()
        dept_layout.addWidget(QLabel("부서:"))
        self.dept_entry = QLineEdit()
        self.dept_entry.setPlaceholderText("예: 개발팀")
        dept_layout.addWidget(self.dept_entry)
        grid_layout.addLayout(dept_layout)

        # 직급
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("직급:"))
        self.pos_entry = QLineEdit()
        self.pos_entry.setPlaceholderText("예: 대리")
        pos_layout.addWidget(self.pos_entry)
        grid_layout.addLayout(pos_layout)

        # 입사일
        hire_layout = QVBoxLayout()
        hire_layout.addWidget(QLabel("입사일(YYYY-MM-DD):"))
        
        hire_input_layout = QHBoxLayout()
        self.hire_entry = QLineEdit()
        self.hire_entry.setPlaceholderText("예: 2024-01-01")
        hire_input_layout.addWidget(self.hire_entry)
        
        hire_prev_btn = QPushButton("◀")
        hire_prev_btn.setFixedSize(35, 25)
        hire_prev_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        hire_prev_btn.clicked.connect(lambda: self.adjust_date("hire_date", -1))
        hire_input_layout.addWidget(hire_prev_btn)
        
        hire_next_btn = QPushButton("▶")
        hire_next_btn.setFixedSize(35, 25)
        hire_next_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        hire_next_btn.clicked.connect(lambda: self.adjust_date("hire_date", 1))
        hire_input_layout.addWidget(hire_next_btn)
        
        hire_layout.addLayout(hire_input_layout)
        grid_layout.addLayout(hire_layout)

        # 퇴사일
        resignation_layout = QVBoxLayout()
        resignation_layout.addWidget(QLabel("퇴사일(YYYY-MM-DD):"))

        resignation_input_layout = QHBoxLayout()
        self.resignation_entry = QLineEdit()
        self.resignation_entry.setPlaceholderText("예: 2024-12-31 (미퇴사시 공란)")
        resignation_input_layout.addWidget(self.resignation_entry)

        resignation_prev_btn = QPushButton("◀")
        resignation_prev_btn.setFixedSize(35, 25)
        resignation_prev_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        resignation_prev_btn.clicked.connect(lambda: self.adjust_date("resignation_date", -1))
        resignation_input_layout.addWidget(resignation_prev_btn)

        resignation_next_btn = QPushButton("▶")
        resignation_next_btn.setFixedSize(35, 25)
        resignation_next_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        resignation_next_btn.clicked.connect(lambda: self.adjust_date("resignation_date", 1))
        resignation_input_layout.addWidget(resignation_next_btn)

        resignation_layout.addLayout(resignation_input_layout)
        grid_layout.addLayout(resignation_layout)

        # 개별 지급일
        pay_layout = QVBoxLayout()
        pay_layout.addWidget(QLabel("개별지급일(DD 또는 YYYY-MM-DD):"))

        # 입력 필드와 버튼을 수평으로 배치
        pay_input_layout = QHBoxLayout()
        self.pay_entry = QLineEdit()
        self.pay_entry.setPlaceholderText("예: 15 또는 2024-01-15")
        pay_input_layout.addWidget(self.pay_entry)

        # 날짜 조정 버튼들 (적절한 크기로)
        pay_prev_btn = QPushButton("◀")
        pay_prev_btn.setFixedSize(35, 25)
        pay_prev_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        pay_prev_btn.clicked.connect(lambda: self.adjust_date("individual_payment_date", -1))
        pay_input_layout.addWidget(pay_prev_btn)

        pay_next_btn = QPushButton("▶")
        pay_next_btn.setFixedSize(35, 25)
        pay_next_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        pay_next_btn.clicked.connect(lambda: self.adjust_date("individual_payment_date", 1))
        pay_input_layout.addWidget(pay_next_btn)

        pay_layout.addLayout(pay_input_layout)
        grid_layout.addLayout(pay_layout)

        # 전체 지급일
        global_pay_layout = QVBoxLayout()
        global_pay_layout.addWidget(QLabel("전체지급일(DD 또는 YYYY-MM-DD):"))

        # 입력 필드와 버튼을 수평으로 배치
        global_pay_input_layout = QHBoxLayout()
        self.global_pay_entry = QLineEdit()
        self.global_pay_entry.setText(self.app.global_payment_date_var)
        self.global_pay_entry.textChanged.connect(self.on_global_pay_changed)
        global_pay_input_layout.addWidget(self.global_pay_entry)

        # 날짜 조정 버튼들 (적절한 크기로)
        global_prev_btn = QPushButton("◀")
        global_prev_btn.setFixedSize(35, 25)
        global_prev_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        global_prev_btn.clicked.connect(lambda: self.adjust_global_date(-1))
        global_pay_input_layout.addWidget(global_prev_btn)

        global_next_btn = QPushButton("▶")
        global_next_btn.setFixedSize(35, 25)
        global_next_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 10px;
                padding: 2px;
            }
        """)
        global_next_btn.clicked.connect(lambda: self.adjust_global_date(1))
        global_pay_input_layout.addWidget(global_next_btn)

        global_pay_layout.addLayout(global_pay_input_layout)
        grid_layout.addLayout(global_pay_layout)

        # 4대보험 대상자 여부
        insurance_layout = QHBoxLayout()
        insurance_layout.addWidget(QLabel("4대보험 대상자:"))
        self.insurance_checkbox = QCheckBox("예 (4대보험 적용)")
        self.insurance_checkbox.setChecked(True)  # 기본값: 대상자
        insurance_layout.addWidget(self.insurance_checkbox)
        insurance_layout.addStretch()
        grid_layout.addLayout(insurance_layout)

        form_layout.addWidget(grid_frame)
        parent_layout.addWidget(form_group)

    def setup_buttons(self, parent_layout):
        """버튼 그룹 설정"""
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)

        # 첫 번째 행 버튼들
        row1_layout = QHBoxLayout()
        add_btn = QPushButton("직원 추가")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_employee)

        update_btn = QPushButton("직원 수정")
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        update_btn.clicked.connect(self.update_employee)

        delete_btn = QPushButton("직원 삭제")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        delete_btn.clicked.connect(self.delete_employee)

        row1_layout.addWidget(add_btn)
        row1_layout.addWidget(update_btn)
        row1_layout.addWidget(delete_btn)
        row1_layout.addStretch()

        # 두 번째 행 버튼들
        row2_layout = QHBoxLayout()
        clear_btn = QPushButton("입력 초기화")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        clear_btn.clicked.connect(self.clear_form)

        import_btn = QPushButton("급여에서 가져오기")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        import_btn.clicked.connect(self.import_from_summary)

        row2_layout.addWidget(clear_btn)
        row2_layout.addWidget(import_btn)
        row2_layout.addStretch()

        button_layout.addLayout(row1_layout)
        button_layout.addLayout(row2_layout)

        parent_layout.addWidget(button_frame)

    def setup_employee_table(self, parent_layout):
        """직원 목록 테이블 설정"""
        table_group = QGroupBox("직원 목록")
        table_layout = QVBoxLayout(table_group)

        # 테이블 생성
        self.employee_table = QTableWidget()
        self.employee_table.setColumnCount(8)
        self.employee_table.setHorizontalHeaderLabels([
            "사용자ID", "이름", "부서", "직급", "입사일", "퇴사일", "개별 지급일", "4대보험"
        ])

        # 테이블 스타일링 및 스크롤바 활성화
        self.employee_table.setAlternatingRowColors(True)
        self.employee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.employee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 좌우 스크롤바 활성화
        self.employee_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.employee_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 컬럼 너비 설정 (스크롤바가 나타나도록 고정 너비 사용)
        header = self.employee_table.horizontalHeader()

        # 모든 컬럼에 최소 너비 설정
        column_widths = [100, 80, 100, 80, 100, 100, 100]  # 사용자ID, 이름, 부서, 직급, 입사일, 퇴사일, 지급일

        for i, width in enumerate(column_widths):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.employee_table.setColumnWidth(i, width)

        # 테이블에 최소 너비 설정 (모든 컬럼 합보다 작게)
        total_min_width = sum(column_widths) - 100  # 약간 작게 설정해서 스크롤바 유도
        self.employee_table.setMinimumWidth(total_min_width)

        # 행 선택 시그널 연결
        self.employee_table.itemSelectionChanged.connect(self.on_table_selection_changed)

        table_layout.addWidget(self.employee_table)
        parent_layout.addWidget(table_group)

        # 초기 데이터 로드는 main_qt.py에서 호출

    def on_table_selection_changed(self):
        """테이블 행 선택 시 폼에 데이터 채우기"""
        selected_rows = set()
        for item in self.employee_table.selectedItems():
            selected_rows.add(item.row())

        if len(selected_rows) == 1:
            row = list(selected_rows)[0]
            user_id = self.employee_table.item(row, 0).text()

            if user_id in self.app.employee_data:
                employee = self.app.employee_data[user_id]
                self.user_id_entry.setText(user_id)
                self.name_entry.setText(employee.get("name", ""))
                self.dept_entry.setText(employee.get("department", ""))
                self.pos_entry.setText(employee.get("position", ""))
                self.hire_entry.setText(employee.get("hire_date", ""))
                self.resignation_entry.setText(employee.get("resignation_date", ""))
                self.pay_entry.setText(employee.get("individual_payment_date", ""))
                self.insurance_checkbox.setChecked(employee.get("insurance_eligible", True))

    def adjust_date(self, field_name, direction):
        """날짜 조정"""
        # 필드 이름 매핑
        field_mapping = {
            "hire_date": "hire_entry",
            "resignation_date": "resignation_entry",
            "individual_payment_date": "pay_entry"
        }

        entry_name = field_mapping.get(field_name, f"{field_name.split('_')[0]}_entry")
        current_value = getattr(self, entry_name).text()

        if not current_value.strip():
            QMessageBox.warning(None, "입력 오류", "날짜를 먼저 입력해주세요.")
            return

        try:
            adjusted_date, is_holiday = date_utils.adjust_for_holiday(
                current_value, self.app.month_var, direction
            )
            getattr(self, entry_name).setText(adjusted_date)

            if is_holiday:
                # 튜토리얼 가이드 박스와 오버레이를 일시적으로 숨김 (메시지 박스 위에 표시되도록)
                guide_box_hidden = False
                overlay_hidden = False
                if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'tutorial_engine') and self.app.main_window.tutorial_engine:
                    if self.app.main_window.tutorial_engine.guide_box:
                        self.app.main_window.tutorial_engine.guide_box.hide()
                        guide_box_hidden = True
                    if self.app.main_window.tutorial_engine.overlay:
                        self.app.main_window.tutorial_engine.overlay.hide()
                        overlay_hidden = True

                # 튜토리얼 환경에서 메시지 박스가 오버레이 위에 표시되도록 강력한 WindowFlags 설정
                msg_box = QMessageBox()
                msg_box.setWindowTitle("휴일 경고")
                msg_box.setText(f"입력하신 날짜 ({current_value})는 휴일이므로, {adjusted_date}로 조정되었습니다.")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowFlags(
                    Qt.WindowType.Window |
                    Qt.WindowType.WindowStaysOnTopHint |
                    Qt.WindowType.WindowCloseButtonHint |
                    Qt.WindowType.WindowSystemMenuHint
                )
                msg_box.raise_()  # 강제로 최상단으로 가져오기
                msg_box.activateWindow()  # 활성화
                msg_box.exec()

                # 튜토리얼 가이드 박스와 오버레이 다시 표시
                if guide_box_hidden and self.app.main_window.tutorial_engine.guide_box:
                    self.app.main_window.tutorial_engine.guide_box.show()
                if overlay_hidden and self.app.main_window.tutorial_engine.overlay:
                    self.app.main_window.tutorial_engine.overlay.show()
        except ValueError as e:
            QMessageBox.critical(None, "날짜 오류", str(e))

    def adjust_global_date(self, direction):
        """전체 지급일 조정"""
        current_value = self.global_pay_entry.text()
        if not current_value.strip() or not self.app.month_var:
            QMessageBox.critical(None, "입력 오류", "날짜와 계산 연월을 모두 입력해주세요.")
            return

        try:
            adjusted_date, is_holiday = date_utils.adjust_for_holiday(
                current_value, self.app.month_var, direction
            )
            self.global_pay_entry.setText(adjusted_date)
            self.app.global_payment_date_var = adjusted_date

            if is_holiday:
                # 튜토리얼 가이드 박스와 오버레이를 일시적으로 숨김 (메시지 박스 위에 표시되도록)
                guide_box_hidden = False
                overlay_hidden = False
                if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'tutorial_engine') and self.app.main_window.tutorial_engine:
                    if self.app.main_window.tutorial_engine.guide_box:
                        self.app.main_window.tutorial_engine.guide_box.hide()
                        guide_box_hidden = True
                    if self.app.main_window.tutorial_engine.overlay:
                        self.app.main_window.tutorial_engine.overlay.hide()
                        overlay_hidden = True

                # 튜토리얼 환경에서 메시지 박스가 오버레이 위에 표시되도록 강력한 WindowFlags 설정
                msg_box = QMessageBox()
                msg_box.setWindowTitle("휴일 경고")
                msg_box.setText(f"입력하신 날짜 ({current_value})는 휴일이므로, {adjusted_date}로 조정되었습니다.")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowFlags(
                    Qt.WindowType.Window |
                    Qt.WindowType.WindowStaysOnTopHint |
                    Qt.WindowType.WindowCloseButtonHint |
                    Qt.WindowType.WindowSystemMenuHint
                )
                msg_box.raise_()  # 강제로 최상단으로 가져오기
                msg_box.activateWindow()  # 활성화
                msg_box.exec()

                # 튜토리얼 가이드 박스와 오버레이 다시 표시
                if guide_box_hidden and self.app.main_window.tutorial_engine.guide_box:
                    self.app.main_window.tutorial_engine.guide_box.show()
                if overlay_hidden and self.app.main_window.tutorial_engine.overlay:
                    self.app.main_window.tutorial_engine.overlay.show()
        except ValueError as e:
            QMessageBox.critical(None, "날짜 오류", str(e))

    def on_global_pay_changed(self, text):
        """전체 지급일 변경 시 앱 데이터 업데이트"""
        self.app.global_payment_date_var = text

    def add_employee(self):
        """직원 추가"""
        user_id = self.user_id_entry.text().strip()
        name = self.name_entry.text().strip()

        if not user_id or not name:
            QMessageBox.critical(None, "입력 오류", "사용자ID와 이름은 필수입니다.")
            return

        if user_id in self.app.employee_data:
            QMessageBox.critical(None, "입력 오류", "이미 존재하는 사용자ID입니다.")
            return

        # 데이터 저장
        self.save_form_data(user_id)
        self.refresh_table()
        self.clear_form()

        # 튜토리얼 가이드 박스를 일시적으로 숨김 (메시지 박스 위에 표시되도록)
        guide_box_hidden = False
        if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'tutorial_engine') and self.app.main_window.tutorial_engine and self.app.main_window.tutorial_engine.guide_box:
            self.app.main_window.tutorial_engine.guide_box.hide()
            guide_box_hidden = True

        # 최상위에 표시되는 성공 메시지 박스 (윈도우 전체 중앙)
        msg_box = QMessageBox(parent=None)
        msg_box.setWindowTitle("성공")
        msg_box.setText("직원이 추가되었습니다.")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.exec()

        # 가이드 박스 다시 표시
        if guide_box_hidden and self.app.main_window.tutorial_engine.guide_box:
            self.app.main_window.tutorial_engine.guide_box.show()

    def update_employee(self):
        """직원 수정"""
        selected_rows = set()
        for item in self.employee_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.critical(None, "선택 오류", "수정할 직원을 목록에서 선택하세요.")
            return

        original_user_id = self.employee_table.item(list(selected_rows)[0], 0).text()
        new_user_id = self.user_id_entry.text().strip()
        name = self.name_entry.text().strip()

        if not new_user_id or not name:
            QMessageBox.critical(None, "입력 오류", "사용자ID와 이름은 필수입니다.")
            return

        if original_user_id != new_user_id and new_user_id in self.app.employee_data:
            QMessageBox.critical(None, "입력 오류", "변경하려는 사용자ID가 이미 존재합니다.")
            return

        # 기존 데이터 삭제 후 새 데이터 저장
        if original_user_id != new_user_id:
            del self.app.employee_data[original_user_id]

        self.save_form_data(new_user_id, silent=True)
        self.refresh_table()
        self.clear_form()

        # 튜토리얼 가이드 박스를 일시적으로 숨김 (메시지 박스 위에 표시되도록)
        guide_box_hidden = False
        if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'tutorial_engine') and self.app.main_window.tutorial_engine and self.app.main_window.tutorial_engine.guide_box:
            self.app.main_window.tutorial_engine.guide_box.hide()
            guide_box_hidden = True

        # 튜토리얼 활성화 상태 확인
        is_tutorial_active = hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'tutorial_engine') and self.app.main_window.tutorial_engine and self.app.main_window.tutorial_engine.guide_box

        if is_tutorial_active:
            # 튜토리얼 환경: 메시지 박스 표시 후 다음 단계 진행
            # 최상위에 표시되는 성공 메시지 박스 (윈도우 전체 중앙)
            msg_box = QMessageBox(parent=None)
            msg_box.setWindowTitle("성공")
            msg_box.setText("직원이 수정되었습니다.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()

            if self.app.main_window.tutorial_engine:
                self.app.main_window.tutorial_engine.next_step()
        else:
            # 일반 환경: 메시지 박스 표시
            # 최상위에 표시되는 성공 메시지 박스 (윈도우 전체 중앙)
            msg_box = QMessageBox(parent=None)
            msg_box.setWindowTitle("성공")
            msg_box.setText("직원이 수정되었습니다.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()

        # 가이드 박스 다시 표시
        if guide_box_hidden and hasattr(self.app, 'main_window') and self.app.main_window.tutorial_engine and self.app.main_window.tutorial_engine.guide_box:
            self.app.main_window.tutorial_engine.guide_box.show()

    def delete_employee(self):
        """직원 삭제"""
        selected_rows = set()
        for item in self.employee_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.critical(None, "선택 오류", "삭제할 직원을 목록에서 선택하세요.")
            return

        user_id = self.employee_table.item(list(selected_rows)[0], 0).text()
        employee_name = self.app.employee_data[user_id].get("name", "알 수 없음")

        reply = QMessageBox.question(
            self, "삭제 확인",
            f"직원 '{employee_name}' ({user_id}) 정보를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.app.employee_data[user_id]
            self.app.save_master_data()
            self.refresh_table()
            self.clear_form()

            # 튜토리얼 가이드 박스를 일시적으로 숨김 (메시지 박스 위에 표시되도록)
            guide_box_hidden = False
            if hasattr(self.app, 'main_window') and hasattr(self.app.main_window, 'tutorial_engine') and self.app.main_window.tutorial_engine and self.app.main_window.tutorial_engine.guide_box:
                self.app.main_window.tutorial_engine.guide_box.hide()
                guide_box_hidden = True

            # 최상위에 표시되는 성공 메시지 박스 (윈도우 전체 중앙)
            msg_box = QMessageBox(parent=None)
            msg_box.setWindowTitle("성공")
            msg_box.setText("직원이 삭제되었습니다.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()

            # 가이드 박스 다시 표시
            if guide_box_hidden and self.app.main_window.tutorial_engine.guide_box:
                self.app.main_window.tutorial_engine.guide_box.show()

    def save_form_data(self, user_id, silent=False):
        """폼 데이터를 앱 데이터에 저장"""
        self.app.employee_data[user_id] = {
            "name": self.name_entry.text().strip(),
            "department": self.dept_entry.text().strip(),
            "position": self.pos_entry.text().strip(),
            "hire_date": self.hire_entry.text().strip(),
            "resignation_date": self.resignation_entry.text().strip(),
            "individual_payment_date": self.pay_entry.text().strip(),
            "insurance_eligible": self.insurance_checkbox.isChecked(),
        }
        self.app.save_master_data(silent=silent)

    def clear_form(self):
        """입력 폼 초기화"""
        self.user_id_entry.clear()
        self.name_entry.clear()
        self.dept_entry.clear()
        self.pos_entry.clear()
        self.hire_entry.clear()
        self.resignation_entry.clear()
        self.pay_entry.clear()
        self.insurance_checkbox.setChecked(True)  # 기본값: 대상자

        # 테이블 선택 해제
        self.employee_table.clearSelection()

    def import_from_summary(self):
        """급여 데이터에서 직원 정보 가져오기"""
        if self.app.summary_df is None or self.app.summary_df.empty:
            # 최상위에 표시되는 메시지 박스
            msg_box = QMessageBox()
            msg_box.setWindowTitle("알림")
            msg_box.setText("가져올 급여 데이터가 없습니다.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()
            return

        new_count = 0
        for _, row in self.app.summary_df.iterrows():
            user_id = str(row['user_id'])
            if user_id not in self.app.employee_data:
                self.app.employee_data[user_id] = {
                    "name": row['name'],
                    "department": "",
                    "position": "",
                    "hire_date": "",
                    "individual_payment_date": "",
                    "insurance_eligible": True  # 기본값: 4대보험 대상자
                }
                new_count += 1

        if new_count > 0:
            self.app.save_master_data(silent=True)
            self.refresh_table()
            # 최상위에 표시되는 성공 메시지 박스
            msg_box = QMessageBox()
            msg_box.setWindowTitle("성공")
            msg_box.setText(f"{new_count}명의 신규 직원을 자동으로 추가했습니다.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()
        else:
            # 최상위에 표시되는 알림 메시지 박스
            msg_box = QMessageBox()
            msg_box.setWindowTitle("알림")
            msg_box.setText("새롭게 추가할 직원이 없습니다.")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()

    def bulk_insurance_enable_all(self):
        """전체 직원을 4대보험 대상자로 설정"""
        if not self.app.employee_data:
            QMessageBox.information(self, "알림", "등록된 직원이 없습니다.")
            return

        reply = QMessageBox.question(
            self, "전체 대상자 활성화",
            f"모든 직원({len(self.app.employee_data)}명)을 4대보험 대상자로 설정하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for user_id in self.app.employee_data:
                self.app.employee_data[user_id]["insurance_eligible"] = True

            self.app.save_master_data()
            self.refresh_table()

            QMessageBox.information(self, "완료", "모든 직원이 4대보험 대상자로 설정되었습니다.")

    def bulk_insurance_disable_all(self):
        """전체 직원을 4대보험 비대상자로 설정"""
        if not self.app.employee_data:
            QMessageBox.information(self, "알림", "등록된 직원이 없습니다.")
            return

        reply = QMessageBox.question(
            self, "전체 비대상자 비활성화",
            f"모든 직원({len(self.app.employee_data)}명)을 4대보험 비대상자로 설정하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for user_id in self.app.employee_data:
                self.app.employee_data[user_id]["insurance_eligible"] = False

            self.app.save_master_data()
            self.refresh_table()

            QMessageBox.information(self, "완료", "모든 직원이 4대보험 비대상자로 설정되었습니다.")

    def bulk_insurance_toggle_selected(self, enable):
        """선택된 직원들의 4대보험 상태를 토글"""
        selected_rows = set()
        for item in self.employee_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            action_text = "대상자" if enable else "비대상자"
            QMessageBox.warning(self, "선택 오류", f"4대보험 {action_text}로 전환할 직원을 선택해주세요.")
            return

        # 선택된 직원들의 ID 수집
        selected_user_ids = []
        for row in selected_rows:
            user_id_item = self.employee_table.item(row, 0)
            if user_id_item:
                selected_user_ids.append(user_id_item.text())

        if not selected_user_ids:
            QMessageBox.warning(self, "선택 오류", "유효한 직원을 선택해주세요.")
            return

        # 상태 변경
        action_text = "대상자" if enable else "비대상자"
        for user_id in selected_user_ids:
            if user_id in self.app.employee_data:
                self.app.employee_data[user_id]["insurance_eligible"] = enable

        self.app.save_master_data()
        self.refresh_table()

        QMessageBox.information(self, "완료", f"선택된 {len(selected_user_ids)}명의 직원이 4대보험 {action_text}로 설정되었습니다.")

    def filter_by_company(self, company_id):
        """특정 회사의 직원만 필터링하여 표시"""
        try:
            self.employee_table.setRowCount(0)

            for user_id, data in self.app.employee_data.items():
                if not user_id.strip():
                    continue

                # 회사 ID로 필터링
                employee_company_id = data.get('company_id')
                if company_id and employee_company_id != company_id:
                    continue  # 다른 회사의 직원은 건너뜀

                row_position = self.employee_table.rowCount()
                self.employee_table.insertRow(row_position)

                self.employee_table.setItem(row_position, 0, QTableWidgetItem(user_id))
                self.employee_table.setItem(row_position, 1, QTableWidgetItem(data.get("name", "")))
                self.employee_table.setItem(row_position, 2, QTableWidgetItem(data.get("department", "")))
                self.employee_table.setItem(row_position, 3, QTableWidgetItem(data.get("position", "")))
                self.employee_table.setItem(row_position, 4, QTableWidgetItem(data.get("hire_date", "")))
                self.employee_table.setItem(row_position, 5, QTableWidgetItem(data.get("resignation_date", "")))
                self.employee_table.setItem(row_position, 6, QTableWidgetItem(data.get("individual_payment_date", "")))

                # 4대보험 상태 표시 (7번 컬럼)
                insurance_status = "✅ 대상자" if data.get("insurance_eligible", True) else "❌ 비대상자"
                insurance_item = QTableWidgetItem(insurance_status)
                # 상태에 따라 색상 설정 (PyQt6 QColor 사용)
                if data.get("insurance_eligible", True):
                    insurance_item.setBackground(QColor(200, 255, 200))  # 연한 초록색
                else:
                    insurance_item.setBackground(QColor(255, 200, 200))  # 연한 빨간색
                self.employee_table.setItem(row_position, 7, insurance_item)

            print(f"회사 '{company_id}'의 직원 {self.employee_table.rowCount()}명 필터링 완료")

        except Exception as e:
            print(f"회사별 필터링 오류: {e}")
            # 오류 시 전체 직원 표시
            self.refresh_table()

    def refresh_table(self):
        """테이블 데이터 새로고침 (모든 직원 표시)"""
        self.employee_table.setRowCount(0)

        for user_id, data in self.app.employee_data.items():
            if not user_id.strip():
                continue

            row_position = self.employee_table.rowCount()
            self.employee_table.insertRow(row_position)

            self.employee_table.setItem(row_position, 0, QTableWidgetItem(user_id))
            self.employee_table.setItem(row_position, 1, QTableWidgetItem(data.get("name", "")))
            self.employee_table.setItem(row_position, 2, QTableWidgetItem(data.get("department", "")))
            self.employee_table.setItem(row_position, 3, QTableWidgetItem(data.get("position", "")))
            self.employee_table.setItem(row_position, 4, QTableWidgetItem(data.get("hire_date", "")))
            self.employee_table.setItem(row_position, 5, QTableWidgetItem(data.get("resignation_date", "")))
            self.employee_table.setItem(row_position, 6, QTableWidgetItem(data.get("individual_payment_date", "")))

            # 4대보험 상태 표시 (7번 컬럼)
            insurance_status = "✅ 대상자" if data.get("insurance_eligible", True) else "❌ 비대상자"
            insurance_item = QTableWidgetItem(insurance_status)
            # 상태에 따라 색상 설정 (PyQt6 QColor 사용)
            if data.get("insurance_eligible", True):
                insurance_item.setBackground(QColor(200, 255, 200))  # 연한 초록색
            else:
                insurance_item.setBackground(QColor(255, 200, 200))  # 연한 빨간색
            self.employee_table.setItem(row_position, 7, insurance_item)


def setup_pane(app, master_pane):
    """
    기존 tkinter 호환성을 위한 함수
    실제로는 MasterDataPaneQt를 직접 사용하도록 변경 예정
    """
    pane = MasterDataPaneQt(app)
    layout = QVBoxLayout(master_pane)
    layout.addWidget(pane)
    return master_pane
