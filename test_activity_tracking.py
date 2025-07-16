#!/usr/bin/env python3
"""
Test Script for Activity Tracking Functionality

This script tests the activity tracking features to ensure they work correctly
with the TeamLogger API and can extract activity percentage data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta
import json
from src.teamlogger_client import TeamLoggerClient
from src.activity_analysis import ActivityAnalyzer
from src.activity_tracker import ActivityTracker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_teamlogger_connection():
    """Test basic TeamLogger connection"""
    print("🔍 TESTING TEAMLOGGER CONNECTION")
    print("=" * 50)
    
    try:
        client = TeamLoggerClient()
        
        # Test API connection
        status = client.get_api_status()
        print(f"Connection Status: {'✅ Connected' if status['connected'] else '❌ Failed'}")
        print(f"Response Time: {status.get('response_time_seconds', 'N/A')} seconds")
        print(f"Employee Count: {status.get('employee_count', 'N/A')}")
        print(f"Base URL: {status.get('base_url', 'N/A')}")
        
        return status['connected']
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_activity_data_extraction():
    """Test activity data extraction from TeamLogger"""
    print("\n🔍 TESTING ACTIVITY DATA EXTRACTION")
    print("=" * 50)
    
    try:
        client = TeamLoggerClient()
        
        # Get employees
        employees = client.get_all_employees()
        if not employees:
            print("❌ No employees found")
            return False
        
        print(f"Found {len(employees)} employees")
        
        # Test with first employee
        test_employee = employees[0]
        employee_id = test_employee['id']
        employee_name = test_employee['name']
        
        print(f"Testing with employee: {employee_name} (ID: {employee_id})")
        
        # Get current week data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        
        # Test activity data extraction
        activity_data = client.get_employee_activity_data(employee_id, start_date, end_date)
        
        if activity_data:
            print("✅ Activity data extracted successfully")
            print(f"Employee: {activity_data.get('employee_name', 'Unknown')}")
            print(f"Total Hours: {activity_data.get('total_hours', 0)}")
            print(f"Idle Hours: {activity_data.get('idle_hours', 0)}")
            
            # Check if actChart data exists
            act_chart = activity_data.get('act_chart', {})
            if act_chart:
                print(f"✅ Activity chart data found with {len(act_chart)} entries")
                
                # Show sample of actChart data
                sample_keys = list(act_chart.keys())[:3]
                for key in sample_keys:
                    print(f"  Sample entry {key}: {act_chart[key]}")
            else:
                print("⚠️ No activity chart data found")
            
            return True
        else:
            print("❌ No activity data found")
            return False
            
    except Exception as e:
        print(f"❌ Activity data extraction failed: {e}")
        return False

def test_activity_periods_extraction():
    """Test activity periods extraction"""
    print("\n🔍 TESTING ACTIVITY PERIODS EXTRACTION")
    print("=" * 50)
    
    try:
        client = TeamLoggerClient()
        
        # Get employees
        employees = client.get_all_employees()
        if not employees:
            print("❌ No employees found")
            return False
        
        # Test with first employee
        test_employee = employees[0]
        employee_id = test_employee['id']
        employee_name = test_employee['name']
        
        print(f"Testing with employee: {employee_name}")
        
        # Get current week data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Extract activity periods
        periods = client.get_employee_activity_periods(employee_id, start_date, end_date)
        
        if periods:
            print(f"✅ Extracted {len(periods)} activity periods")
            
            # Show sample periods
            for i, period in enumerate(periods[:3]):
                print(f"  Period {i+1}:")
                print(f"    Timestamp: {period.timestamp}")
                print(f"    Activity %: {period.activity_percentage:.2f}%")
                print(f"    Active Time: {period.active_time_seconds}s")
                print(f"    Total Time: {period.total_time_seconds}s")
            
            # Calculate some basic stats
            if periods:
                avg_activity = sum(p.activity_percentage for p in periods) / len(periods)
                max_activity = max(p.activity_percentage for p in periods)
                min_activity = min(p.activity_percentage for p in periods)
                
                print(f"\n📊 Activity Statistics:")
                print(f"  Average Activity: {avg_activity:.2f}%")
                print(f"  Max Activity: {max_activity:.2f}%")
                print(f"  Min Activity: {min_activity:.2f}%")
                
                # Count productivity levels
                low_periods = sum(1 for p in periods if p.activity_percentage < 30)
                high_periods = sum(1 for p in periods if p.activity_percentage > 70)
                
                print(f"  Low Productivity Periods (<30%): {low_periods}")
                print(f"  High Productivity Periods (>70%): {high_periods}")
            
            return True
        else:
            print("⚠️ No activity periods found")
            return False
            
    except Exception as e:
        print(f"❌ Activity periods extraction failed: {e}")
        return False

def test_weekly_activity_report():
    """Test weekly activity report generation"""
    print("\n🔍 TESTING WEEKLY ACTIVITY REPORT")
    print("=" * 50)
    
    try:
        client = TeamLoggerClient()
        
        # Get employees
        employees = client.get_all_employees()
        if not employees:
            print("❌ No employees found")
            return False
        
        # Test with first employee
        test_employee = employees[0]
        employee_id = test_employee['id']
        employee_name = test_employee['name']
        
        print(f"Generating report for: {employee_name}")
        
        # Get current week data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Generate activity report
        report = client.generate_employee_activity_report(employee_id, start_date, end_date)
        
        if report:
            print("✅ Weekly activity report generated successfully")
            print(f"Employee: {report.employee_name}")
            print(f"Period: {report.week_start.date()} to {report.week_end.date()}")
            print(f"Overall Average Activity: {report.overall_average_activity:.2f}%")
            print(f"Activity Trend: {report.activity_trend}")
            print(f"Low Productivity Periods: {report.total_low_productivity_periods}")
            print(f"High Productivity Periods: {report.total_high_productivity_periods}")
            
            if report.most_productive_day:
                print(f"Most Productive Day: {report.most_productive_day.strftime('%A, %Y-%m-%d')}")
            if report.least_productive_day:
                print(f"Least Productive Day: {report.least_productive_day.strftime('%A, %Y-%m-%d')}")
            
            # Show daily summaries
            print(f"\n📅 Daily Summaries ({len(report.daily_summaries)} days):")
            for daily in report.daily_summaries:
                print(f"  {daily.date.strftime('%A, %Y-%m-%d')}:")
                print(f"    Average Activity: {daily.average_activity:.2f}%")
                print(f"    Productivity Score: {daily.productivity_score}")
                print(f"    Active Hours: {daily.total_active_hours:.2f}h")
                print(f"    Periods: {daily.total_periods}")
            
            return True
        else:
            print("⚠️ No activity report generated")
            return False
            
    except Exception as e:
        print(f"❌ Weekly activity report failed: {e}")
        return False

def test_team_activity_analysis():
    """Test team-wide activity analysis"""
    print("\n🔍 TESTING TEAM ACTIVITY ANALYSIS")
    print("=" * 50)
    
    try:
        client = TeamLoggerClient()
        analyzer = ActivityAnalyzer(client)
        
        # Get current week data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"Analyzing team activity for period: {start_date.date()} to {end_date.date()}")
        
        # Analyze team activity (limit to first 3 employees for testing)
        employees = client.get_all_employees()[:3]
        print(f"Testing with {len(employees)} employees")
        
        team_analysis = analyzer.analyze_team_activity(start_date, end_date)
        
        if team_analysis and team_analysis.get('team_statistics'):
            print("✅ Team activity analysis completed")
            
            stats = team_analysis['team_statistics']
            print(f"Team Average Activity: {stats.get('team_average_activity', 0):.2f}%")
            print(f"High Performers: {stats.get('high_performers', 0)}")
            print(f"Medium Performers: {stats.get('medium_performers', 0)}")
            print(f"Low Performers: {stats.get('low_performers', 0)}")
            print(f"Improving Employees: {stats.get('improving_employees', 0)}")
            print(f"Declining Employees: {stats.get('declining_employees', 0)}")
            
            # Generate insights
            insights = analyzer.generate_activity_insights(team_analysis)
            print(f"\n💡 Activity Insights:")
            for insight in insights:
                print(f"  {insight}")
            
            return True
        else:
            print("⚠️ Team analysis completed but no statistics available")
            return False
            
    except Exception as e:
        print(f"❌ Team activity analysis failed: {e}")
        return False

def main():
    """Run all activity tracking tests"""
    print("🚀 ACTIVITY TRACKING TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("TeamLogger Connection", test_teamlogger_connection),
        ("Activity Data Extraction", test_activity_data_extraction),
        ("Activity Periods Extraction", test_activity_periods_extraction),
        ("Weekly Activity Report", test_weekly_activity_report),
        ("Team Activity Analysis", test_team_activity_analysis)
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
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Activity tracking is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
