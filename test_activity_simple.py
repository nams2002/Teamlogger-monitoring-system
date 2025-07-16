#!/usr/bin/env python3
"""
Simple test script for updated activity tracking functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta
from src.teamlogger_client import TeamLoggerClient
from src.activity_analysis import ActivityAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_updated_activity_tracking():
    """Test the updated activity tracking with real TeamLogger data"""
    print("🔍 TESTING UPDATED ACTIVITY TRACKING")
    print("=" * 60)
    
    try:
        client = TeamLoggerClient()
        
        # Get employees
        employees = client.get_all_employees()
        if not employees:
            print("❌ No employees found")
            return False
        
        print(f"Found {len(employees)} employees")
        
        # Test with first few employees
        test_employees = employees[:3]
        
        # Get current week data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        print()
        
        for i, employee in enumerate(test_employees, 1):
            employee_id = employee['id']
            employee_name = employee.get('name', 'Unknown')
            
            print(f"🧑 Employee {i}: {employee_name}")
            print("-" * 40)
            
            # Test activity data extraction
            activity_data = client.get_employee_activity_data(employee_id, start_date, end_date)
            
            if activity_data:
                print(f"✅ Activity data extracted")
                print(f"   Activity Percentage: {activity_data.get('activity_percentage', 0):.2f}%")
                print(f"   Active Minutes Ratio: {activity_data.get('active_minutes_ratio', 0):.4f}")
                print(f"   Active Seconds: {activity_data.get('active_seconds_count', 0):,}")
                print(f"   Inactive Seconds: {activity_data.get('inactive_seconds_count', 0):,}")
                print(f"   Total Hours: {activity_data.get('total_hours', 0):.2f}h")
                print(f"   Idle Hours: {activity_data.get('idle_hours', 0):.2f}h")
                
                # Test activity periods extraction
                periods = client.get_employee_activity_periods(employee_id, start_date, end_date)
                print(f"   Activity Periods: {len(periods)}")
                
                if periods:
                    avg_activity = sum(p.activity_percentage for p in periods) / len(periods)
                    print(f"   Average Activity: {avg_activity:.2f}%")
                    
                    # Show sample periods
                    for j, period in enumerate(periods[:2]):
                        print(f"     Period {j+1}: {period.activity_percentage:.2f}% on {period.timestamp.date()}")
                
                # Test weekly report generation
                report = client.generate_employee_activity_report(employee_id, start_date, end_date)
                
                if report:
                    print(f"✅ Weekly report generated")
                    print(f"   Overall Average: {report.overall_average_activity:.2f}%")
                    print(f"   Activity Trend: {report.activity_trend}")
                    print(f"   Daily Summaries: {len(report.daily_summaries)}")
                    print(f"   Low Productivity Periods: {report.total_low_productivity_periods}")
                    print(f"   High Productivity Periods: {report.total_high_productivity_periods}")
                else:
                    print("⚠️ No weekly report generated")
            else:
                print("❌ No activity data found")
            
            print()
        
        # Test team analysis
        print("🏢 TEAM ANALYSIS")
        print("-" * 40)
        
        analyzer = ActivityAnalyzer(client)
        team_analysis = analyzer.analyze_team_activity(start_date, end_date)
        
        if team_analysis and team_analysis.get('team_statistics'):
            stats = team_analysis['team_statistics']
            print(f"✅ Team analysis completed")
            print(f"   Employees Analyzed: {stats.get('total_analyzed', 0)}")
            print(f"   Team Average Activity: {stats.get('team_average_activity', 0):.2f}%")
            print(f"   High Performers: {stats.get('high_performers', 0)}")
            print(f"   Medium Performers: {stats.get('medium_performers', 0)}")
            print(f"   Low Performers: {stats.get('low_performers', 0)}")
            
            # Show insights
            insights = analyzer.generate_activity_insights(team_analysis)
            print(f"\n💡 Key Insights:")
            for insight in insights[:3]:  # Show first 3 insights
                print(f"   {insight}")
        else:
            print("⚠️ Team analysis completed but no statistics available")
        
        print("\n🎉 Activity tracking test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_updated_activity_tracking()
