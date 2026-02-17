# HTML 결과물과 로직 일관성 분석 보고서

**분석일**: 2026년 2월 10일  
**대상 파일**: `logic.py`, `payslip_template.html`, `test_output.html`, `monthly_payroll_pane_qt.py`

---

## 1. 개요

본 보고서는 급여명세서 시스템의 **로직 계산 결과**와 **HTML 출력 결과** 간의 일관성을 분석한 내용입니다.

---

## 2. 변수 매핑 일관성 분석

### 2.1 `_prepare_payslip_data()` 반환 변수 vs 템플릿 사용 변수

| 반환 변수 | 템플릿 사용 여부 | 상태 | 비고 |
|-----------|------------------|------|------|
| `data_month` | ✅ 사용됨 | 정상 | 헤더 표시 |
| `company_name` | ✅ 사용됨 | 정상 | 회사명 표시 |
| `name` | ✅ 사용됨 | 정상 | 직원명 표시 |
| `user_id` | ✅ 사용됨 | 정상 | 사번 표시 |
| `department` | ✅ 사용됨 | 정상 | 부서 표시 |
| `position` | ✅ 사용됨 | 정상 | 직급 표시 |
| `hire_date` | ✅ 사용됨 | 정상 | 입사일 표시 |
| `payment_date` | ✅ 사용됨 | 정상 | 지급일 표시 |
| `base_pay` | ✅ 사용됨 | 정상 | 기본급 (allowance_items로) |
| `weekly_holiday_allowance` | ✅ 사용됨 | 정상 | 주휴수당 (allowance_items로) |
| `extra_pay` | ✅ 사용됨 | 정상 | 연장수당 (allowance_items로) |
| `night_pay` | ✅ 사용됨 | 정상 | 야간수당 (allowance_items로) |
| `allowance_total` | ❌ **미사용** | ⚠️ 주의 | 템플릿에서 직접 사용되지 않음 |
| `allowance_items` | ✅ 사용됨 | 정상 | 지급 항목 리스트 순회 |
| `national_pension` | ✅ 사용됨 | 정상 | 국민연금 |
| `health_insurance` | ✅ 사용됨 | 정상 | 건강보험 |
| `employment_insurance` | ✅ 사용됨 | 정상 | 고용보험 |
| `long_term_care_insurance` | ✅ 사용됨 | 정상 | 장기요양보험 |
| `income_tax` | ✅ 사용됨 | 정상 | 소득세 |
| `local_income_tax` | ✅ 사용됨 | 정상 | 지방소득세 |
| `total_payment` | ✅ 사용됨 | 정상 | 지급합계 |
| `total_deduction` | ✅ 사용됨 | 정상 | 공제합계 |
| `net_pay` | ✅ 사용됨 | 정상 | 실지급액 |
| `hourly_rate` | ✅ 사용됨 | 정상 | 시급 표시 |
| `calculation_note_1` | ✅ 사용됨 | 정상 | 기본급 산출식 |
| `calculation_note_2` | ✅ 사용됨 | 정상 | 주휴수당 산출식 |
| `calculation_note_3` | ✅ 사용됨 | 정상 | 연장수당 산출식 |
| `calculation_note_night` | ❌ **미사용** | ⚠️ 주의 | 템플릿에 전달되지만 미표시 |
| `show_base_pay_note` | ✅ 사용됨 | 정상 | 조걶%20렌더링 |
| `show_holiday_note` | ✅ 사용됨 | 정상 | 조걶%20렌더링 |
| `show_overtime_note` | ✅ 사용됨 | 정상 | 조걶%20렌더링 |
| `show_night_note` | ❌ **미사용** | ⚠️ 주의 | 템플릿에 없음 |
| `show_hourly_rate` | ✅ 사용됨 | 정상 | 시급 표시 여부 |

---

## 3. 발견된 일관성 문제점

### 3.1 🔴 심각: `calculation_note_night` 미표시 문제

**위치**: `logic.py`의 `_prepare_payslip_data()` 함수

**문제 설명**:
- 로직에서 `calculation_note_night` (야간수당 산출식)을 반환함
- 하지만 `payslip_template.html`의 계산식 섹션에는 야간수당 산출식이 없음

**로직 코드** (logic.py):
```python
return {
    # ...
    'calculation_note_night': calculation_note_night,  # 야간수당 산출식 추가
    # ...
}
```

**템플릿 누락** (payslip_template.html):
```html
<div class="calculation-notes">
    <div class="title">계산 상세 내역</div>
    {% if show_base_pay_note %}<p><strong>기본급 산출식:</strong> {{ calculation_note_1 }}</p>{% endif %}
    {% if show_holiday_note %}<p><strong>주휴수당 산출식:</strong> {{ calculation_note_2 }}</p>{% endif %}
    {% if show_overtime_note %}<p><strong>연장수당 산출식:</strong> {{ calculation_note_3 }}</p>{% endif %}
    {% if show_hourly_rate %}<p><strong>시급:</strong> {{ "{:,.0f}".format(hourly_rate) }}원</p>{% endif %}
    <!-- ⚠️ 야간수당 산출식 누락! -->
</div>
```

**권장 수정**:
```html
{% if show_night_note %}<p><strong>야간수당 산출식:</strong> {{ calculation_note_night }}</p>{% endif %}
```

---

### 3.2 🟡 주의: `allowance_total` 필드 미사용

**문제 설명**:
- `allowance_total` (수당합계)가 `_prepare_payslip_data()`에서 반환됨
- 템플릿에서는 직접 사용되지 않고, 개별 `allowance_items`로 표시됨
- 이는 의도된 설계일 수 있으나, "수당합계" 행이 누락될 수 있음

**현재 동작**:
```python
allowance_items = [
    {'name': '기본급', 'amount': base_pay, ...},
    {'name': '주휴수당', 'amount': weekly_allowance, ...},
    {'name': '연장수당', 'amount': overtime_pay, ...},
    {'name': '야간수당', 'amount': night_pay, ...},
    # 수당 항목들도 여기에 추가
]
```

**검증 결과**: ✅ 의도된 설계 - 개별 항목으로 표시되어 사용자가 상세 내역 확인 가능

---

### 3.3 🟡 주의: `show_night_note` 플래그 미사용

**문제 설명**:
- `_prepare_payslip_data()`에서 `show_night_note`를 반환함
- 하지만 템플릿에서는 이 플래그를 사용하지 않음

**로직**:
```python
'show_night_note': explanation_options.get('night_explanation', True),
```

**템플릿**: 해당 플래그 사용 부분 없음

---

### 3.4 🟢 정상: `extra_pay` 필드명 일관성

**검증 결과**: 정상

- `monthly_payroll_pane_qt.py`: `extra_pay`로 테이블 표시
- `logic.py`: `extra_pay`를 `allowance_items`의 "연장수당"으로 매핑
- `_prepare_payslip_data()`:
  ```python
  overtime_pay = user_summary.get('연장수당', 0)
  # ...
  allowance_items.append({
      'name': '연장수당',
      'amount': overtime_pay,
      ...
  })
  ```

---

### 3.5 🟢 정상: 금액 포맷팅 일관성

**로직** (logic.py):
```python
# 수식 표현에서 사용
calculation_note_3 = f"연장근무 {ot_hours:.1f}시간 × 시급 {hourly_rate:,}원 × {ot_multiplier}{premium_label} = {overtime_pay:,.0f}원"
```

**템플릿** (payslip_template.html):
```html
<td class="amount">{{ "{:,.0f}".format(allowance.amount) }}원</td>
```

**검증 결과**: 
- 둘 다 `{:,.0f}` 형식 사용 (쉼표 구분자 + 소수점 이하 0자리)
- 일관성 있게 적용됨 ✅

---

### 3.6 🟡 주의: 공제 항목 rowspan 설정

**템플릿 코드**:
```html
<tr>
    <td></td>
    <td></td>
    <td>국민연금</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(national_pension) }}원</td>
    <td rowspan="5">{{ calculation_note_1 }}</td>  <!-- ⚠️ 5행 span -->
</tr>
```

**검증 결과**:
- 공제 항목이 6개 (국민연금, 건강보험, 고용보험, 장기요양보험, 소득세, 지방소득세)
- `rowspan="5"`로 설정되어 마지막 지방소득세 행에는 비고가 표시되지 않음
- **test_output.html 확인 결과**: 실제로 5행까지만 적용됨

**현재 동작**:
```html
<!-- 국민연금 행: 비고에 기본급 산출식 -->
<!-- 지방소득세 행: 비고 없음 -->
```

**권장사항**: `rowspan="6"`으로 변경 또는 마지막 행 처리 확인

---

## 4. 데이터 흐름 검증

### 4.1 HTML 생성 흐름

```
monthly_payroll_pane_qt.py
    ↓ logic.generate_payslips_html()
    ↓ _prepare_payslip_data()  [데이터 준비]
    ↓ template.render(**payslip_data)  [Jinja2 렌더링]
    ↓ test_output.html  [최종 출력]
```

### 4.2 핵심 데이터 변환 검증

| 소스 데이터 | 중간 변환 | HTML 출력 | 상태 |
|-------------|-----------|-----------|------|
| `연장수당` | `extra_pay` → `allowance_items['연장수당']` | "연장수당" 행 | ✅ 정상 |
| `night_pay` | `allowance_items['야간수당']` | "야간수당" 행 | ✅ 정상 |
| `weekly_holiday_allowance` | `allowance_items['주휴수당']` | "주휴수당" 행 | ✅ 정상 |
| `base_pay` | `allowance_items['기본급']` | "기본급" 행 | ✅ 정상 |
| `수당합계` (직급수당 등) | `allowance_items`에 추가 | 각 수당별 행 | ✅ 정상 |

---

## 5. 최종 평가

### 5.1 심각도별 문제 요약

| 심각도 | 개수 | 내용 |
|--------|------|------|
| 🔴 심각 | 1 | `calculation_note_night` 미표시 |
| 🟡 주의 | 3 | `allowance_total` 미사용, `show_night_note` 미사용, rowspan 불일치 |
| 🟢 정상 | 2 | 금액 포맷팅, 필드명 일관성 |

### 5.2 계산 정확도 평가

| 항목 | 정확도 | 비고 |
|------|--------|------|
| 기본급 계산 | ✅ 정확 | 시간 × 시급 |
| 주휴수당 계산 | ✅ 정확 | 주휴시간 × 시급 |
| 연장수당 계산 | ✅ 정확 | 시간 × 시급 × 배수 |
| 야간수당 계산 | ✅ 정확 | 시간 × 시급 × 0.5배 |
| 공제 항목 계산 | ✅ 정상 | 세법 기준 적용 |
| 실지급액 계산 | ✅ 정확 | 지급합계 - 공제합계 |

---

## 6. 권장 조치사항

### 6.1 즉시 수정 필요 (높은 우선순위)

1. **야간수당 산출식 표시 추가**
   ```html
   <!-- payslip_template.html -->
   {% if show_night_note %}<p><strong>야간수당 산출식:</strong> {{ calculation_note_night }}</p>{% endif %}
   ```

### 6.2 개선 권장 (중간 우선순위)

2. **rowspan 수정** (선택사항)
   ```html
   <!-- 5 → 6으로 수정 -->
   <td rowspan="6">{{ calculation_note_1 }}</td>
   ```

3. **미사용 변수 정리** (선택사항)
   - `allowance_total`, `show_night_note` 사용 또는 제거 검토

---

## 7. 결론

HTML 결과물과 로직은 **대체로 일관성**이 있습니다. 계산 로직은 정확하게 구현되었고, HTML 출력도 의도된 대로 표시됩니다.

주요 문제는 **야간수당 산출식의 누락** 하나뿐이며, 이는 템플릿에 간단히 추가하여 해결할 수 있습니다. 금액 계산 및 표시 로직은 모두 정확하게 작동하고 있습니다.

---

**분석 완료**: 2026년 2월 10일  
**분석자**: Cline Assistant
