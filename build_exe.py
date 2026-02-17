#!/usr/bin/env python3
"""
PyInstaller를 사용한 급여명세서 생성기 exe 빌드 스크립트
세무사용 버전과 고객용 버전을 구분하여 빌드
"""

import PyInstaller.__main__
import os
import shutil
import sys
from pathlib import Path

def build_exe():
    """
    세무사용 버전 exe 파일 빌드
    세무사가 활성화코드 생성 및 고객용 패키지 압축을 위한 버전
    """
    version_type = "tax"  # 세무사용 버전 고정
    print("=== 급여명세서 생성기 세무사용 버전 빌드 시작 ===")

    # 프로젝트 루트 디렉토리
    root_dir = Path(__file__).parent

    # 아이콘 생성/확인 (macOS에서는 기본 아이콘 사용)
    icon_path = root_dir / "icon.ico"
    if not icon_path.exists():
        print("아이콘 파일이 없어 생성합니다...")
        try:
            # 아이콘 생성 스크립트 실행
            import subprocess
            result = subprocess.run([sys.executable, "create_icon.py"],
                                  cwd=root_dir, capture_output=True, text=True)
            if result.returncode == 0:
                print("아이콘 생성 성공")
            else:
                print(f"아이콘 생성 실패: {result.stderr}")
        except Exception as e:
            print(f"아이콘 생성 중 오류: {e}")

    # 출력 디렉토리
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"

    # 기존 빌드 파일 및 캐시 완전 정리 (강력한 정리)
    print("기존 빌드 파일 및 캐시 정리 중...")
    try:
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
    except Exception as e:
        print(f"dist 디렉토리 정리 실패 (무시): {e}")
    
    try:
        if build_dir.exists():
            shutil.rmtree(build_dir)
    except Exception as e:
        print(f"build 디렉토리 정리 실패 (무시): {e}")

    # 기존 spec 파일 삭제 (캐시 문제 해결)
    spec_files = list(root_dir.glob("*.spec"))
    for spec_file in spec_files:
        try:
            spec_file.unlink()
            print(f"기존 spec 파일 삭제: {spec_file.name}")
        except Exception as e:
            print(f"spec 파일 삭제 실패: {e}")

    # PyInstaller 캐시 디렉토리 정리 (선택적)
    try:
        import tempfile
        pyinstaller_cache = Path(tempfile.gettempdir()) / "pyinstaller"
        if pyinstaller_cache.exists():
            shutil.rmtree(pyinstaller_cache)
            print("PyInstaller 캐시 정리 완료")
    except Exception as e:
        print(f"캐시 정리 실패 (무시): {e}")

    # 세무사용 버전 데이터 파일 (세무사 설정 기능 포함 + Qt 플랫폼 플러그인)
    # JSON 파일은 빌드 시 제외 (런타임에서 자동 생성)
    data_files = [
        ('tutorial_data.xlsx', '.'),
        ('payslip_template.html', '.'),
        ('tax_settings_qt.py', '.'),
        ('license_system', 'license_system')
    ]

    # PyQt6 플랫폼 플러그인 포함 (Qt 플랫폼 플러그인 문제 해결)
    try:
        import PyQt6
        pyqt6_base = os.path.dirname(PyQt6.__file__)
        qt_platform_path = os.path.join(pyqt6_base, 'Qt6', 'plugins', 'platforms')
        if os.path.exists(qt_platform_path):
            data_files.append((qt_platform_path, 'PyQt6/Qt6/plugins/platforms'))
            print(f"Qt 플랫폼 플러그인 포함: {qt_platform_path}")
    except Exception as e:
        print(f"Qt 플랫폼 플러그인 검색 실패 (무시): {e}")

    # PyInstaller 기본 옵션 (임시 디렉토리 문제 해결)
    options = [
        '--onefile',                    # 단일 exe 파일 생성
        '--windowed',                   # 콘솔 창 숨김 (GUI 앱)
        '--clean',                      # 캐시 및 임시 파일 정리 (빌드 시에만 적용)
        '--noconfirm',                  # 확인 없이 덮어쓰기
        f'--distpath={dist_dir}',       # 출력 디렉토리
        f'--workpath={build_dir}',      # 작업 디렉토리
        '--name=급여명세서관리',  # exe 파일명
        f'--icon={icon_path}',          # 아이콘 적용
        # Custom Hook 적용 (jaraco.text 문제 해결)
        '--additional-hooks-dir=pyinstaller_hooks',
    ]

    # 불필요한 라이브러리 제외 (경량화 + jaraco.text 문제 해결)
    excluded_modules = [
        'torch',           # 머신러닝 프레임워크
        'tensorflow',      # 머신러닝 프레임워크
        'bitsandbytes',    # CUDA 최적화
        'librosa',         # 오디오 처리
        'cv2',             # OpenCV 이미지 처리
        'matplotlib',      # 그래프 라이브러리
        'scipy.sparse',    # 희소 행렬 (사용하지 않음)
        'scipy.optimize',  # 최적화 (사용하지 않음)
        'scipy.stats',     # 통계 (기본 계산만 사용)
        'PIL.JpegImagePlugin',  # JPEG 처리 (사용하지 않음)
        'PIL.PngImagePlugin',   # PNG 처리 (사용하지 않음)
        'PIL.BmpImagePlugin',   # BMP 처리 (사용하지 않음)
        'PIL.TiffImagePlugin',  # TIFF 처리 (사용하지 않음)
        # jaraco.text 문제 해결
        'pkg_resources',   # 패키지 메타데이터 (사용하지 않음)
    ]

    # 제외 모듈 추가
    for module in excluded_modules:
        options.extend(['--exclude-module', module])

    # 데이터 파일 추가 (macOS에서는 콜론 사용)
    for src, dst in data_files:
        src_path = root_dir / src
        if src_path.exists():
            if src_path.is_file():
                options.extend(['--add-data', f'{src_path}:{dst}'])
            elif src_path.is_dir():
                options.extend(['--add-data', f'{src_path}:{dst}'])
            print(f"데이터 파일 추가: {src} -> {dst}")
        else:
            print(f"경고: 데이터 파일이 존재하지 않음: {src}")

    # 숨겨진 import 추가 (라이선스 시스템 + jaraco.text + cryptography 문제 해결)
    options.extend([
        '--hidden-import=cryptography.fernet',
        '--hidden-import=cryptography.hazmat',
        '--hidden-import=cryptography.hazmat.primitives',
        '--hidden-import=cryptography.hazmat.primitives.asymmetric',
        '--hidden-import=cryptography.hazmat.primitives.asymmetric.rsa',
        '--hidden-import=cryptography.hazmat.primitives.asymmetric.padding',
        '--hidden-import=cryptography.hazmat.primitives.hashes',
        '--hidden-import=cryptography.hazmat.primitives.serialization',
        '--hidden-import=cryptography.hazmat.backends',
        '--hidden-import=cryptography.hazmat.backends.default',
        '--hidden-import=holidays',
        # jaraco.text 모듈 관련 문제 해결
        '--hidden-import=jaraco.text',
        '--hidden-import=jaraco.functools',
        '--hidden-import=jaraco.context',
        '--hidden-import=setuptools._vendor.jaraco.text',
        '--hidden-import=setuptools._vendor.jaraco.functools',
        '--hidden-import=setuptools._vendor.jaraco.context',
    ])

    # jaraco.text는 hook에서 처리하므로 별도 데이터 파일 추가 불필요
    print("jaraco.text 파일은 hook에서 자동 생성됨")

    # 메인 파일 추가
    main_file = root_dir / 'main_qt.py'
    options.append(str(main_file))

    print("PyInstaller 옵션들:")
    for opt in options:
        print(f"  {opt}")

    # PyInstaller 실행
    try:
        PyInstaller.__main__.run(options)
        print("✅ 빌드 완료!")

        # 빌드 결과 확인
        exe_files = list(dist_dir.glob("*.exe"))
        if exe_files:
            exe_file = exe_files[0]
            file_size = exe_file.stat().st_size / (1024 * 1024)  # MB 단위
            print(f"파일 크기: {file_size:.2f} MB")

            # 배포판 구조 생성
            create_distribution_package(dist_dir, version_type)

        return True

    except Exception as e:
        print(f"❌ 빌드 실패: {e}")
        return False

def create_distribution_package(dist_dir, version_type):
    """배포판 패키지 생성"""
    print("\n=== 배포판 패키지 생성 ===")

    package_name = f"급여명세서관리_{version_type}_v2.2"
    package_dir = dist_dir.parent / package_name

    if package_dir.exists():
        shutil.rmtree(package_dir)

    package_dir.mkdir()

    # exe 파일 복사
    exe_files = list(dist_dir.glob("*.exe"))
    if exe_files:
        shutil.copy2(exe_files[0], package_dir)

    # 추가 파일들 복사 (README_PyQt6.md 제외)
    additional_files = [
        'tutorial_data.xlsx',
        'payslip_template.html',
        'config.json',
        'employees.json',
        'requirements.txt'
    ]

    for file in additional_files:
        src = dist_dir.parent / file
        if src.exists():
            shutil.copy2(src, package_dir)

    # license_system 디렉토리 복사
    license_src = dist_dir.parent / 'license_system'
    if license_src.exists():
        shutil.copytree(license_src, package_dir / 'license_system')

    # 사용자 설치 가이드 생성
    create_user_guide(package_dir, version_type)

    print(f"✅ 배포판 생성 완료: {package_dir}")
    print("포함된 파일들:")
    for item in package_dir.iterdir():
        if item.is_file():
            size = item.stat().st_size / 1024  # KB
            print(f"  📄 {item.name} ({size:.1f} KB)")
        else:
            print(f"  📁 {item.name}/")

def create_user_guide(package_dir, version_type):
    """사용자 설치 가이드 생성"""
    guide_content = f"""급여명세서 생성기 v2.2 - {'세무사용 버전' if version_type == 'tax' else '고객용 버전'}

=== 설치 방법 ===
1. 이 폴더의 모든 파일을 원하는 위치에 복사하세요.
2. 급여명세서관리.exe 파일을 실행하세요.

=== 주요 파일들 ===
- 급여명세서관리.exe: 메인 프로그램
- tutorial_data.xlsx: 튜토리얼용 샘플 데이터
- config.json: 프로그램 설정 파일
- employees.json: 직원 정보 파일

=== 사용법 ===
1. 프로그램 실행 후 튜토리얼을 통해 기본 사용법을 익히세요.
2. 좌측 '직원 마스터 관리'에서 직원 정보를 입력하세요.
3. 우측 '월별 급여 계산'에서 급여 데이터를 계산하세요.
4. 최종 파일 생성으로 급여명세서를 출력하세요.

=== 라이선스 ===
{'본 버전은 세무사용을 위한 내부용입니다.' if version_type == 'tax' else '라이선스 활성화를 위해 메뉴 > 설정 > 라이선스 활성화를 선택하세요.'}

=== 기술 지원 ===
문제가 발생하면 개발자에게 문의하세요.
"""

    guide_file = package_dir / "설치_및_사용_가이드.txt"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide_content)

    print(f"사용자 가이드 생성: {guide_file}")

def build_client_version():
    """
    고객용 버전 exe 파일 빌드
    세무사 설정 기능 없이 라이선스 검증만 포함
    """
    version_type = "client"
    print("=== 급여명세서 생성기 고객용 버전 빌드 시작 ===")

    # 프로젝트 루트 디렉토리
    root_dir = Path(__file__).parent

    # 아이콘 생성/확인
    icon_path = root_dir / "icon.ico"
    if not icon_path.exists():
        print("아이콘 파일이 없어 생성합니다...")
        try:
            import subprocess
            result = subprocess.run([sys.executable, "create_icon.py"],
                                  cwd=root_dir, capture_output=True, text=True)
            if result.returncode == 0:
                print("아이콘 생성 성공")
            else:
                print(f"아이콘 생성 실패: {result.stderr}")
        except Exception as e:
            print(f"아이콘 생성 중 오류: {e}")

    # 출력 디렉토리
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"

    # 기존 빌드 파일 및 캐시 완전 정리 (강력한 정리)
    print("기존 빌드 파일 및 캐시 정리 중...")
    try:
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
    except Exception as e:
        print(f"dist 디렉토리 정리 실패 (무시): {e}")
    
    try:
        if build_dir.exists():
            shutil.rmtree(build_dir)
    except Exception as e:
        print(f"build 디렉토리 정리 실패 (무시): {e}")

    # 기존 spec 파일 삭제
    spec_files = list(root_dir.glob("*.spec"))
    for spec_file in spec_files:
        try:
            spec_file.unlink()
            print(f"기존 spec 파일 삭제: {spec_file.name}")
        except Exception as e:
            print(f"spec 파일 삭제 실패: {e}")

    # 고객용 버전 데이터 파일 (세무사 설정 기능 제외)
    # JSON 파일은 빌드 시 제외 (런타임에서 자동 생성)
    data_files = [
        ('tutorial_data.xlsx', '.'),
        ('payslip_template.html', '.'),
        ('license_system', 'license_system')
    ]

    # PyQt6 플랫폼 플러그인 포함
    try:
        import PyQt6
        pyqt6_base = os.path.dirname(PyQt6.__file__)
        qt_platform_path = os.path.join(pyqt6_base, 'Qt6', 'plugins', 'platforms')
        if os.path.exists(qt_platform_path):
            data_files.append((qt_platform_path, 'PyQt6/Qt6/plugins/platforms'))
            print(f"Qt 플랫폼 플러그인 포함: {qt_platform_path}")
    except Exception as e:
        print(f"Qt 플랫폼 플러그인 검색 실패 (무시): {e}")

    # PyInstaller 기본 옵션
    options = [
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        f'--distpath={dist_dir}',
        f'--workpath={build_dir}',
        '--name=급여명세서관리_클라이언트',
        # f'--icon={icon_path}',          # macOS에서는 기본 아이콘 사용
        '--additional-hooks-dir=pyinstaller_hooks',
    ]

    # 불필요한 라이브러리 제외 (세무사 기능 제외로 더 가벼움)
    excluded_modules = [
        'torch', 'tensorflow', 'bitsandbytes', 'librosa', 'cv2', 'matplotlib',
        'scipy.sparse', 'scipy.optimize', 'scipy.stats',
        'PIL.JpegImagePlugin', 'PIL.PngImagePlugin', 'PIL.BmpImagePlugin', 'PIL.TiffImagePlugin',
        'pkg_resources',
    ]

    for module in excluded_modules:
        options.extend(['--exclude-module', module])

    # 데이터 파일 추가 (macOS에서는 콜론 사용)
    for src, dst in data_files:
        src_path = root_dir / src
        if src_path.exists():
            if src_path.is_file():
                options.extend(['--add-data', f'{src_path}:{dst}'])
            elif src_path.is_dir():
                options.extend(['--add-data', f'{src_path}:{dst}'])
            print(f"데이터 파일 추가: {src} -> {dst}")

    # 숨겨진 import 추가 (라이선스 시스템만)
    options.extend([
        '--hidden-import=cryptography.fernet',
        '--hidden-import=cryptography.hazmat',
        '--hidden-import=cryptography.hazmat.primitives',
        '--hidden-import=cryptography.hazmat.primitives.asymmetric',
        '--hidden-import=cryptography.hazmat.primitives.asymmetric.rsa',
        '--hidden-import=cryptography.hazmat.primitives.asymmetric.padding',
        '--hidden-import=cryptography.hazmat.primitives.hashes',
        '--hidden-import=cryptography.hazmat.primitives.serialization',
        '--hidden-import=cryptography.hazmat.backends',
        '--hidden-import=cryptography.hazmat.backends.default',
        '--hidden-import=holidays',
        '--hidden-import=jaraco.text',
        '--hidden-import=jaraco.functools',
        '--hidden-import=jaraco.context',
        '--hidden-import=setuptools._vendor.jaraco.text',
    ])

    # 메인 파일 (고객용 메인 파일이 따로 있어야 함)
    main_file = root_dir / 'main_qt.py'  # 같은 파일 사용하되 라이선스 로직에서 분기
    options.append(str(main_file))

    print("PyInstaller 옵션들:")
    for opt in options:
        print(f"  {opt}")

    # PyInstaller 실행
    try:
        PyInstaller.__main__.run(options)
        print("✅ 고객용 버전 빌드 완료!")

        # 빌드 결과 확인
        exe_files = list(dist_dir.glob("*.exe"))
        if exe_files:
            exe_file = exe_files[0]
            file_size = exe_file.stat().st_size / (1024 * 1024)  # MB 단위
            print(f"파일 크기: {file_size:.2f} MB")

            # 배포판 구조 생성
            create_distribution_package(dist_dir, version_type)

        return True

    except Exception as e:
        print(f"❌ 빌드 실패: {e}")
        return False

def main():
    """메인 함수 - 버전 선택"""
    import argparse

    parser = argparse.ArgumentParser(description='급여명세서 생성기 빌드 도구')
    parser.add_argument('--version', choices=['tax', 'client'],
                       default='tax', help='빌드할 버전 (tax: 세무사용, client: 고객용)')

    args = parser.parse_args()

    if args.version == 'tax':
        print("세무사용 버전 빌드를 시작합니다...")
        print("세무사가 라이선스 코드 생성 및 고객용 패키지 압축을 위한 버전입니다.")
        success = build_exe()
        if success:
            print("\n🎉 세무사용 버전 배포 준비 완료!")
            print("급여명세서관리_tax_v2.2 폴더에서 생성된 파일들을 확인하세요.")
    else:  # client
        print("고객용 버전 빌드를 시작합니다...")
        print("라이선스 검증만 포함된 고객용 버전입니다.")
        success = build_client_version()
        if success:
            print("\n🎉 고객용 버전 배포 준비 완료!")
            print("급여명세서관리_client_v2.0 폴더에서 생성된 파일들을 확인하세요.")

    if not success:
        print("\n❌ 빌드 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()
