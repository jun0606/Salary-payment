#!/usr/bin/env python3
"""
급여명세서 데이터 검증 레이어
"""

class ValidationError(Exception):
    """검증 오류"""
    pass

class PayslipDataValidator:
    """HTML 렌더링 전 데이터 검증"""
    
    def validate_payslip_data(self, payslip_data):
        """필수 변수 검증"""
        required_vars = [
            'data_month',
            'company_name',
            'name',
            'user_id',
            'base_pay',
            'weekly_holiday_allowance',
            'extra_pay',
            'night_pay',
            'allowance_items',
            'total_payment',
            'total_deduction',
            'net_pay',
            'calculation_note_1',
            'calculation_note_2',
            'calculation_note_3',
            'calculation_note_night',
            'show_night_note',
            'show_base_pay_note',
            'show_holiday_note',
            'show_overtime_note',
            'show_hourly_rate'
        ]
        
        missing_vars = []
        for var in required_vars:
            if var not in payslip_data:
                missing_vars.append(var)
        
        if missing_vars:
            raise ValidationError(f"필수 변수 누락: {missing_vars}")
        
        # rowspan 검증
        deduction_count = 6  # 고정값: 국민연금, 건강보험, 고용보험, 장기요양보험, 소득세, 지방소득세
        if payslip_data.get('rowspan') != deduction_count:
            raise ValidationError(f"rowspan 불일치: {payslip_data.get('rowspan')} != {deduction_count}")
        
        # 금액 유효성 검증
        amount_fields = ['total_payment', 'total_deduction', 'net_pay']
        for field in amount_fields:
            if not isinstance(payslip_data[field], (int, float)) or payslip_data[field] < 0:
                raise ValidationError(f"유효하지 않은 금액: {field} = {payslip_data[field]}")
        
        return True
    
    def validate_calculation_notes(self, payslip_data):
        """계산식 검증"""
        note_fields = ['calculation_note_1', 'calculation_note_2', 'calculation_note_3', 'calculation_note_night']
        
        for field in note_fields:
            if field not in payslip_data:
                raise ValidationError(f"계산식 누락: {field}")
            
            if not isinstance(payslip_data[field], str) or not payslip_data[field].strip():
                raise ValidationError(f"유효하지 않은 계산식: {field}")
        
        return True
    
    def validate_allowance_items(self, payslip_data):
        """수당 항목 검증"""
        allowance_items = payslip_data.get('allowance_items', [])
        
        if not isinstance(allowance_items, list):
            raise ValidationError("allowance_items는 리스트 형태여야 합니다")
        
        for item in allowance_items:
            if not isinstance(item, dict):
                raise ValidationError("수당 항목은 딕셔너리 형태여야 합니다")
            
            required_keys = ['name', 'amount', 'detail', 'type']
            for key in required_keys:
                if key not in item:
                    raise ValidationError(f"수당 항목에 누락된 키: {key}")
        
        return True
    
    def validate_business_size_compliance(self, payslip_data, business_size):
        """사업장 규모 적합성 검증"""
        # 5인 미만 사업장의 경우 연장/야간 가산 적용 검증
        if business_size == 'under_5':
            # 연장수당 가산 검증
            if '연장수당' in str(payslip_data.get('calculation_note_3', '')):
                if '1.5배' in str(payslip_data.get('calculation_note_3', '')):
                    raise ValidationError("5인 미만 사업장은 연장수당 가산 의무가 없습니다")
            
            # 야간수당 가산 검증
            if '야간수당' in str(payslip_data.get('calculation_note_night', '')):
                if '0.5배' in str(payslip_data.get('calculation_note_night', '')):
                    raise ValidationError("5인 미만 사업장은 야간수당 가산 의무가 없습니다")
        
        return True
    
    def validate_total_consistency(self, payslip_data):
        """총액 일관성 검증"""
        # 지급 합계 검증
        expected_payment = (
            payslip_data.get('base_pay', 0) +
            payslip_data.get('weekly_holiday_allowance', 0) +
            payslip_data.get('extra_pay', 0) +
            payslip_data.get('night_pay', 0)
        )
        
        actual_payment = payslip_data.get('total_payment', 0)
        
        if abs(expected_payment - actual_payment) > 10:  # 10원 오차 허용
            raise ValidationError(f"지급 합계 불일치: 예상={expected_payment}, 실제={actual_payment}")
        
        # 실지급액 검증
        expected_net = actual_payment - payslip_data.get('total_deduction', 0)
        actual_net = payslip_data.get('net_pay', 0)
        
        if abs(expected_net - actual_net) > 10:
            raise ValidationError(f"실지급액 불일치: 예상={expected_net}, 실제={actual_net}")
        
        return True

if __name__ == "__main__":
    # 테스트 실행
    validator = PayslipDataValidator()
    
    # 샘플 데이터
    sample_data = {
        'data_month': '2025년 12월',
        'company_name': '테스트회사',
        'name': '테스트',
        'user_id': '001',
        'base_pay': 2000000,
        'weekly_holiday_allowance': 100000,
        'extra_pay': 50000,
        'night_pay': 30000,
        'allowance_items': [
            {'name': '기본급', 'amount': 2000000, 'detail': '테스트', 'type': 'base_pay'}
        ],
        'total_payment': 2180000,
        'total_deduction': 180000,
        'net_pay': 2000000,
        'calculation_note_1': '테스트',
        'calculation_note_2': '테스트',
        'calculation_note_3': '테스트',
        'calculation_note_night': '테스트',
        'show_night_note': True,
        'show_base_pay_note': True,
        'show_holiday_note': True,
        'show_overtime_note': True,
        'show_hourly_rate': True
    }
    
    print("=== 급여명세서 데이터 검증 ===")
    
    try:
        validator.validate_payslip_data(sample_data)
        print("✅ 기본 변수 검증 통과")
    except ValidationError as e:
        print(f"❌ 기본 변수 검증 실패: {e}")
    
    try:
        validator.validate_calculation_notes(sample_data)
        print("✅ 계산식 검증 통과")
    except ValidationError as e:
        print(f"❌ 계산식 검증 실패: {e}")
    
    try:
        validator.validate_allowance_items(sample_data)
        print("✅ 수당 항목 검증 통과")
    except ValidationError as e:
        print(f"❌ 수당 항목 검증 실패: {e}")
    
    try:
        validator.validate_total_consistency(sample_data)
        print("✅ 총액 일관성 검증 통과")
    except ValidationError as e:
        print(f"❌ 총액 일관성 검증 실패: {e}")