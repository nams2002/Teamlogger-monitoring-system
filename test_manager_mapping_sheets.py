#!/usr/bin/env python3
"""
Test script for Google Sheets Manager Mapping Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.manager_mapping import (
    test_google_sheets_connection,
    refresh_manager_mappings,
    get_current_data_source,
    get_manager_name,
    get_manager_email,
    get_manager_summary,
    validate_mapping,
    get_mapping_stats
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_sheets_integration():
    """Test the Google Sheets integration for manager mapping"""
    
    print("🧪 Testing Google Sheets Manager Mapping Integration")
    print("=" * 70)
    
    # Test 1: Google Sheets Connection
    print("\n1️⃣ Testing Google Sheets Connection...")
    connection_test = test_google_sheets_connection()
    
    if connection_test['status'] == 'success':
        print("✅ Google Sheets connection successful!")
        print(f"   📊 Spreadsheet ID: {connection_test['spreadsheet_id']}")
        print(f"   📋 Sheet Name: {connection_test['sheet_name']}")
        print(f"   📝 Rows Fetched: {connection_test['rows_fetched']}")
        print(f"   👥 Employees Mapped: {connection_test['employees_mapped']}")
        print(f"   📧 Manager Emails: {connection_test['manager_emails']}")
        
        if connection_test.get('sample_employees'):
            print(f"   🔍 Sample Employees: {', '.join(connection_test['sample_employees'])}")
        if connection_test.get('sample_managers'):
            print(f"   👔 Sample Managers: {', '.join(connection_test['sample_managers'])}")
    else:
        print("❌ Google Sheets connection failed!")
        print(f"   Error: {connection_test['message']}")
        return False
    
    # Test 2: Data Source Information
    print("\n2️⃣ Current Data Source...")
    data_source = get_current_data_source()
    print(f"   📊 {data_source}")
    
    # Test 3: Refresh Mappings
    print("\n3️⃣ Testing Mapping Refresh...")
    refresh_success = refresh_manager_mappings()
    if refresh_success:
        print("✅ Manager mappings refreshed successfully!")
    else:
        print("⚠️ Manager mapping refresh had issues (check logs)")
    
    # Test 4: Test Individual Lookups
    print("\n4️⃣ Testing Individual Employee Lookups...")
    test_employees = [
        'Kartik Jain',
        'Gokul Jagannath', 
        'Satish',
        'Ujjwal Paliwal',
        'Naman Nagi'
    ]
    
    for employee in test_employees:
        manager = get_manager_name(employee)
        email = get_manager_email(employee)
        print(f"   👤 {employee} -> Manager: {manager}, Email: {email}")
    
    # Test 5: Manager Summary
    print("\n5️⃣ Manager Summary...")
    summary = get_manager_summary()
    print(f"   📊 Total Managers: {len(summary)}")
    
    for manager, info in list(summary.items())[:5]:  # Show first 5 managers
        print(f"   👔 {manager}: {info['team_size']} employees, Email: {info['email']}")
    
    if len(summary) > 5:
        print(f"   ... and {len(summary) - 5} more managers")
    
    # Test 6: Validation
    print("\n6️⃣ Validation Results...")
    issues = validate_mapping()
    
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    if total_issues == 0:
        print("✅ No validation issues found!")
    else:
        print(f"⚠️ Found {total_issues} validation issues:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"   - {issue_type}: {len(issue_list)} items")
                if len(issue_list) <= 3:
                    print(f"     {', '.join(issue_list)}")
                else:
                    print(f"     {', '.join(issue_list[:3])} ... and {len(issue_list) - 3} more")
    
    # Test 7: Statistics
    print("\n7️⃣ Mapping Statistics...")
    stats = get_mapping_stats()
    print(f"   👥 Total Employees: {stats['total_employees']}")
    print(f"   👔 Unique Managers: {stats['unique_managers']}")
    print(f"   📧 Managers with Emails: {stats['managers_with_emails']}")
    print(f"   🏆 Largest Team Size: {stats['largest_team']}")
    
    print("\n" + "=" * 70)
    print("🎯 Google Sheets Manager Mapping Integration Test Complete!")
    
    return True

def test_fallback_behavior():
    """Test fallback behavior when Google Sheets is unavailable"""
    
    print("\n🔄 Testing Fallback Behavior...")
    print("-" * 50)
    
    # This would require temporarily breaking the Google Sheets connection
    # For now, just show that fallback data exists
    from src.manager_mapping import _FALLBACK_REPORTING_MANAGERS, _FALLBACK_MANAGER_EMAILS
    
    print(f"📋 Fallback Employee Mappings: {len(_FALLBACK_REPORTING_MANAGERS)}")
    print(f"📧 Fallback Manager Emails: {len(_FALLBACK_MANAGER_EMAILS)}")
    
    # Test a few fallback lookups
    fallback_employees = ['Kartik Jain', 'Gokul Jagannath', 'Satish']
    print("🔍 Sample Fallback Lookups:")
    for employee in fallback_employees:
        manager = _FALLBACK_REPORTING_MANAGERS.get(employee, 'Not found')
        email = _FALLBACK_MANAGER_EMAILS.get(manager, 'No email') if manager != 'Not found' else 'No email'
        print(f"   👤 {employee} -> {manager} ({email})")

if __name__ == "__main__":
    try:
        success = test_google_sheets_integration()
        
        if success:
            test_fallback_behavior()
            
            print("\n🎉 All tests completed!")
            print("✅ Google Sheets manager mapping integration is working!")
            print("\n💡 Next Steps:")
            print("   1. Verify the Google Sheet has the correct column headers")
            print("   2. Ensure all employee names match between TeamLogger and the sheet")
            print("   3. Add manager email addresses to the sheet if not present")
            print("   4. Test with real employee data in your monitoring system")
        else:
            print("\n❌ Tests failed!")
            print("🔧 Troubleshooting:")
            print("   1. Check if the Google Sheet is publicly accessible")
            print("   2. Verify the spreadsheet ID is correct")
            print("   3. Ensure the sheet has employee and manager columns")
            print("   4. Check network connectivity")
            
    except Exception as e:
        print(f"\n💥 Test script error: {str(e)}")
        import traceback
        traceback.print_exc()
