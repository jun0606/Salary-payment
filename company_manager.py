#!/usr/bin/env python3
"""
중앙 집중식 회사 관리 시스템
CompanyManager 클래스를 통해 config.json 접근을 전담하고,
시그널-슬롯 기반 동기화 체계를 구축합니다.
"""

import os
import json
import shutil
import logging
from PyQt6.QtCore import QObject, pyqtSignal


class CompanyManager(QObject):
    """
    중앙 집중식 회사 관리 시스템
    
    기능:
    - config.json 접근 전담
    - 회사 정보 CRUD 작업
    - 변경 시그널 방출
    - 데이터 무결성 검증
    - 트랜잭션 처리
    """
    
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
        """config.json에서 회사 정보 로드 (에러 핸들링 강화)"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._companies = data.get('companies', {})
            else:
                self._companies = {}
        except json.JSONDecodeError as e:
            # JSON 파싱 오류 시 기본값 설정
            logging.error(f"JSON 파싱 오류: {e}")
            self._companies = {}
            self._save_companies()
        except Exception as e:
            # 기타 오류 처리
            logging.error(f"회사 정보 로드 중 오류 발생: {e}")
            raise Exception(f"회사 정보 로드 중 오류 발생: {str(e)}")
    
    def _save_companies(self):
        """config.json 저장 (트랜잭션 처리, 기존 데이터 보존)"""
        try:
            # 기존 config.json 데이터 로드 (세무사 정보 등 보존)
            existing_data = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except (json.JSONDecodeError, Exception):
                    existing_data = {}
            
            # companies 키만 업데이트
            existing_data['companies'] = self._companies
            
            # 임시 파일에 저장 후 원본 파일로 이동 (원자성 보장)
            temp_path = self.config_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            # 원본 파일 백업
            if os.path.exists(self.config_path):
                backup_path = self.config_path + '.backup'
                shutil.copy2(self.config_path, backup_path)
            
            # 임시 파일을 원본 파일로 이동
            os.replace(temp_path, self.config_path)
            
        except Exception as e:
            # 저장 실패 시 롤백
            temp_path = self.config_path + '.tmp'
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logging.error(f"회사 정보 저장 중 오류 발생: {e}")
            raise Exception(f"회사 정보 저장 중 오류 발생: {str(e)}")
    
    def get_companies(self):
        """회사 목록 반환"""
        return self._companies.copy()
    
    def get_company(self, company_id):
        """특정 회사 정보 반환"""
        return self._companies.get(company_id)
    
    def get_company_by_name(self, company_name):
        """회사명으로 회사 정보 반환"""
        for company_id, company_info in self._companies.items():
            if company_info.get('name') == company_name:
                return company_id, company_info
        return None, None
    
    def add_company(self, company_data):
        """회사 추가 (트랜잭션 처리)"""
        try:
            # 1. ID 중복 검사
            company_id = company_data.get('company_id')
            if company_id in self._companies:
                raise Exception(f"이미 존재하는 회사 ID입니다: {company_id}")
            
            # 2. 데이터 유효성 검증
            self._validate_company_data(company_data)
            
            # 3. 트랜잭션 시작
            # (현재는 메모리에서 작업 후 파일에 저장)
            
            # 4. config.json 저장
            self._companies[company_id] = company_data
            self._save_companies()
            
            # 5. 시그널 방출
            self.company_added.emit(company_id)
            self.company_changed.emit()
            
            logging.info(f"회사 추가 성공: {company_id} - {company_data.get('name')}")
            
        except Exception as e:
            logging.error(f"회사 추가 실패: {e}")
            raise Exception(f"회사 추가 중 오류 발생: {str(e)}")
    
    def modify_company(self, company_id, company_data):
        """회사 수정 (트랜잭션 처리)"""
        try:
            # 1. 회사 존재 검사
            if company_id not in self._companies:
                raise Exception(f"존재하지 않는 회사 ID입니다: {company_id}")
            
            # 2. 데이터 유효성 검증
            self._validate_company_data(company_data)
            
            # 3. 트랜잭션 시작
            
            # 4. config.json 저장
            self._companies[company_id] = company_data
            self._save_companies()
            
            # 5. 시그널 방출
            self.company_modified.emit(company_id)
            self.company_changed.emit()
            
            logging.info(f"회사 수정 성공: {company_id} - {company_data.get('name')}")
            
        except Exception as e:
            logging.error(f"회사 수정 실패: {e}")
            raise Exception(f"회사 수정 중 오류 발생: {str(e)}")
    
    def delete_company(self, company_id):
        """회사 삭제 (트랜잭션 처리)"""
        try:
            # 1. 회사 존재 검사
            if company_id not in self._companies:
                raise Exception(f"존재하지 않는 회사 ID입니다: {company_id}")
            
            # 2. 삭제 가능 여부 검사 (사용 중인 회사인지)
            if self._is_company_in_use(company_id):
                raise Exception(f"사용 중인 회사는 삭제할 수 없습니다: {company_id}")
            
            # 3. 트랜잭션 시작
            
            # 4. config.json 저장
            deleted_company = self._companies.pop(company_id)
            self._save_companies()
            
            # 5. 시그널 방출
            self.company_deleted.emit(company_id)
            self.company_changed.emit()
            
            logging.info(f"회사 삭제 성공: {company_id} - {deleted_company.get('name')}")
            
        except Exception as e:
            logging.error(f"회사 삭제 실패: {e}")
            raise Exception(f"회사 삭제 중 오류 발생: {str(e)}")
    
    def _validate_company_data(self, company_data):
        """회사 데이터 유효성 검증"""
        required_fields = ['company_id', 'name', 'business_size', 'industry_type', 'tax_office', 'business_registration']
        
        for field in required_fields:
            if field not in company_data:
                raise Exception(f"필수 필드 누락: {field}")
        
        # 사업장 규모 검증
        business_size = company_data.get('business_size')
        if business_size not in ['over_5', 'under_5']:
            raise Exception(f"유효하지 않은 사업장 규모: {business_size}")
        
        # 회사명 검증
        company_name = company_data.get('name', '').strip()
        if not company_name:
            raise Exception("회사명을 입력해주세요")
        
        # 회사명 중복 검사 (ID는 중복 검사에서 수행)
        for existing_id, existing_info in self._companies.items():
            if existing_id != company_data.get('company_id') and existing_info.get('name') == company_name:
                raise Exception(f"이미 존재하는 회사명입니다: {company_name}")
    
    def _is_company_in_use(self, company_id):
        """회사가 사용 중인지 검사 (employees.json에서 연결된 직원 확인)"""
        try:
            employees_path = os.path.join(os.path.dirname(self.config_path), 'employees.json')
            if os.path.exists(employees_path):
                with open(employees_path, 'r', encoding='utf-8') as f:
                    employees_data = json.load(f)
                
                for emp_id, emp_info in employees_data.get('employees', {}).items():
                    if isinstance(emp_info, dict) and emp_info.get('company_id') == company_id:
                        return True
            return False
        except Exception as e:
            logging.error(f"회사 사용 여부 확인 중 오류: {e}")
            return False  # 오류 시 삭제 허용
    
    def get_company_list_for_combo(self):
        """콤보박스용 회사 목록 반환"""
        company_list = []
        for company_id, company_info in self._companies.items():
            company_list.append({
                'id': company_id,
                'name': company_info.get('name', ''),
                'business_size': company_info.get('business_size', 'over_5')
            })
        return company_list
    
    def get_default_company(self):
        """기본 회사 반환"""
        if self._companies:
            first_company_id = next(iter(self._companies))
            return first_company_id, self._companies[first_company_id]
        return None, None
    
    def create_default_company_if_empty(self):
        """회사가 없을 경우 기본 회사 생성"""
        if not self._companies:
            default_company = {
                "company_id": "default_company",
                "name": "기본 회사",
                "business_size": "over_5",
                "industry_type": "서비스업",
                "tax_office": "세무서",
                "business_registration": "000-00-00000"
            }
            self.add_company(default_company)
            return True
        return False
    
    def get_company_count(self):
        """회사 수 반환"""
        return len(self._companies)
    
    def is_company_exists(self, company_id):
        """회사 존재 여부 확인"""
        return company_id in self._companies
    
    def get_company_id_by_name(self, company_name):
        """회사명으로 회사 ID 반환"""
        for company_id, company_info in self._companies.items():
            if company_info.get('name') == company_name:
                return company_id
        return None