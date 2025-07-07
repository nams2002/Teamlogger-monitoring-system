import requests
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from config.settings import Config
import time

logger = logging.getLogger(__name__)

class TeamLoggerClient:
    def __init__(self):
        # Extract base URL without query parameters
        base_url = Config.TEAMLOGGER_API_URL
        if '?' in base_url:
            base_url = base_url.split('?')[0]
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {Config.TEAMLOGGER_BEARER_TOKEN}',
            'Content-Type': 'application/json'
        }
        logger.info(f"TeamLogger base URL: {self.base_url}")
    
    def _get_timestamp(self, dt: datetime) -> int:
        """Convert datetime to milliseconds timestamp"""
        return int(dt.timestamp() * 1000)
    
    def _get_previous_work_week(self) -> tuple[datetime, datetime]:
        """
        Get the previous work week (Monday to Friday)
        For Monday deployments, this gets the previous week's data
        For other days, gets the current week's data up to today
        """
        today = datetime.now()
        
        # If today is Monday, we want to check the previous week
        # Otherwise, we check the current week up to Friday
        if today.weekday() == 0:  # Monday
            # Get previous week (Monday to Friday)
            last_friday = today - timedelta(days=3)  # Previous Friday
            last_monday = last_friday - timedelta(days=4)  # Previous Monday
        else:
            # Get current week up to Friday or today if before Friday
            current_monday = today - timedelta(days=today.weekday())
            current_friday = current_monday + timedelta(days=4)
            
            # If it's weekend, use the completed week
            if today.weekday() >= 5:  # Saturday or Sunday
                last_monday = current_monday
                last_friday = current_friday
            else:
                # Use current week but only up to today or Friday (whichever is earlier)
                last_monday = current_monday
                last_friday = min(current_friday, today)
        
        # Set times to cover the full day
        start_time = last_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = last_friday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        logger.info(f"Checking work week: {start_time.date()} to {end_time.date()}")
        return start_time, end_time
    
    def get_employee_summary_report(self, start_date: datetime = None, end_date: datetime = None) -> Optional[Dict]:
        """
        Get employee summary report for a specific period
        If no dates provided, uses the previous work week (Monday-Friday)
        """
        try:
            if start_date is None or end_date is None:
                start_date, end_date = self._get_previous_work_week()
            
            endpoint = f"{self.base_url}/api/employee_summary_report"
            params = {
                'startTime': self._get_timestamp(start_date),
                'endTime': self._get_timestamp(end_date)
            }
            
            logger.info(f"Fetching summary report from: {endpoint}")
            logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
            logger.debug(f"Parameters: {params}")
            
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received {len(data) if isinstance(data, list) else 'non-list'} records from API")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Error fetching summary report: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response content: {e.response.text[:500]}...")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching summary report: {str(e)}")
            return None
    
    def get_all_employees(self) -> List[Dict]:
        """
        Get all active employees from the summary report
        Returns list of employee dictionaries with id, name, email, status
        """
        try:
            report = self.get_employee_summary_report()
            
            if not report:
                logger.warning("No report data received")
                return []
            
            # The API returns a list directly
            if isinstance(report, list):
                employees = []
                for item in report:
                    employee = {
                        'id': str(item.get('id', '')),
                        'name': item.get('title', 'Unknown'),  # 'title' contains the employee name
                        'email': item.get('email', f"employee{len(employees)+1}@company.com"),
                        'status': 'active',
                        # Store raw data for debugging
                        '_raw_data': item
                    }
                    if employee['id']:  # Only add if we have an ID
                        employees.append(employee)
                        logger.debug(f"Found employee: {employee['name']} ({employee['id']})")
                
                logger.info(f"Extracted {len(employees)} employees from report")
                return employees
            else:
                logger.warning(f"Unexpected report format: {type(report)}")
                return []
            
        except Exception as e:
            logger.error(f"Error processing employees: {str(e)}")
            return []
    
    def get_weekly_summary(self, employee_id: str, start_date: datetime = None, end_date: datetime = None) -> Optional[Dict]:
        """
        Get weekly summary for an employee for the specified work week
        Returns dictionary with total_hours, days_worked, start_date, end_date
        """
        try:
            if start_date is None or end_date is None:
                start_date, end_date = self._get_previous_work_week()
            
            # Get the full report for the specified period
            report = self.get_employee_summary_report(start_date, end_date)
            
            if not report:
                logger.warning(f"No report data available for employee {employee_id}")
                return None
            
            # Find the employee in the report
            employee_data = None
            
            if isinstance(report, list):
                for item in report:
                    if str(item.get('id', '')) == str(employee_id):
                        employee_data = item
                        break
            
            if not employee_data:
                logger.warning(f"Employee {employee_id} not found in report for week {start_date.date()} to {end_date.date()}")
                return None
            
            # Extract hours from the data with multiple methods
            active_hours = self._extract_total_hours(employee_data)  # Now returns active hours (total - idle)
            idle_hours = self._extract_idle_hours(employee_data)
            original_total_hours = active_hours + idle_hours

            # Calculate actual working days in the period
            working_days = self._count_working_days(start_date, end_date)

            logger.debug(f"Employee {employee_id}: {active_hours:.2f} active hours (original: {original_total_hours:.2f}h, idle: {idle_hours:.2f}h) over {working_days} working days")

            return {
                'employee_id': employee_id,
                'total_hours': round(active_hours, 2),  # Now represents active hours for monitoring
                'original_total_hours': round(original_total_hours, 2),  # Original logged hours
                'idle_hours': round(idle_hours, 2),  # Idle time excluded
                'days_worked': working_days,
                'start_date': start_date.date(),
                'end_date': end_date.date(),
                'week_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'raw_data': employee_data  # Include for debugging
            }
            
        except Exception as e:
            logger.error(f"Error fetching weekly summary for {employee_id}: {str(e)}")
            return None
    
    def _extract_total_hours(self, employee_data: Dict) -> float:
        """
        Extract ACTIVE work hours from employee data (total hours minus idle time)
        This provides real working hours by excluding idle time for accurate monitoring
        """
        total_hours = 0
        idle_hours = 0

        try:
            # Method 0: Check for direct totalHours field (most reliable)
            if 'totalHours' in employee_data:
                total_hours = employee_data['totalHours']
                if isinstance(total_hours, (int, float)) and total_hours > 0:
                    logger.debug(f"Found totalHours: {total_hours:.2f} hours")

                    # Extract idle time to subtract from total
                    idle_hours = self._extract_idle_hours(employee_data)
                    active_hours = max(0, total_hours - idle_hours)

                    logger.info(f"📊 Hours calculation - Total: {total_hours:.2f}h, Idle: {idle_hours:.2f}h, Active: {active_hours:.2f}h")
                    return active_hours

            # Method 1: Check totChart for time data (most common)
            if 'totChart' in employee_data and isinstance(employee_data['totChart'], dict):
                for key, value in employee_data['totChart'].items():
                    if isinstance(value, (int, float)) and value > 0:
                        # Values in totChart are typically in seconds
                        total_hours += value / 3600  # Convert seconds to hours

                if total_hours > 0:
                    # Extract idle time to subtract from total
                    idle_hours = self._extract_idle_hours(employee_data)
                    active_hours = max(0, total_hours - idle_hours)

                    logger.info(f"📊 Hours calculation - Total: {total_hours:.2f}h, Idle: {idle_hours:.2f}h, Active: {active_hours:.2f}h")
                    return active_hours
            
            # Method 2: Check actChart for activity data
            if 'actChart' in employee_data and isinstance(employee_data['actChart'], dict):
                for key, value in employee_data['actChart'].items():
                    if isinstance(value, (int, float)) and value > 0:
                        # Convert seconds to hours
                        total_hours += value / 3600
                
                if total_hours > 0:
                    logger.debug(f"Extracted {total_hours:.2f} hours from actChart")
                    return total_hours
            
            # Method 3: Look for direct hour fields
            hour_fields = ['totalHours', 'total_hours', 'hoursWorked', 'totalTime', 'workTime', 'hours']
            for field in hour_fields:
                if field in employee_data:
                    value = employee_data[field]
                    if isinstance(value, (int, float)) and value > 0:
                        # Check if value is likely in seconds (> 1000) or hours
                        if value > 1000:
                            total_hours = value / 3600  # Convert seconds to hours
                        else:
                            total_hours = value  # Already in hours
                        
                        if total_hours > 0:
                            logger.debug(f"Extracted {total_hours:.2f} hours from {field}")
                            return total_hours
            
            # Method 4: Check for any time-related fields
            time_fields = ['time', 'duration', 'elapsed', 'worked']
            for field in time_fields:
                if field in employee_data:
                    value = employee_data[field]
                    if isinstance(value, (int, float)) and value > 0:
                        # Assume large values are in seconds
                        if value > 1000:
                            total_hours = value / 3600
                        else:
                            total_hours = value
                        
                        if total_hours > 0:
                            logger.debug(f"Extracted {total_hours:.2f} hours from {field}")
                            return total_hours
            
            # Method 5: Sum all reasonable numeric values (last resort)
            numeric_sum = 0
            for key, value in employee_data.items():
                if (isinstance(value, (int, float)) and 
                    value > 0 and 
                    key not in ['id', 'userId', 'timestamp', 'date'] and
                    not key.startswith('_')):
                    numeric_sum += value
            
            if numeric_sum > 1000:  # Likely in seconds
                total_hours = numeric_sum / 3600
                logger.debug(f"Extracted {total_hours:.2f} hours from numeric sum of all fields")
                return total_hours
            elif numeric_sum > 0:  # Likely in hours
                total_hours = numeric_sum
                logger.debug(f"Extracted {total_hours:.2f} hours from numeric sum (assuming hours)")
                return total_hours
            
            # Log available fields for debugging
            available_fields = list(employee_data.keys())
            logger.warning(f"Could not extract hours. Available fields: {available_fields}")
            
            # Check if there are any chart-like structures
            for key, value in employee_data.items():
                if isinstance(value, dict) and value:
                    logger.debug(f"Found dict field '{key}' with keys: {list(value.keys())}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Error extracting hours: {str(e)}")
            return 0

    def _extract_idle_hours(self, employee_data: Dict) -> float:
        """
        Extract idle time from employee data
        Returns idle hours that should be subtracted from total hours
        """
        idle_hours = 0

        try:
            # Method 1: Direct idleHours field (most reliable)
            if 'idleHours' in employee_data:
                value = employee_data['idleHours']
                if isinstance(value, (int, float)) and value >= 0:
                    idle_hours = value
                    logger.debug(f"Found idleHours: {idle_hours:.2f} hours")
                    return idle_hours

            # Method 2: Calculate from active/inactive seconds
            if ('activeSecondsCount' in employee_data and
                'inactiveSecondsCount' in employee_data and
                'totalSecondsCount' in employee_data):

                total_seconds = employee_data.get('totalSecondsCount', 0)
                inactive_seconds = employee_data.get('inactiveSecondsCount', 0)

                if total_seconds > 0 and inactive_seconds > 0:
                    # Calculate idle time as a portion of inactive time
                    # Use inactive seconds as idle time (conservative approach)
                    idle_hours = inactive_seconds / 3600
                    logger.debug(f"Calculated idle from seconds - Total: {total_seconds}s, Inactive: {inactive_seconds}s, Idle: {idle_hours:.2f}h")
                    return idle_hours

            # Method 3: Look for other idle-related fields
            idle_fields = ['idle_time', 'inactiveTime', 'inactive_time', 'breakTime', 'break_time']
            for field in idle_fields:
                if field in employee_data:
                    value = employee_data[field]
                    if isinstance(value, (int, float)) and value > 0:
                        # Convert seconds to hours if needed
                        idle_hours = value / 3600 if value > 1000 else value
                        logger.debug(f"Found idle time from {field}: {idle_hours:.2f} hours")
                        return idle_hours

            # Method 4: Check activity charts for idle indicators
            if 'actChart' in employee_data and isinstance(employee_data['actChart'], dict):
                chart_idle = 0
                for key, value in employee_data['actChart'].items():
                    key_lower = key.lower()
                    if any(indicator in key_lower for indicator in ['idle', 'inactive', 'break', 'away']):
                        if isinstance(value, (int, float)) and value > 0:
                            chart_idle += value / 3600 if value > 1000 else value

                if chart_idle > 0:
                    logger.debug(f"Found idle time from actChart: {chart_idle:.2f} hours")
                    return chart_idle

            logger.debug("No idle time data found - assuming 0 idle hours")
            return 0

        except Exception as e:
            logger.error(f"Error extracting idle hours: {str(e)}")
            return 0

    def _count_working_days(self, start_date: datetime, end_date: datetime) -> int:
        """
        Count actual working days (Monday-Friday) in the given period
        """
        working_days = 0
        current_date = start_date.date()
        end_date = end_date.date()
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                working_days += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def is_employee_active_this_week(self, employee_id: str) -> bool:
        """
        Check if employee was active (logged any hours) this week
        """
        try:
            weekly_data = self.get_weekly_summary(employee_id)
            return weekly_data is not None and weekly_data['total_hours'] > 0
        except Exception as e:
            logger.error(f"Error checking if employee {employee_id} is active: {str(e)}")
            return False
    
    def get_employee_details(self, employee_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific employee
        """
        try:
            employees = self.get_all_employees()
            for employee in employees:
                if employee['id'] == str(employee_id):
                    return employee
            
            logger.warning(f"Employee {employee_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting employee details for {employee_id}: {str(e)}")
            return None
    
    def validate_api_connection(self) -> bool:
        """
        Validate that the API connection is working
        """
        try:
            logger.info("Validating TeamLogger API connection...")
            
            # Test with a simple request
            test_start = datetime.now() - timedelta(days=1)
            test_end = datetime.now()
            
            report = self.get_employee_summary_report(test_start, test_end)
            
            if report is not None:
                logger.info("✅ TeamLogger API connection validated successfully")
                return True
            else:
                logger.error("❌ TeamLogger API connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ TeamLogger API validation failed: {str(e)}")
            return False
    
    def get_api_status(self) -> Dict:
        """
        Get status information about the API connection
        """
        try:
            start_time = time.time()
            
            # Test connection
            is_connected = self.validate_api_connection()
            
            # Get employee count
            employees = self.get_all_employees() if is_connected else []
            
            response_time = time.time() - start_time
            
            return {
                'connected': is_connected,
                'response_time_seconds': round(response_time, 2),
                'employee_count': len(employees),
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'base_url': self.base_url,
                'timestamp': datetime.now().isoformat()
            }
    
    def debug_employee_data(self, employee_id: str) -> Dict:
        """
        Get raw data for debugging purposes
        """
        try:
            report = self.get_employee_summary_report()
            
            if not report or not isinstance(report, list):
                return {'error': 'No report data available'}
            
            for item in report:
                if str(item.get('id', '')) == str(employee_id):
                    return {
                        'employee_id': employee_id,
                        'raw_data': item,
                        'available_fields': list(item.keys()),
                        'extracted_hours': self._extract_total_hours(item)
                    }
            
            return {'error': f'Employee {employee_id} not found in report'}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_work_week_hours_for_all(self) -> List[Dict]:
        """
        Get work week hours for all employees
        Useful for bulk processing and reporting
        """
        try:
            employees = self.get_all_employees()
            results = []
            
            work_week_start, work_week_end = self._get_previous_work_week()
            
            for employee in employees:
                try:
                    weekly_data = self.get_weekly_summary(employee['id'], work_week_start, work_week_end)
                    
                    result = {
                        'employee_id': employee['id'],
                        'employee_name': employee['name'],
                        'employee_email': employee['email'],
                        'hours_worked': weekly_data['total_hours'] if weekly_data else 0,
                        'working_days': weekly_data['days_worked'] if weekly_data else 0,
                        'period_start': work_week_start.date(),
                        'period_end': work_week_end.date(),
                        'data_available': weekly_data is not None
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing employee {employee['name']}: {str(e)}")
                    results.append({
                        'employee_id': employee['id'],
                        'employee_name': employee['name'],
                        'employee_email': employee['email'],
                        'hours_worked': 0,
                        'working_days': 0,
                        'period_start': work_week_start.date(),
                        'period_end': work_week_end.date(),
                        'data_available': False,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting work week hours for all employees: {str(e)}")
            return []