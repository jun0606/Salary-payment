#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연차 관리 GUI 화면 (PyQt6)
- 연차 현황 조회
- 연차 사용 등록
- 월별 리포트
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QDateEdit,
    QDoubleSpinBox, QLineEdit, QMessageBox, QTabWidget,
    QGroupBox, QFormLayout, QHeaderView
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import logging

from annual_leave_manager import AnnualLeaveManager

logger = logging.getLogger(__name__)


class AnnualLeaveDialog(QDialog):
    """연차 관리 메인 다이얼로그"""
    
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.leave_manager = AnnualLeaveManager()
        
        self.setWindowTitle("연차 관리 시스템")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_employees()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        
        # 탭 1: 연차 현황
        self.tab_status = self.create_status_tab()
        self.tab_widget.addTab(self.tab_status, "연차 현황")
        
        # 탭 2: 연차 사용 등록
        self.tab_usage = self.create_usage_tab()
        self.tab_widget.addTab(self.tab_usage, "연차 사용 등록")
        
        # 탭 3: 사용 내역
        self.tab_history = self.create_history_tab()
        self.tab_widget.addTab(self.tab_history, "사용 내역")
        
        layout.addWidget(self.tab_widget)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def create_status_tab(self):
        """연차 현황 탭 생성"""
        widget = QDialog()
        layout = QVBoxLayout()
        
        # 직원 선택
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("직원 선택:"))
        self.combo_employee = QComboBox()
        self.combo_employee.currentTextChanged.connect(self.on_employee_changed)
        select_layout.addWidget(self.combo_employee)
        select_layout.addStretch()
        layout.addLayout(select_layout)
        
        # 연차 현황 표시
        self.group_status = QGroupBox("연차 현황")
        status_layout = QFormLayout()
        
        self.lbl_total_leave = QLabel("-")
        self.lbl_used_leave = QLabel("-")
        self.lbl_remaining_leave = QLabel("-")
        self.lbl_remaining_leave.setStyleSheet("color: #28a745; font-weight: bold; font-size: 16px;")
        
        status_layout.addRow("총 연차:", self.lbl_total_leave)
        status_layout.addRow("사용 연차:", self.lbl_used_leave)
        status_layout.addRow("잔여 연차:", self.lbl_remaining_leave)
        
        self.group_status.setLayout(status_layout)
        layout.addWidget(self.group_status)
        
        # 연차 수당 정보 (퇴사자용)
        self.group_allowance = QGroupBox("퇴사 시 연차수당 예상")
        allowance_layout = QFormLayout()
        
        self.lbl_daily_wage = QLabel("-")
        self.lbl_leave_allowance = QLabel("-")
        self.lbl_leave_allowance.setStyleSheet("color: #dc3545; font-weight: bold; font-size: 16px;")
        
        allowance_layout.addRow("1일 통상임금:", self.lbl_daily_wage)
        allowance_layout.addRow("예상 연차수당:", self.lbl_leave_allowance)
        
        self.group_allowance.setLayout(allowance_layout)
        layout.addWidget(self.group_allowance)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_usage_tab(self):
        """연차 사용 등록 탭 생성"""
        widget = QDialog()
        layout = QVBoxLayout()
        
        # 직원 선택
        form_layout = QFormLayout()
        
        self.combo_usage_employee = QComboBox()
        form_layout.addRow("직원:", self.combo_usage_employee)
        
        # 사용일
        self.date_usage = QDateEdit()
        self.date_usage.setCalendarPopup(True)
        self.date_usage.setDate(QDate.currentDate())
        form_layout.addRow("사용일:", self.date_usage)
        
        # 사용 일수
        self.spin_days = QDoubleSpinBox()
        self.spin_days.setRange(0.5, 30)
        self.spin_days.setValue(1.0)
        self.spin_days.setSingleStep(0.5)
        self.spin_days.setSuffix(" 일")
        form_layout.addRow("사용 일수:", self.spin_days)
        
        # 사유
        self.txt_reason = QLineEdit()
        self.txt_reason.setPlaceholderText("사유를 입력하세요 (예: 개인 사정)")
        form_layout.addRow("사유:", self.txt_reason)
        
        layout.addLayout(form_layout)
        
        # 등록 버튼
        btn_register = QPushButton("연차 사용 등록")
        btn_register.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_register.clicked.connect(self.register_usage)
        layout.addWidget(btn_register)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_history_tab(self):
        """사용 내역 탭 생성"""
        widget = QDialog()
        layout = QVBoxLayout()
        
        # 직원 선택
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("직원 선택:"))
        self.combo_history_employee = QComboBox()
        self.combo_history_employee.currentTextChanged.connect(self.load_history)
        select_layout.addWidget(self.combo_history_employee)
        
        # 연도 선택
        select_layout.addWidget(QLabel("연도:"))
        self.combo_year = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 2):
            self.combo_year.addItem(str(year), year)
        self.combo_year.setCurrentText(str(current_year))
        self.combo_year.currentTextChanged.connect(self.load_history)
        select_layout.addWidget(self.combo_year)
        select_layout.addStretch()
        
        layout.addLayout(select_layout)
        
        # 내역 테이블
        self.table_history = QTableWidget()
        self.table_history.setColumnCount(5)
        self.table_history.setHorizontalHeaderLabels([
            "ID", "사용일", "사용 일수", "사유", "등록일시"
        ])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_history)
        
        widget.setLayout(layout)
        return widget
    
    def load_employees(self):
        """직원 목록 로드"""
        self.combo_employee.clear()
        self.combo_usage_employee.clear()
        self.combo_history_employee.clear()
        
        for user_id, info in self.employee_data.items():
            name = info.get('name', user_id)
            display_text = f"{name} ({user_id})"
            self.combo_employee.addItem(display_text, user_id)
            self.combo_usage_employee.addItem(display_text, user_id)
            self.combo_history_employee.addItem(display_text, user_id)
            
            # 연차 관리 시스템에 직원 등록 (미등록된 경우)
            hire_date = info.get('hire_date')
            if hire_date:
                resignation_date = info.get('resignation_date')
                try:
                    self.leave_manager.add_employee(user_id, name, hire_date, resignation_date)
                except Exception as e:
                    logger.warning(f"직원 {user_id} 등록 실패: {e}")
    
    def on_employee_changed(self, text):
        """직원 변경 시 연차 현황 업데이트"""
        if not text:
            return
        
        user_id = self.combo_employee.currentData()
        if not user_id:
            return
        
        # 연차 현황 조회
        status = self.leave_manager.get_leave_status(user_id)
        if status:
            self.lbl_total_leave.setText(f"{status['annual_leave_days']:.1f}일")
            self.lbl_used_leave.setText(f"{status['used_leave_days']:.1f}일")
            self.lbl_remaining_leave.setText(f"{status['remaining_leave_days']:.1f}일")
            
            # 퇴사자인 경우 연차수당 계산
            if status['resignation_date']:
                employee = self.employee_data.get(user_id, {})
                base_pay = employee.get('base_pay', 2500000)  # 기본값
                allowance = self.leave_manager.calculate_leave_allowance(user_id, base_pay)
                if allowance:
                    self.lbl_daily_wage.setText(f"{allowance['daily_wage']:,.0f}원")
                    self.lbl_leave_allowance.setText(f"{allowance['leave_allowance']:,.0f}원")
                self.group_allowance.setVisible(True)
            else:
                self.group_allowance.setVisible(False)
    
    def register_usage(self):
        """연차 사용 등록"""
        user_id = self.combo_usage_employee.currentData()
        if not user_id:
            QMessageBox.warning(self, "경고", "직원을 선택하세요.")
            return
        
        use_date = self.date_usage.date().toString("yyyy-MM-dd")
        days = self.spin_days.value()
        reason = self.txt_reason.text()
        
        if days <= 0:
            QMessageBox.warning(self, "경고", "사용 일수는 0보다 커야 합니다.")
            return
        
        success = self.leave_manager.use_leave(user_id, use_date, days, reason)
        if success:
            QMessageBox.information(self, "성공", f"연차 사용이 등록되었습니다.\n\n사용일: {use_date}\n일수: {days}일")
            self.txt_reason.clear()
            self.on_employee_changed(None)  # 현황 갱신
        else:
            QMessageBox.warning(self, "실패", "연차 사용 등록에 실패했습니다. 잔여 연차를 확인하세요.")
    
    def load_history(self):
        """연차 사용 내역 로드"""
        user_id = self.combo_history_employee.currentData()
        if not user_id:
            return
        
        year = int(self.combo_year.currentText())
        history = self.leave_manager.get_leave_usage_history(user_id, year)
        
        self.table_history.setRowCount(len(history))
        for row, item in enumerate(history):
            self.table_history.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.table_history.setItem(row, 1, QTableWidgetItem(item['use_date']))
            self.table_history.setItem(row, 2, QTableWidgetItem(f"{item['days_used']:.1f}일"))
            self.table_history.setItem(row, 3, QTableWidgetItem(item['reason'] or "-"))
            self.table_history.setItem(row, 4, QTableWidgetItem(item['created_at']))


# 테스트용 메인 함수
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 테스트 데이터
    test_employees = {
        "TEST001": {"name": "홍길동", "hire_date": "2024-01-15"},
        "TEST002": {"name": "김철수", "hire_date": "2024-03-01", "resignation_date": "2025-12-15"}
    }
    
    dialog = AnnualLeaveDialog(test_employees)
    dialog.show()
    sys.exit(app.exec())
