"""
Google Sheets API Client - For accessing multiple sheet tabs dynamically
This is the recommended approach for multi-month leave tracking
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from config.settings import Config
import os

logger = logging.getLogger(__name__)

class GoogleSheetsAPIClient:
    """Google Sheets API client using service account authentication"""
    
    def __init__(self):
        self.spreadsheet_id = self._extract_spreadsheet_id(Config.GOOGLE_SHEETS_ID)
        self.service = None
        self._sheet_cache = {}  # Cache to avoid hitting rate limits
        self._initialize_api()
        
    def _extract_spreadsheet_id(self, id_or_url: str) -> str:
        """Extract spreadsheet ID from either ID or full URL"""
        import re
        if '/' in id_or_url:
            match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', id_or_url)
            if match:
                return match.group(1)
        return id_or_url
    
    def _initialize_api(self):
        """Initialize Google Sheets API with service account credentials"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            import streamlit as st

            SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            credentials = None

            # Try to load from Streamlit secrets first (for Cloud deployment)
            try:
                if hasattr(st, 'secrets') and 'GOOGLE_SHEETS_CREDENTIALS' in st.secrets:
                    logger.info("Loading credentials from Streamlit secrets...")
                    creds_dict = dict(st.secrets['GOOGLE_SHEETS_CREDENTIALS'])
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict, scopes=SCOPES
                    )
                    logger.info("✅ Loaded credentials from Streamlit secrets")
            except Exception as e:
                logger.debug(f"Could not load from Streamlit secrets: {e}")

            # Fallback to file-based credentials (for local development)
            if not credentials:
                creds_file = getattr(Config, 'GOOGLE_SHEETS_CREDENTIALS_FILE', None)

                if not creds_file:
                    logger.warning("GOOGLE_SHEETS_CREDENTIALS_FILE not configured")
                    return

                if not os.path.exists(creds_file):
                    logger.warning(f"Credentials file not found: {creds_file}")
                    return

                logger.info(f"Loading credentials from file: {creds_file}")
                credentials = service_account.Credentials.from_service_account_file(
                    creds_file, scopes=SCOPES
                )
                logger.info("✅ Loaded credentials from file")

            # Build the service
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("✅ Google Sheets API initialized successfully")

        except ImportError:
            logger.error("Google Sheets API libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets API: {e}")
            import traceback
            traceback.print_exc()
    
    def get_sheet_data(self, sheet_name: str, use_cache: bool = True) -> List[List[str]]:
        """
        Fetch data from a specific sheet tab by name (with caching to avoid rate limits)

        Args:
            sheet_name: Name of the sheet tab (e.g., "Oct 25", "Sep 25")
            use_cache: Whether to use cached data (default: True)

        Returns:
            List of rows, where each row is a list of cell values
        """
        if not self.service:
            logger.error("Google Sheets API not initialized")
            return []

        # Check cache first
        if use_cache and sheet_name in self._sheet_cache:
            logger.debug(f"📦 Using cached data for '{sheet_name}'")
            return self._sheet_cache[sheet_name]

        try:
            # Request data from the sheet
            # Use A:BZ range to get all columns (up to 78 columns)
            range_name = f"'{sheet_name}'!A:BZ"

            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()

            values = result.get('values', [])

            if not values:
                logger.warning(f"No data found in sheet '{sheet_name}'")
                return []

            # Cache the result
            self._sheet_cache[sheet_name] = values
            logger.info(f"✅ Fetched {len(values)} rows from '{sheet_name}' (API) - cached")
            return values

        except Exception as e:
            logger.error(f"Error fetching sheet '{sheet_name}': {e}")
            return []

    def _fetch_sheet_data(self, sheet_name: str, force_refresh: bool = False) -> List[List[str]]:
        """Alias for get_sheet_data for backward compatibility"""
        # If force_refresh is True, bypass cache
        use_cache = not force_refresh
        return self.get_sheet_data(sheet_name, use_cache=use_cache)

    def clear_cache(self):
        """Clear the sheet data cache"""
        self._sheet_cache = {}
        logger.info("🗑️ Sheet cache cleared")

    def is_available(self) -> bool:
        """Check if the Google Sheets API is available and initialized"""
        return self.service is not None
    
    def get_employee_leaves(self, employee_name: str, start_date: datetime,
                          end_date: datetime, force_refresh: bool = True) -> List[Dict]:
        """
        Get employee leave records for a date range
        
        Args:
            employee_name: Name of the employee
            start_date: Start date of the period
            end_date: End date of the period
            
        Returns:
            List of leave records with start_date, end_date, leave_type
        """
        leaves = []
        
        # Determine which months to check
        current_date = start_date
        months_to_check = set()
        
        while current_date <= end_date:
            month_name = current_date.strftime("%b %y")  # e.g., "Oct 25"
            months_to_check.add(month_name)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        # Check each month
        for month_name in months_to_check:
            sheet_data = self.get_sheet_data(month_name)
            
            if not sheet_data or len(sheet_data) < 2:
                continue
            
            # Find employee row
            employee_row = None
            for i, row in enumerate(sheet_data[1:], start=1):  # Skip header
                if row and len(row) > 0:
                    name = str(row[0]).strip()
                    if name.lower() == employee_name.lower():
                        employee_row = row
                        break
            
            if not employee_row:
                continue
            
            # Parse leave data from the row
            header_row = sheet_data[0]
            
            for col_idx, cell_value in enumerate(employee_row[1:], start=1):  # Skip name column
                if col_idx >= len(header_row):
                    break
                
                day_str = str(header_row[col_idx]).strip()
                
                # Try to parse day number
                try:
                    day = int(day_str)
                except (ValueError, TypeError):
                    continue
                
                # Construct the date
                month = datetime.strptime(month_name, "%b %y").month
                year = datetime.strptime(month_name, "%b %y").year
                
                try:
                    leave_date = datetime(year, month, day)
                except ValueError:
                    continue
                
                # Check if date is in range
                if not (start_date <= leave_date <= end_date):
                    continue
                
                # Check if there's a leave on this day
                cell_str = str(cell_value).strip().lower()
                
                if cell_str and cell_str not in ['', '0', 'p', 'present']:
                    # Determine leave type
                    leave_type = "Leave"
                    
                    if 'holiday' in cell_str:
                        leave_type = "Holiday"
                    elif 'half' in cell_str or '0.5' in cell_str:
                        leave_type = "Half Day Leave"
                    elif 'weekend' in cell_str:
                        leave_type = "Weekend"
                    elif 'leave' in cell_str or 'l' == cell_str:
                        leave_type = "Leave"
                    
                    leaves.append({
                        'start_date': leave_date,
                        'end_date': leave_date,
                        'leave_type': leave_type,
                        'employee_name': employee_name
                    })
        
        return leaves
    
    def is_available(self) -> bool:
        """Check if API is properly initialized"""
        return self.service is not None

