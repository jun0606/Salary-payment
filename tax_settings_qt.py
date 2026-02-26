#!/usr/bin/env python3
"""
PyQt6 기반 세무사 설정 대화상자
tkinter tax_settings.py의 PyQt6 버전

기능:
- 세무사 정보 관리
- 라이선스 코드 생성
- HTML 파일 생성 및 열기
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QMessageBox, QDialogButtonBox,
    QTextEdit, QFrame, QProgressBar, QProgressDialog, QComboBox,
    QTabWidget, QListWidget, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QWidget, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap

import os
import datetime
import logging
import json

# 로컬 모듈
from license_system import license_generator, license_verifier
from company_manager import CompanyManager


class PasswordDialogQt(QDialog):
    """
    PyQt6 기반 비밀번호 입력 대화상자
    tkinter PasswordDialog의 PyQt6 버전
    """

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.entered_password = ""

        self.setWindowTitle("마스터 암호 입력")
        self.setModal(True)
        self.setFixedSize(350, 150)

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 안내 레이블
        info_label = QLabel("개인 키 암호를 입력하세요:")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # 비밀번호 입력
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("암호를 입력하세요")
        self.password_input.returnPressed.connect(self.check_password)
        layout.addWidget(self.password_input)

        # 버튼
        button_layout = QHBoxLayout()
        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.check_password)
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def check_password(self):
        """비밀번호 검증"""
        password = self.password_input.text()

        if not password:
            QMessageBox.warning(self, "입력 오류", "암호를 입력해주세요.")
            return

        # 개인 키 파일 존재 확인
        private_key_path = 'license_system/private_key.pem'
        if not os.path.exists(private_key_path):
            QMessageBox.critical(self, "오류", f"개인 키 파일({private_key_path})이 없습니다.\n(세무사 전용 기능)")
            return

        try:
            # 개인 키 암호 검증
            with open(private_key_path, "rb") as key_file:
                from cryptography.hazmat.primitives import serialization
                serialization.load_pem_private_key(
                    key_file.read(),
                    password=password.encode('utf-8')
                )

            self.entered_password = password
            self.accept()

        except (ValueError, TypeError):
            QMessageBox.warning(self, "인증 실패", "암호가 틀렸거나 개인 키 파일이 손상되었습니다.")
            self.password_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"알 수 없는 오류가 발생했습니다: {e}")

    def get_password(self):
        """입력된 비밀번호 반환"""
        return self.entered_password if self.result() == QDialog.DialogCode.Accepted else ""


class CodeDisplayDialogQt(QDialog):
    """
    PyQt6 기반 생성된 코드 표시 대화상자
    tkinter CodeDisplayWindow의 PyQt6 버전
    """

    def __init__(self, parent, code):
        super().__init__(parent)
        self.code = code

        self.setWindowTitle("생성된 활성화 코드")
        self.setModal(True)
        self.setFixedSize(550, 250)

        self.setup_ui()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 안내 레이블
        info_label = QLabel("코드를 복사하여 고객에게 전달하세요:")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # 코드 표시 텍스트 영역
        self.code_display = QTextEdit()
        self.code_display.setPlainText(self.code)
        self.code_display.setReadOnly(True)
        self.code_display.setFont(QFont("Courier New", 10))
        self.code_display.setFixedHeight(80)
        layout.addWidget(self.code_display)

        # 버튼 레이아웃
        button_layout = QHBoxLayout()

        # 클립보드 복사 버튼
        copy_button = QPushButton("📋 클립보드에 복사")
        copy_button.setStyleSheet("""
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
        copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_button)

        # 닫기 버튼 (저장 후 닫기)
        close_button = QPushButton("저장 후 닫기")
        close_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def copy_to_clipboard(self):
        """클립보드에 코드 복사"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.code)

        QMessageBox.information(self, "복사 완료", "활성화 코드가 클립보드에 복사되었습니다.")


class TaxSettingsDialogQt(QDialog):
    """
    PyQt6 기반 세무사 설정 메인 대화상자
    tkinter TaxSettingsDialog의 PyQt6 버전
    """

    def __init__(self, parent, app_instance, master_password):
        super().__init__(parent)
        self.parent = parent
        self.app = app_instance
        self.master_password = master_password

        self.setWindowTitle("세무사 정보 및 라이선스 관리")
        self.setModal(True)
        self.resize(550, 500)

        # 폼 데이터 저장용 딕셔너리
        self.form_vars = {}

        # 저장 상태 추적 플래그
        self.is_saved = True  # 초기 상태는 저장됨으로 설정

        self.setup_ui()
        # tkinter 버전처럼 setup_ui 완료 후 데이터 로드
        self.load_settings()
        # 라이선스 상태 초기화
        self.update_license_status()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 탭 1: 세무사 정보
        self.setup_tax_accountant_tab()

        # 탭 2: 회사 관리
        self.setup_company_management_tab()

        # 라이선스 관련 기능은 세무사 정보 탭으로 이동됨

        # 메인 버튼 그룹 (탭별로 동적 표시)
        button_layout = QHBoxLayout()

        # 정보 저장 버튼 (세무사 정보 탭 전용)
        self.save_button = QPushButton("💾 정보 저장")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        # 라이선스 초기화 버튼 (세무사 정보 탭 전용)
        self.reset_button = QPushButton("🔄 라이선스 초기화")
        self.reset_button.setStyleSheet("""
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
        self.reset_button.clicked.connect(self.reset_license)
        button_layout.addWidget(self.reset_button)

        # 닫기 버튼 (공통)
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.close_without_save)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # 탭 변경 시 버튼 상태 업데이트
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # 초기 탭 상태 설정 (세무사 정보 탭)
        self.on_tab_changed(0)

    def on_tab_changed(self, index):
        """탭 변경 시 버튼 상태 업데이트"""
        if index == 0:  # 세무사 정보 탭
            self.save_button.show()
            self.reset_button.show()
        else:  # 회사 관리 탭
            self.save_button.hide()
            self.reset_button.hide()

    def setup_tax_accountant_tab(self):
        """세무사 정보 탭 설정"""
        tax_tab = QWidget()
        self.tab_widget.addTab(tax_tab, "세무사 정보")

        layout = QVBoxLayout(tax_tab)

        # 세무사 정보 입력 그룹
        info_group = QGroupBox("세무사 정보")
        info_layout = QFormLayout(info_group)

        # 입력 필드들 (회사 관련 필드 제거)
        fields = [
            ("세무사 이름:", "tax_accountant_name"),
            ("상호명:", "tax_office_name"),
            ("전화번호:", "tax_accountant_phone"),
            ("이메일:", "tax_accountant_email"),
            ("지점명:", "tax_branch_name")
        ]

        for label_text, field_name in fields:
            self.form_vars[field_name] = QLineEdit()
            self.form_vars[field_name].setPlaceholderText(f"{label_text.replace(':', '')}을(를) 입력하세요")
            # 텍스트 변경 시 저장 상태 추적
            self.form_vars[field_name].textChanged.connect(self.on_text_changed)
            info_layout.addRow(label_text, self.form_vars[field_name])

        layout.addWidget(info_group)

        # 세무사 라이선스 활성화 그룹
        tax_license_group = QGroupBox("세무사 라이선스 활성화")
        tax_license_layout = QVBoxLayout(tax_license_group)

        # 현재 라이선스 상태 표시
        self.current_license_status = QLabel("라이선스 상태 확인 중...")
        self.current_license_status.setStyleSheet("font-weight: bold; color: #666;")
        tax_license_layout.addWidget(self.current_license_status)

        # 라이선스 관리 입력 영역
        license_input_layout = QHBoxLayout()
        license_input_layout.addWidget(QLabel("라이선스 만료일:"))

        self.tax_license_expiry_input = QLineEdit()
        self.tax_license_expiry_input.setPlaceholderText("YYYY-MM-DD 형식")
        license_input_layout.addWidget(self.tax_license_expiry_input)

        # 공유 라이선스 관리 버튼 (상태에 따라 텍스트/기능 변경)
        self.shared_license_btn = QPushButton()
        self.shared_license_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                color: white;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
        """)
        self.shared_license_btn.clicked.connect(self.handle_shared_license_button)
        license_input_layout.addWidget(self.shared_license_btn)

        tax_license_layout.addLayout(license_input_layout)

        # 라이선스 활성화 설명
        license_desc = QLabel("💡 기존 개인키를 사용하여 이 PC에 세무사 라이선스를 활성화합니다.")
        license_desc.setWordWrap(True)
        license_desc.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        tax_license_layout.addWidget(license_desc)

        layout.addWidget(tax_license_group)

        # 라이선스 생성 그룹
        license_group = QGroupBox("고객용 라이선스 코드 생성")
        license_layout = QVBoxLayout(license_group)

        # 만료일 입력
        expiry_layout = QHBoxLayout()
        expiry_layout.addWidget(QLabel("라이선스 만료일:"))
        self.expiry_input = QLineEdit()
        self.expiry_input.setPlaceholderText("YYYY-MM-DD 형식")
        expiry_layout.addWidget(self.expiry_input)

        # 코드 생성 버튼
        generate_button = QPushButton("📄 코드 생성")
        generate_button.setStyleSheet("""
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
        generate_button.clicked.connect(self.generate_code_from_ui)
        expiry_layout.addWidget(generate_button)

        license_layout.addLayout(expiry_layout)
        layout.addWidget(license_group)

    def load_settings(self):
        """설정 파일에서 데이터 로드"""
        # tkinter 버전처럼 설정 데이터를 다시 로드
        self.app.load_config()

        print(f"세무사 설정 로드 시작")
        print(f"현재 config_data: {self.app.config_data}")

        for field_name, line_edit in self.form_vars.items():
            value = self.app.config_data.get(field_name, "")
            print(f"필드 '{field_name}' 설정: '{value}'")
            line_edit.setText(value)

        print("세무사 설정 로드 완료")

    def on_text_changed(self):
        """텍스트 변경 시 저장 상태 리셋"""
        if self.is_saved:
            print("텍스트 변경 감지 - 저장 상태를 '미저장'으로 변경")
            self.is_saved = False

    def update_all_employees_business_size(self, business_size_value):
        """사업장 규모 변경 시 모든 직원 데이터에 적용"""
        try:
            # 직원 데이터 파일 로드
            import json
            employees_file = 'employees.json'

            if os.path.exists(employees_file):
                with open(employees_file, 'r', encoding='utf-8') as f:
                    employees_data = json.load(f)

                # 모든 직원에 사업장 규모 적용
                for emp_id, emp_info in employees_data.get('employees', {}).items():
                    if isinstance(emp_info, dict):
                        emp_info['business_size'] = business_size_value

                # 변경된 데이터 저장
                with open(employees_file, 'w', encoding='utf-8') as f:
                    json.dump(employees_data, f, ensure_ascii=False, indent=2)

                print(f"모든 직원 데이터에 사업장 규모 '{business_size_value}' 적용 완료")
                QMessageBox.information(
                    self, "직원 데이터 업데이트",
                    f"사업장 규모가 '{business_size_text}'으로 변경되어\n모든 직원 데이터에 적용되었습니다."
                )
            else:
                print("직원 데이터 파일이 존재하지 않음")
                QMessageBox.warning(self, "경고", "직원 데이터 파일을 찾을 수 없습니다.")

        except Exception as e:
            print(f"직원 데이터 업데이트 오류: {e}")
            QMessageBox.critical(self, "오류", f"직원 데이터 업데이트 중 오류가 발생했습니다:\n{str(e)}")

    def save_settings(self):
        """설정 데이터를 파일에 저장"""
        # 입력 데이터 수집
        new_data = {}
        for field_name, line_edit in self.form_vars.items():
            value = line_edit.text().strip()
            new_data[field_name] = value
            self.app.config_data[field_name] = value

        print(f"세무사 설정 저장 시도: {new_data}")

        # 파일에 저장
        save_result = self.app.save_config()

        if save_result:
            # 저장 상태를 True로 설정
            self.is_saved = True
            print("저장 상태를 '저장됨'으로 변경")

            # 저장 후 config_data를 최신 상태로 동기화 (CompanyManager 등에서 저장한 내용 반영)
            self.app.load_config()

            # UI 업데이트
            self.app.run_license_check()

            QMessageBox.information(self, "저장 완료", "세무사 정보가 성공적으로 저장되었습니다.")
            print("세무사 설정 저장 성공")
        else:
            QMessageBox.critical(self, "저장 실패", "세무사 정보 저장에 실패했습니다.\n콘솔 로그를 확인해주세요.")
            print("세무사 설정 저장 실패")

    def reset_license(self):
        """라이선스 초기화"""
        reply = QMessageBox.question(
            self, "초기화 확인",
            "현재 PC에 귀속된 라이선스 정보를 삭제하시겠습니까?\n프로그램을 다시 활성화해야 합니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                license_file = license_verifier.LICENSE_FILE_PATH
                if os.path.exists(license_file):
                    os.remove(license_file)
                    QMessageBox.information(
                        self, "초기화 완료",
                        "라이선스 정보가 삭제되었습니다. 프로그램을 재시작합니다."
                    )

                    # 재시작
                    QTimer.singleShot(1000, self.restart_app)
                else:
                    QMessageBox.information(self, "안내", "삭제할 라이선스 정보가 없습니다.")

            except PermissionError:
                QMessageBox.critical(
                    self, "권한 오류",
                    "라이선스 파일을 삭제할 권한이 없습니다.\n관리자 권한으로 실행해보세요."
                )
            except OSError as e:
                QMessageBox.critical(
                    self, "파일 오류",
                    f"라이선스 파일 삭제 중 시스템 오류 발생: {e}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "오류",
                    f"라이선스 초기화 중 예기치 않은 오류 발생: {e}"
                )

    def generate_code_from_ui(self):
        """UI에서 코드 생성 (개선된 버전: 진행상황 표시 및 압축 파일 생성)"""
        expiry_date_str = self.expiry_input.text().strip()

        if not expiry_date_str:
            QMessageBox.warning(self, "입력 오류", "라이선스 만료일을 입력해주세요.")
            return

        try:
            # 날짜 형식 검증
            datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            QMessageBox.critical(
                self, "입력 오류",
                "라이선스 만료일 형식이 올바르지 않습니다 (YYYY-MM-DD)."
            )
            return

        # 진행상황 대화상자 생성
        progress_dialog = QProgressDialog("라이선스 코드 생성 중...", "취소", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setAutoReset(False)
        progress_dialog.setAutoClose(False)
        progress_dialog.show()

        try:
            # 단계 1: 활성화 코드 생성
            progress_dialog.setLabelText("활성화 코드 생성 중...")
            progress_dialog.setValue(10)

            code = license_generator.generate_activation_code(expiry_date_str, license_verifier.ACTIVATION_WINDOW_MINUTES, self.master_password)

            if not code:
                progress_dialog.close()
                QMessageBox.critical(
                    self, "생성 실패",
                    "활성화 코드 생성에 실패했습니다.\n터미널/콘솔 로그를 확인하세요."
                )
                return

            # 단계 2: HTML 파일 생성
            progress_dialog.setLabelText("라이선스 HTML 파일 생성 중...")
            progress_dialog.setValue(40)

            # HTML 파일 생성 및 열기
            self.create_activation_html_file(code, expiry_date_str)

            # 단계 3: 세무사 라이선스 생성
            progress_dialog.setLabelText("세무사 라이선스 생성 중...")
            progress_dialog.setValue(50)

            # 세무사 자신의 PC에 라이선스 설치 (HW ID 기반)
            from license_system.hardware_id import get_machine_id
            tax_accountant_hw_id = get_machine_id()

            if tax_accountant_hw_id:
                tax_license_success = license_verifier.LicenseManager.create_license_v2(
                    expiry_date_str, tax_accountant_hw_id, license_verifier.LicenseType.TAX_ACCOUNTANT
                )

                if tax_license_success:
                    progress_dialog.setLabelText("세무사 라이선스 생성 완료")
                    print("✓ 세무사 라이선스가 PC에 설치되었습니다.")
                else:
                    progress_dialog.setLabelText("세무사 라이선스 생성 실패")
                    print("⚠️ 세무사 라이선스 생성에 실패했지만 계속 진행합니다.")
            else:
                print("⚠️ HW ID를 가져올 수 없어 세무사 라이선스 생성을 건너뜁니다.")

            # 단계 4: 고객용 패키지 생성
            progress_dialog.setLabelText("고객용 압축 패키지 생성 중...")
            progress_dialog.setValue(80)

            # 라이선스 생성 완료 후 즉시 고객용 패키지 생성
            package_result = self.create_customer_package_for_tax_accountant(expiry_date_str)

            # 단계 5: 완료
            progress_dialog.setLabelText("완료!")
            progress_dialog.setValue(100)

            # 잠시 대기 후 닫기
            QTimer.singleShot(500, progress_dialog.close)

            # 결과 안내
            if package_result:
                self.show_generation_success_dialog(package_result, expiry_date_str)
            else:
                QMessageBox.warning(
                    self, "부분 성공",
                    "라이선스 코드와 HTML 파일은 생성되었지만,\n압축 패키지 생성에 실패했습니다.\n수동으로 파일들을 준비해서 전달해주세요."
                )

        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(
                self, "오류",
                f"라이선스 생성 중 예기치 않은 오류가 발생했습니다:\n{str(e)}"
            )

    def create_customer_package_for_tax_accountant(self, expiry_date):
        """세무사 측에서 고객용 배포 패키지 생성"""
        try:
            # 고객 HW ID는 모르므로 더미 값 사용 (실제 라이선스는 고객이 활성화할 때 생성됨)
            dummy_hw_id = "TAX_ACCOUNTANT_PREPARED"  # 세무사가 준비한 패키지 표시

            print(f"압축 파일 생성 시작: 만료일={expiry_date}, HW_ID={dummy_hw_id}")

            # license_verifier의 create_customer_package 함수 호출
            result = license_verifier.create_customer_package(expiry_date, dummy_hw_id)

            print(f"압축 파일 생성 결과: {result}")

            # 결과 반환 (UI 표시를 위한)
            return result

        except Exception as e:
            print(f"고객 패키지 생성 상세 오류: {e}")
            import traceback
            traceback.print_exc()
            return None

    def show_generation_success_dialog(self, package_path, expiry_date):
        """라이선스 생성 완료 후 성공 대화상자 표시"""
        try:
            # 파일명 추출
            package_filename = os.path.basename(package_path)
            package_dir = os.path.dirname(package_path)

            # HTML 파일명 찾기 (가장 최근 것)
            html_files = [f for f in os.listdir('.') if f.startswith('라이선스_활성화_코드_') and f.endswith('.html')]
            html_filename = html_files[-1] if html_files else "라이선스_활성화_코드_*.html"

            success_dialog = QMessageBox(self)
            success_dialog.setWindowTitle("라이선스 생성 완료")
            success_dialog.setIcon(QMessageBox.Icon.Information)

            success_message = f"""
🎉 라이선스 코드 및 파일 생성이 완료되었습니다!

📅 라이선스 만료일: {expiry_date}

📦 생성된 파일들:
• HTML 파일: {html_filename}
• 압축 패키지: {package_filename}

📂 저장 위치: {package_dir}

💡 다음 단계:
1. HTML 파일({html_filename})을 이메일에 첨부하여 고객에게 전달
2. 압축 파일({package_filename})을 별도로 전달하거나 함께 전달
3. 고객이 HTML 파일을 열고 코드를 복사하여 프로그램에 입력

⚠️ 중요: HTML 파일의 코드는 10분 후 만료됩니다.
"""

            success_dialog.setText(success_message)

            # 버튼 설정
            open_folder_button = success_dialog.addButton("📁 폴더 열기", QMessageBox.ButtonRole.ActionRole)
            copy_path_button = success_dialog.addButton("📋 경로 복사", QMessageBox.ButtonRole.ActionRole)
            close_button = success_dialog.addButton("닫기", QMessageBox.ButtonRole.AcceptRole)

            success_dialog.exec()

            # 버튼 클릭 처리
            clicked_button = success_dialog.clickedButton()

            if clicked_button == open_folder_button:
                try:
                    os.startfile(package_dir)
                except AttributeError:
                    import subprocess
                    subprocess.run(['explorer', package_dir])  # Windows 탐색기
                except Exception as e:
                    QMessageBox.warning(self, "폴더 열기 실패", f"폴더를 열 수 없습니다: {e}")

            elif clicked_button == copy_path_button:
                from PyQt6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(package_dir)
                QMessageBox.information(self, "경로 복사", "폴더 경로가 클립보드에 복사되었습니다.")

        except Exception as e:
            QMessageBox.critical(
                self, "대화상자 오류",
                f"결과 표시 중 오류가 발생했습니다:\n{str(e)}"
            )

    def create_activation_html_file(self, activation_code, expiry_date):
        """활성화 코드를 포함한 HTML 파일 생성"""
        try:
            # 세무사 정보 가져오기
            tax_accountant_name = self.form_vars["tax_accountant_name"].text() or "세무사"
            tax_office_name = self.form_vars["tax_office_name"].text() or "세무회계사무소"

            # 회사 정보 가져오기 (메인 화면 선택 회사 우선 사용)
            company_name = "회사"  # 기본값

            # 1단계: 메인 화면에서 선택된 회사 우선 확인
            if hasattr(self.app, 'company_selector') and self.app.company_selector:
                selected_company = self.app.company_selector.currentText()
                if selected_company and selected_company != "기본 회사":
                    # 선택된 회사가 유효한지 검증
                    if self._is_valid_company_selection(selected_company):
                        company_name = selected_company
                        print(f"라이선스 HTML에 메인 화면 선택 회사 사용: {company_name}")
                    else:
                        print(f"선택된 회사가 유효하지 않아 폴백 사용: {selected_company}")

            # 2단계: 메인 화면 선택이 없거나 유효하지 않으면 기존 방식으로 폴백
            if company_name == "회사":  # 기본값 그대로라면 폴백 실행
                try:
                    if os.path.exists('config.json'):
                        with open('config.json', 'r', encoding='utf-8') as f:
                            config_data = json.load(f)

                        companies = config_data.get('companies', {})
                        if companies:
                            # 첫 번째 회사의 이름 사용 (기존 방식)
                            first_company_id = next(iter(companies))
                            company_info = companies[first_company_id]
                            company_name = company_info.get('name', '회사')
                            print(f"라이선스 HTML에 폴백 회사 사용: {company_name}")
                except Exception as e:
                    print(f"회사 정보 로드 실패: {e}")

            # 코드 생성 시각 및 유효시간 계산 (UTC로 동기화)
            generated_at = datetime.datetime.now(datetime.timezone.utc)
            expiry_time = generated_at + datetime.timedelta(minutes=10)  # 10분 유효시간
            expiry_timestamp = int(expiry_time.timestamp() * 1000)  # 밀리초 타임스탬프

            # 로컬 시간으로 표시 (UTC가 아닌 사용자 지역 시간)
            expiry_time_local = expiry_time.astimezone()
            expiry_time_str = expiry_time_local.strftime("%H:%M:%S")

            # 생성 시각도 로컬 시간으로 변환하여 표시
            generated_at_local = generated_at.astimezone()

            # HTML 템플릿 (간소화된 버전)
            html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>라이선스 활성화 코드</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', '맑은 고딕', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
            max-width: 600px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: #2c3e50;
        }}
        .code-section {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #4CAF50;
        }}
        .code-display {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Courier New', Consolas, monospace;
            font-size: 14px;
            word-break: break-all;
            margin: 10px 0;
        }}
        .copy-btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }}
        .copy-btn:hover {{
            background: #45a049;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .info-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #eee;
        }}
        .info-table .label {{
            font-weight: bold;
            width: 100px;
        }}
        .instructions {{
            background: #e8f5e8;
            border: 1px solid #4CAF50;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .instructions ol {{
            margin: 0;
            padding-left: 20px;
        }}
        .countdown {{
            font-size: 18px;
            font-weight: bold;
            color: #F44336;
            text-align: center;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 급여명세서 프로그램</h1>
            <h2>라이선스 활성화 코드</h2>
        </div>

        <div class="code-section">
            <h3>🔑 활성화 코드</h3>
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 10px; margin: 10px 0; text-align: center;">
                ⚠️ <strong>중요:</strong> 이 코드는 생성 후 <strong>10분</strong> 동안만 유효합니다.<br>
                <span style="color: #d39e00; font-size: 16px;">{expiry_time_str}</span> 까지 사용 가능
            </div>
            <p>아래 버튼을 클릭하여 코드를 복사한 후, 프로그램에 붙여넣으세요.</p>
            <div class="code-display" id="activation-code">{activation_code}</div>
            <div class="countdown" id="countdown">남은 시간: 10:00</div>
            <button class="copy-btn" onclick="copyCode()">📋 코드 복사하기</button>
            <span id="copy-status" style="margin-left: 15px; font-weight: bold;"></span>
        </div>

        <table class="info-table">
            <tr>
                <td class="label">세무사:</td>
                <td>{tax_accountant_name}</td>
            </tr>
            <tr>
                <td class="label">상호명:</td>
                <td>{tax_office_name}</td>
            </tr>
            <tr>
                <td class="label">회사:</td>
                <td>{company_name}</td>
            </tr>
            <tr>
                <td class="label">만료일:</td>
                <td>{expiry_date}</td>
            </tr>
            <tr>
                <td class="label">코드 생성:</td>
                <td>{generated_at_local.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
        </table>

        <div class="instructions">
            <h3>📖 사용 방법</h3>
            <ol>
                <li>위 "코드 복사하기" 버튼을 클릭하세요</li>
                <li>급여명세서 프로그램을 실행하세요</li>
                <li>메뉴에서 "라이선스 활성화"를 선택하세요</li>
                <li>복사한 코드를 입력창에 붙여넣고 확인을 클릭하세요</li>
                <li>프로그램이 정상적으로 활성화됩니다</li>
            </ol>
            <p style="color: #F44336; font-weight: bold; margin-top: 15px;">
                ⚠️ 코드가 만료되면 새 코드를 다시 생성해야 합니다.
            </p>
        </div>
    </div>

    <script>
        // 카운트다운 기능 (밀리초 타임스탬프 사용으로 정확한 동기화)
        let expiryTime = {expiry_timestamp};

        function updateCountdown() {{
            const now = new Date().getTime();
            const distance = expiryTime - now;

            if (distance <= 0) {{
                document.getElementById('countdown').innerHTML = '⏰ 코드 만료됨';
                document.getElementById('countdown').style.color = '#F44336';
                document.querySelector('.copy-btn').disabled = true;
                document.querySelector('.copy-btn').innerHTML = '⏰ 만료됨';
                document.querySelector('.copy-btn').style.background = '#9E9E9E';
                return;
            }}

            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            document.getElementById('countdown').innerHTML = '남은 시간: ' + minutes + ':' + (seconds < 10 ? '0' : '') + seconds;

            // 1분 이하로 남으면 빨간색으로 변경
            if (minutes === 0 && seconds <= 60) {{
                document.getElementById('countdown').style.color = '#F44336';
            }}
        }}

        // 1초마다 카운트다운 업데이트
        setInterval(updateCountdown, 1000);
        updateCountdown(); // 초기 실행

        function copyCode() {{
            const codeElement = document.getElementById('activation-code');
            const statusElement = document.getElementById('copy-status');
            const code = codeElement.textContent;

            // 클립보드에 복사
            navigator.clipboard.writeText(code).then(function() {{
                statusElement.innerHTML = '✅ 코드가 클립보드에 복사되었습니다!';
                statusElement.style.color = '#4CAF50';

                // 3초 후 상태 메시지 제거
                setTimeout(function() {{
                    statusElement.innerHTML = '';
                }}, 3000);
            }}).catch(function(err) {{
                // 대체 방법 (구형 브라우저용)
                const textArea = document.createElement('textarea');
                textArea.value = code;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);

                statusElement.innerHTML = '✅ 코드가 클립보드에 복사되었습니다!';
                statusElement.style.color = '#4CAF50';

                setTimeout(function() {{
                    statusElement.innerHTML = '';
                }}, 3000);
            }});
        }}
    </script>
</body>
</html>"""

            # 파일명 생성 (날짜 포함)
            current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"라이선스_활성화_코드_{current_date}.html"

            # HTML 파일 저장
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_template)

            # 파일 자동 열기
            try:
                os.startfile(filename)
            except AttributeError:
                # Linux/Mac에서는 다른 방법 사용
                import subprocess
                subprocess.run(['xdg-open', filename])

            QMessageBox.information(
                self, "HTML 파일 생성 완료",
                f"'{filename}' 파일이 생성되었습니다.\n\n"
                "이 파일을 이메일에 첨부하거나 고객에게 전달하세요.\n"
                "고객은 파일을 열고 '코드 복사하기' 버튼을 클릭하면 됩니다."
            )

        except Exception as e:
            QMessageBox.critical(
                self, "파일 생성 오류",
                f"HTML 파일 생성 중 오류가 발생했습니다:\n{str(e)}"
            )
            print(f"HTML 파일 생성 오류: {e}")

    def _is_valid_company_selection(self, company_name):
        """선택된 회사가 config.json에 실제로 존재하는지 검증"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                companies = config_data.get('companies', {})
                for company_info in companies.values():
                    if company_info.get('name') == company_name:
                        return True
            return False
        except Exception as e:
            print(f"회사 검증 중 오류: {e}")
            return False

    def close_without_save(self):
        """저장하지 않고 창 닫기"""
        # 이미 저장된 상태라면 바로 닫기
        if self.is_saved:
            print("저장 상태 확인: 이미 저장됨 - 바로 닫기")
            self.reject()
            return

        # 변경사항 확인
        has_unsaved_changes = False
        for field_name, line_edit in self.form_vars.items():
            current_value = line_edit.text().strip()
            saved_value = self.app.config_data.get(field_name, "")
            if current_value != saved_value:
                has_unsaved_changes = True
                break

        # 변경사항이 없다면 바로 닫기
        if not has_unsaved_changes:
            print("변경사항 없음 - 바로 닫기")
            self.reject()
            return

        # 저장되지 않은 변경사항이 있는 경우에만 확인
        reply = QMessageBox.question(
            self, "저장 확인",
            "변경사항이 저장되지 않았습니다.\n저장하지 않고 닫으시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reject()  # 저장하지 않고 닫기

    def closeEvent(self, event):
        """창 닫기 이벤트 - 자동 저장"""
        # 이미 저장된 상태라면 바로 닫기
        if self.is_saved:
            print("창 닫기 이벤트: 이미 저장됨 - 바로 닫기")
            event.accept()
            return

        # 변경사항이 있는지 확인하고 자동 저장
        has_changes = False
        for field_name, line_edit in self.form_vars.items():
            current_value = line_edit.text().strip()
            saved_value = self.app.config_data.get(field_name, "")
            if current_value != saved_value:
                has_changes = True
                break

        # 변경사항이 없다면 바로 닫기
        if not has_changes:
            print("창 닫기 이벤트: 변경사항 없음 - 바로 닫기")
            event.accept()
            return

        # 저장되지 않은 변경사항이 있는 경우에만 확인
        reply = QMessageBox.question(
            self, "자동 저장",
            "변경사항이 있습니다. 자동으로 저장하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 자동 저장
            self.save_settings()
            event.accept()
        elif reply == QMessageBox.StandardButton.No:
            # 저장하지 않고 닫기
            event.accept()
        else:
            # 취소
            event.ignore()

    def activate_tax_accountant_license(self):
        """세무사 라이선스 활성화"""
        expiry_date_str = self.tax_license_expiry_input.text().strip()

        if not expiry_date_str:
            QMessageBox.warning(self, "입력 오류", "라이선스 만료일을 입력해주세요.")
            return

        try:
            # 날짜 형식 검증
            datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            QMessageBox.critical(
                self, "입력 오류",
                "라이선스 만료일 형식이 올바르지 않습니다 (YYYY-MM-DD)."
            )
            return

        # 버튼 비활성화 (중복 클릭 방지)
        self.shared_license_btn.setEnabled(False)
        self.shared_license_btn.setText("라이선스 활성화 중...")

        try:
            # HW ID 가져오기
            from license_system.hardware_id import get_machine_id
            hw_id = get_machine_id()

            if not hw_id:
                QMessageBox.critical(self, "시스템 오류", "컴퓨터의 고유 ID를 가져올 수 없습니다.")
                return

            # 세무사 라이선스 생성 (기존 검증된 개인키 사용)
            success = license_verifier.LicenseManager.create_license_v2(
                expiry_date_str, hw_id, license_verifier.LicenseType.TAX_ACCOUNTANT
            )

            if success:
                # 성공 메시지
                QMessageBox.information(
                    self, "라이선스 활성화 성공",
                    f"세무사 라이선스가 성공적으로 활성화되었습니다!\n\n"
                    f"만료일: {expiry_date_str}\n"
                    f"라이선스 타입: 세무사용\n\n"
                    f"⚠️ 프로그램을 다시 시작해야 변경사항이 적용됩니다.\n"
                    f"프로그램을 종료한 후 다시 실행해주세요.\n"
                    f"(메뉴 [파일] → [종료] 또는 창 닫기)"
                )

                # 라이선스 상태 업데이트
                self.update_license_status()

                # 자동 재시작 제거 - 사용자 수동 재시작 유도

            else:
                QMessageBox.critical(
                    self, "활성화 실패",
                    "세무사 라이선스 활성화에 실패했습니다.\n관리자에게 문의하세요."
                )

        except Exception as e:
            QMessageBox.critical(
                self, "오류",
                f"라이선스 활성화 중 예기치 않은 오류가 발생했습니다:\n{str(e)}"
            )

        finally:
            # 버튼 복원 (공유 버튼 사용)
            self.shared_license_btn.setEnabled(True)
            # 버튼 상태는 update_shared_license_button에서 자동으로 설정됨

    def update_license_status(self):
        """라이선스 상태 표시 업데이트 및 버튼 상태 동기화"""
        try:
            # 현재 라이선스 상태 확인
            status = license_verifier.LicenseManager.check_license_v2(
                license_verifier.LicenseType.TAX_ACCOUNTANT
            )

            if status == 'LICENSED':
                self.current_license_status.setText("✅ 세무사 라이선스 활성화됨")
                self.current_license_status.setStyleSheet("font-weight: bold; color: #4CAF50;")
            elif status == 'EXPIRED':
                self.current_license_status.setText("⏰ 세무사 라이선스 만료됨")
                self.current_license_status.setStyleSheet("font-weight: bold; color: #FF9800;")
            elif status == 'INVALID_LICENSE':
                self.current_license_status.setText("❌ 세무사 라이선스 인증 실패")
                self.current_license_status.setStyleSheet("font-weight: bold; color: #F44336;")
            elif status == 'NOT_LICENSED':
                self.current_license_status.setText("🔒 세무사 라이선스 없음 (비활성화)")
                self.current_license_status.setStyleSheet("font-weight: bold; color: #FF9800;")
            else:
                # 진짜 시스템 오류인 경우에만 "상태 확인 불가" 표시
                self.current_license_status.setText("❓ 라이선스 상태 확인 불가")
                self.current_license_status.setStyleSheet("font-weight: bold; color: #666;")

            # 공유 버튼 상태 업데이트
            self.update_shared_license_button(status)

        except Exception as e:
            self.current_license_status.setText("❌ 라이선스 상태 확인 오류")
            self.current_license_status.setStyleSheet("font-weight: bold; color: #F44336;")
            print(f"라이선스 상태 업데이트 오류: {e}")

    def update_shared_license_button(self, license_status):
        """공유 라이선스 버튼의 상태를 동적으로 업데이트"""
        if license_status == 'LICENSED':
            # 라이선스가 활성화된 상태: 제거 버튼으로 변경
            self.shared_license_btn.setText("🗑️ 세무사 라이선스 제거")
            self.shared_license_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
        else:
            # 라이선스가 없는 상태: 활성화 버튼으로 변경
            self.shared_license_btn.setText("🔑 세무사 라이선스 활성화")
            self.shared_license_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)

    def handle_shared_license_button(self):
        """공유 라이선스 버튼 클릭 처리 - 상태에 따라 적절한 기능 호출"""
        try:
            # 현재 라이선스 상태 확인
            current_status = license_verifier.LicenseManager.check_license_v2(
                license_verifier.LicenseType.TAX_ACCOUNTANT
            )

            if current_status == 'LICENSED':
                # 라이선스가 있으면 제거 기능 호출
                self.remove_tax_accountant_license()
            else:
                # 라이선스가 없으면 활성화 기능 호출
                self.activate_tax_accountant_license()

        except Exception as e:
            QMessageBox.critical(
                self, "오류",
                f"라이선스 버튼 처리 중 오류가 발생했습니다:\n{str(e)}"
            )

    def remove_tax_accountant_license(self):
        """세무사 라이선스 제거"""
        # 안전한 확인 절차
        reply = QMessageBox.question(
            self, "라이선스 제거 확인",
            "세무사 라이선스를 제거하시겠습니까?\n\n"
            "⚠️ 주의사항:\n"
            "• 이 PC의 세무사 라이선스가 영구적으로 삭제됩니다\n"
            "• 프로그램이 '기능 제한' 모드로 전환됩니다\n"
            "• 재활성화를 위해서는 새 라이선스를 생성해야 합니다\n\n"
            "계속하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 버튼 비활성화 (중복 클릭 방지)
        self.shared_license_btn.setEnabled(False)
        self.shared_license_btn.setText("라이선스 제거 중...")

        try:
            # 세무사 라이선스 파일 경로 확인
            license_dir, license_file = license_verifier.LicenseManager.get_license_paths(
                license_verifier.LicenseType.TAX_ACCOUNTANT
            )

            # 라이선스 파일 존재 확인
            if not os.path.exists(license_file):
                QMessageBox.information(
                    self, "안내",
                    "제거할 세무사 라이선스가 없습니다.\n이미 제거되었거나 존재하지 않습니다."
                )
                return

            # 라이선스 파일 삭제
            try:
                os.remove(license_file)
                print(f"세무사 라이선스 파일 삭제 완료: {license_file}")
            except PermissionError:
                QMessageBox.critical(
                    self, "권한 오류",
                    "라이선스 파일을 삭제할 권한이 없습니다.\n관리자 권한으로 실행해보세요."
                )
                return
            except OSError as e:
                QMessageBox.critical(
                    self, "파일 오류",
                    f"라이선스 파일 삭제 중 오류가 발생했습니다:\n{str(e)}"
                )
                return

            # 라이선스 제거 성공 - 즉시 기능 제한 적용
            print(f"세무사 라이선스 제거 완료: {license_file}")

            # 즉시 기능 제한 모드 적용 (메인 윈도우에 적용)
            self.app.locked = True
            self.app._lock_application_features()

            # 메인 윈도우 라이선스 상태 표시 즉시 업데이트
            self.app.run_license_check()

            # 라이선스 상태 업데이트
            self.update_license_status()

            # 성공 메시지 및 강제 종료 안내
            QMessageBox.warning(
                self, "라이선스 제거 완료 - 프로그램 종료 필요",
                "세무사 라이선스가 성공적으로 제거되었습니다!\n\n"
                "⚠️ 즉시 프로그램이 종료됩니다.\n\n"
                "재활성화를 위해서는 프로그램을 다시 실행한 후\n"
                "라이선스를 새로 활성화해야 합니다.\n\n"
                "프로그램이 자동으로 종료됩니다..."
            )

            # 라이선스 제거 후 강제 프로그램 종료 (사용자 선택 없음)
            QTimer.singleShot(2000, self.app.close)  # 2초 후 자동 종료

        except Exception as e:
            QMessageBox.critical(
                self, "오류",
                f"라이선스 제거 중 예기치 않은 오류가 발생했습니다:\n{str(e)}"
            )

        finally:
            # 버튼 복원 (공유 버튼 사용)
            self.shared_license_btn.setEnabled(True)
            # 버튼 상태는 update_shared_license_button에서 자동으로 설정됨




    def setup_company_management_tab(self):
        """회사 관리 탭 설정"""
        company_tab = QWidget()
        self.tab_widget.addTab(company_tab, "회사 관리")

        # MainWindow에서 생성된 공유 CompanyManager 인스턴스 사용
        if hasattr(self.app, 'company_manager') and self.app.company_manager:
            self.company_manager = self.app.company_manager
            print("상위 MainWindow의 공유 CompanyManager 사용")
        else:
            # 폴백: MainWindow에 없으면 새로 생성 (권장되지 않음)
            from company_manager import CompanyManager
            self.company_manager = CompanyManager()
            print("주의: 공유 CompanyManager를 찾을 수 없어 새로 생성함")

        # 현재 선택된 회사 ID 추적
        self.selected_company_id = None

        # 시그널 연결 (이미 연결되어 있을 수도 있지만 안전을 위해 연결 확인)
        try:
            # 중복 연결 방지를 위해 먼저 해제 시도 (필요한 경우)
            try:
                self.company_manager.company_changed.disconnect(self.on_company_changed)
            except:
                pass
            self.company_manager.company_changed.connect(self.on_company_changed)
        except Exception as e:
            print(f"시그널 연결 오류: {e}")

        layout = QVBoxLayout(company_tab)

        # 회사 정보 입력 그룹
        company_group = QGroupBox("회사 정보")
        company_layout = QFormLayout(company_group)

        # 회사 정보 입력 필드
        self.company_form_vars = {
            "company_name": QLineEdit(),
            "company_business_size": QComboBox(),
            "company_industry": QLineEdit(),
            "company_tax_office": QLineEdit(),
            "company_registration": QLineEdit()
        }

        # 사업장 규모 드롭다운 설정
        self.company_form_vars["company_business_size"].addItems([
            "5인 이상 사업장",
            "5인 미만 사업장"
        ])

        # 폼 레이아웃
        company_layout.addRow("회사명:", self.company_form_vars["company_name"])
        company_layout.addRow("사업장 규모:", self.company_form_vars["company_business_size"])
        company_layout.addRow("업종:", self.company_form_vars["company_industry"])
        company_layout.addRow("세무서:", self.company_form_vars["company_tax_office"])
        company_layout.addRow("사업자등록번호:", self.company_form_vars["company_registration"])

        layout.addWidget(company_group)

        # 회사 목록 그룹
        list_group = QGroupBox("등록된 회사 목록")
        list_layout = QVBoxLayout(list_group)

        # 회사 목록 테이블
        self.company_table = QTableWidget()
        self.company_table.setColumnCount(5)
        self.company_table.setHorizontalHeaderLabels([
            "회사명", "사업장 규모", "업종", "세무서", "등록번호"
        ])
        self.company_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.company_table.setAlternatingRowColors(True)

        # 컬럼별 최소 너비 설정 (동적 조정)
        self.company_table.setColumnWidth(0, 150)  # 회사명
        self.company_table.setColumnWidth(1, 120)  # 사업장 규모
        self.company_table.setColumnWidth(2, 100)  # 업종
        self.company_table.setColumnWidth(3, 100)  # 세무서
        self.company_table.setColumnWidth(4, 130)  # 등록번호

        # 동적 컬럼 조정 및 마지막 컬럼 stretch
        self.company_table.resizeColumnsToContents()
        self.company_table.horizontalHeader().setStretchLastSection(True)

        # 테이블 행 선택 시 입력 필드 업데이트 연결
        self.company_table.itemSelectionChanged.connect(self.on_company_table_selection_changed)

        list_layout.addWidget(self.company_table)
        layout.addWidget(list_group)

        # 회사 관리 버튼 그룹 (탭 내부)
        company_button_layout = QHBoxLayout()

        # 회사 정보 저장 버튼
        company_save_button = QPushButton("💾 회사 정보 저장")
        company_save_button.clicked.connect(self.save_company_info)
        company_button_layout.addWidget(company_save_button)

        # 회사 추가 버튼
        add_company_button = QPushButton("➕ 회사 추가")
        add_company_button.clicked.connect(self.add_new_company)
        company_button_layout.addWidget(add_company_button)

        # 회사 삭제 버튼
        delete_company_button = QPushButton("🗑️ 회사 삭제")
        delete_company_button.clicked.connect(self.delete_selected_company)
        company_button_layout.addWidget(delete_company_button)

        layout.addLayout(company_button_layout)

        # 초기 데이터 로드
        self.load_company_info()

    def load_company_info(self):
        """회사 정보 로드 및 테이블 표시"""
        try:
            # CompanyManager를 통해 회사 정보 로드
            companies = self.company_manager.get_companies()
            
            if companies:
                # 회사 ID 목록 저장 (행 인덱스와 매핑)
                self._company_id_list = list(companies.keys())

                # 테이블에 회사 목록 표시
                self.company_table.blockSignals(True)  # 시그널 일시 차단
                self.company_table.setRowCount(len(companies))
                for row, (company_id, info) in enumerate(companies.items()):
                    self.company_table.setItem(row, 0, QTableWidgetItem(info.get("name", "")))
                    business_size_text = "5인 미만" if info.get("business_size") == "under_5" else "5인 이상"
                    self.company_table.setItem(row, 1, QTableWidgetItem(business_size_text))
                    self.company_table.setItem(row, 2, QTableWidgetItem(info.get("industry_type", "")))
                    self.company_table.setItem(row, 3, QTableWidgetItem(info.get("tax_office", "")))
                    self.company_table.setItem(row, 4, QTableWidgetItem(info.get("business_registration", "")))
                self.company_table.blockSignals(False)  # 시그널 복원

                # 첫 번째 행 선택
                if len(companies) > 0:
                    self.company_table.selectRow(0)
            else:
                self._company_id_list = []
                self.selected_company_id = None
                self.company_table.setRowCount(0)

        except Exception as e:
            QMessageBox.critical(self, "회사 정보 로드 오류", f"회사 정보를 로드하는 중 오류가 발생했습니다:\n{str(e)}")
            print(f"회사 정보 로드 오류: {e}")

    def on_company_changed(self):
        """회사 정보 변경 시 호출되는 콜백"""
        print("회사 정보 변경 감지 - 테이블 갱신")
        self.load_company_info()

    def on_company_table_selection_changed(self):
        """테이블에서 회사 선택 시 입력 필드 업데이트"""
        current_row = self.company_table.currentRow()
        if current_row < 0:
            return

        # 행 인덱스로 회사 ID 조회
        if not hasattr(self, '_company_id_list') or current_row >= len(self._company_id_list):
            return

        company_id = self._company_id_list[current_row]
        company_info = self.company_manager.get_company(company_id)

        if not company_info:
            return

        # 선택된 회사 ID 저장
        self.selected_company_id = company_id

        # 입력 필드 업데이트
        self.company_form_vars["company_name"].setText(company_info.get("name", ""))
        business_size = company_info.get("business_size", "over_5")
        if business_size == "under_5":
            self.company_form_vars["company_business_size"].setCurrentText("5인 미만 사업장")
        else:
            self.company_form_vars["company_business_size"].setCurrentText("5인 이상 사업장")
        self.company_form_vars["company_industry"].setText(company_info.get("industry_type", ""))
        self.company_form_vars["company_tax_office"].setText(company_info.get("tax_office", ""))
        self.company_form_vars["company_registration"].setText(company_info.get("business_registration", ""))

        print(f"회사 선택 변경: {company_id} - {company_info.get('name', '')}")

    def save_company_info(self):
        """회사 정보 저장"""
        try:
            # 선택된 회사 확인
            if not self.selected_company_id:
                QMessageBox.warning(self, "선택 오류", "저장할 회사를 목록에서 선택해주세요.")
                return

            # 현재 폼 데이터 수집
            company_name = self.company_form_vars["company_name"].text().strip()
            business_size_text = self.company_form_vars["company_business_size"].currentText()
            industry = self.company_form_vars["company_industry"].text().strip()
            tax_office = self.company_form_vars["company_tax_office"].text().strip()
            registration = self.company_form_vars["company_registration"].text().strip()

            if not company_name:
                QMessageBox.warning(self, "입력 오류", "회사명을 입력해주세요.")
                return

            # 사업장 규모 변환
            business_size = "under_5" if business_size_text == "5인 미만 사업장" else "over_5"

            # CompanyManager를 통해 회사 정보 저장 (선택된 회사 ID 사용)
            company_data = {
                "company_id": self.selected_company_id,
                "name": company_name,
                "business_size": business_size,
                "industry_type": industry,
                "tax_office": tax_office,
                "business_registration": registration
            }

            # 선택된 회사 수정
            self.company_manager.modify_company(self.selected_company_id, company_data)

            QMessageBox.information(self, "저장 완료", f"'{company_name}' 회사 정보가 성공적으로 저장되었습니다.")

        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"회사 정보 저장 중 오류가 발생했습니다:\n{str(e)}")

    def add_new_company(self):
        """새 회사 추가"""
        try:
            # 안전한 회사 ID 생성 (기존 ID와 충돌 방지)
            companies = self.company_manager.get_companies()
            existing_ids = set(companies.keys())
            existing_names = {info.get('name', '') for info in companies.values()}
            next_id_num = 1
            while f"company_{next_id_num:03d}" in existing_ids:
                next_id_num += 1
            new_company_id = f"company_{next_id_num:03d}"

            # 고유한 기본 회사명 생성 (이름 충돌 방지)
            name_num = next_id_num
            company_name = f"새 회사 {name_num}"
            while company_name in existing_names:
                name_num += 1
                company_name = f"새 회사 {name_num}"

            new_company = {
                "company_id": new_company_id,
                "name": company_name,
                "business_size": "over_5",
                "industry_type": "",
                "tax_office": "",
                "business_registration": ""
            }

            # CompanyManager를 통해 새 회사 추가
            self.company_manager.add_company(new_company)

            # 새로 추가된 회사를 선택
            self.selected_company_id = new_company_id

            QMessageBox.information(self, "회사 추가 완료", f"'{company_name}' 회사가 추가되었습니다.\n회사 정보를 수정한 후 '회사 정보 저장' 버튼을 눌러주세요.")

        except Exception as e:
            QMessageBox.critical(self, "회사 추가 오류", f"회사 추가 중 오류가 발생했습니다:\n{str(e)}")

    def delete_selected_company(self):
        """선택된 회사 삭제 (개선된 버전: 직원 재배치 기능 포함)"""
        current_row = self.company_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "선택 오류", "삭제할 회사를 선택해주세요.")
            return

        company_name = self.company_table.item(current_row, 0).text()

        try:
            # CompanyManager를 통해 회사 정보 확인 및 직원 연결 상태 파악
            companies = self.company_manager.get_companies()
            company_to_delete = None
            
            for company_id, company_info in companies.items():
                if company_info.get("name") == company_name:
                    company_to_delete = company_id
                    break

            if not company_to_delete:
                QMessageBox.warning(self, "오류", "회사를 찾을 수 없습니다.")
                return

            # 연결된 직원 수 확인
            linked_employees = []
            if os.path.exists('employees.json'):
                with open('employees.json', 'r', encoding='utf-8') as f:
                    employees_data = json.load(f)

                for emp_id, emp_info in employees_data.get('employees', {}).items():
                    if isinstance(emp_info, dict) and emp_info.get('company_id') == company_to_delete:
                        linked_employees.append(f"{emp_info.get('name', emp_id)}({emp_id})")

            # 남은 회사 목록 생성 (삭제할 회사를 제외)
            remaining_companies = []
            for company_id, company_info in companies.items():
                if company_id != company_to_delete:
                    remaining_companies.append({
                        'id': company_id,
                        'name': company_info.get('name', company_id)
                    })

            # 삭제 확인 다이얼로그 (직원 재배치 옵션 포함)
            if linked_employees:
                # 연결된 직원이 있는 경우
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("회사 삭제 및 직원 재배치")
                msg.setText(f"'{company_name}' 회사를 삭제하시겠습니까?")

                detailed_text = f"""
⚠️ 이 회사에 연결된 직원 {len(linked_employees)}명이 있습니다:

{chr(10).join(linked_employees[:5])}  # 최대 5명까지만 표시
{'...' if len(linked_employees) > 5 else ''}

삭제 시 이 직원들의 회사 연결이 해제됩니다.
"""

                if remaining_companies:
                    detailed_text += "\n💡 삭제 후 이 직원들을 다른 회사로 재배치하시겠습니까?"

                msg.setDetailedText(detailed_text.strip())

                # 버튼 설정
                reassign_btn = msg.addButton("직원 재배치 후 삭제", QMessageBox.ButtonRole.AcceptRole)
                delete_only_btn = msg.addButton("연결 해제 후 삭제", QMessageBox.ButtonRole.DestructiveRole)
                cancel_btn = msg.addButton("취소", QMessageBox.ButtonRole.RejectRole)
                msg.setDefaultButton(cancel_btn)

                msg.exec()

                clicked_button = msg.clickedButton()

                if clicked_button == cancel_btn:
                    return
                elif clicked_button == reassign_btn and remaining_companies:
                    # 직원 재배치 선택
                    if not self.reassign_employees_to_company(company_to_delete, remaining_companies):
                        return  # 재배치 실패 시 삭제 취소
                # delete_only_btn이나 재배치 성공 시 계속 진행
            else:
                # 연결된 직원이 없는 경우
                reply = QMessageBox.question(
                    self, "회사 삭제 확인",
                    f"'{company_name}' 회사를 삭제하시겠습니까?\n\n"
                    "이 회사에 연결된 직원이 없습니다.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply != QMessageBox.StandardButton.Yes:
                    return

            # CompanyManager를 통해 회사 삭제 실행
            self.company_manager.delete_company(company_to_delete)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"회사 삭제 처리 중 오류가 발생했습니다:\n{str(e)}")

    def reassign_employees_to_company(self, old_company_id, remaining_companies):
        """직원을 다른 회사로 재배치"""
        try:
            if not remaining_companies:
                QMessageBox.warning(self, "오류", "재배치할 수 있는 회사가 없습니다.")
                return False

            # 재배치할 회사 선택 다이얼로그
            company_names = [f"{company['name']} ({company['id']})" for company in remaining_companies]
            selected_company_name, ok = QInputDialog.getItem(
                self, "직원 재배치",
                "어떤 회사로 직원들을 재배치하시겠습니까?",
                company_names, 0, False
            )

            if not ok:
                return False

            # 선택된 회사 ID 찾기
            selected_company = None
            for company in remaining_companies:
                if f"{company['name']} ({company['id']})" == selected_company_name:
                    selected_company = company
                    break

            if not selected_company:
                return False

            # 직원 재배치 실행
            reassigned_count = 0
            if os.path.exists('employees.json'):
                with open('employees.json', 'r', encoding='utf-8') as f:
                    employees_data = json.load(f)

                for emp_id, emp_info in employees_data.get('employees', {}).items():
                    if isinstance(emp_info, dict) and emp_info.get('company_id') == old_company_id:
                        emp_info['company_id'] = selected_company['id']
                        reassigned_count += 1
                        print(f"직원 {emp_id} 재배치: {old_company_id} → {selected_company['id']}")

                # employees.json 저장
                with open('employees.json', 'w', encoding='utf-8') as f:
                    json.dump(employees_data, f, ensure_ascii=False, indent=2)

            QMessageBox.information(
                self, "재배치 완료",
                f"{reassigned_count}명의 직원이 '{selected_company['name']}' 회사로 재배치되었습니다."
            )
            return True

        except Exception as e:
            QMessageBox.critical(self, "재배치 오류", f"직원 재배치 중 오류가 발생했습니다:\n{str(e)}")
            return False



def setup_tax_settings(parent, app_instance):
    """
    세무사 설정 창을 여는 함수
    tkinter 호환성을 위한 래퍼 함수
    """
    def open_settings_with_password(password):
        if password:
            dialog = TaxSettingsDialogQt(parent, app_instance, password)
            dialog.exec()

    # 비밀번호 입력 대화상자
    password_dialog = PasswordDialogQt(parent, open_settings_with_password)
    password_dialog.exec()
