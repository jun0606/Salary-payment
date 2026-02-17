# HTML 템플릿 변수 추가 수정 계획

## 📋 개요

HTML-로직 일관성 문제 해결을 위한 Phase 1: 긴급 수정 단계의 구체적인 실행 계획입니다.

## 🎯 목표

템플릿과 로직 간의 변수 불일치 문제를 해결하여 HTML 렌더링 시 발생하는 오류를 방지합니다.

## 📊 현재 상황

### 검증 결과 (2026-02-10)
- **템플릿 변수 수**: 13개
- **로직 변수 수**: 36개
- **동기화 상태**: ❌ 불일치
- **누락 변수 수**: 23개

### 주요 누락 변수
```
1. base_pay - 기본급 금액
2. weekly_holiday_allowance - 주휴수당 금액
3. extra_pay - 연장수당 금액
4. night_pay - 야간수당 금액
5. allowance_total - 기타수당 총액
6. national_pension - 국민연금 금액
7. health_insurance - 건강보험 금액
8. employment_insurance - 고용보험 금액
9. long_term_care_insurance - 장기요양보험 금액
10. income_tax - 소득세 금액
11. local_income_tax - 지방소득세 금액
12. total_payment - 지급총액
13. total_deduction - 공제총액
14. net_pay - 실지급액
15. hourly_rate - 시급
16. show_base_pay_note - 기본급 설명 표시 옵션
17. show_holiday_note - 주휴수당 설명 표시 옵션
18. show_overtime_note - 연장수당 설명 표시 옵션
19. show_night_note - 야간수당 설명 표시 옵션
20. show_hourly_rate - 시급 표시 옵션
21. allowance_items - 수당 상세 항목 리스트
22. allowance_name - 수당명 (템플릿에 존재)
23. allowance_detail - 수당 상세 (템플릿에 존재)
```

## 🚀 실행 계획

### Phase 1: 긴급 수정 (목표: 오늘 완료)

#### 1단계: 핵심 변수 추가 (우선순위: 높음)
- **목표**: 지급/공제 금액 표시에 필수적인 변수 추가
- **예상 소요 시간**: 30분
- **추가 변수**:
  - `base_pay` - 기본급 금액
  - `weekly_holiday_allowance` - 주휴수당 금액
  - `extra_pay` - 연장수당 금액
  - `night_pay` - 야간수당 금액
  - `allowance_total` - 기타수당 총액
  - `national_pension` - 국민연금 금액
  - `health_insurance` - 건강보험 금액
  - `employment_insurance` - 고용보험 금액
  - `long_term_care_insurance` - 장기요양보험 금액
  - `income_tax` - 소득세 금액
  - `local_income_tax` - 지방소득세 금액

#### 2단계: 합계 변수 추가 (우선순위: 높음)
- **목표**: 총액 계산에 필요한 변수 추가
- **예상 소요 시간**: 15분
- **추가 변수**:
  - `total_payment` - 지급총액
  - `total_deduction` - 공제총액
  - `net_pay` - 실지급액

#### 3단계: 옵션 변수 추가 (우선순위: 중간)
- **목표**: 조건부 렌더링에 필요한 옵션 변수 추가
- **예상 소요 시간**: 20분
- **추가 변수**:
  - `show_base_pay_note` - 기본급 설명 표시 옵션
  - `show_holiday_note` - 주휴수당 설명 표시 옵션
  - `show_overtime_note` - 연장수당 설명 표시 옵션
  - `show_night_note` - 야간수당 설명 표시 옵션
  - `show_hourly_rate` - 시급 표시 옵션

#### 4단계: 부가 변수 추가 (우선순위: 낮음)
- **목표**: 상세 정보 표시에 필요한 변수 추가
- **예상 소요 시간**: 15분
- **추가 변수**:
  - `hourly_rate` - 시급
  - `allowance_items` - 수당 상세 항목 리스트

### Phase 2: 검증 및 테스트 (목표: 오늘 완료)

#### 1단계: 템플릿 검증
- **목표**: 변수 추가 후 템플릿 정상 동작 확인
- **예상 소요 시간**: 10분
- **검증 항목**:
  - 변수 렌더링 정상 확인
  - Jinja2 문법 오류 검사
  - HTML 구조 유효성 검사

#### 2단계: 로직 연동 테스트
- **목표**: logic.py와의 연동 정상 확인
- **예상 소요 시간**: 15분
- **검증 항목**:
  - 변수 전달 정상 확인
  - HTML 생성 정상 확인
  - 금액 일관성 검증

#### 3단계: 전체 시스템 검증
- **목표**: sync_checker.py로 전체 검증
- **예상 소요 시간**: 10분
- **검증 항목**:
  - 템플릿-로직 동기화 상태 확인
  - 누락 변수 수 감소 확인
  - 최종 동기화 상태 평가

## 📝 상세 작업 내용

### 1. 템플릿 변수 추가 작업

#### 1.1 지급 항목 변수 추가
```html
<!-- 기본급 표시 -->
<tr>
    <td>기본급</td>
    <td class="amount">{{ "{:,.0f}".format(base_pay) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 주휴수당 표시 -->
<tr>
    <td>주휴수당</td>
    <td class="amount">{{ "{:,.0f}".format(weekly_holiday_allowance) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 연장수당 표시 -->
<tr>
    <td>연장수당</td>
    <td class="amount">{{ "{:,.0f}".format(extra_pay) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 야간수당 표시 -->
<tr>
    <td>야간수당</td>
    <td class="amount">{{ "{:,.0f}".format(night_pay) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 기타수당 표시 -->
<tr>
    <td>기타수당</td>
    <td class="amount">{{ "{:,.0f}".format(allowance_total) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>
```

#### 1.2 공제 항목 변수 추가
```html
<!-- 국민연금 표시 -->
<tr>
    <td>국민연금</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(national_pension) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 건강보험 표시 -->
<tr>
    <td>건강보험</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(health_insurance) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 고용보험 표시 -->
<tr>
    <td>고용보험</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(employment_insurance) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 장기요양보험 표시 -->
<tr>
    <td>장기요양보험</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(long_term_care_insurance) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 소득세 표시 -->
<tr>
    <td>소득세</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(income_tax) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>

<!-- 지방소득세 표시 -->
<tr>
    <td>지방소득세</td>
    <td class="amount deduction-amount">{{ "{:,.0f}".format(local_income_tax) }}원</td>
    <!-- 기존 내용 유지 -->
</tr>
```

#### 1.3 합계 변수 추가
```html
<!-- 총계 표시 -->
<tr class="total-row">
    <td>합계</td>
    <td class="amount">{{ "{:,.0f}".format(total_payment) }}원</td>
    <td>합계</td>
    <td class="amount">{{ "{:,.0f}".format(total_deduction) }}원</td>
    <td></td>
</tr>

<!-- 실지급액 표시 -->
<tr class="net-pay-row">
    <td colspan="2" style="text-align: center;">실지급액</td>
    <td class="amount" colspan="2">{{ "{:,.0f}".format(net_pay) }}원</td>
    <td></td>
</tr>
```

#### 1.4 옵션 변수 추가
```html
<!-- 조건부 렌더링 옵션 -->
{% if show_base_pay_note %}<p><strong>기본급 산출식:</strong> {{ calculation_note_1 }}</p>{% endif %}
{% if show_holiday_note %}<p><strong>주휴수당 산출식:</strong> {{ calculation_note_2 }}</p>{% endif %}
{% if show_overtime_note %}<p><strong>연장수당 산출식:</strong> {{ calculation_note_3 }}</p>{% endif %}
{% if show_night_note %}<p><strong>야간수당 산출식:</strong> {{ calculation_note_night }}</p>{% endif %}
{% if show_hourly_rate %}<p><strong>시급:</strong> {{ "{:,.0f}".format(hourly_rate) }}원</p>{% endif %}
```

### 2. 검증 스크립트 실행

#### 2.1 템플릿 변수 검증
```bash
cd /Volumes/MyExternal/급여명세서
python3 sync_checker.py
```

#### 2.2 예상 결과
- 템플릿 변수 수: 13개 → 36개
- 로직 변수 수: 36개 (변경 없음)
- 동기화 상태: ❌ 불일치 → ✅ 일치
- 누락 변수 수: 23개 → 0개

## ⚠️ 주의사항

### 1. 변수 형식 일치
- 모든 금액 변수는 `"{:,.0f}".format()` 형식으로 포맷팅
- 옵션 변수는 boolean 형식으로 전달
- 리스트 변수는 Jinja2 반복문으로 처리

### 2. HTML 구조 보존
- 기존 HTML 구조와 스타일은 최대한 보존
- 새로운 변수 추가 시 기존 레이아웃과 충돌하지 않도록 주의
- CSS 클래스와 스타일은 변경하지 않음

### 3. 에러 핸들링
- 변수가 None 또는 빈 값일 경우 대비한 기본값 처리
- Jinja2 템플릿 오류 발생 시 빠르게 디버깅할 수 있도록 로그 추가

## 📈 성공 지표 (KPI)

### 1. 템플릿-로직 동기화
- **목표**: 100% 동기화 달성
- **현재**: 63.9% (13/36)
- **목표**: 100% (36/36)

### 2. HTML 렌더링 오류 감소
- **목표**: 0건
- **현재**: 변수 누락으로 인한 렌더링 오류 발생
- **목표**: 변수 누락으로 인한 오류 0건

### 3. 테스트 신뢰도 향상
- **목표**: 95%+
- **현재**: 변수 누락으로 인한 테스트 실패
- **목표**: 변수 관련 테스트 실패 0건

## 🔄 다음 단계

### Phase 2: 검증 시스템 구축 (이번 주)
- logic.py에 검증 레이어 적용
- 자동 검증 스크립트 개선
- 에러 핸들링 강화

### Phase 3: 템플릿 완전 동기화 (차주)
- 동적 공제 항목 표시 구현
- 조건부 렌더링 최적화
- 템플릿 구조 개선

### Phase 4: 자동화 시스템 구축 (다음 달)
- CI/CD 파이프라인 연동
- 실시간 모니터링 시스템 구축
- 자동 알림 시스템 구축

## 📞 담당자 및 연락처

- **프로젝트 리더**: [담당자 이름]
- **기술 담당**: [개발자 이름]
- **QA 담당**: [테스트 담당자 이름]
- **연락처**: [연락처 정보]

## 📅 일정 관리

| 작업 내용 | 담당자 | 시작일 | 종료일 | 상태 |
|-----------|--------|--------|--------|------|
| 핵심 변수 추가 | 개발자 | 2026-02-10 | 2026-02-10 | 진행중 |
| 합계 변수 추가 | 개발자 | 2026-02-10 | 2026-02-10 | 대기 |
| 옵션 변수 추가 | 개발자 | 2026-02-10 | 2026-02-10 | 대기 |
| 부가 변수 추가 | 개발자 | 2026-02-10 | 2026-02-10 | 대기 |
| 템플릿 검증 | QA | 2026-02-10 | 2026-02-10 | 대기 |
| 로직 연동 테스트 | QA | 2026-02-10 | 2026-02-10 | 대기 |
| 전체 시스템 검증 | QA | 2026-02-10 | 2026-02-10 | 대기 |

---

*이 문서는 HTML-로직 일관성 문제 해결을 위한 구체적인 실행 계획을 제공합니다.*