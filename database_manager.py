#!/usr/bin/env python3
"""
급여명세서 기록 데이터베이스 관리 모듈
SQLite 기반으로 급여명세서 저장, 조회, 삭제 기능 제공
"""

import sqlite3
import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

class PayslipDatabase:
    """급여명세서 기록 데이터베이스 관리 클래스"""

    def __init__(self, db_path: str = "payslip_history.db"):
        """
        데이터베이스 초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.init_database()
        logging.info(f"급여명세서 데이터베이스 초기화 완료: {db_path}")

    def init_database(self):
        """데이터베이스 및 테이블 생성"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- 급여명세서 기록 테이블
                CREATE TABLE IF NOT EXISTS payslip_history (
                    id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL,
                    employee_name TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    pay_month TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    memo TEXT,
                    html_content TEXT NOT NULL,
                    calculation_data TEXT,  -- 급여 계산 데이터 JSON
                    input_data_hash TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                );

                -- 데이터 삭제 감사 로그 테이블
                CREATE TABLE IF NOT EXISTS deletion_log (
                    id TEXT PRIMARY KEY,
                    deleted_record_ids TEXT,
                    deletion_reason TEXT,
                    deleted_by TEXT,
                    deletion_method TEXT,
                    deleted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER
                );

                -- 인덱스 생성 (성능 최적화)
                CREATE INDEX IF NOT EXISTS idx_payslip_lookup
                ON payslip_history(employee_id, pay_month, version DESC);

                CREATE INDEX IF NOT EXISTS idx_company_month
                ON payslip_history(company_name, pay_month);

                CREATE INDEX IF NOT EXISTS idx_active_records
                ON payslip_history(is_active);

                CREATE INDEX IF NOT EXISTS idx_created_at
                ON payslip_history(created_at DESC);
            """)

            # 데이터베이스 버전 관리
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER DEFAULT 1,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 버전 정보 확인 및 마이그레이션 수행
            cursor = conn.execute("SELECT version FROM db_version ORDER BY updated_at DESC LIMIT 1")
            current_version = cursor.fetchone()

            if not current_version:
                conn.execute("INSERT INTO db_version (version) VALUES (2)")  # 최신 버전으로 시작
            else:
                current_ver = current_version[0]
                if current_ver < 2:
                    logging.info(f"DB 마이그레이션 필요: v{current_ver} → v2")
                    self.migrate_database_v2(conn)
                    conn.execute("INSERT INTO db_version (version) VALUES (2)")
                    logging.info("DB 마이그레이션 완료: v2")

    def migrate_database_v2(self, conn):
        """
        DB 버전 2로 마이그레이션: calculation_data 필드 추가
        """
        try:
            # calculation_data 필드가 이미 있는지 확인
            cursor = conn.execute("PRAGMA table_info(payslip_history)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'calculation_data' not in columns:
                logging.info("calculation_data 필드 추가 시도")

                # SQLite는 ALTER TABLE로 TEXT 필드 추가가 제한적일 수 있음
                # 안전하게 백업 후 재생성 방식 사용
                self._migrate_with_recreate(conn)
                logging.info("DB 마이그레이션 v2 완료: calculation_data 필드 추가됨")
            else:
                logging.info("calculation_data 필드가 이미 존재함")

        except Exception as e:
            logging.error(f"DB 마이그레이션 v2 실패: {e}")
            raise

    def _migrate_with_recreate(self, conn):
        """
        테이블 재생성 방식으로 마이그레이션 수행
        """
        try:
            # 기존 데이터 백업
            cursor = conn.execute("SELECT * FROM payslip_history")
            existing_data = cursor.fetchall()

            column_names = [description[0] for description in cursor.description]

            if existing_data:
                logging.info(f"기존 데이터 {len(existing_data)}건 백업 완료")

                # 기존 테이블 삭제
                conn.execute("DROP TABLE payslip_history")

                # 새 스키마로 테이블 재생성
                conn.executescript("""
                    CREATE TABLE payslip_history (
                        id TEXT PRIMARY KEY,
                        employee_id TEXT NOT NULL,
                        employee_name TEXT NOT NULL,
                        company_name TEXT NOT NULL,
                        pay_month TEXT NOT NULL,
                        version INTEGER DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        memo TEXT,
                        html_content TEXT NOT NULL,
                        calculation_data TEXT,
                        input_data_hash TEXT,
                        is_active BOOLEAN DEFAULT TRUE
                    );
                """)

                # 데이터 복원 (calculation_data는 빈 값으로)
                for row in existing_data:
                    row_dict = dict(zip(column_names, row))
                    conn.execute("""
                        INSERT INTO payslip_history
                        (id, employee_id, employee_name, company_name, pay_month,
                         version, created_at, memo, html_content, calculation_data, input_data_hash, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row_dict.get('id'),
                        row_dict.get('employee_id'),
                        row_dict.get('employee_name'),
                        row_dict.get('company_name'),
                        row_dict.get('pay_month'),
                        row_dict.get('version', 1),
                        row_dict.get('created_at'),
                        row_dict.get('memo'),
                        row_dict.get('html_content'),
                        None,  # calculation_data는 새로 추가되므로 None
                        row_dict.get('input_data_hash'),
                        row_dict.get('is_active', True)
                    ))

                logging.info(f"데이터 복원 완료: {len(existing_data)}건")

                # 인덱스 재생성
                conn.executescript("""
                    CREATE INDEX IF NOT EXISTS idx_payslip_lookup
                    ON payslip_history(employee_id, pay_month, version DESC);

                    CREATE INDEX IF NOT EXISTS idx_company_month
                    ON payslip_history(company_name, pay_month);

                    CREATE INDEX IF NOT EXISTS idx_active_records
                    ON payslip_history(is_active);

                    CREATE INDEX IF NOT EXISTS idx_created_at
                    ON payslip_history(created_at DESC);
                """)

                logging.info("인덱스 재생성 완료")

        except Exception as e:
            logging.error(f"테이블 재생성 마이그레이션 실패: {e}")
            raise

    def save_payslip_record(self, record: Dict[str, Any]) -> bool:
        """
        급여명세서 기록 저장

        Args:
            record: 급여명세서 기록 데이터
                {
                    'id': 고유 ID,
                    'employee_id': 직원 ID,
                    'employee_name': 직원명,
                    'company_name': 회사명,
                    'pay_month': 지급 월 (YYYY-MM),
                    'version': 버전,
                    'memo': 메모,
                    'html_content': HTML 내용,
                    'calculation_data': 급여 계산 데이터 (JSON 문자열),
                    'input_data_hash': 데이터 해시
                }

        Returns:
            bool: 저장 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO payslip_history
                    (id, employee_id, employee_name, company_name, pay_month,
                     version, memo, html_content, calculation_data, input_data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['id'],
                    record['employee_id'],
                    record['employee_name'],
                    record['company_name'],
                    record['pay_month'],
                    record['version'],
                    record.get('memo', ''),
                    record['html_content'],
                    record.get('calculation_data', '{}'),  # JSON 문자열
                    record.get('input_data_hash', '')
                ))

                logging.info(f"급여명세서 기록 저장 완료: {record['employee_name']} ({record['pay_month']}) v{record['version']}")
                return True

        except Exception as e:
            logging.error(f"급여명세서 기록 저장 실패: {e}")
            return False

    def get_latest_version(self, employee_id: str, pay_month: str) -> int:
        """
        특정 직원/월의 최신 버전 조회

        Args:
            employee_id: 직원 ID
            pay_month: 지급 월 (YYYY-MM)

        Returns:
            int: 최신 버전 번호 (없으면 0)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT MAX(version) FROM payslip_history
                    WHERE employee_id = ? AND pay_month = ? AND is_active = TRUE
                """, (employee_id, pay_month))

                result = cursor.fetchone()
                return result[0] if result[0] else 0

        except Exception as e:
            logging.error(f"최신 버전 조회 실패: {e}")
            return 0

    def get_payslip_records(self, filters: Dict[str, Any] = None,
                           limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        급여명세서 기록 조회 (필터링 지원)

        Args:
            filters: 필터 조건 딕셔너리
                {
                    'employee_name': 직원명 (부분 검색),
                    'company_name': 회사명,
                    'pay_month': 지급 월,
                    'year': 연도,
                    'month': 월
                }
            limit: 최대 조회 건수
            offset: 조회 시작 위치

        Returns:
            List[Dict]: 급여명세서 기록 리스트
        """
        try:
            query = """
                SELECT id, employee_id, employee_name, company_name, pay_month,
                       version, created_at, memo, input_data_hash
                FROM payslip_history
                WHERE is_active = TRUE
            """

            params = []

            if filters:
                conditions = []

                if 'employee_name' in filters and filters['employee_name']:
                    conditions.append("employee_name LIKE ?")
                    params.append(f"%{filters['employee_name']}%")

                if 'company_name' in filters and filters['company_name']:
                    conditions.append("company_name = ?")
                    params.append(filters['company_name'])

                if 'company_name_like' in filters and filters['company_name_like']:
                    conditions.append("company_name LIKE ?")
                    params.append(f"%{filters['company_name_like']}%")

                if 'pay_month' in filters and filters['pay_month']:
                    conditions.append("pay_month = ?")
                    params.append(filters['pay_month'])

                if 'year' in filters and filters['year']:
                    conditions.append("pay_month LIKE ?")
                    params.append(f"{filters['year']}-%")

                if 'month' in filters and filters['month']:
                    month_padded = filters['month'].zfill(2)
                    conditions.append("pay_month LIKE ?")
                    params.append(f"%-{month_padded}")

                if conditions:
                    query += " AND " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)

                records = []
                for row in cursor:
                    record = dict(row)
                    # HTML 콘텐츠는 메모리 절약을 위해 별도 조회
                    record['html_content'] = None
                    records.append(record)

                return records

        except Exception as e:
            logging.error(f"급여명세서 기록 조회 실패: {e}")
            return []

    def get_payslip_content(self, record_id: str) -> Optional[str]:
        """
        특정 기록의 HTML 콘텐츠 조회

        Args:
            record_id: 기록 ID

        Returns:
            Optional[str]: HTML 콘텐츠 (없으면 None)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT html_content FROM payslip_history
                    WHERE id = ? AND is_active = TRUE
                """, (record_id,))

                result = cursor.fetchone()
                return result[0] if result else None

        except Exception as e:
            logging.error(f"급여명세서 콘텐츠 조회 실패: {e}")
            return None

    def get_company_month_records(self, company_name: str, year: str, month: str) -> List[Dict[str, Any]]:
        """
        특정 회사/년도/월의 모든 최신 버전 기록 조회

        Args:
            company_name: 회사명
            year: 연도 (YYYY)
            month: 월 (MM)

        Returns:
            List[Dict]: 급여명세서 기록 리스트
        """
        try:
            pay_month = f"{year}-{month.zfill(2)}"

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT ph.* FROM payslip_history ph
                    INNER JOIN (
                        SELECT employee_id, pay_month, MAX(version) as max_version
                        FROM payslip_history
                        WHERE company_name = ? AND pay_month = ? AND is_active = TRUE
                        GROUP BY employee_id, pay_month
                    ) mv ON ph.employee_id = mv.employee_id
                         AND ph.pay_month = mv.pay_month
                         AND ph.version = mv.max_version
                    WHERE ph.is_active = TRUE
                    ORDER BY ph.employee_name
                """, (company_name, pay_month))

                records = []
                for row in cursor:
                    record = dict(row)
                    records.append(record)

                return records

        except Exception as e:
            logging.error(f"회사/월별 기록 조회 실패: {e}")
            return []

    def soft_delete_records(self, record_ids: List[str], reason: str, deleted_by: str) -> bool:
        """
        기록들 소프트 삭제 (법적 보존을 위해 실제 삭제하지 않음)

        Args:
            record_ids: 삭제할 기록 ID 리스트
            reason: 삭제 사유
            deleted_by: 삭제자

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 소프트 삭제
                placeholders = ','.join('?' * len(record_ids))
                conn.execute(f"""
                    UPDATE payslip_history
                    SET is_active = FALSE
                    WHERE id IN ({placeholders})
                """, record_ids)

                # 삭제 감사 로그 기록
                deletion_id = self._generate_id()
                conn.execute("""
                    INSERT INTO deletion_log
                    (id, deleted_record_ids, deletion_reason, deleted_by,
                     deletion_method, record_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    deletion_id,
                    json.dumps(record_ids),
                    reason,
                    deleted_by,
                    'MANUAL',
                    len(record_ids)
                ))

                logging.info(f"급여명세서 기록 소프트 삭제 완료: {len(record_ids)}건")
                return True

        except Exception as e:
            logging.error(f"급여명세서 기록 삭제 실패: {e}")
            return False

    def get_auto_deletion_candidates(self, retention_years: int = 5) -> List[Dict[str, Any]]:
        """
        법적 보존 기간이 지난 자동 삭제 대상 기록 조회

        Args:
            retention_years: 보존 연수 (기본 5년)

        Returns:
            List[Dict]: 삭제 대상 기록 리스트
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_years * 365)

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM payslip_history
                    WHERE created_at < ?
                    AND is_active = TRUE
                    AND (memo NOT LIKE '%세무조사%' OR memo IS NULL)
                    ORDER BY created_at ASC
                """, (cutoff_date,))

                records = []
                for row in cursor:
                    record = dict(row)
                    record['days_old'] = (datetime.now() - datetime.fromisoformat(record['created_at'])).days
                    records.append(record)

                return records

        except Exception as e:
            logging.error(f"자동 삭제 대상 조회 실패: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        데이터베이스 통계 정보 조회

        Returns:
            Dict: 통계 정보
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 전체 기록 수
                cursor = conn.execute("SELECT COUNT(*) FROM payslip_history WHERE is_active = TRUE")
                total_records = cursor.fetchone()[0]

                # 회사 수
                cursor = conn.execute("SELECT COUNT(DISTINCT company_name) FROM payslip_history WHERE is_active = TRUE")
                total_companies = cursor.fetchone()[0]

                # 직원 수
                cursor = conn.execute("SELECT COUNT(DISTINCT employee_id) FROM payslip_history WHERE is_active = TRUE")
                total_employees = cursor.fetchone()[0]

                # 최근 기록 날짜
                cursor = conn.execute("SELECT MAX(created_at) FROM payslip_history WHERE is_active = TRUE")
                latest_record = cursor.fetchone()[0]

                # 데이터베이스 파일 크기
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                return {
                    'total_records': total_records,
                    'total_companies': total_companies,
                    'total_employees': total_employees,
                    'latest_record': latest_record,
                    'db_size_mb': db_size / (1024 * 1024)
                }

        except Exception as e:
            logging.error(f"통계 정보 조회 실패: {e}")
            return {}

    def backup_database(self, backup_path: str) -> bool:
        """
        데이터베이스 백업

        Args:
            backup_path: 백업 파일 경로

        Returns:
            bool: 백업 성공 여부
        """
        try:
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
                    logging.info(f"데이터베이스 백업 완료: {backup_path}")
                    return True

        except Exception as e:
            logging.error(f"데이터베이스 백업 실패: {e}")
            return False

    def _generate_id(self) -> str:
        """고유 ID 생성"""
        import uuid
        return str(uuid.uuid4())

    def validate_data_integrity(self, record_id: str) -> Dict[str, Any]:
        """
        데이터 무결성 검증

        Args:
            record_id: 검증할 기록 ID

        Returns:
            Dict: 검증 결과
        """
        try:
            record = self.get_payslip_content(record_id)
            if not record:
                return {'valid': False, 'error': '기록을 찾을 수 없습니다'}

            stored_hash = None
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT input_data_hash FROM payslip_history WHERE id = ?", (record_id,))
                result = cursor.fetchone()
                stored_hash = result[0] if result else None

            if not stored_hash:
                return {'valid': False, 'error': '저장된 해시가 없습니다'}

            current_hash = hashlib.sha256(record.encode()).hexdigest()

            if stored_hash == current_hash:
                return {'valid': True, 'message': '데이터 무결성이 확인되었습니다'}
            else:
                return {'valid': False, 'error': '데이터가 변조되었습니다'}

        except Exception as e:
            return {'valid': False, 'error': f'검증 중 오류 발생: {e}'}

    def extract_payslip_data_from_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        """
        DB 행에서 급여명세서 주요 데이터를 추출

        Args:
            row: DB 행 데이터

        Returns:
            Dict: 추출된 급여 데이터
        """
        try:
            html_content = self.get_payslip_content(row['id'])
            if not html_content:
                logging.debug(f"HTML 콘텐츠를 찾을 수 없음: employee_id={row['employee_id']}, pay_month={row['pay_month']}")
                return None

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            data = {
                'employee_id': row['employee_id'],
                'employee_name': row['employee_name'],
                'pay_month': row['pay_month'],
                'base_pay': 0,
                'weekly_holiday_allowance': 0,
                'extra_pay': 0,
                'night_pay': 0,
                'allowance_total': 0,
                'national_pension': 0,
                'health_insurance': 0,
                'employment_insurance': 0,
                'long_term_care_insurance': 0,
                'income_tax': 0,
                'local_income_tax': 0,
                'net_pay': 0,
                'total_payment': 0,
                'total_deduction': 0
            }

            # 급여 항목 추출
            salary_table = soup.find('table', class_='salary-table')
            if salary_table:
                rows = salary_table.find_all('tr')
                for tr in rows:
                    cells = tr.find_all('td')
                    if len(cells) >= 2:
                        item_name = cells[0].get_text(strip=True)
                        amount_text = cells[1].get_text(strip=True).replace(',', '').replace('원', '')

                        try:
                            amount = float(amount_text) if amount_text and amount_text != '-' else 0

                            # 항목명 매핑
                            if '기본급' in item_name:
                                data['base_pay'] = amount
                            elif '주휴수당' in item_name:
                                data['weekly_holiday_allowance'] = amount
                            elif '연장수당' in item_name:
                                data['overtime_pay'] = amount
                            elif '야간수당' in item_name:
                                data['night_pay'] = amount
                            elif '국민연금' in item_name:
                                data['national_pension'] = amount
                            elif '건강보험' in item_name:
                                data['health_insurance'] = amount
                            elif '고용보험' in item_name:
                                data['employment_insurance'] = amount
                            elif '장기요양보험' in item_name:
                                data['long_term_care_insurance'] = amount
                            elif '소득세' in item_name:
                                data['income_tax'] = amount
                            elif '지방소득세' in item_name:
                                data['local_income_tax'] = amount
                        except ValueError as e:
                            logging.debug(f"금액 파싱 실패: item_name={item_name}, amount_text='{amount_text}', error={e}")

                # 합계 행에서 총액 추출
                for tr in rows:
                    if '합계' in tr.get_text():
                        cells = tr.find_all('td')
                        if len(cells) >= 4:
                            # 지급합계, 공제합계
                            payment_text = cells[1].get_text(strip=True).replace(',', '').replace('원', '')
                            deduction_text = cells[3].get_text(strip=True).replace(',', '').replace('원', '')

                            try:
                                data['total_payment'] = float(payment_text) if payment_text else 0
                                data['total_deduction'] = float(deduction_text) if deduction_text else 0
                            except ValueError as e:
                                logging.debug(f"합계 금액 파싱 실패: payment_text='{payment_text}', deduction_text='{deduction_text}', error={e}")

                # 실지급액 추출
                net_pay_row = soup.find('td', string=lambda text: text and '실지급액' in text)
                if net_pay_row:
                    parent_row = net_pay_row.find_parent('tr')
                    if parent_row:
                        cells = parent_row.find_all('td')
                        if len(cells) >= 3:
                            net_pay_text = cells[1].get_text(strip=True).replace(',', '').replace('원', '')
                            try:
                                data['net_pay'] = float(net_pay_text) if net_pay_text else 0
                            except ValueError as e:
                                logging.debug(f"실지급액 파싱 실패: net_pay_text='{net_pay_text}', error={e}")

            logging.debug(f"DB에서 추출된 데이터: employee={data['employee_name']}, base_pay={data['base_pay']}, total_payment={data['total_payment']}, net_pay={data['net_pay']}")
            return data

        except Exception as e:
            logging.error(f"급여 데이터 추출 실패: employee_id={row.get('employee_id', 'unknown')}, error={e}")
            return None

    def compare_payslip_data(self, existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        기존 급여 데이터와 새 데이터를 비교하여 변동사항 반환

        Args:
            existing_data: 기존 DB 데이터
            new_data: 새로 계산된 데이터

        Returns:
            Dict: 변동사항 정보
        """
        employee_name = new_data.get('employee_name', 'Unknown')
        pay_month = new_data.get('pay_month', 'Unknown')

        logging.info(f"[비교시작] 직원: {employee_name}, 월: {pay_month}")

        changes = {
            'has_changes': False,
            'payment_changes': [],
            'deduction_changes': [],
            'summary_changes': []
        }

        # 비교할 필드들
        payment_fields = {
            'base_pay': '기본급',
            'weekly_holiday_allowance': '주휴수당',
            'overtime_pay': '연장수당',
            'night_pay': '야간수당',
            'allowance_total': '수당합계'
        }

        deduction_fields = {
            'national_pension': '국민연금',
            'health_insurance': '건강보험',
            'employment_insurance': '고용보험',
            'long_term_care_insurance': '장기요양보험',
            'income_tax': '소득세',
            'local_income_tax': '지방소득세'
        }

        summary_fields = {
            'total_payment': '지급합계',
            'total_deduction': '공제합계',
            'net_pay': '실지급액'
        }

        # 지급 항목 비교
        print(f"[DEBUG] {employee_name} 지급항목 비교 시작")
        for field, name in payment_fields.items():
            old_val = existing_data.get(field, 0)
            new_val = new_data.get(field, 0)
            diff = abs(old_val - new_val)
            print(f"[비교] 지급항목 '{name}': 기존={old_val:.6f}, 신규={new_val:.6f}, 차이={diff:.6f}")
            if diff > 1.0:  # 1원 이상 차이만 의미있는 변동으로 간주
                print(f"[변동감지] 지급항목 '{name}': 기존 {old_val:,.0f}원 → 신규 {new_val:,.0f}원 (차이: {new_val - old_val:,.0f}원)")
                changes['has_changes'] = True
                changes['payment_changes'].append({
                    'field': field,
                    'name': name,
                    'old_value': old_val,
                    'new_value': new_val,
                    'difference': new_val - old_val
                })

        # 공제 항목 비교
        print(f"[DEBUG] {employee_name} 공제항목 비교 시작")
        for field, name in deduction_fields.items():
            old_val = existing_data.get(field, 0)
            new_val = new_data.get(field, 0)
            diff = abs(old_val - new_val)
            print(f"[비교] 공제항목 '{name}': 기존={old_val:.6f}, 신규={new_val:.6f}, 차이={diff:.6f}")
            if diff > 1.0:  # 1원으로 통일
                print(f"[변동감지] 공제항목 '{name}': 기존 {old_val:,.0f}원 → 신규 {new_val:,.0f}원 (차이: {new_val - old_val:,.0f}원)")
                changes['has_changes'] = True
                changes['deduction_changes'].append({
                    'field': field,
                    'name': name,
                    'old_value': old_val,
                    'new_value': new_val,
                    'difference': new_val - old_val
                })

        # 합계 항목 비교
        print(f"[DEBUG] {employee_name} 합계항목 비교 시작")
        for field, name in summary_fields.items():
            old_val = existing_data.get(field, 0)
            new_val = new_data.get(field, 0)
            diff = abs(old_val - new_val)
            print(f"[비교] 합계항목 '{name}': 기존={old_val:.6f}, 신규={new_val:.6f}, 차이={diff:.6f}")
            if diff > 1.0:  # 1원으로 통일
                print(f"[변동감지] 합계항목 '{name}': 기존 {old_val:,.0f}원 → 신규 {new_val:,.0f}원 (차이: {new_val - old_val:,.0f}원)")
                changes['has_changes'] = True
                changes['summary_changes'].append({
                    'field': field,
                    'name': name,
                    'old_value': old_val,
                    'new_value': new_val,
                    'difference': new_val - old_val
                })

        logging.debug(f"비교 결과: has_changes={changes['has_changes']}, payment_changes={len(changes['payment_changes'])}, deduction_changes={len(changes['deduction_changes'])}, summary_changes={len(changes['summary_changes'])}")
        return changes

    def get_existing_payslip_data(self, employee_id: str, pay_month: str) -> Optional[Dict[str, Any]]:
        """
        특정 직원/월의 최신 급여 데이터를 가져옴 (계산 데이터 우선 사용)

        Args:
            employee_id: 직원 ID
            pay_month: 지급 월 (YYYY-MM)

        Returns:
            Optional[Dict]: 기존 급여 데이터 (없으면 None)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM payslip_history
                    WHERE employee_id = ? AND pay_month = ? AND is_active = TRUE
                    ORDER BY version DESC LIMIT 1
                """, (employee_id, pay_month))

                row = cursor.fetchone()
                if row:
                    row_dict = dict(row)

                    # calculation_data가 있는 경우 JSON 파싱하여 반환
                    calculation_data_json = row_dict.get('calculation_data')
                    if calculation_data_json and calculation_data_json.strip():
                        try:
                            calculation_data = json.loads(calculation_data_json)
                            # 메타데이터 포함
                            calculation_data['version'] = row_dict['version']
                            calculation_data['db_id'] = row_dict['id']
                            logging.debug(f"계산 데이터에서 불러옴: employee={row_dict['employee_name']}, base_pay={calculation_data.get('base_pay', 0)}, v{row_dict['version']}")
                            return calculation_data
                        except json.JSONDecodeError as e:
                            logging.warning(f"계산 데이터 JSON 파싱 실패, HTML 파싱으로 폴백: {e}")

                    # calculation_data가 없거나 파싱 실패한 경우 HTML 파싱으로 폴백
                    return self.extract_payslip_data_from_row(row)

                return None

        except Exception as e:
            logging.error(f"기존 급여 데이터 조회 실패: {e}")
            return None


def get_database_path() -> str:
    """
    설정 파일에서 데이터베이스 경로를 가져옵니다.

    Returns:
        str: 데이터베이스 파일 경로
    """
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        db_path = config.get('database_path', 'payslip_history.db')

        # 경로가 디렉토리인 경우 파일명 추가
        if os.path.isdir(db_path):
            db_path = os.path.join(db_path, 'payslip_history.db')

        # 폴더 생성
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"데이터베이스 폴더 생성: {db_dir}")

        logging.info(f"데이터베이스 경로 설정: {db_path}")
        return db_path

    except FileNotFoundError:
        logging.warning("설정 파일을 찾을 수 없어 기본 데이터베이스 경로 사용")
        return 'payslip_history.db'
    except json.JSONDecodeError:
        logging.warning("설정 파일 파싱 오류로 기본 데이터베이스 경로 사용")
        return 'payslip_history.db'
    except Exception as e:
        logging.warning(f"데이터베이스 경로 설정 오류: {e}, 기본 경로 사용")
        return 'payslip_history.db'


# 전역 데이터베이스 인스턴스
_db_instance = None

def get_database() -> PayslipDatabase:
    """데이터베이스 싱글톤 인스턴스 반환"""
    global _db_instance
    if _db_instance is None:
        db_path = get_database_path()
        _db_instance = PayslipDatabase(db_path)
    return _db_instance
