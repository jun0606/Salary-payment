#!/usr/bin/env python3
"""
PyQt6 기반 급여명세서 생성기 메인 파일
세무사용 버전 - tkinter에서 PyQt6로 마이그레이션된 버전

기능:
- 현대적인 GUI 제공
- 직원 데이터 관리
- 급여 계산 및 명세서 생성
- 라이선스 코드 생성 및 고객용 패키지 압축
- 세무사 정보 관리
"""

import sys
import os
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSplitter, QStatusBar, QMenuBar, QMenu, QGroupBox,
    QSplashScreen, QMessageBox, QDialog, QDialogButtonBox, QProgressBar, QScrollArea, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QPixmap, QPainter, QColor, QFont, QIcon

# 마이그레이션 시스템 임포트
from migration_manager import MigrationManager

# 로컬 모듈 임포트 (아직 마이그레이션되지 않음)
import logic
import date_utils

# 튜토리얼 모듈
try:
    from tutorial_wizard_qt import start_tutorial
    print("튜토리얼 모듈 import 성공")
except ImportError as e:
    print(f"튜토리얼 모듈 import 오류: {e}")
    start_tutorial = None

# 연차 관리 모듈
try:
    from annual_leave_dialog_qt import AnnualLeaveDialog
    print("연차 관리 모듈 import 성공")
except ImportError as e:
    print(f"연차 관리 모듈 import 오류: {e}")
    AnnualLeaveDialog = None

# 라이선스 시스템
try:
    # sys.path에 license_system 경로 추가
    license_system_path = os.path.join(os.path.dirname(__file__), 'license_system')
    if license_system_path not in sys.path:
        sys.path.insert(0, license_system_path)

    import license_verifier
    import hardware_id
    print("라이선스 시스템 import 성공")
except ImportError as e:
    print(f"라이선스 시스템 import 오류: {e}")
    print("라이선스 시스템 경로:", os.path.join(os.path.dirname(__file__), 'license_system'))

    # 더미 객체 생성 (최후의 폴백)
    class DummyLicenseVerifier:
        LICENSE_FILE_PATH = "dummy_license.dat"

        @staticmethod
        def check_license():
            return 'NOT_LICENSED'

        @staticmethod
        def verify_activation_code(code):
            return 'UNKNOWN_ERROR', None

        @staticmethod
        def create_license_file(expiry_date, hw_id):
            return False

        @staticmethod
        def _get_encryption_key(hw_id):
            return b'dummy_key_' + str(hw_id).encode()[:10]

    license_verifier = DummyLicenseVerifier()

    class DummyHardwareId:
        @staticmethod
        def get_machine_id():
            return "dummy_hw_id"
    hardware_id = DummyHardwareId()

    print("더미 라이선스 객체 생성됨 (기능 제한)")


class PayslipQtApp(QMainWindow):
    """
    PyQt6 기반 메인 애플리케이션 클래스

    tkinter PayslipApp의 PyQt6 버전
    """

    def _patch_jaraco_text_early(self):
        """프로그램 시작 시 jaraco.text 문제를 사전 해결"""
        try:
            # lorem_ipsum 텍스트 정의
            lorem_content = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.

Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur?

Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur? At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id est laborum et dolorum fuga.

Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet ut et voluptates repudiandae sint et molestiae non recusandae.

Itaque earum rerum hic tenetur a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis doloribus asperiores repellat."""

            # 더미 클래스들 정의
            class DummyFoldedCase(str):
                def casefold(self):
                    return super().casefold()

            class DummySeparatedValues(str):
                separator = ','

            class DummyExceptionTrap:
                def __init__(self, exception_class):
                    self.exception_class = exception_class

                def passes(self, func):
                    return func

            # 완전한 jaraco.text 더미 모듈 클래스
            class CompleteJaracoText:
                """jaraco.text의 완전한 인터페이스를 제공하는 더미 모듈"""

                # 기본 속성들
                lorem_ipsum = lorem_content

                # 클래스들
                FoldedCase = DummyFoldedCase
                SeparatedValues = DummySeparatedValues
                ExceptionTrap = DummyExceptionTrap
                Splitter = str.split
                Stripper = str.strip
                WordSet = set

                # 함수들
                @staticmethod
                def drop_comment(line):
                    """Drop comments."""
                    return line.partition(' #')[0]

                @staticmethod
                def trim(s):
                    """Trim something like a docstring."""
                    return textwrap.dedent(s).strip()

                @staticmethod
                def wrap(s):
                    """Wrap lines of text."""
                    return '\n'.join(textwrap.wrap(s))

                @staticmethod
                def unwrap(s):
                    """Given a multi-line string, return an unwrapped version."""
                    return ' '.join(s.splitlines())

                @staticmethod
                def normalize_newlines(text):
                    """Replace alternate newlines with the canonical newline."""
                    return text.replace('\r\n', '\n').replace('\r', '\n')

                @staticmethod
                def remove_prefix(text, prefix):
                    """Remove the prefix from the text if it exists."""
                    if text.startswith(prefix):
                        return text[len(prefix):]
                    return text

                @staticmethod
                def remove_suffix(text, suffix):
                    """Remove the suffix from the text if it exists."""
                    if text.endswith(suffix):
                        return text[:-len(suffix)]
                    return text

                @staticmethod
                def simple_html_strip(s):
                    """Remove HTML from the string."""
                    import re
                    html_stripper = re.compile(r'<[^>]+>')
                    return html_stripper.sub('', s)

                @staticmethod
                def is_decodable(value):
                    """Return True if the supplied value is decodable."""
                    try:
                        if isinstance(value, bytes):
                            value.decode('utf-8')
                        return True
                    except:
                        return False

                @staticmethod
                def is_binary(value):
                    """Return True if the value appears to be binary."""
                    return isinstance(value, bytes) and not CompleteJaracoText.is_decodable(value)

                @staticmethod
                def substitution(old, new):
                    """Return a function that will perform a substitution."""
                    return lambda s: s.replace(old, new)

                @staticmethod
                def multi_substitution(*substitutions):
                    """Take a sequence of pairs specifying substitutions."""
                    def substitute(s):
                        for old, new in substitutions:
                            s = s.replace(old, new)
                        return s
                    return substitute

                @staticmethod
                def compose(*functions):
                    """Compose functions."""
                    return functools.reduce(lambda f, g: lambda x: f(g(x)), functions)

                @staticmethod
                def yield_lines(text):
                    """Yield valid lines of a string."""
                    for line in text.splitlines():
                        line = line.strip()
                        if line and not line.startswith('#'):
                            yield line

                @staticmethod
                def join_continuation(lines):
                    """Join lines continued by a trailing backslash."""
                    result = []
                    current = ''
                    for line in lines:
                        if line.endswith('\\'):
                            current += line[:-1]
                        else:
                            current += line
                            result.append(current)
                            current = ''
                    return result

                # 더미 함수들 (기본 구현)
                @staticmethod
                def indent(text, prefix='    '):
                    return '\n'.join(prefix + line for line in text.splitlines())

                @staticmethod
                def read_newlines(filename, limit=1024):
                    return '\n'

                @staticmethod
                def words(text):
                    return text.split()

                # 필요한 서브모듈들
                @staticmethod
                def method_cache(func):
                    return func

            # 완전한 더미 모듈 생성
            dummy_jaraco_text = CompleteJaracoText()

            # 필요한 속성들 추가
            dummy_jaraco_text.re = __import__('re')
            dummy_jaraco_text.textwrap = __import__('textwrap')
            dummy_jaraco_text.itertools = __import__('itertools')
            dummy_jaraco_text.functools = __import__('functools')

            # sys.modules에 설정 (import 전에 미리 설정)
            sys.modules['jaraco.text'] = dummy_jaraco_text
            sys.modules['setuptools._vendor.jaraco.text'] = dummy_jaraco_text
            sys.modules['setuptools._vendor.jaraco'] = type('Module', (), {'text': dummy_jaraco_text})()
            sys.modules['setuptools._vendor'] = type('Module', (), {'jaraco': sys.modules['setuptools._vendor.jaraco']})()
            sys.modules['setuptools'] = type('Module', (), {'_vendor': sys.modules['setuptools._vendor']})()

            print("jaraco.text 사전 패치 완료 - import 전에 모듈 설정됨")

        except Exception as e:
            print(f"jaraco.text 사전 패치 실패: {e}")
            # 실패해도 계속 진행 (중요!)

    def __init__(self):
        print("__init__ 시작")
        try:
            super().__init__()
            print("super().__init__() 완료")
        except Exception as e:
            print(f"super().__init__() 실패: {e}")
            import traceback
            traceback.print_exc()
            # 심각한 문제이므로 재시도
            try:
                super().__init__()
                print("super().__init__() 재시도 성공")
            except Exception as e2:
                print(f"super().__init__() 재시도 실패: {e2}")
                # 최후의 수단으로 기본 QWidget 생성
                from PyQt6.QtWidgets import QWidget
                QWidget.__init__(self)
                print("QWidget.__init__()로 fallback")

        # jaraco.text 문제 사전 해결 (가장 먼저 실행되어야 함)
        print("_patch_jaraco_text_early() 호출")
        try:
            self._patch_jaraco_text_early()
            print("_patch_jaraco_text_early() 성공")
        except Exception as e:
            print(f"_patch_jaraco_text_early() 실패 (무시): {e}")
            # jaraco.text 패치 실패는 치명적이지 않으므로 계속 진행

        # 프로그램 시작 시 이전 임시 디렉토리 자동 정리 (근본 해결)
        print("_cleanup_previous_temp_dirs() 호출")
        try:
            self._cleanup_previous_temp_dirs()
            print("_cleanup_previous_temp_dirs() 성공")
        except Exception as e:
            print(f"_cleanup_previous_temp_dirs() 실패 (무시): {e}")
            # _MEI 정리 실패는 치명적이지 않으므로 계속 진행

        # 애플리케이션 초기화 (마이그레이션 실행 및 파일 검증)
        print("initialize_application() 호출")
        try:
            self.initialize_application()
            print("initialize_application() 성공")
        except Exception as e:
            print(f"initialize_application() 실패 (무시): {e}")
            # 마이그레이션 실패는 치명적이지 않으므로 계속 진행

        print("__init__ 완료 - 기본 초기화 진행")
        self._init_basic_members()


        # 세무사 버전 브랜딩 강화
        self.title = "🏛️ 세무사 급여명세서 관리 시스템 v2.3"
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1400, 900)

        # 세무사 상징 아이콘 설정 (세무서 건물 아이콘)
        try:
            # 세무서 건물 아이콘 이모티콘을 픽스맵으로 변환하여 아이콘으로 설정
            from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setFont(QFont("Segoe UI Emoji", 24))
            painter.setPen(QColor("#2c3e50"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🏛️")
            painter.end()

            self.setWindowIcon(QIcon(pixmap))
        except Exception as e:
            print(f"아이콘 설정 오류: {e}")
            # 아이콘 설정 실패 시 기본 아이콘 사용

        # 데이터 초기화
        self.summary_df = None
        self.employee_data = {}
        self.data_month_for_title = ""
        self.selected_file_path = ""

        # 설정 파일
        self.config_file = "config.json"
        self.employees_file = "employees.json"

        # 라이선스 상태
        self.locked = True

        # CompanyManager 인스턴스 생성 및 시그널 연결
        try:
            from company_manager import CompanyManager
            self.company_manager = CompanyManager()
            self.company_manager.company_changed.connect(self.on_company_data_changed)
            print("CompanyManager 시그널 연결 성공")
        except Exception as e:
            print(f"CompanyManager 연결 실패: {e}")
            self.company_manager = None

        # PyQt6 변수들
        self.master_form_vars = {
            "user_id": "",
            "name": "",
            "department": "",
            "position": "",
            "hire_date": "",
            "individual_payment_date": ""
        }

        self.global_payment_date_var = ""
        self.month_var = ""  # 계산 연월 저장 변수 추가

        # 월별 테이블 컬럼 정의
        self.monthly_columns = [
            "user_id", "name", "department", "position", "hire_date", "payment_date", "base_pay",
            "weekly_holiday_allowance", "extra_pay", "night_pay", "national_pension", "health_insurance",
            "employment_insurance", "long_term_care_insurance", "income_tax", "local_income_tax",
            "deductions", "net_pay", "총급여액"
        ]

        # 기본 데이터 초기화 (스플래시 화면 표시용)
        self.config_data = {}
        self.load_config()

        # 스플래시 화면 표시 및 라이선스 체크
        self.show_splash_and_run_license_check()

    def _init_basic_members(self):
        """기본 멤버 변수 초기화"""

    def initialize_application(self):
        """애플리케이션 초기화 - 마이그레이션 실행 및 파일 검증"""
        try:
            print("애플리케이션 초기화 시작")
            
            # 마이그레이션 매니저 생성
            migration_manager = MigrationManager()
            
            # 마이그레이션 실행
            migration_manager.run_migration()
            
            # 파일 검증
            migration_manager.verify_files()
            
            print("애플리케이션 초기화 완료")
            
        except Exception as e:
            print(f"애플리케이션 초기화 중 오류 (무시): {e}")
            # 초기화 실패는 치명적이지 않으므로 계속 진행

    def _cleanup_previous_temp_dirs(self):
        """2024년 12월 현재 가장 안전한 _MEI 폴더 정리 방법"""
        try:
            # psutil import 시도 (실패해도 프로그램 계속 실행)
            try:
                import psutil
                has_psutil = True
            except ImportError:
                has_psutil = False
                print("psutil 미설치 - 기본 정리 방식 사용")

            import pathlib
            from datetime import datetime, timedelta

            import tempfile
            temp_dir = pathlib.Path(tempfile.gettempdir())
            current_time = datetime.now()

            # psutil이 있는 경우에만 프로세스 모니터링
            current_pids = set()
            if has_psutil:
                for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                    try:
                        if 'python' in proc.info['name'].lower():
                            current_pids.add(proc.info['pid'])
                    except:
                        continue

            # _MEI 폴더들 스마트 검사 및 정리
            for mei_dir in temp_dir.glob('_MEI*'):
                if not mei_dir.is_dir():
                    continue

                try:
                    # 1. 디렉토리 생성 시간 확인
                    stat = mei_dir.stat()
                    created_time = datetime.fromtimestamp(stat.st_ctime)

                    # 2. 30분 이상 된 오래된 폴더만 대상 (psutil 없는 경우 1시간)
                    age_limit = timedelta(minutes=30) if has_psutil else timedelta(hours=1)
                    if current_time - created_time < age_limit:
                        continue

                    # 3. 해당 폴더를 사용하는 프로세스 확인 (psutil 있는 경우에만)
                    folder_in_use = False
                    if has_psutil:
                        try:
                            # 디렉토리 내 파일들을 검사해서 사용 중인지 확인
                            for file_path in mei_dir.rglob('*'):
                                if file_path.is_file():
                                    # 파일이 사용 중인지 확인 (크로스 플랫폼)
                                    try:
                                        with open(file_path, 'rb') as f:
                                            # 파일을 열 수 있으면 사용 가능
                                            pass
                                    except (OSError, PermissionError):
                                        # 파일이 잠겨있으면 사용 중
                                        folder_in_use = True
                                        break
                        except:
                            folder_in_use = True
                    else:
                        # psutil 없는 경우: 파일 접근 시도로만 판단 (더 보수적)
                        try:
                            for file_path in mei_dir.rglob('*'):
                                if file_path.is_file():
                                    with open(file_path, 'rb') as f:
                                        pass
                        except (OSError, PermissionError):
                            folder_in_use = True

                    # 4. 사용 중이 아니면 안전하게 삭제
                    if not folder_in_use:
                        import shutil
                        shutil.rmtree(mei_dir, ignore_errors=True)
                        print(f"안전하게 정리된 오래된 _MEI 폴더: {mei_dir.name}")

                except Exception as e:
                    # 안전하게 무시 - 삭제 실패해도 프로그램 계속 실행
                    print(f"_MEI 폴더 정리 시도 실패 (무시): {mei_dir.name} - {e}")
                    continue

        except Exception as e:
            # 모든 예외 무시 - 정리 실패가 프로그램 실행을 막아서는 안됨
            print(f"스마트 정리 실패 (무시): {e}")

    def _basic_cleanup_fallback(self):
        """psutil 없는 환경을 위한 기본 정리"""
        try:
            import pathlib
            from datetime import datetime, timedelta

            import tempfile
            temp_dir = pathlib.Path(tempfile.gettempdir())
            current_time = datetime.now()

            # 단순 시간 기반 정리 (더 보수적)
            for mei_dir in temp_dir.glob('_MEI*'):
                try:
                    stat = mei_dir.stat()
                    created_time = datetime.fromtimestamp(stat.st_ctime)

                    # 1시간 이상 된 폴더만 정리 (더 긴 시간)
                    if current_time - created_time > timedelta(hours=1):
                        import shutil
                        shutil.rmtree(mei_dir, ignore_errors=True)
                        print(f"기본 방식으로 정리된 _MEI 폴더: {mei_dir.name}")
                except:
                    continue
        except:
            pass

        # TMP 환경변수 변경으로 PyInstaller 임시 디렉토리 제어 (근본 해결)
        self.setup_custom_temp_dir()



        # 기본 설정
        self.title = "⚖️ 급여명세서 관리 Ver 2.0"
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 1400, 900)

        # 세무 상징 아이콘 설정 (무료 아이콘)
        try:
            # 저울 아이콘 이모티콘을 픽스맵으로 변환하여 아이콘으로 설정
            from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.setFont(QFont("Segoe UI Emoji", 24))
            painter.setPen(QColor("#2c3e50"))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "⚖️")
            painter.end()

            self.setWindowIcon(QIcon(pixmap))
        except Exception as e:
            print(f"아이콘 설정 오류: {e}")
            # 아이콘 설정 실패 시 기본 아이콘 사용

        # 데이터 초기화
        self.summary_df = None
        self.employee_data = {}
        self.data_month_for_title = ""
        self.selected_file_path = ""

        # 설정 파일
        self.config_file = "config.json"
        self.employees_file = "employees.json"

        # 라이선스 상태
        self.locked = True

        # PyQt6 변수들
        self.master_form_vars = {
            "user_id": "",
            "name": "",
            "department": "",
            "position": "",
            "hire_date": "",
            "individual_payment_date": ""
        }

        self.global_payment_date_var = ""
        self.month_var = ""  # 계산 연월 저장 변수 추가

        # 월별 테이블 컬럼 정의
        self.monthly_columns = [
            "user_id", "name", "department", "position", "hire_date", "payment_date", "base_pay",
            "weekly_holiday_allowance", "extra_pay", "night_pay", "national_pension", "health_insurance",
            "employment_insurance", "long_term_care_insurance", "income_tax", "local_income_tax",
            "deductions", "net_pay", "총급여액"
        ]

        # 기본 데이터 초기화 (스플래시 화면 표시용)
        self.config_data = {}
        self.load_config()

        # 스플래시 화면 표시 및 라이선스 체크
        self.show_splash_and_run_license_check()

    def show_splash_and_run_license_check(self):
        """스플래시 화면 표시 및 라이선스 체크 (tkinter 버전 디자인 적용)"""
        # 세무사 정보 가져오기
        tax_accountant_name = self.config_data.get("tax_accountant_name", "세무사")
        tax_office_name = self.config_data.get("tax_office_name", "세무회계사무소")
        tax_accountant_phone = self.config_data.get("tax_accountant_phone", "")
        tax_accountant_email = self.config_data.get("tax_accountant_email", "")
        tax_branch_name = self.config_data.get("tax_branch_name", "")
        company_name = self.config_data.get("company_name", "")

        # 세무사무소 스타일 스플래시 위젯 생성 (더 큰 크기로 확대)
        splash_widget = QWidget()
        splash_widget.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        splash_widget.setFixedSize(1100, 800)
        splash_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
        """)

        # 중앙 정렬
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1100) // 2
        y = (screen.height() - 800) // 2
        splash_widget.move(x, y)

        # 레이아웃 설정 (더 넓은 공간 활용)
        layout = QVBoxLayout(splash_widget)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(20)

        # 타이틀 영역
        title_label = QLabel("세무회계 프로그램")
        title_label.setFont(QFont("맑은 고딕", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("급여명세서 자동 생성 시스템")
        subtitle_label.setFont(QFont("맑은 고딕", 14))
        subtitle_label.setStyleSheet("color: #6c757d;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(30)

        # 회사/세무사 정보 영역
        display_office_name = tax_office_name if tax_office_name else "세무회계사무소"
        if tax_branch_name:
            office_text = f"{display_office_name} ({tax_branch_name})"
        else:
            office_text = display_office_name

        print(f"로딩 화면 세무사 정보: 세무서 '{office_text}', 세무사 '{tax_accountant_name}', 지점 '{tax_branch_name}'")

        # 세무사 정보 그룹 (업데이트된 디자인)
        tax_info_widget = QWidget()
        tax_info_layout = QVBoxLayout(tax_info_widget)
        tax_info_layout.setContentsMargins(30, 25, 30, 25)
        tax_info_layout.setSpacing(12)

        # 세무사 이름 (가장 크게, 왼쪽 정렬하여 공간 활용)
        name_label = QLabel(f"세무사/사무장 : {tax_accountant_name}")
        name_label.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2c3e50;")
        tax_info_layout.addWidget(name_label)

        # 세무서 정보 (한 줄에 표시)
        office_info_layout = QHBoxLayout()
        office_info_layout.addWidget(QLabel("세무서:"))
        office_name_label = QLabel(display_office_name)
        office_name_label.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
        office_name_label.setStyleSheet("color: #2c3e50;")
        office_info_layout.addWidget(office_name_label)

        if tax_branch_name:
            office_info_layout.addWidget(QLabel("지점:"))
            branch_name_label = QLabel(f"({tax_branch_name})")
            branch_name_label.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
            branch_name_label.setStyleSheet("color: #2c3e50;")
            office_info_layout.addWidget(branch_name_label)

        office_info_layout.addStretch()
        tax_info_layout.addLayout(office_info_layout)

        # 연락처 정보 (구분선 추가)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #e9ecef;")
        tax_info_layout.addWidget(separator)

        contact_info = []
        if tax_accountant_phone:
            contact_info.append(f"전화: {tax_accountant_phone}")
        if tax_accountant_email:
            contact_info.append(f"이메일: {tax_accountant_email}")

        if contact_info:
            contact_text = " | ".join(contact_info)
            contact_label = QLabel(contact_text)
            contact_label.setFont(QFont("맑은 고딕", 12))
            contact_label.setStyleSheet("color: #495057;")
            tax_info_layout.addWidget(contact_label)

        layout.addWidget(tax_info_widget)

        # 회사 정보 (별도 표시)
        if company_name:
            company_label = QLabel(f"회사명: {company_name}")
            company_label.setFont(QFont("맑은 고딕", 14, QFont.Weight.Bold))
            company_label.setStyleSheet("color: #2C3E50; background-color: rgba(255, 255, 255, 0.9); padding: 8px 15px; border-radius: 5px;")
            company_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(company_label)

        layout.addStretch()

        # 강화된 경고 메시지 (저작권법, 컴퓨터프로그램보호법 등 참고)
        warning_text = f"""【경고】본 소프트웨어는 '{display_office_name}'의 독점적 자산입니다.

「저작권법」제2조, 「컴퓨터프로그램보호법」제2조 및 「부정경쟁방지법」제2조에 따라
본 소프트웨어의 무단 복제・배포・수정・역설계・해킹・임대・대여・양도・상업적 이용을
엄격히 금지합니다.

위반 시 5년 이하의 징역 또는 5천만원 이하의 벌금에 처해질 수 있으며,
민사상 손해배상 책임도 부담합니다 (저작권법 제136조, 컴퓨터프로그램보호법 제27조).

개발・기능개선 문의는 세무사 {tax_accountant_name}에게 직접 연락주시기 바랍니다.
라이선스 위반 시 즉각 사용이 중지됩니다."""

        warning_label = QLabel(warning_text)
        warning_label.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        warning_label.setStyleSheet("color: red;")
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)

        layout.addStretch()

        # 프로그레스 바 (더 눈에 띄게)
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # indeterminate 모드
        progress_bar.setFixedHeight(25)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 12px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.8);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 10px;
            }
        """)
        layout.addWidget(progress_bar)

        # 로딩 텍스트
        loading_label = QLabel("데이터 로딩 중...")
        loading_label.setFont(QFont("맑은 고딕", 11, QFont.Weight.Normal, italic=True))
        loading_label.setStyleSheet("color: gray;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(loading_label)

        # 스플래시 화면 표시
        splash_widget.show()
        QApplication.processEvents()

        try:
            # 데이터 로드 (UI 초기화 없이)
            self.load_master_data()

            # 로딩 완료 후 스플래시 닫고 동의 화면 표시 (10초 유지)
            QTimer.singleShot(10000, lambda: self.show_consent_after_splash(splash_widget))

        except Exception as e:
            splash_widget.close()
            QMessageBox.critical(None, "초기화 오류", f"프로그램 초기화 중 오류가 발생했습니다:\n{str(e)}")
            self.close()

    def show_consent_after_splash(self, splash):
        """스플래시 화면 후 동의 화면 표시"""
        splash.close()

        # 개인정보 동의 대화상자
        if not self.show_privacy_consent_dialog():
            self.close()
            return

        # UI 초기화 (아직 표시하지 않음)
        self.setup_ui()

        # UI 초기화 후 회사 정보 다시 로드 및 갱신
        self.load_config()  # 회사 정보 재로드

        # UI 초기화 후 테이블 업데이트
        if hasattr(self, 'master_data_widget') and self.master_data_widget:
            self.master_data_widget.refresh_table()

        self.run_license_check()

        # 동의 후 메인 창 표시
        self.show()

    def show_privacy_consent_dialog(self):
        """개인정보 처리 방침 동의 대화상자 표시"""
        dialog = QDialog()
        dialog.setWindowTitle("개인정보 처리 방침 동의")
        dialog.setModal(True)
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        # 제목
        title_label = QLabel("개인정보 처리 방침")
        title_label.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 스크롤 내용 위젯
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 세무사 정보 동적 로드
        tax_accountant_name = self.config_data.get("tax_accountant_name", "세무사/사무장")
        tax_accountant_title = self.config_data.get("tax_accountant_title", "세무사/사무장")
        tax_accountant_phone = self.config_data.get("tax_accountant_phone", "")
        tax_accountant_email = self.config_data.get("tax_accountant_email", "")
        company_name = self.config_data.get("company_name", "")

        # 개인정보 처리 방침 내용 (법적 요구사항 기반 + 동적 정보 반영)
        privacy_policy_text = f"""
「개인정보 보호법」제15조, 제22조, 제24조에 따라 귀하의 개인정보를 다음과 같이 처리합니다.

【1. 개인정보의 수집・이용 목적】
본 급여명세서 생성 프로그램은 다음 목적을 위해 개인정보를 수집・이용합니다:
• 직원 급여 계산 및 명세서 생성
• 인사・노무 관리 기록 유지
• 세무 신고 자료 관리
• 프로그램 기능 제공 및 개선

【2. 수집하는 개인정보의 항목】
• 필수항목: 성명, 주민등록번호, 입사일, 부서, 직급, 급여 정보, 계좌번호
• 선택항목: 전화번호, 이메일, 주소 등 추가 연락처 정보

【3. 개인정보의 보유・이용 기간】
• 직원 고용 기간 동안 및 법정 보존 기간 (상법, 근로기준법 등에 따른 3년~5년)
• 동의 철회 시 즉시 파기 (단, 법령에 따른 보존 의무가 있는 경우 제외)

【4. 개인정보의 제3자 제공】
• 원칙적으로 제3자에게 제공하지 않음
• 법령에 따른 수사・조사 기관의 요구가 있는 경우에 한해 제공

【5. 개인정보 처리의 위탁】
• 급여 계산 및 세무 대행을 목적으로 세무사무소에 위탁할 수 있음
• 위탁 시 개인정보 보호 조치를 취함

【6. 정보주체의 권리・의무 및 행사방법】
• 개인정보 열람, 정정, 삭제, 처리정지 요구 가능
• 개인정보 관리 책임자에게 서면・전자우편・모사전송으로 요구
• 동의 거부 시 프로그램 사용이 제한될 수 있음

【7. 개인정보의 파기】
• 보유 기간 경과 시 즉시 파기
• 전자적 파일 형태: 복구 불가능한 방법으로 삭제
• 종이 문서: 분쇄 또는 소각

【8. 개인정보 관리 책임자】
• 성명: {tax_accountant_name}
• 연락처: {tax_accountant_phone}
• 이메일: {tax_accountant_email}

【9. 개인정보 보호책임자】
• 성명: {tax_accountant_name}
• 연락처: {tax_accountant_phone}
• 이메일: {tax_accountant_email}

【10. 개인정보 처리방침 변경】
• 법령・정책 변경에 따라 내용이 변경될 수 있음
• 변경 시 사전 고지

【11. 동의 거부 권리 및 불이익】
귀하는 개인정보 수집・이용에 대한 동의를 거부할 권리가 있습니다.
다만, 동의를 거부하는 경우 급여명세서 생성 및 관리 기능이 제한될 수 있습니다.

위 개인정보 처리 방침을 충분히 읽어보시고, 동의 여부를 결정하여 주시기 바랍니다.
        """

        privacy_policy = QLabel(privacy_policy_text)
        privacy_policy.setWordWrap(True)
        privacy_policy.setAlignment(Qt.AlignmentFlag.AlignTop)
        privacy_policy.setFont(QFont("맑은 고딕", 9))
        privacy_policy.setStyleSheet("line-height: 1.5; padding: 10px;")

        scroll_layout.addWidget(privacy_policy)
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 체크박스 (동의 확인)
        consent_layout = QHBoxLayout()
        self.consent_checkbox = QCheckBox("위 개인정보 처리 방침에 동의합니다.")
        self.consent_checkbox.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        consent_layout.addWidget(self.consent_checkbox)
        layout.addLayout(consent_layout)

        # 버튼들
        button_layout = QHBoxLayout()
        agree_button = QPushButton("동의")
        agree_button.clicked.connect(self.check_consent_and_accept)
        agree_button.setEnabled(False)  # 초기에는 비활성화
        disagree_button = QPushButton("취소")
        disagree_button.clicked.connect(dialog.reject)

        # 체크박스 상태에 따라 버튼 활성화
        self.consent_checkbox.stateChanged.connect(
            lambda: agree_button.setEnabled(self.consent_checkbox.isChecked())
        )

        button_layout.addStretch()
        button_layout.addWidget(agree_button)
        button_layout.addWidget(disagree_button)
        layout.addLayout(button_layout)

        # 다이얼로그를 결과로 저장
        self.privacy_dialog = dialog
        result = dialog.exec()
        return result == QDialog.DialogCode.Accepted

    def check_consent_and_accept(self):
        """동의 확인 후 다이얼로그 닫기"""
        if self.consent_checkbox.isChecked():
            self.privacy_dialog.accept()

    def run_license_check_and_show_main(self, splash):
        """라이선스 체크 후 메인 창 표시"""
        self.run_license_check()
        splash.close()
        self.show()

    def setup_ui(self):
        """메인 UI 설정"""
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)

        # 회사명 표시 영역 (회사 선택 기능 추가)
        self.setup_company_header(main_layout)

        # 메인 컨텐츠 영역 (스플리터)
        self.setup_main_content(main_layout)

        # 상태바
        self.setup_status_bar()

        # 메뉴
        self.setup_menu()

        # 스타일 적용
        self.apply_modern_styles()

    def setup_company_header(self, parent_layout):
        """회사명 표시 영역 설정 (시그널 연결 개선 버전)"""
        try:
            print("setup_company_header 시작")

            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            print("header_frame와 header_layout 생성 완료")

            company_label = QLabel("회사명:")
            self.company_selector = QComboBox()
            self.company_selector.setMinimumWidth(200)
            self.company_selector.currentTextChanged.connect(self.on_company_selected)
            
            # PyQt6 호환성 있는 시그널 연결 방식으로 변경
            try:
                # PyQt6에서 안전한 시그널 연결
                self.company_selector.activated.connect(self.on_company_selector_activated)
                self.company_selector.currentIndexChanged.connect(self.on_company_selector_changed)
                print("시그널 연결 성공")
            except Exception as e:
                print(f"시그널 연결 실패: {e}")
                # 대체 방법: 타이머 기반 변경 감지
                self.setup_company_change_monitor()
            
            # 콤보박스 옵션 업데이트
            self.update_company_selector()
            print("회사 선택 콤보박스 초기화 완료")

            header_layout.addWidget(company_label)
            header_layout.addWidget(self.company_selector)
            print("회사 라벨과 콤보박스 레이아웃에 추가 완료")

            # 회사별 사원 관리 버튼
            manage_employees_btn = QPushButton("👥 사원관리")
            manage_employees_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            manage_employees_btn.clicked.connect(self.open_company_employee_manager)
            header_layout.addWidget(manage_employees_btn)
            print("사원관리 버튼 생성 및 추가 완료")

            # 수당 관리 버튼
            allowance_btn = QPushButton("💰 수당관리")
            allowance_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            allowance_btn.clicked.connect(self.open_allowance_manager)
            header_layout.addWidget(allowance_btn)
            print("수당관리 버튼 생성 및 추가 완료")

            # 연차 관리 버튼
            annual_leave_btn = QPushButton("🗓️ 연차관리")
            annual_leave_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            annual_leave_btn.clicked.connect(self.open_annual_leave_manager)
            header_layout.addWidget(annual_leave_btn)
            print("연차관리 버튼 생성 및 추가 완료")

            header_layout.addStretch()  # 오른쪽으로 밀기
            print("stretch 추가 완료")

            parent_layout.addWidget(header_frame)
            print("header_frame을 parent_layout에 추가 완료")

            print("setup_company_header 성공적으로 완료")

        except Exception as e:
            print(f"setup_company_header 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_company_selector_activated(self, index):
        """콤보박스 선택 시 처리"""
        try:
            company_name = self.company_selector.currentText()
            if company_name:
                self.apply_company_settings(company_name)
                self.refresh_ui_for_company(company_name)
        except Exception as e:
            print(f"회사 선택 처리 오류: {e}")

    def on_company_selector_changed(self, index):
        """콤보박스 인덱스 변경 시 처리"""
        try:
            company_name = self.company_selector.currentText()
            if company_name:
                self.apply_company_settings(company_name)
                self.refresh_ui_for_company(company_name)
        except Exception as e:
            print(f"회사 변경 처리 오류: {e}")

    def setup_company_change_monitor(self):
        """타이머를 사용한 config.json 변경 감지"""
        self.company_check_timer = QTimer()
        self.company_check_timer.timeout.connect(self.check_company_changes)
        self.company_check_timer.start(2000)  # 2초마다 체크

    def check_company_changes(self):
        """config.json 변경 감지 및 UI 업데이트"""
        try:
            # config.json 변경 여부 확인
            current_mtime = os.path.getmtime('config.json')
            if not hasattr(self, '_last_config_mtime'):
                self._last_config_mtime = current_mtime
                return
            
            if current_mtime != self._last_config_mtime:
                print("config.json 변경 감지 - UI 업데이트")
                self._last_config_mtime = current_mtime
                self.load_config()
                self.update_company_selector()
                self.refresh_ui_for_company(self.company_selector.currentText())
        except Exception as e:
            print(f"config.json 체크 실패: {e}")

    def open_allowance_manager(self):
        """수당 관리 팝업 열기"""
        try:
            from allowance_manager import AllowanceManager

            dialog = AllowanceManager(self, self)
            dialog.exec()  # 실행 결과와 상관없이 리로드 (저장 후 X로 닫는 경우 포함)
            
            print("수당 관리 팝업 종료 - 데이터 리로드")
            self.load_master_data()
            
            # 마스터 데이터 위젯이 있으면 새로고침
            if hasattr(self, 'master_data_widget') and self.master_data_widget:
                self.master_data_widget.refresh_table()

        except Exception as e:
            QMessageBox.critical(self, "수당 관리 오류", f"수당 관리 팝업을 열 수 없습니다:\n{str(e)}")

    def open_annual_leave_manager(self):
        """연차 관리 팝업 열기"""
        try:
            if AnnualLeaveDialog is None:
                QMessageBox.warning(self, "연차 관리", "연차 관리 모듈을 불러올 수 없습니다.")
                return

            # 직원 데이터가 없으면 경고
            if not self.employee_data:
                QMessageBox.warning(self, "연차 관리", "직원 데이터가 없습니다. 먼저 직원을 등록해주세요.")
                return

            dialog = AnnualLeaveDialog(self.employee_data, self)
            dialog.exec()
            
            print("연차 관리 팝업 종료")

        except Exception as e:
            QMessageBox.critical(self, "연차 관리 오류", f"연차 관리 팝업을 열 수 없습니다:\n{str(e)}")

    def update_company_selector(self):
        """회사 목록으로 콤보박스 업데이트"""
        try:
            companies = self.get_available_companies()
            self.company_selector.clear()
            self.company_selector.addItems(companies)

            # 현재 선택된 회사 표시
            current_company = self.config_data.get("company_name", "")
            if current_company and current_company in companies:
                self.company_selector.setCurrentText(current_company)
            elif companies:
                # 선택된 회사가 없으면 첫 번째 회사 선택
                self.company_selector.setCurrentIndex(0)
                self.on_company_selected(companies[0])

        except Exception as e:
            print(f"회사 선택 콤보박스 업데이트 오류: {e}")

    def get_available_companies(self):
        """설정 파일에서 회사 목록 가져오기"""
        try:
            companies = []
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                company_data = config_data.get('companies', {})
                for company_id, company_info in company_data.items():
                    company_name = company_info.get("name", company_id)
                    if company_name:
                        companies.append(company_name)

            return companies if companies else ["기본 회사"]

        except Exception as e:
            print(f"회사 목록 가져오기 오류: {e}")
            return ["기본 회사"]

    def on_company_selected(self, company_name):
        """회사 선택 시 설정 및 데이터 업데이트"""
        if not company_name:
            return

        try:
            print(f"회사 선택됨: {company_name}")

            # 선택된 회사의 정보를 config_data에 설정
            self.apply_company_settings(company_name)

            # UI 업데이트 (테이블 새로고침 등)
            self.refresh_ui_for_company(company_name)

        except Exception as e:
            print(f"회사 선택 처리 오류: {e}")

    def on_company_data_changed(self):
        """회사 데이터 변경 시 호출되는 콜백"""
        # 무한 루프 방지를 위한 플래그
        if hasattr(self, '_updating_ui') and self._updating_ui:
            return

        try:
            self._updating_ui = True
            print("회사 데이터 변경 감지 - UI 자동 업데이트 시작")

            # 0. 최신 데이터 로드
            self.load_config()

            # UI가 초기화된 후에만 실행
            if hasattr(self, 'company_selector') and self.company_selector:
                # 1. 회사 선택 콤보박스 업데이트
                self.update_company_selector()
                print("콤보박스 갱신 완료")

                # 2. 현재 선택된 회사가 있으면 UI 새로고침
                current_company = self.company_selector.currentText()
                if current_company:
                    self.refresh_ui_for_company(current_company)
                    print(f"전체 UI 갱신 완료: {current_company}")
                else:
                    # 선택된 회사가 없으면 첫 번째 회사로 재설정 시도
                    self.update_company_selector()

            print("회사 데이터 변경 - UI 자동 업데이트 완료")

        except Exception as e:
            print(f"회사 데이터 변경 콜백 오류: {e}")
            # 예외 발생 시 강제 갱신 시도
            try:
                if hasattr(self, 'company_selector') and self.company_selector:
                    self.update_company_selector()
            except:
                pass
        finally:
            self._updating_ui = False

    def refresh_ui_for_company(self, company_name):
        """회사 선택 시 UI 새로고침 (개선된 버전)"""
        try:
            print(f"UI 새로고침 시작: {company_name}")

            # 1. 회사 설정 적용
            self.apply_company_settings(company_name)

            # 2. 직원 데이터 필터링
            self.filter_employees_by_company(company_name)

            # 3. 마스터 데이터 위젯 새로고침
            if hasattr(self, 'master_data_widget') and self.master_data_widget:
                self.master_data_widget.refresh_table()

            # 4. 월별 급여 패널 새로고침 (필요시)
            if hasattr(self, 'monthly_pane') and self.monthly_pane:
                # 월별 패널의 테이블 새로고침 로직 추가
                pass

            print(f"UI 새로고침 완료: {company_name}")

        except Exception as e:
            print(f"UI 새로고침 오류: {e}")

    def apply_company_settings(self, company_name):
        """선택된 회사의 설정을 현재 설정으로 적용"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                company_data = config_data.get('companies', {})

                # 선택된 회사 찾기
                selected_company_info = None
                for company_id, company_info in company_data.items():
                    if company_info.get("name") == company_name:
                        selected_company_info = company_info
                        break

                if selected_company_info:
                    # 회사 정보를 메인 config_data에 적용
                    self.config_data["company_name"] = selected_company_info.get("name", "")
                    self.config_data["company_business_size"] = selected_company_info.get("business_size", "over_5")
                    self.config_data["company_industry"] = selected_company_info.get("industry_type", "")
                    self.config_data["company_tax_office"] = selected_company_info.get("tax_office", "")
                    self.config_data["company_registration"] = selected_company_info.get("business_registration", "")

                    # 설정 저장
                    self.save_config()

                    print(f"회사 설정 적용 완료: {company_name}")

        except Exception as e:
            print(f"회사 설정 적용 오류: {e}")

    def refresh_ui_for_company(self, company_name):
        """회사 선택 시 UI 새로고침"""
        try:
            # 직원 데이터 필터링 (해당 회사의 직원만 표시)
            self.filter_employees_by_company(company_name)

            # 월별 급여 계산 패널 새로고침 (필요시)
            if hasattr(self, 'monthly_pane') and self.monthly_pane:
                # 월별 패널의 테이블 새로고침 로직 (필요시 구현)
                pass

            print(f"UI 새로고침 완료: {company_name}")

        except Exception as e:
            print(f"UI 새로고침 오류: {e}")

    def filter_employees_by_company(self, company_name):
        """선택된 회사의 직원만 필터링하여 표시"""
        try:
            # 회사 ID 찾기
            company_id = self.get_company_id_by_name(company_name)
            if not company_id:
                print(f"회사 ID를 찾을 수 없음: {company_name}")
                return

            # 직원 마스터 데이터에서 해당 회사 직원만 필터링
            if hasattr(self, 'master_data_widget') and self.master_data_widget:
                self.master_data_widget.filter_by_company(company_id)

            print(f"직원 필터링 완료: 회사 {company_name} (ID: {company_id})")

        except Exception as e:
            print(f"직원 필터링 오류: {e}")

    def get_company_id_by_name(self, company_name):
        """회사명으로 회사 ID 찾기"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                company_data = config_data.get('companies', {})
                for company_id, company_info in company_data.items():
                    if company_info.get("name") == company_name:
                        return company_id

            return None

        except Exception as e:
            print(f"회사 ID 찾기 오류: {e}")
            return None

    def open_company_employee_manager(self):
        """회사별 사원 관리 팝업 열기"""
        try:
            # 현재 선택된 회사 확인
            current_company = self.company_selector.currentText()
            if not current_company or current_company == "기본 회사":
                QMessageBox.warning(self, "회사 선택 필요", "먼저 회사를 선택해주세요.")
                return

            # 회사 ID 찾기
            company_id = self.get_company_id_by_name(current_company)
            if not company_id:
                QMessageBox.warning(self, "회사 찾기 실패", "선택된 회사를 찾을 수 없습니다.")
                return

            # 팝업 열기
            from employee_company_manager import CompanyEmployeeManager

            dialog = CompanyEmployeeManager(self, self, current_company, company_id)

            # 팝업이 닫힐 때 회사 변경 시그널 연결
            dialog.company_updated.connect(self.on_company_updated_from_popup)

            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "팝업 열기 오류", f"회사별 사원 관리 팝업을 열 수 없습니다:\n{str(e)}")

    def on_company_updated_from_popup(self, company_id):
        """팝업에서 회사 정보가 변경되었을 때 처리"""
        try:
            print(f"팝업에서 회사 업데이트됨: {company_id}")

            # 현재 선택된 회사가 변경된 회사라면 UI 새로고침
            current_company = self.company_selector.currentText()
            if current_company:
                company_id_current = self.get_company_id_by_name(current_company)
                if company_id_current == company_id:
                    # 직원 목록 새로고침
                    self.refresh_ui_for_company(current_company)

        except Exception as e:
            print(f"팝업 업데이트 처리 오류: {e}")

    def setup_main_content(self, parent_layout):
        """메인 컨텐츠 영역 설정 (스플리터)"""
        # 스플리터 생성
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 좌측: 직원 관리 패널
        self.master_pane = self.create_master_pane()
        splitter.addWidget(self.master_pane)

        # 우측: 급여 계산 패널
        self.monthly_pane = self.create_monthly_pane()
        splitter.addWidget(self.monthly_pane)

        # 스플리터 비율 설정
        splitter.setSizes([400, 1000])

        parent_layout.addWidget(splitter)

    def setup_status_bar(self):
        """상태바 설정"""
        self.status_bar = self.statusBar()

        # 라이선스 상태 표시
        self.license_status_label = QLabel("라이선스 정보 로딩 중...")
        self.status_bar.addWidget(self.license_status_label)

        # 라이선스 상태 인디케이터 (원형 아이콘)
        self.license_indicator = QLabel("●")
        self.license_indicator.setStyleSheet("color: gray; font-size: 16px;")
        self.status_bar.addPermanentWidget(self.license_indicator)

    def setup_menu(self):
        """메뉴 설정"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        exit_action = QAction('종료', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 설정 메뉴
        settings_menu = menubar.addMenu('설정')
        tax_settings_action = QAction('세무사 정보 설정', self)
        tax_settings_action.triggered.connect(self.open_tax_settings)
        settings_menu.addAction(tax_settings_action)

        # 세법 기준 관리 메뉴 추가
        tax_law_action = QAction('세법 기준 관리', self)
        tax_law_action.triggered.connect(self.open_tax_law_settings)
        settings_menu.addAction(tax_law_action)

        settings_menu.addSeparator()  # 구분선 추가

        license_action = QAction('라이선스 활성화', self)
        license_action.triggered.connect(self.show_activation_dialog)
        settings_menu.addAction(license_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말')
        tutorial_action = QAction('사용법 튜토리얼', self)
        tutorial_action.triggered.connect(self.start_tutorial)
        help_menu.addAction(tutorial_action)

        # 튜토리얼 바로가기 메뉴 (디버깅용)
        tutorial_shortcut_action = QAction('튜토리얼 시작 (F1)', self)
        tutorial_shortcut_action.setShortcut('F1')
        tutorial_shortcut_action.triggered.connect(self.start_tutorial)
        help_menu.addAction(tutorial_shortcut_action)

    def create_master_pane(self):
        """직원 관리 패널 생성"""
        from master_data_pane_qt import MasterDataPaneQt

        pane = QGroupBox("직원 마스터 관리")
        layout = QVBoxLayout(pane)
        self.master_data_widget = MasterDataPaneQt(self)  # 인스턴스 저장
        layout.addWidget(self.master_data_widget)

        return pane

    def create_monthly_pane(self):
        """급여 계산 패널 생성"""
        from monthly_payroll_pane_qt import MonthlyPayrollPaneQt

        pane = QGroupBox("월별 급여 계산")
        layout = QVBoxLayout(pane)
        layout.addWidget(MonthlyPayrollPaneQt(self))

        return pane

    def run_license_check(self):
        """라이선스 상태 확인"""
        # 프로그램 시작 시 기존 라이선스 마이그레이션 시도 (최초 1회만)
        if not hasattr(self, '_migration_attempted'):
            self._migration_attempted = True
            try:
                migration_result = license_verifier.LicenseManager.migrate_legacy_license()
                if migration_result:
                    print("기존 라이선스 마이그레이션 성공")
                else:
                    print("기존 라이선스 마이그레이션 불필요 또는 실패")
            except Exception as e:
                print(f"라이선스 마이그레이션 중 오류: {e}")

        # 라이선스 상태 확인
        status = license_verifier.check_license()

        if status == 'LICENSED':
            self.locked = False
            self._unlock_application_features()
        else:
            self.locked = True
            self._lock_application_features()

            # 미인증 상태에서 사용자 안내 대화상자 표시
            if status in ['NOT_LICENSED', 'INVALID_LICENSE']:
                self.show_unlicensed_user_dialog(status)

        self._update_license_status_display(status)

    def show_unlicensed_user_dialog(self, status):
        """미인증 사용자에게 안내 대화상자 표시"""
        dialog = QDialog(self)
        dialog.setWindowTitle("프로그램 라이선스 안내")
        dialog.setModal(True)
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)

        # 제목
        title_label = QLabel("⚖️ 급여명세서 관리 프로그램")
        title_label.setFont(QFont("맑은 고딕", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 안내 메시지
        if status == 'NOT_LICENSED':
            message = """
귀하의 컴퓨터는 아직 라이선스가 활성화되지 않았습니다.

본 프로그램은 세무사 전문 프로그램으로, 정식 라이선스 활성화 후에만
모든 기능을 사용할 수 있습니다.
"""
        else:  # INVALID_LICENSE
            message = """
라이선스 인증에 문제가 발생했습니다.

라이선스 파일이 손상되었거나 다른 컴퓨터에서 복사된 것으로 의심됩니다.
새로운 라이선스 활성화를 진행해주세요.
"""

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("맑은 고딕", 11))
        message_label.setStyleSheet("color: #495057; line-height: 1.5;")
        layout.addWidget(message_label)

        # 세무사 정보 표시
        tax_info_group = QGroupBox("담당 세무사 연락처")
        tax_layout = QVBoxLayout(tax_info_group)

        # 세무사 정보 가져오기
        tax_accountant_name = self.config_data.get("tax_accountant_name", "세무사")
        tax_office_name = self.config_data.get("tax_office_name", "세무회계사무소")
        tax_accountant_phone = self.config_data.get("tax_accountant_phone", "")
        tax_accountant_email = self.config_data.get("tax_accountant_email", "")
        tax_branch_name = self.config_data.get("tax_branch_name", "")

        # 세무서 정보
        office_text = tax_office_name
        if tax_branch_name:
            office_text += f" ({tax_branch_name})"

        office_label = QLabel(f"세무서: {office_text}")
        office_label.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        tax_layout.addWidget(office_label)

        # 세무사 이름
        name_label = QLabel(f"세무사: {tax_accountant_name}")
        name_label.setFont(QFont("맑은 고딕", 11, QFont.Weight.Bold))
        tax_layout.addWidget(name_label)

        # 연락처 정보
        contact_info = []
        if tax_accountant_phone:
            contact_info.append(f"📞 전화: {tax_accountant_phone}")
        if tax_accountant_email:
            contact_info.append(f"📧 이메일: {tax_accountant_email}")

        if contact_info:
            contact_text = "\n".join(contact_info)
            contact_label = QLabel(contact_text)
            contact_label.setFont(QFont("맑은 고딕", 10))
            contact_label.setStyleSheet("color: #007bff;")
            tax_layout.addWidget(contact_label)
        else:
            no_contact_label = QLabel("연락처 정보가 설정되지 않았습니다.")
            no_contact_label.setFont(QFont("맑은 고딕", 10))
            no_contact_label.setStyleSheet("color: #6c757d; font-style: italic;")
            tax_layout.addWidget(no_contact_label)

        layout.addWidget(tax_info_group)

        # 사용 방법 안내
        usage_group = QGroupBox("라이선스 활성화 방법")
        usage_layout = QVBoxLayout(usage_group)

        usage_text = """
1. 위 연락처로 세무사에게 문의하세요
2. 컴퓨터 정보를 제공받으세요
3. 라이선스 활성화 코드를 받아 입력하세요
4. 메뉴 [설정] → [라이선스 활성화]를 선택하세요
"""
        usage_label = QLabel(usage_text.strip())
        usage_label.setFont(QFont("맑은 고딕", 10))
        usage_label.setWordWrap(True)
        usage_layout.addWidget(usage_label)

        layout.addWidget(usage_group)

        # 버튼들
        button_layout = QHBoxLayout()

        # 라이선스 활성화 버튼
        activate_button = QPushButton("🔑 라이선스 활성화")
        activate_button.setFont(QFont("맑은 고딕", 10, QFont.Weight.Bold))
        activate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        activate_button.clicked.connect(lambda: self.open_activation_and_close(dialog))
        button_layout.addWidget(activate_button)

        # 나중에 하기 버튼
        later_button = QPushButton("나중에 하기")
        later_button.setFont(QFont("맑은 고딕", 10))
        later_button.clicked.connect(dialog.accept)
        button_layout.addWidget(later_button)

        # 프로그램 종료 버튼
        exit_button = QPushButton("프로그램 종료")
        exit_button.setFont(QFont("맑은 고딕", 10))
        exit_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        exit_button.clicked.connect(lambda: self.close_app(dialog))
        button_layout.addWidget(exit_button)

        layout.addLayout(button_layout)

        # 대화상자 표시
        dialog.exec()

    def open_activation_and_close(self, dialog):
        """라이선스 활성화 창 열고 현재 대화상자 닫기"""
        dialog.accept()
        self.show_activation_dialog()

    def close_app(self, dialog):
        """프로그램 종료"""
        dialog.accept()
        self.close()

    def show_activation_dialog(self):
        """라이선스 활성화 대화상자 표시"""
        from activation_dialog_qt import show_activation_dialog

        status = license_verifier.check_license()
        message = {
            'NOT_LICENSED': "프로그램을 사용하려면 활성화 코드가 필요합니다.",
            'EXPIRED': "라이선스가 만료되었습니다. 갱신하려면 새 활성화 코드를 입력하세요.",
            'INVALID_LICENSE': "라이선스가 유효하지 않습니다. 다시 활성화해주세요."
        }.get(status, "라이선스 활성화 코드를 입력해주세요.")

        activation_code = show_activation_dialog(self, message)

        if activation_code:
            self.process_activation(activation_code)

    def process_activation(self, activation_code):
        """라이선스 코드 처리"""
        status, data = license_verifier.verify_activation_code(activation_code)
        if status == 'SUCCESS':
            expiry_date_str = data
            hw_id = hardware_id.get_machine_id()
            if not hw_id:
                QMessageBox.critical(self, "치명적 오류", "컴퓨터의 고유 ID를 가져올 수 없습니다.")
                return

            # 새로운 분리된 라이선스 시스템으로 세무사 라이선스 생성
            success = license_verifier.LicenseManager.create_license_v2(
                expiry_date_str, hw_id, license_verifier.LicenseType.TAX_ACCOUNTANT
            )

            if success:
                QMessageBox.information(self, "활성화 성공",
                    "라이선스가 성공적으로 활성화되었습니다!\n\n"
                    "⚠️ 프로그램을 다시 시작해야 변경사항이 적용됩니다.\n\n"
                    "프로그램을 종료한 후 다시 실행해주세요.\n"
                    "(메뉴 [파일] → [종료] 또는 창 닫기)")
                # 자동 재시작 제거 - 사용자 수동 재시작 유도
            else:
                QMessageBox.critical(self, "활성화 실패", "라이선스 파일 생성에 실패했습니다.")
        else:
            error_messages = {'CODE_EXPIRED': "활성화 코드의 유효 시간이 만료되었습니다.", 'INVALID_SIGNATURE': "활성화 코드가 유효하지 않습니다.", 'PUBLIC_KEY_NOT_FOUND': "인증에 필요한 키 파일이 없습니다.", 'UNKNOWN_ERROR': "알 수 없는 오류로 활성화에 실패했습니다."}
            message = error_messages.get(status, "알 수 없는 오류로 활성화에 실패했습니다.")
            QMessageBox.critical(self, "활성화 실패", message)



    def open_tax_settings(self):
        """세무사 설정 창 열기"""
        from tax_settings_qt import PasswordDialogQt, TaxSettingsDialogQt

        # 비밀번호 입력 대화상자 표시
        password_dialog = PasswordDialogQt(self, None)  # 콜백 없이 생성
        password_dialog.exec()

        # 비밀번호 검증 성공 시 설정 창 열기
        password = password_dialog.get_password()
        if password:
            dialog = TaxSettingsDialogQt(self, self, password)
            dialog.exec()

    def open_tax_law_settings(self):
        """세법 기준 설정 창 열기"""
        from tax_law_settings_dialog import show_tax_law_settings

        # 세법 기준 설정 다이얼로그 표시
        show_tax_law_settings(self)

    def _lock_application_features(self):
        """기능 제한 적용"""
        self.setWindowTitle(f"{self.title} - [기능 제한]")

        # TODO: 실제 UI 컴포넌트 비활성화 로직 구현

    def _unlock_application_features(self):
        """기능 제한 해제"""
        self.setWindowTitle(self.title)

        # TODO: 실제 UI 컴포넌트 활성화 로직 구현

    def start_tutorial(self):
        """튜토리얼 시작"""
        print("튜토리얼 시작 함수 호출됨")  # 디버깅용

        if not start_tutorial:
            print("start_tutorial 함수가 None입니다")  # 디버깅용
            QMessageBox.warning(self, "튜토리얼 오류", "튜토리얼 모듈을 불러올 수 없습니다.")
            return

        try:
            print("튜토리얼 엔진 시작 시도")  # 디버깅용
            # 튜토리얼 엔진 시작
            engine = start_tutorial(self)
            print(f"튜토리얼 엔진 생성됨: {engine}")  # 디버깅용

            # 튜토리얼 완료 시그널 연결
            if hasattr(engine, 'tutorial_completed'):
                engine.tutorial_completed.connect(self.on_tutorial_completed)
                print("튜토리얼 완료 시그널 연결됨")  # 디버깅용
            else:
                print("tutorial_completed 속성이 없음")  # 디버깅용

        except Exception as e:
            print(f"튜토리얼 시작 중 오류: {e}")  # 디버깅용
            QMessageBox.critical(self, "튜토리얼 오류", f"튜토리얼을 시작할 수 없습니다:\n{str(e)}")

    def on_tutorial_completed(self):
        """튜토리얼 완료 처리"""
        QMessageBox.information(
            self, "튜토리얼 완료",
            "튜토리얼이 완료되었습니다!\n\n"
            "이제 실제 업무에 프로그램을 사용해보세요.\n"
            "궁금한 점이 있으시면 도움말을 참고해주세요."
        )

    def _update_license_status_display(self, status):
        """라이선스 상태 표시 업데이트 - 타입 구분 및 만료일 표시"""
        status_text_map = {
            'LICENSED': "라이선스 활성화됨",
            'EXPIRED': "라이선스 만료",
            'INVALID_LICENSE': "인증 실패",
            'NOT_LICENSED': "미인증 (기능 제한)"
        }

        color_map = {
            'LICENSED': "green",
            'EXPIRED': "red",
            'INVALID_LICENSE': "red",
            'NOT_LICENSED': "orange"
        }

        # 라이선스 타입 및 만료 정보 추출
        license_info = self._get_current_license_info()
        current_text = status_text_map.get(status, "상태 확인 중...")

        if status == 'LICENSED' and license_info:
            license_type_text = "세무사용" if license_info['type'] == 'TAX_ACCOUNTANT' else "고객용"
            expiry_date = license_info['expiry_date']
            days_left = license_info['days_left']

            # 상세 정보 표시
            current_text = f"{license_type_text} (만료일: {expiry_date}, 남은 일수: {days_left}일)"

            # 남은 일수에 따른 상태 조정
            if days_left < 0:
                current_text = f"{license_type_text} 라이선스 만료 (만료일: {expiry_date})"
                status = 'EXPIRED'
            elif days_left <= 7:
                # 일주일 이내 만료 시 주의 표시
                current_text = f"{license_type_text} (만료일: {expiry_date}, 남은 일수: {days_left}일 ⚠️)"
                # 색상은 그대로 유지하되 텍스트에 경고 표시

        elif license_info and license_info['type']:
            # 라이선스 파일은 있지만 상태가 정상이 아닌 경우
            license_type_text = "세무사용" if license_info['type'] == 'TAX_ACCOUNTANT' else "고객용"
            current_text = f"{license_type_text} {status_text_map.get(status, '상태 확인 중...')}"

        self.license_status_label.setText(current_text)
        self.license_indicator.setStyleSheet(f"color: {color_map.get(status, 'gray')}; font-size: 16px;")

        # 창 제목에도 라이선스 타입 표시
        if license_info and license_info['type'] == 'TAX_ACCOUNTANT':
            self.setWindowTitle(f"{self.title} - 세무사용")
        elif license_info and license_info['type'] == 'CUSTOMER':
            self.setWindowTitle(f"{self.title} - 고객용")
        else:
            self.setWindowTitle(self.title)

    def _get_current_license_info(self):
        """현재 활성화된 라이선스 정보를 반환"""
        try:
            # 세무사 라이선스 우선 확인
            tax_status = license_verifier.LicenseManager.check_license_v2(
                license_verifier.LicenseType.TAX_ACCOUNTANT
            )
            if tax_status == 'LICENSED':
                expiry_date, days_left = self._extract_license_details('TAX_ACCOUNTANT')
                return {
                    'type': 'TAX_ACCOUNTANT',
                    'expiry_date': expiry_date,
                    'days_left': days_left
                }

            # 세무사 라이선스가 없으면 고객 라이선스 확인
            hw_id = hardware_id.get_machine_id()
            if hw_id:
                customer_status = license_verifier.LicenseManager.check_license_v2(
                    license_verifier.LicenseType.CUSTOMER, hw_id
                )
                if customer_status == 'LICENSED':
                    expiry_date, days_left = self._extract_license_details('CUSTOMER')
                    return {
                        'type': 'CUSTOMER',
                        'expiry_date': expiry_date,
                        'days_left': days_left
                    }

            return None

        except Exception as e:
            print(f"라이선스 정보 추출 오류: {e}")
            return None

    def _extract_license_details(self, license_type):
        """라이선스 파일에서 만료일과 남은 일수를 추출"""
        try:
            from datetime import datetime

            if license_type == 'TAX_ACCOUNTANT':
                # 세무사 라이선스 파일 경로
                license_dir, license_file = license_verifier.LicenseManager.get_license_paths(
                    license_verifier.LicenseType.TAX_ACCOUNTANT
                )
            else:
                # 고객 라이선스 파일 경로
                hw_id = hardware_id.get_machine_id()
                if not hw_id:
                    return "알 수 없음", 0
                license_dir, license_file = license_verifier.LicenseManager.get_license_paths(
                    license_verifier.LicenseType.CUSTOMER, hw_id
                )

            if not os.path.exists(license_file):
                return "알 수 없음", 0

            # 파일 복호화 및 정보 추출
            from cryptography.fernet import Fernet

            hw_id = hardware_id.get_machine_id()
            if not hw_id:
                return "알 수 없음", 0

            encryption_key = license_verifier._get_encryption_key(hw_id)
            f = Fernet(encryption_key)

            with open(license_file, "rb") as license_file_obj:
                encrypted_data = license_file_obj.read()

            decrypted_data = f.decrypt(encrypted_data).decode('utf-8')
            parts = {k: v for k, v in (item.split(':', 1) for item in decrypted_data.split('|'))}
            expiry_date_str = parts.get('expires', '알 수 없음')

            if expiry_date_str and expiry_date_str != '알 수 없음':
                # 만료일 파싱
                try:
                    expiration_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
                    today = datetime.now().date()
                    days_left = (expiration_date - today).days
                    return expiry_date_str, days_left
                except ValueError:
                    return expiry_date_str, 0

            return expiry_date_str, 0

        except Exception as e:
            print(f"라이선스 세부 정보 추출 오류: {e}")
            return "알 수 없음", 0

    def load_config(self):
        """설정 파일 로드"""
        try:
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            else:
                self.config_data = {}

            # UI가 초기화된 경우에만 라벨 업데이트
            if hasattr(self, 'display_company_name_label') and self.display_company_name_label:
                company_name = self.config_data.get("company_name", "회사 이름 없음")
                self.display_company_name_label.setText(company_name)
                print(f"메인 화면 회사명 업데이트: {company_name}")
            else:
                print("display_company_name_label이 아직 초기화되지 않음")
        except Exception as e:
            print(f"설정 파일 로드 오류: {e}")
            self.config_data = {}

    def save_config(self):
        """설정 파일 저장"""
        try:
            import json
            print(f"설정 파일 저장 시도: {self.config_file}")

            # 현재 파일의 데이터를 먼저 읽어서 CompanyManager가 저장한
            # companies 데이터 등을 보존
            existing_data = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, Exception):
                    existing_data = {}

            # 현재 메모리의 설정값으로 업데이트
            # companies와 tax_law_standards는 파일에 있는 최신 버전을 우선순위로 둠
            companies_backup = existing_data.get('companies', {})
            tax_law_backup = existing_data.get('tax_law_standards', {})

            # 기본적으로 현재 메모리의 config_data를 사용
            save_data = self.config_data.copy()

            # 파일에 있는 중요 데이터를 덮어쓰지 않도록 복원 (메모리에 없을 경우만 혹은 항상 최신 유지)
            # 여기서는 파일에 있는 것이 다른 매니저에 의해 수정된 최신본일 가능성이 높음
            if companies_backup:
                save_data['companies'] = companies_backup
            if tax_law_backup:
                save_data['tax_law_standards'] = tax_law_backup

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)

            # 저장 후 내부 메모리 데이터도 동기화
            self.config_data = save_data

            print(f"설정 파일 저장 성공: {len(self.config_data)}개 항목 (회사 정보 보존됨)")
            return True

        except PermissionError as e:
            error_msg = f"설정 파일 쓰기 권한이 없습니다: {e}"
            print(f"설정 파일 저장 오류: {error_msg}")
            QMessageBox.critical(None, "저장 오류", error_msg)
            return False
        except Exception as e:
            error_msg = f"설정 파일 저장 중 오류 발생: {e}"
            print(f"설정 파일 저장 오류: {error_msg}")
            QMessageBox.critical(None, "저장 오류", error_msg)
            return False

    def load_master_data(self):
        """직원 마스터 데이터 로드"""
        try:
            if os.path.exists(self.employees_file):
                import json
                with open(self.employees_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.employee_data = data.get("employees", {})
                    # 빈 키 제거
                    self.employee_data = {k: v for k, v in self.employee_data.items() if k.strip()}
                    self.global_payment_date_var = data.get("payment_date", "")
        except Exception as e:
            print(f"직원 데이터 로드 오류: {e}")
            self.employee_data = {}

        # 데이터 로드 완료 (테이블 업데이트는 setup_ui 후에 수행)

    def save_master_data(self, silent=False):
        """직원 마스터 데이터 저장"""
        try:
            import json
            data_to_save = {"payment_date": self.global_payment_date_var, "employees": self.employee_data}
            with open(self.employees_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            if not silent:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "성공", "직원 정보가 저장되었습니다.")
            return True
        except Exception as e:
            print(f"직원 데이터 저장 오류: {e}")
            if not silent:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "오류", f"직원 정보 저장 실패: {e}")
            return False

    def format_month_string(self, month_str):
        """월 문자열을 YYYY년 MM월 형식으로 변환 (tkinter 버전과 호환)"""
        try:
            year, month = map(int, month_str.split('-'))
            return f"{year}년 {month}월"
        except (ValueError, TypeError):
            return month_str

    def setup_custom_temp_dir(self):
        """PyInstaller 영향권 밖으로 TMP 완전 격리 (최종 해결책)"""
        try:
            # PyInstaller가 접근할 수 없는 경로로 TMP 완전 격리
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller 실행 환경: 실행 파일 디렉토리 사용
                exe_dir = os.path.dirname(sys.executable)
                isolated_temp = os.path.join(exe_dir, 'isolated_temp')
            else:
                # 개발 환경: 현재 디렉토리 사용
                isolated_temp = os.path.join(os.getcwd(), 'isolated_temp')

            # Hook 충돌 방지 확인
            hook_already_set = os.environ.get('PYINSTALLER_HOOK_TMP_SET', '0') == '1'

            current_tmp = os.environ.get('TMP', '')

            # Hook이 이미 설정했고 동일 격리 경로라면 중복 설정 방지
            if hook_already_set and isolated_temp in current_tmp:
                print(f"Hook에 의해 TMP 이미 격리 설정됨: {current_tmp}")
                return

            # 격리된 디렉토리 생성 (PyInstaller 영향권 밖)
            try:
                os.makedirs(isolated_temp, exist_ok=True)
                # 접근 권한 확인
                test_file = os.path.join(isolated_temp, 'test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except (PermissionError, OSError) as e:
                print(f"격리 TMP 생성 실패, 시스템 기본값 사용: {e}")
                # 실패 시에도 계속 진행 (중요)
                isolated_temp = os.environ.get('TMP', os.environ.get('TEMP', 'C:\\Temp'))

            # 환경변수 설정 (PyInstaller 범위 밖)
            os.environ['TMP'] = isolated_temp
            os.environ['TEMP'] = isolated_temp
            os.environ['TMPDIR'] = isolated_temp

            # tempfile 모듈 설정
            import tempfile
            tempfile.tempdir = isolated_temp

            print(f"PyInstaller 영향권 밖 TMP 격리 완료: {isolated_temp}")

        except Exception as e:
            print(f"TMP 격리 실패, 시스템 기본값 유지: {e}")
            # 실패해도 프로그램 계속 실행 (중요!)

        # PyInstaller 정리 메커니즘 안전하게 설정 (추가 안전장치)
        self._setup_safe_pyinstaller_cleanup()

    def _setup_safe_pyinstaller_cleanup(self):
        """PyInstaller 임시 디렉토리 정리를 안전하게 관리"""
        try:
            import shutil
            import os
            import tempfile
            from datetime import datetime, timedelta

            # 현재 프로그램의 _MEI 디렉토리만 추적
            current_mei_dir = getattr(sys, '_MEIPASS', None)
            if current_mei_dir and '_MEI' in current_mei_dir:
                self.current_mei_dir = current_mei_dir
                print(f"현재 _MEI 디렉토리 추적: {current_mei_dir}")

            # 조건부 패치: 현재 실행 중인 _MEI 디렉토리만 보호
            original_rmtree = shutil.rmtree
            def selective_rmtree(path, *args, **kwargs):
                path_str = str(path)

                # 현재 실행 중인 _MEI 디렉토리는 보호
                if hasattr(self, 'current_mei_dir') and self.current_mei_dir in path_str:
                    print(f"현재 실행 중인 _MEI 디렉토리 삭제 방지: {path_str}")
                    return  # 삭제하지 않음

                # 다른 _MEI 디렉토리는 시간 기반 검사 후 정리 허용
                if '_MEI' in path_str:
                    try:
                        # 디렉토리 생성 시간 확인
                        stat = os.stat(path)
                        created_time = datetime.fromtimestamp(stat.st_ctime)
                        current_time = datetime.now()

                        # 5분 이상 된 오래된 _MEI 폴더만 삭제 허용
                        if current_time - created_time > timedelta(minutes=5):
                            print(f"오래된 _MEI 폴더 삭제 허용: {path_str}")
                            return original_rmtree(path, *args, **kwargs)
                        else:
                            print(f"최근 _MEI 폴더 삭제 방지: {path_str}")
                            return  # 삭제하지 않음
                    except:
                        # 시간 확인 실패 시 안전하게 삭제 방지
                        print(f"_MEI 폴더 시간 확인 실패, 삭제 방지: {path_str}")
                        return

                # 일반 디렉토리는 정상 삭제
                return original_rmtree(path, *args, **kwargs)

            shutil.rmtree = selective_rmtree

            # os.remove도 유사하게 처리
            original_remove = os.remove
            def selective_remove(path):
                path_str = str(path)

                # _MEI 관련 파일은 조심스럽게 처리
                if '_MEI' in path_str:
                    try:
                        # 현재 실행 중인 파일인지 확인 (간단한 휴리스틱)
                        if hasattr(self, 'current_mei_dir') and self.current_mei_dir in path_str:
                            print(f"현재 실행 중인 _MEI 파일 삭제 방지: {path_str}")
                            return
                    except:
                        pass

                    # 다른 _MEI 파일은 삭제 허용 (보통 개별 파일 삭제는 안전)
                    print(f"_MEI 파일 삭제 허용: {path_str}")

                return original_remove(path)

            os.remove = selective_remove

            print("PyInstaller 정리 메커니즘 선택적 보호 설정 완료")

        except Exception as e:
            print(f"PyInstaller 정리 보호 설정 실패: {e}")

    def _cleanup_on_exit(self):
        """프로그램 종료 시 안전한 임시 파일 정리"""
        try:
            print("프로그램 종료 시 정리 시작")

            # 현재 실행 중인 _MEI 디렉토리 제외하고 정리
            import tempfile
            import glob
            from datetime import datetime, timedelta

            import tempfile
            temp_base = tempfile.gettempdir()
            current_time = datetime.now()

            # _MEI* 디렉토리 찾아서 안전하게 정리
            mei_pattern = os.path.join(temp_base, '_MEI*')
            mei_dirs = glob.glob(mei_pattern)

            for mei_dir in mei_dirs:
                try:
                    if not os.path.exists(mei_dir):
                        continue

                    # 현재 실행 중인 _MEI 디렉토리는 정리하지 않음
                    if hasattr(self, 'current_mei_dir') and self.current_mei_dir and self.current_mei_dir in mei_dir:
                        print(f"현재 실행 중인 _MEI 디렉토리 유지: {mei_dir}")
                        continue

                    # 디렉토리 생성 시간 확인
                    try:
                        stat = os.stat(mei_dir)
                        created_time = datetime.fromtimestamp(stat.st_ctime)

                        # 10분 이상 된 오래된 폴더만 정리 (프로그램 종료 시 더 관대하게)
                        if current_time - created_time > timedelta(minutes=10):
                            import shutil
                            shutil.rmtree(mei_dir, ignore_errors=True)
                            print(f"프로그램 종료 시 오래된 _MEI 폴더 정리 완료: {mei_dir}")
                        else:
                            print(f"최근 _MEI 폴더 유지: {mei_dir}")

                    except Exception as time_error:
                        # 시간 확인 실패 시 안전하게 유지
                        print(f"_MEI 폴더 시간 확인 실패, 유지: {mei_dir} - {time_error}")

                except Exception as e:
                    # 정리 실패해도 프로그램 종료 진행
                    print(f"_MEI 폴더 정리 실패 (무시): {mei_dir} - {e}")

            print("프로그램 종료 시 정리 완료")

        except Exception as e:
            # 모든 예외 무시 - 정리 실패가 프로그램 종료를 막아서는 안됨
            print(f"프로그램 종료 시 정리 중 오류 (무시): {e}")

    def _cleanup_existing_temp_files(self):
        """기존 PyInstaller 임시 파일 안전하게 정리 (재시작 전)"""
        try:
            import tempfile
            import glob

            import tempfile
            temp_base = tempfile.gettempdir()

            # _MEI* 디렉토리 찾아서 안전하게 정리
            mei_pattern = os.path.join(temp_base, '_MEI*')
            mei_dirs = glob.glob(mei_pattern)

            for mei_dir in mei_dirs:
                try:
                    if os.path.exists(mei_dir):
                        # 안전하게 삭제 (하위 파일들만)
                        for item in os.listdir(mei_dir):
                            item_path = os.path.join(mei_dir, item)
                            try:
                                if os.path.isfile(item_path):
                                    os.remove(item_path)
                            except:
                                pass

                        # 디렉토리 자체는 남겨두기 (PyInstaller 재사용 가능)
                        print(f"임시 파일 정리 완료: {mei_dir}")

                except Exception as e:
                    print(f"임시 파일 정리 실패 (무시): {mei_dir} - {e}")

        except Exception as e:
            print(f"임시 파일 정리 중 오류: {e}")



    def is_windows_dark_mode(self):
        """윈도우 다크 모드 감지"""
        try:
            import winreg
            # 윈도우 레지스트리에서 다크 모드 설정 확인
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0  # 0 = 다크 모드 활성화
        except Exception as e:
            print(f"다크 모드 감지 오류: {e}")
            return False

    def apply_modern_styles(self):
        """모던 스타일시트 적용 (다크 모드 지원)"""
        # 다크 모드 감지
        is_dark_mode = self.is_windows_dark_mode()

        if is_dark_mode:
            # 다크 모드용 스타일시트
            modern_stylesheet = """
            /* 다크 모드 메인 윈도우 */
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }

            /* 다크 모드 그룹 박스 */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: #3c3c3c;
                color: #ffffff;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #ffffff;
                font-size: 14px;
            }

            /* 다크 모드 버튼 */
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }

            QPushButton:pressed {
                background-color: #3d8b40;
            }

            QPushButton:disabled {
                background-color: #666666;
                color: #cccccc;
            }

            /* 다크 모드 입력 필드 */
            QLineEdit, QTextEdit, QComboBox {
                padding: 6px 8px;
                border: 1px solid #666666;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
            }

            QLineEdit:focus, QTextEdit:focus {
                border-color: #4CAF50;
                outline: none;
            }

            /* 다크 모드 라벨 */
            QLabel {
                color: #ffffff;
            }

            /* 다크 모드 테이블 */
            QTableWidget {
                gridline-color: #555555;
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
            }

            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #555555;
                color: #ffffff;
            }

            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #2b2b2b;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #555555;
                font-weight: bold;
                color: #ffffff;
            }

            /* 다크 모드 스플리터 */
            QSplitter::handle {
                background-color: #555555;
            }

            QSplitter::handle:horizontal {
                width: 2px;
            }

            /* 다크 모드 스크롤바 */
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 6px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #888888;
            }

            /* 다크 모드 상태바 */
            QStatusBar {
                background-color: #2b2b2b;
                border-top: 1px solid #555555;
                color: #ffffff;
            }

            QStatusBar QLabel {
                color: #cccccc;
            }

            /* 다크 모드 메뉴 바 - 메뉴 텍스트가 보이도록 흰색 지정 */
            QMenuBar {
                background-color: #2b2b2b;
                border-bottom: 1px solid #555555;
                padding: 4px;
                color: #ffffff;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 4px 8px;
                border-radius: 4px;
                color: #ffffff;  /* 메뉴 텍스트를 흰색으로 명시적 지정 */
            }

            QMenuBar::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }

            /* 다크 모드 메뉴 */
            QMenu {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
            }

            QMenu::item {
                padding: 6px 20px;
                border-radius: 2px;
                color: #ffffff;
            }

            QMenu::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }

            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 4px 0;
            }
            """
        else:
            # 라이트 모드용 스타일시트 (기존 스타일)
            modern_stylesheet = """
        /* 메인 윈도우 */
        QMainWindow {
            background-color: #f8f9fa;
            color: #2c3e50;
        }

        /* 그룹 박스 */
        QGroupBox {
            font-weight: bold;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            margin-top: 1ex;
            background-color: white;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            color: #495057;
            font-size: 14px;
        }

        /* 버튼 스타일링 */
        QPushButton {
            background-color: #4CAF50;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QPushButton:pressed {
            background-color: #3d8b40;
        }

        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }

        /* 입력 필드 */
        QLineEdit, QTextEdit, QComboBox {
            padding: 6px 8px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
            color: #495057;
        }

        QLineEdit:focus, QTextEdit:focus {
            border-color: #4CAF50;
            outline: none;
        }

        /* 라벨 */
        QLabel {
            color: #495057;
        }

        /* 테이블 */
        QTableWidget {
            gridline-color: #dee2e6;
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }

        QTableWidget::item {
            padding: 4px;
            border-bottom: 1px solid #f8f9fa;
        }

        QTableWidget::item:selected {
            background-color: #e8f5e8;
        }

        QHeaderView::section {
            background-color: #f8f9fa;
            padding: 8px;
            border: none;
            border-bottom: 1px solid #dee2e6;
            font-weight: bold;
            color: #495057;
        }

        /* 스플리터 */
        QSplitter::handle {
            background-color: #dee2e6;
        }

        QSplitter::handle:horizontal {
            width: 2px;
        }

        /* 스크롤바 */
        QScrollBar:vertical {
            background-color: #f8f9fa;
            width: 12px;
            border-radius: 6px;
        }

        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 6px;
            min-height: 30px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }

        /* 상태바 */
        QStatusBar {
            background-color: #f8f9fa;
            border-top: 1px solid #dee2e6;
        }

        QStatusBar QLabel {
            color: #6c757d;
        }

        /* 메뉴 바 */
        QMenuBar {
            background-color: white;
            border-bottom: 1px solid #dee2e6;
            padding: 4px;
        }

        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
            border-radius: 4px;
        }

        QMenuBar::item:selected {
            background-color: #e8f5e8;
        }

        /* 메뉴 */
        QMenu {
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }

        QMenu::item {
            padding: 6px 20px;
            border-radius: 2px;
        }

        QMenu::item:selected {
            background-color: #e8f5e8;
        }

        QMenu::separator {
            height: 1px;
            background-color: #dee2e6;
            margin: 4px 0;
        }
        """

        self.setStyleSheet(modern_stylesheet)

    def closeEvent(self, event):
        """앱 종료 이벤트 - 안전한 정리 수행"""
        try:
            print("프로그램 종료: 데이터 저장 및 정리 시작")

            # 데이터 저장
            self.save_config()
            self.save_master_data(silent=True)

            # 프로그램 종료 시 안전한 임시 파일 정리
            self._cleanup_on_exit()

            print("프로그램 종료: 정리 완료")
            event.accept()

        except Exception as e:
            print(f"프로그램 종료 중 오류 (무시): {e}")
            event.accept()  # 오류가 있어도 종료 진행




def main():
    """메인 함수"""
    try:
        print("프로그램 시작: QApplication 생성 시도")
        app = QApplication(sys.argv)
        print("QApplication 생성 성공")

        # 앱 스타일 설정
        app.setStyle('Fusion')  # 모던 스타일
        print("앱 스타일 설정 완료")

        print("메인 윈도우 생성 시도")
        window = PayslipQtApp()
        print("메인 윈도우 생성 성공")

        print("메인 윈도우 표시 시도")
        window.show()
        print("메인 윈도우 표시 성공")

        print("Qt 이벤트 루프 시작")
        result = app.exec()
        print(f"프로그램 정상 종료: {result}")

        sys.exit(result)

    except Exception as e:
        print(f"프로그램 실행 중 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()

        # 예외 상황에서는 QMessageBox 대신 콘솔 출력만 사용 (더 안전)
        print("\n" + "="*50)
        print("프로그램 실행 중 치명적 오류가 발생했습니다!")
        print("오류 메시지:", str(e))
        print("자세한 오류 정보는 위의 트레이스백을 확인해주세요.")
        print("="*50)

        # QMessageBox는 사용하지 않음 (QApplication 상태 불확실)
        # 대신 프로그램 즉시 종료

        sys.exit(1)


if __name__ == "__main__":
    main()
