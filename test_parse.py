import os
import sys

# Add workspace to path
sys.path.append(r"g:\Vessel Performance")

from app import parse_excel_noon_reports

file_path = r"g:\Vessel Performance\NOON_REPORT_RANDOMIZED.xlsx"
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
