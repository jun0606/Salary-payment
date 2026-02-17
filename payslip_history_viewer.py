#!/usr/bin/env python3
"""
이전 급여명세서 조회 뷰어
저장된 급여명세서 기록을 검색하고 출력하는 UI
"""

import os
import zipfile
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QCheckBox, QProgressBar,
    QSplitter, QTextEdit, QDialogButtonBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from database_manager import get_database

class PayslipHistoryViewer(QDialog):
    """
    이전 급여명세서 조회 및 출력 다이얼로그

    검색 기반으로 저장된 급여명세서 기록을 조회하고
    개별 또는 대량으로 출력할 수 있습니다.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self.selected_records = []
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()

    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("📋 이전 급여명세서 출력")
        self.setModal(True)
        self.resize(1200, 800)

        # 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 제목
        title_label = QLabel("이전 급여명세서 조회 및 출력")
        title_label.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 검색 및 필터 영역
        self.setup_search_filters(layout)

        # 결과 테이블
        self.setup_results_table(layout)

        # 액션 버튼 영역
        self.setup_action_buttons(layout)

        # 상태 표시줄
        self.setup_status_bar(layout)

    def setup_search_filters(self, parent_layout):
        """검색 및 필터 영역 설정"""
        search_group = QGroupBox("검색 및 필터")
        search_layout = QVBoxLayout(search_group)
        search_layout.setSpacing(8)

        # 검색 입력줄들
        search_layout_inner = QHBoxLayout()

        # 사원명 검색
        employee_label = QLabel("사원명:")
        self.employee_input = QLineEdit()
        self.employee_input.setPlaceholderText("직원명으로 검색...")
        self.employee_input.setMinimumWidth(180)

        # 회사명 검색
        company_search_label = QLabel("회사명:")
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("회사명으로 검색...")
        self.company_input.setMinimumWidth(180)

        search_layout_inner.addWidget(employee_label)
        search_layout_inner.addWidget(self.employee_input)
        search_layout_inner.addWidget(company_search_label)
        search_layout_inner.addWidget(self.company_input)
        search_layout.addLayout(search_layout_inner)

        # 필터 드롭다운들
        filters_layout = QHBoxLayout()

        # 회사 필터
        company_label = QLabel("회사:")
        self.company_combo = QComboBox()
        self.company_combo.addItem("전체", "")
        self.company_combo.setMinimumWidth(150)

        # 년도 필터
        year_label = QLabel("년도:")
        self.year_combo = QComboBox()
        self.year_combo.addItem("전체", "")
        self.year_combo.setMinimumWidth(100)

        # 월 필터
        month_label = QLabel("월:")
        self.month_combo = QComboBox()
        self.month_combo.addItem("전체", "")
        for month in range(1, 13):
            self.month_combo.addItem(f"{month}월", f"{month:02d}")
        self.month_combo.setMinimumWidth(100)

        # 새로고침 버튼
        self.refresh_btn = QPushButton("🔄 새로고침")
        self.refresh_btn.setMaximumWidth(100)

        filters_layout.addWidget(company_label)
        filters_layout.addWidget(self.company_combo)
        filters_layout.addWidget(year_label)
        filters_layout.addWidget(self.year_combo)
        filters_layout.addWidget(month_label)
        filters_layout.addWidget(self.month_combo)
        filters_layout.addStretch()
        filters_layout.addWidget(self.refresh_btn)

        search_layout.addLayout(filters_layout)
        parent_layout.addWidget(search_group)

    def setup_results_table(self, parent_layout):
        """결과 테이블 설정"""
        table_group = QGroupBox("급여명세서 목록")
        table_layout = QVBoxLayout(table_group)

        # 테이블 생성
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "선택", "회사", "직원", "기간", "버전", "생성일", "금액"
        ])

        # 테이블 스타일링
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 컬럼 너비 설정
        self.results_table.setColumnWidth(0, 60)   # 선택
        self.results_table.setColumnWidth(1, 120)  # 회사
        self.results_table.setColumnWidth(2, 120)  # 직원
        self.results_table.setColumnWidth(3, 100)  # 기간
        self.results_table.setColumnWidth(4, 60)   # 버전
        self.results_table.setColumnWidth(5, 150)  # 생성일
        self.results_table.setColumnWidth(6, 120)  # 금액

        # 더블클릭 이벤트
        self.results_table.itemDoubleClicked.connect(self.show_record_details)

        table_layout.addWidget(self.results_table)

        # 선택 개수 표시
        self.selection_info = QLabel("선택된 기록: 0개")
        self.selection_info.setStyleSheet("color: #666; font-size: 11px;")
        table_layout.addWidget(self.selection_info)

        parent_layout.addWidget(table_group)

    def setup_action_buttons(self, parent_layout):
        """액션 버튼 영역 설정"""
        buttons_layout = QHBoxLayout()

        # HTML 출력 버튼
        self.html_export_btn = QPushButton("📄 HTML 출력")
        self.html_export_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.html_export_btn.setEnabled(False)
        buttons_layout.addWidget(self.html_export_btn)

        # 대량 출력 버튼
        self.bulk_export_btn = QPushButton("📦 대량 출력")
        self.bulk_export_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.bulk_export_btn.setEnabled(False)
        buttons_layout.addWidget(self.bulk_export_btn)

        # 데이터 관리 버튼
        self.data_mgmt_btn = QPushButton("🗂️ 데이터 관리")
        self.data_mgmt_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a359a;
            }
        """)
        buttons_layout.addWidget(self.data_mgmt_btn)

        # 삭제 버튼 (숨김 - 데이터 관리에서 처리)
        self.delete_btn = QPushButton("🗑️ 삭제")
        self.delete_btn.setVisible(False)  # 데이터 관리에서 통합 처리
        buttons_layout.addWidget(self.delete_btn)

        buttons_layout.addStretch()

        # 닫기 버튼
        self.close_btn = QPushButton("닫기")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #545b62;
            }
        """)
        buttons_layout.addWidget(self.close_btn)

        parent_layout.addLayout(buttons_layout)

    def setup_status_bar(self, parent_layout):
        """상태 표시줄 설정"""
        self.status_label = QLabel("준비")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        parent_layout.addWidget(self.status_label)

    def setup_connections(self):
        """시그널 연결"""
        # 검색 및 필터 이벤트
        self.employee_input.textChanged.connect(self.on_search_text_changed)
        self.company_input.textChanged.connect(self.on_search_text_changed)
        self.company_combo.currentIndexChanged.connect(self.perform_search)
        self.year_combo.currentIndexChanged.connect(self.perform_search)
        self.month_combo.currentIndexChanged.connect(self.perform_search)
        self.refresh_btn.clicked.connect(self.load_initial_data)

        # 테이블 이벤트
        self.results_table.itemChanged.connect(self.update_selection_info)

        # 버튼 이벤트
        self.html_export_btn.clicked.connect(self.export_html_selected)
        self.bulk_export_btn.clicked.connect(self.bulk_export_selected)
        self.data_mgmt_btn.clicked.connect(self.open_data_management)
        self.delete_btn.clicked.connect(self.delete_selected_records)
        self.close_btn.clicked.connect(self.accept)

    def load_initial_data(self):
        """초기 데이터 로드"""
        try:
            self.status_label.setText("데이터 로딩 중...")

            # 회사 목록 로드
            self.load_company_list()

            # 년도 목록 로드
            self.load_year_list()

            # 검색 수행
            self.perform_search()

            self.status_label.setText("데이터 로드 완료")

        except Exception as e:
            self.status_label.setText(f"데이터 로드 오류: {str(e)}")
            QMessageBox.critical(self, "오류", f"초기 데이터 로드 중 오류가 발생했습니다:\n{str(e)}")

    def load_company_list(self):
        """회사 목록 로드"""
        try:
            # 현재 선택된 회사 유지
            current_company = self.company_combo.currentData()

            self.company_combo.clear()
            self.company_combo.addItem("전체", "")

            # 데이터베이스에서 회사 목록 조회
            companies = self.db.get_payslip_records(limit=1000)
            unique_companies = set()

            for record in companies:
                if record.get('company_name'):
                    unique_companies.add(record['company_name'])

            for company in sorted(unique_companies):
                self.company_combo.addItem(company, company)

            # 이전 선택 복원
            if current_company:
                index = self.company_combo.findData(current_company)
                if index >= 0:
                    self.company_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"회사 목록 로드 오류: {e}")

    def load_year_list(self):
        """년도 목록 로드"""
        try:
            # 현재 선택된 년도 유지
            current_year = self.year_combo.currentData()

            self.year_combo.clear()
            self.year_combo.addItem("전체", "")

            # 데이터베이스에서 년도 목록 조회
            records = self.db.get_payslip_records(limit=1000)
            unique_years = set()

            for record in records:
                pay_month = record.get('pay_month', '')
                if pay_month and '-' in pay_month:
                    year = pay_month.split('-')[0]
                    if year.isdigit():
                        unique_years.add(year)

            for year in sorted(unique_years, reverse=True):
                self.year_combo.addItem(f"{year}년", year)

            # 이전 선택 복원
            if current_year:
                index = self.year_combo.findData(current_year)
                if index >= 0:
                    self.year_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"년도 목록 로드 오류: {e}")

    def on_search_text_changed(self):
        """검색 텍스트 변경 시 딜레이 검색"""
        self.search_timer.start(300)  # 300ms 딜레이

    def perform_search(self):
        """검색 수행"""
        try:
            self.status_label.setText("검색 중...")

            # 필터 조건 수집
            filters = {}

            employee_text = self.employee_input.text().strip()
            if employee_text:
                filters['employee_name'] = employee_text

            company_text = self.company_input.text().strip()
            if company_text:
                filters['company_name_like'] = company_text

            company_filter = self.company_combo.currentData()
            if company_filter:
                filters['company_name'] = company_filter

            year_filter = self.year_combo.currentData()
            if year_filter:
                filters['year'] = year_filter

            month_filter = self.month_combo.currentData()
            if month_filter:
                filters['month'] = month_filter

            # 검색 수행
            records = self.db.get_payslip_records(filters=filters, limit=500)

            # 결과 표시
            self.display_results(records)

            self.status_label.setText(f"검색 완료: {len(records)}개 기록 찾음")

        except Exception as e:
            self.status_label.setText(f"검색 오류: {str(e)}")
            QMessageBox.critical(self, "검색 오류", f"검색 중 오류가 발생했습니다:\n{str(e)}")

    def display_results(self, records):
        """검색 결과를 테이블에 표시"""
        self.results_table.setRowCount(0)

        for row_idx, record in enumerate(records):
            self.results_table.insertRow(row_idx)

            # 체크박스 (선택용)
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Unchecked)
            checkbox.setData(Qt.ItemDataRole.UserRole, record['id'])
            self.results_table.setItem(row_idx, 0, checkbox)

            # 회사명
            company_item = QTableWidgetItem(record.get('company_name', ''))
            self.results_table.setItem(row_idx, 1, company_item)

            # 직원명
            employee_item = QTableWidgetItem(record.get('employee_name', ''))
            self.results_table.setItem(row_idx, 2, employee_item)

            # 기간
            pay_month = record.get('pay_month', '')
            if pay_month and '-' in pay_month:
                year, month = pay_month.split('-')
                period_text = f"{year}년 {int(month)}월"
            else:
                period_text = pay_month
            period_item = QTableWidgetItem(period_text)
            self.results_table.setItem(row_idx, 3, period_item)

            # 버전
            version_item = QTableWidgetItem(f"v{record.get('version', 1)}")
            self.results_table.setItem(row_idx, 4, version_item)

            # 생성일
            created_at = record.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at)
                    date_text = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_text = created_at
            else:
                date_text = ''
            date_item = QTableWidgetItem(date_text)
            self.results_table.setItem(row_idx, 5, date_item)

            # 금액 정보 (HTML에서 파싱 - 간단히 표시)
            amount_item = QTableWidgetItem("계산 중...")
            self.results_table.setItem(row_idx, 6, amount_item)

            # 레코드 ID 저장 (숨김)
            self.results_table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, record['id'])

        # 테이블 정렬 가능하게 설정
        self.results_table.setSortingEnabled(True)

    def update_selection_info(self):
        """선택된 항목 정보 업데이트"""
        selected_count = 0
        self.selected_records = []

        for row in range(self.results_table.rowCount()):
            checkbox_item = self.results_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                record_id = checkbox_item.data(Qt.ItemDataRole.UserRole)
                self.selected_records.append(record_id)
                selected_count += 1

        self.selection_info.setText(f"선택된 기록: {selected_count}개")

        # 버튼 활성화 상태 업데이트
        has_selection = selected_count > 0
        self.html_export_btn.setEnabled(has_selection)
        self.bulk_export_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def show_record_details(self, item):
        """레코드 상세 정보 표시"""
        if item.column() == 0:  # 체크박스 클릭은 무시
            return

        row = item.row()
        record_id = self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole)

        try:
            # 레코드 상세 정보 조회
            record = self.db.get_payslip_content(record_id)
            if not record:
                QMessageBox.warning(self, "오류", "기록을 찾을 수 없습니다.")
                return

            # 상세 정보 다이얼로그 표시
            dialog = RecordDetailsDialog(record_id, self.db, self)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "오류", f"상세 정보 조회 중 오류가 발생했습니다:\n{str(e)}")

    def export_html_selected(self):
        """선택된 기록들을 HTML 파일로 개별 출력"""
        if not self.selected_records:
            QMessageBox.warning(self, "선택 오류", "출력할 기록을 선택해주세요.")
            return

        try:
            self.status_label.setText("HTML 파일 생성 중...")

            # 출력 디렉토리 선택 또는 기본 디렉토리 사용
            import os
            output_dir = "급여명세서_HTML_출력"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            exported_files = []

            # 각 기록에 대해 HTML 파일 생성
            for record_id in self.selected_records:
                html_content = self.db.get_payslip_content(record_id)
                if html_content:
                    # DB에서 기록 정보 조회하여 파일명 생성
                    records = self.db.get_payslip_records(limit=1000)
                    record_info = None
                    for rec in records:
                        if rec['id'] == record_id:
                            record_info = rec
                            break

                    if record_info:
                        # 파일명: 회사명_직원명_기간_v버전.html
                        company = record_info.get('company_name', '회사없음').replace('/', '_').replace('\\', '_')
                        employee = record_info.get('employee_name', '직원없음').replace('/', '_').replace('\\', '_')
                        pay_month = record_info.get('pay_month', '기간없음').replace('-', '')
                        version = record_info.get('version', 1)

                        filename = f"{company}_{employee}_{pay_month}_v{version}.html"
                        filepath = os.path.join(output_dir, filename)

                        # HTML 파일 저장
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(html_content)

                        exported_files.append(filename)

            if exported_files:
                self.status_label.setText(f"HTML 파일 생성 완료: {output_dir}")
                QMessageBox.information(self, "HTML 출력 완료",
                    f"선택된 {len(self.selected_records)}개의 급여명세서를\nHTML 파일로 출력했습니다.\n\n출력 폴더: {output_dir}\n\n파일 목록:\n" + '\n'.join(exported_files))

                # 출력 폴더 열기
                os.startfile(output_dir)
            else:
                QMessageBox.warning(self, "출력 실패", "HTML 파일을 생성할 수 없습니다.")

        except Exception as e:
            self.status_label.setText(f"HTML 출력 오류: {str(e)}")
            QMessageBox.critical(self, "HTML 출력 오류", f"HTML 파일 생성 중 오류가 발생했습니다:\n{str(e)}")

    def bulk_export_selected(self):
        """선택된 기록들 대량 출력 (ZIP)"""
        if not self.selected_records:
            QMessageBox.warning(self, "선택 오류", "출력할 기록을 선택해주세요.")
            return

        try:
            self.status_label.setText("ZIP 파일 생성 중...")

            # ZIP 파일 생성
            zip_filename = self.create_bulk_zip(self.selected_records)

            # 파일 열기 또는 저장
            if os.path.exists(zip_filename):
                os.startfile(zip_filename)  # Windows에서 파일 열기
                self.status_label.setText(f"ZIP 파일 생성 완료: {zip_filename}")
                QMessageBox.information(self, "대량 출력 완료",
                    f"선택된 {len(self.selected_records)}개의 급여명세서를\nZIP 파일로 묶어 출력했습니다.\n\n파일: {zip_filename}")
            else:
                QMessageBox.critical(self, "오류", "ZIP 파일 생성에 실패했습니다.")

        except Exception as e:
            self.status_label.setText(f"대량 출력 오류: {str(e)}")
            QMessageBox.critical(self, "대량 출력 오류", f"ZIP 파일 생성 중 오류가 발생했습니다:\n{str(e)}")

    def create_bulk_zip(self, record_ids):
        """선택된 기록들을 ZIP 파일로 묶음"""
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"급여명세서_대량출력_{timestamp}.zip"

        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 각 HTML 파일 추가
            for record_id in record_ids:
                html_content = self.db.get_payslip_content(record_id)
                if html_content:
                    # 파일명 생성 (회사명_직원명_기간_v버전.html)
                    # 실제로는 DB에서 조회해야 하지만 간단히 구현
                    safe_filename = f"payslip_{record_id}.html"
                    zipf.writestr(safe_filename, html_content)

            # 목록 파일 추가
            list_content = self.generate_file_list(record_ids)
            zipf.writestr("급여명세서_목록.txt", list_content)

        return zip_filename

    def generate_file_list(self, record_ids):
        """ZIP 파일에 포함된 파일 목록 생성"""
        list_content = "급여명세서 대량 출력 목록\n"
        list_content += "=" * 50 + "\n\n"

        for i, record_id in enumerate(record_ids, 1):
            list_content += f"{i}. payslip_{record_id}.html\n"

        list_content += f"\n총 파일 수: {len(record_ids)}개\n"
        list_content += f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        list_content += "※ 이 파일들은 출력 당시의 계산 결과를 그대로 보존하고 있습니다.\n"

        return list_content

    def delete_selected_records(self):
        """선택된 기록들 삭제"""
        if not self.selected_records:
            QMessageBox.warning(self, "선택 오류", "삭제할 기록을 선택해주세요.")
            return

        # 삭제 확인
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"선택된 {len(self.selected_records)}개의 급여명세서 기록을 삭제하시겠습니까?\n\n"
            "※ 삭제된 기록은 복구할 수 없습니다.\n"
            "※ 법적 보존 기간이 경과한 기록만 삭제하는 것을 권장합니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 삭제 사유 입력
                reason, ok = QInputDialog.getText(self, "삭제 사유", "삭제 사유를 입력하세요:")
                if not ok or not reason.strip():
                    return

                # 삭제 수행
                success = self.db.soft_delete_records(self.selected_records, reason.strip(), "사용자")

                if success:
                    QMessageBox.information(self, "삭제 완료",
                        f"{len(self.selected_records)}개의 기록이 삭제되었습니다.")
                    self.perform_search()  # 목록 새로고침
                else:
                    QMessageBox.critical(self, "삭제 실패", "기록 삭제 중 오류가 발생했습니다.")

            except Exception as e:
                QMessageBox.critical(self, "삭제 오류", f"기록 삭제 중 오류가 발생했습니다:\n{str(e)}")

    def open_data_management(self):
        """데이터 관리 다이얼로그 열기"""
        try:
            from data_deletion_manager import show_data_deletion_manager
            show_data_deletion_manager(self)
            # 데이터 관리가 끝나면 목록을 새로고침
            self.perform_search()
        except ImportError as e:
            QMessageBox.critical(self, "모듈 오류", f"데이터 관리 모듈을 찾을 수 없습니다:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"데이터 관리 창을 열 수 없습니다:\n{str(e)}")


class RecordDetailsDialog(QDialog):
    """급여명세서 기록 상세 정보 다이얼로그"""

    def __init__(self, record_id, db, parent=None):
        super().__init__(parent)
        self.record_id = record_id
        self.db = db
        self.record = None

        self.setup_ui()
        self.load_record_details()
        self.setup_connections()

    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("급여명세서 상세 정보")
        self.setModal(True)
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        # 상세 정보 표시 영역
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)

        # 버튼 영역
        button_layout = QHBoxLayout()

        # HTML로 보기 버튼
        self.view_html_btn = QPushButton("🌐 HTML로 보기")
        self.view_html_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        button_layout.addWidget(self.view_html_btn)

        button_layout.addStretch()

        # 확인/취소 버튼
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)

        layout.addLayout(button_layout)

    def setup_connections(self):
        """시그널 연결"""
        self.view_html_btn.clicked.connect(self.view_html)

    def load_record_details(self):
        """기록 상세 정보 로드"""
        try:
            # DB에서 메타 정보 조회 (HTML 제외)
            records = self.db.get_payslip_records(limit=1000)
            self.record = None

            for record in records:
                if record['id'] == self.record_id:
                    self.record = record
                    break

            if not self.record:
                self.details_text.setText("기록을 찾을 수 없습니다.")
                return

            # 상세 정보 표시
            details = f"""
급여명세서 상세 정보
{'='*30}

기록 ID: {self.record['id']}
직원: {self.record['employee_name']}
회사: {self.record['company_name']}
기간: {self.record['pay_month']}
버전: v{self.record['version']}
생성일: {self.record['created_at']}
메모: {self.record.get('memo', '없음')}

데이터 해시: {self.record.get('input_data_hash', 'N/A')}
"""
            self.details_text.setText(details.strip())

        except Exception as e:
            self.details_text.setText(f"정보 로드 오류: {str(e)}")

    def view_html(self):
        """HTML 파일로 저장하고 열기"""
        try:
            html_content = self.db.get_payslip_content(self.record_id)
            if not html_content:
                QMessageBox.warning(self, "오류", "HTML 콘텐츠를 찾을 수 없습니다.")
                return

            # 출력 디렉토리
            output_dir = "급여명세서_HTML_출력"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 파일명 생성
            company = self.record.get('company_name', '회사없음').replace('/', '_').replace('\\', '_')
            employee = self.record.get('employee_name', '직원없음').replace('/', '_').replace('\\', '_')
            pay_month = self.record.get('pay_month', '기간없음').replace('-', '')
            version = self.record.get('version', 1)

            filename = f"{company}_{employee}_{pay_month}_v{version}.html"
            filepath = os.path.join(output_dir, filename)

            # HTML 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            QMessageBox.information(self, "HTML 파일 저장",
                f"급여명세서가 HTML 파일로 저장되었습니다.\n\n파일: {filepath}")

            # 파일 열기
            os.startfile(filepath)

        except Exception as e:
            QMessageBox.critical(self, "오류", f"HTML 파일 처리 중 오류가 발생했습니다:\n{str(e)}")




def show_payslip_history_viewer(parent=None):
    """급여명세서 기록 뷰어 표시 (편의 함수)"""
    dialog = PayslipHistoryViewer(parent)
    return dialog.exec()
