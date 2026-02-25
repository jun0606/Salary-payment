#!/usr/bin/env python3
"""
시트명 파싱 로직 테스트 파일
"""

import re
import sys
import os

# 현재 디렉토리의 상위 디렉토리를 Python path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def safe_parse_month_from_sheet_name(sheet_name):
    """시트명에서 월을 안전하게 추출하는 함수"""
    try:
        # 정규식 기반 정확한 파싱
        # 패턴 1: "2026년 1월" 형식
        match = re.match(r'^\d{4}년\s*(0?[1-9]|1[0-2])월$', sheet_name)
        if match:
            month_num = int(match.group(1))
            print(f"파싱 성공: '{sheet_name}' → 월: {month_num}")
            return month_num
        
        # 패턴 2: "1월" 형식
        match = re.match(r'^(0?[1-9]|1[0-2])월$', sheet_name)
        if match:
            month_num = int(match.group(1))
            print(f"파싱 성공: '{sheet_name}' → 월: {month_num}")
            return month_num
        
        # 매칭 실패
        print(f"파싱 실패: '{sheet_name}' - 정규식 매칭되지 않음")
        return None
        
    except Exception as e:
        print(f"파싱 오류: 시트명='{sheet_name}', 오류='{e}'")
        return None

def test_current_logic(sheet_name):
    """현재 로직 테스트"""
    print(f"\n=== 현재 로직 테스트: '{sheet_name}' ===")
    
    # 현재 로직 시뮬레이션
    month_str = ''.join(filter(str.isdigit, sheet_name))
    
    try:
        if len(month_str) > 2:
            month_num = int(month_str[-2:])
        elif len(month_str) == 2:
            month_num = int(month_str)
        else:
            month_num = int(month_str) if month_str else 0
    except ValueError:
        month_num = 0
    
    print(f"month_str: '{month_str}'")
    print(f"month_num: {month_num}")
    
    return month_num

def test_improved_logic(sheet_name):
    """개선된 로직 테스트"""
    print(f"\n=== 개선된 로직 테스트: '{sheet_name}' ===")
    
    month_num = safe_parse_month_from_sheet_name(sheet_name)
    print(f"결과: {month_num}")
    
    return month_num

def run_tests():
    """테스트 실행"""
    print("시트명 파싱 로직 테스트")
    print("=" * 50)
    
    # 테스트 케이스 정의
    test_cases = [
        # 정상 케이스
        ("2026년 1월", 1),
        ("2026년 01월", 1),
        ("2026년 12월", 12),
        ("1월", 1),
        ("12월", 12),
        ("01월", 1),
        ("02월", 2),
        
        # 문제 케이스
        ("2026년 61월", None),  # 비정상 입력
        ("61월", None),        # 비정상 입력
        ("2026년 13월", None), # 비정상 입력
        ("13월", None),        # 비정상 입력
        
        # 경계 케이스
        ("2026년 0월", None),  # 비정상 입력
        ("0월", None),         # 비정상 입력
        ("2026년 월", None),   # 비정상 입력
        ("월", None),          # 비정상 입력
    ]
    
    print("\n" + "=" * 50)
    print("테스트 결과 비교")
    print("=" * 50)
    
    for sheet_name, expected in test_cases:
        print(f"\n테스트 케이스: '{sheet_name}' (기대값: {expected})")
        print("-" * 40)
        
        # 현재 로직 테스트
        current_result = test_current_logic(sheet_name)
        
        # 개선된 로직 테스트
        improved_result = test_improved_logic(sheet_name)
        
        # 결과 비교
        current_correct = (current_result == expected)
        improved_correct = (improved_result == expected)
        
        print(f"\n결과 비교:")
        print(f"현재 로직: {current_result} ({'✓' if current_correct else '✗'})")
        print(f"개선 로직: {improved_result} ({'✓' if improved_correct else '✗'})")
        
        if current_correct and improved_correct:
            print("상태: 둘 다 정상")
        elif not current_correct and improved_correct:
            print("상태: 개선 로직만 정상 (문제 해결)")
        elif current_correct and not improved_correct:
            print("상태: 현재 로직만 정상 (검토 필요)")
        else:
            print("상태: 둘 다 오류 (검토 필요)")

def main():
    """메인 함수"""
    print("시트명 파싱 로직 개선 테스트")
    print("=" * 50)
    
    # 개별 테스트
    print("\n1. 개별 테스트")
    print("-" * 30)
    
    # 문제 케이스 집중 테스트
    problem_cases = ["2026년 1월", "2026년 01월", "2026년 61월"]
    
    for case in problem_cases:
        print(f"\n문제 케이스: '{case}'")
        current = test_current_logic(case)
        improved = test_improved_logic(case)
        print(f"현재: {current}, 개선: {improved}")
    
    # 전체 테스트
    print("\n\n2. 전체 테스트")
    print("-" * 30)
    run_tests()
    
    print("\n" + "=" * 50)
    print("테스트 완료")
    print("=" * 50)

if __name__ == "__main__":
    main()