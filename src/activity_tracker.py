"""
Activity Tracker Module for TeamLogger Monitoring System

This module handles activity percentage tracking, screenshot period analysis,
and productivity metrics calculation.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ActivityPeriod:
    """Represents an activity period with timestamp and activity percentage"""
    timestamp: datetime
    activity_percentage: float
    total_time_seconds: int
    active_time_seconds: int
    idle_time_seconds: int

@dataclass
class DailyActivitySummary:
    """Summary of activity for a single day"""
    date: datetime
    total_periods: int
    average_activity: float
    max_activity: float
    min_activity: float
    low_productivity_periods: int  # < 30% activity
    high_productivity_periods: int  # > 70% activity
    total_active_hours: float
    total_idle_hours: float
    productivity_score: str  # "Low", "Medium", "High"

@dataclass
class WeeklyActivityReport:
    """Comprehensive weekly activity report"""
    employee_id: str
    employee_name: str
    week_start: datetime
    week_end: datetime
    daily_summaries: List[DailyActivitySummary]
    overall_average_activity: float
    total_low_productivity_periods: int
    total_high_productivity_periods: int
    most_productive_day: Optional[datetime]
    least_productive_day: Optional[datetime]
    activity_trend: str  # "Improving", "Declining", "Stable"

class ActivityTracker:
    """Main class for tracking and analyzing employee activity"""
    
    def __init__(self):
        self.low_activity_threshold = 30.0  # < 30% is low productivity
        self.high_activity_threshold = 70.0  # > 70% is high productivity
        
    def extract_activity_from_employee_data(self, employee_data: Dict, period_start: datetime, period_end: datetime) -> List[ActivityPeriod]:
        """
        Extract activity data from TeamLogger employee data

        Args:
            employee_data: Dictionary containing employee data from TeamLogger
            period_start: Start of the analysis period
            period_end: End of the analysis period

        Returns:
            List of ActivityPeriod objects (may be a single aggregate period)
        """
        periods = []

        try:
            if not isinstance(employee_data, dict):
                logger.warning("Employee data is not a dictionary")
                return periods

            # Extract activity ratios and counts from the aggregate data
            active_minutes_ratio = employee_data.get('activeMinutesRatio', 0)
            active_seconds_ratio = employee_data.get('activeSecondsRatio', 0)
            active_seconds_count = employee_data.get('activeSecondsCount', 0)
            inactive_seconds_count = employee_data.get('inactiveSecondsCount', 0)
            total_seconds_count = employee_data.get('totalSecondsCount', 0)
            active_tuple_count = employee_data.get('activeTimeTupleCount', 0)
            inactive_tuple_count = employee_data.get('inactiveTimeTupleCount', 0)

            # Use the more reliable activeMinutesRatio for activity percentage
            activity_percentage = active_minutes_ratio * 100 if active_minutes_ratio else 0

            # Create a single aggregate period for the entire time range
            # This represents the overall activity for the period
            if total_seconds_count > 0:
                period = ActivityPeriod(
                    timestamp=period_start,  # Use period start as timestamp
                    activity_percentage=min(100, max(0, activity_percentage)),
                    total_time_seconds=total_seconds_count,
                    active_time_seconds=active_seconds_count,
                    idle_time_seconds=inactive_seconds_count
                )
                periods.append(period)

                logger.info(f"Extracted aggregate activity: {activity_percentage:.2f}% activity over {total_seconds_count/3600:.2f} hours")
                logger.info(f"Active periods: {active_tuple_count}, Inactive periods: {inactive_tuple_count}")

            # If we have tuple counts, we can estimate daily breakdown
            total_tuples = active_tuple_count + inactive_tuple_count
            if total_tuples > 0:
                # Estimate daily activity by distributing across the period
                period_days = (period_end - period_start).days + 1

                for day_offset in range(min(period_days, 7)):  # Limit to 7 days max
                    day_start = period_start + timedelta(days=day_offset)

                    # Estimate daily activity (simplified approach)
                    daily_activity_percentage = activity_percentage
                    daily_active_seconds = active_seconds_count / period_days
                    daily_total_seconds = total_seconds_count / period_days
                    daily_idle_seconds = inactive_seconds_count / period_days

                    if daily_total_seconds > 0:
                        daily_period = ActivityPeriod(
                            timestamp=day_start,
                            activity_percentage=daily_activity_percentage,
                            total_time_seconds=int(daily_total_seconds),
                            active_time_seconds=int(daily_active_seconds),
                            idle_time_seconds=int(daily_idle_seconds)
                        )
                        periods.append(daily_period)

            logger.info(f"Created {len(periods)} activity periods from employee data")

        except Exception as e:
            logger.error(f"Error extracting activity from employee data: {e}")

        return periods
    
    def calculate_daily_summary(self, periods: List[ActivityPeriod], target_date: datetime) -> Optional[DailyActivitySummary]:
        """
        Calculate daily activity summary for a specific date
        
        Args:
            periods: List of activity periods
            target_date: Date to calculate summary for
            
        Returns:
            DailyActivitySummary object or None if no data
        """
        try:
            # Filter periods for the target date
            daily_periods = [
                p for p in periods 
                if p.timestamp.date() == target_date.date()
            ]
            
            if not daily_periods:
                return None
            
            # Calculate statistics
            activity_percentages = [p.activity_percentage for p in daily_periods]
            average_activity = statistics.mean(activity_percentages)
            max_activity = max(activity_percentages)
            min_activity = min(activity_percentages)
            
            # Count productivity periods
            low_productivity_periods = sum(1 for p in daily_periods if p.activity_percentage < self.low_activity_threshold)
            high_productivity_periods = sum(1 for p in daily_periods if p.activity_percentage > self.high_activity_threshold)
            
            # Calculate total hours
            total_active_hours = sum(p.active_time_seconds for p in daily_periods) / 3600
            total_idle_hours = sum(p.idle_time_seconds for p in daily_periods) / 3600
            
            # Determine productivity score
            if average_activity >= self.high_activity_threshold:
                productivity_score = "High"
            elif average_activity >= self.low_activity_threshold:
                productivity_score = "Medium"
            else:
                productivity_score = "Low"
            
            return DailyActivitySummary(
                date=target_date,
                total_periods=len(daily_periods),
                average_activity=round(average_activity, 2),
                max_activity=round(max_activity, 2),
                min_activity=round(min_activity, 2),
                low_productivity_periods=low_productivity_periods,
                high_productivity_periods=high_productivity_periods,
                total_active_hours=round(total_active_hours, 2),
                total_idle_hours=round(total_idle_hours, 2),
                productivity_score=productivity_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating daily summary for {target_date.date()}: {e}")
            return None
    
    def generate_weekly_report(self, employee_id: str, employee_name: str, 
                             periods: List[ActivityPeriod], week_start: datetime, 
                             week_end: datetime) -> WeeklyActivityReport:
        """
        Generate comprehensive weekly activity report
        
        Args:
            employee_id: Employee ID
            employee_name: Employee name
            periods: List of activity periods for the week
            week_start: Start of the week
            week_end: End of the week
            
        Returns:
            WeeklyActivityReport object
        """
        try:
            daily_summaries = []
            current_date = week_start
            
            # Generate daily summaries for each day of the week
            while current_date <= week_end:
                daily_summary = self.calculate_daily_summary(periods, current_date)
                if daily_summary:
                    daily_summaries.append(daily_summary)
                current_date += timedelta(days=1)
            
            if not daily_summaries:
                # Return empty report if no data
                return WeeklyActivityReport(
                    employee_id=employee_id,
                    employee_name=employee_name,
                    week_start=week_start,
                    week_end=week_end,
                    daily_summaries=[],
                    overall_average_activity=0,
                    total_low_productivity_periods=0,
                    total_high_productivity_periods=0,
                    most_productive_day=None,
                    least_productive_day=None,
                    activity_trend="No Data"
                )
            
            # Calculate overall statistics
            overall_average_activity = statistics.mean([d.average_activity for d in daily_summaries])
            total_low_productivity_periods = sum(d.low_productivity_periods for d in daily_summaries)
            total_high_productivity_periods = sum(d.high_productivity_periods for d in daily_summaries)
            
            # Find most and least productive days
            most_productive_day = max(daily_summaries, key=lambda x: x.average_activity).date
            least_productive_day = min(daily_summaries, key=lambda x: x.average_activity).date
            
            # Determine activity trend
            activity_trend = self._calculate_activity_trend(daily_summaries)
            
            return WeeklyActivityReport(
                employee_id=employee_id,
                employee_name=employee_name,
                week_start=week_start,
                week_end=week_end,
                daily_summaries=daily_summaries,
                overall_average_activity=round(overall_average_activity, 2),
                total_low_productivity_periods=total_low_productivity_periods,
                total_high_productivity_periods=total_high_productivity_periods,
                most_productive_day=most_productive_day,
                least_productive_day=least_productive_day,
                activity_trend=activity_trend
            )
            
        except Exception as e:
            logger.error(f"Error generating weekly report for {employee_name}: {e}")
            return WeeklyActivityReport(
                employee_id=employee_id,
                employee_name=employee_name,
                week_start=week_start,
                week_end=week_end,
                daily_summaries=[],
                overall_average_activity=0,
                total_low_productivity_periods=0,
                total_high_productivity_periods=0,
                most_productive_day=None,
                least_productive_day=None,
                activity_trend="Error"
            )
    
    def _calculate_activity_trend(self, daily_summaries: List[DailyActivitySummary]) -> str:
        """Calculate activity trend based on daily summaries"""
        if len(daily_summaries) < 2:
            return "Insufficient Data"
        
        activities = [d.average_activity for d in daily_summaries]
        
        # Simple trend calculation
        first_half = activities[:len(activities)//2]
        second_half = activities[len(activities)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        difference = second_avg - first_avg
        
        if difference > 5:
            return "Improving"
        elif difference < -5:
            return "Declining"
        else:
            return "Stable"
