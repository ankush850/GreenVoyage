import os
import sys

# Add workspace to path dynamically
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import parse_excel_noon_reports

# Use sample excel file inside the repository
file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'PROMBLEM-STATEMENT',
    'NOON REPORT- SAMPLE.xlsx'
)
print(f"Testing parsing on: {file_path}")

try:
    reports = parse_excel_noon_reports(file_path)
    print(f"Success! Parsed {len(reports)} reports.")
    if reports:
        print("First report sample:")
        print(reports[0])
except Exception as e:
    import traceback
    print("Error parsing excel:")
    traceback.print_exc()
