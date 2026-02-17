#!/usr/bin/env python3
"""
logic.py 파일에서 allowances 변수 초기화를 추가하는 스크립트
"""

import re

# 파일 읽기
with open('logic.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 찾을 패턴: "# 추가 수당 항목들 (직원별 수당 데이터)" 다음 줄에 초기화 추가
old_pattern = r"(    # 추가 수당 항목들 \(직원별 수당 데이터\)\n)(    if employee_data and str\(user_summary\['user_id'\]\) in employee_data:)"
new_pattern = r"\1    allowances = {}  # 초기화 추가\n\2"

# 치환
new_content = re.sub(old_pattern, new_pattern, content)

# 변경 사항 확인
if new_content != content:
    # 파일 쓰기
    with open('logic.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ allowances = {} 초기화가 추가되었습니다.")
else:
    print("⚠️ 변경 사항이 없습니다. 패턴을 찾을 수 없습니다.")
    
    # 대체 패턴 시도
    print("\n대체 패턴으로 시도 중...")
    old_pattern2 = "    # 추가 수당 항목들 (직원별 수당 데이터)\n    if employee_data and str(user_summary['user_id']) in employee_data:"
    new_pattern2 = "    # 추가 수당 항목들 (직원별 수당 데이터)\n    allowances = {}  # 초기화 추가\n    if employee_data and str(user_summary['user_id']) in employee_data:"
    
    new_content2 = content.replace(old_pattern2, new_pattern2)
    
    if new_content2 != content:
        with open('logic.py', 'w', encoding='utf-8') as f:
            f.write(new_content2)
        print("✅ allowances = {} 초기화가 추가되었습니다. (대체 패턴)")
    else:
        print("❌ 여전히 패턴을 찾을 수 없습니다.")
        # 파일에서 해당 문자열 검색
        if "# 추가 수당 항목들" in content:
            print("   - '# 추가 수당 항목들'은 존재합니다")
        if "if employee_data and str(user_summary['user_id']) in employee_data:" in content:
            print("   - 'if employee_data and str(user_summary['user_id']) in employee_data:'는 존재합니다")
