# 실행파일 배포 개선 계획서

## 📋 개요

본 문서는 급여명세서 생성기 프로젝트의 실행파일 배포 개선을 위한 종합적인 계획을 정리한 것입니다.

## 🎯 목표

- 최신 업데이트에 맞춘 실행파일 생성 방법 개선
- PyQt6 최적화 및 파일 크기 감소
- 에디션별 배포 옵션 제공
- 사용자 친화적인 배포 환경 구축

## 🔍 현재 상황 분석

### 최신 업데이트 현황

#### 1. **핵심 변경사항 파악**
- **HTML 일관성 문제 완전 해결**: 주차별 주휴수당 계산 로직 개선
- **PyQt6 마이그레이션 완료**: tkinter에서 완전 전환
- **라이선스 시스템 강화**: HW 기반 보안 검증
- **5인 미만 사업장 지원**: 근로기준법 제56조 준수
- **연차 관리 시스템 추가**: annual_leave_manager.py 등

#### 2. **실행파일 생성 방법의 수정 필요성**

**현재 build_exe.py의 한계점:**
- PyQt6 플랫폼 플러그인 자동 포함 로직 미비
- 연차 관리 모듈(annual_leave_manager.py) 미반영
- 최신 HTML 템플릿 변수 지원 미비
- PyQt6 최적화 옵션 미적용

## 🚀 개선 방안

### 1. **의존성 모듈 추가**

```python
# 추가 필요 모듈
excluded_modules.extend([
    'annual_leave_manager',    # 연차 관리 모듈
    'annual_leave_dialog_qt',  # 연차 GUI 모듈
    'sync_checker',           # 동기화 체커
    'validation',             # 검증 모듈
])
```

### 2. **데이터 파일 확장**

```python
# 추가 데이터 파일
data_files.extend([
    ('annual_leave_manager.py', '.'),
    ('annual_leave_dialog_qt.py', '.'),
    ('sync_checker.py', '.'),
    ('validation.py', '.'),
])
```

### 3. **PyQt6 최적화 옵션**

```python
# 추가 PyInstaller 옵션
options.extend([
    '--hidden-import=PyQt6.QtWebEngineWidgets',  # HTML 렌더링
    '--hidden-import=PyQt6.QtPrintSupport',      # 인쇄 지원
    '--collect-all=PyQt6',                       # PyQt6 전체 수집
])
```

### 4. **실행파일 크기 최적화**

**현재 문제점:**
- PyQt6 전체 포함으로 인한 파일 크기 증가 (50-100MB)
- 불필요한 Qt 모듈 포함
- 연차 관리 등 선택적 기능 무조건 포함

**개선 방안:**
```python
# 선택적 모듈 포함
excluded_modules.extend([
    'PyQt6.QtWebEngineCore',     # 웹엔진 코어 (필요 시 제외)
    'PyQt6.QtMultimedia',        # 멀티미디어 (필요 시 제외)
    'PyQt6.QtOpenGL',           # OpenGL (필요 시 제외)
])
```

### 5. **배포 환경 개선**

**새로운 배포 옵션 추가:**
```python
# 버전별 배포 옵션
parser.add_argument('--edition', choices=['standard', 'lite'],
                   default='standard', 
                   help='배포 에디션 (standard: 전체 기능, lite: 기본 기능)')
```

**Lite 버전 구성:**
- 기본 급여 계산 기능만 포함
- 연차 관리 모듈 제외
- 최소 PyQt6 모듈만 포함
- 파일 크기 30-50% 감소

## 📦 개선된 배포 패키지 구조

### Standard 버전
```
배포판/
├── 급여명세서관리.exe
├── tutorial_data.xlsx
├── payslip_template.html
├── config.json
├── employees.json
├── license_system/
├── annual_leave_manager.py
├── annual_leave_dialog_qt.py
└── README.txt
```

### Lite 버전
```
배포판/
├── 급여명세서관리_lite.exe
├── tutorial_data.xlsx
├── payslip_template.html
├── config.json
├── employees.json
├── license_system/
└── README_lite.txt
```

## 🛠️ 구현 단계

### 1단계: **PyQt6 최적화**
- 불필요한 Qt 모듈 제외
- 플랫폼 플러그인 자동 포함
- 파일 크기 최적화

### 2단계: **모듈 포함 옵션**
- 연차 관리 모듈 선택적 포함
- 에디션별 모듈 구성
- 의존성 최소화

### 3단계: **빌드 스크립트 개선**
- 에디션별 빌드 옵션 추가
- 자동 최적화 로직 구현
- 사용자 친화적 명령어 제공

### 4단계: **배포 패키지 구조 개선**
- 에디션별 패키지 구조 설계
- 문서 자동 생성
- 설치 가이드 개선

## 📊 예상 효과

### 파일 크기 감소
- **Standard 버전**: 50-70MB (기존 대비 30% 감소)
- **Lite 버전**: 20-30MB (기존 대비 60% 감소)

### 배포 효율성
- **에디션 선택**: 사용자 요구에 맞는 최적 배포
- **빠른 설치**: 파일 크기 감소로 인한 빠른 설치
- **유지보수**: 모듈별 관리로 인한 효율적 유지보수

### 사용자 만족도
- **맞춤형 배포**: 필요 기능만 포함된 최적 배포
- **빠른 실행**: 파일 크기 감소로 인한 빠른 실행
- **안정성**: 최적화된 모듈 구성으로 인한 안정성 향상

## 🎯 실행 명령어

### 에디션 지정 빌드
```bash
# Standard 버전 빌드
python build_exe.py --version client --edition standard

# Lite 버전 빌드
python build_exe.py --version client --edition lite
```

### 빠른 빌드 옵션
```bash
# 기본 설정으로 빠르게 빌드
python build_exe.py --quick
```

## 📋 검증 항목

### 1. **기능 검증**
- [ ] Standard 버전: 모든 기능 정상 작동
- [ ] Lite 버전: 기본 기능 정상 작동
- [ ] PyQt6 GUI 정상 표시
- [ ] 라이선스 검증 정상 작동

### 2. **성능 검증**
- [ ] 파일 크기 목표 달성
- [ ] 실행 속도 향상
- [ ] 메모리 사용량 최적화

### 3. **호환성 검증**
- [ ] Windows 10/11 호환성
- [ ] 다양한 환경에서 실행 테스트
- [ ] 업데이트 후 호환성 검증

## 🚀 향후 계획

### 단기 목표 (1-2개월)
- [ ] 개선된 빌드 스크립트 구현
- [ ] 에디션별 배포 패키지 테스트
- [ ] 사용자 피드백 수집 및 개선

### 중기 목표 (3-6개월)
- [ ] 자동 최적화 로직 개선
- [ ] 추가 에디션 옵션 검토
- [ ] CI/CD 파이프라인 연동

### 장기 목표 (6개월 이상)
- [ ] 클라우드 배포 옵션 검토
- [ ] 자동 업데이트 시스템 구축
- [ ] 글로벌 배포 환경 구축

## 📝 결론

본 개선 계획을 통해 급여명세서 생성기의 실행파일 배포 환경을 대폭 개선할 수 있습니다. 특히 PyQt6 최적화와 에디션별 배포 옵션을 통해 사용자의 다양한 요구를 만족시킬 수 있을 것입니다.

실행파일 크기 감소와 함께 제공되는 맞춤형 배포 옵션은 사용자 만족도를 크게 향상시킬 것으로 기대됩니다.