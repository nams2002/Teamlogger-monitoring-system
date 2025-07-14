#!/usr/bin/env python3
"""
Debug Employee Filtering - Check why removed employees still appear
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from src.workflow_manager import WorkflowManager
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_employee_sources():
    """Debug where employees are coming from"""
    print("🔍 DEBUGGING EMPLOYEE FILTERING ISSUE")
    print("="*60)
    
    # Initialize clients
    teamlogger = TeamLoggerClient()
    google_sheets = GoogleSheetsLeaveClient()
    workflow = WorkflowManager()
    
    # Get current week
    work_week_start, work_week_end = workflow._get_monitoring_period()
    print(f"📅 Monitoring Period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")
    
    # 1. Get ALL employees from TeamLogger
    print("\n1️⃣ TEAMLOGGER EMPLOYEES:")
    print("-" * 30)
    all_teamlogger_employees = teamlogger.get_all_employees()
    print(f"Total TeamLogger employees: {len(all_teamlogger_employees)}")
    
    teamlogger_names = [emp.get('name', '') for emp in all_teamlogger_employees]
    for i, name in enumerate(teamlogger_names[:10]):
        print(f"  {i+1:2d}. {name}")
    if len(teamlogger_names) > 10:
        print(f"  ... and {len(teamlogger_names) - 10} more")
    
    # 2. Check current month's Google Sheet
    print(f"\n2️⃣ GOOGLE SHEETS EMPLOYEES (Current Month):")
    print("-" * 40)
    current_month_sheet = datetime.now().strftime("%B %y")
    print(f"Checking sheet: '{current_month_sheet}'")
    
    sheet_data = google_sheets._fetch_sheet_data(current_month_sheet, force_refresh=True)
    if sheet_data:
        print(f"Sheet has {len(sheet_data)} rows")
        google_sheet_names = []
        for i, row in enumerate(sheet_data):
            if row and len(row) > 0 and row[0].strip():
                name = row[0].strip()
                if name and not name.lower().startswith(('name', 'employee', 'sl')):  # Skip headers
                    google_sheet_names.append(name)
        
        print(f"Found {len(google_sheet_names)} employees in Google Sheets:")
        for i, name in enumerate(google_sheet_names[:10]):
            print(f"  {i+1:2d}. {name}")
        if len(google_sheet_names) > 10:
            print(f"  ... and {len(google_sheet_names) - 10} more")
    else:
        print("❌ Could not fetch Google Sheets data")
        google_sheet_names = []
    
    # 3. Compare the lists
    print(f"\n3️⃣ COMPARISON:")
    print("-" * 20)
    
    # Find employees in TeamLogger but NOT in Google Sheets (these should be filtered out)
    teamlogger_set = set(name.lower().strip() for name in teamlogger_names if name)
    google_sheet_set = set(name.lower().strip() for name in google_sheet_names if name)
    
    employees_to_filter = []
    for tl_name in teamlogger_names:
        if not tl_name:
            continue
        tl_name_lower = tl_name.lower().strip()
        
        # Check if this TeamLogger employee exists in Google Sheets
        found_in_sheets = False
        for gs_name in google_sheet_names:
            gs_name_lower = gs_name.lower().strip()
            if (tl_name_lower == gs_name_lower or 
                tl_name_lower in gs_name_lower or 
                gs_name_lower in tl_name_lower):
                found_in_sheets = True
                break
        
        if not found_in_sheets:
            employees_to_filter.append(tl_name)
    
    print(f"🔍 Employees in TeamLogger but NOT in Google Sheets (should be filtered):")
    if employees_to_filter:
        for i, name in enumerate(employees_to_filter):
            print(f"  ❌ {i+1:2d}. {name}")
    else:
        print("  ✅ All TeamLogger employees found in Google Sheets")
    
    # 4. Test the filtering function
    print(f"\n4️⃣ TESTING FILTERING FUNCTION:")
    print("-" * 35)
    
    try:
        filtered_employees = workflow._filter_active_employees(all_teamlogger_employees, work_week_start, work_week_end)
        print(f"Original count: {len(all_teamlogger_employees)}")
        print(f"Filtered count: {len(filtered_employees)}")
        print(f"Removed: {len(all_teamlogger_employees) - len(filtered_employees)}")
        
        filtered_names = [emp.get('name', '') for emp in filtered_employees]
        print(f"\nFiltered employees (first 10):")
        for i, name in enumerate(filtered_names[:10]):
            print(f"  ✅ {i+1:2d}. {name}")
        
        # Check if any of the "should be filtered" employees are still in the filtered list
        still_present = []
        for name in employees_to_filter:
            if name in filtered_names:
                still_present.append(name)
        
        if still_present:
            print(f"\n⚠️  PROBLEM: These employees should be filtered but are still present:")
            for name in still_present:
                print(f"  ❌ {name}")
        else:
            print(f"\n✅ Filtering working correctly - removed employees are filtered out")
            
    except Exception as e:
        print(f"❌ Error testing filtering function: {str(e)}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    debug_employee_sources()
