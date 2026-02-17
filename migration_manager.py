#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MigrationManager - 버전 기반 마이그레이션 시스템
SMART_MIGRATION_SYSTEM_DESIGN 구현
"""

import json
import os
import shutil
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class MigrationLogger:
    """마이그레이션 로깅 클래스"""
    
    def __init__(self, log_file: str = "migration.log"):
        self.log_file = log_file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_migration(self, version: str, action: str, details: str = ""):
        """마이그레이션 로그 기록"""
        self.logger.info(f"Migration {version}: {action} - {details}")
    
    def log_error(self, error_msg: str):
        """에러 로그 기록"""
        self.logger.error(f"Migration Error: {error_msg}")

class BackupManager:
    """백업 및 복구 관리 클래스"""
    
    def __init__(self, backup_dir: str = "backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, source_files: List[str], version: str) -> Optional[str]:
        """파일 백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{version}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            for file_path in source_files:
                if os.path.exists(file_path):
                    shutil.copy2(file_path, backup_path / os.path.basename(file_path))
            
            return str(backup_path)
        except Exception as e:
            return None
    
    def restore_backup(self, backup_path: str, target_files: List[str]) -> bool:
        """백업 복구"""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                return False
            
            for file_path in target_files:
                backup_file = backup_dir / os.path.basename(file_path)
                if backup_file.exists():
                    shutil.copy2(backup_file, file_path)
            
            return True
        except Exception as e:
            return False

class MigrationManager:
    """버전 기반 마이그레이션 관리 클래스"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.logger = MigrationLogger()
        self.backup_manager = BackupManager()
        self.current_version = "1.0.0"
        
        # 마이그레이션 스크립트 정의
        self.migration_scripts = {
            "1.0.0": self._migrate_to_v1_0_0,
            "1.1.0": self._migrate_to_v1_1_0,
            "1.2.0": self._migrate_to_v1_2_0,
        }
    
    def get_current_version(self) -> str:
        """현재 버전 확인"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('version', self.current_version)
        except Exception as e:
            self.logger.log_error(f"Failed to read config file: {e}")
        
        return self.current_version
    
    def set_version(self, version: str):
        """버전 설정"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['version'] = version
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
            self.logger.log_migration(version, "Version updated", f"Set to {version}")
        except Exception as e:
            self.logger.log_error(f"Failed to update version: {e}")
    
    def needs_migration(self) -> bool:
        """마이그레이션이 필요한지 확인"""
        current = self.get_current_version()
        return current != self.current_version
    
    def run_migration(self) -> bool:
        """마이그레이션 실행"""
        current = self.get_current_version()
        
        if not self.needs_migration():
            self.logger.log_migration(current, "No migration needed", "Already up to date")
            return True
        
        self.logger.log_migration(current, "Migration started", f"From {current} to {self.current_version}")
        
        # 백업 생성
        backup_path = self.backup_manager.create_backup(
            ["config.json", "employees.json", "tax_settings.json"], 
            current
        )
        
        if backup_path:
            self.logger.log_migration(current, "Backup created", backup_path)
        else:
            self.logger.log_error("Failed to create backup")
            return False
        
        try:
            # 마이그레이션 스크립트 실행
            if current in self.migration_scripts:
                self.migration_scripts[current]()
                self.set_version(self.current_version)
                self.logger.log_migration(current, "Migration completed", "Successfully migrated")
                return True
            else:
                self.logger.log_error(f"No migration script for version {current}")
                return False
                
        except Exception as e:
            # 에러 발생 시 백업 복구
            if backup_path and self.backup_manager.restore_backup(backup_path, 
                ["config.json", "employees.json", "tax_settings.json"]):
                self.logger.log_migration(current, "Rollback completed", "Restored from backup")
            else:
                self.logger.log_error("Failed to rollback from backup")
            
            self.logger.log_error(f"Migration failed: {e}")
            return False
    
    def _migrate_to_v1_0_0(self):
        """v1.0.0 마이그레이션 - 최소 JSON 구조 생성"""
        self.logger.log_migration("1.0.0", "Creating minimal JSON structure")
        
        # config.json 생성
        if not os.path.exists("config.json"):
            config_data = {
                "version": "1.0.0",
                "business_size": "small",
                "tax_settings": {
                    "national_pension": 0.045,
                    "health_insurance": 0.035,
                    "employment_insurance": 0.008,
                    "income_tax": 0.06,
                    "local_income_tax": 0.1
                },
                "allowance_settings": {
                    "meal_allowance": 10000,
                    "transportation_allowance": 100000
                }
            }
            
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.logger.log_migration("1.0.0", "Created", "config.json")
        
        # employees.json 생성
        if not os.path.exists("employees.json"):
            employees_data = {
                "employees": [],
                "companies": [],
                "allowances": []
            }
            
            with open("employees.json", 'w', encoding='utf-8') as f:
                json.dump(employees_data, f, ensure_ascii=False, indent=2)
            
            self.logger.log_migration("1.0.0", "Created", "employees.json")
    
    def _migrate_to_v1_1_0(self):
        """v1.1.0 마이그레이션 - HTML 템플릿 변수 추가"""
        self.logger.log_migration("1.1.0", "Adding HTML template variables")
        
        # config.json에 HTML 템플릿 변수 추가
        if os.path.exists("config.json"):
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # HTML 템플릿 변수 정의
            html_variables = {
                "weekly_holiday_allowance": "주휴수당",
                "overtime_allowance": "연장수당",
                "night_allowance": "야간수당",
                "holiday_allowance": "휴일수당",
                "meal_allowance": "식대",
                "transportation_allowance": "교통비",
                "performance_allowance": "성과수당",
                "position_allowance": "직책수당",
                "family_allowance": "가족수당",
                "etc_allowance": "기타수당"
            }
            
            config["html_template_variables"] = html_variables
            
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            self.logger.log_migration("1.1.0", "Updated", "config.json with HTML variables")
    
    def _migrate_to_v1_2_0(self):
        """v1.2.0 마이그레이션 - 연차 관리 시스템 추가"""
        self.logger.log_migration("1.2.0", "Adding annual leave management")
        
        # employees.json에 연차 데이터 구조 추가
        if os.path.exists("employees.json"):
            with open("employees.json", 'r', encoding='utf-8') as f:
                employees = json.load(f)
            
            # 연차 데이터 구조가 없으면 추가
            if "annual_leaves" not in employees:
                employees["annual_leaves"] = []
            
            with open("employees.json", 'w', encoding='utf-8') as f:
                json.dump(employees, f, ensure_ascii=False, indent=2)
            
            self.logger.log_migration("1.2.0", "Updated", "employees.json with annual leave structure")

def main():
    """메인 실행 함수"""
    migration_manager = MigrationManager()
    
    if migration_manager.needs_migration():
        print("마이그레이션이 필요합니다...")
        if migration_manager.run_migration():
            print("마이그레이션이 성공적으로 완료되었습니다.")
        else:
            print("마이그레이션에 실패했습니다. 백업에서 복구되었습니다.")
    else:
        print("최신 버전입니다. 마이그레이션이 필요하지 않습니다.")

if __name__ == "__main__":
    main()