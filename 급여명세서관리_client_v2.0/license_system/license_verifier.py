import base64
import datetime
import os
import logging
import socket
import struct
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet
import hashlib

# 다른 모듈에서 함수 임포트
try:
    from .hardware_id import get_machine_id
except ImportError:
    from hardware_id import get_machine_id


# --- 상수 정의 ---
LICENSE_FILE_NAME = "license.dat"  # 파일명 변경으로 식별성 낮춤
# 시스템 영역으로 이동 (관리자 권한 필요할 수 있음)
LICENSE_DIR = os.path.join(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'), 'PayslipApp', 'license')
LICENSE_FILE_PATH = os.path.join(LICENSE_DIR, LICENSE_FILE_NAME)
PUBLIC_KEY_PATH = 'license_system/public_key.pem'
ACTIVATION_WINDOW_MINUTES = 5 # 활성화 코드가 유효한 시간(분)


def _get_encryption_key(hardware_id):
    """하드웨어 ID를 기반으로 대칭키 암호화에 사용할 키를 생성합니다."""
    key = hashlib.sha256(hardware_id.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(key)

def _get_ntp_time():
    """NTP 서버에서 현재 시간을 가져옵니다."""
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
                return ntp_datetime

            except (socket.timeout, socket.error) as e:
                logging.warning(f"NTP 서버 {server} 연결 실패: {e}")
                continue

        logging.error("모든 NTP 서버 연결 실패")
        return None

    except Exception as e:
        logging.error(f"NTP 시간 가져오기 중 오류: {e}")
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

def create_license_file(expiry_date, hardware_id):
    """
    검증 성공 후, 하드웨어 ID와 만료일을 암호화하여 라이선스 파일에 저장합니다.
    """
    logging.info(f"라이선스 파일 생성을 시작합니다. 경로: {LICENSE_FILE_PATH}")
    try:
        os.makedirs(LICENSE_DIR, exist_ok=True)
        logging.info(f"라이선스 디렉터리 확인/생성 완료: {LICENSE_DIR}")
        
        encryption_key = _get_encryption_key(hardware_id)
        f = Fernet(encryption_key)
        logging.info("암호화 키 생성 완료.")

        license_data = f"hw_id:{hardware_id}|expires:{expiry_date}"
        logging.info(f"저장할 라이선스 데이터: {license_data}")
        
        encrypted_data = f.encrypt(license_data.encode('utf-8'))
        
        with open(LICENSE_FILE_PATH, "wb") as license_file:
            license_file.write(encrypted_data)
        
        logging.info(f"라이선스 파일 저장 성공: {LICENSE_FILE_PATH}")
        return True
    except Exception as e:
        logging.error(f"라이선스 파일 생성 중 치명적 오류 발생: {e}", exc_info=True)
        return False


def check_license():
    """
    프로그램 시작 시 라이선스의 유효성을 검증합니다.
    :return: 'LICENSED', 'EXPIRED', 'INVALID_LICENSE', 'NOT_LICENSED' 중 하나
    """
    logging.info("===== 라이선스 체크 시작 =====")
    if not os.path.exists(LICENSE_FILE_PATH):
        logging.warning(f"라이선스 파일이 존재하지 않습니다: {LICENSE_FILE_PATH}")
        logging.info("===== 라이선스 체크 종료 (결과: NOT_LICENSED) =====")
        return 'NOT_LICENSED'
    
    logging.info(f"라이선스 파일을 찾았습니다: {LICENSE_FILE_PATH}")

    current_hw_id = get_machine_id()
    if not current_hw_id:
        logging.error("현재 컴퓨터의 하드웨어 ID를 가져올 수 없습니다.")
        logging.info("===== 라이선스 체크 종료 (결과: INVALID_LICENSE) =====")
        return 'INVALID_LICENSE'
    logging.info(f"현재 HW_ID: {current_hw_id}")

    try:
        encryption_key = _get_encryption_key(current_hw_id)
        f = Fernet(encryption_key)
        logging.info("현재 HW_ID 기반 암호화 키 생성 완료.")

        with open(LICENSE_FILE_PATH, "rb") as license_file:
            encrypted_data = license_file.read()
        
        decrypted_data = f.decrypt(encrypted_data).decode('utf-8')
        logging.info("라이선스 파일 복호화 성공.")

        parts = {k: v for k, v in (item.split(':') for item in decrypted_data.split('|'))}
        stored_hw_id = parts.get('hw_id')
        expiry_date_str = parts.get('expires')
        logging.info(f"저장된 HW_ID: {stored_hw_id}, 저장된 만료일: {expiry_date_str}")

        if stored_hw_id != current_hw_id:
            logging.warning("HW_ID 불일치. 복사된 라이선스로 의심됩니다.")
            logging.info("===== 라이선스 체크 종료 (결과: INVALID_LICENSE) =====")
            return 'INVALID_LICENSE'
        logging.info("HW_ID 일치 확인.")

        # 시간 동기화 검증 (NTP 서버와 비교)
        if not _verify_system_time():
            logging.warning("시스템 시간이 NTP 서버와 동기화되지 않음. 라이선스 검증 거부.")
            logging.info("===== 라이선스 체크 종료 (결과: INVALID_LICENSE) =====")
            return 'INVALID_LICENSE'

        expiry_date = datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        current_date = datetime.date.today()

        # NTP 시간으로 검증 (시스템 시간 조작 방지)
        ntp_time = _get_ntp_time()
        if ntp_time:
            ntp_date = ntp_time.date()
            if ntp_date > current_date:
                logging.warning(f"NTP 시간({ntp_date})이 시스템 시간({current_date})보다 미래임. 시간 조작 의심.")
                logging.info("===== 라이선스 체크 종료 (결과: INVALID_LICENSE) =====")
                return 'INVALID_LICENSE'
            current_date = ntp_date

        if current_date > expiry_date:
            logging.warning("라이선스 기간 만료.")
            logging.info("===== 라이선스 체크 종료 (결과: EXPIRED) =====")
            return 'EXPIRED'
        logging.info("라이선스 기간 유효 확인.")
        
        logging.info("모든 검증 통과.")
        logging.info("===== 라이선스 체크 종료 (결과: LICENSED) =====")
        return 'LICENSED'

    except Exception as e:
        logging.error(f"라이선스 검증 중 오류 발생 (파일 손상 또는 HW_ID 불일치로 인한 복호화 실패 가능성): {e}", exc_info=True)
        logging.info("===== 라이선스 체크 종료 (결과: INVALID_LICENSE) =====")
        return 'INVALID_LICENSE'
