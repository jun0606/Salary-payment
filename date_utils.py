from datetime import datetime, timedelta
import holidays

def adjust_for_holiday(date_str: str, year_month_context: str, direction: str = 'before') -> str:
    """
    Adjusts a date if it falls on a weekend or a South Korean public holiday.

    :param date_str: The date string to adjust (can be "YYYY-MM-DD" or just "DD").
    :param year_month_context: The "YYYY-MM" string to provide context if date_str is only a day.
    :param direction: 'before' or 'after' to adjust to the previous or next working day.
    :return: The adjusted date string in "YYYY-MM-DD" format.
    """
    if not date_str.strip():
        return ""

    try:
        if '-' in date_str:
            # Full date provided
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            # Only day provided, use context
            if not year_month_context:
                raise ValueError("Year-month context is required when only providing the day.")
            dt = datetime.strptime(f"{year_month_context}-{int(date_str):02d}", "%Y-%m-%d")
    except ValueError:
        # Return original string if format is incorrect
        return date_str

    kr_holidays = holidays.KR()
    
    # Check if the original date is a holiday
    is_original_date_holiday = dt.weekday() >= 5 or dt in kr_holidays

    # Loop to find the next valid working day
    while dt.weekday() >= 5 or dt in kr_holidays:
        if direction == 'before':
            dt -= timedelta(days=1)
        else: # 'after'
            dt += timedelta(days=1)
            
    return dt.strftime("%Y-%m-%d"), is_original_date_holiday


def check_for_holiday(date_str: str, year_month_context: str) -> bool:
    """
    Checks if a given date falls on a weekend or a South Korean public holiday.

    :param date_str: The date string to check ("YYYY-MM-DD" or just "DD").
    :param year_month_context: The "YYYY-MM" string to provide context if date_str is only a day.
    :return: True if the date is a holiday (weekend or public holiday), False otherwise.
    """
    if not date_str.strip():
        return False

    try:
        if '-' in date_str:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            if not year_month_context:
                # If context is missing and only day is provided, consider it not a holiday for safety
                return False 
            dt = datetime.strptime(f"{year_month_context}-{int(date_str):02d}", "%Y-%m-%d")
    except ValueError:
        return False # Invalid date format, not a holiday

    kr_holidays = holidays.KR()
    return dt.weekday() >= 5 or dt in kr_holidays

if __name__ == '__main__':
    # --- Test Cases ---
    y_m_context = "2025-05"
    
    # Weekend tests
    may_3_saturday = "2025-05-03"
    print(f"{may_3_saturday} (Sat) -> Before: {adjust_for_holiday(may_3_saturday, y_m_context, 'before')}") # Expect 2025-05-02
    print(f"{may_3_saturday} (Sat) -> After:  {adjust_for_holiday(may_3_saturday, y_m_context, 'after')}")  # Expect 2025-05-06 (5th is holiday)

    may_4_sunday = "4"
    print(f"{y_m_context}-{may_4_sunday} (Sun) -> Before: {adjust_for_holiday(may_4_sunday, y_m_context, 'before')}") # Expect 2025-05-02
    print(f"{y_m_context}-{may_4_sunday} (Sun) -> After:  {adjust_for_holiday(may_4_sunday, y_m_context, 'after')}")  # Expect 2025-05-06

    # Public holiday tests (2025)
    may_5_childrens_day = "5"
    print(f"Children's Day 2025-05-05 (Mon) -> Before: {adjust_for_holiday(may_5_childrens_day, y_m_context, 'before')}") # Expect 2025-05-02
    print(f"Children's Day 2025-05-05 (Mon) -> After:  {adjust_for_holiday(may_5_childrens_day, y_m_context, 'after')}")  # Expect 2025-05-06
    
    y_m_context_sep = "2025-10"
    oct_3_national_foundation = "2025-10-03"
    print(f"Foundation Day {oct_3_national_foundation} (Fri) -> Before: {adjust_for_holiday(oct_3_national_foundation, y_m_context_sep, 'before')}") # Expect 2025-10-02
    print(f"Foundation Day {oct_3_national_foundation} (Fri) -> After:  {adjust_for_holiday(oct_3_national_foundation, y_m_context_sep, 'after')}") # Expect 2025-10-06 (weekend) 
    
    # Non-holiday test
    may_7_wednesday = "7"
    print(f"Non-holiday 2025-05-07 (Wed) -> Before: {adjust_for_holiday(may_7_wednesday, y_m_context, 'before')}") # Expect 2025-05-07
    print(f"Non-holiday 2025-05-07 (Wed) -> After:  {adjust_for_holiday(may_7_wednesday, y_m_context, 'after')}")  # Expect 2025-05-07

    print("\n--- check_for_holiday tests ---")
    print(f"2025-05-03 (Sat) is holiday: {check_for_holiday(may_3_saturday, y_m_context)}") # True
    print(f"2025-05-04 (Sun) is holiday: {check_for_holiday(may_4_sunday, y_m_context)}") # True
    print(f"2025-05-05 (Mon, Holiday) is holiday: {check_for_holiday(may_5_childrens_day, y_m_context)}") # True
    print(f"2025-05-07 (Wed, not Holiday) is holiday: {check_for_holiday(may_7_wednesday, y_m_context)}") # False
    print(f"Invalid date is holiday: {check_for_holiday('invalid-date', y_m_context)}") # False
    print(f"Empty date is holiday: {check_for_holiday('', y_m_context)}") # False