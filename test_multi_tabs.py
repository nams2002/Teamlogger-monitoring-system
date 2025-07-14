#!/usr/bin/env python3
"""
Test script to verify Google Sheets multi-tab access
"""

from src.googlesheets_Client import GoogleSheetsLeaveClient
from datetime import datetime, timedelta
import json

def test_multi_tab_access():
    print("🔍 Testing Google Sheets Multi-Tab Access")
    print("=" * 50)
    
    sheets = GoogleSheetsLeaveClient()
    
    # Test 1: Basic connection validation
    print("\n1️⃣ Testing basic connection...")
    validation = sheets.validate_google_sheets_connection()
    print(f"Status: {validation['status']}")
    print(f"Message: {validation['message']}")
    if validation['status'] == 'success':
        print(f"✅ Connected to spreadsheet: {validation['spreadsheet_id']}")
        print(f"📊 Current sheet ({validation['test_sheet']}): {validation['rows_found']} rows")
        print(f"👥 Sample employees: {validation['sample_employees']}")
    
    # Test 2: Access multiple tabs directly
    print("\n2️⃣ Testing direct access to multiple tabs...")
    test_sheets = ['July 25', 'June 25', 'May 25', 'Apr 25', 'Mar 25', 'Feb 25']
    
    accessible_tabs = []
    for sheet_name in test_sheets:
        try:
            data = sheets._fetch_sheet_data(sheet_name)
            if data and len(data) > 1:
                accessible_tabs.append(sheet_name)
                print(f"✅ {sheet_name}: {len(data)} rows")
                
                # Show first few employee names
                employees = []
                for row in data[1:4]:  # Skip header, get first 3 employees
                    if row and len(row) > 0 and row[0].strip():
                        employees.append(row[0].strip())
                if employees:
                    print(f"   👥 Employees: {', '.join(employees)}")
            else:
                print(f"❌ {sheet_name}: No data found")
        except Exception as e:
            print(f"❌ {sheet_name}: Error - {str(e)}")
    
    print(f"\n📋 Summary: {len(accessible_tabs)} tabs accessible out of {len(test_sheets)} tested")
    print(f"✅ Accessible tabs: {accessible_tabs}")
    
    # Test 3: Multi-month leave data retrieval
    print("\n3️⃣ Testing multi-month leave data retrieval...")
    
    # Use an employee we know exists
    test_employee = "Aakash Kumar"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=120)  # Go back 4 months
    
    print(f"Employee: {test_employee}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        leaves = sheets.get_employee_leaves(test_employee, start_date, end_date)
        print(f"✅ Found {len(leaves)} leave records")
        
        if leaves:
            # Group by month to show which tabs were accessed
            months_accessed = set()
            for leave in leaves:
                month_key = leave['start_date'].strftime('%B %y')
                months_accessed.add(month_key)
            
            print(f"📅 Months/tabs accessed: {sorted(months_accessed)}")
            
            # Show some sample leave records
            print("📋 Sample leave records:")
            for i, leave in enumerate(leaves[:3]):  # Show first 3
                date_str = leave['start_date'].strftime('%Y-%m-%d')
                leave_type = leave['leave_type']
                days = leave['days_count']
                print(f"   {i+1}. {date_str} - {leave_type} ({days} days)")
        else:
            print("ℹ️  No leave records found (employee might have no leaves in this period)")
            
    except Exception as e:
        print(f"❌ Error retrieving leave data: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check if system can handle date ranges spanning multiple months
    print("\n4️⃣ Testing cross-month date range handling...")
    
    # Test a specific date range that spans multiple months
    test_start = datetime(2025, 3, 1)  # March 1st
    test_end = datetime(2025, 7, 31)   # July 31st
    
    print(f"Testing date range: {test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
    
    try:
        leaves = sheets.get_employee_leaves(test_employee, test_start, test_end)
        print(f"✅ Successfully processed cross-month query: {len(leaves)} leaves found")
        
        if leaves:
            months_in_results = set()
            for leave in leaves:
                months_in_results.add(leave['start_date'].strftime('%B %y'))
            print(f"📅 Months found in results: {sorted(months_in_results)}")
        
    except Exception as e:
        print(f"❌ Error with cross-month query: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSION:")
    if len(accessible_tabs) >= 3:
        print("✅ Multi-tab access is working correctly!")
        print("✅ Your system can access different months/tabs in the Google Sheet")
        print("✅ The leave tracking system should work across all available months")
    else:
        print("⚠️  Limited tab access detected")
        print("🔧 You may need to check sheet permissions or tab names")
    
    return accessible_tabs

if __name__ == "__main__":
    test_multi_tab_access()
