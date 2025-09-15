import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config.settings import Config
import requests
import csv
from io import StringIO
import urllib.parse
import re
import time
import random

logger = logging.getLogger(__name__)

class GoogleSheetsLeaveClient:
    def __init__(self):
        self.spreadsheet_id = self._extract_spreadsheet_id(Config.GOOGLE_SHEETS_ID)
        self.gid = self._extract_gid_from_url()
        self._session = requests.Session()
        
        logger.info(f"Google Sheets client initialized - Real-Time Mode")
        logger.info(f"Spreadsheet ID: {self.spreadsheet_id}")
        if self.gid:
            logger.info(f"GID: {self.gid}")
    
    def _extract_spreadsheet_id(self, id_or_url: str) -> str:
        """Extract spreadsheet ID from either ID or full URL"""
        if '/' in id_or_url:
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', id_or_url)
            if match:
                return match.group(1)
        return id_or_url
    
    def _extract_gid_from_url(self) -> Optional[str]:
        """Extract GID (sheet ID) from the URL if provided"""
        if hasattr(Config, 'GOOGLE_SHEETS_URL') and Config.GOOGLE_SHEETS_URL:
            match = re.search(r'[#&]gid=(\d+)', Config.GOOGLE_SHEETS_URL)
            if match:
                return match.group(1)
        return None
    
    def _get_sheet_csv_url(self, sheet_name: str) -> Tuple[str, str]:
        """Generate CSV export URLs with cache busting - FIXED to fetch full range"""
        timestamp = int(time.time() * 1000000)
        random_id = random.randint(100000, 999999)

        encoded_sheet_name = urllib.parse.quote(sheet_name)

        # FIXED: Try different approaches to get full sheet data
        # Standard GVIZ URL (may truncate)
        gviz_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}&ts={timestamp}&rnd={random_id}"

        # FIXED: Use export URL which should get full sheet data
        export_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid={self.gid}&ts={timestamp}" if self.gid else None

        # Alternative: Try published CSV URL if available
        published_url = None
        if hasattr(Config, 'GOOGLE_SHEETS_PUBLISHED_CSV_URL') and Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL:
            published_url = f"{Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL}&ts={timestamp}"

        return gviz_url, export_url, published_url
    
    def _fetch_sheet_data(self, sheet_name: str, force_refresh: bool = True) -> List[List[str]]:
        """Fetch sheet data - try multiple approaches"""
        logger.info(f"Fetching real-time data for sheet '{sheet_name}'")
        
        # Try multiple sheet name formats
        sheet_variations = [
            sheet_name,  # June 25
            sheet_name.replace(" ", "%20"),  # June%2025
            sheet_name.lower(),  # june 25
            sheet_name.upper(),  # JUNE 25
        ]
        
        headers = {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'User-Agent': f'EmployeeMonitor/{Config.APP_VERSION}'
        }
        
        # Close existing session
        self._session.close()
        self._session = requests.Session()
        
        # FIXED: Try published CSV URL first (gets ALL columns - up to 35 for safety)
        if hasattr(Config, 'GOOGLE_SHEETS_PUBLISHED_CSV_URL') and Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL:
            try:
                # Force fetch ALL columns by adding range parameter
                base_url = Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL
                # Add range to get columns A through AI (35 columns) to ensure we get all month days
                published_url = f"{base_url}&range=A:AI&ts={int(time.time() * 1000)}"
                logger.debug(f"Trying published CSV URL with full range: {published_url}")

                response = self._session.get(published_url, timeout=30, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    csv_data = StringIO(content)
                    reader = csv.reader(csv_data)
                    data = list(reader)

                    if data and len(data) > 1:
                        logger.info(f"Successfully fetched {len(data)} rows with {len(data[0])} columns using published CSV with range")
                        return data
            except Exception as e:
                logger.warning(f"Published CSV with range failed: {e}")

        # Fallback: Try published URL without range
        if hasattr(Config, 'GOOGLE_SHEETS_PUBLISHED_CSV_URL') and Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL:
            try:
                published_url = f"{Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL}&ts={int(time.time() * 1000)}"
                logger.debug(f"Trying published CSV URL (fallback): {published_url}")

                response = self._session.get(published_url, timeout=30, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    csv_data = StringIO(content)
                    reader = csv.reader(csv_data)
                    data = list(reader)

                    if data and len(data) > 1:
                        logger.info(f"Successfully fetched {len(data)} rows with {len(data[0])} columns using published CSV (fallback)")
                        return data
            except Exception as e:
                logger.warning(f"Published CSV fallback failed: {e}")

        # Try with GID if available (fallback)
        if self.gid:
            try:
                url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid={self.gid}"
                logger.debug(f"Trying GID-based URL: {url}")

                response = self._session.get(url, timeout=30, headers=headers)
                if response.status_code == 200:
                    content = response.text
                    csv_data = StringIO(content)
                    reader = csv.reader(csv_data)
                    data = list(reader)

                    if data:
                        logger.info(f"Successfully fetched {len(data)} rows using GID")
                        return data
            except Exception as e:
                logger.warning(f"GID fetch failed: {e}")
        
        # Try with sheet name variations
        for sheet_var in sheet_variations:
            try:
                gviz_url, export_url, published_url = self._get_sheet_csv_url(sheet_var)

                # FIXED: Try published URL first (most complete data), then export, then gviz
                for url_name, url in [("Published", published_url), ("Export", export_url), ("GVIZ", gviz_url)]:
                    if not url:
                        continue
                        
                    logger.debug(f"Trying URL: {url}")
                    response = self._session.get(url, timeout=30, headers=headers)
                    
                    if response.status_code == 200:
                        content = response.text
                        csv_data = StringIO(content)
                        reader = csv.reader(csv_data)
                        data = list(reader)
                        
                        if data:
                            logger.info(f"Successfully fetched {len(data)} rows from '{sheet_var}'")
                            return data
            except Exception as e:
                logger.debug(f"Error with {sheet_var}: {e}")
                continue
        
        logger.error(f"Could not fetch sheet data after all attempts")
        return []
    
    def get_employee_leaves(self, employee_name: str, start_date: datetime, end_date: datetime, 
                          force_refresh: bool = True) -> List[Dict]:
        """Get employee leave records with better matching"""
        try:
            all_leaves = []
            processed_months = set()
            
            current_date = start_date
            while current_date <= end_date:
                month_key = (current_date.year, current_date.month)
                
                if month_key not in processed_months:
                    processed_months.add(month_key)
                    
                    # Try different sheet name formats - PRIORITIZE "Sep 25" format
                    sheet_names = [
                        current_date.strftime("%b %y"),      # Sep 25 (PRIORITY - has actual leave data)
                        current_date.strftime("%B %y"),      # September 25
                        current_date.strftime("%B %Y"),      # September 2025
                        current_date.strftime("%B_%y"),      # September_25
                        current_date.strftime("%B-%y"),      # September-25
                    ]
                    
                    sheet_data = []
                    for sheet_name in sheet_names:
                        sheet_data = self._fetch_sheet_data(sheet_name, force_refresh=True)
                        if sheet_data:
                            logger.info(f"Found data with sheet name: {sheet_name}")
                            break
                    
                    if sheet_data and len(sheet_data) > 1:
                        leaves = self._extract_leaves_with_half_days(
                            sheet_data, 
                            employee_name, 
                            current_date.year, 
                            current_date.month,
                            start_date,
                            end_date
                        )
                        all_leaves.extend(leaves)
                    else:
                        logger.warning(f"No data found for {current_date.strftime('%B %Y')}")
                
                current_date += timedelta(days=1)
            
            logger.info(f"Total leaves found for {employee_name}: {len(all_leaves)}")
            return all_leaves
            
        except Exception as e:
            logger.error(f"Error fetching leaves for {employee_name}: {str(e)}")
            return []
    
    def _extract_leaves_with_half_days(self, sheet_data: List[List[str]], employee_name: str, 
                                     year: int, month: int, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Extract leave data with improved matching"""
        leaves = []
        
        if not sheet_data or len(sheet_data) < 2:
            return leaves
        
        # Debug: Print first few rows to see structure
        logger.debug(f"Sheet has {len(sheet_data)} rows")
        for i in range(min(5, len(sheet_data))):
            if sheet_data[i] and len(sheet_data[i]) > 0:
                logger.debug(f"Row {i}: {sheet_data[i][0]}")
        
        # Find employee row - improved matching
        employee_row_idx = None
        employee_name_lower = employee_name.strip().lower()
        employee_parts = employee_name_lower.split()
        
        for idx, row in enumerate(sheet_data):
            if not row or len(row) == 0:
                continue
                
            cell_name = str(row[0]).strip().lower()
            
            # Exact match
            if employee_name_lower == cell_name:
                employee_row_idx = idx
                logger.info(f"Found exact match for {employee_name} at row {idx}")
                break
            
            # Check if all parts of employee name are in cell
            if all(part in cell_name for part in employee_parts if len(part) > 2):
                employee_row_idx = idx
                logger.info(f"Found partial match for {employee_name} at row {idx}: {row[0]}")
                break
            
            # Check reverse (cell parts in employee name)
            cell_parts = cell_name.split()
            if all(part in employee_name_lower for part in cell_parts if len(part) > 2):
                employee_row_idx = idx
                logger.info(f"Found reverse match for {employee_name} at row {idx}: {row[0]}")
                break
        
        if employee_row_idx is None:
            logger.warning(f"Employee '{employee_name}' not found in sheet. Available names: {[row[0] for row in sheet_data[:20] if row and len(row) > 0]}")
            return leaves
        
        employee_row = sheet_data[employee_row_idx]
        logger.debug(f"Processing row for {employee_name}: {employee_row[:10] if len(employee_row) > 10 else employee_row}")
        
        # Process each day (columns 1-31)
        for day in range(1, 32):
            try:
                try:
                    current_day = datetime(year, month, day)
                except ValueError:
                    continue
                
                if current_day < start_date or current_day > end_date:
                    continue
                
                # Skip weekends when counting leaves
                if current_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    continue
                
                # Get cell value
                cell_value = ""
                if day < len(employee_row):
                    cell_value = str(employee_row[day]).strip()
                
                # Check if it's a leave
                if self._is_leave_cell(cell_value):
                    is_half_day = self._is_half_day_leave(cell_value)
                    leave_type = self._get_leave_type(cell_value, is_half_day)
                    
                    leaves.append({
                        'employee_name': employee_name,
                        'start_date': current_day,
                        'end_date': current_day,
                        'leave_type': leave_type,
                        'status': 'Approved',
                        'days_count': 0.5 if is_half_day else 1.0,
                        'is_half_day': is_half_day
                    })
                    
                    logger.debug(f"{employee_name} - {current_day.strftime('%Y-%m-%d')}: {leave_type} ({cell_value})")
                    
            except Exception as e:
                logger.warning(f"Error processing day {day}: {str(e)}")
                continue
        
        return leaves
    
    def _is_leave_cell(self, cell_value: str) -> bool:
        """Enhanced leave detection"""
        if not cell_value:
            return False
        
        cell_lower = cell_value.lower().strip()
        
        # Empty or working indicators
        if cell_lower in ["", "-", ".", "na", "n/a", "nil", "working", "present", "p", "0", "w/o", "wo"]:
            return False
        
        # Weekend is NOT a leave (it's already excluded from working days)
        if cell_lower in ["weekend", "week end", "sat", "sun", "saturday", "sunday"]:
            return False
        
        # Definite leave indicators
        leave_indicators = [
            "leave", "holiday", "vacation", "sick", "personal", "casual", "earned",
            "comp off", "compoff", "co", "wfh", "work from home", "cl", "sl", "pl", "el", 
            "medical", "emergency", "half", "0.5", "½", "maternity", "paternity", 
            "annual", "privilege", "bereavement", "marriage", "study",
            "sick leave", "casual leave", "personal leave", "earned leave",
            "half sick leave", "half day", "half cl", "half sl"
        ]
        
        # Check if any leave indicator is present
        for indicator in leave_indicators:
            if indicator in cell_lower:
                return True
        
        # Check for patterns like "CL", "SL", "PL", "EL" (uppercase)
        if re.match(r'^(CL|SL|PL|EL|CO)$', cell_value.strip(), re.IGNORECASE):
            return True
        
        return False
    
    def _is_half_day_leave(self, cell_value: str) -> bool:
        """Check if it's a half-day leave"""
        cell_lower = cell_value.lower().strip()
        
        half_day_indicators = [
            "half", "0.5", "½", "1/2", "partial", 
            "half day", "half-day", "hd", "h.d",
            "morning leave", "afternoon leave", "short leave",
            "half sick", "half cl", "half sl", "half casual"
        ]
        
        return any(indicator in cell_lower for indicator in half_day_indicators)
    
    def _get_leave_type(self, cell_value: str, is_half_day: bool) -> str:
        """Get normalized leave type"""
        cell_lower = cell_value.lower()
        
        prefix = "Half Day " if is_half_day else ""
        
        if "casual" in cell_lower or re.search(r'\bcl\b', cell_lower, re.IGNORECASE):
            return f"{prefix}Casual Leave"
        elif "sick" in cell_lower or re.search(r'\bsl\b', cell_lower, re.IGNORECASE):
            return f"{prefix}Sick Leave"
        elif "earned" in cell_lower or re.search(r'\bel\b', cell_lower, re.IGNORECASE):
            return f"{prefix}Earned Leave"
        elif "personal" in cell_lower or re.search(r'\bpl\b', cell_lower, re.IGNORECASE):
            return f"{prefix}Personal Leave"
        elif "comp" in cell_lower or re.search(r'\bco\b', cell_lower, re.IGNORECASE):
            return f"{prefix}Comp Off"
        elif "medical" in cell_lower:
            return f"{prefix}Medical Leave"
        elif "wfh" in cell_lower or "work from home" in cell_lower:
            return f"{prefix}Work From Home"
        else:
            return f"{prefix}Leave"
    
    def get_approved_leaves_count(self, employee_name: str, start_date: datetime, end_date: datetime) -> float:
        """Get count of approved leave days with half-day support"""
        try:
            leaves = self.get_employee_leaves(employee_name, start_date, end_date, force_refresh=True)
            total_leave_days = 0.0
            
            for leave in leaves:
                # Only count working days (Mon-Fri)
                if leave['start_date'].weekday() < 5:
                    total_leave_days += leave.get('days_count', 1.0)
            
            logger.info(f"{employee_name}: {total_leave_days} working day leaves (real-time)")
            return total_leave_days
            
        except Exception as e:
            logger.error(f"Error calculating leave days for {employee_name}: {str(e)}")
            return 0.0
    
    def validate_google_sheets_connection(self) -> Dict:
        """Validate the Google Sheets connection"""
        try:
            logger.info("Validating Google Sheets access...")
            
            # Try current month - use "Sep 25" format first
            test_sheet_name = datetime.now().strftime("%b %y")  # Sep 25 format
            test_data = self._fetch_sheet_data(test_sheet_name)
            
            if test_data:
                # Find some employee names
                employee_names = []
                for row in test_data[1:10]:  # Skip header, check first 10 rows
                    if row and len(row) > 0 and row[0].strip():
                        employee_names.append(row[0].strip())
                
                return {
                    'status': 'success',
                    'message': 'Google Sheets access successful',
                    'spreadsheet_id': self.spreadsheet_id,
                    'gid': self.gid,
                    'test_sheet': test_sheet_name,
                    'rows_found': len(test_data),
                    'sample_employees': employee_names[:5],
                    'mode': 'Real-Time',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': 'Could not fetch sheet data. Check sheet name format or permissions.',
                    'spreadsheet_id': self.spreadsheet_id,
                    'test_sheet': test_sheet_name,
                    'timestamp': datetime.now().isoformat()
                }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def debug_employee_leave_detection(self, employee_name: str, year: int = None, month: int = None) -> Dict:
        """Debug method to check leave detection for a specific employee"""
        try:
            if not year:
                year = datetime.now().year
            if not month:
                month = datetime.now().month
            
            # Try to fetch the sheet - PRIORITIZE "Sep 25" format
            sheet_names = [
                datetime(year, month, 1).strftime("%b %y"),      # Sep 25 (PRIORITY)
                datetime(year, month, 1).strftime("%B %y"),      # September 25
                datetime(year, month, 1).strftime("%B %Y"),      # September 2025
            ]
            
            sheet_data = []
            used_sheet_name = None
            for sheet_name in sheet_names:
                sheet_data = self._fetch_sheet_data(sheet_name)
                if sheet_data:
                    used_sheet_name = sheet_name
                    break
            
            if not sheet_data:
                return {'error': f'No sheet data found for {year}-{month:02d}'}
            
            # Find employee
            employee_row_idx = None
            employee_name_lower = employee_name.strip().lower()
            
            for idx, row in enumerate(sheet_data):
                if row and len(row) > 0:
                    if employee_name_lower in row[0].strip().lower():
                        employee_row_idx = idx
                        break
            
            if employee_row_idx is None:
                available_names = [row[0] for row in sheet_data[:20] if row and len(row) > 0]
                return {
                    'error': f'Employee {employee_name} not found',
                    'sheet_used': used_sheet_name,
                    'available_names': available_names
                }
            
            # Analyze leaves
            employee_row = sheet_data[employee_row_idx]
            leave_analysis = []
            
            for day in range(1, min(32, len(employee_row))):
                if day < len(employee_row):
                    cell_value = str(employee_row[day]).strip()
                    if cell_value and self._is_leave_cell(cell_value):
                        leave_analysis.append({
                            'day': day,
                            'cell_value': cell_value,
                            'is_half_day': self._is_half_day_leave(cell_value),
                            'leave_type': self._get_leave_type(cell_value, self._is_half_day_leave(cell_value))
                        })
            
            total_leaves = sum(0.5 if l['is_half_day'] else 1.0 for l in leave_analysis)
            
            return {
                'employee_name': employee_name,
                'sheet_used': used_sheet_name,
                'found_at_row': employee_row_idx,
                'employee_row_data': employee_row[:10],
                'leave_days_found': leave_analysis,
                'total_leave_days': total_leaves
            }
            
        except Exception as e:
            return {'error': str(e)}