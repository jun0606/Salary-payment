#!/usr/bin/env python3
"""
PyQt6 기반 회사별 사원 관리 팝업
직원 목록에서 복수 선택하여 회사에 등록/제거하는 기능

기능:
- 회사별 사원 등록/제거 팝업
- 직원 목록 표시 (체크박스로 복수 선택)
- 회사 정보 표시
- 실시간 업데이트
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QMessageBox,
    QCheckBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import json
import os


class CompanyEmployeeManager(QDialog):
    """
    회사별 사원 관리 팝업 클래스
    """

    # 회사 변경 시그널
    company_updated = pyqtSignal(str)  # company_id

    def __init__(self, parent, app_instance, company_name, company_id):
        super().__init__(parent)
        self.app = app_instance
        self.company_name = company_name
        self.company_id = company_id

        self.setWindowTitle(f"회사별 사원 관리 - {company_name}")
        self.setModal(True)
        self.resize(600, 500)

        self.setup_ui()
        self.load_employee_list()

    def setup_ui(self):
        """UI 설정"""
        layout = QVBoxLayout(self)

        # 회사 정보 표시
        self.setup_company_info(layout)

        # 메인 콘텐츠 (스플리터)
        self.setup_main_content(layout)

        # 버튼 그룹
        self.setup_buttons(layout)

    def setup_company_info(self, parent_layout):
        """회사 정보 표시 영역"""
        company_group = QGroupBox("회사 정보")
        company_layout = QVBoxLayout(company_group)

        # 회사명 표시
        company_name_label = QLabel(f"회사명: {self.company_name}")
        company_name_label.setFont(QFont("맑은 고딕", 12, QFont.Weight.Bold))
        company_layout.addWidget(company_name_label)

        # 회사 ID 표시
        company_id_label = QLabel(f"회사 ID: {self.company_id}")
        company_id_label.setStyleSheet("color: #666; font-size: 10px;")
        company_layout.addWidget(company_id_label)

        parent_layout.addWidget(company_group)

    def setup_main_content(self, parent_layout):
        """메인 콘텐츠 영역 설정"""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 전체 직원 목록
        self.setup_all_employees_list(splitter)

        # 우측: 회사 소속 직원 목록
        self.setup_company_employees_list(splitter)

        parent_layout.addWidget(splitter)

    def setup_all_employees_list(self, parent):
        """전체 직원 목록 (체크박스로 선택)"""
        all_group = QGroupBox("전체 직원 목록")
        all_layout = QVBoxLayout(all_group)

        # 설명
        desc_label = QLabel("✅ 체크하여 회사에 등록할 직원을 선택하세요")
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        all_layout.addWidget(desc_label)

        # 직원 목록
        self.all_employees_list = QListWidget()
        self.all_employees_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        all_layout.addWidget(self.all_employees_list)

        # 전체 선택/해제 버튼
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("전체 선택")
        select_all_btn.clicked.connect(self.select_all_employees)
        select_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("전체 해제")
        deselect_all_btn.clicked.connect(self.deselect_all_employees)
        select_layout.addWidget(deselect_all_btn)

        all_layout.addLayout(select_layout)
        parent.addWidget(all_group)

    def setup_company_employees_list(self, parent):
        """회사 소속 직원 목록"""
        company_group = QGroupBox(f"{self.company_name} 소속 직원")
        company_layout = QVBoxLayout(company_group)

        # 설명
        desc_label = QLabel("🔵 이 회사의 현재 직원들입니다")
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        company_layout.addWidget(desc_label)

        # 직원 목록
        self.company_employees_list = QListWidget()
        self.company_employees_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        company_layout.addWidget(self.company_employees_list)

        # 선택 해제 버튼
        deselect_btn = QPushButton("선택 해제")
        deselect_btn.clicked.connect(self.deselect_company_employees)
        company_layout.addWidget(deselect_btn)

        parent.addWidget(company_group)

    def setup_buttons(self, parent_layout):
        """버튼 그룹 설정"""
        button_layout = QHBoxLayout()

        # 회사에 등록 버튼
        add_btn = QPushButton("➕ 회사에 등록")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_employees_to_company)
        button_layout.addWidget(add_btn)

        # 회사에서 제거 버튼
        remove_btn = QPushButton("➖ 회사에서 제거")
        remove_btn.setStyleSheet("""
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
        remove_btn.clicked.connect(self.remove_employees_from_company)
        button_layout.addWidget(remove_btn)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        parent_layout.addLayout(button_layout)

    def load_employee_list(self):
        """직원 목록 로드 및 표시"""
        try:
            # 리스트 초기화 (중요: 기존 아이템 완전 제거)
            self.all_employees_list.clear()
            self.company_employees_list.clear()

            print(f"직원 목록 로드 시작: 회사 {self.company_id}")

            # 전체 직원 목록
            all_employees_count = 0
            company_employees_count = 0

            for user_id, data in self.app.employee_data.items():
                if not user_id.strip():
                    continue

                name = data.get("name", "")
                department = data.get("department", "")
                position = data.get("position", "")

                # 표시 텍스트
                display_text = f"{name} ({user_id})"
                if department or position:
                    display_text += f" - {department} {position}".strip()

                # 리스트 아이템 생성
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, user_id)  # user_id 저장

                # 이미 회사 소속인지 확인
                current_company_id = data.get('company_id')
                is_company_employee = (current_company_id == self.company_id)

                if is_company_employee:
                    # 회사 소속 직원은 회색으로 표시하고 선택 불가
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    item.setBackground(Qt.GlobalColor.lightGray)
                    item.setToolTip("이미 이 회사에 소속되어 있습니다")
                    company_employees_count += 1

                self.all_employees_list.addItem(item)
                all_employees_count += 1

                # 회사 소속 직원 목록에도 추가
                if is_company_employee:
                    company_item = QListWidgetItem(display_text)
                    company_item.setData(Qt.ItemDataRole.UserRole, user_id)
                    self.company_employees_list.addItem(company_item)

            print(f"직원 목록 로드 완료: 전체 {all_employees_count}명, 회사 소속 {company_employees_count}명")

            # UI 강제 갱신
            self.all_employees_list.repaint()
            self.company_employees_list.repaint()

        except Exception as e:
            print(f"직원 목록 로드 오류: {e}")
            QMessageBox.critical(self, "오류", f"직원 목록 로드 중 오류가 발생했습니다:\n{str(e)}")

    def select_all_employees(self):
        """전체 직원 선택"""
        for i in range(self.all_employees_list.count()):
            item = self.all_employees_list.item(i)
            # 회색 아이템(이미 회사 소속)은 선택하지 않음
            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                item.setSelected(True)

    def deselect_all_employees(self):
        """전체 직원 선택 해제"""
        self.all_employees_list.clearSelection()

    def deselect_company_employees(self):
        """회사 직원 선택 해제"""
        self.company_employees_list.clearSelection()

    def add_employees_to_company(self):
        """선택된 직원을 회사에 등록"""
        selected_items = self.all_employees_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "회사에 등록할 직원을 선택해주세요.")
            return

        # 선택된 직원 수집
        selected_user_ids = []
        for item in selected_items:
            user_id = item.data(Qt.ItemDataRole.UserRole)
            selected_user_ids.append(user_id)

        # 확인 대화상자
        employee_names = []
        for user_id in selected_user_ids:
            if user_id in self.app.employee_data:
                name = self.app.employee_data[user_id].get("name", user_id)
                employee_names.append(f"{name}({user_id})")

        confirm_msg = f"다음 {len(selected_user_ids)}명의 직원을 '{self.company_name}' 회사에 등록하시겠습니까?\n\n"
        confirm_msg += "\n".join(employee_names[:10])  # 최대 10명까지만 표시
        if len(employee_names) > 10:
            confirm_msg += f"\n... 외 {len(employee_names) - 10}명"

        reply = QMessageBox.question(
            self, "직원 등록 확인",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 직원 회사 등록 (중복 등록 방지)
            updated_count = 0
            skipped_count = 0
            skipped_employees = []

            for user_id in selected_user_ids:
                if user_id in self.app.employee_data:
                    employee_data = self.app.employee_data[user_id]
                    current_company_id = employee_data.get('company_id')

                    # 이미 이 회사에 소속되어 있는지 확인
                    if current_company_id == self.company_id:
                        skipped_count += 1
                        employee_name = employee_data.get('name', user_id)
                        skipped_employees.append(f"{employee_name}({user_id})")
                        print(f"⚠️ 직원 {user_id}은(는) 이미 회사 {self.company_id}에 소속되어 있음 - 등록 건너뜀")
                    else:
                        # 다른 회사에 소속되어 있거나 소속 없음 → 등록 가능
                        self.app.employee_data[user_id]['company_id'] = self.company_id
                        updated_count += 1
                        print(f"✅ 직원 {user_id}를 회사 {self.company_id}에 등록")

            # 데이터 저장
            self.app.save_master_data()

            # 결과 메시지 구성
            result_msg = f"{updated_count}명의 직원이 '{self.company_name}' 회사에 등록되었습니다."

            if skipped_count > 0:
                result_msg += f"\n\n⚠️ 이미 회사 소속이어서 건너뛴 직원 ({skipped_count}명):"
                result_msg += "\n" + "\n".join(skipped_employees[:5])  # 최대 5명 표시
                if len(skipped_employees) > 5:
                    result_msg += f"\n... 외 {len(skipped_employees) - 5}명"

            QMessageBox.information(self, "등록 완료", result_msg)

            # UI 새로고침
            self.load_employee_list()

            # 시그널 발생 (메인 윈도우에서 처리)
            self.company_updated.emit(self.company_id)

    def remove_employees_from_company(self):
        """선택된 직원을 회사에서 제거"""
        selected_items = self.company_employees_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "회사에서 제거할 직원을 선택해주세요.")
            return

        # 선택된 직원 수집
        selected_user_ids = []
        for item in selected_items:
            user_id = item.data(Qt.ItemDataRole.UserRole)
            selected_user_ids.append(user_id)

        # 확인 대화상자
        employee_names = []
        for user_id in selected_user_ids:
            if user_id in self.app.employee_data:
                name = self.app.employee_data[user_id].get("name", user_id)
                employee_names.append(f"{name}({user_id})")

        confirm_msg = f"다음 {len(selected_user_ids)}명의 직원을 '{self.company_name}' 회사에서 제거하시겠습니까?\n\n"
        confirm_msg += "\n".join(employee_names[:10])  # 최대 10명까지만 표시
        if len(employee_names) > 10:
            confirm_msg += f"\n... 외 {len(employee_names) - 10}명"

        confirm_msg += "\n\n⚠️ 경고: 회사를 제거하면 해당 직원들은 회사와의 연결이 해제됩니다."

        reply = QMessageBox.question(
            self, "직원 제거 확인",
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 직원 회사 연결 해제 (강력한 삭제 로직)
            updated_count = 0
            failed_deletions = []

            for user_id in selected_user_ids:
                try:
                    if user_id in self.app.employee_data:
                        employee_data = self.app.employee_data[user_id]

                        # 현재 회사 연결 상태 확인
                        current_company_id = employee_data.get('company_id')
                        print(f"직원 {user_id}({employee_data.get('name', '이름없음')}) 삭제 전 회사 연결: {current_company_id}")

                        # 이 회사에 연결되어 있는지 확인
                        if current_company_id == self.company_id:
                            # company_id 필드 완전 삭제
                            if 'company_id' in employee_data:
                                del employee_data['company_id']
                                updated_count += 1
                                print(f"✅ 직원 {user_id}의 회사 연결 해제 성공")
                            else:
                                print(f"⚠️ 직원 {user_id}에 company_id 필드가 없음")
                                failed_deletions.append(f"{employee_data.get('name', user_id)} (필드 없음)")
                        else:
                            print(f"⚠️ 직원 {user_id}은(는) 이 회사({self.company_id})에 연결되어 있지 않음 (현재: {current_company_id})")
                            failed_deletions.append(f"{employee_data.get('name', user_id)} (다른 회사 소속)")
                    else:
                        print(f"❌ 직원 {user_id}가 직원 데이터에 존재하지 않음")
                        failed_deletions.append(f"ID:{user_id} (존재하지 않음)")

                except Exception as e:
                    print(f"❌ 직원 {user_id} 삭제 중 오류: {e}")
                    failed_deletions.append(f"{user_id} (오류: {e})")

            # 데이터 저장
            save_result = self.app.save_master_data()
            if not save_result:
                QMessageBox.warning(self, "저장 실패", "직원 데이터 저장에 실패했습니다. 변경사항이 유지되지 않을 수 있습니다.")

            # 결과 메시지
            success_msg = f"{updated_count}명의 직원이 '{self.company_name}' 회사에서 제거되었습니다."
            if failed_deletions:
                success_msg += f"\n\n실패한 항목 ({len(failed_deletions)}개):\n" + "\n".join(failed_deletions[:5])
                if len(failed_deletions) > 5:
                    success_msg += f"\n... 외 {len(failed_deletions) - 5}개"

            QMessageBox.information(self, "제거 완료", success_msg)

            # UI 새로고침 (항상 실행)
            self.load_employee_list()

            # 시그널 발생 (메인 윈도우에서 처리)
            self.company_updated.emit(self.company_id)


def show_company_employee_manager(parent, app_instance, company_name, company_id):
    """
    회사별 사원 관리 팝업을 표시하는 함수
    """
    dialog = CompanyEmployeeManager(parent, app_instance, company_name, company_id)
    result = dialog.exec()

    # 팝업이 닫힐 때 필요한 후처리
    if hasattr(dialog, 'company_updated'):
        # 시그널 연결로 후처리 가능
        pass

    return result == QDialog.DialogCode.Accepted