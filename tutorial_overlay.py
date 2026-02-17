#!/usr/bin/env python3
"""
PyQt6 기반 통합 튜토리얼 오버레이 컴포넌트
투명 오버레이 + 안내 상자를 단일 창으로 통합
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialog, QFrame, QMessageBox, QApplication, QGroupBox
from PyQt6.QtCore import Qt, QTimer, QRect, QPointF, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QPen, QMouseEvent, QBitmap, QRegion, QKeyEvent

# 컴포넌트 모듈 임포트
from tutorial_components import TutorialGuideWidget


class TutorialOverlay(QWidget):
    """통합 튜토리얼 오버레이 위젯 (투명 오버레이 + 안내 상자)"""

    # 시그널 정의
    guide_next_clicked = pyqtSignal()
    guide_previous_clicked = pyqtSignal()
    guide_skip_clicked = pyqtSignal()

    def __init__(self, parent=None, tutorial_engine=None):
        super().__init__(parent)
        self.parent_window = parent
        self.tutorial_engine = tutorial_engine
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
            # Tool 제거하여 더 강력한 최상단 우선순위
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 투명 배경 허용

        # 프로그램 종료 시 자동으로 닫히도록 설정
        QApplication.instance().aboutToQuit.connect(self.close)

        # 부모 윈도우를 완전히 덮도록 설정
        if parent:
            # 부모 윈도우의 절대 위치와 크기로 설정
            parent_geometry = parent.geometry()
            self.setGeometry(parent_geometry)

        # 안내 상자 위젯 생성 (자식으로 추가)
        self.guide_widget = TutorialGuideWidget(self)
        self.guide_widget.hide()  # 초기에는 숨김

        # 안내 상자 버튼 시그널 연결
        self.guide_widget.next_button.clicked.connect(self._on_guide_next)
        self.guide_widget.back_button.clicked.connect(self._on_guide_previous)
        self.guide_widget.skip_button.clicked.connect(self._on_guide_skip)

        # 오버레이 배경 설정 - 투명 (안내 상자가 자체 배경을 가짐)
        self.setStyleSheet("background: transparent;")

        # 창 크기 변경 이벤트 연결
        if parent:
            parent.installEventFilter(self)  # 이벤트 필터 설치

        # 클릭 허용 관련 변수들
        self.clickable_widget = None
        self.clickable_rect = None
        self.current_step_data = None  # 현재 단계 데이터

    def _on_guide_next(self):
        """안내 상자 다음 버튼 클릭"""
        self.guide_next_clicked.emit()

    def _on_guide_previous(self):
        """안내 상자 이전 버튼 클릭"""
        self.guide_previous_clicked.emit()

    def _on_guide_skip(self):
        """안내 상자 건너뛰기 버튼 클릭"""
        self.guide_skip_clicked.emit()



    def show_step(self, step_data):
        """단계 표시 - 오버레이 + 안내 상자 통합 표시"""
        import logging
        logging.info(f"TutorialOverlay.show_step() 호출됨 - 단계 {step_data.step_id}")  # 디버깅용

        # 기존 상태 완전 초기화 (다음 단계 진행 시 필수)
        self.clickable_widget = None
        self.clickable_rect = None
        logging.info("오버레이 상태 초기화 완료")  # 디버깅용

        # 현재 단계 데이터 저장
        self.current_step_data = step_data

        # 클릭 가능한 영역 설정
        self.setup_clickable_area(step_data)

        # 안내 상자 표시 및 위치 조정
        self.guide_widget.show_step(step_data)
        self.guide_widget.adjust_position(self.width(), self.height())

        # 오버레이 표시
        logging.info(f"오버레이 표시 전 가시성: {self.isVisible()}")  # 디버깅용
        self.show()
        logging.info(f"오버레이 표시 후 가시성: {self.isVisible()}")  # 디버깅용

        logging.info("TutorialOverlay + GuideWidget 표시 완료")  # 디버깅용

    def setup_clickable_area(self, step_data):
        """클릭 가능한 영역 설정 및 투명 구멍 생성"""
        # 클릭 가능한 위젯 설정
        self.clickable_widget = None
        self.clickable_rect = None

        # 3단계 특별 처리: 파일 선택 상태에 따라 동적으로 결정
        if step_data.step_id == 3:
            if not self.tutorial_engine.main_app.selected_file_path:
                # 파일이 선택되지 않은 경우: 파일 선택 버튼
                clickable_widget_name = "file_select_button"
            else:
                # 파일이 선택된 경우: 급여 계산 버튼
                clickable_widget_name = "calc_button"
        else:
            # 다른 단계들은 기존 로직
            clickable_widget_name = step_data.clickable_widget

        if clickable_widget_name:
            self.find_clickable_widget(clickable_widget_name)
            print(f"클릭 가능한 위젯 설정됨: {self.clickable_widget}")  # 디버깅용

            # 투명 구멍 생성을 위한 화면 갱신
            self.update()



    def eventFilter(self, obj, event):
        """이벤트 필터 - 부모 윈도우 크기 변경 감지"""
        if obj == self.parent_window and event.type() == event.Type.Resize:
            # 부모 윈도우 크기 변경 시 오버레이 재설정
            self.update_geometry()
        return super().eventFilter(obj, event)

    def find_clickable_widget(self, widget_name):
        """클릭 가능한 위젯 찾기"""
        try:
            # monthly_payroll_pane_qt에서 버튼 찾기
            if hasattr(self.parent_window, 'monthly_pane') and widget_name in ["file_select_button", "calc_button"]:
                monthly_pane = self.parent_window.monthly_pane
                # MonthlyPayrollPaneQt는 QWidget을 상속받았으므로 직접 findChildren 사용
                for child in monthly_pane.findChildren(QPushButton):
                    button_text = child.text()
                    print(f"monthly_pane 버튼 찾음: '{button_text}'")  # 디버깅용

                    # 파일 선택 버튼
                    if widget_name == "file_select_button" and "파일" in button_text and "선택" in button_text:
                        self.clickable_widget = child
                        # 위젯의 절대 위치 계산
                        widget_pos = child.mapToGlobal(child.rect().topLeft())
                        overlay_pos = self.mapFromGlobal(widget_pos)
                        self.clickable_rect = child.rect().translated(overlay_pos)
                        print(f"클릭 가능한 위젯 찾음: '{button_text}', 영역: {self.clickable_rect}")
                        break

                    # 급여 계산 버튼
                    elif widget_name == "calc_button" and "급여" in button_text and "계산" in button_text:
                        self.clickable_widget = child
                        # 위젯의 절대 위치 계산
                        widget_pos = child.mapToGlobal(child.rect().topLeft())
                        overlay_pos = self.mapFromGlobal(widget_pos)
                        self.clickable_rect = child.rect().translated(overlay_pos)
                        print(f"클릭 가능한 위젯 찾음: '{button_text}', 영역: {self.clickable_rect}")
                        break

            # master_pane에서 버튼 찾기 (직원 정보 가져오기 버튼)
            elif hasattr(self.parent_window, 'master_pane') and widget_name == "import_button":
                master_pane = self.parent_window.master_pane
                print(f"master_pane 찾음: {master_pane}")  # 디버깅용

                # master_pane은 QGroupBox, 그 안의 MasterDataPaneQt 위젯에서 버튼 찾기
                for child in master_pane.findChildren(QPushButton):
                    button_text = child.text()
                    print(f"master_pane 버튼 찾음: '{button_text}'")  # 디버깅용

                    # 직원 정보 가져오기 버튼
                    if "급여" in button_text and "가져오기" in button_text:
                        self.clickable_widget = child
                        # 위젯의 절대 위치 계산
                        widget_pos = child.mapToGlobal(child.rect().topLeft())
                        overlay_pos = self.mapFromGlobal(widget_pos)
                        # 버튼이 잘 보이도록 투명 구멍을 크게 설정
                        button_rect = child.rect()
                        enlarged_rect = button_rect.adjusted(-10, -10, 10, 10)  # 10px씩 확장
                        self.clickable_rect = enlarged_rect.translated(overlay_pos)
                        print(f"클릭 가능한 위젯 찾음: '{button_text}', 영역: {self.clickable_rect}")
                        break

            # master_pane 전체 영역 클릭 가능하게 (단계 6용)
            elif hasattr(self.parent_window, 'master_pane') and widget_name == "master_pane":
                master_pane = self.parent_window.master_pane
                print(f"master_pane 전체 영역 클릭 가능하게 설정: {master_pane}")  # 디버깅용

                # master_pane의 절대 위치와 크기 계산
                pane_pos = master_pane.mapToGlobal(master_pane.rect().topLeft())
                overlay_pos = self.mapFromGlobal(pane_pos)
                self.clickable_rect = master_pane.rect().translated(overlay_pos)
                print(f"master_pane 전체 영역: {self.clickable_rect}")

            # 파일 생성 그룹 전체 영역 클릭 가능하게 (단계 9용)
            elif hasattr(self.parent_window, 'monthly_pane') and widget_name == "file_generation_group":
                import logging
                monthly_pane = self.parent_window.monthly_pane
                logging.info(f"file_generation_group 탐색 시작: monthly_pane = {monthly_pane}")  # 디버깅용

                # 파일 생성 그룹 찾기 - 재귀적 탐색 방식
                button_group = None

                # 1. 재귀적으로 모든 QGroupBox 찾기
                all_group_boxes = monthly_pane.findChildren(QGroupBox)
                logging.info(f"monthly_pane에서 찾은 모든 QGroupBox: {[f'{gb.objectName()} ({gb.title()})' for gb in all_group_boxes]}")

                # 2. objectName으로 button_group 찾기
                for gb in all_group_boxes:
                    if gb.objectName() == "file_generation_group":
                        button_group = gb
                        logging.info(f"file_generation_group 찾음: {button_group}")
                        break

                # 3. button_group이 있으면 투명 구멍 설정
                if button_group:
                    # 그룹의 절대 위치와 크기 계산
                    group_pos = button_group.mapToGlobal(button_group.rect().topLeft())
                    overlay_pos = self.mapFromGlobal(group_pos)
                    # 여유 있게 확장 (15px씩 - 콤보박스 포함)
                    enlarged_rect = button_group.rect().adjusted(-15, -15, 15, 15)
                    self.clickable_rect = enlarged_rect.translated(overlay_pos)
                    logging.info(f"file_generation_group 투명 구멍 설정: {self.clickable_rect}")
                else:
                    logging.warning("file_generation_group을 찾지 못함 - monthly_pane 전체를 클릭 가능하게 설정")
                    # 실패 시 monthly_pane 전체를 클릭 가능하게 설정
                    pane_pos = monthly_pane.mapToGlobal(monthly_pane.rect().topLeft())
                    overlay_pos = self.mapFromGlobal(pane_pos)
                    self.clickable_rect = monthly_pane.rect().translated(overlay_pos)
                    logging.info(f"monthly_pane 전체 영역: {self.clickable_rect}")
        except Exception as e:
            print(f"클릭 가능한 위젯 찾기 오류: {e}")
            import traceback
            traceback.print_exc()

    def update_geometry(self):
        """오버레이 지오메트리 업데이트"""
        if self.parent_window:
            parent_geometry = self.parent_window.geometry()
            self.setGeometry(parent_geometry)

    def forward_event_to_parent(self, pos):
        """부모 윈도우에게 이벤트 전달 (중복 코드 제거)"""
        try:
            if self.parent_window:
                parent_pos = self.mapToParent(pos)
                print(f"부모 좌표로 변환: {parent_pos}")  # 디버깅용

                from PyQt6.QtGui import QMouseEvent
                from PyQt6.QtCore import QPointF
                parent_event = QMouseEvent(
                    QMouseEvent.Type.MouseButtonPress,  # 이벤트 타입
                    QPointF(parent_pos),
                    Qt.MouseButton.LeftButton,  # 버튼
                    Qt.MouseButton.LeftButton,  # 버튼 상태 (PyQt6에서는 단일 값)
                    Qt.KeyboardModifier.NoModifier  # 수정자 (PyQt6 API)
                )

                from PyQt6.QtWidgets import QApplication
                result = QApplication.sendEvent(self.parent_window, parent_event)
                print(f"클릭 이벤트 부모에게 전달됨 (결과: {result})")  # 디버깅용
        except Exception as e:
            print(f"이벤트 전달 중 오류: {e}")  # 디버깅용
            import traceback
            traceback.print_exc()

    def mousePressEvent(self, event):
        """마우스 클릭 이벤트 처리 - 투명 영역 클릭 시 버튼 직접 트리거"""
        pos = event.pos()

        # 투명 구멍 영역 클릭 처리
        if self.clickable_rect and self.clickable_rect.contains(pos):
            print(f"투명 영역 클릭 감지: {pos}")  # 디버깅용

            # 클릭 가능한 위젯이 있다면 직접 clicked 시그널 emit
            if self.clickable_widget:
                print(f"버튼 직접 클릭: {self.clickable_widget.text()}")  # 디버깅용
                self.clickable_widget.click()  # 버튼 직접 클릭
                print("버튼 클릭 완료")  # 디버깅용
                return

            # 위젯이 없다면 이벤트 전달 방식 사용 (fallback)
            self.forward_event_to_parent(pos)
            return

        # 다른 영역은 부모에게 이벤트 전달
        print(f"오버레이 영역 클릭 - 부모에게 전달: {pos}")  # 디버깅용
        self.forward_event_to_parent(pos)

    def keyPressEvent(self, event: QKeyEvent):
        """키보드 이벤트 처리 - ESC 키로 튜토리얼 종료"""
        if event.key() == Qt.Key.Key_Escape:
            print("오버레이 ESC 키 감지 - 튜토리얼 종료")  # 디버깅용
            # ESC 키로 튜토리얼 종료
            if self.tutorial_engine:
                self.tutorial_engine.complete_tutorial(skip=True)
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        """오버레이 그리기 - 진한 통합 투명도 배경 + 클릭 구멍"""
        painter = QPainter(self)

        # 1. 통합된 진한 투명도 배경색 설정 (40% 정도)
        alpha = 102  # 진한 검은색 배경 (40% 투명도)
        background_color = QColor(0, 0, 0, alpha)
        painter.fillRect(self.rect(), background_color)

        # 2. 클릭 가능한 영역만큼 투명 구멍 만들기
        if self.clickable_rect:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.clickable_rect, Qt.GlobalColor.transparent)

        painter.end()

        # 부모의 paintEvent 호출하지 않음 (기본 배경 방지)

    def closeEvent(self, event):
        """통합 오버레이 닫힘 이벤트"""
        print("통합 TutorialOverlay 닫힘")  # 디버깅용
        # 안내 상자는 자동으로 함께 닫힘 (부모-자식 관계)
        super().closeEvent(event)
