#!/usr/bin/env python3
"""
System Diagnostic Test for Employee Hours Monitoring System
Run this file to diagnose all system components and identify issues
Usage: python test_system_health.py
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import traceback

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    from config.settings import Config
    from src.teamlogger_client import TeamLoggerClient
    from src.googlesheets_Client import GoogleSheetsLeaveClient
    from src.email_service import EmailService
    from src.manager_mapping import (
        get_manager_name, get_manager_email, validate_mapping, 
        get_manager_summary, REPORTING_MANAGERS, MANAGER_EMAILS
    )
    from src.workflow_manager import WorkflowManager
    from src.utils import setup_logging
except ImportError as e:
    print(f"❌ CRITICAL: Failed to import modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

class SystemDiagnostic:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'UNKNOWN',
            'components': {},
            'issues': [],
            'recommendations': []
        }
        
        # Setup logging for diagnostic
        setup_logging('DEBUG', 'logs/diagnostic_test.log')
        self.logger = logging.getLogger(__name__)
        
        print("🔍 EMPLOYEE HOURS MONITORING SYSTEM - DIAGNOSTIC TEST")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    def test_environment_variables(self) -> Dict:
        """Test all required environment variables"""
        print("\n🔧 Testing Environment Variables...")
        
        required_vars = [
            'TEAMLOGGER_API_URL',
            'TEAMLOGGER_BEARER_TOKEN',
            'SMTP_HOST',
            'SMTP_PORT',
            'SMTP_USERNAME',
            'SMTP_PASSWORD',
            'FROM_EMAIL',
            'GOOGLE_SHEETS_ID'
        ]
        
        optional_vars = [
            'GOOGLE_SHEETS_URL',
            'GOOGLE_SHEETS_PUBLISHED_CSV_URL',
            'ALERT_CC_EMAILS',
            'OPENAI_API_KEY'
        ]
        
        result = {
            'status': 'PASS',
            'missing_required': [],
            'missing_optional': [],
            'configured_vars': {},
            'issues': []
        }
        
        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value or value in ['your_email@gmail.com', 'your_app_password', 'your-key-here']:
                result['missing_required'].append(var)
                result['status'] = 'FAIL'
                print(f"  ❌ {var}: Missing or has default value")
            else:
                # Mask sensitive values for display
                if 'PASSWORD' in var or 'TOKEN' in var or 'KEY' in var:
                    display_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
                else:
                    display_value = value
                result['configured_vars'][var] = display_value
                print(f"  ✅ {var}: {display_value}")
        
        # Check optional variables
        for var in optional_vars:
            value = os.getenv(var)
            if not value:
                result['missing_optional'].append(var)
                print(f"  ⚠️  {var}: Not configured (optional)")
            else:
                if 'KEY' in var:
                    display_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
                else:
                    display_value = value
                result['configured_vars'][var] = display_value
                print(f"  ✅ {var}: {display_value}")
        
        # Check .env file existence
        env_file_path = '.env'
        if os.path.exists(env_file_path):
            print(f"  ✅ .env file found: {os.path.abspath(env_file_path)}")
        else:
            print(f"  ⚠️  .env file not found in: {os.path.abspath(env_file_path)}")
            result['issues'].append(".env file not found")
        
        if result['missing_required']:
            result['issues'].append(f"Missing required variables: {', '.join(result['missing_required'])}")
        
        return result

    def test_configuration_class(self) -> Dict:
        """Test Config class and validation"""
        print("\n⚙️ Testing Configuration Class...")
        
        result = {
            'status': 'PASS',
            'config_valid': False,
            'missing_configs': [],
            'work_schedule': {},
            'issues': []
        }
        
        try:
            # Test config validation
            is_valid, missing = Config.validate()
            result['config_valid'] = is_valid
            result['missing_configs'] = missing
            
            if is_valid:
                print("  ✅ Configuration validation passed")
            else:
                print(f"  ❌ Configuration validation failed: {missing}")
                result['status'] = 'FAIL'
                result['issues'].append(f"Invalid configuration: {missing}")
            
            # Test work schedule calculations
            result['work_schedule'] = {
                'minimum_hours_per_week': Config.MINIMUM_HOURS_PER_WEEK,
                'acceptable_hours_per_week': Config.ACCEPTABLE_HOURS_PER_WEEK,
                'work_days_per_week': Config.WORK_DAYS_PER_WEEK,
                'hours_per_working_day': Config.HOURS_PER_WORKING_DAY
            }
            
            # Test leave calculations
            print("  ✅ Leave day calculations:")
            for days in range(6):
                required = Config.calculate_required_hours_for_leave_days(days)
                acceptable = Config.calculate_acceptable_hours_for_leave_days(days)
                print(f"    {days} leave days: {required}h required, {acceptable}h acceptable")
            
        except Exception as e:
            result['status'] = 'FAIL'
            result['issues'].append(f"Configuration error: {str(e)}")
            print(f"  ❌ Configuration error: {str(e)}")
        
        return result

    def test_teamlogger_connection(self) -> Dict:
        """Test TeamLogger API connection"""
        print("\n🔗 Testing TeamLogger API Connection...")
        
        result = {
            'status': 'UNKNOWN',
            'connected': False,
            'employee_count': 0,
            'sample_employees': [],
            'api_response_time': 0,
            'issues': []
        }
        
        try:
            start_time = time.time()
            teamlogger = TeamLoggerClient()
            
            # Test basic connection
            status = teamlogger.get_api_status()
            result['connected'] = status.get('connected', False)
            result['employee_count'] = status.get('employee_count', 0)
            result['api_response_time'] = time.time() - start_time
            
            if result['connected']:
                print(f"  ✅ TeamLogger API connected successfully")
                print(f"  📊 Found {result['employee_count']} employees")
                print(f"  ⏱️  Response time: {result['api_response_time']:.2f} seconds")
                
                # Get sample employees
                employees = teamlogger.get_all_employees()
                if employees:
                    result['sample_employees'] = [
                        {'name': emp['name'], 'id': emp['id'], 'email': emp['email']} 
                        for emp in employees[:3]
                    ]
                    print(f"  👥 Sample employees:")
                    for emp in result['sample_employees']:
                        print(f"    - {emp['name']} ({emp['id']})")
                
                # Test weekly summary for first employee
                if employees:
                    test_emp = employees[0]
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
                    
                    weekly_data = teamlogger.get_weekly_summary(test_emp['id'], start_date, end_date)
                    if weekly_data:
                        print(f"  ✅ Weekly data test: {weekly_data['total_hours']:.2f} hours for {test_emp['name']}")
                        result['status'] = 'PASS'
                    else:
                        print(f"  ⚠️  Weekly data test: No data returned")
                        result['status'] = 'PARTIAL'
                        result['issues'].append("No weekly data available")
                else:
                    result['status'] = 'PARTIAL'
                    result['issues'].append("No employees found")
            else:
                print(f"  ❌ TeamLogger API connection failed")
                result['status'] = 'FAIL'
                result['issues'].append("API connection failed")
                
        except Exception as e:
            result['status'] = 'FAIL'
            result['issues'].append(f"TeamLogger error: {str(e)}")
            print(f"  ❌ TeamLogger error: {str(e)}")
            print(f"  📋 Traceback: {traceback.format_exc()}")
        
        return result

    def test_google_sheets_connection(self) -> Dict:
        """Test Google Sheets connection"""
        print("\n📊 Testing Google Sheets Connection...")
        
        result = {
            'status': 'UNKNOWN',
            'connected': False,
            'spreadsheet_id': Config.GOOGLE_SHEETS_ID,
            'test_data_found': False,
            'sample_leaves': [],
            'issues': []
        }
        
        try:
            sheets = GoogleSheetsLeaveClient()
            
            # Test basic connection
            validation = sheets.validate_google_sheets_connection()
            result['connected'] = validation.get('status') == 'success'
            
            if result['connected']:
                print(f"  ✅ Google Sheets connected successfully")
                print(f"  📄 Spreadsheet ID: {result['spreadsheet_id']}")
                print(f"  📊 Rows found: {validation.get('rows_found', 0)}")
                
                # Test leave data for a sample employee
                test_employees = ['Aakash Kumar', 'Kartik Jain', 'Mohd Arbaz Khan']
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                
                for emp_name in test_employees:
                    try:
                        leaves = sheets.get_employee_leaves(emp_name, start_date, end_date)
                        if leaves:
                            result['test_data_found'] = True
                            result['sample_leaves'].extend([
                                {
                                    'employee': emp_name,
                                    'start_date': leave['start_date'].strftime('%Y-%m-%d'),
                                    'end_date': leave['end_date'].strftime('%Y-%m-%d'),
                                    'days': leave['days_count']
                                } for leave in leaves[:2]
                            ])
                            print(f"  ✅ Leave data found for {emp_name}: {len(leaves)} records")
                            break
                    except Exception as e:
                        print(f"  ⚠️  No leave data for {emp_name}: {str(e)}")
                
                if result['test_data_found']:
                    result['status'] = 'PASS'
                else:
                    result['status'] = 'PARTIAL'
                    result['issues'].append("No leave data found for test employees")
                    
            else:
                print(f"  ❌ Google Sheets connection failed")
                print(f"  📋 Error: {validation.get('message', 'Unknown error')}")
                result['status'] = 'FAIL'
                result['issues'].append(f"Connection failed: {validation.get('message')}")
                
        except Exception as e:
            result['status'] = 'FAIL'
            result['issues'].append(f"Google Sheets error: {str(e)}")
            print(f"  ❌ Google Sheets error: {str(e)}")
            print(f"  📋 Traceback: {traceback.format_exc()}")
        
        return result

    def test_email_service(self) -> Dict:
        """Test email service configuration"""
        print("\n📧 Testing Email Service...")
        
        result = {
            'status': 'UNKNOWN',
            'config_valid': False,
            'smtp_connection': False,
            'cc_emails': [],
            'issues': []
        }
        
        try:
            email_service = EmailService()
            
            # Test configuration
            result['config_valid'] = email_service.test_email_configuration()
            result['cc_emails'] = email_service.cc_emails
            
            print(f"  📧 From Email: {Config.FROM_EMAIL}")
            print(f"  🏢 SMTP Host: {Config.SMTP_HOST}:{Config.SMTP_PORT}")
            print(f"  📬 CC Recipients: {len(result['cc_emails'])}")
            for email in result['cc_emails']:
                print(f"    - {email}")
            
            if result['config_valid']:
                print(f"  ✅ Email configuration is valid")
                result['status'] = 'PASS'
                
                # Test sending a test email (comment out if you don't want to send)
                # test_success = email_service.send_test_email(Config.FROM_EMAIL)
                # if test_success:
                #     print(f"  ✅ Test email sent successfully")
                # else:
                #     print(f"  ⚠️  Test email sending failed")
                #     result['issues'].append("Test email sending failed")
                
            else:
                print(f"  ❌ Email configuration is invalid")
                result['status'] = 'FAIL'
                result['issues'].append("Invalid email configuration")
                
        except Exception as e:
            result['status'] = 'FAIL'
            result['issues'].append(f"Email service error: {str(e)}")
            print(f"  ❌ Email service error: {str(e)}")
            print(f"  📋 Traceback: {traceback.format_exc()}")
        
        return result

    def test_manager_mapping(self) -> Dict:
        """Test manager mapping functionality"""
        print("\n👨‍💼 Testing Manager Mapping...")
        
        result = {
            'status': 'UNKNOWN',
            'total_employees': len(REPORTING_MANAGERS),
            'total_managers': len(MANAGER_EMAILS),
            'validation_issues': {},
            'sample_mappings': [],
            'issues': []
        }
        
        try:
            # Run validation
            validation_issues = validate_mapping()
            result['validation_issues'] = validation_issues
            
            print(f"  👥 Total Employees: {result['total_employees']}")
            print(f"  👨‍💼 Total Managers: {result['total_managers']}")
            
            # Check for issues
            has_issues = False
            for issue_type, issues in validation_issues.items():
                if issues:
                    has_issues = True
                    print(f"  ❌ {issue_type}: {len(issues)} issues")
                    for issue in issues[:3]:  # Show first 3 issues
                        print(f"    - {issue}")
                    if len(issues) > 3:
                        print(f"    ... and {len(issues) - 3} more")
                else:
                    print(f"  ✅ {issue_type}: No issues")
            
            # Test sample mappings
            test_employees = ['Aakash Kumar', 'Kartik Jain', 'Mohd Arbaz Khan', 'Varnita Saxena']
            print(f"  🧪 Testing sample employee mappings:")
            
            for emp_name in test_employees:
                manager_name = get_manager_name(emp_name)
                manager_email = get_manager_email(emp_name)
                
                result['sample_mappings'].append({
                    'employee': emp_name,
                    'manager': manager_name,
                    'manager_email': manager_email
                })
                
                if manager_name and manager_email:
                    print(f"    ✅ {emp_name} → {manager_name} ({manager_email})")
                else:
                    print(f"    ❌ {emp_name} → No manager found")
                    has_issues = True
            
            # Get manager summary
            manager_summary = get_manager_summary()
            print(f"  📊 Manager teams:")
            for manager, info in list(manager_summary.items())[:5]:
                print(f"    - {manager}: {info['team_size']} employees ({info['email']})")
            
            if not has_issues:
                result['status'] = 'PASS'
            else:
                result['status'] = 'PARTIAL'
                result['issues'].append("Manager mapping has validation issues")
                
        except Exception as e:
            result['status'] = 'FAIL'
            result['issues'].append(f"Manager mapping error: {str(e)}")
            print(f"  ❌ Manager mapping error: {str(e)}")
            print(f"  📋 Traceback: {traceback.format_exc()}")
        
        return result

    def test_workflow_manager(self) -> Dict:
        """Test workflow manager functionality"""
        print("\n🔄 Testing Workflow Manager...")
        
        result = {
            'status': 'UNKNOWN',
            'should_send_alerts': False,
            'work_week_period': {},
            'employees_needing_alerts': 0,
            'preview_successful': False,
            'issues': []
        }
        
        try:
            workflow = WorkflowManager()
            
            # Test basic functionality
            result['should_send_alerts'] = workflow.should_send_alerts_today()
            print(f"  📅 Should send alerts today: {result['should_send_alerts']}")
            
            # Get work week boundaries
            start_date, end_date = workflow._get_previous_work_week()
            result['work_week_period'] = {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
            print(f"  📊 Work week period: {result['work_week_period']['start']} to {result['work_week_period']['end']}")
            
            # Test preview functionality
            try:
                employees_needing_alerts = workflow.get_employees_needing_real_alerts()
                result['employees_needing_alerts'] = len(employees_needing_alerts)
                result['preview_successful'] = True
                
                print(f"  ⚠️  Employees needing alerts: {result['employees_needing_alerts']}")
                
                if employees_needing_alerts:
                    print(f"  📋 Sample employees needing alerts:")
                    for item in employees_needing_alerts[:3]:
                        emp = item['employee']
                        print(f"    - {emp['name']}: {item['actual_shortfall']:.2f}h shortfall")
                
                result['status'] = 'PASS'
                
            except Exception as e:
                result['issues'].append(f"Preview functionality failed: {str(e)}")
                print(f"  ❌ Preview functionality failed: {str(e)}")
                result['status'] = 'PARTIAL'
                
        except Exception as e:
            result['status'] = 'FAIL'
            result['issues'].append(f"Workflow manager error: {str(e)}")
            print(f"  ❌ Workflow manager error: {str(e)}")
            print(f"  📋 Traceback: {traceback.format_exc()}")
        
        return result

    def test_file_permissions(self) -> Dict:
        """Test file and directory permissions"""
        print("\n📁 Testing File Permissions...")
        
        result = {
            'status': 'PASS',
            'log_directory': False,
            'template_files': False,
            'config_files': False,
            'issues': []
        }
        
        # Check log directory
        log_dir = 'logs'
        if os.path.exists(log_dir):
            if os.access(log_dir, os.W_OK):
                print(f"  ✅ Log directory writable: {os.path.abspath(log_dir)}")
                result['log_directory'] = True
            else:
                print(f"  ❌ Log directory not writable: {os.path.abspath(log_dir)}")
                result['issues'].append("Log directory not writable")
                result['status'] = 'PARTIAL'
        else:
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"  ✅ Created log directory: {os.path.abspath(log_dir)}")
                result['log_directory'] = True
            except Exception as e:
                print(f"  ❌ Cannot create log directory: {str(e)}")
                result['issues'].append(f"Cannot create log directory: {str(e)}")
                result['status'] = 'FAIL'
        
        # Check template files
        template_paths = [
            'templates/low_hours_email.html',
            'low_hours_email.html',
            'src/templates/low_hours_email.html'
        ]
        
        template_found = False
        for template_path in template_paths:
            if os.path.exists(template_path):
                print(f"  ✅ Email template found: {template_path}")
                result['template_files'] = True
                template_found = True
                break
        
        if not template_found:
            print(f"  ⚠️  Email template not found (will use fallback)")
            result['issues'].append("Email template not found")
        
        # Check config files
        if os.path.exists('.env'):
            print(f"  ✅ .env file found")
            result['config_files'] = True
        else:
            print(f"  ❌ .env file not found")
            result['issues'].append(".env file not found")
            result['status'] = 'PARTIAL'
        
        return result

    def run_full_diagnostic(self) -> Dict:
        """Run complete system diagnostic"""
        print("🏃‍♂️ Running Full System Diagnostic...\n")
        
        # Run all tests
        self.results['components']['environment'] = self.test_environment_variables()
        self.results['components']['configuration'] = self.test_configuration_class()
        self.results['components']['file_permissions'] = self.test_file_permissions()
        self.results['components']['teamlogger'] = self.test_teamlogger_connection()
        self.results['components']['google_sheets'] = self.test_google_sheets_connection()
        self.results['components']['email_service'] = self.test_email_service()
        self.results['components']['manager_mapping'] = self.test_manager_mapping()
        self.results['components']['workflow_manager'] = self.test_workflow_manager()
        
        # Determine overall status
        statuses = [comp['status'] for comp in self.results['components'].values()]
        
        if all(status == 'PASS' for status in statuses):
            self.results['overall_status'] = 'HEALTHY'
        elif any(status == 'FAIL' for status in statuses):
            self.results['overall_status'] = 'CRITICAL'
        else:
            self.results['overall_status'] = 'WARNING'
        
        # Collect all issues
        for component, data in self.results['components'].items():
            for issue in data.get('issues', []):
                self.results['issues'].append(f"{component}: {issue}")
        
        # Generate recommendations
        self.generate_recommendations()
        
        return self.results

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Environment variable issues
        env_component = self.results['components'].get('environment', {})
        if env_component.get('missing_required'):
            recommendations.append(
                "Create or update your .env file with missing required variables: " + 
                ", ".join(env_component['missing_required'])
            )
        
        # TeamLogger issues
        tl_component = self.results['components'].get('teamlogger', {})
        if not tl_component.get('connected'):
            recommendations.append(
                "Check TeamLogger API URL and bearer token. Verify network connectivity."
            )
        
        # Google Sheets issues
        gs_component = self.results['components'].get('google_sheets', {})
        if not gs_component.get('connected'):
            recommendations.append(
                "Verify Google Sheets ID and ensure the sheet is publicly accessible."
            )
        
        # Email issues
        email_component = self.results['components'].get('email_service', {})
        if not email_component.get('config_valid'):
            recommendations.append(
                "Check SMTP configuration. For Gmail, ensure you're using App Password instead of regular password."
            )
        
        # Manager mapping issues
        mm_component = self.results['components'].get('manager_mapping', {})
        validation_issues = mm_component.get('validation_issues', {})
        if validation_issues.get('managers_without_emails'):
            recommendations.append(
                "Add missing manager emails to MANAGER_EMAILS dictionary in manager_mapping.py"
            )
        
        self.results['recommendations'] = recommendations

    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 60)
        print("🏥 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        # Overall status
        status_emoji = {
            'HEALTHY': '✅',
            'WARNING': '⚠️',
            'CRITICAL': '❌',
            'UNKNOWN': '❓'
        }
        
        print(f"Overall Status: {status_emoji.get(self.results['overall_status'], '❓')} {self.results['overall_status']}")
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Component status
        print(f"\n📊 Component Status:")
        for component, data in self.results['components'].items():
            status = data['status']
            emoji = '✅' if status == 'PASS' else '⚠️' if status == 'PARTIAL' else '❌'
            print(f"  {emoji} {component.replace('_', ' ').title()}: {status}")
        
        # Issues
        if self.results['issues']:
            print(f"\n🚨 Issues Found ({len(self.results['issues'])}):")
            for i, issue in enumerate(self.results['issues'], 1):
                print(f"  {i}. {issue}")
        else:
            print(f"\n✅ No issues found!")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "=" * 60)

    def save_results(self, filename: str = None):
        """Save diagnostic results to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'diagnostic_results_{timestamp}.json'
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"📄 Diagnostic results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")

def main():
    """Main function to run diagnostic"""
    try:
        diagnostic = SystemDiagnostic()
        results = diagnostic.run_full_diagnostic()
        diagnostic.print_summary()
        diagnostic.save_results()
        
        # Exit with appropriate code
        if results['overall_status'] == 'CRITICAL':
            sys.exit(1)
        elif results['overall_status'] == 'WARNING':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Diagnostic interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Diagnostic failed with error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()