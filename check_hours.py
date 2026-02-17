import pandas as pd

# 11월 시트
df_nov = pd.read_excel('12월 급여포함.xlsx', sheet_name='2025년 11월', header=None)
choi_nov = df_nov[df_nov[1] == '190335410']
print('=== 11월 최유진 데이터 ===')
print(f'데이터 건수: {len(choi_nov)}')
if not choi_nov.empty:
    total_hours = 0
    for idx, row in choi_nov.iterrows():
        work_time = str(row[9])
        if ':' in work_time:
            parts = work_time.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            total_hours += hours + minutes/60
    print(f'11월 근무시간: {total_hours}시간')
else:
    total_hours = 0
    print('11월 데이터 없음')

# 12월 시트
df_dec = pd.read_excel('12월 급여포함.xlsx', sheet_name='2025년 12월', header=None)
choi_dec = df_dec[df_dec[1] == '190335410']
print('\n=== 12월 최유진 데이터 ===')
print(f'데이터 건수: {len(choi_dec)}')
total_dec = 0
for idx, row in choi_dec.iterrows():
    work_time = str(row[9])
    if ':' in work_time:
        parts = work_time.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        total_dec += hours + minutes/60
print(f'12월 근무시간: {total_dec}시간')

print(f'\n=== 합계 ===')
print(f'11월 + 12월 = {total_hours + total_dec}시간')
print(f'HTML에 표시된 값: 37.0시간')
