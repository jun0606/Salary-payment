# 회사 관리 시스템 개선 방안 설계

## 📋 개요

MCP 실행 결과를 통해 확인된 회사 관리 시스템의 근본적인 문제점을 해결하기 위한 종합적인 개선 방안을 설계합니다.

## 🔍 현재 문제점 요약

### 1. 데이터 흐름 차단
- **문제**: config.json 변경 사항이 메인 화면으로 전달되지 않음
- **증거**: tax_settings_qt.py에서 회사 정보 변경 후 메인 화면 콤보박스 자동 갱신되지 않음

### 2. UI 동기화 부재
- **문제**: 메인 화면 콤보박스는 초기화 시점에만 데이터 로드
- **증거**: update_company_selector()는 초기화 시에만 호출, 실시간 갱신되지 않음

### 3. 이벤트 연결 누락
- **문제**: 회사 정보 변경 시 다른 화면에 알릴 수단이 없음
- **증거**: 시그널-슬롯 기반 동기화 메커니즘이 구현되지 않음

### 4. 상태 불일치
- **문제**: config.json과 메인 화면 콤보박스가 서로 다른 상태 유지
- **증거**: 회사 추가/수정/삭제 후 메인 화면에서 변경 사항이 반영되지 않음

### 5. 추가 발견 문제점
- **회사 ID 중복**: new_company_id 생성 로직에서 기존 회사와 ID 충돌 가능성
- **에러 핸들링 부재**: 예외 발생 시 명확한 오류 메시지 제공되지 않음
- **트랜잭션 처리 부재**: config.json 저장 중 실패 시 롤백 메커니즘이 없음

## 🎯 개선 목표

1. **실시간 동기화**: 회사 정보 변경 시 모든 화면 즉시 갱신
2. **중앙 집중식 관리**: config.json 접근을 전담하는 중앙 클래스 구현
3. **이벤트 기반 아키텍처**: 시그널-슬롯 기반 동기화 체계 구축
4. **에러 처리 강화**: 예외 상황에 대한 명확한 사용자 피드백 제공
5. **데이터 무결성**: 트랜잭션 처리를 통한 데이터 일관성 보장

## 🏗️ 시스템 아키텍처 개선 설계

### 1. 중앙 집중식 회사 관리 시스템 설계

```
┌─────────────────────────────────────────────────────────────┐
│                    CompanyManager (신규)                     │
├─────────────────────────────────────────────────────────────┤
│  - config.json 접근 전담                                   │
│  - 회사 정보 CRUD 작업                                      │
│  - 변경 시그널 방출                                        │
│  - 데이터 무결성 검증                                      │
│  - 트랜잭션 처리                                           │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  tax_settings_  │  │   main_qt.py    │  │   기타 모듈     │
│     qt.py       │  │                 │  │                 │
│                 │  │                 │  │                 │
│ - 회사 관리 UI  │  │ - 회사 선택 UI  │  │ - 회사 정보    │
│ - 변경 시 시그널│  │ - 시그널 수신   │  │   접근 모듈    │
│   방출          │  │ - 실시간 갱신   │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 2. 이벤트 기반 동기화 설계

```
회사 정보 변경 시 흐름:

1. 사용자 입력 → tax_settings_qt.py
2. CompanyManager.update_company() 호출
3. config.json 저장 (트랜잭션)
4. CompanyManager.company_changed 시그널 방출
5. main_qt.py에서 시그널 수신
6. update_company_selector() 호출
7. UI 실시간 갱신
```

## 📝 구체적 구현 방안

### 1. CompanyManager 클래스 설계

```python
class CompanyManager(QObject):
    """중앙 집중식 회사 관리 시스템"""
    
    # 시그널 정의
    company_added = pyqtSignal(str)      # 회사 추가 시
    company_modified = pyqtSignal(str)   # 회사 수정 시  
    company_deleted = pyqtSignal(str)    # 회사 삭제 시
    company_changed = pyqtSignal()       # 회사 정보 변경 시 (전체)
    
    def __init__(self, config_path="config.json"):
        super().__init__()
        self.config_path = config_path
        self._companies = {}
        self._load_companies()
    
    def _load_companies(self):
        """config.json에서 회사 정보 로드"""
        # 기존 load_company_info() 로직 재사용
    
    def add_company(self, company_data):
        """회사 추가 (트랜잭션 처리)"""
        # 1. ID 중복 검사
        # 2. 데이터 유효성 검증
        # 3. 트랜잭션 시작
        # 4. config.json 저장
        # 5. 시그널 방출
        # 6. 트랜잭션 커밋/롤백
    
    def modify_company(self, company_id, company_data):
        """회사 수정 (트랜잭션 처리)"""
        # 1. 회사 존재 검사
        # 2. 데이터 유효성 검증
        # 3. 트랜잭션 시작
        # 4. config.json 저장
        # 5. 시그널 방출
        # 6. 트랜잭션 커밋/롤백
    
    def delete_company(self, company_id):
        """회사 삭제 (트랜잭션 처리)"""
        # 1. 회사 존재 검사
        # 2. 삭제 가능 여부 검사 (사용 중인 회사인지)
        # 3. 트랜잭션 시작
        # 4. config.json 저장
        # 5. 시그널 방출
        # 6. 트랜잭션 커밋/롤백
    
    def get_companies(self):
        """회사 목록 반환"""
        return self._companies.copy()
    
    def get_company(self, company_id):
        """특정 회사 정보 반환"""
        return self._companies.get(company_id)
```

### 2. tax_settings_qt.py 개선 방안

```python
class TaxSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 기존 초기화 코드
        
        # CompanyManager 인스턴스 생성
        self.company_manager = CompanyManager()
        
        # 시그널 연결
        self.company_manager.company_changed.connect(self.on_company_changed)
    
    def on_company_changed(self):
        """회사 정보 변경 시 처리"""
        # 세무사 설정 화면 내부 테이블 갱신
        self.load_company_info()
    
    def add_company(self):
        """회사 추가 로직 개선"""
        try:
            # 기존 입력값 검증
            
            # CompanyManager를 통한 회사 추가
            company_data = {
                'company_id': new_company_id,
                'company_name': company_name,
                'business_number': business_number,
                'representative': representative,
                'address': address,
                'phone': phone
            }
            
            self.company_manager.add_company(company_data)
            
            # 성공 메시지 표시
            QMessageBox.information(self, "성공", "회사가 성공적으로 추가되었습니다.")
            
        except Exception as e:
            # 에러 핸들링 강화
            QMessageBox.critical(self, "오류", f"회사 추가 중 오류가 발생했습니다: {str(e)}")
    
    def modify_company(self):
        """회사 수정 로직 개선"""
        # CompanyManager를 통한 회사 수정
        # 에러 핸들링 강화
    
    def delete_company(self):
        """회사 삭제 로직 개선"""
        # CompanyManager를 통한 회사 삭제
        # 에러 핸들링 강화
```

### 3. main_qt.py 개선 방안

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 기존 초기화 코드
        
        # CompanyManager 인스턴스 생성
        self.company_manager = CompanyManager()
        
        # 시그널 연결
        self.company_manager.company_changed.connect(self.on_company_changed)
    
    def on_company_changed(self):
        """회사 정보 변경 시 처리"""
        # 메인 화면 콤보박스 실시간 갱신
        self.update_company_selector()
        
        # 현재 선택된 회사가 삭제된 경우 기본값으로 설정
        current_company = self.company_selector.currentText()
        if current_company not in [company['company_name'] for company in self.company_manager.get_companies().values()]:
            self.company_selector.setCurrentIndex(0)
    
    def update_company_selector(self):
        """회사 선택 콤보박스 갱신 (개선)"""
        # CompanyManager에서 회사 목록 가져오기
        companies = self.company_manager.get_companies()
        
        # 콤보박스 내용 초기화
        self.company_selector.clear()
        
        # 회사 목록 추가
        for company_id, company_info in companies.items():
            self.company_selector.addItem(company_info['company_name'], company_id)
        
        # 기본값 설정
        if companies:
            self.company_selector.setCurrentIndex(0)
```

### 4. 에러 핸들링 강화 방안

```python
class CompanyManager(QObject):
    def __init__(self, config_path="config.json"):
        super().__init__()
        self.config_path = config_path
        self._companies = {}
        try:
            self._load_companies()
        except Exception as e:
            # 초기화 실패 시 기본값 설정
            self._companies = {}
            self._save_companies()  # 빈 파일 생성
    
    def _load_companies(self):
        """config.json 로드 (에러 핸들링 강화)"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._companies = data.get('companies', {})
            else:
                self._companies = {}
        except json.JSONDecodeError as e:
            # JSON 파싱 오류 시 기본값 설정
            self._companies = {}
            self._save_companies()
        except Exception as e:
            # 기타 오류 처리
            raise Exception(f"회사 정보 로드 중 오류 발생: {str(e)}")
    
    def _save_companies(self):
        """config.json 저장 (트랜잭션 처리)"""
        try:
            # 임시 파일에 저장 후 원본 파일로 이동 (원자성 보장)
            temp_path = self.config_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump({'companies': self._companies}, f, ensure_ascii=False, indent=2)
            
            # 원본 파일 백업
            if os.path.exists(self.config_path):
                backup_path = self.config_path + '.backup'
                shutil.copy2(self.config_path, backup_path)
            
            # 임시 파일을 원본 파일로 이동
            os.replace(temp_path, self.config_path)
            
        except Exception as e:
            # 저장 실패 시 롤백
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise Exception(f"회사 정보 저장 중 오류 발생: {str(e)}")
```

## 🔄 구현 단계

### Phase 1: 기본 구조 구현
1. **CompanyManager 클래스 생성**
   - 시그널 정의
   - 기본 CRUD 메서드 구현
   - 에러 핸들링 기본 구현

2. **tax_settings_qt.py 개선**
   - CompanyManager 인스턴스화
   - 시그널 연결
   - 기존 메서드를 CompanyManager로 리팩토링

3. **main_qt.py 개선**
   - CompanyManager 인스턴스화
   - 시그널 연결
   - 실시간 갱신 로직 구현

### Phase 2: 고급 기능 구현
1. **트랜잭션 처리 구현**
   - 원자성 보장
   - 롤백 메커니즘
   - 백업 시스템

2. **데이터 무결성 검증**
   - ID 중복 검사
   - 입력값 검증
   - 참조 무결성 검사

3. **에러 핸들링 강화**
   - 상세 오류 메시지
   - 사용자 친화적 에러 표시
   - 로그 기록

### Phase 3: 테스트 및 검증
1. **단위 테스트 작성**
   - CompanyManager 테스트
   - 시그널-슬롯 테스트
   - 에러 핸들링 테스트

2. **통합 테스트**
   - 전체 시스템 테스트
   - 실시간 동기화 테스트
   - 에러 상황 테스트

3. **사용자 테스트**
   - 실제 사용 시나리오 테스트
   - 성능 테스트
   - 사용성 테스트

## 📊 기대 효과

### 1. 사용자 경험 개선
- **실시간 반영**: 회사 정보 변경 즉시 모든 화면에 반영
- **에러 안내**: 명확한 오류 메시지와 해결 방법 제공
- **안정성**: 데이터 손실 위험 최소화

### 2. 개발 및 유지보수 개선
- **코드 일관성**: 중앙 집중식 관리로 코드 중복 최소화
- **디버깅 용이**: 이벤트 흐름을 통한 문제 추적 용이
- **확장성**: 새로운 기능 추가 시 구조적 변경 최소화

### 3. 시스템 안정성 향상
- **데이터 무결성**: 트랜잭션 처리를 통한 데이터 일관성 보장
- **오류 복구**: 자동 백업 및 롤백 메커니즘
- **성능 최적화**: 불필요한 파일 접근 최소화

## ⚠️ 구현 시 고려사항

### 1. 하위 호환성
- 기존 config.json 형식과의 호환성 유지
- 기존 코드와의 연동 최소화

### 2. 성능 고려
- 불필요한 시그널 방출 방지
- 대량 데이터 처리 최적화

### 3. 보안 고려
- 파일 접근 권한 검사
- 데이터 무결성 검증

## 📅 구현 일정

| 단계 | 작업 내용 | 예상 기간 |
|------|-----------|-----------|
| Phase 1 | 기본 구조 구현 | 2-3일 |
| Phase 2 | 고급 기능 구현 | 3-4일 |
| Phase 3 | 테스트 및 검증 | 2-3일 |
| **총계** | **전체 구현** | **7-10일** |

## 🎯 성공 기준

1. **실시간 동기화**: 회사 정보 변경 후 1초 이내에 모든 화면에 반영
2. **에러 처리**: 모든 예외 상황에 대해 사용자에게 명확한 메시지 제공
3. **데이터 무결성**: 트랜잭션 실패 시 원래 상태로 완전 복구
4. **사용자 만족도**: 기존 문제점에 대한 사용자 불만 0건

이 개선 방안을 통해 회사 관리 시스템의 근본적인 문제점을 완전히 해결하고, 보다 안정적이고 사용자 친화적인 시스템으로 개선할 수 있습니다.