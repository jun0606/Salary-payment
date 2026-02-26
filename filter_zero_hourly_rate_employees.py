def filter_zero_hourly_rate_employees(employee_data):
    """
    시급이 0원인 직원을 employee_data에서 제외합니다.
    
    Args:
        employee_data: 직원 데이터 딕셔너리
        
    Returns:
        시급이 0원이 아닌 직원들만 포함된 employee_data
    """
    if employee_data is None:
        return None
    
    # 시급이 0원이 아닌 직원만 필터링
    filtered_employee_data = {}
    for user_id, employee_info in employee_data.items():
        # 시급 정보 확인 (hourly_rate 또는 기본급 정보)
        hourly_rate = employee_info.get('hourly_rate', 0)
        
        # 시급이 0원이 아닌 경우만 포함
        if hourly_rate > 0:
            filtered_employee_data[user_id] = employee_info
    
    logging.info(f"Filtered employee_data from {len(employee_data)} to {len(filtered_employee_data)} employees (excluded zero hourly rate)")
    return filtered_employee_data