import base64
import datetime
import os
import socket
import struct
import time
import zipfile
import shutil
import tempfile
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
import hashlib

# 로깅 설정 import (logic.py의 SecureLogger 사용)
try:
    from logic import logging
except ImportError:
    # fallback: 기본 logging 사용
    import logging

# 다른 모듈에서 함수 임포트
try:
    from .hardware_id import get_machine_id
except ImportError:
    from hardware_id import get_machine_id


# --- 성능 최적화 캐시 ---
_license_cache = {}
_cache_expiry = {}
CACHE_DURATION = 300  # 5분 캐시
NTP_CACHE_DURATION = 600  # NTP 시간 10분 캐시
_ntp_cache = None
_ntp_cache_time = 0

# --- 상수 정의 ---
LICENSE_FILE_NAME = "license.dat"  # 파일명 변경으로 식별성 낮춤
# 시스템 영역으로 이동 (관리자 권한 필요할 수 있음)
LICENSE_DIR = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'PayslipApp', 'license')
LICENSE_FILE_PATH = os.path.join(LICENSE_DIR, LICENSE_FILE_NAME)

# 라이선스 타입 정의
class LicenseType:
    """라이선스 유형 정의"""
    TAX_ACCOUNTANT = "tax_accountant"  # 세무사 라이선스
    CUSTOMER = "customer"            # 고객 라이선스

# 라이선스 파일 경로 분리 (세무사/고객 완전 분리)
BASE_LICENSE_DIR = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'PayslipApp', 'license')
TAX_ACCOUNTANT_DIR = os.path.join(BASE_LICENSE_DIR, LicenseType.TAX_ACCOUNTANT)
CUSTOMER_DIR = os.path.join(BASE_LICENSE_DIR, LicenseType.CUSTOMER)

PUBLIC_KEY_PATH = 'license_system/public_key.pem'
ACTIVATION_WINDOW_MINUTES = 10 # 활성화 코드가 유효한 시간(분)


class LicenseManager:
    """
    세무사와 고객 라이선스를 완전히 분리하여 관리하는 클래스
    기존 단일 라이선스 시스템을 대체하는 새로운 아키텍처
    """

    @staticmethod
    def get_license_paths(license_type, hw_id=None):
        """
        라이선스 타입별 파일 경로를 반환합니다.

        :param license_type: LicenseType.TAX_ACCOUNTANT 또는 LicenseType.CUSTOMER
        :param hw_id: 고객 라이선스의 경우 HW ID (세무사 라이선스는 자동으로 현재 PC HW ID 사용)
        :return: (license_dir, license_file_path) 튜플
        """
        if license_type == LicenseType.TAX_ACCOUNTANT:
            # 세무사 라이선스: 고정 경로 사용
            license_dir = TAX_ACCOUNTANT_DIR
            license_file = os.path.join(license_dir, LICENSE_FILE_NAME)

        elif license_type == LicenseType.CUSTOMER:
            # 고객 라이선스: HW ID 기반 동적 경로
            if not hw_id:
                raise ValueError("고객 라이선스의 경우 HW_ID가 필요합니다")
            license_dir = os.path.join(CUSTOMER_DIR, hw_id)
            license_file = os.path.join(license_dir, LICENSE_FILE_NAME)

        else:
            raise ValueError(f"알 수 없는 라이선스 타입: {license_type}")

        return license_dir, license_file

    @staticmethod
    def check_license_v2(license_type, hw_id=None):
        """
        새로운 라이선스 검증 로직 (타입별 분리) - 캐시 최적화 적용

        :param license_type: 라이선스 타입
        :param hw_id: 고객 라이선스의 경우 HW ID
        :return: 'LICENSED', 'EXPIRED', 'INVALID_LICENSE', 'NOT_LICENSED' 중 하나
        """
        # 캐시 키 생성
        cache_key = f"{license_type}:{hw_id if hw_id else 'default'}"

        # 캐시 확인 (5분 이내)
        current_time = time.time()
        if cache_key in _license_cache and cache_key in _cache_expiry:
            if current_time < _cache_expiry[cache_key]:
                logging.info(f"라이선스 캐시 히트 ({license_type}): {_license_cache[cache_key]}")
                return _license_cache[cache_key]
            else:
                # 캐시 만료 - 제거
                del _license_cache[cache_key]
                del _cache_expiry[cache_key]

        logging.info(f"===== 새 라이선스 체크 시작 ({license_type}) =====")

        try:
            # 라이선스 파일 경로 획득
            license_dir, license_file = LicenseManager.get_license_paths(license_type, hw_id)

            # 라이선스 파일 존재 확인
            if not os.path.exists(license_file):
                logging.warning(f"라이선스 파일이 존재하지 않습니다: {license_file}")
                result = 'NOT_LICENSED'
                logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")
                # 캐시에 저장
                _license_cache[cache_key] = result
                _cache_expiry[cache_key] = current_time + CACHE_DURATION
                return result

            logging.info(f"라이선스 파일을 찾았습니다: {license_file}")

            # HW ID 결정 (세무사 vs 고객)
            if license_type == LicenseType.TAX_ACCOUNTANT:
                current_hw_id = get_machine_id()  # 세무사 PC의 HW ID
            elif license_type == LicenseType.CUSTOMER:
                current_hw_id = hw_id  # 파라미터로 전달된 HW ID
            else:
                current_hw_id = get_machine_id()  # fallback

            if not current_hw_id:
                logging.error("HW ID를 가져올 수 없습니다.")
                result = 'INVALID_LICENSE'
                logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")
                # 캐시에 저장
                _license_cache[cache_key] = result
                _cache_expiry[cache_key] = current_time + CACHE_DURATION
                return result

            logging.info("현재 HW_ID: [HW_ID_MASKED]")

            # 암호화 키 생성 및 파일 복호화
            encryption_key = _get_encryption_key(current_hw_id)
            f = Fernet(encryption_key)
            logging.info("암호화 키 생성 완료.")

            with open(license_file, "rb") as license_file_obj:
                encrypted_data = license_file_obj.read()

            decrypted_data = f.decrypt(encrypted_data).decode('utf-8')
            logging.info("라이선스 파일 복호화 성공.")

            # 데이터 파싱
            parts = {k: v for k, v in (item.split(':') for item in decrypted_data.split('|'))}
            stored_hw_id = parts.get('hw_id')
            expiry_date_str = parts.get('expires')
            logging.info(f"저장된 HW_ID: [HW_ID_MASKED], 저장된 만료일: {expiry_date_str}")

            # HW ID 검증 (복사 방지)
            if stored_hw_id != current_hw_id:
                logging.warning("HW_ID 불일치. 복사된 라이선스로 의심됩니다.")
                result = 'INVALID_LICENSE'
                logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")
                # 캐시에 저장
                _license_cache[cache_key] = result
                _cache_expiry[cache_key] = current_time + CACHE_DURATION
                return result

            logging.info("HW_ID 일치 확인.")

            # 시간 동기화 검증
            if not _verify_system_time():
                logging.warning("시스템 시간이 NTP 서버와 동기화되지 않음.")
                result = 'INVALID_LICENSE'
                logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")
                # 캐시에 저장
                _license_cache[cache_key] = result
                _cache_expiry[cache_key] = current_time + CACHE_DURATION
                return result

            # 만료일 검증
            expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
            current_date = datetime.date.today()

            # NTP 시간 우선 사용
            ntp_time = _get_ntp_time()
            if ntp_time:
                ntp_date = ntp_time.date()
                if ntp_date > current_date:
                    logging.warning(f"NTP 시간({ntp_date})이 시스템 시간({current_date})보다 미래임.")
                    result = 'INVALID_LICENSE'
                    logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")
                    # 캐시에 저장
                    _license_cache[cache_key] = result
                    _cache_expiry[cache_key] = current_time + CACHE_DURATION
                    return result
                current_date = ntp_date

            if current_date > expiry_date:
                logging.warning("라이선스 기간 만료.")
                result = 'EXPIRED'
                logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")
                # 캐시에 저장
                _license_cache[cache_key] = result
                _cache_expiry[cache_key] = current_time + CACHE_DURATION
                return result

            logging.info("모든 검증 통과.")
            result = 'LICENSED'
            logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")

            # 캐시에 저장
            _license_cache[cache_key] = result
            _cache_expiry[cache_key] = current_time + CACHE_DURATION

            return result

        except Exception as e:
            logging.error(f"새 라이선스 검증 중 오류 발생 ({license_type}): {e}", exc_info=True)
            result = 'INVALID_LICENSE'
            logging.info(f"===== 새 라이선스 체크 종료 ({license_type}: {result}) =====")

            # 캐시에 저장 (오류 상태도 캐시)
            _license_cache[cache_key] = result
            _cache_expiry[cache_key] = current_time + CACHE_DURATION

            return result

    @staticmethod
    def create_license_v2(expiry_date, hw_id, license_type):
        """
        새로운 라이선스 생성 로직 (타입별 분리)

        :param expiry_date: 만료일 (YYYY-MM-DD)
        :param hw_id: 하드웨어 ID
        :param license_type: 라이선스 타입
        :return: 성공 여부
        """
        logging.info(f"새 라이선스 생성 시작 ({license_type}): HW_ID={hw_id}, 만료일={expiry_date}")

        try:
            # 라이선스 파일 경로 획득
            license_dir, license_file = LicenseManager.get_license_paths(license_type, hw_id)

            # 디렉토리 생성
            os.makedirs(license_dir, exist_ok=True)
            logging.info(f"라이선스 디렉터리 확인/생성 완료: {license_dir}")

            # 암호화 키 생성 및 데이터 암호화
            encryption_key = _get_encryption_key(hw_id)
            f = Fernet(encryption_key)
            logging.info("암호화 키 생성 완료.")

            license_data = f"hw_id:{hw_id}|expires:{expiry_date}"
            logging.info(f"저장할 라이선스 데이터: {license_data}")

            encrypted_data = f.encrypt(license_data.encode('utf-8'))

            # 파일 저장
            with open(license_file, "wb") as license_file_obj:
                license_file_obj.write(encrypted_data)

            logging.info(f"새 라이선스 파일 저장 성공 ({license_type}): {license_file}")
            return True

        except Exception as e:
            logging.error(f"새 라이선스 생성 중 오류 발생 ({license_type}): {e}", exc_info=True)
            return False

    @staticmethod
    def migrate_legacy_license():
        """
        기존 라이선스 파일을 새로운 분리된 구조로 마이그레이션합니다.

        기존 파일이 있으면 세무사 라이선스로 가정하여 이전합니다.
        마이그레이션 성공 시 기존 파일을 삭제합니다.
        실패 시 안전하게 기존 시스템으로 돌아갑니다.

        :return: 마이그레이션 성공 여부
        """
        logging.info("=== 레거시 라이선스 마이그레이션 시작 ===")

        try:
            # 기존 라이선스 파일 존재 확인
            if not os.path.exists(LICENSE_FILE_PATH):
                logging.info("기존 라이선스 파일이 없음 - 마이그레이션 불필요")
                logging.info("=== 레거시 라이선스 마이그레이션 완료 (불필요) ===")
                return True

            logging.info(f"기존 라이선스 파일 발견: {LICENSE_FILE_PATH}")

            # 기존 라이선스 파일 읽기
            with open(LICENSE_FILE_PATH, "rb") as old_file:
                encrypted_data = old_file.read()

            # 현재 PC의 HW ID로 복호화 시도
            current_hw_id = get_machine_id()
            if not current_hw_id:
                logging.error("HW ID를 가져올 수 없음 - 마이그레이션 실패")
                logging.info("=== 레거시 라이선스 마이그레이션 실패 (HW ID 오류) ===")
                return False

            logging.info("현재 HW ID: [HW_ID_MASKED]")

            # 암호화 키 생성 및 복호화
            encryption_key = _get_encryption_key(current_hw_id)
            f = Fernet(encryption_key)

            try:
                decrypted_data = f.decrypt(encrypted_data).decode('utf-8')
                logging.info("기존 라이선스 파일 복호화 성공")
            except Exception as e:
                logging.error(f"기존 라이선스 파일 복호화 실패: {e}")
                logging.info("=== 레거시 라이선스 마이그레이션 실패 (복호화 오류) ===")
                return False

            # 데이터 파싱
            parts = {k: v for k, v in (item.split(':') for item in decrypted_data.split('|'))}
            stored_hw_id = parts.get('hw_id')
            expiry_date_str = parts.get('expires')

            if not expiry_date_str:
                logging.error("기존 라이선스 데이터 파싱 실패 - 만료일 정보 없음")
                logging.info("=== 레거시 라이선스 마이그레이션 실패 (데이터 파싱 오류) ===")
                return False

            logging.info(f"기존 라이선스 데이터 파싱 성공: HW_ID=[HW_ID_MASKED], 만료일={expiry_date_str}")

            # HW ID 검증 (기존 라이선스가 현재 PC의 것인지 확인)
            if stored_hw_id != current_hw_id:
                logging.warning("HW ID 불일치: 저장된=[HW_ID_MASKED], 현재=[HW_ID_MASKED]")
                logging.warning("기존 라이선스가 다른 PC에서 생성된 것으로 보임 - 마이그레이션 취소")
                logging.info("=== 레거시 라이선스 마이그레이션 취소 (HW ID 불일치) ===")
                return False

            # 새로운 세무사 라이선스 생성
            success = LicenseManager.create_license_v2(expiry_date_str, current_hw_id, LicenseType.TAX_ACCOUNTANT)

            if not success:
                logging.error("새로운 라이선스 생성 실패")
                logging.info("=== 레거시 라이선스 마이그레이션 실패 (새 라이선스 생성 오류) ===")
                return False

            # 마이그레이션 성공 - 기존 파일 백업 후 안전하게 삭제
            print("🔄 레거시 라이선스 파일 정리 시작...")

            backup_path = LICENSE_FILE_PATH + ".backup"
            backup_success = False
            delete_success = False

            # 1단계: 백업 생성 (안전성 확보)
            try:
                shutil.copy2(LICENSE_FILE_PATH, backup_path)
                logging.info(f"기존 라이선스 파일 백업 생성: {backup_path}")
                backup_success = True
                print(f"✅ 백업 파일 생성: {os.path.basename(backup_path)}")
            except Exception as e:
                logging.error(f"기존 파일 백업 실패: {e}")
                print(f"⚠️ 백업 생성 실패 (계속 진행): {e}")

            # 2단계: 새로운 라이선스 시스템 정상 동작 재확인
            verification_attempts = 0
            max_verification_attempts = 3

            while verification_attempts < max_verification_attempts:
                try:
                    # 새로운 라이선스 시스템이 정상 동작하는지 확인
                    verification_status = LicenseManager.check_license_v2(LicenseType.TAX_ACCOUNTANT)
                    if verification_status == 'LICENSED':
                        logging.info("새로운 라이선스 시스템 정상 동작 확인")
                        print("✅ 새로운 라이선스 시스템 검증 완료")
                        break
                    else:
                        logging.warning(f"라이선스 검증 실패 (시도 {verification_attempts + 1}/{max_verification_attempts}): {verification_status}")
                        verification_attempts += 1
                        time.sleep(1)  # 잠시 대기 후 재시도
                except Exception as e:
                    logging.error(f"라이선스 검증 중 오류 (시도 {verification_attempts + 1}/{max_verification_attempts}): {e}")
                    verification_attempts += 1
                    time.sleep(1)

            if verification_attempts >= max_verification_attempts:
                logging.error("새로운 라이선스 시스템 검증 실패 - 삭제 취소")
                print("❌ 새로운 라이선스 시스템 검증 실패 - 안전을 위해 기존 파일 유지")
                return False

            # 3단계: 기존 파일 삭제 (안전하게)
            try:
                # 파일이 여전히 존재하는지 확인
                if os.path.exists(LICENSE_FILE_PATH):
                    os.remove(LICENSE_FILE_PATH)
                    logging.info(f"기존 라이선스 파일 삭제 완료: {LICENSE_FILE_PATH}")
                    delete_success = True
                    print(f"✅ 기존 라이선스 파일 삭제: {os.path.basename(LICENSE_FILE_PATH)}")
                else:
                    logging.warning("삭제할 파일이 이미 존재하지 않음")
                    delete_success = True  # 파일이 이미 없으면 성공으로 간주
                    print("ℹ️ 기존 라이선스 파일이 이미 제거됨")
            except Exception as e:
                logging.error(f"기존 파일 삭제 실패: {e}")
                print(f"⚠️ 기존 파일 삭제 실패 (백업 파일 유지): {e}")

            # 4단계: 최종 검증 및 정리
            if delete_success:
                # 백업 파일 정리 (삭제 성공 시)
                try:
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        logging.info(f"백업 파일 정리 완료: {backup_path}")
                        print(f"🧹 백업 파일 정리: {os.path.basename(backup_path)}")
                except Exception as e:
                    logging.warning(f"백업 파일 정리 실패 (무시): {e}")

                # 마이그레이션 완료 로그
                migration_log_path = LICENSE_FILE_PATH + ".migration_completed"
                try:
                    with open(migration_log_path, 'w', encoding='utf-8') as log_file:
                        log_file.write(f"마이그레이션 완료: {datetime.datetime.now().isoformat()}\n")
                        log_file.write(f"원본 파일: {LICENSE_FILE_PATH}\n")
                        log_file.write(f"새 라이선스 타입: {LicenseType.TAX_ACCOUNTANT}\n")
                        log_file.write(f"HW ID: {current_hw_id}\n")
                        log_file.write(f"만료일: {expiry_date_str}\n")
                    logging.info(f"마이그레이션 완료 로그 기록: {migration_log_path}")
                except Exception as e:
                    logging.warning(f"마이그레이션 로그 기록 실패: {e}")

            logging.info("=== 레거시 라이선스 마이그레이션 성공 ===")
            print("🎉 레거시 라이선스 파일 마이그레이션 완료!")
            print("   기존 단일 라이선스 → 새로운 세무사/고객 분리 시스템")
            return True

        except Exception as e:
            logging.error(f"레거시 라이선스 마이그레이션 중 예기치 않은 오류: {e}", exc_info=True)
            logging.info("=== 레거시 라이선스 마이그레이션 실패 (예기치 않은 오류) ===")
            return False


def setup_license_permissions():
    """
    라이선스 파일 및 디렉토리에 대한 권한을 설정합니다.
    Windows 시스템에서 파일 접근을 제한하여 보안을 강화합니다.

    :return: 권한 설정 성공 여부
    """
    logging.info("라이선스 권한 설정 시작...")

    try:
        import win32security
        import win32api
        import ntsecuritycon as con

        # 현재 사용자 SID 가져오기
        current_user_sid = win32security.GetTokenInformation(
            win32security.OpenProcessToken(win32api.GetCurrentProcess(), con.TOKEN_QUERY),
            con.TokenUser
        )[0]

        # 라이선스 파일 권한 설정 함수
        def set_file_permissions(file_path):
            if not os.path.exists(file_path):
                logging.warning(f"파일이 존재하지 않아 권한 설정 건너뜀: {file_path}")
                return

            try:
                # 파일 보안 정보 가져오기
                sd = win32security.GetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION)

                # 현재 DACL 가져오기
                dacl = sd.GetSecurityDescriptorDacl()

                if dacl is None:
                    # DACL이 없으면 새로 생성
                    dacl = win32security.ACL()

                # 현재 사용자에게만 전체 권한 부여
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.GENERIC_ALL,
                    current_user_sid
                )

                # Administrators 그룹에게 읽기 권한 부여 (관리용)
                admin_sid = win32security.ConvertStringSidToSid("S-1-5-32-544")  # Administrators 그룹
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.GENERIC_READ,
                    admin_sid
                )

                # System에게 읽기 권한 부여 (시스템 프로세스용)
                system_sid = win32security.ConvertStringSidToSid("S-1-5-18")  # SYSTEM
                dacl.AddAccessAllowedAce(
                    win32security.ACL_REVISION,
                    con.GENERIC_READ,
                    system_sid
                )

                # 보안 디스크립터에 DACL 설정
                sd.SetSecurityDescriptorDacl(1, dacl, 0)
                win32security.SetFileSecurity(file_path, win32security.DACL_SECURITY_INFORMATION, sd)

                logging.info(f"파일 권한 설정 완료: {file_path}")

            except Exception as e:
                logging.warning(f"파일 권한 설정 실패: {file_path} - {e}")

        # 모든 라이선스 파일에 권한 설정 적용
        for license_type in [LicenseType.TAX_ACCOUNTANT, LicenseType.CUSTOMER]:
            try:
                license_dir, license_file = LicenseManager.get_license_paths(license_type)

                # 디렉토리가 존재하면 파일 권한 설정
                if os.path.exists(license_file):
                    set_file_permissions(license_file)
                    logging.info(f"라이선스 파일 권한 설정: {license_type}")

                # 고객 라이선스의 경우 모든 HW ID 폴더의 파일들에 권한 설정
                if license_type == LicenseType.CUSTOMER and os.path.exists(license_dir):
                    for hw_id_dir in os.listdir(license_dir):
                        hw_id_path = os.path.join(license_dir, hw_id_dir)
                        if os.path.isdir(hw_id_path):
                            license_file_path = os.path.join(hw_id_path, LICENSE_FILE_NAME)
                            if os.path.exists(license_file_path):
                                set_file_permissions(license_file_path)

            except Exception as e:
                logging.warning(f"라이선스 타입 권한 설정 실패: {license_type} - {e}")

        logging.info("라이선스 권한 설정 완료")
        return True

    except ImportError:
        logging.warning("pywin32 모듈이 없어 Windows 권한 설정을 건너뜁니다")
        return False
    except Exception as e:
        logging.error(f"라이선스 권한 설정 중 오류: {e}")
        return False


def audit_license_access():
    """
    라이선스 파일 접근을 감사하고 로깅합니다.
    비정상적인 접근 시도를 탐지하여 경고합니다.

    :return: 감사 성공 여부
    """
    logging.info("라이선스 접근 감사 시작...")

    try:
        import time

        # 감사 정보 수집
        audit_info = {
            'timestamp': time.time(),
            'process_id': os.getpid(),
            'user': os.environ.get('USERNAME', 'unknown'),
            'license_files': []
        }

        # 라이선스 파일 상태 확인
        for license_type in [LicenseType.TAX_ACCOUNTANT, LicenseType.CUSTOMER]:
            try:
                license_dir, license_file = LicenseManager.get_license_paths(license_type)

                file_info = {
                    'type': license_type,
                    'path': license_file,
                    'exists': os.path.exists(license_file)
                }

                if file_info['exists']:
                    stat = os.stat(license_file)
                    file_info.update({
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'accessed': stat.st_atime
                    })

                    # 최근 접근 시간 확인 (1시간 이내)
                    current_time = time.time()
                    if current_time - stat.st_atime < 3600:  # 1시간
                        logging.info(f"라이선스 파일 최근 접근: {license_type} - {license_file}")

                audit_info['license_files'].append(file_info)

            except Exception as e:
                logging.warning(f"라이선스 파일 감사 실패: {license_type} - {e}")

        # 감사 로그 기록
        logging.info(f"라이선스 접근 감사 완료: {len(audit_info['license_files'])}개 파일 확인")

        # 비정상적인 상황 감지
        for file_info in audit_info['license_files']:
            if file_info['exists'] and file_info.get('size', 0) == 0:
                logging.warning(f"의심스러운 빈 라이선스 파일: {file_info['path']}")

        return True

    except Exception as e:
        logging.error(f"라이선스 접근 감사 중 오류: {e}")
        return False


def _get_encryption_key(hardware_id):
    """하드웨어 ID를 기반으로 대칭키 암호화에 사용할 키를 생성합니다."""
    key = hashlib.sha256(hardware_id.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(key)

def _get_ntp_time():
    """NTP 서버에서 현재 시간을 가져옵니다. (캐시 적용)"""
    global _ntp_cache, _ntp_cache_time

    current_time = time.time()

    # 캐시 확인 (10분 이내)
    if _ntp_cache is not None and (current_time - _ntp_cache_time) < NTP_CACHE_DURATION:
        logging.info("NTP 캐시 히트")
        return _ntp_cache

    try:
        # NTP 서버 목록 (안정적인 순서대로)
        ntp_servers = [
            'time.nist.gov',
            'time.windows.com',
            'pool.ntp.org'
        ]

        for server in ntp_servers:
            try:
                # NTP 패킷 생성 (버전 3, 모드 3 - 클라이언트 모드)
                ntp_packet = b'\x1b' + 47 * b'\x00'

                # 소켓 생성 및 타임아웃 설정
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(5)

                # NTP 서버에 요청
                sock.sendto(ntp_packet, (server, 123))

                # 응답 받기
                data, _ = sock.recvfrom(1024)
                sock.close()

                # NTP 타임스탬프 추출 (1900년 1월 1일부터의 초 단위)
                ntp_timestamp = struct.unpack('!12I', data)[10]

                # Unix 타임스탬프로 변환 (NTP는 1900년 기준, Unix는 1970년 기준)
                unix_timestamp = ntp_timestamp - 2208988800

                # datetime 객체로 변환
                ntp_datetime = datetime.datetime.fromtimestamp(unix_timestamp, tz=datetime.timezone.utc)

                logging.info(f"NTP 시간 동기화 성공: {server}")

                # 캐시에 저장
                _ntp_cache = ntp_datetime
                _ntp_cache_time = current_time

                return ntp_datetime

            except (socket.timeout, socket.error) as e:
                logging.warning(f"NTP 서버 {server} 연결 실패: {e}")
                continue

        logging.error("모든 NTP 서버 연결 실패")

        # 실패 시에도 캐시에 저장 (다음 시도까지 재시도 방지)
        _ntp_cache = None
        _ntp_cache_time = current_time

        return None

    except Exception as e:
        logging.error(f"NTP 시간 가져오기 중 오류: {e}")

        # 오류 시에도 캐시 업데이트
        _ntp_cache = None
        _ntp_cache_time = current_time

        return None

def _verify_system_time():
    """시스템 시간이 NTP 서버와 동기화되었는지 확인합니다."""
    try:
        ntp_time = _get_ntp_time()
        if not ntp_time:
            return False

        system_time = datetime.datetime.now(datetime.timezone.utc)
        time_diff = abs((ntp_time - system_time).total_seconds())

        # 5분 이내 차이는 허용
        max_allowed_diff = 300  # 5분

        if time_diff > max_allowed_diff:
            logging.warning(f"시스템 시간과 NTP 시간 차이: {time_diff}초")
            return False

        return True

    except Exception as e:
        logging.error(f"시스템 시간 검증 중 오류: {e}")
        return False

def verify_activation_code(activation_code):
    """
    세무사에게 받은 활성화 코드가 유효한지 공개 키로 검증하고, 유효 시간도 확인합니다.
    :param activation_code: 사용자가 입력한 활성화 코드
    :return: (상태, 데이터) 튜플. 예: ('SUCCESS', '만료일'), ('CODE_EXPIRED', None)
    """
    logging.info("활성화 코드 검증 시작...")
    try:
        # 1. 공개 키 로드
        with open(PUBLIC_KEY_PATH, "rb") as key_file:
            public_key = serialization.load_pem_public_key(key_file.read())
        logging.info("공개 키 로드 성공.")

        # 2. 페이로드와 서명 분리
        encoded_payload, encoded_signature = activation_code.split('.')
        payload_bytes = base64.urlsafe_b64decode(encoded_payload)
        signature = base64.urlsafe_b64decode(encoded_signature)
        logging.info("페이로드 및 서명 분리 성공.")

        # 3. 서명 검증
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        logging.info("서명 검증 성공.")
        
        # 4. 페이로드에서 정보 추출
        payload = payload_bytes.decode('utf-8')
        # 수정: item.split(':') -> item.split(':', 1)
        # ISO 시간 형식에 포함된 추가 콜론(:)으로 인한 오류 방지
        parts = {k: v for k, v in (item.split(':', 1) for item in payload.split('|'))}
        generated_at_str = parts.get('generated_at')
        expiry_date_str = parts.get('expires')

        if not generated_at_str or not expiry_date_str:
            logging.error("페이로드 파싱 실패: 'generated_at' 또는 'expires' 필드 누락.")
            return 'INVALID_PAYLOAD', None
        logging.info(f"페이로드 파싱 성공: 생성시각={generated_at_str}, 만료일={expiry_date_str}")

        # 5. 활성화 코드 자체의 유효 시간 검증
        generated_at = datetime.datetime.fromisoformat(generated_at_str)
        time_limit = generated_at + datetime.timedelta(minutes=ACTIVATION_WINDOW_MINUTES)
        
        logging.info(f"코드 생성 시각: {generated_at}, 유효시간 제한: {time_limit}, 현재시각(UTC): {datetime.datetime.now(datetime.timezone.utc)}")

        if datetime.datetime.now(datetime.timezone.utc) > time_limit:
            logging.warning("활성화 코드 유효 시간 만료.")
            return 'CODE_EXPIRED', None
        
        logging.info("활성화 코드 유효 시간 검증 통과.")
        return 'SUCCESS', expiry_date_str

    except InvalidSignature:
        logging.error("활성화 코드 서명 검증 실패 (InvalidSignature).")
        return 'INVALID_SIGNATURE', None
    except FileNotFoundError:
        logging.error(f"공개 키 파일('{PUBLIC_KEY_PATH}')을 찾을 수 없음.")
        return 'PUBLIC_KEY_NOT_FOUND', None
    except Exception as e:
        logging.error(f"활성화 코드 검증 중 예상치 못한 오류 발생: {e}", exc_info=True)
        return 'UNKNOWN_ERROR', None



def create_customer_package(expiry_date, hardware_id):
    """
    라이선스 생성 완료 후 고객용 배포 패키지를 자동으로 생성합니다.
    README_PyQt6.md는 제외하고 압축 파일명에 만료일을 포함합니다.
    압축 파일은 실행 파일과 같은 위치에 생성됩니다.
    같은 만료일의 압축 파일이 이미 존재하면 새로 생성하지 않습니다.
    """
    logging.info("고객용 배포 패키지 생성 시작...")

    try:
        # 실행 파일의 디렉토리 경로
        import sys
        if getattr(sys, 'frozen', False):
            # PyInstaller로 빌드된 경우
            exe_dir = os.path.dirname(sys.executable)
        else:
            # 개발 중인 경우 현재 작업 디렉토리
            exe_dir = os.getcwd()

        logging.info(f"압축 파일 생성 위치: {exe_dir}")

        # 같은 만료일의 압축 파일이 이미 존재하는지 확인
        expiry_formatted = expiry_date.replace('-', '')  # YYYYMMDD 형식으로
        existing_zips = [f for f in os.listdir(exe_dir) if f.startswith('고객용_패키지_') and f'만료{expiry_date}' in f]

        if existing_zips:
            existing_zip_path = os.path.join(exe_dir, existing_zips[0])
            logging.info(f"이미 존재하는 압축 파일 발견: {existing_zips[0]}")
            print(f"ℹ️ 동일한 만료일의 압축 파일이 이미 존재합니다: {existing_zips[0]}")
            return existing_zip_path

        # 현재 날짜로 패키지명 생성
        current_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"고객용_패키지_{current_date}_만료{expiry_date}"

        # PyInstaller 임시 디렉토리와 충돌하지 않도록 exe_dir 하위에 임시 폴더 생성
        temp_base = os.path.join(exe_dir, 'temp_packages')
        os.makedirs(temp_base, exist_ok=True)

        # 임시 디렉토리 생성 (충돌 방지)
        with tempfile.TemporaryDirectory(dir=temp_base) as temp_dir:
            package_dir = os.path.join(temp_dir, package_name)
            os.makedirs(package_dir, exist_ok=True)

            # 현재 폴더에서 exe 파일 찾기
            exe_files = [f for f in os.listdir(exe_dir) if f.endswith('.exe') and '급여명세서관리' in f]
            if exe_files:
                exe_filename = exe_files[0]  # 첫 번째 exe 파일 사용
                # license_system 폴더의 경로 찾기 (배포판 내에서)
                license_system_dir = os.path.join(exe_dir, 'license_system')
                logging.info(f"license_system_dir 경로: {license_system_dir}")
                logging.info(f"license_system 폴더 존재: {os.path.exists(license_system_dir)}")

                # 배포판 내 license_system이 없으면 프로젝트 루트에서 찾기 (개발용)
                if not os.path.exists(license_system_dir):
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    license_system_dir = os.path.join(project_root, 'license_system')
                    logging.info(f"프로젝트 루트 license_system_dir 경로: {license_system_dir}")
                    logging.info(f"프로젝트 루트 license_system 폴더 존재: {os.path.exists(license_system_dir)}")

                customer_files = [
                    (os.path.join(exe_dir, exe_filename), exe_filename),  # exe 파일 (현재 폴더에서)
                    (os.path.join(license_system_dir, 'public_key.pem'), 'license_system/public_key.pem'),  # 공개 키
                    (os.path.join(license_system_dir, '__init__.py'), 'license_system/__init__.py'),  # 라이선스 시스템 모듈
                    (os.path.join(license_system_dir, 'hardware_id.py'), 'license_system/hardware_id.py'),  # HW ID 모듈
                    (os.path.join(license_system_dir, 'license_verifier.py'), 'license_system/license_verifier.py'),  # 검증 모듈
                    (os.path.join(exe_dir, 'config.json'), 'config.json'),
                    (os.path.join(exe_dir, 'employees.json'), 'employees.json'),
                    (os.path.join(exe_dir, 'tutorial_data.xlsx'), 'tutorial_data.xlsx'),
                    (os.path.join(exe_dir, '급여명세서.xlsx'), '급여명세서.xlsx'),  # 급여명세서 템플릿 파일 추가
                    (os.path.join(exe_dir, 'payslip_template.html'), 'payslip_template.html'),
                    # ('README_PyQt6.md', 'README.md'),  # 제외됨
                ]
                logging.info(f"exe 파일 찾음: {exe_filename}")
            else:
                # exe 파일이 없으면 기본 파일들만 포함
                customer_files = [
                    ('license_system/public_key.pem', 'public_key.pem'),  # 공개 키만
                    ('config.json', 'config.json'),
                    ('employees.json', 'employees.json'),
                    ('tutorial_data.xlsx', 'tutorial_data.xlsx'),
                    ('payslip_template.html', 'payslip_template.html'),
                    # ('README_PyQt6.md', 'README.md'),  # 제외됨
                ]
                logging.warning("exe 파일을 찾을 수 없음")

            # 가장 최근에 생성된 라이선스 활성화 HTML 파일 찾기 (실행 파일 폴더에서)
            html_files = [f for f in os.listdir(exe_dir) if f.startswith('라이선스_활성화_코드_') and f.endswith('.html')]
            if html_files:
                # 가장 최근 파일 선택 (파일명에 날짜가 포함되어 있으므로 정렬)
                html_files.sort(reverse=True)
                latest_html = html_files[0]
                customer_files.append((os.path.join(exe_dir, latest_html), latest_html))
                logging.info(f"라이선스 HTML 파일 포함: {latest_html}")

            copied_files = []
            for src_path, dst_name in customer_files:
                logging.info(f"파일 복사 시도: src_path={src_path}, dst_name={dst_name}, is_abs={os.path.isabs(src_path)}, exists={os.path.exists(src_path) if os.path.isabs(src_path) else 'N/A'}")

                # src_path가 이미 절대 경로인 경우
                if os.path.isabs(src_path) and os.path.exists(src_path):
                    dst_path = os.path.join(package_dir, dst_name)
                    # 대상 폴더가 없으면 생성
                    dst_dir = os.path.dirname(dst_path)
                    if dst_dir and not os.path.exists(dst_dir):
                        os.makedirs(dst_dir, exist_ok=True)
                        logging.info(f"대상 폴더 생성: {dst_dir}")
                    shutil.copy2(src_path, dst_path)
                    copied_files.append(dst_name)
                    logging.info(f"파일 복사 성공: {src_path} -> {dst_name}")
                # 상대 경로인 경우 exe_dir 기준으로 찾기
                elif not os.path.isabs(src_path):
                    src_full_path = os.path.join(exe_dir, src_path)
                    logging.info(f"상대 경로 변환: {src_path} -> {src_full_path}, exists={os.path.exists(src_full_path)}")
                    if os.path.exists(src_full_path):
                        dst_path = os.path.join(package_dir, dst_name)
                        shutil.copy2(src_full_path, dst_path)
                        copied_files.append(dst_name)
                        logging.info(f"파일 복사 성공: {src_full_path} -> {dst_name}")
                    else:
                        logging.warning(f"파일을 찾을 수 없음: {src_full_path}")
                else:
                    logging.error(f"파일 복사 실패: 절대 경로이지만 파일이 존재하지 않음: {src_path}")

            # 라이선스 파일은 포함하지 않음 (고객이 직접 활성화해야 함)
            # 세무사의 라이선스 파일을 고객용 패키지에 포함하면 안됨
            logging.info("라이선스 파일은 고객용 패키지에 포함하지 않습니다 (고객이 직접 활성화)")

            # 설치 가이드 생성
            create_installation_guide(package_dir, expiry_date, hardware_id)

            # ZIP 파일 생성
            zip_filename = f"{package_name}.zip"
            zip_path = os.path.join(exe_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(package_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)

            logging.info(f"고객용 패키지 생성 완료: {zip_path}")
            print(f"\n🎉 고객용 배포 패키지가 생성되었습니다!")
            print(f"📦 파일명: {zip_filename}")
            print(f"📁 포함 파일들: {', '.join(copied_files)}")
            print(f"📅 라이선스 만료일: {expiry_date}")
            print(f"\n💡 이 ZIP 파일을 고객에게 전달하세요.")
            print(f"   저장 위치: {zip_path}")

            return zip_path

    except Exception as e:
        logging.error(f"고객용 패키지 생성 중 오류 발생: {e}")
        print(f"❌ 고객용 패키지 생성 실패: {e}")
        return None

def create_installation_guide(package_dir, expiry_date, hardware_id):
    """고객용 패키지에 설치 가이드를 생성합니다."""
    guide_content = f"""급여명세서 생성기 - 고객용 설치 가이드

📦 설치 파일: 급여명세서관리.exe
📅 라이선스 만료일: {expiry_date}
🖥️ 하드웨어 ID: {hardware_id[:16]}... (일부만 표시)

=== 설치 방법 ===
1. 이 ZIP 파일의 모든 내용을 원하는 폴더에 압축 해제하세요.
2. 급여명세서관리.exe 파일을 실행하세요.
3. 튜토리얼에 따라 사용법을 익히세요.

=== 포함 파일들 ===
- 급여명세서관리.exe: 메인 프로그램
- license_system/: 라이선스 검증 시스템
- config.json: 프로그램 설정
- employees.json: 직원 데이터 템플릿
- tutorial_data.xlsx: 튜토리얼용 샘플 데이터
- payslip_template.html: 급여명세서 템플릿
- 설치_및_사용_가이드.txt: 이 파일

=== 라이선스 활성화 방법 ===
1. 프로그램을 실행하면 라이선스 안내 대화상자가 표시됩니다
2. 세무사에게 연락하여 라이선스 활성화 코드를 받아주세요
3. 메뉴 [설정] → [라이선스 활성화]를 선택하세요
4. 받은 활성화 코드를 입력하면 라이선스가 활성화됩니다

=== 주의사항 ===
- 이 패키지는 귀하의 컴퓨터에 맞춤 생성되었습니다
- 라이선스 만료일: {expiry_date}
- 라이선스 파일은 포함되어 있지 않습니다 (직접 활성화 필요)

=== 기술 지원 ===
문제가 발생하면 세무사에게 문의하세요.

---
생성일: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    guide_path = os.path.join(package_dir, "설치_및_사용_가이드.txt")
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)


def check_license():
    """
    호환성 레이어: 기존 코드와의 호환성을 유지하기 위해 세무사와 고객 라이선스를 순차적으로 확인합니다.

    1. 먼저 세무사 라이선스(TAX_ACCOUNTANT)를 확인
    2. 세무사 라이선스가 없으면 고객 라이선스(CUSTOMER)를 확인
    3. 둘 다 없으면 NOT_LICENSED 반환

    :return: 'LICENSED', 'EXPIRED', 'INVALID_LICENSE', 'NOT_LICENSED' 중 하나
    """
    logging.info("===== 라이선스 체크 시작 (호환성 모드) =====")

    # 1. 세무사 라이선스 우선 확인
    tax_accountant_status = LicenseManager.check_license_v2(LicenseType.TAX_ACCOUNTANT)
    if tax_accountant_status == 'LICENSED':
        logging.info("세무사 라이선스 확인됨 - 라이선스 유효")
        logging.info("===== 라이선스 체크 종료 (결과: LICENSED) =====")
        return 'LICENSED'
    elif tax_accountant_status in ['EXPIRED', 'INVALID_LICENSE']:
        logging.info(f"세무사 라이선스 상태: {tax_accountant_status}")
        logging.info("===== 라이선스 체크 종료 =====")
        return tax_accountant_status

    # 2. 세무사 라이선스가 없으면 고객 라이선스 확인
    logging.info("세무사 라이선스가 없음 - 고객 라이선스 확인 시도")
    hw_id = get_machine_id()
    if not hw_id:
        logging.error("HW ID를 가져올 수 없음")
        logging.info("===== 라이선스 체크 종료 (결과: INVALID_LICENSE) =====")
        return 'INVALID_LICENSE'

    customer_status = LicenseManager.check_license_v2(LicenseType.CUSTOMER, hw_id)
    logging.info(f"고객 라이선스 상태: {customer_status}")
    logging.info("===== 라이선스 체크 종료 =====")
    return customer_status
