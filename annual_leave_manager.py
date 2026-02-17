#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연차 관리 시스템
- 연차 발생/사용/잔여 관리
- 퇴사 시 연차수당 자동 계산
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnnualLeaveManager:
    """연차 관리 클래스"""
    
    def __init__(self, db_path: str = "annual_leave.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 직원 연차 설정 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employee_leave_settings (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                hire_date DATE NOT NULL,
                resignation_date DATE,
                annual_leave_days REAL DEFAULT 15,
                used_leave_days REAL DEFAULT 0,
                remaining_leave_days REAL DEFAULT 15,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 연차 사용 이력 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leave_usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                use_date DATE NOT NULL,
                days_used REAL NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES employee_leave_settings(user_id)
            )
        ''')
        
        # 월별 연차 발생 테이블 (1년 미만 직원용)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_leave_accrual (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                year_month TEXT NOT NULL,
                accrued_days REAL DEFAULT 1.0,
                FOREIGN KEY (user_id) REFERENCES employee_leave_settings(user_id),
                UNIQUE(user_id, year_month)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("연차 관리 데이터베이스 초기화 완료")
    
    def calculate_annual_leave(self, hire_date: str, current_date: str, 
                               resignation_date: str = None) -> Dict:
        """
        근로기준법에 따른 연차 계산
        
        Args:
            hire_date: 입사일 (YYYY-MM-DD)
            current_date: 기준일 (YYYY-MM-DD)
            resignation_date: 퇴사일 (YYYY-MM-DD, optional)
        
        Returns:
            {
                'total_leave': 총 발생 연차,
                'used_leave': 사용 연차,
                'remaining_leave': 잔여 연차,
                'is_under_1_year': 1년 미만 여부
            }
        """
        hire = datetime.strptime(hire_date, '%Y-%m-%d')
        current = datetime.strptime(current_date, '%Y-%m-%d')
        resign = datetime.strptime(resignation_date, '%Y-%m-%d') if resignation_date else None
        
        # 기준일 설정 (퇴사일이 있으면 퇴사일까지, 없으면 현재)
        end_date = resign if resign else current
        
        # 근무 일수 계산
        tenure_days = (end_date - hire).days
        
        if tenure_days < 0:
            return {
                'total_leave': 0,
                'used_leave': 0,
                'remaining_leave': 0,
                'is_under_1_year': True
            }
        
        if tenure_days < 365:
            # 1년 미만: 월 1일 발생 (입사일 기준 한 달 후부터)
            # 만약 1월 15일 입사면 2월 15일부터 1일씩 발생
            months_worked = 0
            current_month = hire.replace(day=15) + timedelta(days=32)
            current_month = current_month.replace(day=15)
            
            while current_month <= end_date:
                months_worked += 1
                next_month = current_month + timedelta(days=32)
                current_month = next_month.replace(day=15)
            
            total_leave = min(months_worked, 11)  # 최대 11일
            is_under_1_year = True
        else:
            # 1년 이상: 15일 + (2년마다 1일 추가)
            years = tenure_days // 365
            additional_days = max(0, (years - 1) // 2)
            total_leave = min(15 + additional_days, 25)  # 최대 25일
            is_under_1_year = False
        
        return {
            'total_leave': float(total_leave),
            'used_leave': 0,  # 별도로 계산 필요
            'remaining_leave': float(total_leave),  # 사용 후 계산
            'is_under_1_year': is_under_1_year
        }
    
    def add_employee(self, user_id: str, name: str, hire_date: str,
                     resignation_date: str = None):
        """직원 등록 및 연차 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 연차 계산
        leave_info = self.calculate_annual_leave(
            hire_date,
            datetime.now().strftime('%Y-%m-%d'),
            resignation_date
        )
        
        cursor.execute('''
            INSERT OR REPLACE INTO employee_leave_settings 
            (user_id, name, hire_date, resignation_date, annual_leave_days, 
             used_leave_days, remaining_leave_days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, name, hire_date, resignation_date,
            leave_info['total_leave'], 0, leave_info['total_leave']
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"직원 {name}({user_id}) 연차 등록 완료: {leave_info['total_leave']}일")
    
    def use_leave(self, user_id: str, use_date: str, days: float, 
                  reason: str = "") -> bool:
        """연차 사용 등록"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 현재 잔여 연차 확인
        cursor.execute('''
            SELECT remaining_leave_days FROM employee_leave_settings 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            logger.error(f"직원 {user_id}를 찾을 수 없습니다")
            return False
        
        remaining = result[0]
        if remaining < days:
            conn.close()
            logger.error(f"잔여 연차 부족: {remaining}일 중 {days}일 사용 시도")
            return False
        
        # 연차 사용 이력 추가
        cursor.execute('''
            INSERT INTO leave_usage_history (user_id, use_date, days_used, reason)
            VALUES (?, ?, ?, ?)
        ''', (user_id, use_date, days, reason))
        
        # 잔여 연차 차감
        cursor.execute('''
            UPDATE employee_leave_settings 
            SET used_leave_days = used_leave_days + ?,
                remaining_leave_days = remaining_leave_days - ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (days, days, user_id))
        
        conn.commit()
        conn.close()
        logger.info(f"연차 사용 등록: {user_id}, {use_date}, {days}일")
        return True
    
    def get_leave_status(self, user_id: str) -> Optional[Dict]:
        """직원 연차 현황 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, hire_date, resignation_date,
                   annual_leave_days, used_leave_days, remaining_leave_days
            FROM employee_leave_settings 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'user_id': result[0],
            'name': result[1],
            'hire_date': result[2],
            'resignation_date': result[3],
            'annual_leave_days': result[4],
            'used_leave_days': result[5],
            'remaining_leave_days': result[6]
        }
    
    def get_leave_usage_history(self, user_id: str, 
                                year: int = None) -> List[Dict]:
        """연차 사용 이력 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if year:
            cursor.execute('''
                SELECT id, use_date, days_used, reason, created_at
                FROM leave_usage_history 
                WHERE user_id = ? AND strftime('%Y', use_date) = ?
                ORDER BY use_date DESC
            ''', (user_id, str(year)))
        else:
            cursor.execute('''
                SELECT id, use_date, days_used, reason, created_at
                FROM leave_usage_history 
                WHERE user_id = ?
                ORDER BY use_date DESC
            ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [{
            'id': r[0],
            'use_date': r[1],
            'days_used': r[2],
            'reason': r[3],
            'created_at': r[4]
        } for r in results]
    
    def calculate_leave_allowance(self, user_id: str, 
                                  base_pay: float) -> Optional[Dict]:
        """
        퇴사 시 연차수당 계산
        
        Args:
            user_id: 직원 ID
            base_pay: 월 기본급
        
        Returns:
            {
                'total_leave': 총 연차,
                'used_leave': 사용 연차,
                'unused_leave': 미사용 연차,
                'daily_wage': 1일 통상임금,
                'leave_allowance': 연차수당
            }
        """
        status = self.get_leave_status(user_id)
        if not status:
            return None
        
        if not status['resignation_date']:
            logger.warning(f"직원 {user_id}는 퇴사일이 설정되지 않았습니다")
            return None
        
        # 현재까지 발생한 총 연차 재계산
        leave_info = self.calculate_annual_leave(
            status['hire_date'],
            status['resignation_date'],
            status['resignation_date']
        )
        
        total_leave = leave_info['total_leave']
        used_leave = status['used_leave_days']
        unused_leave = max(0, total_leave - used_leave)
        
        # 1일 통상임금 = (월급 / 209시간) * 8시간
        daily_wage = (base_pay / 209) * 8
        
        # 연차수당
        leave_allowance = unused_leave * daily_wage
        
        return {
            'total_leave': total_leave,
            'used_leave': used_leave,
            'unused_leave': unused_leave,
            'daily_wage': round(daily_wage, 0),
            'leave_allowance': round(leave_allowance, 0)
        }
    
    def sync_from_employees_json(self, employees_json_path: str):
        """employees.json에서 직원 데이터 동기화"""
        try:
            with open(employees_json_path, 'r', encoding='utf-8') as f:
                employees = json.load(f)
            
            for user_id, info in employees.items():
                hire_date = info.get('hire_date')
                resignation_date = info.get('resignation_date')
                name = info.get('name', user_id)
                
                if hire_date:
                    self.add_employee(user_id, name, hire_date, resignation_date)
            
            logger.info(f"employees.json 동기화 완료: {len(employees)}명")
        except Exception as e:
            logger.error(f"동기화 실패: {e}")


# 테스트 코드
if __name__ == "__main__":
    manager = AnnualLeaveManager()
    
    # 테스트 직원 등록
    manager.add_employee("TEST001", "홍길동", "2024-01-15")
    
    # 연차 사용
    manager.use_leave("TEST001", "2025-12-20", 1.0, "개인 사정")
    manager.use_leave("TEST001", "2025-12-23", 0.5, "병원 방문")
    
    # 현황 조회
    status = manager.get_leave_status("TEST001")
    print("연차 현황:", status)
    
    # 사용 이력
    history = manager.get_leave_usage_history("TEST001")
    print("사용 이력:", history)
    
    # 연차수당 계산 (퇴사자 가정)
    manager.add_employee("TEST002", "김퇴사", "2024-03-01", "2025-12-15")
    allowance = manager.calculate_leave_allowance("TEST002", 3135000)
    print("연차수당:", allowance)
