#!/usr/bin/env python3
"""
PyQt6 기반 라이선스 활성화 대화상자
tkinter ActivationDialog의 PyQt6 버전

기능:
- 라이선스 코드 입력 및 검증
- 실시간 유효성 검증
- 사용자 친화적 에러 메시지
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QMessageBox, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# 라이선스 시스템
from license_system import license_verifier, hardware_id


class ActivationDialogQt(QDialog):
    """
    PyQt6 기반 라이선스 활성화 대화상자
    """

    def __init__(self, parent, message):
        super().__init__(parent)
        self.message = message
        self.activation_code = ""

        self.setWindowTitle("라이선스 활성화")
        self.setModal(True)
        self.resize(500, 400)

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 안내 메시지
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(message_label)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 코드 입력 영역
        input_group = QFrame()
        input_layout = QVBoxLayout(input_group)

        # 입력 레이블
        input_label = QLabel("활성화 코드:")
        input_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        input_layout.addWidget(input_label)

        # 코드 입력 필드 (여러 줄)
        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("활성화 코드를 붙여넣으세요...")
        self.code_input.setFont(QFont("Courier New", 10))
        self.code_input.setMaximumHeight(100)
        self.code_input.textChanged.connect(self.on_code_changed)
        input_layout.addWidget(self.code_input)

        # 입력 힌트
        hint_label = QLabel("💡 코드를 복사하여 붙여넣거나 직접 입력하세요")
        hint_label.setStyleSheet("color: #888; font-size: 12px; margin-top: 5px;")
        input_layout.addWidget(hint_label)

        layout.addWidget(input_group)

        # 상태 표시
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("margin: 10px 0;")
        layout.addWidget(self.status_label)

        # 버튼 영역
        button_layout = QHBoxLayout()

        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        # 활성화 버튼
        self.activate_btn = QPushButton("라이선스 활성화")
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.activate_btn.clicked.connect(self.activate_license)
        self.activate_btn.setEnabled(False)  # 초기에는 비활성화
        button_layout.addWidget(self.activate_btn)

        layout.addLayout(button_layout)

        # 코드 검증 타이머 (실시간 검증)
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_code_format)

    def on_code_changed(self):
        """코드 입력 시 실시간 검증"""
        code = self.code_input.toPlainText().strip()

        if len(code) > 10:  # 최소 길이 체크
            self.activate_btn.setEnabled(True)
            self.status_label.setText("✅ 코드 형식이 올바릅니다")
            self.status_label.setStyleSheet("color: #4CAF50; margin: 10px 0;")
        else:
            self.activate_btn.setEnabled(False)
            if code:
                self.status_label.setText("⚠️ 코드가 너무 짧습니다")
                self.status_label.setStyleSheet("color: #FF9800; margin: 10px 0;")
            else:
                self.status_label.setText("")
                self.status_label.setStyleSheet("margin: 10px 0;")

    def validate_code_format(self):
        """코드 형식 검증"""
        code = self.code_input.toPlainText().strip()

        if not code:
            return

        # 기본 형식 검증 (점으로 구분된 두 부분)
        if '.' not in code:
            self.status_label.setText("❌ 잘못된 코드 형식 (점(.)이 없습니다)")
            self.status_label.setStyleSheet("color: #F44336; margin: 10px 0;")
            self.activate_btn.setEnabled(False)
            return

        parts = code.split('.')
        if len(parts) != 2:
            self.status_label.setText("❌ 잘못된 코드 형식 (두 부분으로 나눠야 합니다)")
            self.status_label.setStyleSheet("color: #F44336; margin: 10px 0;")
            self.activate_btn.setEnabled(False)
            return

        # 각 부분의 최소 길이 검증
        if len(parts[0]) < 20 or len(parts[1]) < 20:
            self.status_label.setText("❌ 코드가 너무 짧습니다")
            self.status_label.setStyleSheet("color: #F44336; margin: 10px 0;")
            self.activate_btn.setEnabled(False)
            return

        # 형식 검증 통과
        self.activate_btn.setEnabled(True)

    def activate_license(self):
        """라이선스 활성화 처리"""
        code = self.code_input.toPlainText().strip()

        if not code:
            QMessageBox.warning(self, "입력 오류", "활성화 코드를 입력해주세요.")
            return

        # 버튼 비활성화 (중복 클릭 방지)
        self.activate_btn.setEnabled(False)
        self.activate_btn.setText("활성화 중...")

        # 상태 업데이트
        self.status_label.setText("🔄 라이선스를 활성화하는 중...")
        self.status_label.setStyleSheet("color: #2196F3; margin: 10px 0;")

        # UI 업데이트
        self.repaint()

        try:
            # 라이선스 코드 검증
            status, data = license_verifier.verify_activation_code(code)

            if status == 'SUCCESS':
                # HW ID 확인
                hw_id = hardware_id.get_machine_id()
                if not hw_id:
                    QMessageBox.critical(self, "시스템 오류",
                        "컴퓨터의 고유 ID를 가져올 수 없습니다.\n관리자에게 문의하세요.")
                    self.reject()
                    return

                # 라이선스 파일 생성 (새로운 분리된 시스템 사용)
                expiry_date_str = data
                success = license_verifier.LicenseManager.create_license_v2(
                    expiry_date_str, hw_id, license_verifier.LicenseType.TAX_ACCOUNTANT
                )

                if success:
                    QMessageBox.information(self, "활성화 성공",
                        "라이선스가 성공적으로 활성화되었습니다!\n\n"
                        "⚠️ 프로그램을 다시 시작해야 변경사항이 적용됩니다.\n\n"
                        "프로그램을 종료한 후 다시 실행해주세요.\n"
                        "(메뉴 [파일] → [종료] 또는 창 닫기)")

                    # 성공 코드 설정
                    self.activation_code = code
                    self.accept()

                    # 자동 재시작 제거 - 사용자 수동 재시작 유도

                else:
                    QMessageBox.critical(self, "활성화 실패",
                        "라이선스 파일 생성에 실패했습니다.\n관리자에게 문의하세요.")
                    self.reject()

            else:
                # 에러 메시지 매핑
                error_messages = {
                    'CODE_EXPIRED': "활성화 코드의 유효 시간이 만료되었습니다.\n새 코드를 요청하세요.",
                    'INVALID_SIGNATURE': "활성화 코드가 유효하지 않습니다.\n코드를 확인하세요.",
                    'PUBLIC_KEY_NOT_FOUND': "인증에 필요한 키 파일이 없습니다.\n관리자에게 문의하세요.",
                    'UNKNOWN_ERROR': "알 수 없는 오류로 활성화에 실패했습니다.\n관리자에게 문의하세요."
                }

                error_msg = error_messages.get(status,
                    "알 수 없는 오류로 활성화에 실패했습니다.\n관리자에게 문의하세요.")

                QMessageBox.critical(self, "활성화 실패", error_msg)
                self.reject()

        except Exception as e:
            QMessageBox.critical(self, "오류",
                f"라이선스 활성화 중 예기치 않은 오류가 발생했습니다:\n{str(e)}")
            self.reject()

        finally:
            # 버튼 복원
            self.activate_btn.setEnabled(True)
            self.activate_btn.setText("라이선스 활성화")



    def get_activation_code(self):
        """활성화된 코드 반환"""
        return self.activation_code if self.result() == QDialog.DialogCode.Accepted else ""


def show_activation_dialog(parent, message):
    """
    라이선스 활성화 대화상자를 표시하는 함수
    tkinter 호환성을 위한 래퍼 함수
    """
    dialog = ActivationDialogQt(parent, message)
    dialog.exec()
    return dialog.get_activation_code()
