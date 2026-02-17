
import hashlib
import platform
import uuid
import subprocess

# Windows에서만 wmi import
try:
    if platform.system() == 'Windows':
        import wmi
        _HAS_WMI = True
    else:
        _HAS_WMI = False
except ImportError:
    _HAS_WMI = False


def _get_macos_machine_id():
    """
    macOS에서 하드웨어 ID를 생성합니다.
    MAC 주소와 시스템 정보를 조합하여 고유 ID를 생성합니다.
    :return: SHA-256으로 해시된 고유 머신 ID 문자열. 실패 시 None.
    """
    try:
        components = []
        
        # 1. MAC 주소 가져오기 (가장 안정적인 식별자)
        mac = uuid.getnode()
        if mac:
            mac_address = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) 
                                    for elements in range(0, 2*6, 2)][::-1])
            components.append(f"MAC:{mac_address}")
        
        # 2. 시스템 아키텍처
        machine = platform.machine()
        if machine:
            components.append(f"ARCH:{machine}")
        
        # 3. macOS 시리얼 번호 (system_profiler 사용)
        try:
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'Serial Number' in line and 'system' not in line.lower():
                        serial = line.split(':')[-1].strip()
                        if serial:
                            components.append(f"SN:{serial}")
                            break
        except Exception:
            pass
        
        # 최소 1개 이상의 정보가 있어야 함
        if len(components) < 1:
            print("오류: macOS에서 충분한 하드웨어 정보를 가져올 수 없습니다.")
            return None
        
        # 정보를 조합하여 유일한 문자열 생성
        combined_id = "|".join(sorted(components))
        
        # SHA-256 해시를 사용하여 최종 머신 ID 생성
        hashed_id = hashlib.sha256(combined_id.encode('utf-8')).hexdigest()
        
        return hashed_id
        
    except Exception as e:
        print(f"macOS 하드웨어 ID 생성 중 오류: {e}")
        return None


def get_machine_id():
    """
    컴퓨터의 고유 하드웨어 정보를 조합하여 암호화된 머신 ID를 생성합니다.
    CPU ID, 메인보드 시리얼, 디스크 시리얼, BIOS 정보를 사용합니다.
    :return: SHA-256으로 해시된 고유 머신 ID 문자열. 실패 시 None.
    """
    # macOS 지원 추가
    if platform.system() == 'Darwin':  # macOS
        return _get_macos_machine_id()
    
    # Windows가 아니면 None 반환
    if not _HAS_WMI:
        print(f"하드웨어 ID 조회는 Windows에서만 지원됩니다. (현재: {platform.system()})")
        return None
    
    try:
        c = wmi.WMI()
        components = []

        # CPU 정보 가져오기
        cpu_id = ""
        for cpu in c.Win32_Processor():
            cpu_id = cpu.ProcessorId.strip()
            if cpu_id:
                components.append(f"CPU:{cpu_id}")
                break

        # 메인보드 정보 가져오기
        board_id = ""
        for board in c.Win32_BaseBoard():
            board_id = board.SerialNumber.strip()
            if board_id:
                components.append(f"BOARD:{board_id}")
                break

        # 디스크 시리얼 정보 가져오기
        disk_id = ""
        for disk in c.Win32_DiskDrive():
            if disk.SerialNumber and disk.SerialNumber.strip():
                disk_id = disk.SerialNumber.strip()
                components.append(f"DISK:{disk_id}")
                break

        # BIOS 정보 가져오기
        bios_id = ""
        for bios in c.Win32_BIOS():
            bios_id = bios.SerialNumber.strip() if bios.SerialNumber else ""
            if not bios_id and bios.Version:
                bios_id = bios.Version.strip()
            if bios_id:
                components.append(f"BIOS:{bios_id}")
                break

        # 최소 2개 이상의 하드웨어 정보가 있어야 함
        if len(components) < 2:
            print("오류: 충분한 하드웨어 정보를 가져올 수 없습니다.")
            return None

        # 정보를 조합하여 유일한 문자열 생성
        combined_id = "|".join(sorted(components))  # 정렬하여 일관성 확보

        # SHA-256 해시를 사용하여 최종 머신 ID 생성
        hashed_id = hashlib.sha256(combined_id.encode('utf-8')).hexdigest()

        return hashed_id

    except Exception as e:
        print(f"하드웨어 정보 조회 중 오류 발생: {e}")
        print("프로그램을 '관리자 권한으로 실행'하면 문제가 해결될 수 있습니다.")
        return None

if __name__ == '__main__':
    # 모듈 단독 실행 시 테스트
    machine_id = get_machine_id()
    if machine_id:
        print(f"생성된 컴퓨터 고유 ID: {machine_id}")
    else:
        print("컴퓨터 고유 ID 생성에 실패했습니다.")
