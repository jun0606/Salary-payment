# HTML 결과물-로직 일관성 문제 해결 방안

**작성일**: 2026년 2월 10일  
**작성자**: Cline Assistant  
**관련 파일**: `payslip_template.html`, `logic.py`

---

## 🔴 문제 1: 야간수당 산출식 미표시 (심각)

### 문제 설명
- 로직(`logic.py`)에서 `calculation_note_night`를 반환하지만
- 템플릿(`payslip_template.html`)에서 해당 변수를 표시하지 않음
- 결과: 사용자가 야간수당 계산식을 확인할 수 없음

### 해결 방안

#### 방법 A: 템플릿에 야간수당 산출식 추가 (권장)

**파일**: `payslip_template.html`

**위치**: `<div class="calculation-notes">` 섹션

**변경 전**:
```html
<div class="calculation-notes">
    <div class="title">계산 상세 내역</div>
    {% if show_base_pay_note %}<p><strong>기본급 산출식:</strong> {{ calculation_note_1 }}</p>{% endif %}
    {% if show_holiday_note %}<p><strong>주휴수당 산출식:</strong> {{ calculation_note_2 }}</p>{% endif %}
    {% if show_overtime_note %}<p><strong>연장수당 산출식:</strong> {{ calculation_note_3 }}</p>{% endif %}
    {% if show_hourly_rate %}<p><strong>시급:</strong> {{ "{:,.0f}".format(hourly_rate) }}원</p>{% endif %}
</div>
```

**변경 후**:
```html
<div class="calculation-notes">
    <div class="title">계산 상세 내역</div>
    {% if show_base_pay_note %}<p><strong>기본급 산출식:</strong> {{ calculation_note_1 }}</p>{% endif %}
    {% if show_holiday_note %}<p><strong>주휴수당 산출식:</strong> {{ calculation_note_2 }}</p>{% endif %}
    {% if show_overtime_note %}<p><strong>연장수당 산출식:</strong> {{ calculation_note_3 }}</p>{% endif %}
    {% if show_night_note %}<p><strong>야간수당 산출식:</strong> {{ calculation_note_night }}</p>{% endif %}
    {% if show_hourly_rate %}<p><strong>시급:</strong> {{ "{:,.0f}".format(hourly_rate) }}원</p>{% endif %}
</div>
```

**적용 효과**: 
- ✅ 야간수당 산출식이 계산 상세 내역에 표시됨
- ✅ `show_night_note` 옵션으로 표시 여부 제어 가능
- ✅ 기존 UI 스타일과 일관성 유지

---

## 🟡 문제 2: 공제 항목 rowspan 불일치

### 문제 설명
- 공제 항목이 6개 (국민연금, 건강보험, 고용보험, 장기요양보험, 소득세, 지방소득세)
- `rowspan="5"`로 설정되어 마지막 지방소득세 행에는 비고가 표시되지 않음

### 해결 방안

#### 방법 A: rowspan 값 수정 (단순)

**파일**: `payslip_template.html`

**변경 전**:
```html
<tr>
    <td></td>
    <td></td>
    <td>국민연금</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(national_pension) }}원</td>
    <td rowspan="5">{{ calculation_note_1 }}</td>
</tr>
```

**변경 후**:
```html
<tr>
    <td></td>
    <td></td>
    <td>국민연금</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(national_pension) }}원</td>
    <td rowspan="6">{{ calculation_note_1 }}</td>
</tr>
```

**적용 효과**:
- ✅ 모든 공제 항목 행에 비고(기본급 산출식)가 표시됨
- ✅ 레이아웃 일관성 확보

#### 방법 B: 비고 내용 분리 (대안)

모든 공제 항목에 동일한 비고가 표시되는 것이 부적절하다면:

```html
<tr>
    <td></td>
    <td></td>
    <td>국민연금</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(national_pension) }}원</td>
    <td rowspan="2">4대보험<br>공제내역</td>
</tr>
<tr>
    <td></td>
    <td></td>
    <td>건강보험</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(health_insurance) }}원</td>
</tr>
<tr>
    <td></td>
    <td></td>
    <td>고용보험</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(employment_insurance) }}원</td>
    <td rowspan="2">세금<br>공제내역</td>
</tr>
<tr>
    <td></td>
    <td></td>
    <td>장기요양보험</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(long_term_care_insurance) }}원</td>
</tr>
<tr>
    <td></td>
    <td></td>
    <td>소득세</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(income_tax) }}원</td>
    <td rowspan="2">지방세</td>
</tr>
<tr>
    <td></td>
    <td></td>
    <td>지방소득세</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(local_income_tax) }}원</td>
</tr>
```

---

## 🟡 문제 3: 미사용 변수 정리

### 문제 설명
- `allowance_total`과 `show_night_note`가 로직에서 반환되지만 템플릿에서 미사용
- 코드 혼란 및 유지보수성 저하

### 해결 방안

#### 방법 A: 변수 사용 (권장)

`show_night_note`는 문제 1 해결로 자동 사용됨

`allowance_total`을 템플릿에 추가하려면:

**파일**: `payslip_template.html`

**변경**: allowance_items 순회 후 수당합계 행 추가

```html
<!-- 모든 지급 항목 동적 표시 -->
{% for allowance in allowance_items %}
<tr>
    <td>{{ allowance.name }}</td>
    <td class="amount">{{ "{:,.0f}".format(allowance.amount) }}원</td>
    <td></td>
    <td></td>
    <td>{{ allowance.detail }}</td>
</tr>
{% endfor %}

<!-- 수당합계 행 추가 (선택사항) -->
{% if allowance_total > 0 %}
<tr style="background-color: #e8f5e8;">
    <td><strong>수당합계</strong></td>
    <td class="amount"><strong>{{ "{:,.0f}".format(allowance_total) }}원</strong></td>
    <td></td>
    <td></td>
    <td>직급수당 및 기타수당 합계</td>
</tr>
{% endif %}
```

#### 방법 B: 미사용 변수 제거

**파일**: `logic.py`

**변경**: `_prepare_payslip_data()` 함수의 return 문 수정

```python
# 변경 전
return {
    # ... 다른 변수들
    'allowance_total': user_summary.get('수당합계', 0),  # 제거 대상
    'show_night_note': explanation_options.get('night_explanation', True),  # 사용되지 않음
    # ...
}

# 변경 후
return {
    # ... 다른 변수들
    # 'allowance_total': user_summary.get('수당합계', 0),  # 제거
    'show_night_note': explanation_options.get('night_explanation', True),  # 문제 1 해결 시 사용
    # ...
}
```

---

## 🛠️ 적용 우선순위 및 절차

### 우선순위 1 (즉시 적용 권장)
1. **야간수당 산출식 표시 추가** (문제 1)
   - 파일: `payslip_template.html`
   - 위험도: 낮음
   - 영향: 사용자 경험 향상

### 우선순위 2 (선택적 적용)
2. **rowspan 수정** (문제 2)
   - 파일: `payslip_template.html`
   - 위험도: 낮음
   - 영향: 레이아웃 일관성

3. **미사용 변수 정리** (문제 3)
   - 파일: `logic.py`, `payslip_template.html`
   - 위험도: 중간 (기능 변경 가능성)
   - 영향: 코드 품질 개선

---

## 🧪 테스트 계획

### 테스트 시나리오

1. **야간수당 표시 테스트**
   ```
   - 야간근무 시간이 있는 직원 데이터 준비
   - HTML 생성 실행
   - 계산 상세 내역에 야간수당 산출식 표시 확인
   - show_night_note 옵션 ON/OFF 확인
   ```

2. **레이아웃 테스트**
   ```
   - 모든 공제 항목이 표시되는지 확인
   - 비고 컬럼이 모든 행에 적절히 표시되는지 확인
   - 인쇄 레이아웃 확인
   ```

3. **회귀 테스트**
   ```
   - 기존 기능(기본급, 주휴수당, 연장수당 표시) 확인
   - 다양한 브라우저에서 렌더링 확인
   - 금액 포맷팅 확인
   ```

---

## 📋 수정 체크리스트

- [ ] `payslip_template.html`에 야간수당 산출식 추가
- [ ] `rowspan="5"` → `rowspan="6"` 변경
- [ ] 수정 후 HTML 파일 생성 테스트
- [ ] 다양한 데이터(야간근무 유/무)로 테스트
- [ ] 기존 기능 회귀 테스트

---

## 📝 참고사항

1. **백업 필수**: 수정 전 `payslip_template.html` 백업 권장
2. **점진적 적용**: 우선순위 1부터 순차적으로 적용
3. **버전 관리**: Git 커밋 시 변경사항 명확히 기록
4. **문서화**: 적용 완료 후 관련 문서 업데이트

---

**최종 수정일**: 2026년 2월 10일  
**담당자**: _______________
