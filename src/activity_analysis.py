"""
Activity Analysis Module for TeamLogger Monitoring System

This module provides advanced analysis functions for activity data,
including productivity insights, trend analysis, and reporting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
import pandas as pd
from dataclasses import asdict

from .activity_tracker import ActivityTracker, WeeklyActivityReport, DailyActivitySummary
from .teamlogger_client import TeamLoggerClient

logger = logging.getLogger(__name__)

class ActivityAnalyzer:
    """Advanced activity analysis and reporting"""
    
    def __init__(self, teamlogger_client: TeamLoggerClient):
        self.teamlogger = teamlogger_client
        self.activity_tracker = ActivityTracker()
        
    def analyze_team_activity(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Analyze activity for all team members
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary containing team activity analysis
        """
        try:
            employees = self.teamlogger.get_all_employees()
            team_reports = []
            
            logger.info(f"Analyzing activity for {len(employees)} employees")
            
            for employee in employees:
                try:
                    report = self.teamlogger.generate_employee_activity_report(
                        employee['id'], start_date, end_date
                    )
                    
                    if report:
                        team_reports.append(report)
                        
                except Exception as e:
                    logger.error(f"Error analyzing activity for {employee.get('name', 'Unknown')}: {e}")
                    continue
            
            # Calculate team statistics
            team_stats = self._calculate_team_statistics(team_reports)
            
            return {
                'period_start': start_date,
                'period_end': end_date,
                'total_employees': len(employees),
                'employees_with_data': len(team_reports),
                'team_reports': team_reports,
                'team_statistics': team_stats,
                'analysis_timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing team activity: {e}")
            return {
                'period_start': start_date,
                'period_end': end_date,
                'total_employees': 0,
                'employees_with_data': 0,
                'team_reports': [],
                'team_statistics': {},
                'error': str(e),
                'analysis_timestamp': datetime.now()
            }
    
    def _calculate_team_statistics(self, reports: List[WeeklyActivityReport]) -> Dict:
        """Calculate team-wide activity statistics"""
        if not reports:
            return {}
        
        try:
            # Extract overall activity percentages
            activity_percentages = [r.overall_average_activity for r in reports if r.overall_average_activity > 0]
            
            if not activity_percentages:
                return {'error': 'No activity data available'}
            
            # Calculate statistics
            team_avg_activity = statistics.mean(activity_percentages)
            team_median_activity = statistics.median(activity_percentages)
            team_max_activity = max(activity_percentages)
            team_min_activity = min(activity_percentages)
            
            # Count productivity levels
            high_performers = sum(1 for a in activity_percentages if a >= 70)
            medium_performers = sum(1 for a in activity_percentages if 30 <= a < 70)
            low_performers = sum(1 for a in activity_percentages if a < 30)
            
            # Calculate total productivity periods
            total_low_periods = sum(r.total_low_productivity_periods for r in reports)
            total_high_periods = sum(r.total_high_productivity_periods for r in reports)
            
            # Identify trends
            improving_employees = sum(1 for r in reports if r.activity_trend == "Improving")
            declining_employees = sum(1 for r in reports if r.activity_trend == "Declining")
            stable_employees = sum(1 for r in reports if r.activity_trend == "Stable")
            
            return {
                'team_average_activity': round(team_avg_activity, 2),
                'team_median_activity': round(team_median_activity, 2),
                'team_max_activity': round(team_max_activity, 2),
                'team_min_activity': round(team_min_activity, 2),
                'high_performers': high_performers,
                'medium_performers': medium_performers,
                'low_performers': low_performers,
                'total_low_productivity_periods': total_low_periods,
                'total_high_productivity_periods': total_high_periods,
                'improving_employees': improving_employees,
                'declining_employees': declining_employees,
                'stable_employees': stable_employees,
                'total_analyzed': len(reports)
            }
            
        except Exception as e:
            logger.error(f"Error calculating team statistics: {e}")
            return {'error': str(e)}
    
    def identify_productivity_patterns(self, reports: List[WeeklyActivityReport]) -> Dict:
        """
        Identify productivity patterns across the team
        
        Args:
            reports: List of weekly activity reports
            
        Returns:
            Dictionary containing productivity patterns
        """
        try:
            patterns = {
                'most_productive_days': {},
                'least_productive_days': {},
                'common_low_productivity_times': [],
                'high_performers': [],
                'employees_needing_attention': []
            }
            
            # Analyze most/least productive days
            for report in reports:
                if report.most_productive_day:
                    day_name = report.most_productive_day.strftime('%A')
                    patterns['most_productive_days'][day_name] = patterns['most_productive_days'].get(day_name, 0) + 1
                
                if report.least_productive_day:
                    day_name = report.least_productive_day.strftime('%A')
                    patterns['least_productive_days'][day_name] = patterns['least_productive_days'].get(day_name, 0) + 1
            
            # Identify high performers (>70% average activity)
            patterns['high_performers'] = [
                {
                    'name': r.employee_name,
                    'activity': r.overall_average_activity,
                    'trend': r.activity_trend
                }
                for r in reports if r.overall_average_activity >= 70
            ]
            
            # Identify employees needing attention (<30% average activity or declining trend)
            patterns['employees_needing_attention'] = [
                {
                    'name': r.employee_name,
                    'activity': r.overall_average_activity,
                    'trend': r.activity_trend,
                    'low_periods': r.total_low_productivity_periods,
                    'reason': 'Low Activity' if r.overall_average_activity < 30 else 'Declining Trend'
                }
                for r in reports 
                if r.overall_average_activity < 30 or r.activity_trend == "Declining"
            ]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying productivity patterns: {e}")
            return {'error': str(e)}
    
    def generate_activity_insights(self, team_analysis: Dict) -> List[str]:
        """
        Generate actionable insights from team activity analysis
        
        Args:
            team_analysis: Team activity analysis data
            
        Returns:
            List of insight strings
        """
        insights = []
        
        try:
            stats = team_analysis.get('team_statistics', {})
            reports = team_analysis.get('team_reports', [])
            
            if not stats or not reports:
                return ["No activity data available for analysis"]
            
            # Overall team performance insight
            avg_activity = stats.get('team_average_activity', 0)
            if avg_activity >= 70:
                insights.append(f"🟢 Excellent team performance with {avg_activity}% average activity")
            elif avg_activity >= 50:
                insights.append(f"🟡 Good team performance with {avg_activity}% average activity")
            else:
                insights.append(f"🔴 Team performance needs improvement - {avg_activity}% average activity")
            
            # High performers insight
            high_performers = stats.get('high_performers', 0)
            total = stats.get('total_analyzed', 1)
            high_performer_percentage = (high_performers / total) * 100
            insights.append(f"📈 {high_performers} out of {total} employees ({high_performer_percentage:.1f}%) are high performers (>70% activity)")
            
            # Low performers insight
            low_performers = stats.get('low_performers', 0)
            if low_performers > 0:
                low_performer_percentage = (low_performers / total) * 100
                insights.append(f"⚠️ {low_performers} employees ({low_performer_percentage:.1f}%) have low activity (<30%) and may need support")
            
            # Trend insights
            improving = stats.get('improving_employees', 0)
            declining = stats.get('declining_employees', 0)
            
            if improving > declining:
                insights.append(f"📊 Positive trend: {improving} employees improving vs {declining} declining")
            elif declining > improving:
                insights.append(f"📉 Concerning trend: {declining} employees declining vs {improving} improving")
            else:
                insights.append(f"📊 Stable trends: {improving} improving, {declining} declining")
            
            # Productivity periods insight
            low_periods = stats.get('total_low_productivity_periods', 0)
            high_periods = stats.get('total_high_productivity_periods', 0)
            
            if high_periods > low_periods:
                insights.append(f"✅ More high productivity periods ({high_periods}) than low ({low_periods})")
            else:
                insights.append(f"⚠️ More low productivity periods ({low_periods}) than high ({high_periods})")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return [f"Error generating insights: {str(e)}"]
    
    def export_activity_data_to_dataframe(self, team_analysis: Dict) -> pd.DataFrame:
        """
        Export activity data to pandas DataFrame for further analysis
        
        Args:
            team_analysis: Team activity analysis data
            
        Returns:
            pandas DataFrame with activity data
        """
        try:
            reports = team_analysis.get('team_reports', [])
            
            if not reports:
                return pd.DataFrame()
            
            # Convert reports to DataFrame
            data = []
            for report in reports:
                row = {
                    'employee_id': report.employee_id,
                    'employee_name': report.employee_name,
                    'week_start': report.week_start,
                    'week_end': report.week_end,
                    'overall_average_activity': report.overall_average_activity,
                    'total_low_productivity_periods': report.total_low_productivity_periods,
                    'total_high_productivity_periods': report.total_high_productivity_periods,
                    'activity_trend': report.activity_trend,
                    'most_productive_day': report.most_productive_day,
                    'least_productive_day': report.least_productive_day,
                    'days_with_data': len(report.daily_summaries)
                }
                
                # Add daily summary data
                for i, daily in enumerate(report.daily_summaries):
                    row[f'day_{i+1}_activity'] = daily.average_activity
                    row[f'day_{i+1}_productivity_score'] = daily.productivity_score
                
                data.append(row)
            
            df = pd.DataFrame(data)
            logger.info(f"Exported activity data for {len(df)} employees to DataFrame")
            return df
            
        except Exception as e:
            logger.error(f"Error exporting to DataFrame: {e}")
            return pd.DataFrame()
