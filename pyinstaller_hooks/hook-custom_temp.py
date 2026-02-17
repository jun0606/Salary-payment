"""
PyInstaller Hook: Custom Temporary Directory Setup

PyInstaller 빌드 시 TMP 환경변수를 변경하여 임시 디렉토리 경고 문제를 근본적으로 해결합니다.
"""

import os
import sys
from PyInstaller.utils.hooks import logger

def pre_safe_import_module(api):
    """
    PyInstaller 분석 단계 전에 TMP 환경변수 설정

    이 함수는 PyInstaller가 모듈을 분석하기 전에 호출되며,
    TMP 환경변수를 프로그램 전용 임시 디렉토리로 변경합니다.
    """
    try:
        # 프로그램 전용 임시 디렉토리 생성
        custom_temp = os.path.join(
            os.environ.get('LOCALAPPDATA', 'C:\\Temp'),
            'PaySlipApp_Temp'
        )

        # 디렉토리 생성 (존재하지 않으면)
        os.makedirs(custom_temp, exist_ok=True)

        # 환경변수 변경
        os.environ['TMP'] = custom_temp
        os.environ['TEMP'] = custom_temp

        # Hook 설정 플래그 (런타임 충돌 방지)
        os.environ['PYINSTALLER_HOOK_TMP_SET'] = '1'

        logger.info(f"PyInstaller Hook: TMP 환경변수 설정됨 - {custom_temp}")

        # Python tempfile 모듈의 기본 디렉토리도 변경
        import tempfile
        tempfile.tempdir = custom_temp

        print(f"PyInstaller Hook: 임시 디렉토리 설정 완료 - {custom_temp}")

    except Exception as e:
        logger.warning(f"PyInstaller Hook: TMP 설정 실패 - {e}")
        print(f"PyInstaller Hook: TMP 설정 실패 - {e}")

def pre_find_module_path(api):
    """
    모듈 경로 찾기 전에 추가 환경 설정

    안전하게 한 번 더 TMP 환경변수를 확인하고 설정합니다.
    """
    try:
        custom_temp = os.path.join(
            os.environ.get('LOCALAPPDATA', 'C:\\Temp'),
            'PaySlipApp_Temp'
        )

        # 환경변수가 올바르게 설정되어 있는지 확인
        current_tmp = os.environ.get('TMP', '')
        if not current_tmp or 'PaySlipApp_Temp' not in current_tmp:
            os.makedirs(custom_temp, exist_ok=True)
            os.environ['TMP'] = custom_temp
            os.environ['TEMP'] = custom_temp
            print(f"PyInstaller Hook: TMP 재설정 완료 - {custom_temp}")

    except Exception as e:
        print(f"PyInstaller Hook: 경로 설정 실패 - {e}")

# Hook 정보 출력
print("PyInstaller Custom Temp Hook 로드됨")
