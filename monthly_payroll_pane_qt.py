#!/usr/bin/env python3
"""
PyQt6 기반 급여 계산 패널
tkinter monthly_payroll_pane.py의 PyQt6 버전

기능:
- 엑셀 파일 선택 및 로드
- 급여 계산 및 미리보기
- 결과 테이블 표시 및 편집
- 최종 파일 생성 (Excel/HTML)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QFileDialog, QMessageBox, QHeaderView, QInputDialog, QCheckBox,
    QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import logic
import os
import datetime
import pandas as pd
import logging

# 컬럼 헤더 매핑 (HTML 템플릿과 동일한 이름 사용)
COLUMN_HEADER_MAP = {
    "user_id": "사번", "name": "성명", "department": "부서", "position": "직급",
    "hire_date": "입사일", "payment_date": "지급일", "base_pay": "기본급",
    "weekly_holiday_allowance": "주휴수당", "extra_pay": "연장수당",
    "night_pay": "야간수당", "national_pension": "국민연금",
    "health_insurance": "건강보험", "employment_insurance": "고용보험",
    "long_term_care_insurance": "장기요양보험", "income_tax": "소득세",
    "local_income_tax": "지방소득세", "deductions": "합계(공제)",
    "net_pay": "실지급액", "총급여액": "합계(지급)"
}


class MonthlyPayrollPaneQt(QWidget):
    """
    PyQt6 기반 급여 계산 패널 클래스
    """

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance

        # 데이터 초기화
        self.monthly_table = None
        self.file_path_label = None
        self.status_label = None

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 파일 선택 영역
        self.setup_file_selection(layout)

        # 계산 옵션 영역
        self.setup_calculation_options(layout)

        # 결과 테이블
        self.setup_results_table(layout)

        # 상태 표시
        self.setup_status_display(layout)

        # 파일 생성 버튼
        self.setup_file_generation(layout)

    def setup_file_selection(self, parent_layout):
        """파일 선택 영역 설정"""
        file_group = QGroupBox("근태 파일 선택")
        file_layout = QHBoxLayout(file_group)

        # 파일 경로 표시 레이블
        self.file_path_label = QLabel("선택된 파일: 없음")
        self.file_path_label.setStyleSheet("color: #666; font-style: italic;")
        file_layout.addWidget(self.file_path_label)

        # 파일 선택 버튼
        select_btn = QPushButton("📁 파일 선택")
        select_btn.setStyleSheet("""
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
        select_btn.clicked.connect(self.select_file)
        file_layout.addWidget(select_btn)

        parent_layout.addWidget(file_group)

    def setup_calculation_options(self, parent_layout):
        """계산 옵션 영역 설정"""
        calc_group = QGroupBox("급여 계산 옵션")
        calc_layout = QHBoxLayout(calc_group)

        # 계산 연월 입력 (tkinter 버전처럼 수동 입력)
        month_label = QLabel("계산 연월 (YYYY-MM):")
        self.month_entry = QLineEdit()
        self.month_entry.setPlaceholderText("예: 2024-12")
        self.month_entry.setMaximumWidth(120)

        # 기본값을 현재 월로 설정
        current_month_str = datetime.datetime.now().strftime("%Y-%m")
        self.month_entry.setText(current_month_str)

        calc_layout.addWidget(month_label)
        calc_layout.addWidget(self.month_entry)

        # 계산 시작 버튼
        calc_btn = QPushButton("📊 급여 계산")
        calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        calc_btn.clicked.connect(self.preview_data)
        calc_layout.addWidget(calc_btn)

        # 급여대장 버튼
        payroll_register_btn = QPushButton("📋 급여대장")
        payroll_register_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        payroll_register_btn.clicked.connect(self.open_payroll_register)
        calc_layout.addWidget(payroll_register_btn)

        calc_layout.addStretch()
        parent_layout.addWidget(calc_group)

    def setup_results_table(self, parent_layout):
        """결과 테이블 설정"""
        table_group = QGroupBox("급여 계산 결과")
        table_layout = QVBoxLayout(table_group)

        # 테이블 생성
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(len(self.app.monthly_columns))
        # HTML 템플릿과 동일한 한글 헤더 사용
        header_labels = [COLUMN_HEADER_MAP.get(col, col) for col in self.app.monthly_columns]
        self.monthly_table.setHorizontalHeaderLabels(header_labels)

        # 테이블 스타일링
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # 스크롤바 활성화
        self.monthly_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.monthly_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 컬럼 너비 설정 - 스크롤 사용을 위해 고정 너비로 변경
        header = self.monthly_table.horizontalHeader()

        # 각 컬럼별 기본 너비 설정 (픽셀 단위)
        column_widths = {
            'user_id': 80, 'name': 100, 'department': 100, 'position': 100,
            'hire_date': 100, 'payment_date': 100, 'base_pay': 120,
            'weekly_holiday_allowance': 120, 'extra_pay': 120, 'night_pay': 120,
            'national_pension': 120, 'health_insurance': 120, 'employment_insurance': 120,
            'long_term_care_insurance': 140, 'income_tax': 120, 'local_income_tax': 120,
            'deductions': 120, 'net_pay': 120, '총급여액': 120
        }

        for i, col in enumerate(self.app.monthly_columns):
            width = column_widths.get(col, 100)  # 기본 100px
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            self.monthly_table.setColumnWidth(i, width)

        # 더블클릭 이벤트 연결
        self.monthly_table.itemDoubleClicked.connect(self.on_table_double_click)

        table_layout.addWidget(self.monthly_table)
        parent_layout.addWidget(table_group)

    def setup_status_display(self, parent_layout):
        """상태 표시 영역 설정"""
        status_group = QGroupBox("처리 상태")
        status_layout = QVBoxLayout(status_group)

        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        status_layout.addWidget(self.status_label)

        parent_layout.addWidget(status_group)

    def setup_file_generation(self, parent_layout):
        """파일 생성 버튼 영역 설정"""
        button_group = QGroupBox("최종 파일 생성")
        button_group.setObjectName("file_generation_group")
        button_layout = QHBoxLayout(button_group)

        # 파일 형식은 HTML로 고정 (Excel 제거로 인한 효율성 향상)
        format_label = QLabel("출력 형식: HTML")
        button_layout.addWidget(format_label)

        # 출력 모드 선택
        mode_label = QLabel("출력 모드:")
        self.output_mode_combo = QComboBox()
        self.output_mode_combo.addItems(["통합", "개별(모든직원)", "선택"])
        self.output_mode_combo.setCurrentText("통합")

        button_layout.addWidget(mode_label)
        button_layout.addWidget(self.output_mode_combo)

        # 설명 표시 옵션 그룹
        explanation_group = QGroupBox("설명 표시 옵션")
        explanation_layout = QVBoxLayout(explanation_group)

        # 체크박스들 생성
        self.base_pay_explanation_cb = QCheckBox("기본급 산출식 표시")
        self.holiday_explanation_cb = QCheckBox("주휴수당 산출식 표시")
        self.night_explanation_cb = QCheckBox("야간수당 산출식 표시")
        self.holiday_work_explanation_cb = QCheckBox("휴일근로수당 산출식 표시")
        self.overtime_explanation_cb = QCheckBox("연장수당 산출식 표시")

        # 기본적으로 모두 체크
        self.base_pay_explanation_cb.setChecked(True)
        self.holiday_explanation_cb.setChecked(True)
        self.night_explanation_cb.setChecked(True)
        self.holiday_work_explanation_cb.setChecked(True)
        self.overtime_explanation_cb.setChecked(True)

        # 체크박스들을 레이아웃에 추가
        explanation_layout.addWidget(self.base_pay_explanation_cb)
        explanation_layout.addWidget(self.holiday_explanation_cb)
        explanation_layout.addWidget(self.night_explanation_cb)
        explanation_layout.addWidget(self.holiday_work_explanation_cb)
        explanation_layout.addWidget(self.overtime_explanation_cb)

        parent_layout.addWidget(explanation_group)

        # 생성 버튼
        generate_btn = QPushButton("🚀 최종 파일 생성")
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #D84315;
            }
        """)
        generate_btn.clicked.connect(self.generate_final_file)
        button_layout.addWidget(generate_btn)

        # 이전 급여내역서 출력 버튼
        history_btn = QPushButton("📋 이전 급여내역서 출력")
        history_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        history_btn.clicked.connect(self.open_payslip_history)
        button_layout.addWidget(history_btn)

        button_layout.addStretch()
        parent_layout.addWidget(button_group)

    def select_file(self):
        """파일 선택"""
        if self.app.locked:
            QMessageBox.warning(self, "라이선스 잠금",
                "라이선스가 유효하지 않아 이 기능을 사용할 수 없습니다.")
            return

        print("파일 선택 다이얼로그 열기")  # 디버깅용

        # 튜토리얼 오버레이 일시적 숨김 (안내 상자는 유지)
        overlay_hidden = False
        try:
            from tutorial_wizard_qt import TutorialEngine
            if TutorialEngine._current_instance:
                # 오버레이만 숨김 (안내 상자는 유지)
                if TutorialEngine._current_instance.overlay:
                    TutorialEngine._current_instance.overlay.hide()
                    overlay_hidden = True
                    print("튜토리얼 오버레이 일시적 숨김")
        except Exception as e:
            print(f"튜토리얼 컴포넌트 숨김 실패: {e}")

        # 최상위에 표시되는 파일 선택 대화상자
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("근태 파일을 선택하세요")
        file_dialog.setNameFilters(["Excel files (*.xlsx)", "All files (*.*)"])
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setWindowFlags(file_dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
            else:
                file_path = ""
        else:
            file_path = ""

        # 오버레이 다시 표시
        if overlay_hidden:
            try:
                if TutorialEngine._current_instance and TutorialEngine._current_instance.overlay:
                    TutorialEngine._current_instance.overlay.show()
                    print("튜토리얼 오버레이 다시 표시")
            except Exception as e:
                print(f"오버레이 표시 실패: {e}")

        print(f"파일 선택 결과: '{file_path}' (길이: {len(file_path)})")  # 디버깅용

        if file_path and file_path.strip():  # 빈 문자열이 아닌 경우만
            print(f"유효한 파일 경로 설정: {file_path}")  # 디버깅용
            print(f"파일 설정 전 selected_file_path: {getattr(self.app, 'selected_file_path', 'NOT_SET')}")  # 디버깅용
            self.app.selected_file_path = file_path
            print(f"파일 설정 후 selected_file_path: {self.app.selected_file_path}")  # 디버깅용
            self.file_path_label.setText(f"선택된 파일: {os.path.basename(file_path)}")

            # 튜토리얼 안내 박스 최상위로 올리기 (파일 선택 완료 후)
            try:
                from tutorial_wizard_qt import TutorialEngine
                if TutorialEngine._current_instance and TutorialEngine._current_instance.guide_box:
                    TutorialEngine._current_instance.guide_box.raise_()
                    print("안내 박스 최상위로 올림")
            except Exception as e:
                print(f"안내 박스 raise 실패: {e}")

            # 파일에서 사용 가능한 월 분석 및 자동 설정
            try:
                xls = pd.ExcelFile(file_path)
                available_months = []

                for sheet_name in xls.sheet_names:
                    # 시트명 패턴 매칭 (기존 logic.py와 동일)
                    if pd.Series([sheet_name]).str.match(r'^(\d{1,2}월|\d{4}년 \d{1,2}월)$').any():
                        month_str = ''.join(filter(str.isdigit, sheet_name))
                        month_num = int(month_str[-2:]) if len(month_str) > 2 else int(month_str)
                        available_months.append(month_num)

                if available_months:
                    # 가장 최근 월로 자동 설정
                    latest_month = max(available_months)
                    current_year = datetime.datetime.now().year
                    suggested_month = f"{current_year}-{latest_month:02d}"

                    self.month_entry.setText(suggested_month)
                    available_months_str = ", ".join([f"{m}월" for m in sorted(set(available_months))])
                    self.status_label.setText(f"파일 분석 완료. 최근 데이터 월({latest_month}월)로 자동 설정되었습니다.\n사용 가능한 월: {available_months_str}")
                    self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    self.month_entry.setText("")
                    self.status_label.setText("파일에서 월별 시트를 찾을 수 없습니다. 수동으로 월을 입력해주세요.")
                    self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")

            except Exception as e:
                print(f"파일 분석 오류: {e}")
                self.status_label.setText("파일이 선택되었습니다. 계산 연월을 입력하세요.")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            print("파일 선택 취소됨 또는 빈 경로")  # 디버깅용
            # 파일 선택이 취소된 경우
            self.file_path_label.setText("선택된 파일: 없음")
            self.status_label.setText("파일 선택이 취소되었습니다.")
            self.status_label.setStyleSheet("color: #666; font-style: italic;")

    def preview_data(self):
        """데이터 미리보기 및 계산"""
        if self.app.locked:
            QMessageBox.warning(self, "라이선스 잠금",
                "라이선스가 유효하지 않아 급여 계산을 진행할 수 없습니다.")
            return

        if not self.app.selected_file_path:
            QMessageBox.critical(self, "오류", "근태 파일을 먼저 선택해주세요.")
            return

        selected_month = self.month_entry.text().strip()
        if not selected_month:
            QMessageBox.critical(self, "오류", "계산 연월을 입력해주세요.")
            return

        # 상태 업데이트
        self.status_label.setText("급여 계산 중...")
        self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.app.month_var = selected_month

        # UI 업데이트
        self.repaint()

        try:
            # 급여 계산 실행
            self.app.summary_df, self.app.data_month_for_title, self.app.business_size = logic.process_payroll_for_gui(
                self.app.selected_file_path, selected_month, self.app.employee_data
            )

            # 직원 정보와 결합
            if self.app.summary_df is not None:
                print(f"직원 데이터 연동 시작: 직원 수 = {len(self.app.employee_data)}, 급여 데이터 행 수 = {len(self.app.summary_df)}")

                matched_count = 0
                for index, row in self.app.summary_df.iterrows():
                    user_id = str(row['user_id'])
                    master_info = self.app.employee_data.get(user_id, {})

                    if master_info:  # 매칭된 경우
                        matched_count += 1
                        print(f"직원 매칭 성공: {user_id} -> {master_info.get('name', '이름없음')}")
                    else:
                        print(f"직원 매칭 실패: {user_id} (사용 가능한 키: {list(self.app.employee_data.keys())[:5]})")

                    # 마스터 데이터에서 정보 복사
                    for col in ['department', 'position', 'hire_date', 'resignation_date']:
                        self.app.summary_df.loc[index, col] = master_info.get(col, '')

                    # 지급일 설정
                    payment_date = master_info.get('individual_payment_date') or self.app.global_payment_date_var
                    if payment_date and len(payment_date) <= 2 and payment_date.isdigit():
                        payment_date = f"{selected_month}-{int(payment_date):02d}"
                    self.app.summary_df.loc[index, 'payment_date'] = payment_date

                print(f"직원 데이터 연동 완료: {matched_count}/{len(self.app.summary_df)} 행 매칭됨")

                # 테이블에 결과 표시
                self.populate_table()

                self.status_label.setText("계산 완료. 수정하려면 셀을 더블클릭하세요.")
                self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

                # 최상위에 표시되는 성공 메시지 박스
                msg_box = QMessageBox()
                msg_box.setWindowTitle("성공")
                msg_box.setText("급여 계산이 완료되었습니다.")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                msg_box.exec()

        except Exception as e:
            self.status_label.setText("계산 오류 발생.")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            QMessageBox.critical(self, "계산 오류", str(e))
            print(f"급여 계산 오류: {e}")

    def populate_table(self):
        """테이블에 데이터 채우기 - tkinter 버전 방식으로 고정 컬럼 순서 유지"""
        if self.app.summary_df is None:
            return

        # tkinter 버전처럼: monthly_columns에 정의된 모든 컬럼 표시
        # 없는 컬럼은 빈 값으로 채움
        for col in self.app.monthly_columns:
            if col not in self.app.summary_df.columns:
                self.app.summary_df[col] = ''

        # 테이블 초기화 (헤더는 이미 setup_results_table에서 설정됨)
        self.monthly_table.setRowCount(0)

        # 데이터 채우기 (항상 monthly_columns 순서대로)
        for index, row in self.app.summary_df.iterrows():
            row_position = self.monthly_table.rowCount()
            self.monthly_table.insertRow(row_position)

            for col_index, col_name in enumerate(self.app.monthly_columns):
                value = row.get(col_name, "")

                # 빈 값 처리 (MCP 분석 결과 적용)
                import pandas as pd
                if value == "" or pd.isna(value):
                    if col_name in ['base_pay', 'weekly_holiday_allowance', 'extra_pay', 'night_pay',
                                  'national_pension', 'health_insurance', 'employment_insurance',
                                  'long_term_care_insurance', 'income_tax', 'local_income_tax',
                                  'deductions', 'net_pay', '총급여액']:
                        value = 0  # 숫자 컬럼은 0으로 초기화
                    else:
                        value = "-"  # 텍스트 컬럼은 "-"로 표시

                # 숫자 데이터 포맷팅 - 과학적 표기법 방지 및 깔끔한 표시
                if isinstance(value, (int, float)):
                    # 정수로 표현 가능한 경우 정수로 표시, 그렇지 않으면 소수점 유지
                    if value == int(value):
                        display_value = f"{int(value):,}"  # 정수: 쉼표 구분만
                    else:
                        display_value = f"{value:,.0f}"  # 실수: 소수점 이하가 있는 경우만 표시
                else:
                    display_value = str(value)

                item = QTableWidgetItem(display_value)
                self.monthly_table.setItem(row_position, col_index, item)

    def on_table_double_click(self, item):
        """테이블 셀 더블클릭 처리"""
        if self.app.locked:
            return

        row = item.row()
        col = item.column()

        # tkinter 버전처럼: monthly_columns에서 직접 가져옴
        if col >= len(self.app.monthly_columns):
            return

        col_name = self.app.monthly_columns[col]

        # 수정 불가능한 컬럼 체크
        if col_name in ["deductions", "net_pay", "총급여액"]:
            QMessageBox.information(self, "알림", "이 컬럼은 직접 수정할 수 없습니다.")
            return

        # 현재 값 가져오기
        current_value = item.text().replace(',', '')

        # 간단한 입력 대화상자로 수정
        new_value, ok = QInputDialog.getText(
            self, "값 수정",
            f"{col_name} 값 입력:",
            text=current_value
        )

        if ok and new_value != current_value:
            self.update_table_value(row, col_name, new_value)

    def update_table_value(self, row_index, column_name, new_value_str):
        """테이블 값 업데이트"""
        try:
            df_index = row_index

            # 데이터 타입 변환
            numeric_cols = ['base_pay', 'weekly_holiday_allowance', 'extra_pay', 'night_pay',
                          'national_pension', 'health_insurance', 'employment_insurance',
                          'long_term_care_insurance', 'income_tax', 'local_income_tax']

            if column_name in numeric_cols:
                new_value = float(new_value_str)
            else:
                new_value = new_value_str

            # 데이터프레임 업데이트
            self.app.summary_df.loc[df_index, column_name] = new_value

            # 재계산
            row = self.app.summary_df.loc[df_index]

            # 공제액 합계
            deduction_fields = ['national_pension', 'health_insurance', 'employment_insurance',
                              'long_term_care_insurance', 'income_tax', 'local_income_tax']
            total_deductions = 0
            for f in deduction_fields:
                val = pd.to_numeric(row.get(f, 0), errors='coerce')
                total_deductions += val if not pd.isna(val) else 0

            # 지급액 합계
            total_payment = 0
            for f in ['base_pay', 'weekly_holiday_allowance', 'extra_pay']:
                val = pd.to_numeric(row.get(f, 0), errors='coerce')
                total_payment += val if not pd.isna(val) else 0

            # 실지급액 계산
            net_pay = total_payment - total_deductions

            # 업데이트
            self.app.summary_df.loc[df_index, 'deductions'] = total_deductions
            self.app.summary_df.loc[df_index, 'net_pay'] = net_pay
            self.app.summary_df.loc[df_index, '총급여액'] = total_payment

            # 테이블 다시 채우기
            self.populate_table()

            employee_name = row.get('name', '알 수 없음')
            self.status_label.setText(f"{employee_name}의 {column_name}이(가) 업데이트되었습니다.")
            self.status_label.setStyleSheet("color: #2196F3; font-weight: bold;")

        except Exception as e:
            QMessageBox.critical(self, "업데이트 오류", f"값 업데이트 중 오류 발생: {e}")
            print(f"테이블 값 업데이트 오류: {e}")

    def extract_payslip_data_from_html(self, html_content, data_month, company_name):
        """
        HTML 콘텐츠에서 급여명세서 데이터를 추출하여 DB 저장용 데이터 생성

        Args:
            html_content: HTML 문자열
            data_month: 데이터 월 (예: "2025년 12월")
            company_name: 회사명

        Returns:
            dict: DB 저장용 데이터 또는 None
        """
        import re
        import uuid
        import hashlib
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            data = {
                'id': str(uuid.uuid4()),
                'employee_name': '',
                'company_name': company_name,
                'pay_month': '',
                'html_content': html_content,
                'employee_id': '',
                'version': 1,
                'input_data_hash': hashlib.sha256(html_content.encode()).hexdigest()
            }

            # pay_month 변환 (예: "2025년 12월" → "2025-12")
            if data_month and '년' in data_month and '월' in data_month:
                match = re.search(r'(\d{4})년 (\d{1,2})월', data_month)
                if match:
                    year = match.group(1)
                    month = match.group(2).zfill(2)
                    data['pay_month'] = f"{year}-{month}"

            # HTML에서 데이터 추출
            info_table = soup.find('table', class_='info-table')
            if info_table:
                rows = info_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)

                        if '회사명' in label:
                            data['company_name'] = value
                        elif '성명' in label:
                            data['employee_name'] = value
                        elif '사번' in label:
                            data['employee_id'] = value or f"emp_{hash(data['employee_name']) % 10000}"

            # employee_id가 없으면 생성
            if not data['employee_id'] and data['employee_name']:
                data['employee_id'] = f"emp_{hash(data['employee_name']) % 10000}"

            # 급여 항목 추출 - salary-table 구조에 맞게 수정
            salary_table = soup.find('table', class_='salary-table')
            if salary_table:
                rows = salary_table.find_all('tr')

                for tr in rows:
                    cells = tr.find_all('td')
                    if len(cells) < 5:  # 충분한 셀이 없는 행은 건너뜀
                        continue

                    # 지급 항목 추출 (1번째 셀: 항목명, 2번째 셀: 금액)
                    item_name = cells[0].get_text(strip=True)
                    payment_amount = cells[1].get_text(strip=True).replace(',', '').replace('원', '')

                    # 공제 항목 추출 (3번째 셀: 항목명, 4번째 셀: 금액)
                    deduction_name = cells[2].get_text(strip=True)
                    deduction_amount = cells[3].get_text(strip=True).replace(',', '').replace('원', '')

                    # 지급 항목 처리
                    if item_name and payment_amount:
                        try:
                            amount = float(payment_amount) if payment_amount.replace('.', '').isdigit() else 0
                            if '기본급' in item_name:
                                data['base_pay'] = amount
                            elif '주휴수당' in item_name:
                                data['weekly_holiday_allowance'] = amount
                            elif '연장수당' in item_name:
                                data['overtime_pay'] = amount
                            elif '야간수당' in item_name:
                                data['night_pay'] = amount
                        except (ValueError, AttributeError) as e:
                            logging.debug(f"지급 항목 금액 파싱 실패: item_name={item_name}, amount_text='{payment_amount}', error={e}")

                    # 공제 항목 처리
                    if deduction_name and deduction_amount:
                        try:
                            amount = float(deduction_amount) if deduction_amount.replace('.', '').isdigit() else 0
                            if '국민연금' in deduction_name:
                                data['national_pension'] = amount
                            elif '건강보험' in deduction_name:
                                data['health_insurance'] = amount
                            elif '고용보험' in deduction_name:
                                data['employment_insurance'] = amount
                            elif '장기요양보험' in deduction_name:
                                data['long_term_care_insurance'] = amount
                            elif '소득세' in deduction_name:
                                data['income_tax'] = amount
                            elif '지방소득세' in deduction_name:
                                data['local_income_tax'] = amount
                        except (ValueError, AttributeError) as e:
                            logging.debug(f"공제 항목 금액 파싱 실패: item_name={deduction_name}, amount_text='{deduction_amount}', error={e}")

                # 합계 행에서 총액 추출
                for tr in rows:
                    if 'total-row' in tr.get('class', []) or '합계' in tr.get_text():
                        cells = tr.find_all('td')
                        if len(cells) >= 4:
                            # 지급합계, 공제합계
                            payment_text = cells[1].get_text(strip=True).replace(',', '').replace('원', '')
                            deduction_text = cells[3].get_text(strip=True).replace(',', '').replace('원', '')

                            try:
                                data['total_payment'] = float(payment_text) if payment_text.replace('.', '').isdigit() else 0
                                data['total_deduction'] = float(deduction_text) if deduction_text.replace('.', '').isdigit() else 0
                            except (ValueError, AttributeError) as e:
                                logging.debug(f"합계 금액 파싱 실패: payment_text='{payment_text}', deduction_text='{deduction_text}', error={e}")

                # 실지급액 추출
                net_pay_row = soup.find('tr', class_='net-pay-row')
                if net_pay_row:
                    cells = net_pay_row.find_all('td')
                    if len(cells) >= 3:
                        net_pay_text = cells[1].get_text(strip=True).replace(',', '').replace('원', '')
                        try:
                            data['net_pay'] = float(net_pay_text) if net_pay_text.replace('.', '').isdigit() else 0
                        except (ValueError, AttributeError) as e:
                            logging.debug(f"실지급액 파싱 실패: net_pay_text='{net_pay_text}', error={e}")

            return data

        except Exception as e:
            print(f"HTML 데이터 추출 오류: {e}")
            return None

    def open_payroll_register(self):
        """급여대장 생성 팝업 열기"""
        try:
            from payroll_register_dialog import PayrollRegisterDialog
            dialog = PayrollRegisterDialog(self.app, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                company_name, year = dialog.get_selected_options()
                if company_name and year:
                    # 급여대장 생성
                    self.generate_payroll_register(company_name, year)
        except ImportError as e:
            QMessageBox.critical(self, "모듈 오류", f"급여대장 모듈을 찾을 수 없습니다:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"급여대장 팝업을 열 수 없습니다:\n{str(e)}")

    def generate_payroll_register(self, company_name, year):
        """급여대장 생성"""
        try:
            from payroll_register_generator import generate_payroll_register
            file_path = generate_payroll_register(company_name, year)
            if file_path:
                QMessageBox.information(self, "급여대장 생성 완료",
                    f"급여대장이 성공적으로 생성되었습니다.\n\n파일: {file_path}")
                # 파일 열기
                try:
                    os.startfile(file_path)
                except AttributeError:
                    import subprocess
                    subprocess.run(['xdg-open', file_path])
            else:
                QMessageBox.warning(self, "생성 실패", "급여대장 생성에 실패했습니다.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"급여대장 생성 중 오류가 발생했습니다:\n{str(e)}")

    def open_payslip_history(self):
        """이전 급여내역서 조회 창 열기"""
        try:
            from payslip_history_viewer import PayslipHistoryViewer
            dialog = PayslipHistoryViewer(self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.critical(self, "모듈 오류", f"필요한 모듈을 찾을 수 없습니다:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"이전 급여내역서 조회 창을 열 수 없습니다:\n{str(e)}")

    def generate_final_file(self):
        """최종 파일 생성 (HTML 전용)"""
        import os  # os 모듈 import 추가
        import glob  # glob 모듈 import 추가
        if self.app.locked:
            QMessageBox.warning(self, "라이선스 잠금",
                "라이선스가 유효하지 않아 파일을 저장할 수 없습니다.")
            return

        if self.app.summary_df is None:
            QMessageBox.critical(self, "오류", "먼저 급여 계산을 실행해주세요.")
            return

        output_mode = self.output_mode_combo.currentText()

        # 출력 경로 결정 (연도별 폴더 자동 생성)
        data_month = self.app.format_month_string(self.app.month_var)
        year = data_month.split()[0].replace('년', '')  # "2026년" → "2026"
        month = data_month.split()[1].replace('월', '')  # "12월" → "12"
        company_name_clean = self.app.config_data.get("company_name", "기본회사").replace('/', '_').replace('\\', '_')

        # 연도별 폴더 구조 생성
        save_base_folder = "급여명세서_저장본"
        year_folder = os.path.join(save_base_folder, f"{year}년")
        os.makedirs(year_folder, exist_ok=True)

        if output_mode in ["개별(모든직원)", "선택"]:
            # 개별/선택 모드: 폴더 선택 (기존 방식 유지하되 기본 폴더 제안)
            output_path = QFileDialog.getExistingDirectory(
                self, "저장할 폴더를 선택하세요",
                year_folder  # 기본적으로 연도 폴더 제안
            )
            if not output_path:
                return
            base_filename = f"급여명세서_{self.app.month_var}.html"
        else:
            # 통합 모드: 연도별 폴더에 자동 저장
            safe_month = data_month.replace(' ', '_').replace('년', 'year').replace('월', 'month')
            filename = f"{safe_month}_{company_name_clean}_통합.html"
            output_path = os.path.join(year_folder, filename)
            base_filename = None

            # 파일이 이미 존재하면 확인
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self, "파일 덮어쓰기",
                    f"파일이 이미 존재합니다:\n{output_path}\n\n덮어쓰시겠습니까?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

        # 처리 시작
        self.status_label.setText("최종 파일 생성 중...")
        self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        self.repaint()

        try:
            data_month = self.app.format_month_string(self.app.month_var)
            company_name = self.app.config_data.get("company_name", "")

            # explanation_options 수집
            explanation_options = {
                'base_pay_explanation': self.base_pay_explanation_cb.isChecked(),
                'holiday_explanation': self.holiday_explanation_cb.isChecked(),
                'night_explanation': self.night_explanation_cb.isChecked(),
                'holiday_work_explanation': self.holiday_work_explanation_cb.isChecked(),
                'overtime_explanation': self.overtime_explanation_cb.isChecked()
            }

            if output_mode == "선택":
                # 선택 모드: 직원 선택 다이얼로그 표시
                dialog = EmployeeSelectionDialog(self.app.summary_df, self)
                dialog.exec()
                if dialog.result() == QDialog.DialogCode.Accepted:
                    selected_user_ids = dialog.get_selected_ids()
                    if selected_user_ids:
                        # 선택된 직원만 개별 파일 생성 (폴더 경로만 전달)
                        logic.generate_payslips_html(
                            self.app.summary_df,
                            output_path,  # 폴더 경로만 전달
                            data_month, company_name, selected_user_ids,  # 선택된 ID들 전달
                            explanation_options=explanation_options,
                            data_file_path=self.app.selected_file_path,
                            employee_data=self.app.employee_data,
                            business_size=getattr(self.app, 'business_size', 'under_5')
                        )
                        selected_count = len(selected_user_ids)
                        QMessageBox.information(self, "성공",
                            f"선택된 {selected_count}명의 급여명세서가 성공적으로 저장되었습니다.\n\n저장 위치: {output_path}")
                        return  # 선택 모드 처리 완료
                    else:
                        QMessageBox.information(self, "알림", "선택된 직원이 없습니다.")
                        return  # 취소 처리
                else:
                    # 취소됨
                    return  # 취소 처리

            if output_mode == "개별(모든직원)":
                # 개별 파일 생성
                logic.generate_payslips_html(
                    self.app.summary_df,
                    os.path.join(output_path, base_filename),
                    data_month, company_name, [],
                    explanation_options=explanation_options,
                    data_file_path=self.app.selected_file_path,
                    employee_data=self.app.employee_data,
                    business_size=getattr(self.app, 'business_size', 'under_5')
                )
            else:  # 통합
                logic.generate_payslips_html(
                    self.app.summary_df, output_path,
                    data_month, company_name, None,
                    explanation_options=explanation_options,
                    data_file_path=self.app.selected_file_path,
                    employee_data=self.app.employee_data,
                    business_size=getattr(self.app, 'business_size', 'under_5')
                )

            self.status_label.setText("파일 생성 완료!")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            # 급여명세서 생성 완료 후 DB 저장 처리 (개별 모드만)
            if output_mode == "개별(모든직원)":
                # 개별 모드: 생성된 모든 HTML 파일을 DB에 저장 (변동사항 확인 후)
                try:
                    from database_manager import get_database
                    import glob
                    import os
                    import re
                    import uuid
                    import hashlib
                    from bs4 import BeautifulSoup

                    db = get_database()
                    saved_count = 0
                    skipped_count = 0
                    changed_count = 0

                    # 생성된 HTML 파일들 찾기
                    html_files = glob.glob(os.path.join(output_path, "*.html"))

                    for html_file in html_files:
                        try:
                            # HTML 파일 읽기
                            with open(html_file, 'r', encoding='utf-8') as f:
                                html_content = f.read()

                            # HTML에서 데이터 추출 및 계산 데이터 준비
                            new_data = self.extract_payslip_data_from_html(html_content, data_month, company_name)

                            if new_data and new_data['employee_name']:
                                employee_name = new_data['employee_name']
                                pay_month = new_data['pay_month']

                                # summary_df에서 해당 직원의 실제 계산 데이터 가져오기 (HTML 파싱 우회)
                                employee_row = None
                                for idx, row in self.app.summary_df.iterrows():
                                    if str(row.get('user_id', '')).strip() == str(new_data['employee_id']).strip():
                                        employee_row = row
                                        break

                                if employee_row is not None:
                                    logging.debug(f"summary_df에서 계산 데이터 추출: employee={employee_name}, base_pay={employee_row.get('base_pay', 0)}")

                                    # summary_df의 실제 계산 데이터를 사용 (HTML 파싱 우회)
                                    calculation_data = {
                                        'employee_id': str(employee_row.get('user_id', new_data['employee_id'])),
                                        'employee_name': employee_row.get('name', new_data['employee_name']),
                                        'pay_month': new_data['pay_month'],
                                        'base_pay': float(employee_row.get('base_pay', 0)),
                                        'weekly_holiday_allowance': float(employee_row.get('weekly_holiday_allowance', 0)),
                                        'overtime_pay': float(employee_row.get('overtime_pay', 0)),
                                        'night_pay': float(employee_row.get('night_pay', 0)),
                                        'allowance_total': float(employee_row.get('수당합계', 0)),
                                        'national_pension': float(employee_row.get('national_pension', 0)),
                                        'health_insurance': float(employee_row.get('health_insurance', 0)),
                                        'employment_insurance': float(employee_row.get('employment_insurance', 0)),
                                        'long_term_care_insurance': float(employee_row.get('long_term_care_insurance', 0)),
                                        'income_tax': float(employee_row.get('income_tax', 0)),
                                        'local_income_tax': float(employee_row.get('local_income_tax', 0)),
                                        'net_pay': float(employee_row.get('net_pay', 0)),
                                        'total_payment': float(employee_row.get('총급여액', employee_row.get('total_payment', 0))),
                                        'total_deduction': float(employee_row.get('deductions', employee_row.get('total_deduction', 0)))
                                    }
                                else:
                                    logging.warning(f"summary_df에서 직원 데이터를 찾을 수 없음: {new_data['employee_id']}")
                                    # 폴백: HTML 파싱 데이터 사용
                                    calculation_data = {
                                        'employee_id': new_data['employee_id'],
                                        'employee_name': new_data['employee_name'],
                                        'pay_month': new_data['pay_month'],
                                        'base_pay': new_data.get('base_pay', 0),
                                        'weekly_holiday_allowance': new_data.get('weekly_holiday_allowance', 0),
                                        'overtime_pay': new_data.get('overtime_pay', 0),
                                        'night_pay': new_data.get('night_pay', 0),
                                        'allowance_total': new_data.get('allowance_total', 0),
                                        'national_pension': new_data.get('national_pension', 0),
                                        'health_insurance': new_data.get('health_insurance', 0),
                                        'employment_insurance': new_data.get('employment_insurance', 0),
                                        'long_term_care_insurance': new_data.get('long_term_care_insurance', 0),
                                        'income_tax': new_data.get('income_tax', 0),
                                        'local_income_tax': new_data.get('local_income_tax', 0),
                                        'net_pay': new_data.get('net_pay', 0),
                                        'total_payment': new_data.get('total_payment', 0),
                                        'total_deduction': new_data.get('total_deduction', 0)
                                    }

                                # 기존 데이터 조회 (이제 calculation_data에서 가져옴)
                                existing_data = db.get_existing_payslip_data(new_data['employee_id'], pay_month)

                                # DB 저장용 데이터 준비
                                db_record = new_data.copy()
                                db_record['id'] = str(uuid.uuid4())
                                db_record['version'] = 1
                                db_record['html_content'] = html_content
                                db_record['calculation_data'] = json.dumps(calculation_data, ensure_ascii=False)

                                if existing_data is None:
                                    # 신규 데이터인 경우 바로 저장
                                    success = db.save_payslip_record(db_record)
                                    if success:
                                        saved_count += 1
                                        print(f"신규 저장 성공: {employee_name} ({pay_month})")
                                    else:
                                        print(f"신규 저장 실패: {employee_name} ({pay_month})")
                                else:
                                    # 기존 데이터가 있는 경우 변동사항 비교
                                    changes = db.compare_payslip_data(existing_data, calculation_data)

                                    if changes.get('has_changes', False):
                                        # 변동사항이 있는 경우 사용자 확인 다이얼로그 표시
                                        dialog = PayslipChangeConfirmationDialog(employee_name, pay_month, changes, self)
                                        result = dialog.exec()

                                        if result == QDialog.DialogCode.Accepted and dialog.user_confirmed:
                                            # 사용자가 저장 동의한 경우
                                            db_record['version'] = existing_data.get('version', 1) + 1
                                            success = db.save_payslip_record(db_record)
                                            if success:
                                                changed_count += 1
                                                print(f"변동사항 저장 성공: {employee_name} ({pay_month}) v{db_record['version']}")
                                            else:
                                                print(f"변동사항 저장 실패: {employee_name} ({pay_month})")
                                        else:
                                            # 사용자가 취소한 경우
                                            skipped_count += 1
                                            print(f"사용자 취소로 건너뜀: {employee_name} ({pay_month})")
                                    else:
                                        # 변동사항이 없는 경우
                                        skipped_count += 1
                                        print(f"변동사항 없어 건너뜀: {employee_name} ({pay_month})")
                            else:
                                print(f"데이터 추출 실패: {html_file}")

                        except Exception as e:
                            print(f"HTML 파일 DB 저장 오류 ({html_file}): {e}")

                    # 결과 메시지 표시
                    message_parts = []
                    if saved_count > 0:
                        message_parts.append(f"신규 저장: {saved_count}개")
                    if changed_count > 0:
                        message_parts.append(f"변경 저장: {changed_count}개")
                    if skipped_count > 0:
                        message_parts.append(f"건너뜀: {skipped_count}개")

                    if message_parts:
                        QMessageBox.information(self, "DB 저장 완료",
                            f"급여명세서 데이터베이스 저장이 완료되었습니다.\n\n" + "\n".join(message_parts))
                    else:
                        QMessageBox.information(self, "DB 저장 완료", "저장할 데이터가 없습니다.")

                except ImportError as e:
                    QMessageBox.warning(self, "알림", f"DB 저장에 필요한 모듈이 없습니다: {str(e)}")
                except Exception as e:
                    QMessageBox.warning(self, "알림", f"급여명세서 DB 저장 중 오류가 발생했습니다: {str(e)}")
            # 통합/선택 모드: 저장 다이얼로그 표시하지 않음 (파일만 생성)

            QMessageBox.information(self, "성공",
                f"급여명세서가 성공적으로 저장되었습니다.\n\n저장 위치: {output_path}")

        except Exception as e:
            self.status_label.setText("파일 생성 오류.")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            QMessageBox.critical(self, "파일 생성 오류", str(e))
            print(f"파일 생성 오류: {e}")


class EmployeeSelectionDialog(QDialog):
    """직원 선택 다이얼로그"""

    def __init__(self, employees_df, parent=None):
        super().__init__(parent)
        self.employees_df = employees_df
        self.selected_ids = []
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("직원 선택")
        self.setModal(True)
        self.resize(400, 500)

        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel("급여명세서를 생성할 직원을 선택하세요")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 선택 옵션
        options_layout = QHBoxLayout()

        self.select_all_cb = QCheckBox("모두 선택")
        self.select_all_cb.stateChanged.connect(self.on_select_all_changed)
        options_layout.addWidget(self.select_all_cb)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        # 직원 리스트
        self.employee_list = QListWidget()
        self.employee_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)

        # 직원 데이터 추가
        for _, row in self.employees_df.iterrows():
            user_id = str(row['user_id'])
            name = row['name']
            department = row['department'] or '부서미정'
            position = row['position'] or '직급미정'

            display_text = f"{user_id} - {name} ({department}/{position})"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, user_id)  # user_id 저장
            self.employee_list.addItem(item)

        layout.addWidget(self.employee_list)

        # 선택 개수 표시
        self.count_label = QLabel("선택된 직원: 0명")
        self.count_label.setStyleSheet("color: #666; margin-top: 5px;")
        layout.addWidget(self.count_label)

        # 선택 변경 이벤트 연결
        self.employee_list.itemSelectionChanged.connect(self.update_selection_count)

        # 버튼 박스
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_select_all_changed(self, state):
        """모두 선택/해제"""
        if state == Qt.CheckState.Checked:
            self.employee_list.selectAll()
        else:
            self.employee_list.clearSelection()

    def update_selection_count(self):
        """선택 개수 업데이트"""
        selected_count = len(self.employee_list.selectedItems())
        total_count = self.employee_list.count()
        self.count_label.setText(f"선택된 직원: {selected_count}명 / 전체: {total_count}명")

    def get_selected_ids(self):
        """선택된 직원 ID들 반환"""
        selected_items = self.employee_list.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]


class PayslipChangeConfirmationDialog(QDialog):
    """급여명세서 변동사항 확인 다이얼로그"""

    def __init__(self, employee_name, pay_month, changes, parent=None):
        super().__init__(parent)
        self.employee_name = employee_name
        self.pay_month = pay_month
        self.changes = changes
        self.user_confirmed = False
        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        self.setWindowTitle("급여명세서 변동사항 확인")
        self.setModal(True)
        self.resize(600, 700)

        layout = QVBoxLayout(self)

        # 제목
        title_label = QLabel(f"{self.employee_name}님 {self.pay_month} 급여명세서")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 변동사항 설명
        desc_label = QLabel("기존 데이터와 비교하여 다음과 같은 변동사항이 발견되었습니다:")
        desc_label.setStyleSheet("margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # 스크롤 영역
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 지급 항목 변동사항
        if self.changes.get('payment_changes'):
            payment_group = self.create_change_group("💰 지급 항목 변동", self.changes['payment_changes'], "#e8f5e8")
            scroll_layout.addWidget(payment_group)

        # 공제 항목 변동사항
        if self.changes.get('deduction_changes'):
            deduction_group = self.create_change_group("📉 공제 항목 변동", self.changes['deduction_changes'], "#ffebee")
            scroll_layout.addWidget(deduction_group)

        # 합계 항목 변동사항
        if self.changes.get('summary_changes'):
            summary_group = self.create_change_group("📊 합계 변동", self.changes['summary_changes'], "#fff3e0")
            scroll_layout.addWidget(summary_group)

        # 변동사항 없음
        if not self.changes.get('has_changes', False):
            no_change_label = QLabel("변동사항이 없습니다.")
            no_change_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            scroll_layout.addWidget(no_change_label)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # 경고 메시지
        if self.changes.get('has_changes', False):
            warning_label = QLabel("⚠️ 변동사항을 확인하시고 저장을 진행하시겠습니까?")
            warning_label.setStyleSheet("color: #f57c00; font-weight: bold; margin-top: 10px;")
            layout.addWidget(warning_label)

        # 버튼 박스
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes |
            QDialogButtonBox.StandardButton.No
        )
        button_box.button(QDialogButtonBox.StandardButton.Yes).setText("저장 진행")
        button_box.button(QDialogButtonBox.StandardButton.No).setText("취소")
        button_box.accepted.connect(self.on_accepted)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def create_change_group(self, title, changes, bg_color):
        """변동사항 그룹 생성"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 5px;
                background-color: {bg_color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout(group)

        for change in changes:
            change_layout = QHBoxLayout()

            # 항목명
            name_label = QLabel(change['name'])
            name_label.setStyleSheet("font-weight: bold; min-width: 100px;")
            change_layout.addWidget(name_label)

            # 기존 값
            old_value = f"{change['old_value']:,.0f}원"
            old_label = QLabel(f"기존: {old_value}")
            old_label.setStyleSheet("color: #666; min-width: 120px;")
            change_layout.addWidget(old_label)

            # 새 값
            new_value = f"{change['new_value']:,.0f}원"
            new_label = QLabel(f"변경: {new_value}")
            new_label.setStyleSheet("color: #1976d2; font-weight: bold; min-width: 120px;")
            change_layout.addWidget(new_label)

            # 차이
            difference = change['difference']
            diff_text = f"차이: {'+' if difference > 0 else ''}{difference:,.0f}원"
            diff_color = "#388e3c" if difference > 0 else "#d32f2f" if difference < 0 else "#666"
            diff_label = QLabel(diff_text)
            diff_label.setStyleSheet(f"color: {diff_color}; font-weight: bold;")
            change_layout.addWidget(diff_label)

            change_layout.addStretch()
            layout.addLayout(change_layout)

        return group

    def on_accepted(self):
        """사용자가 저장 진행을 선택함"""
        self.user_confirmed = True
        self.accept()


    def open_payslip_history(self):
        """이전 급여내역서 조회 창 열기"""
        try:
            from payslip_history_viewer import PayslipHistoryViewer
            dialog = PayslipHistoryViewer(self)
            dialog.exec()
        except ImportError as e:
            QMessageBox.critical(self, "모듈 오류", f"필요한 모듈을 찾을 수 없습니다:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"이전 급여내역서 조회 창을 열 수 없습니다:\n{str(e)}")


def setup_pane(app, monthly_pane):
    """
    기존 tkinter 호환성을 위한 함수
    실제로는 MonthlyPayrollPaneQt를 직접 사용하도록 변경 예정
    """
    pane = MonthlyPayrollPaneQt(app)
    layout = QVBoxLayout(monthly_pane)
    layout.addWidget(pane)
    return monthly_pane
    return monthly_pane
