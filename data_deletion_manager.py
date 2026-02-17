#!/usr/bin/env python3
"""
급여명세서 데이터 삭제 관리 모듈
법적 보존 기간 준수 및 안전한 데이터 삭제 기능
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QGroupBox,
    QTextEdit, QCheckBox, QProgressBar, QComboBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from database_manager import get_database

class DataDeletionManager:
    """급여명세서 데이터 삭제 관리 클래스"""

    # 법적 보존 기간 (세무 기록 5년)
    RETENTION_PERIOD_YEARS = 5

    def __init__(self):
        self.db = get_database()

    def get_auto_deletion_candidates(self) -> List[Dict[str, Any]]:
        """
        자동 삭제 대상 기록 조회
        법적 보존 기간이 경과한 기록들

        Returns:
            List[Dict]: 삭제 대상 기록 리스트
        """
        return self.db.get_auto_deletion_candidates(self.RETENTION_PERIOD_YEARS)

    def get_manual_deletion_candidates(self, company_name: str = None,
                                     year: str = None) -> List[Dict[str, Any]]:
        """
        수동 삭제 대상 기록 조회
        필터링 조건에 맞는 기록들

        Args:
            company_name: 회사명 필터
            year: 연도 필터

        Returns:
            List[Dict]: 삭제 대상 기록 리스트
        """
        try:
            # 기본 쿼리
            query = """
                SELECT * FROM payslip_history
                WHERE is_active = TRUE
            """

            params = []

            if company_name:
                query += " AND company_name = ?"
                params.append(company_name)

            if year:
                query += " AND pay_month LIKE ?"
                params.append(f"{year}-%")

            query += " ORDER BY created_at ASC"

            # 데이터베이스에서 조회
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)

                records = []
                for row in cursor:
                    record = dict(row)
                    # 경과 일수 계산
                    if record.get('created_at'):
                        try:
                            created_date = datetime.fromisoformat(record['created_at'])
                            record['days_old'] = (datetime.now() - created_date).days
                        except:
                            record['days_old'] = 0
                    records.append(record)

                return records

        except Exception as e:
            print(f"수동 삭제 대상 조회 오류: {e}")
            return []

    def perform_auto_deletion(self, reason: str = "법적 보존 기간 만료") -> Dict[str, Any]:
        """
        자동 삭제 실행
        법적 보존 기간이 경과한 모든 기록 삭제

        Args:
            reason: 삭제 사유

        Returns:
            Dict: 삭제 결과
        """
        try:
            candidates = self.get_auto_deletion_candidates()

            if not candidates:
                return {
                    'success': True,
                    'deleted_count': 0,
                    'message': '삭제 대상 기록이 없습니다.'
                }

            # 삭제할 기록 ID들
            record_ids = [record['id'] for record in candidates]

            # 삭제 수행
            success = self.db.soft_delete_records(record_ids, reason, "SYSTEM")

            if success:
                return {
                    'success': True,
                    'deleted_count': len(record_ids),
                    'message': f'{len(record_ids)}개의 오래된 기록을 삭제했습니다.'
                }
            else:
                return {
                    'success': False,
                    'deleted_count': 0,
                    'message': '삭제 처리 중 오류가 발생했습니다.'
                }

        except Exception as e:
            return {
                'success': False,
                'deleted_count': 0,
                'message': f'자동 삭제 중 오류 발생: {str(e)}'
            }

    def perform_manual_deletion(self, record_ids: List[str], reason: str,
                               deleted_by: str) -> bool:
        """
        수동 삭제 실행

        Args:
            record_ids: 삭제할 기록 ID 리스트
            reason: 삭제 사유
            deleted_by: 삭제자

        Returns:
            bool: 삭제 성공 여부
        """
        if not record_ids:
            return False

        if not reason or not reason.strip():
            raise ValueError("삭제 사유를 입력해야 합니다.")

        return self.db.soft_delete_records(record_ids, reason.strip(), deleted_by)

    def get_deletion_statistics(self) -> Dict[str, Any]:
        """
        삭제 관련 통계 정보

        Returns:
            Dict: 통계 정보
        """
        try:
            # 전체 기록 수
            all_records = self.db.get_payslip_records(limit=10000)
            total_count = len(all_records)

            # 삭제 대상 기록 수
            candidates = self.get_auto_deletion_candidates()
            deletable_count = len(candidates)

            # 최근 삭제 일시
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute("""
                    SELECT MAX(deleted_at) FROM deletion_log
                """)
                last_deletion = cursor.fetchone()[0]

            return {
                'total_records': total_count,
                'deletable_records': deletable_count,
                'retention_period_years': self.RETENTION_PERIOD_YEARS,
                'last_deletion': last_deletion,
                'next_auto_deletion': datetime.now() + timedelta(days=30)  # 30일 후
            }

        except Exception as e:
            print(f"삭제 통계 조회 오류: {e}")
            return {}


class DataDeletionDialog(QDialog):
    """데이터 삭제 관리 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.deletion_manager = DataDeletionManager()
        self.selected_records = []

        self.setup_ui()
        self.load_statistics()
        self.load_auto_deletion_candidates()

    def setup_ui(self):
        """UI 구성"""
        self.setWindowTitle("🗑️ 데이터 삭제 관리")
        self.setModal(True)
        self.resize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 제목
        title_label = QLabel("급여명세서 데이터 삭제 관리")
        title_label.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 통계 정보 영역
        self.setup_statistics_section(layout)

        # 탭 영역 (자동 삭제 / 수동 삭제)
        self.setup_deletion_tabs(layout)

        # 버튼 영역
        self.setup_buttons(layout)

    def setup_statistics_section(self, parent_layout):
        """통계 정보 섹션"""
        stats_group = QGroupBox("삭제 현황")
        stats_layout = QHBoxLayout(stats_group)

        # 통계 레이블들
        self.stats_labels = {}

        stats_items = [
            ("전체 기록 수", "total_records"),
            ("삭제 가능 기록", "deletable_records"),
            ("보존 기간(년)", "retention_period_years"),
            ("최근 삭제", "last_deletion"),
            ("다음 자동 삭제", "next_auto_deletion")
        ]

        for label_text, key in stats_items:
            label = QLabel(f"{label_text}: 계산 중...")
            label.setStyleSheet("font-size: 11px;")
            stats_layout.addWidget(label)
            self.stats_labels[key] = label

        parent_layout.addWidget(stats_group)

    def setup_deletion_tabs(self, parent_layout):
        """삭제 탭 영역"""
        tabs_layout = QHBoxLayout()

        # 자동 삭제 탭
        auto_group = QGroupBox("자동 삭제 (법적 보존 기간 만료)")
        auto_layout = QVBoxLayout(auto_group)

        # 자동 삭제 설명
        auto_desc = QLabel(
            f"법적 보존 기간({self.deletion_manager.RETENTION_PERIOD_YEARS}년)이 경과한 기록들을\n"
            "자동으로 삭제합니다. 세무 조사 관련 기록은 제외됩니다."
        )
        auto_desc.setStyleSheet("color: #666; font-size: 11px;")
        auto_desc.setWordWrap(True)
        auto_layout.addWidget(auto_desc)

        # 자동 삭제 대상 목록
        self.auto_table = QTableWidget()
        self.auto_table.setColumnCount(5)
        self.auto_table.setHorizontalHeaderLabels([
            "직원", "회사", "기간", "생성일", "경과일수"
        ])
        self.auto_table.setMaximumHeight(200)
        auto_layout.addWidget(self.auto_table)

        # 자동 삭제 버튼
        self.auto_delete_btn = QPushButton("🚫 자동 삭제 실행")
        self.auto_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.auto_delete_btn.clicked.connect(self.perform_auto_deletion)
        auto_layout.addWidget(self.auto_delete_btn)

        tabs_layout.addWidget(auto_group)

        # 수동 삭제 탭
        manual_group = QGroupBox("수동 삭제")
        manual_layout = QVBoxLayout(manual_group)

        # 수동 삭제 필터
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("회사:"))
        self.manual_company_combo = QComboBox()
        self.manual_company_combo.addItem("전체", "")
        filter_layout.addWidget(self.manual_company_combo)

        filter_layout.addWidget(QLabel("년도:"))
        self.manual_year_combo = QComboBox()
        self.manual_year_combo.addItem("전체", "")
        filter_layout.addWidget(self.manual_year_combo)

        self.manual_filter_btn = QPushButton("필터 적용")
        self.manual_filter_btn.clicked.connect(self.load_manual_deletion_candidates)
        filter_layout.addWidget(self.manual_filter_btn)

        filter_layout.addStretch()
        manual_layout.addLayout(filter_layout)

        # 수동 삭제 대상 목록
        self.manual_table = QTableWidget()
        self.manual_table.setColumnCount(6)
        self.manual_table.setHorizontalHeaderLabels([
            "선택", "직원", "회사", "기간", "생성일", "경과일수"
        ])
        manual_layout.addWidget(self.manual_table)

        # 삭제 사유 입력
        reason_layout = QHBoxLayout()
        reason_layout.addWidget(QLabel("삭제 사유:"))
        self.deletion_reason_edit = QTextEdit()
        self.deletion_reason_edit.setPlaceholderText("삭제 사유를 입력하세요")
        self.deletion_reason_edit.setMaximumHeight(60)
        reason_layout.addWidget(self.deletion_reason_edit)
        manual_layout.addLayout(reason_layout)

        # 수동 삭제 버튼
        self.manual_delete_btn = QPushButton("🗑️ 선택 항목 삭제")
        self.manual_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.manual_delete_btn.clicked.connect(self.perform_manual_deletion)
        self.manual_delete_btn.setEnabled(False)
        manual_layout.addWidget(self.manual_delete_btn)

        tabs_layout.addWidget(manual_group)

        parent_layout.addLayout(tabs_layout)

    def setup_buttons(self, parent_layout):
        """버튼 영역 설정"""
        buttons_layout = QHBoxLayout()

        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_data)
        buttons_layout.addWidget(refresh_btn)

        buttons_layout.addStretch()

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        parent_layout.addLayout(buttons_layout)

    def load_statistics(self):
        """통계 정보 로드"""
        try:
            stats = self.deletion_manager.get_deletion_statistics()

            # 통계 표시
            self.stats_labels['total_records'].setText(f"전체 기록 수: {stats.get('total_records', 0):,}")
            self.stats_labels['deletable_records'].setText(f"삭제 가능 기록: {stats.get('deletable_records', 0):,}")
            self.stats_labels['retention_period_years'].setText(f"보존 기간(년): {stats.get('retention_period_years', 5)}")

            # 날짜 포맷팅
            last_deletion = stats.get('last_deletion')
            if last_deletion:
                try:
                    dt = datetime.fromisoformat(last_deletion)
                    last_deletion_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    last_deletion_str = last_deletion
            else:
                last_deletion_str = "없음"
            self.stats_labels['last_deletion'].setText(f"최근 삭제: {last_deletion_str}")

            next_auto = stats.get('next_auto_deletion')
            if next_auto:
                next_auto_str = next_auto.strftime("%Y-%m-%d")
                self.stats_labels['next_auto_deletion'].setText(f"다음 자동 삭제: {next_auto_str}")
            else:
                self.stats_labels['next_auto_deletion'].setText("다음 자동 삭제: 설정되지 않음")

        except Exception as e:
            print(f"통계 로드 오류: {e}")
            for label in self.stats_labels.values():
                label.setText("오류 발생")

    def load_auto_deletion_candidates(self):
        """자동 삭제 대상 로드"""
        try:
            candidates = self.deletion_manager.get_auto_deletion_candidates()

            self.auto_table.setRowCount(0)

            for row_idx, record in enumerate(candidates):
                self.auto_table.insertRow(row_idx)

                # 직원명
                employee_item = QTableWidgetItem(record.get('employee_name', ''))
                self.auto_table.setItem(row_idx, 0, employee_item)

                # 회사명
                company_item = QTableWidgetItem(record.get('company_name', ''))
                self.auto_table.setItem(row_idx, 1, company_item)

                # 기간
                pay_month = record.get('pay_month', '')
                if pay_month and '-' in pay_month:
                    year, month = pay_month.split('-')
                    period_text = f"{year}년 {int(month)}월"
                else:
                    period_text = pay_month
                period_item = QTableWidgetItem(period_text)
                self.auto_table.setItem(row_idx, 2, period_item)

                # 생성일
                created_at = record.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at)
                        date_text = dt.strftime("%Y-%m-%d")
                    except:
                        date_text = created_at
                else:
                    date_text = ''
                date_item = QTableWidgetItem(date_text)
                self.auto_table.setItem(row_idx, 3, date_item)

                # 경과 일수
                days_old = record.get('days_old', 0)
                days_item = QTableWidgetItem(f"{days_old}일")
                # 5년(1825일) 이상 경과한 경우 빨간색
                if days_old >= (365 * 5):
                    days_item.setBackground(Qt.GlobalColor.red)
                    days_item.setForeground(Qt.GlobalColor.white)
                self.auto_table.setItem(row_idx, 4, days_item)

            # 자동 삭제 버튼 활성화 상태
            self.auto_delete_btn.setEnabled(len(candidates) > 0)
            if len(candidates) > 0:
                self.auto_delete_btn.setText(f"🚫 자동 삭제 실행 ({len(candidates)}건)")
            else:
                self.auto_delete_btn.setText("🚫 자동 삭제 실행 (대상 없음)")

        except Exception as e:
            print(f"자동 삭제 대상 로드 오류: {e}")
            QMessageBox.critical(self, "오류", f"자동 삭제 대상 로드 중 오류가 발생했습니다:\n{str(e)}")

    def load_manual_deletion_candidates(self):
        """수동 삭제 대상 로드"""
        try:
            company_filter = self.manual_company_combo.currentData()
            year_filter = self.manual_year_combo.currentData()

            candidates = self.deletion_manager.get_manual_deletion_candidates(
                company_name=company_filter if company_filter else None,
                year=year_filter if year_filter else None
            )

            self.manual_table.setRowCount(0)
            self.selected_records = []

            for row_idx, record in enumerate(candidates):
                self.manual_table.insertRow(row_idx)

                # 체크박스 (선택용)
                checkbox = QTableWidgetItem()
                checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                checkbox.setData(Qt.ItemDataRole.UserRole, record['id'])
                self.manual_table.setItem(row_idx, 0, checkbox)

                # 직원명
                employee_item = QTableWidgetItem(record.get('employee_name', ''))
                self.manual_table.setItem(row_idx, 1, employee_item)

                # 회사명
                company_item = QTableWidgetItem(record.get('company_name', ''))
                self.manual_table.setItem(row_idx, 2, company_item)

                # 기간
                pay_month = record.get('pay_month', '')
                if pay_month and '-' in pay_month:
                    year, month = pay_month.split('-')
                    period_text = f"{year}년 {int(month)}월"
                else:
                    period_text = pay_month
                period_item = QTableWidgetItem(period_text)
                self.manual_table.setItem(row_idx, 3, period_item)

                # 생성일
                created_at = record.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at)
                        date_text = dt.strftime("%Y-%m-%d")
                    except:
                        date_text = created_at
                else:
                    date_text = ''
                date_item = QTableWidgetItem(date_text)
                self.manual_table.setItem(row_idx, 4, date_item)

                # 경과 일수
                days_old = record.get('days_old', 0)
                days_item = QTableWidgetItem(f"{days_old}일")
                self.manual_table.setItem(row_idx, 5, days_item)

            # 테이블 이벤트 연결
            self.manual_table.itemChanged.connect(self.update_manual_selection)

            # 수동 삭제 버튼 초기 상태
            self.update_manual_delete_button()

        except Exception as e:
            print(f"수동 삭제 대상 로드 오류: {e}")
            QMessageBox.critical(self, "오류", f"수동 삭제 대상 로드 중 오류가 발생했습니다:\n{str(e)}")

    def update_manual_selection(self, item):
        """수동 선택 항목 업데이트"""
        if item.column() != 0:  # 체크박스 컬럼만 처리
            return

        self.selected_records = []
        for row in range(self.manual_table.rowCount()):
            checkbox_item = self.manual_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                record_id = checkbox_item.data(Qt.ItemDataRole.UserRole)
                self.selected_records.append(record_id)

        self.update_manual_delete_button()

    def update_manual_delete_button(self):
        """수동 삭제 버튼 상태 업데이트"""
        has_selection = len(self.selected_records) > 0
        self.manual_delete_btn.setEnabled(has_selection)

        if has_selection:
            self.manual_delete_btn.setText(f"🗑️ 선택 항목 삭제 ({len(self.selected_records)}건)")
        else:
            self.manual_delete_btn.setText("🗑️ 선택 항목 삭제")

    def perform_auto_deletion(self):
        """자동 삭제 실행"""
        candidates = self.deletion_manager.get_auto_deletion_candidates()

        if not candidates:
            QMessageBox.information(self, "알림", "삭제 대상 기록이 없습니다.")
            return

        # 삭제 확인
        reply = QMessageBox.question(
            self, "자동 삭제 확인",
            f"법적 보존 기간이 경과한 {len(candidates)}개의 기록을 삭제하시겠습니까?\n\n"
            "※ 이 작업은 되돌릴 수 없습니다.\n"
            "※ 세무 조사 관련 기록은 자동으로 제외됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                result = self.deletion_manager.perform_auto_deletion()

                if result['success']:
                    QMessageBox.information(
                        self, "삭제 완료",
                        f"자동 삭제가 완료되었습니다.\n\n{result['message']}"
                    )
                    self.refresh_data()
                else:
                    QMessageBox.critical(self, "삭제 실패", result['message'])

            except Exception as e:
                QMessageBox.critical(self, "삭제 오류", f"자동 삭제 중 오류가 발생했습니다:\n{str(e)}")

    def perform_manual_deletion(self):
        """수동 삭제 실행"""
        if not self.selected_records:
            QMessageBox.warning(self, "선택 오류", "삭제할 기록을 선택해주세요.")
            return

        reason = self.deletion_reason_edit.toPlainText().strip()
        if not reason:
            QMessageBox.warning(self, "입력 오류", "삭제 사유를 입력해주세요.")
            return

        # 삭제 확인
        reply = QMessageBox.question(
            self, "수동 삭제 확인",
            f"선택된 {len(self.selected_records)}개의 기록을 삭제하시겠습니까?\n\n"
            f"삭제 사유: {reason}\n\n"
            "※ 이 작업은 되돌릴 수 없습니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.deletion_manager.perform_manual_deletion(
                    self.selected_records, reason, "사용자"
                )

                if success:
                    QMessageBox.information(
                        self, "삭제 완료",
                        f"{len(self.selected_records)}개의 기록이 삭제되었습니다."
                    )
                    self.load_manual_deletion_candidates()
                    self.selected_records = []
                    self.update_manual_delete_button()
                else:
                    QMessageBox.critical(self, "삭제 실패", "기록 삭제 중 오류가 발생했습니다.")

            except Exception as e:
                QMessageBox.critical(self, "삭제 오류", f"수동 삭제 중 오류가 발생했습니다:\n{str(e)}")

    def refresh_data(self):
        """데이터 새로고침"""
        self.load_statistics()
        self.load_auto_deletion_candidates()

        # 수동 삭제 필터가 적용되어 있다면 다시 로드
        if self.manual_company_combo.currentData() or self.manual_year_combo.currentData():
            self.load_manual_deletion_candidates()

    def showEvent(self, event):
        """다이얼로그 표시 시 회사 목록 로드"""
        super().showEvent(event)

        # 회사 목록 로드 (최초 1회)
        if self.manual_company_combo.count() == 1:  # "전체"만 있는 경우
            try:
                companies = self.deletion_manager.db.get_payslip_records(limit=1000)
                unique_companies = set()

                for record in companies:
                    if record.get('company_name'):
                        unique_companies.add(record['company_name'])

                for company in sorted(unique_companies):
                    self.manual_company_combo.addItem(company, company)

            except Exception as e:
                print(f"회사 목록 로드 오류: {e}")

        # 년도 목록 로드 (최초 1회)
        if self.manual_year_combo.count() == 1:  # "전체"만 있는 경우
            try:
                records = self.deletion_manager.db.get_payslip_records(limit=1000)
                unique_years = set()

                for record in records:
                    pay_month = record.get('pay_month', '')
                    if pay_month and '-' in pay_month:
                        year = pay_month.split('-')[0]
                        if year.isdigit():
                            unique_years.add(year)

                for year in sorted(unique_years, reverse=True):
                    self.manual_year_combo.addItem(f"{year}년", year)

            except Exception as e:
                print(f"년도 목록 로드 오류: {e}")


def show_data_deletion_manager(parent=None):
    """데이터 삭제 관리 다이얼로그 표시"""
    dialog = DataDeletionDialog(parent)
    return dialog.exec()