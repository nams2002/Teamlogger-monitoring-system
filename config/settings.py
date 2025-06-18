import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class for Employee Hours Monitoring System
    FIXED: Removed 10-minute negligible shortfall, using only 3-hour buffer
    """
    
    # TeamLogger Configuration
    TEAMLOGGER_API_URL = os.getenv('TEAMLOGGER_API_URL')
    TEAMLOGGER_BEARER_TOKEN = os.getenv('TEAMLOGGER_BEARER_TOKEN')
    
    # Google Sheets Configuration - FORCE REAL-TIME
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '1RJt6TXG_x5EmTWX6YNyC9qiCCEVsmb4lBjTUe2Ua8Yk')
    GOOGLE_SHEETS_URL = os.getenv('GOOGLE_SHEETS_URL', 'https://docs.google.com/spreadsheets/d/1RJt6TXG_x5EmTWX6YNyC9qiCCEVsmb4lBjTUe2Ua8Yk/edit?gid=1013361163#gid=1013361163')
    GOOGLE_SHEETS_PUBLISHED_CSV_URL = os.getenv("GOOGLE_SHEETS_PUBLISHED_CSV_URL")
    
    # Email Configuration
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    
    # Alert CC Emails
    _cc_emails = os.getenv('ALERT_CC_EMAILS', '')
    ALERT_CC_EMAILS = [email.strip() for email in _cc_emails.split(',') if email.strip()] if _cc_emails else []
    CONSTANT_CC_EMAIL = 'teamhr@rapidinnovation.dev'
    
    # FIXED: Excluded employees list
    EXCLUDED_EMPLOYEES = [
        'Aishik Chatterjee',
        'Tirtharaj Bhoumik',
        'Vishal Kumar'
    ]
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # 5-DAY WORK SYSTEM CONFIGURATION
    MINIMUM_HOURS_PER_WEEK = 40
    HOURS_BUFFER = 3  # Only 3-hour buffer matters
    ACCEPTABLE_HOURS_PER_WEEK = 37
    
    WORK_DAYS_PER_WEEK = 5
    COMPLETION_DAYS_PER_WEEK = 7
    HOURS_PER_WORKING_DAY = 8
    HOURS_PER_HALF_DAY = 4  # Half-day support
    
    WEEKEND_DAYS = [5, 6]
    MONITORING_PERIOD_DAYS = 7
    
    CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', '24'))
    
    # Schedule configuration
    EXECUTION_DAY = 0  # Monday
    EXECUTION_HOUR = 8
    EXECUTION_MINUTE = 0
    
    # REMOVED: Minimum shortfall minutes - we only use 3-hour buffer now
    # Alert Configuration
    MINIMUM_SHORTFALL_MINUTES = 0  # Disabled - using buffer only
    
    # Time Zone Configuration
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Application Configuration
    APP_NAME = os.getenv('APP_NAME', 'Employee Hours Monitor')
    APP_VERSION = os.getenv('APP_VERSION', '4.0.0')
    
    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Feature Flags
    ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'
    ENABLE_SLACK_NOTIFICATIONS = os.getenv('ENABLE_SLACK_NOTIFICATIONS', 'false').lower() == 'true'
    ENABLE_OPENAI_ENHANCEMENT = os.getenv('ENABLE_OPENAI_ENHANCEMENT', 'false').lower() == 'true'  # Disabled by default
    ENABLE_AI_INTELLIGENT_DECISIONS = os.getenv('ENABLE_AI_INTELLIGENT_DECISIONS', 'false').lower() == 'true'
    
    # Activity Monitoring Configuration
    ENABLE_ACTIVITY_MONITORING = os.getenv('ENABLE_ACTIVITY_MONITORING', 'true').lower() == 'true'
    ACTIVITY_THRESHOLD = float(os.getenv('ACTIVITY_THRESHOLD', '60'))
    CONSECUTIVE_LOW_DAYS = int(os.getenv('CONSECUTIVE_LOW_DAYS', '3'))
    ACTIVITY_CHECK_SCREENSHOTS = os.getenv('ACTIVITY_CHECK_SCREENSHOTS', 'true').lower() == 'true'
    
    # Combined Monitoring Configuration
    ENABLE_COMBINED_MONITORING = os.getenv('ENABLE_COMBINED_MONITORING', 'true').lower() == 'true'
    CRITICAL_ALERT_THRESHOLD = float(os.getenv('CRITICAL_ALERT_THRESHOLD', '40'))
    
    # Senior Management Emails
    SENIOR_MANAGEMENT_EMAILS = os.getenv('SENIOR_MANAGEMENT_EMAILS', '').split(',') if os.getenv('SENIOR_MANAGEMENT_EMAILS') else []
    
    # Report Generation Configuration
    GENERATE_PDF_REPORTS = os.getenv('GENERATE_PDF_REPORTS', 'false').lower() == 'true'
    REPORT_STORAGE_PATH = os.getenv('REPORT_STORAGE_PATH', 'reports/')
    
    # Enhanced Monitoring Schedule
    ACTIVITY_CHECK_SCHEDULE = os.getenv('ACTIVITY_CHECK_SCHEDULE', 'daily')
    ACTIVITY_CHECK_TIME = os.getenv('ACTIVITY_CHECK_TIME', '18:00')
    
    # Performance Thresholds
    PERFORMANCE_EXCELLENT = float(os.getenv('PERFORMANCE_EXCELLENT', '90'))
    PERFORMANCE_GOOD = float(os.getenv('PERFORMANCE_GOOD', '70'))
    PERFORMANCE_NEEDS_IMPROVEMENT = float(os.getenv('PERFORMANCE_NEEDS_IMPROVEMENT', '50'))
    
    # Slack Configuration
    SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
    SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#hr-alerts')
    
    # Performance Configuration
    API_REQUEST_TIMEOUT = int(os.getenv('API_REQUEST_TIMEOUT', '30'))
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))

    @classmethod
    def validate(cls) -> tuple[bool, list]:
        """Validate all required configuration settings"""
        required_configs = [
            ('TEAMLOGGER_API_URL', cls.TEAMLOGGER_API_URL),
            ('TEAMLOGGER_BEARER_TOKEN', cls.TEAMLOGGER_BEARER_TOKEN),
            ('SMTP_USERNAME', cls.SMTP_USERNAME),
            ('SMTP_PASSWORD', cls.SMTP_PASSWORD),
            ('FROM_EMAIL', cls.FROM_EMAIL),
        ]
        
        missing_configs = []
        for config_name, config_value in required_configs:
            if not config_value or config_value in ['your_email@gmail.com', 'your_app_password', 'your-key-here']:
                missing_configs.append(config_name)
        
        return len(missing_configs) == 0, missing_configs
    
    @classmethod
    def calculate_required_hours_for_leave_days(cls, leave_days: float) -> float:
        """
        Calculate required hours based on leave days (supports half days)
        Formula: 8 hours × (5 - leave_days)
        """
        if leave_days >= cls.WORK_DAYS_PER_WEEK:
            return 0.0
        
        working_days_available = cls.WORK_DAYS_PER_WEEK - leave_days
        required_hours = cls.HOURS_PER_WORKING_DAY * working_days_available
        
        return required_hours
    
    @classmethod
    def calculate_acceptable_hours_for_leave_days(cls, leave_days: float) -> float:
        """
        Calculate acceptable hours (with 3-hour buffer)
        """
        required_hours = cls.calculate_required_hours_for_leave_days(leave_days)
        if required_hours == 0:
            return 0.0
        
        acceptable_hours = max(0, required_hours - cls.HOURS_BUFFER)
        return acceptable_hours
    
    @classmethod
    def determine_employee_status(cls, actual_hours: float, leave_days: float, is_excluded: bool = False) -> dict:
        """
        FIXED: Simple status determination without negligible shortfall
        """
        if is_excluded:
            return {
                'status': 'excluded',
                'display_status': '🚫 Excluded from Alerts',
                'alert_needed': False,
                'required_hours': 0,
                'acceptable_hours': 0,
                'actual_hours': actual_hours,
                'leave_days': leave_days,
                'explanation': 'Employee is in excluded list'
            }
        
        required_hours = cls.calculate_required_hours_for_leave_days(leave_days)
        acceptable_hours = cls.calculate_acceptable_hours_for_leave_days(leave_days)
        
        # Full leave protection
        if leave_days >= cls.WORK_DAYS_PER_WEEK:
            return {
                'status': 'full_leave',
                'display_status': '🏖️ Full Leave (Protected)',
                'alert_needed': False,
                'required_hours': required_hours,
                'acceptable_hours': acceptable_hours,
                'actual_hours': actual_hours,
                'leave_days': leave_days,
                'explanation': f'Employee on full week leave ({leave_days} days)'
            }
        
        # Check if hours meet acceptable threshold (with 3-hour buffer)
        if actual_hours >= acceptable_hours:
            return {
                'status': 'meeting_requirements',
                'display_status': '✅ Meeting Requirements',
                'alert_needed': False,
                'required_hours': required_hours,
                'acceptable_hours': acceptable_hours,
                'actual_hours': actual_hours,
                'leave_days': leave_days,
                'explanation': f'Hours {actual_hours:.1f}h >= acceptable {acceptable_hours:.1f}h'
            }
        
        # Alert needed - no negligible shortfall check
        shortfall = required_hours - actual_hours
        shortfall_minutes = int(shortfall * 60)
        
        return {
            'status': 'alert_required',
            'display_status': '🔴 Alert Required',
            'alert_needed': True,
            'required_hours': required_hours,
            'acceptable_hours': acceptable_hours,
            'actual_hours': actual_hours,
            'leave_days': leave_days,
            'shortfall': shortfall,
            'shortfall_minutes': shortfall_minutes,
            'explanation': f'Hours {actual_hours:.1f}h < acceptable {acceptable_hours:.1f}h'
        }
    
    @classmethod
    def should_send_alert(cls, actual_hours: float, leave_days: float) -> tuple[bool, dict]:
        """Determine if an alert should be sent"""
        status_info = cls.determine_employee_status(actual_hours, leave_days, is_excluded=False)
        return status_info['alert_needed'], status_info
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """Get configuration summary"""
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'work_schedule': {
                'minimum_hours_per_week': cls.MINIMUM_HOURS_PER_WEEK,
                'acceptable_hours_per_week': cls.ACCEPTABLE_HOURS_PER_WEEK,
                'hours_buffer': cls.HOURS_BUFFER,
                'work_days_per_week': cls.WORK_DAYS_PER_WEEK,
                'completion_days_per_week': cls.COMPLETION_DAYS_PER_WEEK,
                'hours_per_working_day': cls.HOURS_PER_WORKING_DAY,
                'hours_per_half_day': cls.HOURS_PER_HALF_DAY,
                'weekend_days': cls.WEEKEND_DAYS,
                'monitoring_period_days': cls.MONITORING_PERIOD_DAYS,
                'system_type': '5-Day Work System (Optimized)'
            },
            'execution_schedule': {
                'day': 'Monday',
                'time': f'{cls.EXECUTION_HOUR:02d}:{cls.EXECUTION_MINUTE:02d}',
                'timezone': cls.TIMEZONE
            },
            'teamlogger_url': cls.TEAMLOGGER_API_URL,
            'smtp_host': cls.SMTP_HOST,
            'smtp_port': cls.SMTP_PORT,
            'from_email': cls.FROM_EMAIL,
            'cc_emails_count': len(cls.ALERT_CC_EMAILS),
            'constant_cc_email': cls.CONSTANT_CC_EMAIL,
            'excluded_employees': cls.EXCLUDED_EMPLOYEES,
            'log_level': cls.LOG_LEVEL,
            'log_file': cls.LOG_FILE,
            'features': {
                'email_alerts': cls.ENABLE_EMAIL_ALERTS,
                'slack_notifications': cls.ENABLE_SLACK_NOTIFICATIONS,
                'openai_enhancement': cls.ENABLE_OPENAI_ENHANCEMENT and bool(cls.OPENAI_API_KEY),
                'ai_intelligent_decisions': cls.ENABLE_AI_INTELLIGENT_DECISIONS and bool(cls.OPENAI_API_KEY),
            },
            'performance': {
                'api_timeout': cls.API_REQUEST_TIMEOUT,
                'max_retries': cls.MAX_RETRY_ATTEMPTS,
                'batch_size': cls.BATCH_SIZE,
            }
        }
    
    @classmethod
    def is_working_day(cls, weekday: int) -> bool:
        """Check if a given weekday is a working day"""
        return weekday not in cls.WEEKEND_DAYS
    
    @classmethod
    def format_leave_days(cls, leave_days: float) -> str:
        """Format leave days for display (handles half days)"""
        if leave_days == int(leave_days):
            return f"{int(leave_days)} day{'s' if leave_days != 1 else ''}"
        else:
            full_days = int(leave_days)
            if full_days == 0:
                return "0.5 day (half day)"
            else:
                return f"{full_days}.5 days ({full_days} full + 1 half)"
    
    @classmethod
    def get_ai_status(cls) -> dict:
        """Get AI enhancement status"""
        return {
            'enabled': cls.ENABLE_OPENAI_ENHANCEMENT and bool(cls.OPENAI_API_KEY),
            'api_key_configured': bool(cls.OPENAI_API_KEY),
            'features': {
                'smart_decisions': cls.ENABLE_OPENAI_ENHANCEMENT and bool(cls.OPENAI_API_KEY),
                'personalized_messages': cls.ENABLE_OPENAI_ENHANCEMENT and bool(cls.OPENAI_API_KEY),
                'context_analysis': cls.ENABLE_OPENAI_ENHANCEMENT and bool(cls.OPENAI_API_KEY),
                'intelligent_overrides': cls.ENABLE_AI_INTELLIGENT_DECISIONS and bool(cls.OPENAI_API_KEY)
            }
        }
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'