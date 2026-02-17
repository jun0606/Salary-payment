#!/usr/bin/env python3
"""
라이선스 시스템 보안 모니터링 및 관리 스크립트

기능:
- 정기적 라이선스 파일 보안 검사
- 라이선스 접근 로그 분석
- HW ID 변경 감지 및 알림
- 라이선스 파일 무결성 검증
- 보안 이벤트 로깅
"""

import os
import sys
import logging
import datetime
import hashlib
import json
from pathlib import Path

# 라이선스 시스템 모듈 임포트
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'license_system'))
from license_system import license_verifier
from license_system.license_verifier import LicenseType, LicenseManager, audit_license_access


class LicenseSecurityMonitor:
    """
    라이선스 시스템의 보안을 모니터링하고 관리하는 클래스
    """

    def __init__(self):
        self.monitor_log_path = os.path.join(
            os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
            'PayslipApp', 'security_monitor.log'
        )
        self.integrity_db_path = os.path.join(
            os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
            'PayslipApp', 'license_integrity.json'
        )

        # 로깅 설정
        self._setup_logging()

    def _setup_logging(self):
        """보안 모니터링용 로깅 설정"""
        logging.basicConfig(
            filename=self.monitor_log_path,
            level=logging.INFO,
            format='%(asctime)s - SECURITY - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 콘솔에도 출력
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        self.logger = logging.getLogger(__name__)

    def run_full_security_audit(self):
        """
        전체 라이선스 시스템 보안 감사를 수행합니다.
        """
        self.logger.info("=== 라이선스 시스템 보안 감사 시작 ===")

        audit_results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'checks': []
        }

        try:
            # 1. 라이선스 파일 존재 및 권한 검사
            audit_results['checks'].append(self._check_license_file_integrity())

            # 2. 라이선스 파일 접근 감사
            audit_results['checks'].append(self._audit_license_access())

            # 3. HW ID 일관성 검사
            audit_results['checks'].append(self._check_hw_id_consistency())

            # 4. 라이선스 파일 무결성 검증
            audit_results['checks'].append(self._verify_license_integrity())

            # 5. 라이선스 만료 상태 모니터링
            audit_results['checks'].append(self._monitor_license_expiry())

            # 6. 비정상 접근 패턴 감지
            audit_results['checks'].append(self._detect_suspicious_activity())

            # 감사 결과 요약
            self._summarize_audit_results(audit_results)

            self.logger.info("=== 라이선스 시스템 보안 감사 완료 ===")

            return audit_results

        except Exception as e:
            self.logger.error(f"보안 감사 중 오류 발생: {e}")
            audit_results['error'] = str(e)
            return audit_results

    def _check_license_file_integrity(self):
        """라이선스 파일의 무결성을 검사합니다."""
        self.logger.info("라이선스 파일 무결성 검사 시작")

        results = {
            'check': 'license_file_integrity',
            'status': 'PASS',
            'details': [],
            'issues': []
        }

        try:
            # 세무사 라이선스 검사
            try:
                tax_dir, tax_file = LicenseManager.get_license_paths(LicenseType.TAX_ACCOUNTANT)

                if os.path.exists(tax_file):
                    # 파일 권한 검사
                    file_stat = os.stat(tax_file)

                    # 파일 크기 검사 (비어있지 않은지)
                    if file_stat.st_size == 0:
                        results['issues'].append(f"빈 세무사 라이선스 파일 발견: {tax_file}")
                        results['status'] = 'WARN'

                    # 파일 권한 검사 (읽기 가능해야 함)
                    if not os.access(tax_file, os.R_OK):
                        results['issues'].append(f"세무사 라이선스 파일 읽기 권한 없음: {tax_file}")
                        results['status'] = 'FAIL'

                    results['details'].append("✓ 세무사 라이선스 파일 검증 완료")
                else:
                    results['details'].append("ℹ️ 세무사 라이선스 파일 없음")

            except Exception as e:
                results['issues'].append(f"세무사 라이선스 파일 검사 중 오류: {e}")
                results['status'] = 'ERROR'

            # 고객 라이선스 검사 (HW ID별 폴더 검사)
            try:
                customer_base_dir = license_verifier.CUSTOMER_DIR

                if os.path.exists(customer_base_dir):
                    customer_folders = [f for f in os.listdir(customer_base_dir)
                                      if os.path.isdir(os.path.join(customer_base_dir, f))]

                    if customer_folders:
                        results['details'].append(f"✓ {len(customer_folders)}개 고객 라이선스 폴더 발견")

                        for hw_id_folder in customer_folders:
                            customer_file = os.path.join(customer_base_dir, hw_id_folder, license_verifier.LICENSE_FILE_NAME)
                            if os.path.exists(customer_file):
                                # 파일 권한 검사
                                file_stat = os.stat(customer_file)

                                # 파일 크기 검사
                                if file_stat.st_size == 0:
                                    results['issues'].append(f"빈 고객 라이선스 파일 발견: {customer_file}")
                                    results['status'] = 'WARN'

                                # 파일 권한 검사
                                if not os.access(customer_file, os.R_OK):
                                    results['issues'].append(f"고객 라이선스 파일 읽기 권한 없음: {customer_file}")
                                    results['status'] = 'FAIL'
                            else:
                                results['issues'].append(f"고객 라이선스 파일 누락: {customer_file}")
                                results['status'] = 'WARN'
                    else:
                        results['details'].append("ℹ️ 고객 라이선스 폴더 없음")
                else:
                    results['details'].append("ℹ️ 고객 라이선스 기본 폴더 없음")

            except Exception as e:
                results['issues'].append(f"고객 라이선스 파일 검사 중 오류: {e}")
                results['status'] = 'ERROR'

        except Exception as e:
            results['issues'].append(f"파일 무결성 검사 중 오류: {e}")
            results['status'] = 'ERROR'

        self.logger.info(f"라이선스 파일 무결성 검사 완료: {results['status']}")
        return results

    def _audit_license_access(self):
        """라이선스 파일 접근을 감사합니다."""
        self.logger.info("라이선스 파일 접근 감사 시작")

        results = {
            'check': 'license_access_audit',
            'status': 'PASS',
            'details': [],
            'issues': []
        }

        try:
            # audit_license_access 함수 호출
            audit_success = audit_license_access()

            if audit_success:
                results['details'].append("라이선스 접근 감사 성공")
            else:
                results['issues'].append("라이선스 접근 감사 실패")
                results['status'] = 'WARN'

        except Exception as e:
            results['issues'].append(f"접근 감사 중 오류: {e}")
            results['status'] = 'ERROR'

        self.logger.info(f"라이선스 파일 접근 감사 완료: {results['status']}")
        return results

    def _check_hw_id_consistency(self):
        """HW ID의 일관성을 검사합니다."""
        self.logger.info("HW ID 일관성 검사 시작")

        results = {
            'check': 'hw_id_consistency',
            'status': 'PASS',
            'details': [],
            'issues': []
        }

        try:
            from license_system.hardware_id import get_machine_id
            current_hw_id = get_machine_id()

            if not current_hw_id:
                results['issues'].append("현재 HW ID를 가져올 수 없음")
                results['status'] = 'ERROR'
                return results

            results['details'].append(f"현재 HW ID: {current_hw_id}")

            # 라이선스 파일들의 HW ID 검증
            for license_type in [LicenseType.TAX_ACCOUNTANT, LicenseType.CUSTOMER]:
                try:
                    if license_type == LicenseType.TAX_ACCOUNTANT:
                        status = LicenseManager.check_license_v2(license_type)
                        if status == 'INVALID_LICENSE':
                            results['issues'].append(f"{license_type} 라이선스 HW ID 불일치")
                            results['status'] = 'WARN'
                        else:
                            results['details'].append(f"✓ {license_type} 라이선스 HW ID 검증 완료")
                    else:
                        # 고객 라이선스는 모든 HW ID 폴더 검사
                        customer_dir = license_verifier.CUSTOMER_DIR
                        if os.path.exists(customer_dir):
                            for hw_id_dir in os.listdir(customer_dir):
                                hw_id_path = os.path.join(customer_dir, hw_id_dir)
                                if os.path.isdir(hw_id_path):
                                    status = LicenseManager.check_license_v2(license_type, hw_id_dir)
                                    if status == 'INVALID_LICENSE':
                                        results['issues'].append(f"고객 라이선스 HW ID 불일치: {hw_id_dir}")
                                        results['status'] = 'WARN'

                except Exception as e:
                    results['issues'].append(f"{license_type} HW ID 검사 중 오류: {e}")
                    results['status'] = 'ERROR'

        except Exception as e:
            results['issues'].append(f"HW ID 일관성 검사 중 오류: {e}")
            results['status'] = 'ERROR'

        self.logger.info(f"HW ID 일관성 검사 완료: {results['status']}")
        return results

    def _verify_license_integrity(self):
        """라이선스 파일의 무결성을 검증합니다."""
        self.logger.info("라이선스 파일 무결성 검증 시작")

        results = {
            'check': 'license_integrity',
            'status': 'PASS',
            'details': [],
            'issues': []
        }

        try:
            # 기존 무결성 데이터베이스 로드
            integrity_db = self._load_integrity_database()

            for license_type in [LicenseType.TAX_ACCOUNTANT, LicenseType.CUSTOMER]:
                try:
                    license_dir, license_file = LicenseManager.get_license_paths(license_type)

                    if os.path.exists(license_file):
                        # 파일 해시 계산
                        current_hash = self._calculate_file_hash(license_file)

                        # 이전 해시와 비교
                        file_key = f"{license_type}:{license_file}"
                        previous_hash = integrity_db.get(file_key)

                        if previous_hash:
                            if current_hash != previous_hash:
                                results['issues'].append(f"라이선스 파일 변경 감지: {license_file}")
                                results['status'] = 'WARN'
                                self.logger.warning(f"라이선스 파일 무결성 변경: {license_file}")
                            else:
                                results['details'].append(f"✓ {license_type} 라이선스 파일 무결성 확인")
                        else:
                            results['details'].append(f"✓ {license_type} 라이선스 파일 초기 해시 기록")

                        # 현재 해시 저장
                        integrity_db[file_key] = current_hash

                    else:
                        results['details'].append(f"ℹ️ {license_type} 라이선스 파일 없음")

                except Exception as e:
                    results['issues'].append(f"{license_type} 무결성 검증 중 오류: {e}")
                    results['status'] = 'ERROR'

            # 무결성 데이터베이스 저장
            self._save_integrity_database(integrity_db)

        except Exception as e:
            results['issues'].append(f"라이선스 무결성 검증 중 오류: {e}")
            results['status'] = 'ERROR'

        self.logger.info(f"라이선스 파일 무결성 검증 완료: {results['status']}")
        return results

    def _monitor_license_expiry(self):
        """라이선스 만료 상태를 모니터링합니다."""
        self.logger.info("라이선스 만료 모니터링 시작")

        results = {
            'check': 'license_expiry_monitoring',
            'status': 'PASS',
            'details': [],
            'issues': []
        }

        try:
            # 모든 라이선스 파일 검사
            for license_type in [LicenseType.TAX_ACCOUNTANT, LicenseType.CUSTOMER]:
                try:
                    if license_type == LicenseType.TAX_ACCOUNTANT:
                        status = LicenseManager.check_license_v2(license_type)
                        if status == 'EXPIRED':
                            results['issues'].append("세무사 라이선스 만료됨")
                            results['status'] = 'WARN'
                        elif status == 'LICENSED':
                            results['details'].append("✓ 세무사 라이선스 유효")
                        else:
                            results['details'].append(f"세무사 라이선스 상태: {status}")
                    else:
                        # 고객 라이선스는 모든 HW ID 폴더 검사
                        customer_dir = license_verifier.CUSTOMER_DIR
                        if os.path.exists(customer_dir):
                            for hw_id_dir in os.listdir(customer_dir):
                                hw_id_path = os.path.join(customer_dir, hw_id_dir)
                                if os.path.isdir(hw_id_path):
                                    status = LicenseManager.check_license_v2(license_type, hw_id_dir)
                                    if status == 'EXPIRED':
                                        results['issues'].append(f"고객 라이선스 만료됨: {hw_id_dir}")
                                        results['status'] = 'WARN'
                                    elif status == 'LICENSED':
                                        results['details'].append(f"✓ 고객 라이선스 유효: {hw_id_dir}")

                except Exception as e:
                    results['issues'].append(f"{license_type} 만료 모니터링 중 오류: {e}")
                    results['status'] = 'ERROR'

        except Exception as e:
            results['issues'].append(f"라이선스 만료 모니터링 중 오류: {e}")
            results['status'] = 'ERROR'

        self.logger.info(f"라이선스 만료 모니터링 완료: {results['status']}")
        return results

    def _detect_suspicious_activity(self):
        """비정상적인 라이선스 접근 패턴을 감지합니다."""
        self.logger.info("비정상 활동 감지 시작")

        results = {
            'check': 'suspicious_activity_detection',
            'status': 'PASS',
            'details': [],
            'issues': []
        }

        try:
            # 최근 로그 파일 분석 (단순 구현)
            if os.path.exists(self.monitor_log_path):
                # 여러 인코딩 시도
                lines = []
                encodings_to_try = ['utf-8', 'cp949', 'euc-kr', 'latin1']

                for encoding in encodings_to_try:
                    try:
                        with open(self.monitor_log_path, 'r', encoding=encoding) as f:
                            lines = f.readlines()[-100:]  # 최근 100줄 분석
                        break  # 성공하면 중단
                    except UnicodeDecodeError:
                        continue  # 다음 인코딩 시도
                    except Exception as e:
                        results['issues'].append(f"로그 파일 읽기 중 오류 ({encoding}): {e}")
                        break

                if lines:
                    # 간단한 패턴 분석
                    error_count = sum(1 for line in lines if 'ERROR' in line or 'FAIL' in line)
                    warning_count = sum(1 for line in lines if 'WARNING' in line or 'WARN' in line)

                    results['details'].append(f"최근 로그 분석: 오류 {error_count}개, 경고 {warning_count}개")

                    if error_count > 10:
                        results['issues'].append("과도한 오류 발생 감지")
                        results['status'] = 'WARN'

                    if warning_count > 20:
                        results['issues'].append("과도한 경고 발생 감지")
                        results['status'] = 'WARN'
                else:
                    results['issues'].append("로그 파일을 읽을 수 있는 인코딩을 찾을 수 없음")
                    results['status'] = 'WARN'

            else:
                results['details'].append("로그 파일이 없어 분석 불가")

        except Exception as e:
            results['issues'].append(f"비정상 활동 감지 중 오류: {e}")
            results['status'] = 'ERROR'

        self.logger.info(f"비정상 활동 감지 완료: {results['status']}")
        return results

    def _calculate_file_hash(self, file_path):
        """파일의 SHA256 해시를 계산합니다."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _load_integrity_database(self):
        """무결성 데이터베이스를 로드합니다."""
        try:
            if os.path.exists(self.integrity_db_path):
                with open(self.integrity_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"무결성 데이터베이스 로드 실패: {e}")

        return {}

    def _save_integrity_database(self, integrity_db):
        """무결성 데이터베이스를 저장합니다."""
        try:
            # 디렉토리 생성
            os.makedirs(os.path.dirname(self.integrity_db_path), exist_ok=True)

            with open(self.integrity_db_path, 'w', encoding='utf-8') as f:
                json.dump(integrity_db, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"무결성 데이터베이스 저장 실패: {e}")

    def _summarize_audit_results(self, audit_results):
        """감사 결과를 요약합니다."""
        total_checks = len(audit_results['checks'])
        passed_checks = sum(1 for check in audit_results['checks'] if check['status'] == 'PASS')
        warning_checks = sum(1 for check in audit_results['checks'] if check['status'] == 'WARN')
        failed_checks = sum(1 for check in audit_results['checks'] if check['status'] in ['FAIL', 'ERROR'])

        summary = f"""
보안 감사 요약:
- 총 검사 항목: {total_checks}
- 통과: {passed_checks}
- 경고: {warning_checks}
- 실패: {failed_checks}
"""

        # 모든 문제 수집
        all_issues = []
        for check in audit_results['checks']:
            all_issues.extend(check.get('issues', []))

        if all_issues:
            summary += "\n감지된 문제들:\n" + "\n".join(f"- {issue}" for issue in all_issues)

        self.logger.info(summary)

        # 요약을 감사 결과에 추가
        audit_results['summary'] = {
            'total_checks': total_checks,
            'passed': passed_checks,
            'warnings': warning_checks,
            'failures': failed_checks,
            'issues': all_issues
        }

    def schedule_regular_audits(self):
        """정기적인 보안 감사를 예약합니다."""
        self.logger.info("정기 보안 감사 스케줄링 설정")

        # 실제 구현에서는 cron job이나 Windows Task Scheduler를 사용
        # 여기서는 간단한 구현만 제공

        schedule_info = """
정기 보안 감사 스케줄:
- 일일 감사: 매일 오전 2시
- 주간 감사: 매주 일요일 오전 3시
- 월간 감사: 매월 1일 오전 4시

실제 스케줄링을 위해서는 다음 중 하나를 사용하세요:
1. Windows Task Scheduler (Windows)
2. cron (Linux/Mac)
3. Python schedule 라이브러리

명령어 예시:
python license_security_monitor.py --audit
"""

        self.logger.info(schedule_info)

        # 스케줄 파일 생성
        schedule_path = os.path.join(
            os.environ.get('PROGRAMDATA', 'C:\\ProgramData'),
            'PayslipApp', 'security_schedule.txt'
        )

        try:
            with open(schedule_path, 'w', encoding='utf-8') as f:
                f.write(schedule_info)
            self.logger.info(f"스케줄 정보 파일 생성: {schedule_path}")
        except Exception as e:
            self.logger.error(f"스케줄 파일 생성 실패: {e}")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='라이선스 시스템 보안 모니터링')
    parser.add_argument('--audit', action='store_true', help='전체 보안 감사 실행')
    parser.add_argument('--schedule', action='store_true', help='정기 감사 스케줄 설정')
    parser.add_argument('--check-integrity', action='store_true', help='라이선스 무결성 검사')

    args = parser.parse_args()

    monitor = LicenseSecurityMonitor()

    if args.audit:
        print("라이선스 시스템 보안 감사를 시작합니다...")
        results = monitor.run_full_security_audit()

        print("\n=== 감사 결과 ===")
        print(f"총 검사 항목: {results['summary']['total_checks']}")
        print(f"통과: {results['summary']['passed']}")
        print(f"경고: {results['summary']['warnings']}")
        print(f"실패: {results['summary']['failures']}")

        if results['summary']['issues']:
            print("\n감지된 문제들:")
            for issue in results['summary']['issues']:
                print(f"- {issue}")

    elif args.schedule:
        print("정기 보안 감사 스케줄을 설정합니다...")
        monitor.schedule_regular_audits()
        print("스케줄 설정이 완료되었습니다.")

    elif args.check_integrity:
        print("라이선스 파일 무결성을 검사합니다...")
        integrity_result = monitor._verify_license_integrity()
        print(f"무결성 검사 결과: {integrity_result['status']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
