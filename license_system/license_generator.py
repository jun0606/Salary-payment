import argparse
import datetime
import base64
import getpass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

def generate_activation_code(expiry_date_str: str, minutes_active: int, password: str, private_key_path='license_system/private_key.pem'):
    """
    지정된 만료일과 코드 생성 시각을 개인 키로 서명하여 활성화 코드를 생성합니다.
    :param expiry_date_str: 라이선스 만료일 (YYYY-MM-DD 형식)
    :param minutes_active: 활성화 코드가 유효할 시간 (분)
    :param password: 개인 키를 복호화하기 위한 암호
    :param private_key_path: 개인 키 파일 경로
    :return: 생성된 활성화 코드 문자열, 실패 시 None
    """
    if not password:
        print("오류: 개인 키 암호가 필요합니다.")
        return None

    try:
        datetime.datetime.strptime(expiry_date_str, "%Y-%m-%d")

        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=password.encode('utf-8'),
            )

        generated_at = datetime.datetime.now(datetime.timezone.utc)
        payload = f"generated_at:{generated_at.isoformat()}|expires:{expiry_date_str}"
        payload_bytes = payload.encode('utf-8')

        signature = private_key.sign(
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        encoded_payload = base64.urlsafe_b64encode(payload_bytes).decode('utf-8')
        encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8')
        
        activation_code = f"{encoded_payload}.{encoded_signature}"
        
        return activation_code

    except FileNotFoundError:
        print(f"오류: 개인 키 파일('{private_key_path}')을 찾을 수 없습니다.")
        return None
    except (ValueError, TypeError):
        # ValueError는 날짜 파싱 실패 또는 암호가 틀렸을 때 발생할 수 있음
        print("오류: 개인 키 암호가 틀렸거나 날짜 형식이 올바르지 않습니다.")
        return None
    except Exception as e:
        print(f"활성화 코드 생성 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="라이선스 활성화 코드를 생성합니다.")
    parser.add_argument(
        "expiry_date", 
        type=str, 
        help="라이선스 만료일을 YYYY-MM-DD 형식으로 입력하세요. (예: 2025-12-31)"
    )
    parser.add_argument(
        "--minutes", 
        type=int,
        default=5,
        help="활성화 코드가 유효한 시간(분)을 설정합니다. 기본값은 10분입니다."
    )
    args = parser.parse_args()

    password = getpass.getpass("개인 키 암호를 입력하세요: ")

    print(f"만료일 '{args.expiry_date}' 까지 유효한 라이선스를 생성합니다...")
    print(f"활성화 코드는 생성 후 {args.minutes}분 동안 유효합니다.")
    
    code = generate_activation_code(args.expiry_date, args.minutes, password)

    if code:
        print("\n========================================================")
        print(f"라이선스 만료일: {args.expiry_date}")
        print("생성된 활성화 코드 (이 코드를 고객에게 전달하세요):")
        print(code)
        print("========================================================")
