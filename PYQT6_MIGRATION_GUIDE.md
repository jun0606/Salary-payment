# PyQt6 마이그레이션 완전 가이드

## 📋 개요

**프로젝트**: 급여명세서 생성기  
**현재 프레임워크**: tkinter + ttk  
**목표 프레임워크**: PyQt6  
**마이그레이션 목표**: 현대적 UI, 향상된 사용자 경험, 크로스 플랫폼 호환성  
**기간**: 19일 (총 14단계)  
**리스크**: 기능 유실 방지, 호환성 유지

## 🔍 현재 시스템 파일별 분석

### main_app.py - 메인 애플리케이션

**파일 크기**: ~600줄  
**주요 기능**: 메인 윈도우, 메뉴, 라이선스 관리, 이벤트 처리

#### 클래스 및 함수
```python
class ActivationDialog(simpledialog.Dialog):
    # 라이선스 활성화 입력 대화상자

class PayslipApp(tk.Tk):
    # 메인 애플리케이션 클래스

    # 초기화 및 설정
    def __init__(self):  # 앱 초기화
    def setup_ui(self):  # UI 레이아웃 설정
    def setup_master_pane(self):  # 직원 관리 패널 설정
    def setup_monthly_pane(self):  # 급여 계산 패널 설정

    # 라이선스 관리
    def run_license_check(self):  # 라이선스 상태 확인
    def show_activation_dialog_from_menu(self):  # 활성화 대화상자 표시
    def process_activation(self):  # 라이선스 코드 검증 및 활성화
    def _lock_application_features(self):  # 기능 제한
    def _unlock_application_features(self):  # 기능 해제
    def _update_license_status_display(self):  # 상태 표시 업데이트

    # 데이터 관리
    def load_config(self):  # 설정 파일 로드
    def save_config(self):  # 설정 파일 저장
    def load_master_data(self):  # 직원 데이터 로드
    def save_master_data(self):  # 직원 데이터 저장
    def populate_master_treeview(self):  # 트리뷰 데이터 채우기

    # 직원 관리 기능
    def on_master_row_select(self):  # 트리뷰 선택 이벤트
    def adjust_master_date(self):  # 날짜 조정
    def adjust_global_date(self):  # 전체 지급일 조정
    def add_employee(self):  # 직원 추가
    def update_employee(self):  # 직원 수정
    def delete_employee(self):  # 직원 삭제
    def clear_master_form(self):  # 폼 초기화
    def import_from_summary(self):  # 급여 데이터에서 가져오기

    # 급여 계산 기능
    def select_file(self):  # 파일 선택
    def preview_data(self):  # 데이터 미리보기 및 계산
    def populate_monthly_treeview(self):  # 월별 데이터 표시
    def on_monthly_cell_double_click(self):  # 셀 더블클릭 편집
    def update_monthly_value(self):  # 값 업데이트
    def generate_final_file(self):  # 최종 파일 생성

    # 유틸리티
    def open_tax_settings(self):  # 세무사 설정 열기
    def on_close(self):  # 앱 종료
    def format_month_string(self):  # 월 문자열 포맷팅
    def _get_selected_users(self):  # 선택된 사용자 가져오기
```

#### tkinter 의존성
- `tk.Tk` → 메인 윈도우
- `ttk.Style` → 스타일링
- `tk.Menu` → 메뉴 시스템
- `ttk.PanedWindow` → 분할 레이아웃
- `ttk.LabelFrame` → 그룹 박스
- 이벤트 바인딩 (`.bind()`)

#### 유지해야 할 기능
- 모든 비즈니스 로직
- 데이터 처리 및 저장
- 라이선스 관리
- 파일 입출력
- 사용자 입력 검증

#### 삭제 대상 코드
```python
# tkinter 스타일 설정
self.style = ttk.Style()
self.style.theme_use('clam')
self.style.configure('.', font=('맑은 고딕', 10))

# tkinter 이벤트 바인딩
app.master_tree.bind("<<TreeviewSelect>>", app.on_master_row_select)
entry.bind("<Return>", on_update_value)

# tkinter 위젯 생성
root = tk.Tk()
button = ttk.Button(parent, text="클릭")
```

### master_data_pane.py - 직원 관리 UI

**파일 크기**: ~80줄  
**주요 기능**: 직원 정보 입력 폼, 직원 목록 표시

#### 함수
```python
def setup_pane(app, master_pane):
    # 직원 관리 패널 초기화 및 설정
```

#### tkinter 의존성
- `ttk.Frame` → 컨테이너
- `ttk.Label` → 텍스트 표시
- `ttk.Entry` → 입력 필드
- `ttk.Button` → 액션 버튼
- `ttk.Treeview` → 데이터 테이블
- `ttk.Scrollbar` → 스크롤바

#### 유지해야 할 기능
- 모든 데이터 입력/수정/삭제 로직
- 유효성 검증
- 날짜 조정 기능
- 데이터 바인딩

#### 삭제 대상 코드
```python
# tkinter 위젯 생성 및 배치
entry = ttk.Entry(form_frame, textvariable=app.master_form_vars[field_name])
entry.grid(row=row, column=1, sticky=tk.EW, pady=2, padx=5)

# 이벤트 바인딩
app.master_tree.bind("<<TreeviewSelect>>", app.on_master_row_select)
```

### monthly_payroll_pane.py - 급여 계산 UI

**파일 크기**: ~100줄  
**주요 기능**: 급여 계산 인터페이스, 결과 표시

#### 함수
```python
def setup_pane(app, monthly_pane):
    # 급여 계산 패널 초기화 및 설정
```

#### tkinter 의존성
- `ttk.LabelFrame` → 패널 컨테이너
- `ttk.Button` → 계산/저장 버튼
- `ttk.Combobox` → 월 선택
- `ttk.Treeview` → 결과 테이블
- `ttk.Scrollbar` → 스크롤바
- 인라인 편집 이벤트

#### 유지해야 할 기능
- 파일 선택 및 검증
- 데이터 미리보기 및 계산
- 셀 단위 편집
- 값 업데이트 및 재계산
- 파일 생성 옵션

#### 삭제 대상 코드
```python
# tkinter 이벤트 처리
entry.bind("<Return>", on_update_value)
entry.bind("<FocusOut>", on_update_value)

# tkinter 위젯 속성
tree.configure(yscrollcommand=scrollbar.set)
```

### tax_settings.py - 세무사 설정 UI

**파일 크기**: ~200줄  
**주요 기능**: 세무사 정보 관리, 라이선스 코드 생성

#### 클래스
```python
class PasswordDialog(tk.Toplevel):
    # 비밀번호 입력 대화상자

class CodeDisplayWindow(tk.Toplevel):
    # 생성된 코드 표시 창

class TaxSettingsDialog(tk.Toplevel):
    # 세무사 설정 메인 대화상자
```

#### tkinter 의존성
- `tk.Toplevel` → 팝업 창
- `ttk.Label`/`ttk.Entry` → 폼 컨트롤
- `ttk.Button` → 액션 버튼
- `tk.Text` → 텍스트 표시
- 클립보드 조작

#### 유지해야 할 기능
- 모든 설정 저장/로딩
- 라이선스 코드 생성 로직
- HTML 파일 생성 기능
- 폼 유효성 검증

#### 삭제 대상 코드
```python
# tkinter 창 생성
dialog = tk.Toplevel(parent)
dialog.title("라이선스 활성화")

# tkinter 이벤트
self.entry.bind("<Return>", lambda e: self.check_password())
```

### logic.py - 비즈니스 로직

**파일 크기**: ~500줄  
**주요 기능**: 데이터 처리, 급여 계산, 파일 생성

#### 함수 (주요)
```python
def load_and_preprocess_data():  # 데이터 로드 및 전처리
def calculate_salary():  # 급여 계산
def create_user_summaries():  # 사용자 요약 생성
def generate_payslips():  # Excel 파일 생성
def generate_payslips_html():  # HTML 파일 생성
def process_payroll_for_gui():  # GUI용 급여 처리
```

**tkinter 의존성**: 없음 (순수 비즈니스 로직)

**유지해야 할 기능**: 100% 유지 (UI 프레임워크 변경과 무관)

**삭제 대상 코드**: 없음

### license_system/ - 라이선스 시스템

**하위 파일들**:
- `license_verifier.py` - 라이선스 검증
- `license_generator.py` - 코드 생성
- `hardware_id.py` - HW ID 생성

**tkinter 의존성**: 없음

**유지해야 할 기능**: 100% 유지

## 🎯 마이그레이션 전략

### 단계별 접근
```
Phase 1: 환경 설정 및 코어 구조 (3일)
Phase 2: UI 컴포넌트 변환 (7일)
Phase 3: 이벤트 처리 마이그레이션 (3일)
Phase 4: 스타일링 및 테마 적용 (2일)
Phase 5: 통합 테스트 (3일)
Phase 6: 배포 준비 (1일)
```

### 파일별 변환 매핑

| tkinter 컴포넌트 | PyQt6 컴포넌트 | 변환 복잡도 |
|------------------|----------------|-------------|
| `tk.Tk` | `QApplication` + `QMainWindow` | 높음 |
| `tk.Toplevel` | `QDialog` | 중간 |
| `ttk.Frame` | `QWidget` + `QVBoxLayout` | 중간 |
| `ttk.Label` | `QLabel` | 낮음 |
| `ttk.Entry` | `QLineEdit` | 낮음 |
| `ttk.Button` | `QPushButton` | 낮음 |
| `ttk.Treeview` | `QTableWidget` | 높음 |
| `ttk.Combobox` | `QComboBox` | 낮음 |
| `tk.Menu` | `QMenuBar` + `QAction` | 중간 |
| 이벤트 바인딩 | 시그널/슬롯 | 높음 |

### 기능 유실 방지 체크리스트

#### UI 기능
- [ ] 창 크기/위치 유지
- [ ] 메뉴 기능 정상 작동
- [ ] 폼 입력/검증
- [ ] 데이터 표시/편집
- [ ] 파일 다이얼로그
- [ ] 진행 상태 표시

#### 비즈니스 로직
- [ ] 데이터 로드/처리
- [ ] 급여 계산 정확성
- [ ] 파일 생성 (Excel/HTML)
- [ ] 라이선스 검증
- [ ] 설정 저장/로딩

#### 사용자 경험
- [ ] 키보드 단축키
- [ ] 마우스 이벤트
- [ ] 포커스 이동
- [ ] 에러 메시지 표시
- [ ] 진행 피드백

## 🔧 PyQt6 변환 상세 가이드

### 메인 윈도우 변환
```python
# tkinter → PyQt6
class PayslipApp(tk.Tk):  # 기존
    def __init__(self):
        super().__init__()
        self.title("제목")

class PayslipQtApp(QMainWindow):  # 변환
    def __init__(self):
        super().__init__()
        self.setWindowTitle("제목")
        self.setGeometry(100, 100, 1200, 800)

        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
```

### 위젯 변환 예시
```python
# 버튼
tkinter: button = ttk.Button(parent, text="클릭", command=callback)
PyQt6: button = QPushButton("클릭", parent)
        button.clicked.connect(callback)

# 입력 필드
tkinter: entry = ttk.Entry(parent, textvariable=var)
PyQt6: entry = QLineEdit(parent)
        entry.textChanged.connect(self.on_text_changed)

# 레이블
tkinter: label = ttk.Label(parent, text="텍스트")
PyQt6: label = QLabel("텍스트", parent)

# 테이블
tkinter: tree = ttk.Treeview(parent, columns=cols)
PyQt6: table = QTableWidget(parent)
        table.setColumnCount(len(cols))
```

### 이벤트 처리 변환
```python
# tkinter 이벤트 바인딩
button.bind("<Button-1>", callback)
tree.bind("<<TreeviewSelect>>", callback)

# PyQt6 시그널/슬롯
button.clicked.connect(callback)
tree.itemSelectionChanged.connect(callback)
```

### 레이아웃 변환
```python
# tkinter pack/grid
frame.pack(fill=tk.X, padx=5, pady=5)
widget.grid(row=0, column=0, sticky=tk.EW)

# PyQt6 레이아웃
layout = QVBoxLayout()
layout.addWidget(widget, stretch=1)
frame.setLayout(layout)
```

## 🗑️ 삭제 대상 코드 정리

### tkinter import 및 초기화
```python
# 삭제 대상
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# PyQt6 대체
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QPushButton, QLabel, QLineEdit, QTableWidget, QDialog)
from PyQt6.QtCore import Qt
```

### tkinter 스타일링
```python
# 삭제 대상
self.style = ttk.Style()
self.style.theme_use('clam')
self.style.configure('TButton', padding=5)

# PyQt6 대체
app.setStyle('Fusion')  # 또는 스타일시트 사용
```

### tkinter 이벤트 바인딩
```python
# 삭제 대상
widget.bind("<Button-1>", callback)
widget.bind("<Return>", callback)
widget.bind("<<TreeviewSelect>>", callback)

# PyQt6 대체
widget.clicked.connect(callback)
widget.returnPressed.connect(callback)
widget.itemSelectionChanged.connect(callback)
```

### tkinter 위젯 속성
```python
# 삭제 대상
widget.config(state=tk.DISABLED)
widget.pack(fill=tk.X, expand=True)
tree.heading(col, text="제목")

# PyQt6 대체
widget.setEnabled(False)
layout.addWidget(widget, stretch=1)
table.setHorizontalHeaderItem(col, QTableWidgetItem("제목"))
```

## 🧪 테스트 및 검증 계획

### 단위 테스트
- 각 모듈별 독립 테스트
- UI 컴포넌트 생성 확인
- 이벤트 처리 검증

### 통합 테스트
- 전체 워크플로우 테스트
- 데이터 처리 정확성 검증
- 파일 입출력 테스트

### 사용자验收 테스트
- 실제 사용자 시나리오 테스트
- UI/UX 개선 피드백 수집
- 성능 비교 (tkinter vs PyQt6)

### 크로스 플랫폼 테스트
- Windows 10/11
- 다른 해상도
- 터치 지원

## 🔄 롤백 계획

### 백업 전략
- 마이그레이션 전 완전 백업
- git 브랜치 분리 (`tkinter` → `pyqt6`)
- 데이터 호환성 유지

### 롤백 절차
1. PyQt6 브랜치에서 tkinter 브랜치로 체크아웃
2. 의존성 복원 (`pip uninstall PyQt6`)
3. tkinter 재설치 (`pip install tkinter` - 기본 포함)
4. 설정 파일 및 데이터 확인

### 중간 롤백 지점
- Phase 1 완료 후 롤백 가능
- Phase 3 완료 후 부분 롤백 가능
- Phase 5 완료 후 완전 롤백 불가

## 📅 마이그레이션 일정

| 단계 | 기간 | 담당 | 산출물 |
|------|------|------|--------|
| Phase 1 | 3일 | 개발자 | PyQt6 기본 구조 |
| Phase 2 | 7일 | 개발자 | UI 컴포넌트 변환 |
| Phase 3 | 3일 | 개발자 | 이벤트 처리 |
| Phase 4 | 2일 | 디자이너 | 스타일링 |
| Phase 5 | 3일 | QA팀 | 테스트 및 디버깅 |
| Phase 6 | 1일 | 개발자 | 배포 준비 |

**총 기간: 19일**

## ⚠️ 리스크 관리

### 기술적 리스크
- **PyQt6 학습 곡선**: 공식 문서 및 튜토리얼 활용
- **호환성 이슈**: 각 OS별 테스트 환경 구축
- **성능 저하**: 프로파일링 도구로 모니터링

### 기능적 리스크
- **UI/UX 변경**: 사용자 피드백 기반 개선
- **기능 유실**: 상세한 체크리스트로 검증
- **데이터 손실**: 백업 및 마이그레이션 스크립트

### 일정 리스크
- **예상치 못한 복잡성**: 버퍼 기간 20% 확보
- **외부 의존성**: 안정적인 라이브러리 버전 사용
- **테스트 환경**: 다양한 환경에서 테스트

---

**이 문서는 PyQt6 마이그레이션의 완전한 가이드라인으로, 기능 유실 없이 체계적인 변환을 보장합니다.**
