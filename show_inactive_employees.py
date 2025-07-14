#!/usr/bin/env python3
"""
Show Inactive Employees - Display employees who are in TeamLogger but NOT in Google Sheets
These are employees who have left the organization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

def get_inactive_employees():
    """Get list of employees who are in TeamLogger but NOT in Google Sheets"""
    print("🔍 FINDING INACTIVE EMPLOYEES")
    print("="*60)
    print("Employees who are in TeamLogger but NOT in Google Leave Tracker")
    print("(These are employees who have left the organization)")
    print("="*60)
    
    try:
        # Initialize clients
        teamlogger = TeamLoggerClient()
        google_sheets = GoogleSheetsLeaveClient()
        
        # Get all employees from TeamLogger
        print("📊 Getting employees from TeamLogger...")
        all_teamlogger_employees = teamlogger.get_all_employees()
        teamlogger_names = [emp.get('name', '').strip() for emp in all_teamlogger_employees if emp.get('name', '').strip()]
        print(f"   Found {len(teamlogger_names)} employees in TeamLogger")
        
        # Get employees from Google Sheets (current month)
        current_month_sheet = datetime.now().strftime("%B %y")
        print(f"📋 Getting employees from Google Sheets ('{current_month_sheet}')...")
        
        sheet_data = google_sheets._fetch_sheet_data(current_month_sheet, force_refresh=True)
        google_sheet_names = []
        
        if sheet_data:
            for row in sheet_data:
                if row and len(row) > 0 and row[0].strip():
                    name = row[0].strip()
                    # Skip headers
                    if name and not name.lower().startswith(('name', 'employee', 'sl', 'sr')):
                        google_sheet_names.append(name)
            print(f"   Found {len(google_sheet_names)} employees in Google Sheets")
        else:
            print("   ❌ Could not fetch Google Sheets data")
            return
        
        # Find inactive employees (in TeamLogger but NOT in Google Sheets)
        inactive_employees = []
        
        print(f"\n🔍 Comparing lists to find inactive employees...")
        
        for tl_name in teamlogger_names:
            if not tl_name:
                continue
                
            tl_name_lower = tl_name.lower().strip()
            found_in_sheets = False
            
            # Check if this TeamLogger employee exists in Google Sheets
            for gs_name in google_sheet_names:
                gs_name_lower = gs_name.lower().strip()
                
                # Multiple matching strategies
                if (tl_name_lower == gs_name_lower or 
                    tl_name_lower in gs_name_lower or 
                    gs_name_lower in tl_name_lower or
                    # Check if main parts of names match
                    any(part in gs_name_lower for part in tl_name_lower.split() if len(part) > 2)):
                    found_in_sheets = True
                    break
            
            if not found_in_sheets:
                inactive_employees.append(tl_name)
        
        # Display results
        print(f"\n📋 INACTIVE EMPLOYEES REPORT")
        print("="*60)
        print(f"Total TeamLogger employees: {len(teamlogger_names)}")
        print(f"Total Google Sheets employees: {len(google_sheet_names)}")
        print(f"Inactive employees (left organization): {len(inactive_employees)}")
        print("="*60)
        
        if inactive_employees:
            print(f"\n❌ EMPLOYEES WHO HAVE LEFT THE ORGANIZATION:")
            print("-" * 50)
            for i, name in enumerate(inactive_employees, 1):
                print(f"{i:2d}. {name}")
            
            print(f"\n💡 These {len(inactive_employees)} employees are still in TeamLogger")
            print("   but have been removed from the Google Leave Tracker.")
            print("   The system will automatically filter them out from monitoring.")
        else:
            print(f"\n✅ All TeamLogger employees are present in Google Sheets")
            print("   No inactive employees found.")
        
        # Show some active employees for comparison
        print(f"\n✅ SAMPLE ACTIVE EMPLOYEES (first 10):")
        print("-" * 40)
        active_count = 0
        for tl_name in teamlogger_names:
            if tl_name not in inactive_employees:
                active_count += 1
                if active_count <= 10:
                    print(f"{active_count:2d}. {tl_name}")
        
        total_active = len(teamlogger_names) - len(inactive_employees)
        if total_active > 10:
            print(f"    ... and {total_active - 10} more active employees")
        
        print(f"\n📊 SUMMARY:")
        print(f"   🟢 Active employees: {total_active}")
        print(f"   🔴 Inactive employees: {len(inactive_employees)}")
        print(f"   📈 Total in TeamLogger: {len(teamlogger_names)}")
        
        return {
            'total_teamlogger': len(teamlogger_names),
            'total_google_sheets': len(google_sheet_names),
            'inactive_employees': inactive_employees,
            'active_count': total_active
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    result = get_inactive_employees()
    print("\n" + "="*60)
