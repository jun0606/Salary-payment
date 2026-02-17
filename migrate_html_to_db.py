#!/usr/bin/env python3
"""
기존 HTML 급여명세서 파일들을 DB에 저장하는 마이그레이션 스크립트
"""

import os
import re
import uuid
import hashlib
from datetime import datetime
from bs4 import BeautifulSoup
from database_manager import get_database

def extract_payslip_data(html_content, file_path):
    """
    HTML 콘텐츠에서 급여명세서 데이터를 추출

    Args:
        html_content: HTML 문자열
        file_path: 파일 경로 (디버깅용)

    Returns:
        dict: 추출된 데이터
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    data = {
        'id': str(uuid.uuid4()),
        'employee_name': '',
        'company_name': '',
        'pay_month': '',
        'html_content': html_content,
        'employee_id': '',
        'version': 1,
        'input_data_hash': hashlib.sha256(html_content.encode()).hexdigest()
    }

    try:
        # 제목에서 기간 추출
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # "2025년 12월 급여명세서 - 박다은" 형식
            match = re.search(r'(\d{4})년 (\d{1,2})월', title_text)
            if match:
                year = match.group(1)
                month = match.group(2).zfill(2)
                data['pay_month'] = f"{year}-{month}"

        # 직원 정보 테이블에서 데이터 추출
        info_table = soup.find('table', class_='info-table')
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)

                    if '회사명' in label:
                        data['company_name'] = value
                    elif '성명' in label:
                        data['employee_name'] = value
                    elif '사번' in label:
                        data['employee_id'] = value or f"emp_{hash(data['employee_name']) % 10000}"

        # employee_id가 없으면 생성
        if not data['employee_id'] and data['employee_name']:
            data['employee_id'] = f"emp_{hash(data['employee_name']) % 10000}"

        print(f"추출 완료: {data['employee_name']} ({data['pay_month']}) - {data['company_name']}")

    except Exception as e:
        print(f"데이터 추출 오류 ({file_path}): {e}")

    return data

def migrate_html_files_to_db():
    """
    HTML 파일들을 DB에 저장
    """
    db = get_database()

    # HTML 파일들이 있는 폴더들
    html_dirs = [
        '급여명세서_저장본/2025년',
        '급여명세서_저장본/2026년'  # 미래 폴더도 확인
    ]

    migrated_count = 0
    skipped_count = 0

    for html_dir in html_dirs:
        if not os.path.exists(html_dir):
            print(f"디렉토리가 존재하지 않음: {html_dir}")
            continue

        print(f"\n=== {html_dir} 처리 시작 ===")

        for filename in os.listdir(html_dir):
            if not filename.endswith('.html'):
                continue

            file_path = os.path.join(html_dir, filename)

            try:
                # HTML 파일 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                # 데이터 추출
                payslip_data = extract_payslip_data(html_content, file_path)

                # 필수 데이터 확인
                if not all([
                    payslip_data['employee_name'],
                    payslip_data['company_name'],
                    payslip_data['pay_month']
                ]):
                    print(f"필수 데이터 누락으로 건너뜀: {filename}")
                    skipped_count += 1
                    continue

                # DB에 이미 존재하는지 확인 (동일 직원/기간/버전)
                existing_records = db.get_payslip_records(
                    filters={
                        'employee_name': payslip_data['employee_name'],
                        'pay_month': payslip_data['pay_month']
                    },
                    limit=1
                )

                if existing_records:
                    print(f"이미 존재하여 건너뜀: {payslip_data['employee_name']} ({payslip_data['pay_month']})")
                    skipped_count += 1
                    continue

                # DB에 저장
                success = db.save_payslip_record(payslip_data)
                if success:
                    print(f"저장 성공: {payslip_data['employee_name']} ({payslip_data['pay_month']})")
                    migrated_count += 1
                else:
                    print(f"저장 실패: {payslip_data['employee_name']} ({payslip_data['pay_month']})")
                    skipped_count += 1

            except Exception as e:
                print(f"파일 처리 오류 ({filename}): {e}")
                skipped_count += 1

    print("\n=== 마이그레이션 완료 ===")
    print(f"저장 성공: {migrated_count}개")
    print(f"건너뜀: {skipped_count}개")
    print(f"총 처리: {migrated_count + skipped_count}개")

    # 검증
    print("\n=== DB 검증 ===")
    total_records = len(db.get_payslip_records(limit=1000))
    print(f"DB 총 레코드 수: {total_records}")

if __name__ == "__main__":
    print("HTML 급여명세서 파일을 DB로 마이그레이션 시작...")
    migrate_html_files_to_db()
    print("마이그레이션 완료!")
