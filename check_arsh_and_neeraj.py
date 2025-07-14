#!/usr/bin/env python3
"""
Check Arsh and Neeraj Deshpande Status
1. Check if Arsh is in TeamLogger and/or Google Sheets
2. Check Neeraj Deshpande's manager email status
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from src.manager_mapping import get_manager_name, get_manager_email, refresh_manager_mapping
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

def check_arsh_status():
    """Check if Arsh is in TeamLogger and Google Sheets"""
    print("🔍 CHECKING ARSH STATUS")
    print("="*40)
    
    try:
        # Initialize clients
        teamlogger = TeamLoggerClient()
        google_sheets = GoogleSheetsLeaveClient()
        
        # Get all employees from TeamLogger
        all_teamlogger_employees = teamlogger.get_all_employees()
        teamlogger_names = [emp.get('name', '').strip() for emp in all_teamlogger_employees if emp.get('name', '').strip()]
        
        # Find Arsh in TeamLogger
        arsh_in_teamlogger = []
        for name in teamlogger_names:
            if 'arsh' in name.lower():
                arsh_in_teamlogger.append(name)
        
        print(f"📊 TeamLogger Results:")
        if arsh_in_teamlogger:
            for name in arsh_in_teamlogger:
                print(f"   ✅ Found: {name}")
        else:
            print(f"   ❌ No 'Arsh' found in TeamLogger")
        
        # Get employees from Google Sheets
        current_month_sheet = datetime.now().strftime("%B %y")
        sheet_data = google_sheets._fetch_sheet_data(current_month_sheet, force_refresh=True)
        
        arsh_in_google_sheets = []
        if sheet_data:
            for row in sheet_data:
                if row and len(row) > 0 and row[0].strip():
                    name = row[0].strip()
                    if 'arsh' in name.lower():
                        arsh_in_google_sheets.append(name)
        
        print(f"\n📋 Google Sheets Results:")
        if arsh_in_google_sheets:
            for name in arsh_in_google_sheets:
                print(f"   ✅ Found: {name}")
        else:
            print(f"   ❌ No 'Arsh' found in Google Sheets")
        
        # Summary for Arsh
        print(f"\n📊 ARSH SUMMARY:")
        print(f"   TeamLogger: {len(arsh_in_teamlogger)} matches")
        print(f"   Google Sheets: {len(arsh_in_google_sheets)} matches")
        
        if arsh_in_teamlogger and not arsh_in_google_sheets:
            print(f"   🔴 Status: INACTIVE (left organization)")
        elif arsh_in_teamlogger and arsh_in_google_sheets:
            print(f"   🟢 Status: ACTIVE")
        elif not arsh_in_teamlogger:
            print(f"   ⚪ Status: NOT IN TEAMLOGGER")
        
        return {
            'teamlogger': arsh_in_teamlogger,
            'google_sheets': arsh_in_google_sheets
        }
        
    except Exception as e:
        print(f"❌ Error checking Arsh: {str(e)}")
        return None

def check_neeraj_manager_status():
    """Check Neeraj Deshpande's manager email status"""
    print("\n🔍 CHECKING NEERAJ DESHPANDE MANAGER STATUS")
    print("="*50)
    
    try:
        # Force refresh manager mapping
        print("🔄 Refreshing manager mapping from Google Sheets...")
        mapping = refresh_manager_mapping()
        print(f"   Loaded {len(mapping)} manager mappings")
        
        # Check if Neeraj is in the manager mapping
        neeraj_variations = [
            'Neeraj Deshpande',
            'neeraj deshpande',
            'Neeraj',
            'neeraj'
        ]
        
        print(f"\n📋 Checking Neeraj in Manager Mapping:")
        neeraj_found_as_employee = False
        neeraj_found_as_manager = False
        
        # Check if Neeraj is listed as an employee
        for employee, manager in mapping.items():
            for variation in neeraj_variations:
                if variation.lower() in employee.lower():
                    print(f"   👤 Found as Employee: {employee} -> Manager: {manager}")
                    neeraj_found_as_employee = True
                    
                    # Try to get manager email
                    manager_email = get_manager_email(employee, force_refresh=True)
                    if manager_email:
                        print(f"      📧 Manager Email: {manager_email}")
                    else:
                        print(f"      ❌ No manager email found")
        
        # Check if Neeraj is listed as a manager for others
        employees_under_neeraj = []
        for employee, manager in mapping.items():
            for variation in neeraj_variations:
                if variation.lower() in manager.lower():
                    employees_under_neeraj.append(employee)
                    neeraj_found_as_manager = True
        
        if employees_under_neeraj:
            print(f"\n👥 Neeraj found as Manager for {len(employees_under_neeraj)} employees:")
            for i, emp in enumerate(employees_under_neeraj[:10], 1):  # Show first 10
                print(f"   {i:2d}. {emp}")
            if len(employees_under_neeraj) > 10:
                print(f"       ... and {len(employees_under_neeraj) - 10} more")
            
            # Try to get Neeraj's email as a manager
            neeraj_email = get_manager_email('Neeraj Deshpande', force_refresh=True)
            if neeraj_email:
                print(f"   📧 Neeraj's Manager Email: {neeraj_email}")
            else:
                print(f"   ❌ No email found for Neeraj as manager")
        
        # Check manager email mapping directly
        print(f"\n📧 Checking Manager Email Mapping:")
        from src.manager_mapping import MANAGER_EMAILS
        
        neeraj_email_found = False
        for manager_name, email in MANAGER_EMAILS.items():
            for variation in neeraj_variations:
                if variation.lower() in manager_name.lower():
                    print(f"   ✅ Found: {manager_name} -> {email}")
                    neeraj_email_found = True
        
        if not neeraj_email_found:
            print(f"   ❌ Neeraj not found in manager email mapping")
        
        # Summary for Neeraj
        print(f"\n📊 NEERAJ SUMMARY:")
        print(f"   As Employee: {'✅ Found' if neeraj_found_as_employee else '❌ Not found'}")
        print(f"   As Manager: {'✅ Found' if neeraj_found_as_manager else '❌ Not found'}")
        print(f"   Email Mapping: {'✅ Found' if neeraj_email_found else '❌ Not found'}")
        
        if not neeraj_found_as_employee and not neeraj_found_as_manager:
            print(f"   🔴 Status: REMOVED from manager mapping (left organization)")
        elif neeraj_found_as_manager:
            print(f"   🟢 Status: ACTIVE as manager")
        else:
            print(f"   🟡 Status: Found as employee only")
        
        return {
            'found_as_employee': neeraj_found_as_employee,
            'found_as_manager': neeraj_found_as_manager,
            'email_mapping_found': neeraj_email_found,
            'employees_under_neeraj': employees_under_neeraj
        }
        
    except Exception as e:
        print(f"❌ Error checking Neeraj: {str(e)}")
        return None

def main():
    """Main function to check both Arsh and Neeraj"""
    print("🔍 CHECKING ARSH AND NEERAJ STATUS")
    print("="*60)
    
    # Check Arsh
    arsh_result = check_arsh_status()
    
    # Check Neeraj
    neeraj_result = check_neeraj_manager_status()
    
    print(f"\n" + "="*60)
    print("📋 FINAL SUMMARY")
    print("="*60)
    
    if arsh_result:
        if arsh_result['teamlogger'] and not arsh_result['google_sheets']:
            print("🔴 ARSH: Left organization (in TeamLogger but not in Google Sheets)")
        elif arsh_result['teamlogger'] and arsh_result['google_sheets']:
            print("🟢 ARSH: Active employee")
        else:
            print("⚪ ARSH: Not found in TeamLogger")
    
    if neeraj_result:
        if not neeraj_result['found_as_employee'] and not neeraj_result['found_as_manager']:
            print("🔴 NEERAJ: Removed from manager mapping (left organization)")
            print("   📧 His manager emails should no longer be used")
        elif neeraj_result['found_as_manager']:
            print("🟢 NEERAJ: Still active as manager")
            print(f"   👥 Managing {len(neeraj_result['employees_under_neeraj'])} employees")
        
    print("="*60)

if __name__ == "__main__":
    main()
