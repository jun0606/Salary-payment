#!/usr/bin/env python3
"""
PyQt6 기반 튜토리얼 UI 컴포넌트 모듈
TutorialOverlay와 TutorialGuideBox의 통합을 위한 재사용 가능한 컴포넌트들
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
from PyQt6.QtCore import Qt


class TutorialGuideWidget(QWidget):
    """
    튜토리얼 안내 상자 위젯
    TutorialOverlay의 자식으로 사용되는 QWidget 기반 컴포넌트
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_step_data = None
        self.setup_ui()

    def setup_ui(self):
        """안내 박스 UI 설정"""
        # 메인 프레임
        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        # 제목
        self.title_label = QLabel("튜토리얼")
        self.title_label.setFont(self.font())
        self.title_label.setStyleSheet("color: #2c3e50; border: none;")
        layout.addWidget(self.title_label)

        # 설명 텍스트 (스크롤 영역 추가)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setMaximumHeight(200)  # 최대 높이 제한
        self.scroll_area.setMinimumHeight(80)   # 최소 높이 설정
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background-color: rgba(0, 0, 0, 0.1);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 0, 0, 0.5);
            }
        """)

        # 스크롤 영역 내부 위젯
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #495057; border: none; line-height: 1.5;")
        scroll_layout.addWidget(self.description_label)

        self.scroll_area.setWidget(scroll_widget)
        layout.addWidget(self.scroll_area)

        # 버튼 영역
        button_layout = QHBoxLayout()

        self.skip_button = QPushButton("건너뛰기")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(self.skip_button)

        button_layout.addStretch()

        self.back_button = QPushButton("◀ 이전")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        button_layout.addWidget(self.back_button)

        self.next_button = QPushButton("다음 ▶")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)

        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)

    def show_step(self, step_data):
        """단계 표시"""
        self.current_step_data = step_data

        self.title_label.setText(f"튜토리얼 - 단계 {step_data.step_id}")
        self.description_label.setText(step_data.description)

        # 버튼 상태 설정
        self.back_button.setEnabled(step_data.step_id > 1)
        self.next_button.setText("완료" if step_data.step_id >= 8 else "다음 ▶")

        self.show()

    def adjust_position(self, parent_width, parent_height):
        """부모 컨테이너 내 위치 조정"""
        if not self.current_step_data:
            return

        # 안내 박스 크기 계산
        self.main_frame.adjustSize()
        box_size = self.main_frame.size()
        box_width = box_size.width()
        box_height = box_size.height()

        # 단계별 위치 설정
        if self.current_step_data.step_id in [1, 2, 3, 4, 8]:
            # 단계 1-4, 8: 고정 중앙 하단 위치 (박스 크기와 무관하게 동일 위치)
            x = max(20, (parent_width - 500) // 2)  # 고정 중앙
            y = parent_height - 350  # 고정 하단 위치
        elif self.current_step_data.step_id in [5, 6, 7]:
            # 단계 5-7: 우측 중앙 위치 (직원 마스터 관리 패널 가림 방지)
            x = parent_width - 600  # 우측 배치
            y = max(20, (parent_height - 300) // 2)  # 중앙 높이
        else:
            # 단계 9-10: 중앙 배치 (오버레이 범위 초과 방지)
            x = max(20, (parent_width - box_width) // 2)
            y = max(20, (parent_height - box_height) // 2)

        # 경계 체크
        x = max(0, min(x, parent_width - box_width))
        y = max(0, min(y, parent_height - box_height))

        self.move(x, y)


class TutorialOverlayWidget(QWidget):
    """
    투명 오버레이 위젯
    TutorialOverlay의 투명 오버레이 부분을 분리한 컴포넌트
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clickable_rect = None
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

    def set_clickable_area(self, rect):
        """클릭 가능한 영역 설정"""
        self.clickable_rect = rect
        self.update()

    def paintEvent(self, event):
        """투명 오버레이 그리기"""
        from PyQt6.QtGui import QPainter, QColor

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 102))  # 진한 검은색 배경

        # 클릭 가능한 영역만큼 투명 구멍 만들기
        if self.clickable_rect:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.clickable_rect, Qt.GlobalColor.transparent)

        painter.end()

    def mousePressEvent(self, event):
        """클릭 이벤트 처리"""
        if self.clickable_rect and self.clickable_rect.contains(event.pos()):
            # 클릭 가능한 영역 클릭 시 부모에게 시그널 발생
            self.clicked.emit(event.pos())
        else:
            super().mousePressEvent(event)


# 시그널 정의를 위한 헬퍼
from PyQt6.QtCore import pyqtSignal

class ClickableOverlayWidget(TutorialOverlayWidget):
    """클릭 이벤트를 처리할 수 있는 오버레이 위젯"""
    clicked = pyqtSignal(object)  # QPoint를 파라미터로 전달
