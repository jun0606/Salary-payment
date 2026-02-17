#!/usr/bin/env python3
"""
급여명세서 저장 다이얼로그
급여명세서 생성 후 저장 여부를 확인하고 메모를 입력받는 UI
"""

import uuid
import hashlib
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QCheckBox, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from database_manager import get_database

class PayslipSaveDialog(QDialog):
    """
    급여명세서 저장 확인 다이얼로그

    급여명세서 생성 후 사용자에게 저장 여부를 확인하고,
    저장 시 메모를 입력받아 데이터베이스에 저장합니다.
    """

    def __init__(self, employee_name: str, pay_month: str,
                 html_content: str, company_name: str = "",
                 employee_id: str = "", parent=None):
        """
        초기화

        Args:
            employee_name: 직원명
            pay_month: 지급 월 (YYYY년 MM월 형식)
            html_content: 저장할 HTML 콘텐츠
            company_name: 회사명
            employee_id: 직원 ID
            parent: 부모 위젯
        """
        super().__init__(parent)
        self.employee_name = employee_name
        self.pay_month = pay_month
        self.html_content = html_content
        self.company_name = company_name or "기본 회사"
        self.employee_id = employee_id or f"emp_{hash(employee_name) % 10000}"

        self.db = get_database()
        self.saved = False

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("급여명세서 저장")
        self.setModal(True)
        self.resize(500, 400)

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title_label = QLabel("📄 급여명세서 저장")
        title_label.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)

        # 정보 표시 영역
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)

        # 저장할 급여명세서 정보
        info_title = QLabel("저장할 급여명세서 정보")
        info_title.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        info_layout.addWidget(info_title)

        employee_info = QLabel(f"👤 직원: {self.employee_name}")
        employee_info.setFont(QFont("맑은 고딕", 10))
        info_layout.addWidget(employee_info)

        month_info = QLabel(f"📅 지급 월: {self.pay_month}")
        month_info.setFont(QFont("맑은 고딕", 10))
        info_layout.addWidget(month_info)

        company_info = QLabel(f"🏢 회사: {self.company_name}")
        company_info.setFont(QFont("맑은 고딕", 10))
        info_layout.addWidget(company_info)

        layout.addWidget(info_frame)

        # 저장 옵션
        self.save_checkbox = QCheckBox("급여명세서를 기록에 저장합니다")
        self.save_checkbox.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        self.save_checkbox.setChecked(True)  # 기본적으로 체크
        layout.addWidget(self.save_checkbox)

        # 메모 입력 영역
        memo_label = QLabel("저장 메모 (선택사항)")
        memo_label.setFont(QFont("맑은 고딕", 10))
        layout.addWidget(memo_label)

        self.memo_edit = QTextEdit()
        self.memo_edit.setPlaceholderText(
            "급여명세서 저장 목적이나 특이사항을 입력하세요.\n"
            "예: 정규 급여 지급, 특별 보너스, 연말정산 등"
        )
        self.memo_edit.setMaximumHeight(80)
        self.memo_edit.setFont(QFont("맑은 고딕", 9))
        layout.addWidget(self.memo_edit)

        # 안내 메시지
        info_msg = QLabel(
            "💡 저장된 급여명세서는 법적 보존 기간(5년) 동안 안전하게 보관되며,\n"
            "   '이전 급여내역서 출력' 메뉴에서 언제든지 조회할 수 있습니다."
        )
        info_msg.setFont(QFont("맑은 고딕", 9))
        info_msg.setStyleSheet("color: #6c757d; padding-top: 10px;")
        info_msg.setWordWrap(True)
        layout.addWidget(info_msg)

        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(self.save_btn)

        self.skip_btn = QPushButton("건너뛰기")
        self.skip_btn.setFont(QFont("맑은 고딕", 10))
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        button_layout.addWidget(self.skip_btn)

        layout.addLayout(button_layout)

    def setup_connections(self):
        """시그널 연결"""
        self.save_checkbox.stateChanged.connect(self.on_save_checkbox_changed)
        self.save_btn.clicked.connect(self.save_payslip)
        self.skip_btn.clicked.connect(self.skip_save)

        # 초기 상태 설정
        self.on_save_checkbox_changed(self.save_checkbox.isChecked())

    def on_save_checkbox_changed(self, checked):
        """저장 체크박스 상태 변경 처리"""
        self.memo_edit.setEnabled(checked)
        self.save_btn.setEnabled(checked)

        if checked:
            self.save_btn.setText("💾 저장")
            self.skip_btn.setText("건너뛰기")
        else:
            self.save_btn.setText("확인")
            self.skip_btn.setText("확인")

    def save_payslip(self):
        """급여명세서 저장"""
        if not self.save_checkbox.isChecked():
            self.accept()
            return

        try:
            # 저장 데이터 준비
            record_id = str(uuid.uuid4())
            memo = self.memo_edit.toPlainText().strip()

            # 버전 확인
            pay_month_short = self.convert_pay_month_to_short(self.pay_month)
            latest_version = self.db.get_latest_version(self.employee_id, pay_month_short)
            version = latest_version + 1

            # 데이터 해시 생성 (무결성 검증용)
            data_hash = hashlib.sha256(self.html_content.encode()).hexdigest()

            # 저장 데이터 구성
            record = {
                'id': record_id,
                'employee_id': self.employee_id,
                'employee_name': self.employee_name,
                'company_name': self.company_name,
                'pay_month': pay_month_short,
                'version': version,
                'memo': memo,
                'html_content': self.html_content,
                'input_data_hash': data_hash,
                'file_path': getattr(self, 'file_path', None)  # 파일 경로 추가
            }

            # 데이터베이스에 저장
            success = self.db.save_payslip_record(record)

            if success:
                self.saved = True
                QMessageBox.information(
                    self, "저장 완료",
                    f"급여명세서가 성공적으로 저장되었습니다.\n\n"
                    f"직원: {self.employee_name}\n"
                    f"기간: {self.pay_month}\n"
                    f"버전: v{version}\n\n"
                    f"저장된 기록은 '이전 급여내역서 출력' 메뉴에서\n"
                    f"언제든지 조회할 수 있습니다."
                )
                self.accept()
            else:
                QMessageBox.critical(self, "저장 실패", "급여명세서 저장 중 오류가 발생했습니다.")
                self.reject()

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"급여명세서 저장 중 오류가 발생했습니다:\n{str(e)}")
            self.reject()

    def skip_save(self):
        """저장 건너뛰기"""
        if self.save_checkbox.isChecked():
            # 저장하지 않고 건너뛰기 확인
            reply = QMessageBox.question(
                self, "저장 건너뛰기",
                "급여명세서를 저장하지 않고 진행하시겠습니까?\n\n"
                "저장하지 않으면 나중에 이 급여명세서를 조회할 수 없습니다.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.saved = False
                self.accept()
        else:
            # 저장하지 않음 확인
            self.saved = False
            self.accept()

    def convert_pay_month_to_short(self, pay_month: str) -> str:
        """
        긴 월 형식(YYYY년 MM월)을 짧은 형식(YYYY-MM)으로 변환

        Args:
            pay_month: 긴 형식 월 (예: "2024년 12월")

        Returns:
            str: 짧은 형식 월 (예: "2024-12")
        """
        try:
            # "2024년 12월" → "2024-12"
            parts = pay_month.replace('년', '').replace('월', '').strip().split()
            if len(parts) == 2:
                year = parts[0]
                month = parts[1].zfill(2)
                return f"{year}-{month}"
            else:
                # 변환 실패 시 원본 반환
                return pay_month
        except:
            return pay_month

    def is_saved(self) -> bool:
        """
        급여명세서가 저장되었는지 확인

        Returns:
            bool: 저장 여부
        """
        return self.saved

    @staticmethod
    def show_save_dialog(employee_name: str, pay_month: str,
                        html_content: str, company_name: str = "",
                        employee_id: str = "", parent=None) -> bool:
        """
        급여명세서 저장 다이얼로그 표시 (정적 메서드)

        Args:
            employee_name: 직원명
            pay_month: 지급 월
            html_content: HTML 콘텐츠
            company_name: 회사명
            employee_id: 직원 ID
            parent: 부모 위젯

        Returns:
            bool: 저장 성공 여부
        """
        dialog = PayslipSaveDialog(
            employee_name, pay_month, html_content,
            company_name, employee_id, parent
        )
        dialog.exec()
        return dialog.is_saved()