# 스마트 마이그레이션 시스템 설계서

## 📋 개요

본 문서는 급여명세서 생성기 프로젝트에서 실행 시 JSON 파일을 자동 생성하고, 버전이 업데이트될 때마다 자동으로 마이그레이션하는 고급 시스템을 설계한 것입니다.

## 🎯 목표

- 프로그램 실행 시 JSON 파일 자동 생성
- 버전 업데이트 시 자동 마이그레이션
- 데이터 무결성 보장
- 사용자 개입 최소화
- 안전한 롤백 시스템 구축

## 🔧 구현 방법

### 1. **버전 기반 마이그레이션 시스템**

#### A. 마이그레이션 매니저 클래스
```python
class MigrationManager:
    """JSON 파일 자동 마이그레이션 매니저"""
    
    def __init__(self):
        self.current_version = "2.1.0"
        self.migration_scripts = {
            "2.0.0": self.migrate_v2_0_0,
            "2.1.0": self.migrate_v2_1_0,
            "2.2.0": self.migrate_v2_2_0
        }
    
    def ensure_latest_version(self):
        """최신 버전으로 마이그레이션"""
        
        # 1. 현재 버전 확인
        current_app_version = self.get_current_app_version()
        
        # 2. 파일 버전 확인
        file_version = self.get_file_version()
        
        # 3. 마이그레이션 필요 여부 확인
        if file_version < current_app_version:
            print(f"🔄 마이그레이션 시작: {file_version} → {current_app_version}")
            
            # 4. 순차적 마이그레이션 실행
            self.run_migration_chain(file_version, current_app_version)
            
            print("✅ 마이그레이션 완료")
        else:
            print("✅ 최신 버전 사용 중")
    
    def run_migration_chain(self, from_version, to_version):
        """순차적 마이그레이션 실행"""
        
        # 버전 목록 생성
        version_chain = self.get_version_chain(from_version, to_version)
        
        # 순차적 마이그레이션
        for version in version_chain:
            if version in self.migration_scripts:
                print(f"📦 {version} 마이그레이션 실행")
                self.migration_scripts[version]()
    
    def get_version_chain(self, from_version, to_version):
        """버전 체인 생성"""
        # 단순화를 위해 직접 리스트 반환
        versions = ["2.0.0", "2.1.0", "2.2.0"]
        start_idx = versions.index(from_version) + 1
        end_idx = versions.index(to_version) + 1
        return versions[start_idx:end_idx]
```

#### B. 구체적인 마이그레이션 스크립트

**v2.1.0 마이그레이션 (현재 버전)**
```python
def migrate_v2_1_0(self):
    """v2.1.0 마이그레이션: 연차 관리 기능 추가"""
    
    # 1. employees.json 마이그레이션
    employees_file = Path('employees.json')
    if employees_file.exists():
        employees_data = json.loads(employees_file.read_text(encoding='utf-8'))
        
        # 모든 직원에 연차 정보 추가
        for company_id, company_data in employees_data.items():
            if isinstance(company_data, dict) and 'employees' in company_data:
                for emp_id, emp_data in company_data['employees'].items():
                    if 'annual_leave' not in emp_data:
                        emp_data['annual_leave'] = {
                            'total_days': 0,
                            'used_days': 0,
                            'remaining_days': 0,
                            'last_updated': datetime.now().strftime('%Y-%m-%d')
                        }
        
        # 버전 정보 추가
        employees_data['version'] = "2.1.0"
        
        # 파일 저장
        with open(employees_file, 'w', encoding='utf-8') as f:
            json.dump(employees_data, f, ensure_ascii=False, indent=2)
    
    # 2. config.json 마이그레이션
    config_file = Path('config.json')
    if config_file.exists():
        config_data = json.loads(config_file.read_text(encoding='utf-8'))
        
        # 새로운 설정 항목 추가
        if 'annual_leave_enabled' not in config_data:
            config_data['annual_leave_enabled'] = True
        
        if 'sync_enabled' not in config_data:
            config_data['sync_enabled'] = False
        
        # 버전 정보 추가
        config_data['version'] = "2.1.0"
        
        # 파일 저장
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
```

**v2.2.0 마이그레이션 (예정)**
```python
def migrate_v2_2_0(self):
    """v2.2.0 마이그레이션: 새로운 세금 계산 방식"""
    
    config_file = Path('config.json')
    if config_file.exists():
        config_data = json.loads(config_file.read_text(encoding='utf-8'))
        
        # 새로운 세금 설정 추가
        if 'tax_calculation_method' not in config_data:
            config_data['tax_calculation_method'] = 'new'
        
        if 'deduction_options' not in config_data:
            config_data['deduction_options'] = {
                'national_pension': True,
                'health_insurance': True,
                'employment_insurance': True,
                'long_term_care': True,
                'income_tax': True,
                'local_income_tax': True
            }
        
        config_data['version'] = "2.2.0"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
```

### 2. **자동 생성 및 마이그레이션 통합 시스템**

#### A. 메인 초기화 함수
```python
def initialize_application():
    """애플리케이션 초기화 (자동 생성 + 마이그레이션)"""
    
    print("🚀 애플리케이션 초기화 시작...")
    
    # 1. 마이그레이션 매니저 생성
    migration_manager = MigrationManager()
    
    # 2. 필수 파일 존재 확인 및 생성
    ensure_required_files_exist()
    
    # 3. 자동 마이그레이션 실행
    migration_manager.ensure_latest_version()
    
    # 4. 파일 검증
    validate_and_repair_files()
    
    # 5. 사용자 안내
    show_startup_guide()
    
    print("✅ 애플리케이션 초기화 완료")

def ensure_required_files_exist():
    """필수 파일 존재 확인 및 생성"""
    
    # 기본 구조 정의
    base_employees = {
        "default_company": {
            "name": "",
            "employees": {}
        },
        "version": "2.0.0"  # 기본 버전
    }
    
    base_config = {
        "company_name": "",
        "payment_date": "25",
        "business_size": "5인 이상 사업장",
        "tax_year": 2025,
        "version": "2.0.0"  # 기본 버전
    }
    
    # 파일 생성
    employees_file = Path('employees.json')
    if not employees_file.exists():
        with open(employees_file, 'w', encoding='utf-8') as f:
            json.dump(base_employees, f, ensure_ascii=False, indent=2)
        print("✅ employees.json 기본 생성")
    
    config_file = Path('config.json')
    if not config_file.exists():
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(base_config, f, ensure_ascii=False, indent=2)
        print("✅ config.json 기본 생성")
```

### 3. **마이그레이션 히스토리 관리**

#### A. 마이그레이션 로그 시스템
```python
class MigrationLogger:
    """마이그레이션 로그 관리"""
    
    def __init__(self):
        self.log_file = Path('migration.log')
    
    def log_migration(self, from_version, to_version, success=True):
        """마이그레이션 로그 기록"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "SUCCESS" if success else "FAILED"
        
        log_entry = f"[{timestamp}] MIGRATION: {from_version} → {to_version} [{status}]\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def get_migration_history(self):
        """마이그레이션 히스토리 조회"""
        if self.log_file.exists():
            return self.log_file.read_text(encoding='utf-8').split('\n')
        return []
```

### 4. **실패 시 롤백 시스템**

#### A. 백업 및 롤백 기능
```python
class BackupManager:
    """파일 백업 및 롤백 관리"""
    
    def create_backup(self, file_path):
        """파일 백업 생성"""
        backup_dir = Path('backups')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = backup_dir / f"{file_path.name}.{timestamp}.bak"
        
        shutil.copy2(file_path, backup_file)
        return backup_file
    
    def rollback(self, file_path):
        """파일 롤백"""
        backup_dir = Path('backups')
        if not backup_dir.exists():
            return False
        
        # 가장 최근 백업 파일 찾기
        backup_files = list(backup_dir.glob(f"{file_path.name}.*.bak"))
        if not backup_files:
            return False
        
        latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
        
        # 롤백 실행
        shutil.copy2(latest_backup, file_path)
        print(f"🔄 {file_path.name} 롤백 완료: {latest_backup.name}")
        return True
```

### 5. **실행 시 자동 초기화 시스템**

#### A. 메인 실행 파일 통합
```python
def main():
    """메인 실행 함수"""
    
    print("🚀 애플리케이션 시작...")
    
    # 1. 애플리케이션 초기화 (자동 생성 + 마이그레이션)
    initialize_application()
    
    # 2. 기존 메인 로직 실행
    app = QApplication(sys.argv)
    # ... 기존 로직
```

#### B. 오류 처리 및 복구
```python
def safe_initialize_application():
    """안전한 애플리케이션 초기화"""
    
    try:
        initialize_application()
        return True
    except Exception as e:
        print(f"⚠️ 초기화 실패: {e}")
        print("🔧 안전 모드로 전환...")
        
        # 안전 모드 초기화
        safe_mode_initialize()
        return False

def safe_mode_initialize():
    """안전 모드 초기화"""
    
    # 최소 구조로 파일 생성
    ensure_required_files_exist()
    
    # 사용자에게 문제 알림
    show_safe_mode_guide()
```

## 🎯 장점 분석

### ✅ **자동화**
- **🚀 완전 자동**: 사용자 개입 없이 자동으로 생성 및 마이그레이션
- **⚡ 실시간 적용**: 버전 업데이트 시 즉시 적용
- **🛡️ 안전성**: 백업 및 롤백 시스템으로 안전 보장

### ✅ **유지보수성**
- **🔄 버전 관리**: 명확한 버전 기반 마이그레이션
- **📊 히스토리 추적**: 모든 마이그레이션 기록 보관
- **🔧 확장성**: 새로운 버전 추가가 용이

### ✅ **안정성**
- **🔒 데이터 보호**: 마이그레이션 전 백업 자동 생성
- **⚡ 실패 복구**: 마이그레이션 실패 시 자동 롤백
- **🛡️ 검증 시스템**: 마이그레이션 후 데이터 검증

## 📋 구현 단계

### 1단계: **마이그레이션 시스템 구축**
```python
# migration_manager.py 파일 생성
class MigrationManager:
    # 위에서 정의한 클래스 추가
    pass
```

### 2단계: **메인 파일에 통합**
```python
# main_qt.py 시작 부분
from migration_manager import MigrationManager

def main():
    # 마이그레이션 시스템 초기화
    initialize_application()
    
    # 기존 메인 로직 실행
    app = QApplication(sys.argv)
    # ... 기존 로직
```

### 3단계: **테스트 및 검증**
```bash
# 마이그레이션 테스트
python test_migration.py
```

### 4단계: **사용자 피드백 수집**
- 실제 사용 환경에서 테스트
- 문제 발생 시 빠른 수정
- 사용자 만족도 조사

## 🔍 최종 아키텍처

```
시스템 구조:
main_qt.py
├── initialize_application()           # 메인 초기화
├── ensure_required_files_exist()      # 파일 생성
├── MigrationManager                   # 마이그레이션 관리
├── MigrationLogger                    # 로그 관리
└── BackupManager                      # 백업 관리

데이터 흐름:
실행 → 파일 확인 → 생성/마이그레이션 → 검증 → 사용
```

## 📊 마이그레이션 예시

### v2.0.0 → v2.1.0 마이그레이션
```json
// 마이그레이션 전 (v2.0.0)
{
  "default_company": {
    "name": "",
    "employees": {
      "EMP001": {
        "name": "홍길동",
        "department": "인사부"
      }
    }
  },
  "version": "2.0.0"
}

// 마이그레이션 후 (v2.1.0)
{
  "default_company": {
    "name": "",
    "employees": {
      "EMP001": {
        "name": "홍길동",
        "department": "인사부",
        "annual_leave": {
          "total_days": 0,
          "used_days": 0,
          "remaining_days": 0,
          "last_updated": "2026-02-14"
        }
      }
    }
  },
  "version": "2.1.0"
}
```

## 🛡️ 안전성 보장

### 1. **다중 백업 시스템**
- 마이그레이션 전 자동 백업
- 시간 기반 백업 파일 관리
- 백업 파일 무결성 검증

### 2. **실패 감지 및 복구**
- 마이그레이션 중 오류 감지
- 자동 롤백 실행
- 사용자에게 상세 알림

### 3. **데이터 검증**
- 마이그레이션 후 구조 검증
- 필수 필드 존재 확인
- 데이터 타입 검증

## 🎉 결론

스마트 마이그레이션 시스템은 최고의 해결책입니다:

1. **🚀 완전 자동화**: 설치 후 즉시 최신 상태로 자동 설정
2. **🔒 데이터 안전**: 백업 및 롤백 시스템으로 완벽한 보호
3. **📊 버전 관리**: 명확한 버전 기반 마이그레이션으로 유지보수 용이
4. **⚡ 실시간 적용**: 버전 업데이트 시 즉시 최신 기능 적용
5. **🛡️ 안정성**: 실패 시 자동 복구로 시스템 안정성 확보

이 시스템을 구현하면 **미래의 모든 업데이트**에 대해 자동으로 대응할 수 있는 **완벽한 배포 시스템**을 갖추게 됩니다.