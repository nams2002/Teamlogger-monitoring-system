#!/usr/bin/env python3
"""
Diagnostic script to check specific employees' work hours and leave data
NO EMAILS WILL BE SENT - This is for investigation only
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
from datetime import datetime, timedelta
from src.workflow_manager import WorkflowManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_employee_details(employee_names):
    """Check specific employees' work hours and leave data"""
    print("🔍 Employee Hours & Leave Diagnostic Tool")
    print("=" * 60)
    print("⚠️  NO EMAILS WILL BE SENT - Investigation Only")
    print("=" * 60)
    
    # Initialize clients
    workflow = WorkflowManager()
    teamlogger = workflow.teamlogger
    
    # Get monitoring period (same as the system uses)
    work_week_start, work_week_end = workflow._get_monitoring_period()
    print(f"\n📅 Monitoring Period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")
    
    # Get all employees
    all_employees = teamlogger.get_all_employees()
    print(f"📊 Total employees in system: {len(all_employees)}")
    
    # Find and check specific employees
    for target_name in employee_names:
        print(f"\n{'='*60}")
        print(f"🔍 CHECKING: {target_name}")
        print(f"{'='*60}")
        
        # Find employee in the list
        found_employee = None
        for emp in all_employees:
            emp_name = emp.get('name', '').strip()
            if target_name.lower() in emp_name.lower() or emp_name.lower() in target_name.lower():
                found_employee = emp
                break
        
        if not found_employee:
            print(f"❌ Employee '{target_name}' not found in TeamLogger")
            # Show similar names
            similar = [emp.get('name') for emp in all_employees if target_name.lower()[:3] in emp.get('name', '').lower()]
            if similar:
                print(f"   Similar names found: {similar[:5]}")
            continue
        
        employee_id = found_employee.get('id')
        employee_email = found_employee.get('email')
        actual_name = found_employee.get('name')
        
        print(f"✅ Found: {actual_name}")
        print(f"   ID: {employee_id}")
        print(f"   Email: {employee_email}")
        
        # Check if excluded
        is_excluded = workflow._is_employee_excluded(actual_name)
        print(f"   Excluded from alerts: {is_excluded}")
        
        if is_excluded:
            print(f"   ⚠️  This employee is EXCLUDED from monitoring alerts")
            continue
        
        # Get work hours
        print(f"\n📊 WORK HOURS ANALYSIS:")
        weekly_data = teamlogger.get_weekly_summary(employee_id, work_week_start, work_week_end)
        
        if not weekly_data:
            print(f"   ❌ No work data found for {actual_name}")
            continue
        
        actual_hours = weekly_data['total_hours']
        print(f"   Total hours worked: {actual_hours:.2f}")
        
        # Get leave days
        print(f"\n🏖️  LEAVE ANALYSIS:")
        try:
            leave_days = workflow._get_working_day_leaves_count_realtime(
                actual_name, work_week_start, work_week_end
            )
            print(f"   Leave days: {leave_days}")
        except Exception as e:
            print(f"   ❌ Error getting leave data: {str(e)}")
            leave_days = 0
        
        # Calculate requirements
        print(f"\n📋 REQUIREMENTS CALCULATION:")
        required_hours = workflow._calculate_required_hours(leave_days)
        acceptable_hours = max(0, required_hours - 3.0)  # 3-hour buffer
        
        print(f"   Required hours: {required_hours:.1f}")
        print(f"   Acceptable hours (with 3h buffer): {acceptable_hours:.1f}")
        print(f"   Actual hours: {actual_hours:.1f}")
        
        # Decision logic
        print(f"\n🎯 ALERT DECISION:")
        if leave_days >= 5:
            print(f"   ✅ On full leave ({leave_days} days) - NO ALERT NEEDED")
        elif actual_hours >= acceptable_hours:
            print(f"   ✅ Hours sufficient ({actual_hours:.1f}h >= {acceptable_hours:.1f}h) - NO ALERT NEEDED")
        else:
            shortfall = required_hours - actual_hours
            print(f"   🚨 ALERT WOULD BE SENT!")
            print(f"   Shortfall: {shortfall:.2f} hours ({int(shortfall * 60)} minutes)")
            print(f"   Reason: {actual_hours:.1f}h < {acceptable_hours:.1f}h (acceptable)")
        
        # Show detailed daily breakdown if available
        if hasattr(weekly_data, 'daily_breakdown'):
            print(f"\n📅 DAILY BREAKDOWN:")
            for day, hours in weekly_data.get('daily_breakdown', {}).items():
                print(f"   {day}: {hours:.2f}h")

def main():
    """Main function"""
    # Employees to check
    employees_to_check = [
        "Abhijeet Sonaje",
        "Abhijeet",
        "Debi Prasad Mishra", 
        "Debi",
        "Debi Prasad"
    ]
    
    try:
        check_employee_details(employees_to_check)
        
        print(f"\n{'='*60}")
        print("✅ Investigation completed!")
        print("📧 NO EMAILS WERE SENT - This was diagnostic only")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Error during investigation: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
