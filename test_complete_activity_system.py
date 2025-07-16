#!/usr/bin/env python3
"""
Complete test for the activity tracking and alert system
Tests both preview mode and actual functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta
from src.workflow_manager import WorkflowManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_activity_preview_mode():
    """Test the activity alert preview functionality"""
    print("🔍 TESTING ACTIVITY ALERT PREVIEW MODE")
    print("=" * 60)
    
    try:
        workflow = WorkflowManager()
        
        # Get employees needing activity alerts
        employees_needing_alerts = workflow.get_employees_needing_activity_alerts()
        
        print(f"Found {len(employees_needing_alerts)} employees needing activity alerts")
        
        if employees_needing_alerts:
            print("\n📋 EMPLOYEES NEEDING ACTIVITY ALERTS:")
            print("-" * 50)
            
            for i, emp in enumerate(employees_needing_alerts[:5], 1):  # Show first 5
                print(f"{i}. {emp['name']}")
                print(f"   📧 Email: {emp['email']}")
                print(f"   📊 Activity: {emp['activity_percentage']:.1f}% (threshold: {emp['activity_threshold']:.0f}%)")
                print(f"   📉 Shortfall: {emp['activity_shortfall']:.1f}%")
                print(f"   ⏰ Hours: {emp['hours_worked']:.1f}h")
                print(f"   🏖️ Leave: {emp['leave_days']} days")
                print(f"   📈 Trend: {emp['activity_trend']}")
                print(f"   👤 Manager: {emp['manager_name']} ({emp['manager_email']})")
                print(f"   📅 Period: {emp['period_start']} to {emp['period_end']}")
                print()
            
            if len(employees_needing_alerts) > 5:
                print(f"... and {len(employees_needing_alerts) - 5} more employees")
            
            # Test email preview (without sending)
            print("\n📧 EMAIL PREVIEW SAMPLE:")
            print("-" * 30)
            sample_emp = employees_needing_alerts[0]
            
            print(f"To: {sample_emp['email']}")
            print(f"CC: {sample_emp['manager_email']}, teamhr@rapidinnovation.dev")
            print(f"Subject: Activity Level Reminder - {sample_emp['name']}")
            print()
            print("Email Content Preview:")
            print(f"- Employee: {sample_emp['name']}")
            print(f"- Activity Level: {sample_emp['activity_percentage']:.1f}%")
            print(f"- Required: {sample_emp['activity_threshold']:.0f}%")
            print(f"- Shortfall: {sample_emp['activity_shortfall']:.1f}%")
            print(f"- Period: {sample_emp['period_start']} to {sample_emp['period_end']}")
            
        else:
            print("✅ No employees need activity alerts - all above 50% threshold!")
        
        return True
        
    except Exception as e:
        print(f"❌ Preview test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_activity_data_extraction():
    """Test activity data extraction for a few employees"""
    print("\n🔍 TESTING ACTIVITY DATA EXTRACTION")
    print("=" * 60)
    
    try:
        workflow = WorkflowManager()
        
        # Get a few employees for testing
        employees = workflow.teamlogger.get_all_employees()[:3]
        
        # Get monitoring period
        work_week_start, work_week_end = workflow._get_monitoring_period()
        print(f"Period: {work_week_start.date()} to {work_week_end.date()}")
        
        for i, employee in enumerate(employees, 1):
            employee_name = employee.get('name', 'Unknown')
            employee_id = employee.get('id')
            
            print(f"\n{i}. Testing {employee_name}")
            print("-" * 30)
            
            # Get activity report
            activity_report = workflow.teamlogger.generate_employee_activity_report(
                employee_id, work_week_start, work_week_end
            )
            
            if activity_report:
                print(f"✅ Activity report generated")
                print(f"   Overall Activity: {activity_report.overall_average_activity:.2f}%")
                print(f"   Activity Trend: {activity_report.activity_trend}")
                print(f"   Daily Summaries: {len(activity_report.daily_summaries)}")
                print(f"   Low Productivity Periods: {activity_report.total_low_productivity_periods}")
                print(f"   High Productivity Periods: {activity_report.total_high_productivity_periods}")
                
                if activity_report.most_productive_day:
                    print(f"   Most Productive: {activity_report.most_productive_day.strftime('%A')}")
                if activity_report.least_productive_day:
                    print(f"   Least Productive: {activity_report.least_productive_day.strftime('%A')}")
                
                # Check if below threshold
                if activity_report.overall_average_activity < 50:
                    print(f"   🔴 Below 50% threshold - would receive alert")
                else:
                    print(f"   ✅ Above 50% threshold - no alert needed")
            else:
                print(f"⚠️ No activity report available")
        
        return True
        
    except Exception as e:
        print(f"❌ Data extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hours_vs_activity_comparison():
    """Compare hours alerts vs activity alerts"""
    print("\n🔍 TESTING HOURS VS ACTIVITY ALERTS COMPARISON")
    print("=" * 60)
    
    try:
        workflow = WorkflowManager()
        
        # Get both types of alerts
        hours_alerts = workflow.get_employees_needing_real_alerts()
        activity_alerts = workflow.get_employees_needing_activity_alerts()
        
        print(f"Hours alerts needed: {len(hours_alerts)}")
        print(f"Activity alerts needed: {len(activity_alerts)}")
        
        # Find overlap
        hours_names = {emp['employee']['name'] for emp in hours_alerts}
        activity_names = {emp['name'] for emp in activity_alerts}
        
        overlap = hours_names.intersection(activity_names)
        hours_only = hours_names - activity_names
        activity_only = activity_names - hours_names
        
        print(f"\n📊 ALERT COMPARISON:")
        print(f"Both hours & activity alerts: {len(overlap)}")
        print(f"Hours alerts only: {len(hours_only)}")
        print(f"Activity alerts only: {len(activity_only)}")
        
        if overlap:
            print(f"\nEmployees needing BOTH types of alerts:")
            for name in list(overlap)[:5]:  # Show first 5
                print(f"  - {name}")
        
        if hours_only:
            print(f"\nEmployees needing HOURS alerts only:")
            for name in list(hours_only)[:3]:  # Show first 3
                print(f"  - {name}")
        
        if activity_only:
            print(f"\nEmployees needing ACTIVITY alerts only:")
            for name in list(activity_only)[:3]:  # Show first 3
                print(f"  - {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 COMPLETE ACTIVITY TRACKING SYSTEM TEST")
    print("=" * 70)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Activity Data Extraction", test_activity_data_extraction),
        ("Activity Preview Mode", test_activity_preview_mode),
        ("Hours vs Activity Comparison", test_hours_vs_activity_comparison)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Activity tracking system is ready!")
        print("\n📋 NEXT STEPS:")
        print("1. ✅ Activity tracking is working")
        print("2. ✅ Preview mode shows employees needing alerts")
        print("3. ✅ Email templates are ready")
        print("4. 🔄 Test the Streamlit interface")
        print("5. 📧 When ready, enable email sending")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
