#!/usr/bin/env python3
"""
PyQt6 기반 고객용 튜토리얼 시스템
급여명세서 생성 프로그램 튜토리얼 모드
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import QMessageBox, QApplication
import os

from tutorial_overlay import TutorialOverlay


class TutorialStep:
    """튜토리얼 단계 데이터 클래스"""

    def __init__(self, step_id, title, description, validation_func=None,
                 clickable_widget=None):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.validation_func = validation_func
        self.clickable_widget = clickable_widget


class TutorialEngine(QObject):
    """튜토리얼 진행 엔진"""

    tutorial_completed = pyqtSignal()
    _current_instance = None  # 현재 실행 중인 튜토리얼 인스턴스 추적

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.current_step = 0
        self.overlay = None
        self.guide_box = None  # 안내 박스 추가
        self.steps = self.define_steps()
        self.validation_timer = None
        self._is_creating_overlay = False  # 오버레이 생성 중 플래그

    def define_steps(self):
        """튜토리얼 단계 정의"""
        return [
            TutorialStep(
                1,
                "프로그램 소개",
                """안녕하세요! 급여명세서 관리 프로그램 튜토리얼에 오신 것을 환영합니다.

이 튜토리얼에서는 급여 계산부터 명세서 생성까지의 전체 과정을 단계별로 안내해 드리겠습니다.

준비되셨으면 '다음' 버튼을 클릭해주세요."""
            ),

            TutorialStep(
                2,
                "샘플 데이터 준비",
                """튜토리얼에서는 미리 준비된 샘플 데이터를 사용합니다.

프로그램 폴더에 있는 'tutorial_data.xlsx' 파일을 사용하여
급여 계산 과정을 체험해보겠습니다.

이 파일에는 5명의 직원(홍길동, 영희, 철수, 이순신, 진희)의
11월 근태 데이터가 포함되어 있습니다."""
            ),

            TutorialStep(
                3,
                "급여 데이터 파일 선택",
                """이제 실제 급여 데이터를 불러와보겠습니다.

오른쪽 '월별 급여 계산' 패널에서 '📁 파일 선택' 버튼을 클릭하여
tutorial_data.xlsx 파일을 선택해주세요.

파일을 선택하면 프로그램이 자동으로 파일을 분석하여
사용 가능한 월 정보를 표시합니다.

파일 선택이 완료되면 아래의 '다음 ▶' 버튼을 클릭하여
다음 단계로 진행해주세요.""",
                self.validate_file_selected, clickable_widget="file_select_button"
            ),

            TutorialStep(
                4,
                "급여 데이터 계산",
                """이제 선택한 파일의 급여 데이터를 계산해보겠습니다.

오른쪽 '월별 급여 계산' 패널에서 계산 연월을 확인하고
'📊 급여 계산' 버튼을 클릭하여 급여 데이터를 계산해주세요.

프로그램이 자동으로 다음과 같은 항목들을 계산합니다:
• 홍길동, 철수, 영희, 이순신, 진희 등 5명의 직원 데이터
• 11월 근무시간, 야간근무, 휴일근무 기록
• 주휴 수당 (주 15시간 이상 근무 시)

급여 계산이 완료되면 아래의 '다음 ▶' 버튼을 클릭하여
다음 단계로 진행해주세요.""",
                self.validate_payroll_calculated, clickable_widget="calc_button"
            ),

            TutorialStep(
                5,
                "직원 목록 불러오기",
                """급여 데이터에서 직원 정보를 불러와보겠습니다.

왼쪽 '직원 마스터 관리' 패널에서 '급여에서 가져오기' 버튼을 클릭하여
홍길동, 영희, 철수, 이순신, 진희 등 5명의 직원 목록을 불러오세요.

버튼을 클릭하면 급여 데이터에 있는 직원들이 자동으로 추가됩니다.""",
                self.validate_employee_list, clickable_widget="import_button"
            ),

            TutorialStep(
                6,
                "직원 정보 보완 - 부서・직급",
                """이제 각 직원의 추가 정보를 입력해보겠습니다.

목록에서 첫 번째 직원(홍길동)을 선택하고,
부서와 직급 정보를 입력해주세요.

예시:
- 부서: 개발팀, 영업팀, 디자인팀 중 선택
- 직급: 사원, 주임, 대리, 과장, 차장, 부장 중 선택

정보를 입력한 후에는 반드시 저장해주세요.""",
                self.validate_employee_info,
                clickable_widget="master_pane"
            ),

            TutorialStep(
                7,
                "직원 정보 보완 - 입사일・지급일",
                """이제 각 직원의 입사일과 급여 지급일을 설정해보겠습니다.

직원별로 다음 정보를 입력해주세요:

1. 입사일 설정:
   - 과거 날짜를 선택하여 직원의 입사일을 입력합니다.
   - 예: 홍길동의 입사일이 2020년 1월 15일이라면 2020-01-15로 설정
   - 날짜 입력 필드에 직접 입력하거나 달력에서 선택 가능

2. 급여 지급일 설정:
   - 매월 급여를 지급할 날짜를 선택합니다 (1-31일)
   - 예: 매월 15일에 급여를 지급한다면 15로 설정
   - 말일 지급인 경우 31로 설정 (말일 자동 조정)

3. 날짜 조정 기능:
   - 날짜 입력 필드 옆의 ◀ ▶ 버튼으로 연/월/일을 개별 조정 가능
   - 달력 팝업에서 날짜를 선택할 수도 있습니다
   - 휴일(토요일, 일요일)에 지급일이 해당되면 자동으로 전 영업일로 조정됩니다

입사일과 지급일은 급여 계산의 중요한 기준이 되므로 정확히 입력해주세요.""",
                None,
                clickable_widget="master_pane"
            ),

            TutorialStep(
                8,
                "급여 계산 실행",
                """모든 직원 정보를 입력했다면 급여 계산을 실행해보겠습니다.

오른쪽 '월별 급여 계산' 패널에서 '📊 급여 계산' 버튼을 클릭하여
최종 급여를 계산해주세요.

프로그램이 자동으로 다음과 같은 항목들을 계산합니다:
• 기본 근무시간에 따른 기본급
• 야간근무・휴일근무 수당
• 주휴 수당 (주 15시간 이상 근무 시)
• 4대 보험 및 세금 공제

특히 홍길동, 철수, 이순신은 주 40시간 초과 근무로
주휴 수당이 자동 계산됩니다!""",
                self.validate_payroll_calculated, clickable_widget="calc_button"
            ),

            TutorialStep(
                9,
                "명세서 생성 및 저장",
                """마지막으로 계산된 급여 데이터를 바탕으로
급여명세서를 생성해보겠습니다.

생성 옵션을 선택하고 (HTML 권장) 출력 경로를 지정한 후
'명세서 생성' 버튼을 클릭해주세요.

각 직원별로 개별 명세서가 생성됩니다.""",
                None,
                clickable_widget="file_generation_group"
            ),

            TutorialStep(
                10,
                "튜토리얼 완료",
                """축하합니다! 급여명세서 관리 프로그램의 모든 기능을
성공적으로 익히셨습니다.

이제 실제 업무에서 이 프로그램을 사용하여
효율적으로 급여를 관리하실 수 있습니다.""",
                None
            )
        ]

    def start_tutorial(self):
        """튜토리얼 시작"""
        # 이미 오버레이 생성 중인지 확인
        if self._is_creating_overlay:
            print("오버레이 생성 중이므로 무시")  # 디버깅용
            return

        # 생성 시작 플래그 설정
        self._is_creating_overlay = True
        print("오버레이 생성 시작 플래그 설정")  # 디버깅용

        # 기존 컴포넌트 강제 정리
        if self.overlay:
            self.overlay.close()
            self.overlay = None

        # QApplication에서 기존 튜토리얼 오버레이 정리
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if isinstance(widget, TutorialOverlay):
                    print(f"기존 TutorialOverlay 정리: {widget}")
                    widget.close()
                    widget.deleteLater()

        # 통합 오버레이 생성 (안내 상자 포함)
        def create_tutorial_components():
            try:
                print("통합 튜토리얼 오버레이 생성 시도")  # 디버깅용

                # 통합 오버레이 생성 (안내 상자 포함)
                self.overlay = TutorialOverlay(self.main_app, self)

                # 시그널 연결
                self.overlay.guide_next_clicked.connect(self.next_step)
                self.overlay.guide_previous_clicked.connect(self.previous_step)
                self.overlay.guide_skip_clicked.connect(self.skip_tutorial)

                # 기존 guide_box 참조 제거 (통합되었으므로)
                self.guide_box = None

                self.current_step = 0
                self.show_current_step()
                print("통합 튜토리얼 오버레이 생성 완료")  # 디버깅용

            except Exception as e:
                print(f"통합 튜토리얼 오버레이 생성 중 오류: {e}")  # 디버깅용
            finally:
                # 생성 완료 플래그 해제
                self._is_creating_overlay = False
                print("오버레이 생성 플래그 해제")  # 디버깅용

        # 정리 완료를 위한 딜레이 후 생성
        QTimer.singleShot(100, create_tutorial_components)

    def show_current_step(self):
        """현재 단계 표시"""
        if 0 <= self.current_step < len(self.steps):
            step_data = self.steps[self.current_step]

            # 통합 오버레이 표시 (안내 상자 포함)
            if self.overlay:
                self.overlay.show_step(step_data)

            # 검증 타이머 제거 - 수동 검증만 사용 (다음 버튼 클릭 시)
            # if step_data.validation_func and step_data.clickable_widget:
            #     self.start_periodic_validation(step_data.validation_func)

    def next_step(self):
        """다음 단계로 진행"""
        if self.current_step < len(self.steps) - 1:
            current_step_data = self.steps[self.current_step]

            if self.validation_timer:
                self.stop_periodic_validation()

            if current_step_data.validation_func:
                try:
                    validation_result = current_step_data.validation_func()
                except Exception:
                    validation_result = False

                if not validation_result:
                    if current_step_data.clickable_widget:
                        # 오버레이를 일시적으로 숨기고 메시지 박스 표시
                        overlay_visible = self.overlay.isVisible() if self.overlay else False
                        if overlay_visible:
                            self.overlay.hide()

                        # 튜토리얼 환경에서 메시지 박스가 오버레이 위에 표시되도록 강력한 WindowFlags 설정
                        msg_box = QMessageBox()
                        msg_box.setWindowTitle("작업 필요")
                        msg_box.setText("튜토리얼에서 안내하는 UI 요소를 먼저 클릭해주세요.")
                        msg_box.setIcon(QMessageBox.Icon.Information)
                        msg_box.setWindowFlags(
                            Qt.WindowType.Window |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowSystemMenuHint
                        )
                        msg_box.raise_()  # 강제로 최상단으로 가져오기
                        msg_box.activateWindow()  # 활성화
                        msg_box.exec()

                        if overlay_visible:
                            self.overlay.show()
                    else:
                        # 오버레이를 일시적으로 숨기고 메시지 박스 표시
                        overlay_visible = self.overlay.isVisible() if self.overlay else False
                        if overlay_visible:
                            self.overlay.hide()

                        # 튜토리얼 환경에서 메시지 박스가 오버레이 위에 표시되도록 강력한 WindowFlags 설정
                        msg_box = QMessageBox()
                        msg_box.setWindowTitle("단계 미완료")
                        msg_box.setText("이 단계를 완료한 후 다음 단계로 진행해주세요.")
                        msg_box.setIcon(QMessageBox.Icon.Warning)
                        msg_box.setWindowFlags(
                            Qt.WindowType.Window |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowSystemMenuHint
                        )
                        msg_box.raise_()  # 강제로 최상단으로 가져오기
                        msg_box.activateWindow()  # 활성화
                        msg_box.exec()

                        if overlay_visible:
                            self.overlay.show()
                    return

            self.current_step += 1
            self.show_current_step()
        else:
            self.complete_tutorial()

    def previous_step(self):
        """이전 단계로 돌아가기"""
        if self.current_step > 0:
            self.current_step -= 1
            self.show_current_step()

    def skip_tutorial(self):
        """튜토리얼 건너뛰기"""
        # 오버레이를 일시적으로 숨기고 메시지 박스 표시
        overlay_visible = self.overlay.isVisible() if self.overlay else False
        if overlay_visible:
            self.overlay.hide()

        # 최상위에 표시되는 확인 대화상자
        msg_box = QMessageBox()
        msg_box.setWindowTitle("튜토리얼 건너뛰기")
        msg_box.setText("튜토리얼을 중단하시겠습니까?\n나중에 다시 시작할 수 있습니다.")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        reply = msg_box.exec()

        if overlay_visible:
            self.overlay.show()

        if reply == QMessageBox.StandardButton.Yes:
            self.complete_tutorial(skip=True)

    def complete_tutorial(self, skip=False):
        """튜토리얼 완료"""
        print(f"튜토리얼 완료 시작 - skip: {skip}")  # 디버깅용
        if self.overlay:
            self.overlay.close()
            self.overlay = None
            print("통합 오버레이 닫힘")  # 디버깅용

        # 실행 중인 인스턴스 해제
        TutorialEngine._current_instance = None
        print("현재 인스턴스 None으로 설정")  # 디버깅용

        # 완료 메시지는 main_qt.py의 on_tutorial_completed에서 표시하므로 여기서는 생략
        self.tutorial_completed.emit()

    def start_periodic_validation(self, validation_func):
        """주기적 검증 시작"""
        if self.validation_timer:
            self.validation_timer.stop()

        self.validation_timer = QTimer(self)
        self.validation_timer.timeout.connect(lambda: self.check_validation(validation_func))
        self.validation_timer.start(2000)

    def stop_periodic_validation(self):
        """주기적 검증 중지"""
        if self.validation_timer:
            self.validation_timer.stop()
            self.validation_timer = None

    def check_validation(self, validation_func):
        """검증 실행 및 결과 처리"""
        try:
            result = validation_func()
            if result:
                self.stop_periodic_validation()
                QTimer.singleShot(500, self.auto_next_step)
        except Exception:
            pass

    def start_periodic_validation_for_step3(self):
        """3단계 특별 검증 시작 - 파일 선택 상태에 따라 동적 처리"""
        if self.validation_timer:
            self.validation_timer.stop()

        self.validation_timer = QTimer(self)
        self.validation_timer.timeout.connect(self.check_step3_validation)
        self.validation_timer.start(1000)  # 1초마다 확인

    def check_step3_validation(self):
        """3단계 검증 - 파일 선택 상태 확인 및 UI 업데이트"""
        try:
            file_selected = self.validate_file_selected()

            if file_selected:
                # 파일이 선택되었으면 검증 타이머 중지 및 다음 단계로 진행
                self.stop_periodic_validation()
                QTimer.singleShot(500, self.auto_next_step)
            else:
                # 파일이 아직 선택되지 않았으면 오버레이 갱신 (투명 구멍 유지)
                if self.overlay:
                    current_step_data = self.steps[self.current_step]
                    self.overlay.show_step(current_step_data)
        except Exception as e:
            print(f"3단계 검증 오류: {e}")

    def auto_next_step(self):
        """자동으로 다음 단계 진행"""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.show_current_step()

    def update_overlay_for_calc_button(self):
        """급여 계산 버튼으로 투명 구멍 전환"""
        if self.overlay:
            print("급여 계산 버튼으로 투명 구멍 전환")  # 디버깅용
            # clickable_widget을 calc_button으로 변경
            self.overlay.clickable_widget = "calc_button"
            # overlay 갱신
            current_step_data = self.steps[self.current_step]
            self.overlay.setup_clickable_area(current_step_data)

    # 검증 함수들
    def validate_file_selected(self):
        """파일 선택 완료 검증"""
        return self.main_app.selected_file_path is not None

    def validate_employee_list(self):
        """직원 목록 검증"""
        return bool(self.main_app.employee_data) and len(self.main_app.employee_data) >= 5

    def validate_employee_info(self):
        """직원 정보 입력 검증"""
        if not self.main_app.employee_data:
            return False

        for employee in self.main_app.employee_data.values():
            if employee.get('department') and employee.get('position'):
                return True
        return False

    def validate_date_info(self):
        """날짜 정보 검증"""
        if not self.main_app.employee_data:
            return False

        for employee in self.main_app.employee_data.values():
            if employee.get('hire_date'):
                return True
        return False

    def validate_payroll_calculated(self):
        """급여 계산 검증"""
        return self.main_app.summary_df is not None and len(self.main_app.summary_df) > 0

    def validate_payslips_generated(self):
        """명세서 생성 검증"""
        return True


def start_tutorial(main_app):
    """튜토리얼 시작 함수"""
    # 이전 인스턴스가 남아있을 수 있으므로 안전하게 정리
    if TutorialEngine._current_instance is not None:
        print(f"이전 튜토리얼 인스턴스 발견: {TutorialEngine._current_instance}")  # 디버깅용
        try:
            # 이전 인스턴스 정리 시도
            if hasattr(TutorialEngine._current_instance, 'overlay') and TutorialEngine._current_instance.overlay:
                TutorialEngine._current_instance.overlay.close()
            if hasattr(TutorialEngine._current_instance, 'guide_box') and TutorialEngine._current_instance.guide_box:
                TutorialEngine._current_instance.guide_box.close()
            TutorialEngine._current_instance = None
            print("이전 인스턴스 정리됨")  # 디버깅용
        except Exception as e:
            print(f"이전 인스턴스 정리 중 오류: {e}")  # 디버깅용
            TutorialEngine._current_instance = None

    print("새로운 튜토리얼 엔진 생성")  # 디버깅용
    # 새로운 튜토리얼 엔진 생성 및 시작
    engine = TutorialEngine(main_app)
    TutorialEngine._current_instance = engine  # 현재 인스턴스 설정
    print(f"튜토리얼 엔진 생성됨: {engine}")  # 디버깅용
    engine.start_tutorial()
    return engine
