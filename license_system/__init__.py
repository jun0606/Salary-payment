"""
라이선스 시스템 패키지
PyQt6 마이그레이션된 급여명세서 생성기의 라이선스 관리 모듈
"""

# 패키지 버전
__version__ = "2.1.0"

# 주요 모듈 import (편의를 위해)
from . import license_verifier
from . import license_generator
from . import hardware_id
from . import key_manager

__all__ = [
    'license_verifier',
    'license_generator',
    'hardware_id',
    'key_manager'
]
