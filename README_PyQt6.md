# 💰 급여명세서 생성기 (PyQt6 버전)

tkinter에서 PyQt6로 완전히 마이그레이션된 현대적인 급여명세서 생성기입니다.

## ✨ 주요 특징

- **현대적 UI**: PyQt6 기반의 세련된 사용자 인터페이스
- **실시간 계산**: 엑셀 데이터 기반 자동 급여 계산
- **법적 준수**: 근로기준법 제56조 준수 (5인 미만 사업장 연장근무 처리)
- **직원 관리**: 직원 정보 CRUD 및 검색 기능
- **라이선스 시스템**: HW 기반 보안 라이선스 검증
- **다양한 출력**: Excel/HTML 형식 지원
- **크로스 플랫폼**: Windows, macOS, Linux 지원

## 🚀 설치 및 실행

### 요구사항
- Python 3.9 이상 (권장)
- pip 패키지 관리자
- Windows 10/11 (기본 지원)

### 설치
```bash
# 의존성 설치
pip install -r requirements.txt

# 또는 개별 설치
pip install PyQt6 pandas openpyxl jinja2 cryptography holidays numpy
# Windows 전용 추가 패키지
pip install wmi
```

### 실행
```bash
# PyQt6 버전 실행 (권장)
python main_qt.py

# 기존 tkinter 버전 (호환성)
python main_app.py
```

## 📦 배포 (Distribution)

### 개요
본 프로젝트는 PyInstaller를 사용하여 독립 실행형 exe 파일로 배포할 수 있습니다.

### 배포 환경 준비
```bash
# PyInstaller 설치
pip install pyinstaller

# 또는 GUI 도구
pip install auto-py-to-exe
```

### exe 파일 생성
```bash
# 자동 빌드 스크립트 사용 (권장)
# 고객용 버전 빌드
python build_exe.py client

# 세무사용 버전 빌드
python build_exe.py tax

# 수동 빌드 (고급 사용자용)
pyinstaller --onefile --windowed --name=급여명세서관리 \
  --add-data "tutorial_data.xlsx;." \
  --add-data "payslip_template.html;." \
  --add-data "license_system;license_system" \
  --add-data "config.json;." \
  --add-data "employees.json;." \
  main_qt.py
```

### 버전별 배포 설정

#### 세무사용 버전 (Tax Accountant Version)
```python
# license_verifier.py에서 라이선스 체크 우회
def check_license():
    return 'LICENSED'  # 항상 라이선스됨으로 설정
```

#### 고객용 버전 (Client Version)
```python
# license_verifier.py에서 정상 라이선스 체크 유지
def check_license():
    # 기존 라이선스 검증 로직
    return license_verifier.verify_license()
```

### 배포 파일 구조
```
배포판/
├── 급여명세서관리.exe    # 메인 실행 파일
├── tutorial_data.xlsx    # 튜토리얼 데이터
├── payslip_template.html # 급여명세서 템플릿
├── config.json          # 기본 설정
├── employees.json       # 샘플 직원 데이터
└── license_system/      # 라이선스 시스템
```

### 배포 테스트
```bash
# 생성된 exe 파일 테스트
./dist/급여명세서관리.exe
```

### 배포 팁
- **파일 크기**: PyQt6 포함으로 약 50-100MB 예상
- **호환성**: Windows 10/11 기본 지원
- **보안**: 라이선스 시스템으로 무단 배포 방지
- **업데이트**: exe 파일 교체로 간편 업데이트 가능

## 📁 프로젝트 구조

```
급여명세서 생성기/
├── main_qt.py                 # PyQt6 메인 애플리케이션
├── main_app.py                # tkinter 메인 애플리케이션 (호환성)
├── master_data_pane_qt.py     # PyQt6 직원 관리 패널
├── monthly_payroll_pane_qt.py # PyQt6 급여 계산 패널
├── tax_settings_qt.py        # PyQt6 세무사 설정
├── activation_dialog_qt.py    # PyQt6 라이선스 활성화
├── logic.py                   # 비즈니스 로직
├── date_utils.py              # 날짜 유틸리티
├── test_qt_migration.py       # 마이그레이션 테스트
├── requirements.txt           # 의존성 목록
├── PYQT6_MIGRATION_GUIDE.md   # 마이그레이션 가이드
├── payslip_template.html      # 급여명세서 HTML 템플릿
└── license_system/            # 라이선스 시스템
    ├── license_verifier.py
    ├── license_generator.py
    ├── hardware_id.py
    ├── private_key.pem
    └── public_key.pem
```

## 🎯 주요 기능

### 직원 관리
- 직원 정보 추가/수정/삭제
- 입사일 및 지급일 관리
- 날짜 자동 조정 (휴일 고려)
- 실시간 데이터 검증

### 급여 계산
- 엑셀 파일 데이터 로드
- 자동 급여 계산 (기본급, 수당, 공제액)
- 실시간 값 수정
- 미리보기 및 검증

### 파일 생성
- Excel 형식 출력
- HTML 웹 페이지 생성
- 통합/개별 파일 옵션
- 회사 정보 포함

### 라이선스 관리
- HW 기반 라이선스 검증
- 실시간 상태 표시
- 코드 생성 및 활성화
- 보안 암호화

## ⚖️ 5인 미만 사업장 연장근무 처리

본 시스템은 근로기준법 제56조를 준수하여 5인 미만 사업장의 연장근무를 올바르게 처리합니다.

### 법적 근거

**근로기준법 제56조 (연장·야간 및 휴일근로)**
> 상시근로자 5명 이상의 사업장은 연장근로에 대하여 통상임금의 100분의 50을 가산하여 지급하여야 한다.
>
> ※ 5인 미만 사업장은 연장근로 가산금 지급 의무가 없음

### 기능 설명

#### 사업장 규모별 계산 방식
- **5인 이상 사업장**: 연장수당 = 연장시간 × 시급 × 1.5배 (통상임금의 50% 가산)
- **5인 미만 사업장**: 연장수당 = 0원 (연장시간을 기본급에 포함)

#### 데이터 처리 흐름
1. **직원 데이터 확인**: 각 직원의 사업장 규모 정보 확인
2. **자동 분류**: 5인 이상/미만에 따른 계산 로직 적용
3. **법적 준수**: 연장근무 가산금 지급 의무 배제

### 설정 방법

#### 1. 세무사 설정에서 사업장 규모 지정
```
메뉴 → 세무사 설정 → 사업장 규모 드롭다운
├── 5인 이상 사업장 (기본)
└── 5인 미만 사업장
```

#### 2. 자동 적용
- 설정 저장 시 모든 직원 데이터에 사업장 규모 자동 적용
- 개별 직원별 수동 설정도 지원

#### 3. 계산 결과
```
5인 미만 사업장 예시:
기본급 = (근무시간 + 연장시간) × 시급
연장수당 = 0원

5인 이상 사업장 예시:
기본급 = 근무시간 × 시급
연장수당 = 연장시간 × 시급 × 1.5배
```

### 검증 사례

#### 오수민 직원 (5인 미만 사업장)
```
입력: 근무시간 61시간, 연장시간 1시간
계산: 기본급 = 62시간 × 시급, 연장수당 = 0원
결과: 법적 준수 (연장 가산금 미지급)
```

### 안전장치

#### 데이터 무결성
- 사업장 규모 정보 누락 시 "5인 이상"으로 기본 적용
- 변경 이력 추적 및 감사 로그 기록
- 실시간 법적 준수 검증

#### 사용자 안내
- 설정 변경 시 법적 영향 명확히 안내
- 계산 결과에 법적 근거 표시
- 세무사 전문가 상담 권장

### 확장성

#### 미래 지원 기능
- **다중 사업장**: 회사별 사업장 규모 관리
- **업종별 규정**: 산업별 상이한 근로기준 적용
- **지역별 차이**: 지방세율 자동 적용
- **연도별 업데이트**: 세법 변경 자동 반영

#### API 지원
- 직원별 사업장 규모 조회
- 계산 결과 법적 준수 검증
- 보고서 생성 및 감사 자료 제공

## 🔧 기술 스택

- **GUI**: PyQt6 (Qt6 기반)
- **데이터 처리**: pandas, openpyxl
- **템플릿**: Jinja2
- **암호화**: cryptography
- **시스템**: WMI (Windows)
- **테스트**: subprocess 기반 자동화

## 🧪 테스트

```bash
# 마이그레이션 테스트 실행
python test_qt_migration.py
```

## 📊 마이그레이션 정보

본 프로젝트는 tkinter에서 PyQt6로 완전히 마이그레이션되었습니다.

### 마이그레이션 장점
- ✅ **현대적 UI**: 네이티브 OS 스타일
- ✅ **더 나은 성능**: 하드웨어 가속 지원
- ✅ **풍부한 기능**: 애니메이션, 테마 지원
- ✅ **장기 유지보수**: 활발한 Qt 커뮤니티

### 이전 버전 호환성
- tkinter 버전: `main_app.py` (기존 사용자용)
- PyQt6 버전: `main_qt.py` (신규 사용자용)

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 참고하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 생성해주세요.

---

**개발자**: PyQt6 마이그레이션 팀
**버전**: 2.1.0 (PyQt6 - 5인 미만 사업장 지원)
**최종 업데이트**: 2026-01-07
