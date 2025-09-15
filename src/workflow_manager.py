import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from src.email_service import EmailService
from src.activity_analysis import ActivityAnalyzer
from config.settings import Config

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self):
        self.teamlogger = TeamLoggerClient()
        self.google_sheets = GoogleSheetsLeaveClient()
        self.email_service = EmailService()
        self.activity_analyzer = ActivityAnalyzer(self.teamlogger)
        
        # 5-day work system configuration
        self.min_hours = Config.MINIMUM_HOURS_PER_WEEK  # 40 hours
        self.acceptable_hours = Config.ACCEPTABLE_HOURS_PER_WEEK  # 37 hours (with 3-hour buffer)
        self.work_days = Config.WORK_DAYS_PER_WEEK  # 5 days (Monday-Friday)
        self.hours_per_day = Config.HOURS_PER_WORKING_DAY  # 8 hours per day

        # Activity monitoring configuration
        self.activity_threshold = 50.0  # Minimum activity percentage (50%)
        self.enable_activity_alerts = False  # Disabled for now - only preview mode
        
        # FIXED: Excluded employees with case-insensitive matching
        self.excluded_employees = {
            'aishik chatterjee': ['aishik', 'chatterjee', 'aishik chatterjee'],
            'tirtharaj bhoumik': ['tirtharaj', 'bhoumik', 'tirtharaj bhoumik'],
            'vishal kumar': ['vishal', 'kumar', 'vishal kumar']
        }
        
        # --- AI Client Initialization ---
        self.openai_client = None

        # Log exactly what Config saw
        logger.debug(f"Config.OPENAI_API_KEY            = {bool(Config.OPENAI_API_KEY)}")
        logger.debug(f"Config.ENABLE_OPENAI_ENHANCEMENT = {Config.ENABLE_OPENAI_ENHANCEMENT}")

        # Only wire up OpenAI if both the key and flag are present
        if Config.OPENAI_API_KEY and Config.ENABLE_OPENAI_ENHANCEMENT:
            try:
                import openai
                # ensure global key is set
                openai.api_key = Config.OPENAI_API_KEY
                # use the module itself as "client"
                self.openai_client = openai
                logger.info("🤖 OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize OpenAI client: {e}")
        else:
            logger.info("🤖 Skipping AI init (OPENAI_API_KEY or ENABLE_OPENAI_ENHANCEMENT missing)")


    
    def _is_employee_excluded(self, employee_name: str) -> bool:
        """Check if employee should be excluded (case-insensitive with variations)"""
        name_lower = employee_name.lower().strip()
        
        # Check exact matches
        for excluded_name, variations in self.excluded_employees.items():
            if name_lower == excluded_name:
                return True
            
            # Check variations
            for variation in variations:
                if variation in name_lower or name_lower in variation:
                    return True
            
            # Check by parts (first name or last name)
            name_parts = name_lower.split()
            for part in name_parts:
                if part in variations:
                    return True
        
        return False
    
    def run_workflow(self):
        """Main workflow execution - OPTIMIZED for speed and accuracy"""
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("Starting Employee Hours Monitoring Workflow")
        logger.info(f"Execution time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        # Get monitoring period
        work_week_start, work_week_end = self._get_monitoring_period()
        logger.info(f"Monitoring period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")
        
        # Get all employees in batch (faster)
        all_employees = self.teamlogger.get_all_employees()

        # Filter to only include employees who are currently in Google Sheets (active employees)
        employees = self._filter_active_employees(all_employees, work_week_start, work_week_end)
        total_employees = len(employees)
        logger.info(f"Found {len(all_employees)} total employees, {total_employees} active employees in Google Sheets")
        
        if not employees:
            logger.error("No employees found. Workflow cannot proceed.")
            return
        
        # Process counters
        processed_count = 0
        alerts_sent = 0
        employees_on_leave = 0
        employees_meeting_hours = 0
        excluded_count = 0
        errors_count = 0
        
        # Batch process employees for speed
        for employee in employees:
            try:
                processed_count += 1
                employee_name = employee.get('name', 'Unknown')
                
                # FIXED: Check exclusion first
                if self._is_employee_excluded(employee_name):
                    logger.info(f"🚫 Excluding {employee_name} from alerts")
                    excluded_count += 1
                    continue
                
                # Process employee
                result = self._process_employee_fast(employee, work_week_start, work_week_end)
                
                if result['status'] == 'alert_sent':
                    alerts_sent += 1
                elif result['status'] == 'on_full_leave':
                    employees_on_leave += 1
                elif result['status'] == 'hours_met':
                    employees_meeting_hours += 1
                    
            except Exception as e:
                errors_count += 1
                logger.error(f"Error processing {employee.get('name', 'Unknown')}: {str(e)}")
        
        # Summary
        execution_time = datetime.now() - start_time
        
        logger.info("="*60)
        logger.info("WORKFLOW EXECUTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Execution time: {execution_time}")
        logger.info(f"Total employees: {total_employees}")
        logger.info(f"Successfully processed: {processed_count - errors_count}")
        logger.info(f"Excluded employees: {excluded_count}")
        logger.info(f"Alerts sent: {alerts_sent}")
        logger.info(f"Employees on full leave: {employees_on_leave}")
        logger.info(f"Employees meeting hours: {employees_meeting_hours}")
        logger.info(f"Processing errors: {errors_count}")
        logger.info("="*60)
        
        return {
            'total_employees': total_employees,
            'processed': processed_count - errors_count,
            'excluded': excluded_count,
            'alerts_sent': alerts_sent,
            'on_leave': employees_on_leave,
            'hours_met': employees_meeting_hours,
            'errors': errors_count,
            'execution_time': str(execution_time)
        }
    
    def _process_employee_fast(self, employee: Dict, work_week_start: datetime, work_week_end: datetime) -> Dict:
        """Process individual employee - FAST and ACCURATE"""
        employee_id = employee.get('id')
        employee_email = employee.get('email')
        employee_name = employee.get('name', 'Employee')
        
        # Get hours worked (Mon-Sun)
        weekly_data = self.teamlogger.get_weekly_summary(employee_id, work_week_start, work_week_end)
        if not weekly_data:
            logger.warning(f"No data for {employee_name}")
            return {'status': 'no_data', 'employee': employee_name}
        
        actual_hours_worked = weekly_data['total_hours']
        
        # FIXED: Get leave days with force refresh for real-time accuracy
        leave_days = self._get_working_day_leaves_count_realtime(
            employee_name, work_week_start, work_week_end
        )
        
        # Calculate requirements
        required_hours = self._calculate_required_hours(leave_days)
        acceptable_hours = max(0, required_hours - Config.HOURS_BUFFER)  # 3-hour buffer
        
        # REMOVED: 10-minute negligible shortfall check
        # Now using only the 3-hour buffer for decisions
        
        # Simple decision logic (removed complex AI for accuracy)
        if leave_days >= 5:
            logger.info(f"🏖️ {employee_name} on full leave ({leave_days} days)")
            return {'status': 'on_full_leave', 'employee': employee_name, 'leave_days': leave_days}
        
        if actual_hours_worked >= acceptable_hours:
            logger.debug(f"✅ {employee_name}: {actual_hours_worked:.1f}h >= {acceptable_hours:.1f}h")
            return {'status': 'hours_met', 'employee': employee_name, 'hours': actual_hours_worked}
        
        # Alert needed
        shortfall = required_hours - actual_hours_worked
        
        logger.info(f"🚨 Alert for {employee_name}:")
        logger.info(f"  Hours: {actual_hours_worked:.1f}h < {acceptable_hours:.1f}h")
        logger.info(f"  Required: {required_hours:.1f}h, Shortfall: {shortfall:.1f}h")
        logger.info(f"  Leave days: {leave_days}")
        
        # Create email data with idle time information
        email_data = {
            'email': employee_email,
            'name': employee_name,
            'week_start': work_week_start.strftime('%Y-%m-%d'),
            'week_end': work_week_end.strftime('%Y-%m-%d'),
            'total_hours': round(actual_hours_worked, 2),  # Now represents active hours (total - idle)
            'original_total_hours': round(weekly_data.get('original_total_hours', actual_hours_worked), 2),
            'idle_hours': round(weekly_data.get('idle_hours', 0), 2),
            'required_hours': round(required_hours, 2),
            'acceptable_hours': round(acceptable_hours, 2),
            'shortfall': round(shortfall, 2),
            'shortfall_minutes': int(shortfall * 60),
            'days_worked': 5 - leave_days,
            'leave_days': leave_days
        }
        
        # Send alert
        if self.email_service.send_low_hours_alert(email_data):
            logger.info(f"📧 Alert sent to {employee_name}")
            return {'status': 'alert_sent', 'employee': employee_name, 'shortfall': shortfall}
        else:
            logger.error(f"❌ Failed to send alert to {employee_name}")
            return {'status': 'error', 'employee': employee_name}
    
    def _calculate_required_hours(self, leave_days: float) -> float:
        """Simple calculation: 8 hours × (5 - leave_days)"""
        if leave_days >= 5:
            return 0.0
        return 8.0 * (5 - leave_days)
    
    def _get_working_day_leaves_count_realtime(self, employee_name: str, start_date: datetime, end_date: datetime) -> float:
        """Get leave count with FORCE REFRESH for real-time accuracy"""
        try:
            # FIXED: Force refresh for real-time data
            leaves = self.google_sheets.get_employee_leaves(employee_name, start_date, end_date, force_refresh=True)
            
            working_day_leave_count = 0.0
            
            for leave in leaves:
                leave_start = max(leave['start_date'], start_date)
                leave_end = min(leave['end_date'], end_date)
                
                if leave_start <= leave_end:
                    # Check if half day
                    if leave.get('is_half_day', False) or leave.get('days_count', 1) == 0.5:
                        working_day_leave_count += 0.5
                    else:
                        # Count only working days (Mon-Fri)
                        current = leave_start
                        while current <= leave_end:
                            if current.weekday() < 5:  # Monday=0, Friday=4
                                working_day_leave_count += 1
                            current += timedelta(days=1)
            
            logger.info(f"📊 {employee_name}: {working_day_leave_count} leave days (real-time)")
            return working_day_leave_count
            
        except Exception as e:
            logger.error(f"Error getting leaves for {employee_name}: {str(e)}")
            return 0.0
    
    def _get_monitoring_period(self) -> Tuple[datetime, datetime]:
        """Get the monitoring period (previous Monday to Sunday)"""
        today = datetime.now()
        current_monday = today - timedelta(days=today.weekday())
        previous_monday = current_monday - timedelta(days=7)
        previous_sunday = previous_monday + timedelta(days=6)
        
        start_time = previous_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = previous_sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return start_time, end_time
    
    def _get_working_day_leaves_count(self, employee_name: str, start_date: datetime, end_date: datetime) -> float:
        """Get count of approved leave days that fall on working days (Monday-Friday) only"""
        try:
            leaves = self.google_sheets.get_employee_leaves(employee_name, start_date, end_date, force_refresh=True)
            working_day_leave_count = 0.0
            
            for leave in leaves:
                # Only count if it's a working day (Mon-Fri)
                if leave['start_date'].weekday() < 5:
                    working_day_leave_count += leave.get('days_count', 1.0)
            
            logger.info(f"📊 {employee_name}: {working_day_leave_count} working day leaves")
            return working_day_leave_count
            
        except Exception as e:
            logger.error(f"Error calculating working day leaves for {employee_name}: {str(e)}")
            return 0.0

    def _filter_active_employees(self, employees: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """Filter employees to only include those who are currently in Google Sheets (active employees)

        Known inactive employees (left organization):
        - Priya Bhadauria, aishik chatterjee, Ashique Mohammed C, Aayush Limbbad
        - Kajol Jaiswal, Tirtharaj Bhowmik, Neeraj Deshpande, Arsh Sohal
        """
        active_employees = []

        # Known inactive employees who have left the organization
        KNOWN_INACTIVE_EMPLOYEES = {
            'priya bhadauria', 'aishik chatterjee', 'ashique mohammed c', 'aayush limbbad',
            'kajol jaiswal', 'tirtharaj bhowmik', 'neeraj deshpande', 'arsh sohal',
            'aayush limbad'  # Alternative spelling
        }

        logger.info(f"Filtering {len(employees)} employees to find active ones in Google Sheets...")

        for employee in employees:
            employee_name = employee.get('name', '')
            if not employee_name:
                continue

            # Quick check against known inactive employees
            employee_name_lower = employee_name.strip().lower()
            if employee_name_lower in KNOWN_INACTIVE_EMPLOYEES:
                logger.info(f"❌ {employee_name} - Known inactive employee (left organization)")
                continue

            try:
                # Try to get leave data for this employee from Google Sheets
                # If the employee is not in the sheet, this will return empty or fail
                leaves = self.google_sheets.get_employee_leaves(employee_name, start_date, end_date, force_refresh=True)

                # Check if we can find this employee in the current month's sheet
                current_month_sheet = datetime.now().strftime("%b %y")  # Use "Sep 25" format
                sheet_data = self.google_sheets._fetch_sheet_data(current_month_sheet, force_refresh=True)

                employee_found_in_sheet = False
                if sheet_data:
                    for row in sheet_data:
                        if row and len(row) > 0:
                            cell_name = str(row[0]).strip().lower()
                            # Multiple matching strategies
                            if (employee_name_lower == cell_name or
                                employee_name_lower in cell_name or
                                cell_name in employee_name_lower or
                                # Check if main parts of names match
                                any(part in cell_name for part in employee_name_lower.split() if len(part) > 2)):
                                employee_found_in_sheet = True
                                break

                if employee_found_in_sheet:
                    active_employees.append(employee)
                    logger.debug(f"✅ {employee_name} - Found in Google Sheets (active)")
                else:
                    logger.info(f"❌ {employee_name} - Not found in Google Sheets (likely left organization)")

            except Exception as e:
                logger.warning(f"Error checking {employee_name} in Google Sheets: {str(e)}")
                # If there's an error, exclude the employee to be safe (don't include potentially inactive employees)
                logger.info(f"❌ {employee_name} - Excluded due to error (safer to exclude)")

        logger.info(f"Filtered to {len(active_employees)} active employees (removed {len(employees) - len(active_employees)} who left)")
        return active_employees

    def get_employees_needing_real_alerts(self) -> List[Dict]:
        """Get list of employees who would receive alerts - ACCURATE VERSION"""
        work_week_start, work_week_end = self._get_monitoring_period()
        employees = self.teamlogger.get_all_employees()

        # Filter out employees who are no longer in Google Sheets (left the organization)
        active_employees = self._filter_active_employees(employees, work_week_start, work_week_end)
        employees_needing_alerts = []

        for employee in active_employees:
            try:
                employee_name = employee.get('name', '')
                
                # FIXED: Skip excluded employees
                if self._is_employee_excluded(employee_name):
                    logger.debug(f"Skipping excluded employee: {employee_name}")
                    continue
                
                weekly_data = self.teamlogger.get_weekly_summary(employee['id'], work_week_start, work_week_end)
                if not weekly_data:
                    continue
                
                # Get real-time leave data
                leave_days = self._get_working_day_leaves_count_realtime(
                    employee_name, work_week_start, work_week_end
                )
                
                actual_hours = weekly_data['total_hours']
                required_hours = self._calculate_required_hours(leave_days)
                acceptable_hours = max(0, required_hours - Config.HOURS_BUFFER)
                
                # Simple check - no AI complications
                if actual_hours < acceptable_hours and leave_days < 5:
                    shortfall = required_hours - actual_hours
                    
                    employees_needing_alerts.append({
                        'employee': employee,
                        'weekly_data': weekly_data,
                        'leave_days': leave_days,
                        'required_hours': required_hours,
                        'acceptable_hours': acceptable_hours,
                        'shortfall': shortfall,
                        'shortfall_minutes': int(shortfall * 60),
                        'working_days': 5 - leave_days
                    })
                    
            except Exception as e:
                logger.error(f"Error checking {employee.get('name', 'Unknown')}: {str(e)}")
        
        return employees_needing_alerts

    def run_preview_mode(self):
        """Preview mode - show who would get alerts without sending emails"""
        logger.info("🔍 PREVIEW MODE - No emails will be sent")
        logger.info("="*60)

        # Get monitoring period
        work_week_start, work_week_end = self._get_monitoring_period()
        logger.info(f"Preview period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")

        # Get employees who would receive alerts
        employees_needing_alerts = self.get_employees_needing_real_alerts()

        if not employees_needing_alerts:
            logger.info("✅ No employees would receive alerts - all meeting requirements!")
            return {
                'preview_mode': True,
                'alerts_would_be_sent': 0,
                'employees_checked': len(self._filter_active_employees(self.teamlogger.get_all_employees(), work_week_start, work_week_end))
            }

        logger.info(f"📧 {len(employees_needing_alerts)} employees would receive alerts:")
        logger.info("-" * 60)

        for alert_data in employees_needing_alerts:
            employee = alert_data['employee']
            employee_name = employee.get('name', 'Unknown')
            shortfall = alert_data['shortfall']
            required_hours = alert_data['required_hours']
            actual_hours = alert_data['weekly_data']['total_hours']
            leave_days = alert_data['leave_days']

            logger.info(f"👤 {employee_name}")
            logger.info(f"   📧 Email: {employee.get('email', 'N/A')}")
            logger.info(f"   ⏰ Hours: {actual_hours:.1f}h / {required_hours:.1f}h (shortfall: {shortfall:.1f}h)")
            logger.info(f"   🏖️ Leave days: {leave_days}")

            # Get manager info
            manager_name = self._get_manager_name(employee_name)
            manager_email = self._get_manager_email(employee_name)
            if manager_name:
                logger.info(f"   👔 Manager: {manager_name} ({manager_email})")
            logger.info("")

        logger.info("="*60)
        logger.info(f"📊 PREVIEW SUMMARY: {len(employees_needing_alerts)} alerts would be sent")

        return {
            'preview_mode': True,
            'alerts_would_be_sent': len(employees_needing_alerts),
            'employee_details': employees_needing_alerts
        }

    def should_send_alerts_today(self) -> bool:
        """Check if today is Monday or Tuesday"""
        return datetime.now().weekday() in [0, 1]
    
    def is_optimal_execution_time(self) -> bool:
        """Check if current time is optimal for sending alerts (Monday 8 AM)"""
        now = datetime.now()
        return (now.weekday() == Config.EXECUTION_DAY and now.hour == Config.EXECUTION_HOUR)
    
    def get_week_boundaries(self) -> Tuple[datetime, datetime]:
        """Get monitoring period boundaries"""
        return self._get_monitoring_period()
    
    def get_work_week_statistics(self) -> Dict:
        """Get comprehensive statistics for the work week"""
        try:
            work_week_start, work_week_end = self._get_monitoring_period()
            all_employees = self.teamlogger.get_all_employees()

            # Filter to only include active employees (those in Google Sheets)
            employees = self._filter_active_employees(all_employees, work_week_start, work_week_end)
            
            stats = {
                'period': {
                    'start': work_week_start.strftime('%Y-%m-%d'),
                    'end': work_week_end.strftime('%Y-%m-%d'),
                    'type': '5-Day Work System'
                },
                'totals': {
                    'employees': len(employees),
                    'alerts_needed': 0,
                    'on_full_leave': 0,
                    'meeting_requirements': 0,
                    'excluded_employees': 0
                },
                'hour_distribution': {
                    '0-10h': 0, '11-20h': 0, '21-30h': 0,
                    '31-37h': 0, '37-40h': 0, '40h+': 0
                },
                'leave_distribution': {
                    '0_days': 0, '1_day': 0, '2_days': 0,
                    '3_days': 0, '4_days': 0, '5_days': 0
                }
            }
            
            for employee in employees:
                try:
                    if self._is_employee_excluded(employee['name']):
                        stats['totals']['excluded_employees'] += 1
                        continue
                    
                    weekly_data = self.teamlogger.get_weekly_summary(
                        employee['id'], work_week_start, work_week_end
                    )
                    if not weekly_data:
                        continue
                    
                    leave_days = self._get_working_day_leaves_count_realtime(
                        employee['name'], work_week_start, work_week_end
                    )
                    
                    hours = weekly_data['total_hours']
                    required_hours = self._calculate_required_hours(leave_days)
                    acceptable_hours = max(0, required_hours - Config.HOURS_BUFFER)
                    
                    # Categorize
                    if leave_days >= 5:
                        stats['totals']['on_full_leave'] += 1
                    elif hours < acceptable_hours:
                        stats['totals']['alerts_needed'] += 1
                    else:
                        stats['totals']['meeting_requirements'] += 1
                    
                    # Hour distribution
                    if hours < 11:
                        stats['hour_distribution']['0-10h'] += 1
                    elif hours < 21:
                        stats['hour_distribution']['11-20h'] += 1
                    elif hours < 31:
                        stats['hour_distribution']['21-30h'] += 1
                    elif hours < 37:
                        stats['hour_distribution']['31-37h'] += 1
                    elif hours < 40:
                        stats['hour_distribution']['37-40h'] += 1
                    else:
                        stats['hour_distribution']['40h+'] += 1
                    
                    # Leave distribution
                    leave_key = f'{min(int(leave_days), 5)}_day{"s" if leave_days != 1 else ""}'
                    if leave_key in stats['leave_distribution']:
                        stats['leave_distribution'][leave_key] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing statistics for {employee.get('name', 'Unknown')}: {str(e)}")
                    continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Error generating work week statistics: {str(e)}")
            return {}

    def get_employees_needing_activity_alerts(self) -> List[Dict]:
        """
        Get employees who need activity alerts based on previous week's activity levels

        Returns:
            List of employee dictionaries with activity data
        """
        try:
            work_week_start, work_week_end = self._get_monitoring_period()
            logger.info(f"Checking activity levels for period: {work_week_start.date()} to {work_week_end.date()}")

            all_employees = self.teamlogger.get_all_employees()
            # Filter to only include active employees (those in Google Sheets)
            employees = self._filter_active_employees(all_employees, work_week_start, work_week_end)
            employees_needing_alerts = []

            for employee in employees:
                try:
                    employee_name = employee.get('name', 'Unknown')
                    employee_id = employee.get('id')
                    employee_email = employee.get('email', '')

                    # Skip excluded employees
                    if self._is_employee_excluded(employee_name):
                        logger.debug(f"Skipping excluded employee: {employee_name}")
                        continue

                    # Get activity report for the employee
                    activity_report = self.teamlogger.generate_employee_activity_report(
                        employee_id, work_week_start, work_week_end
                    )

                    if not activity_report:
                        logger.warning(f"No activity data for {employee_name}")
                        continue

                    # Check if activity is below threshold
                    activity_percentage = activity_report.overall_average_activity

                    if activity_percentage < self.activity_threshold:
                        # Get manager information
                        manager_name = self._get_manager_name(employee_name)
                        manager_email = self._get_manager_email(employee_name)

                        # Get leave days for context
                        leave_days = self._get_working_day_leaves_count_realtime(
                            employee_name, work_week_start, work_week_end
                        )

                        # Get hours worked for context
                        weekly_data = self.teamlogger.get_weekly_summary(employee_id, work_week_start, work_week_end)
                        hours_worked = weekly_data['total_hours'] if weekly_data else 0

                        employee_alert_data = {
                            'id': employee_id,
                            'name': employee_name,
                            'email': employee_email,
                            'activity_percentage': round(activity_percentage, 2),
                            'activity_threshold': self.activity_threshold,
                            'activity_shortfall': round(self.activity_threshold - activity_percentage, 2),
                            'hours_worked': hours_worked,
                            'leave_days': leave_days,
                            'manager_name': manager_name,
                            'manager_email': manager_email,
                            'activity_trend': activity_report.activity_trend,
                            'low_productivity_periods': activity_report.total_low_productivity_periods,
                            'high_productivity_periods': activity_report.total_high_productivity_periods,
                            'most_productive_day': activity_report.most_productive_day.strftime('%A') if activity_report.most_productive_day else 'N/A',
                            'least_productive_day': activity_report.least_productive_day.strftime('%A') if activity_report.least_productive_day else 'N/A',
                            'period_start': work_week_start.strftime('%Y-%m-%d'),
                            'period_end': work_week_end.strftime('%Y-%m-%d')
                        }

                        employees_needing_alerts.append(employee_alert_data)
                        logger.info(f"🔴 {employee_name}: {activity_percentage:.1f}% activity (below {self.activity_threshold}% threshold)")
                    else:
                        logger.debug(f"✅ {employee_name}: {activity_percentage:.1f}% activity (above threshold)")

                except Exception as e:
                    logger.error(f"Error processing activity for {employee.get('name', 'Unknown')}: {e}")
                    continue

            logger.info(f"Found {len(employees_needing_alerts)} employees needing activity alerts")
            return employees_needing_alerts

        except Exception as e:
            logger.error(f"Error getting employees needing activity alerts: {e}")
            return []

    def run_activity_monitoring_workflow(self):
        """Run the activity monitoring workflow - separate from hours monitoring"""
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("Starting Activity Monitoring Workflow")
        logger.info(f"Execution time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

        # Get monitoring period
        work_week_start, work_week_end = self._get_monitoring_period()
        logger.info(f"Activity monitoring period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")

        # Get employees needing activity alerts
        employees_needing_alerts = self.get_employees_needing_activity_alerts()

        if not employees_needing_alerts:
            logger.info("✅ No employees need activity alerts - all above 50% threshold!")
            return {
                'total_employees_checked': len(self._filter_active_employees(self.teamlogger.get_all_employees(), work_week_start, work_week_end)),
                'activity_alerts_sent': 0,
                'activity_errors': 0,
                'execution_time': str(datetime.now() - start_time)
            }

        # Send activity alerts
        alerts_sent = 0
        errors_count = 0

        for employee_data in employees_needing_alerts:
            try:
                if self.email_service.send_low_activity_alert(employee_data):
                    alerts_sent += 1
                    logger.info(f"📧 Activity alert sent to {employee_data['name']}")
                else:
                    errors_count += 1
                    logger.error(f"❌ Failed to send activity alert to {employee_data['name']}")

            except Exception as e:
                errors_count += 1
                logger.error(f"Error sending activity alert to {employee_data.get('name', 'Unknown')}: {e}")

        # Summary
        execution_time = datetime.now() - start_time

        logger.info("="*60)
        logger.info("ACTIVITY MONITORING WORKFLOW SUMMARY")
        logger.info("="*60)
        logger.info(f"Execution time: {execution_time}")
        logger.info(f"Employees checked: {len(employees_needing_alerts)}")
        logger.info(f"Activity alerts sent: {alerts_sent}")
        logger.info(f"Activity errors: {errors_count}")
        logger.info("="*60)

        return {
            'total_employees_checked': len(employees_needing_alerts),
            'activity_alerts_sent': alerts_sent,
            'activity_errors': errors_count,
            'execution_time': str(execution_time)
        }

    def _get_manager_name(self, employee_name: str) -> str:
        """Get manager name for an employee"""
        try:
            from src.manager_mapping import get_manager_name
            return get_manager_name(employee_name) or "Not Assigned"
        except Exception as e:
            logger.error(f"Error getting manager name for {employee_name}: {e}")
            return "Not Assigned"

    def _get_manager_email(self, employee_name: str) -> str:
        """Get manager email for an employee"""
        try:
            from src.manager_mapping import get_manager_email
            return get_manager_email(employee_name) or "Not Available"
        except Exception as e:
            logger.error(f"Error getting manager email for {employee_name}: {e}")
            return "Not Available"