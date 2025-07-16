#!/usr/bin/env python3
"""
Debug script to examine TeamLogger API data structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime, timedelta
from src.teamlogger_client import TeamLoggerClient

def debug_api_data():
    """Debug the actual data structure from TeamLogger API"""
    print("🔍 DEBUGGING TEAMLOGGER API DATA STRUCTURE")
    print("=" * 60)
    
    try:
        client = TeamLoggerClient()
        
        # Get employees
        employees = client.get_all_employees()
        if not employees:
            print("❌ No employees found")
            return
        
        print(f"Found {len(employees)} employees")
        
        # Test with first employee
        test_employee = employees[0]
        employee_id = test_employee['id']
        employee_name = test_employee.get('name', 'Unknown')
        
        print(f"\nTesting with employee: {employee_name} (ID: {employee_id})")
        
        # Get current week data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        
        # Get raw report data
        report = client.get_employee_summary_report(start_date, end_date)
        
        if not report:
            print("❌ No report data")
            return
        
        # Find our test employee in the report
        employee_data = None
        for item in report:
            if str(item.get('id', '')) == str(employee_id):
                employee_data = item
                break
        
        if not employee_data:
            print(f"❌ Employee {employee_id} not found in report")
            return
        
        print(f"\n📊 RAW DATA STRUCTURE FOR {employee_name}:")
        print("=" * 60)
        
        # Print all available fields
        print("Available fields:")
        for key in sorted(employee_data.keys()):
            value = employee_data[key]
            if isinstance(value, dict):
                print(f"  {key}: dict with {len(value)} keys")
                if len(value) <= 5:  # Show small dicts
                    for subkey, subvalue in value.items():
                        print(f"    {subkey}: {type(subvalue).__name__} = {subvalue}")
            elif isinstance(value, list):
                print(f"  {key}: list with {len(value)} items")
                if len(value) <= 3:  # Show small lists
                    for i, item in enumerate(value):
                        print(f"    [{i}]: {type(item).__name__} = {item}")
            else:
                print(f"  {key}: {type(value).__name__} = {value}")
        
        # Look specifically for activity-related fields
        print(f"\n🔍 ACTIVITY-RELATED FIELDS:")
        print("=" * 40)
        
        activity_fields = ['actChart', 'activity', 'screenshots', 'totChart', 'timeChart', 'productivity']
        for field in activity_fields:
            if field in employee_data:
                value = employee_data[field]
                print(f"✅ {field}: {type(value).__name__}")
                if isinstance(value, dict):
                    print(f"   Keys: {list(value.keys())[:10]}...")  # Show first 10 keys
                    # Show a sample entry
                    if value:
                        sample_key = list(value.keys())[0]
                        sample_value = value[sample_key]
                        print(f"   Sample: {sample_key} -> {sample_value}")
                elif isinstance(value, list):
                    print(f"   Length: {len(value)}")
                    if value:
                        print(f"   Sample: {value[0]}")
                else:
                    print(f"   Value: {value}")
            else:
                print(f"❌ {field}: Not found")
        
        # Check for screenshot-related data
        print(f"\n📸 SCREENSHOT-RELATED FIELDS:")
        print("=" * 40)
        
        screenshot_fields = ['screenshots', 'images', 'captures', 'screen']
        for field in screenshot_fields:
            if field in employee_data:
                value = employee_data[field]
                print(f"✅ {field}: {type(value).__name__} = {value}")
            else:
                print(f"❌ {field}: Not found")
        
        # Look for time-based data that might contain activity info
        print(f"\n⏰ TIME-BASED FIELDS:")
        print("=" * 40)
        
        time_fields = ['totChart', 'timeChart', 'hourlyData', 'dailyData', 'periods']
        for field in time_fields:
            if field in employee_data:
                value = employee_data[field]
                print(f"✅ {field}: {type(value).__name__}")
                if isinstance(value, dict) and value:
                    # Show structure of time-based data
                    sample_key = list(value.keys())[0]
                    sample_value = value[sample_key]
                    print(f"   Sample key: {sample_key}")
                    print(f"   Sample value: {sample_value} ({type(sample_value).__name__})")
                    
                    # If the sample value is a dict, show its structure
                    if isinstance(sample_value, dict):
                        print(f"   Sample value keys: {list(sample_value.keys())}")
            else:
                print(f"❌ {field}: Not found")
        
        # Save raw data to file for detailed inspection
        output_file = f"debug_employee_data_{employee_id}.json"
        with open(output_file, 'w') as f:
            json.dump(employee_data, f, indent=2, default=str)
        
        print(f"\n💾 Raw data saved to: {output_file}")
        print("You can examine this file to understand the complete data structure.")
        
        # Try to find any field that might contain activity percentages
        print(f"\n🔍 SEARCHING FOR ACTIVITY PERCENTAGE DATA:")
        print("=" * 50)
        
        def search_for_percentages(data, path=""):
            """Recursively search for data that might be activity percentages"""
            findings = []
            
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Check if this might be activity data
                    if isinstance(value, (int, float)):
                        if 0 <= value <= 100:
                            findings.append(f"{current_path}: {value} (possible percentage)")
                        elif 0 <= value <= 1:
                            findings.append(f"{current_path}: {value} (possible decimal percentage)")
                    
                    # Recurse into nested structures
                    findings.extend(search_for_percentages(value, current_path))
            
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    findings.extend(search_for_percentages(item, current_path))
            
            return findings
        
        percentage_findings = search_for_percentages(employee_data)
        
        if percentage_findings:
            print("Possible activity percentage fields found:")
            for finding in percentage_findings[:20]:  # Show first 20 findings
                print(f"  {finding}")
            if len(percentage_findings) > 20:
                print(f"  ... and {len(percentage_findings) - 20} more")
        else:
            print("No obvious activity percentage fields found")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_api_data()
