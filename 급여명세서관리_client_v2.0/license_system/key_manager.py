import argparse
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

# --- 개인 키 생성 로직 ---
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096, # 키 사이즈를 4096으로 강화
)

# --- 공개 키 생성 로직 ---
public_key = private_key.public_key()
pem_public_key = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# --- 암호를 인자로 받아 개인 키 암호화 ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="암호화된 개인 키와 공개 키 쌍을 생성합니다.")
    parser.add_argument(
        "password",
        type=str,
        help="개인 키를 암호화할 마스터 암호를 입력하세요."
    )
    args = parser.parse_args()

    password = args.password

    if not password:
        print("오류: 암호는 비워둘 수 없습니다. 키 생성을 중단합니다.")
        exit()

    # 개인 키 파일이 이미 존재하면 경고하고 덮어쓸지 묻기
    private_key_path = 'license_system/private_key.pem'
    public_key_path = 'license_system/public_key.pem'

    if os.path.exists(private_key_path) or os.path.exists(public_key_path):
        print(f"경고: 기존 키 파일({private_key_path}, {public_key_path})이 존재합니다.")
        response = input("덮어쓰시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("키 생성을 취소합니다.")
            exit()

    try:
        pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
        )

        # --- 파일 저장 ---
        with open(private_key_path, 'wb') as f:
            f.write(pem_private_key)

        with open(public_key_path, 'wb') as f:
            f.write(pem_public_key)

        print("\n개인 키(암호화됨)와 공개 키가 'license_system' 디렉터리에 성공적으로 생성되었습니다.")
        print(" - private_key.pem: 설정하신 암호로 암호화되었습니다. 안전하게 보관하세요.")
        print(" - public_key.pem: 고객용 프로그램에 포함될 공개 키입니다.")

    except Exception as e:
        print(f"키 생성 중 오류가 발생했습니다: {e}")
