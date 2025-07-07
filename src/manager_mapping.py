"""
Manager Mapping Module - Dynamic Google Sheets Integration
Maps employees to their reporting managers for CC in email alerts
Data is fetched dynamically from Google Sheets
"""

import logging
import requests
import csv
import re
import time
import random
import urllib.parse
from io import StringIO
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Manager Mapping Google Sheet Configuration
MANAGER_MAPPING_SPREADSHEET_ID = "1hqj2whB7bH0aoDeNV-ORIl_5dXX0eHcglhabW9xeVt8"
MANAGER_MAPPING_SHEET_NAME = "Sheet1"  # Default sheet name, can be updated if needed

# IMPORTANT: To use Google Sheets integration, the sheet must be publicly accessible
# Steps to make the sheet public:
# 1. Open the Google Sheet
# 2. Click "Share" button (top right)
# 3. Click "Change to anyone with the link"
# 4. Set permission to "Viewer"
# 5. Click "Done"
#
# Expected sheet format:
# Column A: Employee Name
# Column B: Manager Name
# Column C: Manager Email (optional)
#
# Example:
# Employee Name    | Manager Name      | Manager Email
# Kartik Jain      | Prasanjit Dey     | pd@rapidinnovation.io
# Gokul Jagannath  | Shailesh Kala     | sk@rapidinnovation.dev

class GoogleSheetsManagerClient:
    """Client for fetching manager mapping data from Google Sheets"""

    def __init__(self):
        self.spreadsheet_id = MANAGER_MAPPING_SPREADSHEET_ID
        self.sheet_name = MANAGER_MAPPING_SHEET_NAME
        self._session = requests.Session()
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = 300  # 5 minutes cache

        logger.info(f"Manager mapping client initialized for spreadsheet: {self.spreadsheet_id}")

    def _get_sheet_csv_urls(self) -> List[str]:
        """Generate multiple CSV export URLs to try"""
        timestamp = int(time.time() * 1000000)
        random_id = random.randint(100000, 999999)

        urls = []

        # Method 1: gviz with sheet name
        encoded_sheet_name = urllib.parse.quote(self.sheet_name)
        gviz_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}&ts={timestamp}&rnd={random_id}"
        urls.append(gviz_url)

        # Method 2: export with gid=0 (first sheet)
        export_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv&gid=0&ts={timestamp}"
        urls.append(export_url)

        # Method 3: gviz without sheet name (gets first sheet)
        gviz_simple = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/gviz/tq?tqx=out:csv&ts={timestamp}&rnd={random_id}"
        urls.append(gviz_simple)

        return urls

    def _fetch_manager_data(self) -> List[List[str]]:
        """Fetch manager mapping data from Google Sheets"""
        try:
            logger.info("Fetching manager mapping data from Google Sheets...")

            headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'User-Agent': 'EmployeeMonitor/4.0.0'
            }

            # Close existing session and create new one
            self._session.close()
            self._session = requests.Session()

            # Try multiple URLs
            urls = self._get_sheet_csv_urls()

            for i, url in enumerate(urls):
                try:
                    logger.info(f"Trying URL {i+1}/{len(urls)}: {url[:100]}...")
                    response = self._session.get(url, timeout=30, headers=headers)

                    if response.status_code == 200:
                        content = response.text.strip()
                        if content and not content.startswith('<!DOCTYPE') and not content.startswith('<html'):
                            logger.info(f"Successfully fetched data using URL {i+1}")

                            # Parse CSV content
                            csv_data = StringIO(content)
                            reader = csv.reader(csv_data)
                            data = list(reader)

                            if data and len(data) > 1:  # Has header and data
                                logger.info(f"Parsed {len(data)-1} data rows from sheet")
                                return data
                            else:
                                logger.warning(f"URL {i+1} returned empty or invalid data")
                        else:
                            logger.warning(f"URL {i+1} returned HTML instead of CSV")
                    else:
                        logger.warning(f"URL {i+1} returned status code: {response.status_code}")

                except requests.RequestException as e:
                    logger.warning(f"URL {i+1} failed with error: {e}")
                    continue

            logger.error("All URLs failed to fetch data")
            return []

        except Exception as e:
            logger.error(f"Error fetching manager mapping data: {str(e)}")
            return []

    def _parse_manager_data(self, raw_data: List[List[str]]) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Parse raw CSV data into manager mappings and email mappings"""
        reporting_managers = {}
        manager_emails = {}

        if not raw_data or len(raw_data) < 2:
            logger.warning("Insufficient data in manager mapping sheet")
            return reporting_managers, manager_emails

        # Assume first row is header
        headers = [col.strip().lower() for col in raw_data[0]]
        logger.info(f"Manager mapping sheet headers: {headers}")

        # Find column indices based on expected Google Sheet format
        # Expected: Name, Email ID, Reporting Manager, Manager Mail ID
        employee_col = None
        employee_email_col = None
        manager_col = None
        manager_email_col = None

        for i, header in enumerate(headers):
            header_clean = header.replace(' ', '').lower()
            if header_clean == 'name' or 'employee' in header:
                employee_col = i
            elif header_clean == 'emailid' or 'email' in header:
                employee_email_col = i
            elif 'reporting' in header or header_clean == 'reportingmanager':
                manager_col = i
            elif 'manager' in header and 'mail' in header:
                manager_email_col = i

        # Fallback to positional based on actual Google Sheet structure
        # Name(0), Empty(1), Email ID(2), Reporting Manager(3), Manager Mail ID(4)
        if len(headers) >= 5 and (employee_col is None or manager_col is None):
            logger.info("Using positional column mapping based on Google Sheet structure")
            employee_col = 0  # Name
            employee_email_col = 2  # Email ID (skipping empty column 1)
            manager_col = 3  # Reporting Manager
            manager_email_col = 4  # Manager Mail ID

        if employee_col is None or manager_col is None:
            logger.error("Could not find employee and manager columns in the sheet")
            return reporting_managers, manager_emails

        logger.info(f"Using columns - Employee: {employee_col}, Manager: {manager_col}, ManagerEmail: {manager_email_col}")

        # Parse data rows
        for row_idx, row in enumerate(raw_data[1:], start=2):
            try:
                if len(row) <= max(employee_col, manager_col):
                    continue

                employee_name = row[employee_col].strip() if employee_col < len(row) else ""
                employee_email = row[employee_email_col].strip() if employee_email_col is not None and employee_email_col < len(row) else ""
                manager_name = row[manager_col].strip() if manager_col < len(row) else ""

                if employee_name and manager_name:
                    # Use employee email as key if available, otherwise use name
                    key = employee_email if employee_email else employee_name
                    reporting_managers[key] = manager_name
                    logger.debug(f"Mapped: {key} ({employee_name}) -> {manager_name}")

                # Store manager email if available
                if manager_email_col is not None and manager_email_col < len(row):
                    manager_email = row[manager_email_col].strip()
                    if manager_name and manager_email and '@' in manager_email:
                        manager_emails[manager_name] = manager_email
                        logger.debug(f"Manager email: {manager_name} -> {manager_email}")

            except Exception as e:
                logger.warning(f"Error parsing row {row_idx}: {str(e)}")
                continue

        logger.info(f"Parsed {len(reporting_managers)} employee-manager mappings")
        logger.info(f"Parsed {len(manager_emails)} manager email mappings")

        return reporting_managers, manager_emails

    def get_manager_mappings(self, force_refresh: bool = False) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Get manager mappings with caching"""
        current_time = time.time()

        # Check cache
        if (not force_refresh and
            self._cache_timestamp and
            current_time - self._cache_timestamp < self._cache_duration and
            'reporting_managers' in self._cache and
            'manager_emails' in self._cache):

            logger.debug("Using cached manager mapping data")
            return self._cache['reporting_managers'], self._cache['manager_emails']

        # Fetch fresh data
        raw_data = self._fetch_manager_data()
        reporting_managers, manager_emails = self._parse_manager_data(raw_data)

        # Update cache
        self._cache = {
            'reporting_managers': reporting_managers,
            'manager_emails': manager_emails
        }
        self._cache_timestamp = current_time

        return reporting_managers, manager_emails

# Global client instance
_manager_client = None

def _get_manager_client() -> GoogleSheetsManagerClient:
    """Get or create the global manager client instance"""
    global _manager_client
    if _manager_client is None:
        _manager_client = GoogleSheetsManagerClient()
    return _manager_client

def _get_current_mappings() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Get current manager mappings from Google Sheets"""
    try:
        client = _get_manager_client()
        return client.get_manager_mappings()
    except Exception as e:
        logger.error(f"Error getting manager mappings: {str(e)}")
        return {}, {}

# Legacy manual mappings as fallback (will be removed after Google Sheets integration is confirmed working)
_FALLBACK_REPORTING_MANAGERS: Dict[str, str] = {
    # Employee Name: Reporting Manager (fallback data)
    'Aakash Kumar': 'Abhijeet Sonaje',
    'Aayush Limbbad': 'Neeraj Deshpande',
    'Abhijeet Sonaje': 'Abhijeet Sonaje',
    'Abhishek Negi': 'Hitesh Goyal',
    'Abhishek Ajayan': 'Jesse Anglen',
    'Adarsh Bajpai': 'Neeraj Deshpande',
    'Aditya Bisht': 'Aditya Bisht',
    'Aditya Singh': 'Abhijeet Sonaje',
    'Akshit Gupta': 'Prasanjit Dey',
    'Aman Kale': 'Abhijeet Sonaje',
    'Aman Rao': 'Shailesh Kala',
    'Amar Kant Yadav': 'Abhijeet Sonaje',
    'Anubhav Bhatt': 'Neeraj Deshpande',
    'Apoorv Nag': 'Abhijeet Sonaje',
    'Arsh': 'Neeraj Deshpande',
    'Arunima Ray': 'Jesse Anglen',
    'Ashique Mohammed C': 'Neeraj Deshpande',
    'Ashutosh Vatsya': 'Shailesh Kala',
    'Debi Prasad Mishra': 'Shailesh Kala',
    'Deepak Lal CK': 'Shailesh Kala',
    'Dravid Sajinraj J': 'Abhijeet Sonaje',
    'Gokul Jagannath': 'Shailesh Kala',
    'Gopal Arjunrao Mate': 'Shailesh Kala',
    'Harshit Sharma': 'Aditya Bisht',
    'Harshit Gupta': 'Abhijeet Sonaje',
    'Himanshu Yadav': 'Prasanjit Dey',
    'Himanshu Devrani': 'Abhijeet Sonaje',
    'Istekhar Khan': 'Prasanjit Dey',
    'Jeetanshu Srivastava': 'Prasanjit Dey',
    'Arti Padiyar': 'Rajnikant Sonvane',
    'Kajol Jaiswal': 'Neeraj Deshpande',
    'Kartik Jain': 'Prasanjit Dey',
    'Kashish': 'Shailesh Kala',
    'Kesavan Manokar': 'Prasanjit Dey',
    'Kevin Pinto': 'Neeraj Deshpande',
    'Kishan Sahu': 'Hitesh Goyal',
    'Komal Kumari': 'Prasanjit Dey',
    'Krishnakanth Ankam': 'Abhijeet Sonaje',
    'Kunwar Siddharth Thakur': 'Aditya Bisht',
    'Kushagra Gupta': 'Abhijeet Sonaje',
    'Madhav Gupta': 'Prasanjit Dey',
    'Mayank Parashar': 'Hitesh Goyal',
    'Mayank Mittal': 'Shailesh Kala',
    'Mohamed Aleem': 'Rajnikant Sonvane',
    'MOHAN CHAUDHARI': 'Abhijeet Sonaje',
    'Arbaz Khan': 'Hitesh Goyal',
    'Naman Nagi': 'Shailesh Kala',
    'Namit Jain': 'Hitesh Goyal',
    'Neeraj Deshpande': 'Jesse Anglen',
    'Nekhlesh Singh Sajwan': 'Tyson Faulkner',
    'Nihal H Adoni': 'Tyson Faulkner',
    'Nikhil Patil': 'Jeetanshu',
    'Nitin Singh': 'Shailesh Kala',
    'Pavan S N': 'Abhijeet Sonaje',
    'Pillai Satish': 'Aditya Bisht',
    'Prashanth Manda': 'Rajnikant Sonvane',
    'Pratham Agarwal': 'Prasanjit Dey',
    'Pratik Kumar': 'Prasanjit Dey',
    'Pratyush Nag': 'Prasanjit Dey',
    'Priya Bhadauria': 'Neeraj Deshpande',
    'Punesh Ramrao Borkar': 'Shailesh Kala',
    'Rajnikant Sonvane': 'Jesse Anglen',
    'Rana Munshi': 'Abhijeet Sonaje',
    'Ranjith Nair': 'Hitesh Goyal',
    'Rishabh Kala': 'Shailesh Kala',
    'Wajid Pariyani':  'Tyson Faulkner',
    'Ritwik Rohitashwa': 'Aditya Bisht',
    'Sai Charan': 'Rajnikant Sonvane',
    'Shalu Yadav': 'Hitesh Goyal',
    'Shaurya Singh': 'Shailesh Kala',
    'Shivam Rajput': 'Prasanjit Dey',
    'Shobhit Vishnoi': 'Shailesh Kala',
    'Shreya Singh': 'Aditya Bisht',
    'Shruti Agarwal': 'Prasanjit Dey',
    'Shruti Kamble': 'Neeraj Deshpande',
    'Shwetha Vasanth Kamath': 'Shailesh Kala',
    'Sourav Suman': 'Hitesh Goyal',
    'Sumit Guha': 'Hitesh Goyal',
    'Sunishtha Rajput': 'Neeraj Deshpande',
    'Sunny Singha': 'Shailesh Kala',
    'Sushil Baburao Khatke': 'Shailesh Kala',
    'Tushar Garg': 'Abhijeet Sonaje',
    'Ujjwal Paliwal': 'Tyson Faulkner',
    'Vaibhav Chandolia': 'Abhijeet Sonaje',
    'Varnita Saxena': 'Neeraj Deshpande',
    'Vipin Yadav': 'Tyson Faulkner',
    'Yaoreichan Ramshang': 'Rajnikant Sonvane',
    'Arvind Kumar': 'Himanshu Yadav',
}

# Fallback manager email mapping (used when Google Sheets doesn't have email data)
_FALLBACK_MANAGER_EMAILS: Dict[str, str] = {
    'Abhijeet Sonaje': 'abhijeet@rapidinnovation.dev',
    'Aditya Bisht': 'ab@rapidinnovation.dev',
    'Hitesh Goyal': 'Hitesh@rapidinnovation.dev',
    'Jesse Anglen': 'Jesse@rapidinnovation.io',
    'Neeraj Deshpande': 'neerajdeshpande@rapidinnovation.dev',
    'Prasanjit Dey': 'pd@rapidinnovation.io',
    'Rajnikant Sonvane': 'rajnikantsonvane@rapidinnovation.dev',
    'Shailesh Kala': 'sk@rapidinnovation.dev',
    'Tyson Faulkner': 'tyson@rapidinnovation.io',
    'Jeetanshu': 'jeetanshu@rapidinnovation.dev',
    'Himanshu Yadav': 'hy@rapidinnovation.dev',
}

# Alternative name variations (for handling different name formats)
NAME_VARIATIONS: Dict[str, str] = {
    # Common variations from TeamLogger vs Google Sheets
    'Mohd Arbaz Khan': 'Mohd Arbaz Khan',
    'Mohd. Arbaz Khan': 'Mohd Arbaz Khan',
    'Mohammed Abdul Aleem': 'Mohamed Abdul Aleem',
    'Mohan Chaudhari': 'MOHAN CHAUDHARI',
    'Pankaj Bansal': 'Pankaj kumar Bansal',
    'Rishab Kala': 'Rishabh Kala',
    'Shruti Agarwal': 'Shruti Agarwal',
    'Aditya Singh': 'Aditya Singh',
    'Jeetanshu': 'Jeetanshu Srivastava',
    'Shwetha Kamath': 'Shwetha Vasanth Kamath',
    'Kesavan': 'Kesavan Manokar',
    'Siddharth Thakur': 'Kunwar Siddharth Thakur',
    'Ashique': 'Ashique Mohammed C',
    'Istekhar': 'Istekhar Khan',
    'Nekhlesh': 'Nekhlesh Singh Sajwan',
    'Nihal': 'Nihal H Adoni',
    'Satish': 'Pillai Satish',
    'Prashanth': 'Prashanth Manda',
    'Pratham': 'Pratham Agarwal',
    'Prateek': 'Pratik Kumar',
    'Punesh': 'Punesh Ramrao Borkar',
    'Rajnikant': 'Rajnikant Sonvane',
    'Ritwik': 'Ritwik Rohitashwa',
    'Shwetha': 'Shwetha Vasanth Kamath',
    'Sushil': 'Sushil Baburao Khatke',
    'Vaibhav': 'Vaibhav Chandolia',
    'Yaoreichan': 'Yaoreichan Ramshang',
    # Manager case variations
    'shailesh Kala': 'Shailesh Kala',
    'prasanjit Dey': 'Prasanjit Dey',
}


def normalize_name(name: str) -> str:
    """
    Normalize employee name to match the mapping
    Handles case variations and common name differences
    """
    if not name:
        return ""

    # Get current mappings from Google Sheets
    reporting_managers, _ = _get_current_mappings()

    # Try exact match first
    if name in reporting_managers:
        return name

    # Try case-insensitive match
    name_lower = name.lower()
    for mapped_name in reporting_managers:
        if mapped_name.lower() == name_lower:
            return mapped_name

    # Try name variations
    if name in NAME_VARIATIONS:
        return NAME_VARIATIONS[name]

    # Try partial match (first name + last name)
    name_parts = name.split()
    if len(name_parts) >= 2:
        for mapped_name in reporting_managers:
            mapped_parts = mapped_name.split()
            if len(mapped_parts) >= 2:
                if (name_parts[0].lower() == mapped_parts[0].lower() and
                    name_parts[-1].lower() == mapped_parts[-1].lower()):
                    return mapped_name

    # Try just first name match
    if len(name_parts) >= 1:
        first_name = name_parts[0].lower()
        for mapped_name in reporting_managers:
            if mapped_name.lower().startswith(first_name):
                return mapped_name

    return name


def get_manager_name(employee_identifier: str) -> Optional[str]:
    """
    Get the reporting manager's name for an employee

    Args:
        employee_identifier: Name or email of the employee

    Returns:
        Manager's name or None if not found
    """
    # Get current mappings from Google Sheets
    reporting_managers, _ = _get_current_mappings()

    # If Google Sheets data is empty, fall back to static data
    if not reporting_managers:
        logger.warning("No Google Sheets data available, using fallback data")
        reporting_managers = _FALLBACK_REPORTING_MANAGERS

    # Try direct lookup first (could be email or name)
    manager = reporting_managers.get(employee_identifier)
    if manager:
        logger.debug(f"Found manager for {employee_identifier}: {manager}")
        return manager

    # Try normalized name lookup
    normalized_name = normalize_name(employee_identifier)
    manager = reporting_managers.get(normalized_name)

    if not manager:
        logger.warning(f"No manager found for employee: {employee_identifier} (normalized: {normalized_name})")

    return manager


def get_manager_email(employee_identifier: str) -> Optional[str]:
    """
    Get the reporting manager's email for an employee

    Args:
        employee_identifier: Name or email of the employee

    Returns:
        Manager's email address or None if not found
    """
    manager_name = get_manager_name(employee_identifier)

    if not manager_name:
        return None

    # Get current mappings from Google Sheets
    _, manager_emails = _get_current_mappings()

    # If Google Sheets doesn't have email data, fall back to static data
    if not manager_emails:
        logger.debug("No manager email data from Google Sheets, using fallback data")
        manager_emails = _FALLBACK_MANAGER_EMAILS

    # Handle case variations in manager names
    manager_email = manager_emails.get(manager_name)

    if not manager_email:
        # Try case-insensitive match for manager email
        for mapped_manager, email in manager_emails.items():
            if mapped_manager.lower() == manager_name.lower():
                manager_email = email
                break

    if not manager_email:
        logger.warning(f"No email found for manager: {manager_name}")
        return None

    logger.debug(f"Found manager email for {employee_identifier}: {manager_name} -> {manager_email}")
    return manager_email


def get_all_manager_emails(employee_names: List[str]) -> List[str]:
    """
    Get unique manager emails for a list of employees
    
    Args:
        employee_names: List of employee names
        
    Returns:
        List of unique manager email addresses
    """
    manager_emails = set()
    
    for employee in employee_names:
        email = get_manager_email(employee)
        if email:
            manager_emails.add(email)
    
    return sorted(list(manager_emails))


def get_employees_by_manager(manager_name: str) -> List[str]:
    """
    Get all employees reporting to a specific manager

    Args:
        manager_name: Name of the manager

    Returns:
        List of employee names
    """
    employees = []

    # Get current mappings from Google Sheets
    reporting_managers, manager_emails = _get_current_mappings()

    # If Google Sheets data is empty, fall back to static data
    if not reporting_managers:
        reporting_managers = _FALLBACK_REPORTING_MANAGERS
    if not manager_emails:
        manager_emails = _FALLBACK_MANAGER_EMAILS

    # Handle case variations
    manager_variations = [manager_name]
    for mapped_manager in manager_emails:
        if mapped_manager.lower() == manager_name.lower():
            manager_variations.append(mapped_manager)

    for employee, manager in reporting_managers.items():
        if manager in manager_variations:
            employees.append(employee)

    return sorted(employees)


def get_manager_summary() -> Dict[str, Dict]:
    """
    Get a summary of all managers and their teams

    Returns:
        Dictionary with manager information and team sizes
    """
    summary = {}

    # Get current mappings from Google Sheets
    reporting_managers, manager_emails = _get_current_mappings()

    # If Google Sheets data is empty, fall back to static data
    if not reporting_managers:
        reporting_managers = _FALLBACK_REPORTING_MANAGERS
    if not manager_emails:
        manager_emails = _FALLBACK_MANAGER_EMAILS

    # Get unique managers
    unique_managers = set()
    for manager in reporting_managers.values():
        if manager:  # Skip empty managers
            unique_managers.add(manager)

    for manager in unique_managers:
        employees = get_employees_by_manager(manager)

        # Get email handling case variations
        email = manager_emails.get(manager, 'Not configured')
        if email == 'Not configured':
            # Try case-insensitive match
            for mapped_manager, mapped_email in manager_emails.items():
                if mapped_manager.lower() == manager.lower():
                    email = mapped_email
                    break

        summary[manager] = {
            'email': email,
            'team_size': len(employees),
            'employees': employees
        }

    return summary


def validate_mapping() -> Dict[str, List[str]]:
    """
    Validate the manager mapping configuration

    Returns:
        Dictionary with validation results
    """
    issues = {
        'missing_manager_emails': [],
        'duplicate_employees': [],
        'managers_without_emails': [],
        'employees_without_managers': []
    }

    # Get current mappings from Google Sheets
    reporting_managers, manager_emails = _get_current_mappings()

    # If Google Sheets data is empty, fall back to static data
    if not reporting_managers:
        reporting_managers = _FALLBACK_REPORTING_MANAGERS
    if not manager_emails:
        manager_emails = _FALLBACK_MANAGER_EMAILS

    # Check for managers without emails
    all_managers = set()
    for manager in reporting_managers.values():
        if manager:
            all_managers.add(manager)

    for manager in all_managers:
        found_email = False
        # Check exact match and case-insensitive match
        for mapped_manager in manager_emails:
            if mapped_manager.lower() == manager.lower():
                found_email = True
                break
        if not found_email:
            issues['managers_without_emails'].append(manager)

    # Check for employees without managers
    for employee, manager in reporting_managers.items():
        if not manager:
            issues['employees_without_managers'].append(employee)

    # Check for duplicate employee entries
    employee_counts = {}
    for employee in reporting_managers:
        employee_lower = employee.lower()
        if employee_lower in employee_counts:
            issues['duplicate_employees'].append(employee)
        employee_counts[employee_lower] = employee_counts.get(employee_lower, 0) + 1

    return issues


def print_manager_report():
    """
    Print a formatted report of all managers and their teams
    """
    print("\n" + "="*60)
    print("MANAGER REPORT - UPDATED")
    print("="*60)
    
    summary = get_manager_summary()
    
    for manager, info in sorted(summary.items()):
        print(f"\nManager: {manager}")
        print(f"Email: {info['email']}")
        print(f"Team Size: {info['team_size']}")
        print("Team Members:")
        for employee in info['employees']:
            print(f"  - {employee}")
    
    # Get current mappings for stats
    reporting_managers, _ = _get_current_mappings()
    if not reporting_managers:
        reporting_managers = _FALLBACK_REPORTING_MANAGERS

    print("\n" + "="*60)
    print(f"Total Managers: {len(summary)}")
    print(f"Total Employees: {len(reporting_managers)}")
    print("="*60)


def get_mapping_stats():
    """Get mapping statistics"""
    # Get current mappings from Google Sheets
    reporting_managers, manager_emails = _get_current_mappings()

    # If Google Sheets data is empty, fall back to static data
    if not reporting_managers:
        reporting_managers = _FALLBACK_REPORTING_MANAGERS
    if not manager_emails:
        manager_emails = _FALLBACK_MANAGER_EMAILS

    unique_managers = set(reporting_managers.values())
    return {
        'total_employees': len(reporting_managers),
        'unique_managers': len(unique_managers),
        'managers_with_emails': len(manager_emails),
        'largest_team': max([list(reporting_managers.values()).count(manager)
                           for manager in unique_managers] or [0])
    }


def refresh_manager_mappings() -> bool:
    """
    Force refresh manager mappings from Google Sheets

    Returns:
        True if successful, False otherwise
    """
    try:
        client = _get_manager_client()
        reporting_managers, manager_emails = client.get_manager_mappings(force_refresh=True)

        if reporting_managers:
            logger.info(f"Successfully refreshed manager mappings: {len(reporting_managers)} employees, {len(manager_emails)} manager emails")
            return True
        else:
            logger.warning("No data received from Google Sheets refresh")
            return False
    except Exception as e:
        logger.error(f"Error refreshing manager mappings: {str(e)}")
        return False


def test_google_sheets_connection() -> Dict:
    """
    Test the Google Sheets connection and return status

    Returns:
        Dictionary with connection status and sample data
    """
    try:
        client = _get_manager_client()
        raw_data = client._fetch_manager_data()

        if raw_data:
            reporting_managers, manager_emails = client._parse_manager_data(raw_data)

            return {
                'status': 'success',
                'message': 'Google Sheets connection successful',
                'spreadsheet_id': client.spreadsheet_id,
                'sheet_name': client.sheet_name,
                'rows_fetched': len(raw_data),
                'employees_mapped': len(reporting_managers),
                'manager_emails': len(manager_emails),
                'sample_employees': list(reporting_managers.keys())[:5],
                'sample_managers': list(set(reporting_managers.values()))[:5],
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'error',
                'message': 'Could not fetch data from Google Sheets. Check spreadsheet ID and permissions.',
                'spreadsheet_id': client.spreadsheet_id,
                'sheet_name': client.sheet_name,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error testing Google Sheets connection: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }


def get_current_data_source() -> str:
    """
    Get information about the current data source being used

    Returns:
        String describing the data source
    """
    try:
        reporting_managers, manager_emails = _get_current_mappings()

        if reporting_managers:
            return f"Google Sheets (Live) - {len(reporting_managers)} employees, {len(manager_emails)} manager emails"
        else:
            return f"Fallback Data (Static) - {len(_FALLBACK_REPORTING_MANAGERS)} employees, {len(_FALLBACK_MANAGER_EMAILS)} manager emails"
    except Exception as e:
        return f"Error determining data source: {str(e)}"


# For testing the module independently
if __name__ == "__main__":
    # Run validation
    print("Validating updated manager mapping...")
    issues = validate_mapping()
    
    if issues['managers_without_emails']:
        print(f"\n⚠️  Managers without email configuration: {', '.join(issues['managers_without_emails'])}")
    
    if issues['duplicate_employees']:
        print(f"\n⚠️  Potential duplicate employees: {', '.join(issues['duplicate_employees'])}")
    
    if issues['employees_without_managers']:
        print(f"\n⚠️  Employees without managers: {', '.join(issues['employees_without_managers'])}")
    
    # Show statistics
    stats = get_mapping_stats()
    print(f"\n📊 Mapping Statistics:")
    print(f"  Total Employees: {stats['total_employees']}")
    print(f"  Unique Managers: {stats['unique_managers']}")
    print(f"  Managers with Emails: {stats['managers_with_emails']}")
    print(f"  Largest Team Size: {stats['largest_team']}")
    
    # Print report
    print_manager_report()
    
    # Test some lookups
    print("\n\nTest Lookups:")
    test_names = ['Kartik Jain', 'Mohd Arbaz Khan', 'Varnita Saxena', 'Aayush Limbad', 'Arvind Kumar']
    for name in test_names:
        manager = get_manager_name(name)
        email = get_manager_email(name)
        print(f"{name} -> Manager: {manager}, Email: {email}")