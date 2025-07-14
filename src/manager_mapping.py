"""
Manager Mapping Module - Dynamic Google Sheets Integration
Maps employees to their reporting managers for CC in email alerts
Now reads from Google Sheets in real-time to ensure accuracy
"""

import logging
import requests
import csv
from io import StringIO
from typing import Dict, List, Optional
from config.settings import Config

logger = logging.getLogger(__name__)

class DynamicManagerMapping:
    """Dynamic manager mapping that reads from Google Sheets in real-time"""

    def __init__(self):
        # Manager mapping Google Sheet URL
        self.manager_sheet_url = "https://docs.google.com/spreadsheets/d/1hqj2whB7bH0aoDeNV-ORIl_5dXX0eHcglhabW9xeVt8/edit?usp=sharing"
        self.spreadsheet_id = "1hqj2whB7bH0aoDeNV-ORIl_5dXX0eHcglhabW9xeVt8"
        self._cached_mapping = {}
        self._cache_timestamp = None

    def _fetch_manager_mapping_from_sheets(self) -> Dict[str, str]:
        """Fetch the latest manager mapping from Google Sheets"""
        try:
            # Convert Google Sheets URL to CSV export URL
            csv_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/export?format=csv"

            headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }

            logger.info("Fetching manager mapping from Google Sheets...")
            response = requests.get(csv_url, timeout=30, headers=headers)

            if response.status_code == 200:
                content = response.text
                csv_data = StringIO(content)
                reader = csv.reader(csv_data)

                mapping = {}
                manager_emails = {}
                next(reader, None)  # Skip header row

                for row in reader:
                    if len(row) >= 2 and row[0].strip() and row[1].strip():
                        employee_name = row[0].strip()
                        manager_name = row[1].strip()
                        mapping[employee_name] = manager_name

                        # Also capture manager email if available (column D)
                        if len(row) >= 4 and row[3].strip():
                            manager_email = row[3].strip()
                            if '@' in manager_email:  # Basic email validation
                                manager_emails[manager_name] = manager_email
                                logger.debug(f"Manager email: {manager_name} -> {manager_email}")

                        logger.debug(f"Mapped: {employee_name} -> {manager_name}")

                # Update global manager emails with fresh data
                global MANAGER_EMAILS
                MANAGER_EMAILS.update(manager_emails)

                logger.info(f"Successfully loaded {len(mapping)} manager mappings from Google Sheets")
                logger.info(f"Updated {len(manager_emails)} manager email addresses")
                return mapping
            else:
                logger.error(f"Failed to fetch manager mapping: HTTP {response.status_code}")
                return {}

        except Exception as e:
            logger.error(f"Error fetching manager mapping from Google Sheets: {str(e)}")
            return {}

    def get_current_mapping(self, force_refresh: bool = False) -> Dict[str, str]:
        """Get current manager mapping with optional caching"""
        from datetime import datetime, timedelta

        # Check if we need to refresh (force refresh or cache is old)
        now = datetime.now()
        cache_expired = (self._cache_timestamp is None or
                        now - self._cache_timestamp > timedelta(minutes=5))

        if force_refresh or cache_expired or not self._cached_mapping:
            fresh_mapping = self._fetch_manager_mapping_from_sheets()
            if fresh_mapping:  # Only update cache if we got data
                self._cached_mapping = fresh_mapping
                self._cache_timestamp = now
                logger.info("Manager mapping cache updated")
            elif not self._cached_mapping:  # Fallback to static mapping if no cache and fetch failed
                logger.warning("Using fallback static manager mapping")
                self._cached_mapping = self._get_fallback_mapping()

        return self._cached_mapping

    def _get_fallback_mapping(self) -> Dict[str, str]:
        """Fallback to static mapping if Google Sheets is unavailable"""
        return STATIC_REPORTING_MANAGERS

# Create global instance
_manager_mapping_instance = DynamicManagerMapping()

# Static fallback mapping (your current mapping as backup)
STATIC_REPORTING_MANAGERS: Dict[str, str] = {
    # Employee Name: Reporting Manager
    'Aakash Kumar': 'Abhijeet Sonaje',
    'Aayush Limbad': 'Neeraj Deshpande',
    'Abhijeet Sonaje': 'Abhijeet Sonaje',
    'Abhishek Negi': 'Hitesh Goyal',
    'Abhishek Jain': 'Tyson Faulkner',
    'Abhishek Ajayan': 'Jesse Anglen',
    'Adarsh Bajpai': 'Neeraj Deshpande',
    'Aditya Bisht': 'Aditya Bisht',
    'Aditya Singh': 'Abhijeet Sonaje',
    'Akash Aaglawe': 'Prasanjit Dey',
    'Akshit Gupta': 'Prasanjit Dey',
    'Aman Kale': 'Abhijeet Sonaje',
    'Aman Rao': 'Shailesh Kala',  # Fixed case
    'Amar Kant Yadav': 'Abhijeet Sonaje',
    'Anubhav Bhatt': 'Neeraj Deshpande',
    'Apoorv Nag': 'Abhijeet Sonaje',
    'Arsh': 'Neeraj Deshpande',
    'Arunima Ray': 'Jesse Anglen',
    'Ashique Mohammed C': 'Rajnikant Sonvane',
    'Ashutosh Vatsya': 'Shailesh Kala',  # Fixed case
    'Aziya Solkar': 'Abhijeet Sonaje',
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
    'Kajol Jaiswal': 'Neeraj Deshpande',
    'Kartik Jain': 'Prasanjit Dey',
    'Kashish': 'Shailesh Kala',  # Fixed case
    'Kesavan Manokar': 'Prasanjit Dey',
    'Kevin Pinto': 'Neeraj Deshpande',
    'Kishan Sahu': 'Hitesh Goyal',
    'Komal Kumari': 'Prasanjit Dey',  # Fixed case
    'Krishnakanth Ankam': 'Abhijeet Sonaje',
    'Kunwar Siddharth Thakur': 'Aditya Bisht',
    'Kushagra Gupta': 'Abhijeet Sonaje',
    'Madhav Gupta': 'Prasanjit Dey',  # Fixed case
    'Mayank Parashar': 'Hitesh Goyal',
    'Mayank Mittal': 'Shailesh Kala',  # Fixed case
    'Mohamed Abdul Aleem': 'Rajnikant Sonvane',
    'MOHAN CHAUDHARI': 'Abhijeet Sonaje',
    'Mohd Arbaz Khan': 'Hitesh Goyal',
    'Naman Nagi': 'Shailesh Kala',  # Fixed case
    'Namit Jain': 'Hitesh Goyal',
    'Neeraj Deshpande': 'Jesse Anglen',
    'Nekhlesh Singh Sajwan': 'Tyson Faulkner',
    'Nihal H Adoni': 'Tyson Faulkner',
    'Nikhil Patil': 'Jeetanshu',
    'Nitin Singh': 'Shailesh Kala',
    'Pavan S N': 'Abhijeet Sonaje',
    'Pillai Satish': 'Aditya Bisht',
    'Prashanth Manda': 'Rajnikant Sonvane',
    'Pratham Agarwal': 'Prasanjit Dey',  # Fixed case
    'Pratik Kumar': 'Prasanjit Dey',
    'Pratyush Nag': 'Prasanjit Dey',  # Fixed case
    'Pravallika': 'Prasanjit Dey',
    'Priya Bhadauria': 'Neeraj Deshpande',
    'Punesh Ramrao Borkar': 'Shailesh Kala',
    'Rajnikant Sonvane': 'Jesse Anglen',
    'Rana Munshi': 'Abhijeet Sonaje',
    'Ranjith Nair': 'Hitesh Goyal',
    'Rishabh Kala': 'Shailesh Kala',  # Fixed case
    'Ritwik Rohitashwa': 'Aditya Bisht',
    'Sai Charan': 'Rajnikant Sonvane',
    'Shalu Yadav': 'Hitesh Goyal',
    'Shaurya Singh': 'Shailesh Kala',
    'Shital Nandan': 'Shailesh Kala',  # Fixed case
    'Shivam Rajput': 'Prasanjit Dey',
    'Shobhit Vishnoi': 'Shailesh Kala',
    'Shreya Singh': 'Aditya Bisht',
    'Shruti Agarwal': 'Prasanjit Dey',  # Fixed case
    'Shruti Kamble': 'Neeraj Deshpande',
    'Shwetha Vasanth Kamath': 'Shailesh Kala',
    'Sourav Suman': 'Hitesh Goyal',
    'Sumit Guha': 'Hitesh Goyal',
    'Sunishtha Rajput': 'Neeraj Deshpande',
    'Sunny Singha': 'Shailesh Kala',
    'Sushil Baburao Khatke': 'Shailesh Kala',
    'Tushar Garg': 'Abhijeet Sonaje',
    'Ujjwal Paliwal': 'Shailesh Kala',
    'Vaibhav Chandolia': 'Abhijeet Sonaje',
    'Varnita Saxena': 'Neeraj Deshpande',
    'Vipin Yadav': 'Tyson Faulkner',
    'Yaoreichan Ramshang': 'Rajnikant Sonvane',
    # Missing from original - added from Google Sheets
    'Arvind Kumar': 'Himanshu Yadav',  # Fixed - was pointing to email instead of manager
}

# Manager email mapping - Fixed case issues and added missing managers
MANAGER_EMAILS: Dict[str, str] = {
    'Abhijeet Sonaje': 'abhijeet@rapidinnovation.dev',
    'Aditya Bisht': 'ab@rapidinnovation.dev',
    'Hitesh Goyal': 'Hitesh@rapidinnovation.dev',
    'Jesse Anglen': 'Jesse@rapidinnovation.io',
    # 'Neeraj Deshpande': 'neerajdeshpande@rapidinnovation.dev',  # REMOVED - Left organization
    'Prasanjit Dey': 'pd@rapidinnovation.io',
    'Rajnikant Sonvane': 'rajnikantsonvane@rapidinnovation.dev',
    'Shailesh Kala': 'sk@rapidinnovation.dev',
    'Tyson Faulkner': 'tyson@rapidinnovation.io',
    'Jeetanshu': 'jeetanshu@rapidinnovation.dev',
    # Added missing manager from Google Sheets
    'Himanshu Yadav': 'hy@rapidinnovation.dev',  # You may need to verify this email
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
    
    # Get current mapping from Google Sheets
    reporting_managers = _manager_mapping_instance.get_current_mapping()

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


def get_manager_name(employee_name: str, force_refresh: bool = False) -> Optional[str]:
    """
    Get the reporting manager's name for an employee from Google Sheets

    Args:
        employee_name: Name of the employee
        force_refresh: Whether to force refresh from Google Sheets

    Returns:
        Manager's name or None if not found
    """
    reporting_managers = _manager_mapping_instance.get_current_mapping(force_refresh=force_refresh)
    normalized_name = normalize_name(employee_name)
    manager = reporting_managers.get(normalized_name)

    if not manager:
        logger.warning(f"No manager found for employee: {employee_name} (normalized: {normalized_name})")
        logger.debug(f"Available employees in mapping: {list(reporting_managers.keys())[:10]}...")

    return manager


def get_manager_email(employee_name: str, force_refresh: bool = False) -> Optional[str]:
    """
    Get the reporting manager's email for an employee
    
    Args:
        employee_name: Name of the employee
        
    Returns:
        Manager's email address or None if not found
    """
    manager_name = get_manager_name(employee_name, force_refresh=force_refresh)
    
    if not manager_name:
        return None
    
    # Handle case variations in manager names
    manager_email = MANAGER_EMAILS.get(manager_name)
    
    if not manager_email:
        # Try case-insensitive match for manager email
        for mapped_manager, email in MANAGER_EMAILS.items():
            if mapped_manager.lower() == manager_name.lower():
                manager_email = email
                break
    
    if not manager_email:
        logger.warning(f"No email found for manager: {manager_name}")
        return None
    
    logger.debug(f"Found manager email for {employee_name}: {manager_name} -> {manager_email}")
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
    
    # Handle case variations
    manager_variations = [manager_name]
    for mapped_manager in MANAGER_EMAILS:
        if mapped_manager.lower() == manager_name.lower():
            manager_variations.append(mapped_manager)
    
    reporting_managers = _manager_mapping_instance.get_current_mapping()
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
    
    # Get unique managers
    reporting_managers = _manager_mapping_instance.get_current_mapping()
    unique_managers = set()
    for manager in reporting_managers.values():
        if manager:  # Skip empty managers
            unique_managers.add(manager)
    
    for manager in unique_managers:
        employees = get_employees_by_manager(manager)
        
        # Get email handling case variations
        email = MANAGER_EMAILS.get(manager, 'Not configured')
        if email == 'Not configured':
            # Try case-insensitive match
            for mapped_manager, mapped_email in MANAGER_EMAILS.items():
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
    
    # Check for managers without emails
    reporting_managers = _manager_mapping_instance.get_current_mapping()
    all_managers = set()
    for manager in reporting_managers.values():
        if manager:
            all_managers.add(manager)

    for manager in all_managers:
        found_email = False
        # Check exact match and case-insensitive match
        for mapped_manager in MANAGER_EMAILS:
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
    
    print("\n" + "="*60)
    print(f"Total Managers: {len(summary)}")
    reporting_managers = _manager_mapping_instance.get_current_mapping()
    print(f"Total Employees: {len(reporting_managers)}")
    print("="*60)


def get_mapping_stats():
    """Get mapping statistics"""
    reporting_managers = _manager_mapping_instance.get_current_mapping()
    unique_managers = set(reporting_managers.values())
    return {
        'total_employees': len(reporting_managers),
        'unique_managers': len(unique_managers),
        'managers_with_emails': len(MANAGER_EMAILS),
        'largest_team': max([list(reporting_managers.values()).count(manager)
                           for manager in unique_managers] or [0])
    }


def refresh_manager_mapping():
    """Force refresh manager mapping from Google Sheets"""
    logger.info("Force refreshing manager mapping from Google Sheets...")
    mapping = _manager_mapping_instance.get_current_mapping(force_refresh=True)
    logger.info(f"Refreshed manager mapping with {len(mapping)} employees")
    return mapping


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