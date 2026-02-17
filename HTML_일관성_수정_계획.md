# HTML-로직 일관성 수정 계획 및 진행

**작성일**: 2026년 2월 10일  
**목표**: HTML 결과물과 로직의 일관성 확보

---

## 수정 단계

### Phase 1: 즉시 수정 (오늘 완료)

#### 1.1 payslip_template.html 수정

**수정 1: 야간수당 계산식 표시 추가**
- 파일: `payslip_template.html`
- 위치: `<div class="calculation-notes">` 섹션
- 변경: `calculation_note_night` 및 `show_night_note` 추가

**수정 2: rowspan 수정**
- 변경: `rowspan="5"` → `rowspan="6"`
- 이유: 6개 공제 항목 모두에 비고 표시

#### 1.2 테스트 실행 및 검증
- 수정 후 테스트 실행
- HTML 출력 확인

---

### Phase 2: 검증 레이어 도입 (내일)

#### 2.1 validation.py 생성
- 데이터 스키마 정의
- 검증 로직 구현

#### 2.2 logic.py 통합
- `_prepare_payslip_data()`에 검증 추가
- 오류 메시지 개선

---

### Phase 3: 테스트 개선 (차주)

#### 3.1 test_html_consistency.py 수정
- 실제 데이터 기반 테스트 강화
- 실패 케이스 개선

---

## 수정 진행 상황

- [ ] 1.1 payslip_template.html 수정
  - [ ] 야간수당 계산식 추가
  - [ ] rowspan 수정
- [ ] 1.2 테스트 실행
- [ ] 2.1 validation.py 생성
- [ ] 2.2 logic.py 통합
- [ ] 3.1 테스트 개선

