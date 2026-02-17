# 개인정보 보호 보안 개선 계획서

## 📋 개요

본 문서는 급여명세서 생성기 프로젝트의 개인정보 보호를 위한 실행파일 배포 보안 개선 방안을 정리한 것입니다.

## 🎯 목표

- 개발용 테스트 데이터 절대 포함 방지
- 자동 보안 검증 시스템 구축
- 모드별 배포 전략을 통한 데이터 보호
- 사용자 신뢰도 향상

## 🚨 문제점 파악

### 현재 위험 상황

**❌ 현재 위험 요소:**
- 개발용 JSON 파일(employees.json, config.json 등)에 실제 테스트 데이터 포함
- 배포 시 고객에게 개발자의 테스트 직원 정보 노출 위험
- 개인정보 보호법 위반 가능성
- 고객 신뢰도 하락

**위험 데이터 예시:**
```json
{
  "190335406": {
    "name": "홍유민",           // ❌ 실제 테스트 데이터
    "department": "운영팀",      // ❌ 실제 테스트 데이터
    "position": "사원",         // ❌ 실제 테스트 데이터
    "hire_date": "2024-03-01",  // ❌ 실제 테스트 데이터
    "hourly_rate": 10120        // ❌ 실제 테스트 데이터
  }
}
```

## 🛡️ 보안 개선 전략

### 1. **배포 전 데이터 정리 자동화**

#### A. 빌드 스크립트 개선
```python
def create_secure_distribution_package(dist_dir, version_type):
    """보안 강화된 배포 패키지 생성"""
    print("=== 개인정보 보호를 위한 데이터 정리 ===")
    
    # 1. 개발용 JSON 파일 백업
    dev_files = ['employees.json', 'config.json']
    for file in dev_files:
        src = dist_dir.parent / file
        if src.exists():
            backup_path = dist_dir.parent / f"{file}.dev_backup"
            shutil.copy2(src, backup_path)
            print(f"개발용 파일 백업: {backup_path}")
    
    # 2. 안전한 샘플 데이터 생성
    create_sample_data_files(dist_dir)
    
    # 3. 배포 패키지 생성
    create_distribution_package(dist_dir, version_type)
```

#### B. 샘플 데이터 생성 함수
```python
def create_sample_data_files(dist_dir):
    """안전한 샘플 데이터 파일 생성"""
    
    # employees.json 샘플
    sample_employees = {
        "company_001": {
            "name": "테스트회사",
            "employees": {
                "EMP001": {
                    "name": "홍길동",
                    "department": "인사부",
                    "position": "대리",
                    "hire_date": "2024-01-01",
                    "hourly_rate": 15000,
                    "allowances": {
                        "recurring": [
                            {"name": "직급수당", "amount": 100000, "taxable": true},
                            {"name": "식대", "amount": 150000, "taxable": true}
                        ],
                        "one_time": []
                    }
                }
            }
        }
    }
    
    # config.json 샘플
    sample_config = {
        "company_name": "테스트회사",
        "payment_date": "25",
        "business_size": "5인 이상 사업장",
        "tax_year": 2025,
        "version": "2.1.0"
    }
    
    # 파일 저장
    with open(dist_dir / 'employees.json', 'w', encoding='utf-8') as f:
        json.dump(sample_employees, f, ensure_ascii=False, indent=2)
    
    with open(dist_dir / 'config.json', 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    
    print("✅ 안전한 샘플 데이터 생성 완료")
```

### 2. **배포 모드 구분**

#### A. 빌드 옵션 추가
```python
parser.add_argument('--distribution-mode', 
                   choices=['dev', 'test', 'production'],
                   default='production',
                   help='배포 모드 (dev: 개발용, test: 테스트용, production: 양산용)')
```

#### B. 모드별 데이터 처리
```python
def handle_distribution_mode(mode):
    """배포 모드에 따른 데이터 처리"""
    if mode == 'production':
        # 양산용: 완전히 비어있는 상태로 배포
        create_empty_data_files()
        print("🔒 양산용 모드: 빈 데이터 파일 생성")
        
    elif mode == 'test':
        # 테스트용: 샘플 데이터 포함
        create_sample_data_files()
        print("🧪 테스트 모드: 샘플 데이터 포함")
        
    else:  # dev
        # 개발용: 원본 데이터 유지
        print("💻 개발 모드: 원본 데이터 유지")
```

### 3. **데이터 암호화 옵션**

#### A. 민감 데이터 암호화
```python
def encrypt_sensitive_data():
    """민감 데이터 암호화"""
    sensitive_files = ['employees.json', 'config.json']
    
    for file in sensitive_files:
        file_path = Path(file)
        if file_path.exists():
            # AES-256 암호화
            encrypted_data = encrypt_file_aes(file_path.read_bytes())
            file_path.write_bytes(encrypted_data)
            print(f"🔒 {file} 암호화 완료")
```

#### B. 실행 시 복호화
```python
def decrypt_data_at_runtime():
    """실행 시 데이터 복호화"""
    try:
        # 암호화된 파일 복호화
        decrypted_data = decrypt_file_aes('employees.json.enc')
        with open('employees.json', 'wb') as f:
            f.write(decrypted_data)
        return True
    except:
        # 복호화 실패 시 빈 데이터 생성
        create_empty_data_files()
        return False
```

### 4. **배포 검증 시스템**

#### A. 개인정보 검증
```python
def validate_distribution_package(dist_dir):
    """배포 패키지 개인정보 검증"""
    print("=== 개인정보 검증 시작 ===")
    
    # 위험 키워드 검색
    risky_keywords = ['홍유민', '홍길동', '010-', '123-4567', 'test@', 'dev@']
    
    for file_path in dist_dir.glob('*.json'):
        content = file_path.read_text(encoding='utf-8')
        for keyword in risky_keywords:
            if keyword in content:
                print(f"⚠️ 위험 키워드 발견: {file_path} - {keyword}")
                return False
    
    print("✅ 개인정보 검증 통과")
    return True
```

#### B. 자동 검증 통합
```python
def build_with_security_check():
    """보안 검증 포함 빌드"""
    # 1. 일반 빌드 실행
    success = build_exe()
    
    if success:
        # 2. 보안 검증 실행
        if validate_distribution_package(dist_dir):
            print("🎉 보안 검증 통과 - 배포 가능")
        else:
            print("❌ 보안 검증 실패 - 수정 필요")
            return False
    
    return success
```

## 📦 배포 패키지 구조

### 양산용 (Production)
```
배포판/
├── 급여명세서관리.exe
├── employees.json (빈 파일 또는 기본 구조만)
├── config.json (기본 설정만)
├── tutorial_data.xlsx
└── README.txt
```

### 테스트용 (Test)
```
배포판/
├── 급여명세서관리.exe
├── employees.json (샘플 데이터)
├── config.json (샘플 설정)
├── tutorial_data.xlsx
└── README.txt
```

### 개발용 (Dev)
```
배포판/
├── 급여명세서관리.exe
├── employees.json (원본 개발 데이터)
├── config.json (원본 개발 설정)
├── tutorial_data.xlsx
└── README.txt
```

## 🎯 실행 명령어

### 보안 강화 빌드
```bash
# 양산용 보안 빌드
python build_exe.py --version client --distribution-mode production

# 테스트용 샘플 데이터 빌드
python build_exe.py --version client --distribution-mode test

# 개발용 원본 데이터 빌드
python build_exe.py --version client --distribution-mode dev
```

### 보안 검증 전용 명령
```bash
# 배포 패키지 보안 검증
python build_exe.py --validate-only

# 암호화 옵션 포함 빌드
python build_exe.py --encrypt-data
```

## 🔐 보안 강화 효과

### 1. **✅ 개인정보 완전 보호**
- 개발 데이터 절대 포함되지 않음
- 위험 키워드 자동 검출 및 차단
- 모드별 데이터 분리로 보안 강화

### 2. **✅ 자동 검증 시스템**
- 배포 전 자동으로 위험 요소 검출
- 키워드 기반 위험도 평가
- 검증 로그 자동 기록

### 3. **✅ 모드별 배포**
- 용도에 맞는 적절한 데이터 제공
- 개발/테스트/양산 환경 분리
- 사용자 요구에 맞는 최적 배포

### 4. **✅ 암호화 옵션**
- 추가 보안이 필요한 경우 암호화 지원
- 실행 시 자동 복호화
- 복호화 실패 시 안전 모드 전환

### 5. **✅ 검증 로그**
- 모든 검증 과정 로그 기록
- 문제 발생 시 빠른 원인 파악
- 보안 이력 관리

## 📋 검증 항목

### 1. **보안 검증**
- [ ] 위험 키워드 검출 정확도 100%
- [ ] 암호화/복호화 정상 작동
- [ ] 모드별 데이터 정확성 검증

### 2. **기능 검증**
- [ ] 각 모드별 정상 실행
- [ ] 데이터 무결성 검증
- [ ] 복호화 실패 시 안전 모드 작동

### 3. **성능 검증**
- [ ] 암호화로 인한 성능 저하 최소화
- [ ] 검증 시간 최적화
- [ ] 메모리 사용량 최적화

## 🚀 구현 단계

### 1단계: **기본 보안 시스템 구축**
- 위험 키워드 정의
- 기본 검증 로직 구현
- 모드별 배포 옵션 추가

### 2단계: **고급 보안 기능**
- 데이터 암호화 시스템 구축
- 자동 검증 로직 개선
- 검증 로그 시스템 구현

### 3단계: **통합 및 최적화**
- 모든 보안 기능 통합
- 성능 최적화
- 사용자 피드백 반영

## 📝 결론

본 보안 개선 계획을 통해 급여명세서 생성기의 개인정보 보호 수준을 크게 향상시킬 수 있습니다. 특히 자동 검증 시스템과 모드별 배포 전략을 통해 개발자의 실수로 인한 개인정보 유출을 완전히 방지할 수 있을 것입니다.

보안 검증 시스템은 단순한 키워드 검출을 넘어, 지속적인 업데이트와 개선을 통해 더욱 강력한 보안 체계를 구축할 수 있을 것입니다.