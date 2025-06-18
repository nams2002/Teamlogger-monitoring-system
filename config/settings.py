import os
import streamlit as st
from dotenv import load_dotenv

# Load local .env in development (ignored on Streamlit Cloud)
load_dotenv()

def get_env_var(key, default=None):
    """
    Try to read an environment variable first; if not set,
    fall back to Streamlit secrets; finally return default.
    """
    # 1) OS environment
    value = os.getenv(key, None)
    if value is not None and value != "":
        return value

    # 2) Streamlit Cloud secrets
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

class Config:
    """
    Configuration class for Employee Hours Monitoring System
    """

    # TeamLogger Configuration
    TEAMLOGGER_API_URL       = get_env_var('TEAMLOGGER_API_URL')
    TEAMLOGGER_BEARER_TOKEN  = get_env_var('TEAMLOGGER_BEARER_TOKEN')

    # Google Sheets Configuration
    GOOGLE_SHEETS_ID              = get_env_var('GOOGLE_SHEETS_ID', '1RJt6TXG_x5EmTWX6YNyC9qiCCEVsmb4lBjTUe2Ua8Yk')
    GOOGLE_SHEETS_URL             = get_env_var('GOOGLE_SHEETS_URL', 'https://docs.google.com/spreadsheets/d/1RJt6TXG_x5EmTWX6YNyC9qiCCEVsmb4lBjTUe2Ua8Yk/edit?gid=1013361163#gid=1013361163')
    GOOGLE_SHEETS_PUBLISHED_CSV_URL = get_env_var('GOOGLE_SHEETS_PUBLISHED_CSV_URL')

    # Email Configuration
    SMTP_HOST       = get_env_var('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT       = int(get_env_var('SMTP_PORT', '587'))
    SMTP_USERNAME   = get_env_var('SMTP_USERNAME')
    SMTP_PASSWORD   = get_env_var('SMTP_PASSWORD')
    FROM_EMAIL      = get_env_var('FROM_EMAIL')
    _cc_emails      = get_env_var('ALERT_CC_EMAILS', '')
    ALERT_CC_EMAILS = [email.strip() for email in _cc_emails.split(',') if email.strip()] if _cc_emails else []
    CONSTANT_CC_EMAIL = 'teamhr@rapidinnovation.dev'

    # Excluded employees
    EXCLUDED_EMPLOYEES = [
        'Aishik Chatterjee',
        'Tirtharaj Bhoumik',
        'Vishal Kumar'
    ]

    # OpenAI Configuration
    OPENAI_API_KEY             = get_env_var('OPENAI_API_KEY')
    ENABLE_OPENAI_ENHANCEMENT  = get_env_var('ENABLE_OPENAI_ENHANCEMENT', 'false').lower() == 'true'
    ENABLE_AI_INTELLIGENT_DECISIONS = get_env_var('ENABLE_AI_INTELLIGENT_DECISIONS', 'false').lower() == 'true'

    # 5-Day Work System Configuration
    MINIMUM_HOURS_PER_WEEK      = 40
    HOURS_BUFFER                = 3
    ACCEPTABLE_HOURS_PER_WEEK   = 37
    WORK_DAYS_PER_WEEK          = 5
    COMPLETION_DAYS_PER_WEEK    = 7
    HOURS_PER_WORKING_DAY       = 8
    HOURS_PER_HALF_DAY          = 4
    WEEKEND_DAYS                = [5, 6]
    MONITORING_PERIOD_DAYS      = 7

    CHECK_INTERVAL_HOURS        = int(get_env_var('CHECK_INTERVAL_HOURS', '24'))

    # Schedule configuration
    EXECUTION_DAY    = 0   # Monday
    EXECUTION_HOUR   = 8
    EXECUTION_MINUTE = 0

    # Alert configuration
    MINIMUM_SHORTFALL_MINUTES = 0  # disabled (using buffer only)

    # Time Zone
    TIMEZONE         = get_env_var('TIMEZONE', 'Asia/Kolkata')

    # Logging Configuration
    LOG_LEVEL        = get_env_var('LOG_LEVEL', 'INFO')
    LOG_FILE         = get_env_var('LOG_FILE', 'logs/app.log')

    # Application Info
    APP_NAME         = get_env_var('APP_NAME', 'Employee Hours Monitor')
    APP_VERSION      = get_env_var('APP_VERSION', '4.0.0')
    ENVIRONMENT      = get_env_var('ENVIRONMENT', 'development')

    # Security
    SECRET_KEY       = get_env_var('SECRET_KEY', 'default-secret-key-change-in-production')

    # Database
    DATABASE_URL     = get_env_var('DATABASE_URL')

    # Feature Flags
    ENABLE_EMAIL_ALERTS         = get_env_var('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'
    ENABLE_SLACK_NOTIFICATIONS  = get_env_var('ENABLE_SLACK_NOTIFICATIONS', 'false').lower() == 'true'
    ENABLE_ACTIVITY_MONITORING  = get_env_var('ENABLE_ACTIVITY_MONITORING', 'true').lower() == 'true'
    ACTIVITY_THRESHOLD          = float(get_env_var('ACTIVITY_THRESHOLD', '60'))
    CONSECUTIVE_LOW_DAYS        = int(get_env_var('CONSECUTIVE_LOW_DAYS', '3'))
    ACTIVITY_CHECK_SCREENSHOTS  = get_env_var('ACTIVITY_CHECK_SCREENSHOTS', 'true').lower() == 'true'

    # Combined Monitoring
    ENABLE_COMBINED_MONITORING  = get_env_var('ENABLE_COMBINED_MONITORING', 'true').lower() == 'true'
    CRITICAL_ALERT_THRESHOLD    = float(get_env_var('CRITICAL_ALERT_THRESHOLD', '40'))

    # Senior Management
    SENIOR_MANAGEMENT_EMAILS    = get_env_var('SENIOR_MANAGEMENT_EMAILS', '').split(',') if get_env_var('SENIOR_MANAGEMENT_EMAILS') else []

    # Report Generation
    GENERATE_PDF_REPORTS        = get_env_var('GENERATE_PDF_REPORTS', 'false').lower() == 'true'
    REPORT_STORAGE_PATH         = get_env_var('REPORT_STORAGE_PATH', 'reports/')

    # Enhanced Monitoring Schedule
    ACTIVITY_CHECK_SCHEDULE     = get_env_var('ACTIVITY_CHECK_SCHEDULE', 'daily')
    ACTIVITY_CHECK_TIME         = get_env_var('ACTIVITY_CHECK_TIME', '18:00')

    # Performance Thresholds
    PERFORMANCE_EXCELLENT       = float(get_env_var('PERFORMANCE_EXCELLENT', '90'))
    PERFORMANCE_GOOD            = float(get_env_var('PERFORMANCE_GOOD', '70'))
    PERFORMANCE_NEEDS_IMPROVEMENT = float(get_env_var('PERFORMANCE_NEEDS_IMPROVEMENT', '50'))

    # Slack Integration
    SLACK_BOT_TOKEN             = get_env_var('SLACK_BOT_TOKEN')
    SLACK_CHANNEL               = get_env_var('SLACK_CHANNEL', '#hr-alerts')

    # HTTP/Batching
    API_REQUEST_TIMEOUT         = int(get_env_var('API_REQUEST_TIMEOUT', '30'))
    MAX_RETRY_ATTEMPTS          = int(get_env_var('MAX_RETRY_ATTEMPTS', '3'))
    BATCH_SIZE                  = int(get_env_var('BATCH_SIZE', '10'))

    @classmethod
    def validate(cls) -> tuple[bool, list]:
        """Validate presence of required config vars"""
        required = [
            ('TEAMLOGGER_API_URL', cls.TEAMLOGGER_API_URL),
            ('TEAMLOGGER_BEARER_TOKEN', cls.TEAMLOGGER_BEARER_TOKEN),
            ('SMTP_USERNAME', cls.SMTP_USERNAME),
            ('SMTP_PASSWORD', cls.SMTP_PASSWORD),
            ('FROM_EMAIL', cls.FROM_EMAIL),
        ]
        missing = [name for name, val in required if not val]
        return (len(missing) == 0, missing)

    @classmethod
    def calculate_required_hours_for_leave_days(cls, leave_days: float) -> float:
        if leave_days >= cls.WORK_DAYS_PER_WEEK:
            return 0.0
        return cls.HOURS_PER_WORKING_DAY * (cls.WORK_DAYS_PER_WEEK - leave_days)

    @classmethod
    def calculate_acceptable_hours_for_leave_days(cls, leave_days: float) -> float:
        req = cls.calculate_required_hours_for_leave_days(leave_days)
        return max(0.0, req - cls.HOURS_BUFFER) if req > 0 else 0.0

    @classmethod
    def determine_employee_status(cls, actual_hours: float, leave_days: float, is_excluded: bool = False) -> dict:
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
        required = cls.calculate_required_hours_for_leave_days(leave_days)
        acceptable = cls.calculate_acceptable_hours_for_leave_days(leave_days)
        if leave_days >= cls.WORK_DAYS_PER_WEEK:
            return {
                'status': 'full_leave',
                'display_status': '🏖️ Full Leave (Protected)',
                'alert_needed': False,
                'required_hours': required,
                'acceptable_hours': acceptable,
                'actual_hours': actual_hours,
                'leave_days': leave_days,
                'explanation': f'On full week leave ({leave_days} days)'
            }
        if actual_hours >= acceptable:
            return {
                'status': 'meeting_requirements',
                'display_status': '✅ Meeting Requirements',
                'alert_needed': False,
                'required_hours': required,
                'acceptable_hours': acceptable,
                'actual_hours': actual_hours,
                'leave_days': leave_days,
                'explanation': f'{actual_hours:.1f}h ≥ {acceptable:.1f}h'
            }
        # Alert required
        shortfall = required - actual_hours
        return {
            'status': 'alert_required',
            'display_status': '🔴 Alert Required',
            'alert_needed': True,
            'required_hours': required,
            'acceptable_hours': acceptable,
            'actual_hours': actual_hours,
            'leave_days': leave_days,
            'shortfall': shortfall,
            'shortfall_minutes': int(shortfall * 60),
            'explanation': f'{actual_hours:.1f}h < {acceptable:.1f}h'
        }

    @classmethod
    def should_send_alert(cls, actual_hours: float, leave_days: float) -> tuple[bool, dict]:
        info = cls.determine_employee_status(actual_hours, leave_days)
        return info['alert_needed'], info

    @classmethod
    def get_config_summary(cls) -> dict:
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'work_schedule': {
                'minimum_hours_per_week': cls.MINIMUM_HOURS_PER_WEEK,
                'acceptable_hours_per_week': cls.ACCEPTABLE_HOURS_PER_WEEK,
                'hours_buffer': cls.HOURS_BUFFER,
                'work_days_per_week': cls.WORK_DAYS_PER_WEEK,
                'hours_per_working_day': cls.HOURS_PER_WORKING_DAY,
                'half_day_hours': cls.HOURS_PER_HALF_DAY,
            },
            'execution_schedule': {
                'day': 'Monday',
                'time': f'{cls.EXECUTION_HOUR:02d}:{cls.EXECUTION_MINUTE:02d}',
                'timezone': cls.TIMEZONE
            },
            'features': {
                'email_alerts': cls.ENABLE_EMAIL_ALERTS,
                'openai_enhancement': cls.ENABLE_OPENAI_ENHANCEMENT and bool(cls.OPENAI_API_KEY),
                'ai_intelligent_decisions': cls.ENABLE_AI_INTELLIGENT_DECISIONS and bool(cls.OPENAI_API_KEY),
            },
            'excluded_employees': cls.EXCLUDED_EMPLOYEES
        }

    @classmethod
    def is_working_day(cls, weekday: int) -> bool:
        return weekday not in cls.WEEKEND_DAYS

    @classmethod
    def format_leave_days(cls, leave_days: float) -> str:
        if leave_days == int(leave_days):
            return f"{int(leave_days)} day{'s' if leave_days != 1 else ''}"
        else:
            full = int(leave_days)
            return f"{full}.5 days" if full else "0.5 day"
