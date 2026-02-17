# HTML-로직 일관성 근본적 문제 분석 및 해결

**작성일**: 2026년 2월 10일  
**분석 대상**: logic.py, payslip_template.html, 테스트 결과

---

## 1. 근본적 문제 분석

### 1.1 아키텍처적 문제

```
┌────────────────────────────────────────────────────────────────┐
│                      근본적 문제 구조                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │   logic.py   │          │  template    │                     │
│  │              │          │              │                     │
│  │ - 변수 정의   │   ???    │ - 변수 사용   │  ← 동기화 문제!      │
│  │ - 계산 로직   │ ────────→│ - HTML 구조   │                     │
│  │ - 데이터 반환 │          │ - 조건 분기   │                     │
│  └──────────────┘          └──────────────┘                     │
│         ↓                           ↓                          │
│  ┌──────────────┐          ┌──────────────┐                     │
│  │  변수명:     │          │  변수명:     │  ← 명명 불일치!      │
│  │  night_pay   │          │  야간수당    │                     │
│  │  extra_pay   │          │  연장수당    │                     │
│  └──────────────┘          └──────────────┘                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                검증 계층 부재                          │      │
│  │   - 런타임 검증 없음                                   │      │
│  │   - 타입 체크 없음                                     │      │
│  │   - 계산 일관성 검증 없음                               │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 발견된 근본적 문제 5가지

| # | 문제 | 현상 | 근본 원인 |
|---|------|------|-----------|
| 1 | **양방향 동기화 실패** | 변수 추가 시 템플릿/로직 불일치 | 수동 동기화 |
| 2 | **단일 출처 원칙 위반** | 변수명 한글/영어 혼용 | 정의가 분산 |
| 3 | **검증 계층 부재** | 오류 런타임 발생 | 컴파일/빌드 시 검증 없음 |
| 4 | **조건 분기 분산** | show_* 플래그와 실제 렌더링 불일치 | 조건 로직 중복 |
| 5 | **데이터-뷰 결합** | 계산과 표현이 섞임 | 관심사 분리 실패 |

---

## 2. 근본적 해결 방안

### 방안 A: 중앙 집중식 데이터 정의 (Schema-First)

**개념**: 모든 데이터 정의를 한 곳에서 관리

**구현**:
```python
# payslip_schema.py - 단일 출처 원칙
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class ItemType(Enum):
    BASE_PAY = "기본급"
    HOLIDAY_ALLOWANCE = "주휴수당"
    OVERTIME_PAY = "연장수당"
    NIGHT_PAY = "야간수당"
    POSITION_ALLOWANCE = "직급수당"
    OTHER_ALLOWANCE = "기타수당"

@dataclass(frozen=True)  # 불변 객체
class PayslipField:
    """급여명세서 필드 정의 - 모든 로직/템플릿이 이것을 참조"""
    name: str                    # 로직에서 사용하는 이름 (snake_case)
    display_name: str            # 템플릿에서 표시할 이름
    type: str                    # 데이터 타입
    required: bool = True        # 필수 여부
    show_flag: Optional[str] = None  # 조걶%20표시 플래그
    validation_rules: List[str] = field(default_factory=list)
    
    @property
    def template_var(self) -> str:
        """Jinja2 템플릿 변수명"""
        return self.name

# 중앙 집중식 필드 정의
PAYSLIP_FIELDS = {
    # 기본 정보
    'data_month': PayslipField('data_month', '급여 월', 'str'),
    'company_name': PayslipField('company_name', '회사명', 'str'),
    'name': PayslipField('name', '성명', 'str'),
    'user_id': PayslipField('user_id', '사번', 'str'),
    
    # 지급 항목
    'base_pay': PayslipField(
        'base_pay', '기본급', 'float',
        show_flag='show_base_pay_note',
        validation_rules=['min:0']
    ),
    'weekly_holiday_allowance': PayslipField(
        'weekly_holiday_allowance', '주휴수당', 'float',
        show_flag='show_holiday_note'
    ),
    'extra_pay': PayslipField(
        'extra_pay', '연장수당', 'float',
        show_flag='show_overtime_note'
    ),
    'night_pay': PayslipField(
        'night_pay', '야간수당', 'float',
        show_flag='show_night_note'  # ← 이것이 자동으로 연결!
    ),
    
    # 계산식
    'calculation_note_1': PayslipField('calculation_note_1', '기본급 산출식', 'str'),
    'calculation_note_2': PayslipField('calculation_note_2', '주휴수당 산출식', 'str'),
    'calculation_note_3': PayslipField('calculation_note_3', '연장수당 산출식', 'str'),
    'calculation_note_night': PayslipField(
        'calculation_note_night', '야간수당 산출식', 'str',
        show_flag='show_night_note'  # ← 동일한 플래그 공유
    ),
}
```

**템플릿 코드 생성**:
```python
# generate_template_code.py
from payslip_schema import PAYSLIP_FIELDS

def generate_template_snippet():
    """스키마에서 템플릿 코드 자동 생성"""
    lines = ['<div class="calculation-notes">']
    lines.append('    <div class="title">계산 상세 내역</div>')
    
    for field_name, field in PAYSLIP_FIELDS.items():
        if 'calculation_note' in field_name:
            if field.show_flag:
                lines.append(f'    {{{{% if {field.show_flag} %}}}}')
                lines.append(f'    <p><strong>{field.display_name}:</strong> {{{{ {field.name} }}}}</p>')
                lines.append(f'    {{{{% endif %}}}}')
            else:
                lines.append(f'    <p><strong>{field.display_name}:</strong> {{{{ {field.name} }}}}</p>')
    
    lines.append('</div>')
    return '\n'.join(lines)

# 자동 생성된 코드
print(generate_template_snippet())
```

**생성 결과**:
```html
<div class="calculation-notes">
    <div class="title">계산 상세 내역</div>
    <p><strong>기본급 산출식:</strong> {{ calculation_note_1 }}</p>
    <p><strong>주휴수당 산출식:</strong> {{ calculation_note_2 }}</p>
    <p><strong>연장수당 산출식:</strong> {{ calculation_note_3 }}</p>
    {% if show_night_note %}
    <p><strong>야간수당 산출식:</strong> {{ calculation_note_night }}</p>
    {% endif %}
</div>
```

---

### 방안 B: 파이프라인 아키텍처 (Pipeline)

**개념**: 데이터 흐름을 단방향 파이프라인으로 구성

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   입력      │ →  │   검증      │ →  │   변환      │ →  │   렌더링    │
│  (로직)     │    │  (스키마)    │    │  (어댑터)   │    │  (템플릿)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
  raw_data          validated_data     template_data        html
  (DataFrame)       (TypedDict)        (Context)            (String)
```

**구현**:
```python
# pipeline.py
from typing import TypedDict, Callable
from dataclasses import dataclass

class PipelineStage:
    """파이프라인 스테이지 기반 클래스"""
    def process(self, data):
        raise NotImplementedError

@dataclass
class PayslipPipeline:
    """급여명세서 생성 파이프라인"""
    stages: List[Callable] = field(default_factory=list)
    
    def add_stage(self, stage: Callable):
        self.stages.append(stage)
        return self
    
    def execute(self, initial_data):
        data = initial_data
        for stage in self.stages:
            data = stage(data)
            if data is None:
                raise ValueError(f"Stage {stage.__name__} returned None")
        return data

# 파이프라인 구성
def create_payslip_pipeline():
    return (
        PayslipPipeline()
        .add_stage(load_data)           # 1. 데이터 로드
        .add_stage(validate_input)      # 2. 입력 검증
        .add_stage(calculate_salary)    # 3. 급여 계산
        .add_stage(validate_calculation) # 4. 계산 검증
        .add_stage(transform_to_context) # 5. 템플릿 컨텍스트 변환
        .add_stage(validate_context)    # 6. 컨텍스트 검증 ★ 핵심
        .add_stage(render_template)     # 7. 템플릿 렌더링
        .add_stage(validate_html)       # 8. HTML 검증
    )

# 사용
pipeline = create_payslip_pipeline()
html = pipeline.execute({
    'file_path': '12월 급여포함.xlsx',
    'year_month': '2025-12',
    'employee_data': {...}
})
```

---

### 방안 C: 계약 기반 프로그래밍 (Contract-Based)

**개념**: 사전/사후 조건을 명시적으로 정의

```python
# contracts.py
from functools import wraps
import inspect

class ContractViolation(Exception):
    pass

def requires(**conditions):
    """사전 조건 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 인자 바인딩
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            
            # 조건 검사
            for var, check in conditions.items():
                if var in bound.arguments:
                    value = bound.arguments[var]
                    if not check(value):
                        raise ContractViolation(
                            f"{func.__name__}: {var} 조건 위반 - 값: {value}"
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def ensures(**conditions):
    """사후 조건 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # 반환값 검사
            for var, check in conditions.items():
                if var == 'return':
                    if not check(result):
                        raise ContractViolation(
                            f"{func.__name__}: 반환값 조건 위반"
                        )
                elif isinstance(result, dict) and var in result:
                    if not check(result[var]):
                        raise ContractViolation(
                            f"{func.__name__}: {var} 반환값 조건 위반"
                        )
            
            return result
        return wrapper
    return decorator

# 적용
@requires(
    user_summary=lambda x: 'name' in x,
    data_month=lambda x: isinstance(x, str) and '년' in x and '월' in x
)
@ensures(
    return=lambda x: isinstance(x, dict),
    calculation_note_night=lambda x: isinstance(x, str) and len(x) > 0,
    show_night_note=lambda x: isinstance(x, bool)
)
def _prepare_payslip_data(user_summary, data_month, ...):
    """계약에 의해 보장된 함수"""
    ...
```

---

### 방안 D: 이벤트 소싱 패턴 (Event Sourcing)

**개념**: 상태 변경을 이벤트로 기록하고 재생

```python
# events.py
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List

@dataclass
class PayslipEvent:
    """급여명세서 생성 이벤트"""
    timestamp: datetime
    event_type: str
    data: dict
    
@dataclass
class CalculationEvent(PayslipEvent):
    employee_id: str
    field_name: str
    old_value: float
    new_value: float
    formula: str

class PayslipEventStore:
    """이벤트 저장소"""
    def __init__(self):
        self.events: List[PayslipEvent] = []
    
    def record(self, event: PayslipEvent):
        self.events.append(event)
    
    def replay(self, employee_id: str) -> dict:
        """이벤트 재생으로 최종 상태 복원"""
        state = {}
        for event in self.events:
            if isinstance(event, CalculationEvent) and event.employee_id == employee_id:
                state[event.field_name] = event.new_value
        return state
    
    def audit_trail(self, employee_id: str) -> List[dict]:
        """감사 추적"""
        return [
            asdict(e) for e in self.events
            if hasattr(e, 'employee_id') and e.employee_id == employee_id
        ]

# 사용
store = PayslipEventStore()

# 계산 과정 기록
store.record(CalculationEvent(
    timestamp=datetime.now(),
    event_type='BASE_PAY_CALCULATED',
    employee_id='190335406',
    field_name='base_pay',
    old_value=0,
    new_value=2000000,
    formula='160시간 * 12500원',
    data={'hours': 160, 'rate': 12500}
))

# 나중에 검증
final_state = store.replay('190335406')
audit = store.audit_trail('190335406')
```

---

## 3. 즉시 적용 가능한 근본적 해결

### Step 1: 단일 스키마 파일 도입 (오늘)

```bash
# 1. 스키마 파일 생성
touch payslip_schema.py

# 2. 모든 변수 정의 중앙화
# 3. 로직과 템플릿이 스키마를 참조하도록 수정
```

### Step 2: 검증 레이어 도입 (내일)

```bash
# 1. validation.py 생성
touch validation.py

# 2. _prepare_payslip_data에 검증 추가
# 3. generate_payslips_html에 검증 추가
```

### Step 3: 코드 생성 도구 (이번 주)

```bash
# 1. generate_template_code.py 생성
# 2. 스키마에서 템플릿 코드 자동 생성
# 3. CI/CD에 통합
```

---

## 4. 예상 효과

| 항목 | Before | After |
|------|--------|-------|
| 변수 추가 시간 | 30분 (수정+검증) | 5분 (스키마만 수정) |
| 오류 발견 시점 | 런타임/사용자 신고 | 개발 시점 (검증) |
| 변수명 불일치 | 빈번 | 없음 (코드 생성) |
| 조건 분기 누락 | 발생 | 자동 연결 |
| 유지보수성 | 낮음 | 높음 |

---

## 5. 결론

**근본적 문제**: 데이터 정의 분산 + 검증 부재 + 수동 동기화

**근본적 해결**: 
1. **스키마 중앙화** - 단일 출처 원칙
2. **파이프라인 아키텍처** - 단방향 데이터 흐름
3. **계약 기반** - 사전/사후 조건 강제
4. **코드 생성** - 사람의 실수 제거

이 방식을 도입하면 HTML-로직 불일치 문제가 영구적으로 해결됩니다.
