"""
Configuration Page - Updated with AI Settings and Fixed Hours Display
ENHANCED: AI Intelligence Settings + Corrected 5-Day Calculations + AI Testing
"""

import streamlit as st
from datetime import datetime
import json
import os

from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from src.email_service import EmailService
from config.settings import Config

st.set_page_config(
    page_title="Configuration - Employee Hours",
    page_icon="⚙️",
    layout="wide"
)

def mask_sensitive_value(value, mask_percentage=0.7):
    """Mask sensitive configuration values"""
    if not value:
        return "Not configured"
    
    value_str = str(value)
    visible_chars = int(len(value_str) * (1 - mask_percentage))
    if visible_chars < 3:
        return "*" * len(value_str)
    
    return value_str[:visible_chars] + "*" * (len(value_str) - visible_chars)

def test_teamlogger_connection():
    """Test TeamLogger API connection"""
    try:
        teamlogger = TeamLoggerClient()
        status = teamlogger.get_api_status()
        
        if status['connected']:
            return {
                'status': 'success',
                'message': f"Connected successfully. Found {status['employee_count']} employees.",
                'details': status
            }
        else:
            return {
                'status': 'error',
                'message': "Connection failed",
                'details': status
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Connection error: {str(e)}",
            'details': None
        }

def test_google_sheets_connection():
    """Test Google Sheets connection"""
    try:
        sheets = GoogleSheetsLeaveClient()
        validation = sheets.validate_google_sheets_connection()
        
        return {
            'status': validation.get('status', 'error'),
            'message': validation.get('message', 'Unknown error'),
            'details': validation
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Connection error: {str(e)}",
            'details': None
        }

def test_email_service():
    """Test email service configuration"""
    try:
        email = EmailService()
        if email.test_email_configuration():
            return {
                'status': 'success',
                'message': "Email service configured correctly",
                'details': {
                    'smtp_host': Config.SMTP_HOST,
                    'smtp_port': Config.SMTP_PORT,
                    'from_email': Config.FROM_EMAIL,
                    'cc_emails': email.cc_emails
                }
            }
        else:
            return {
                'status': 'error',
                'message': "Email configuration test failed",
                'details': None
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Email service error: {str(e)}",
            'details': None
        }

def test_ai_intelligence():
    """Test AI intelligence capabilities"""
    try:
        from src.workflow_manager import WorkflowManager
        workflow = WorkflowManager()
        
        if hasattr(workflow, 'openai_client') and workflow.openai_client:
            # Test AI decision making with sample data
            test_decision = workflow._ai_enhanced_decision(
                employee_name="Test Employee",
                actual_hours=35.5,
                required_hours=40.0,
                acceptable_hours=37.0,
                leave_days=0
            )
            
            if test_decision and test_decision.get('action') in ['send_alert', 'no_alert']:
                return {
                    'status': 'success',
                    'message': "AI intelligence working correctly",
                    'details': {
                        'openai_configured': True,
                        'test_decision': test_decision,
                        'features': {
                            'smart_decisions': True,
                            'personalized_messages': True,
                            'context_analysis': True,
                            'intelligent_overrides': True
                        }
                    }
                }
            else:
                return {
                    'status': 'error',
                    'message': "AI returned invalid decision",
                    'details': test_decision
                }
        else:
            return {
                'status': 'warning',
                'message': "AI intelligence not configured (OPENAI_API_KEY missing)",
                'details': {
                    'openai_configured': False,
                    'features': {
                        'smart_decisions': False,
                        'personalized_messages': False,
                        'context_analysis': False,
                        'intelligent_overrides': False
                    }
                }
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"AI intelligence test failed: {str(e)}",
            'details': None
        }

def send_test_email(recipient_email):
    """Send a test email"""
    try:
        email_service = EmailService()
        
        # Create test email data
        test_data = {
            'email': recipient_email,
            'name': 'Test User',
            'week_start': datetime.now().strftime('%Y-%m-%d'),
            'week_end': datetime.now().strftime('%Y-%m-%d'),
            'total_hours': 35.5,
            'required_hours': 40.0,
            'shortfall': 4.5,
            'shortfall_minutes': 270,
            'days_worked': 5,
            'leave_days': 0,
            'ai_personalized_message': 'This is a test message generated by the AI-enhanced system.'
        }
        
        # Send test email
        if email_service.send_low_hours_alert(test_data):
            return True, "Test email sent successfully!"
        else:
            return False, "Failed to send test email"
    
    except Exception as e:
        return False, f"Error sending test email: {str(e)}"

# Main page
st.title("⚙️ System Configuration")
st.markdown("View system settings and test component connections (AI-Enhanced 5-Day Work System)")

# Configuration Overview
st.subheader("📋 Configuration Overview")

# Create tabs for different configuration sections
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔧 General Settings", 
    "📊 Work Schedule", 
    "🤖 AI Intelligence",
    "🔌 API Connections", 
    "📧 Email Settings",
    "🧪 Connection Tests"
])

with tab1:
    st.markdown("### General Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**App Name:** {Config.APP_NAME}")
        st.info(f"**Version:** {Config.APP_VERSION}")
        st.info(f"**Environment:** {'Production' if Config.is_production() else 'Development'}")
        st.info(f"**Timezone:** {Config.TIMEZONE}")
        st.info(f"**System Type:** AI-Enhanced 5-Day Work System")
    
    with col2:
        st.info(f"**Log Level:** {Config.LOG_LEVEL}")
        st.info(f"**Log File:** {Config.LOG_FILE}")
        st.info(f"**API Timeout:** {Config.API_REQUEST_TIMEOUT} seconds")
        st.info(f"**Max Retries:** {Config.MAX_RETRY_ATTEMPTS}")
        st.info(f"**Monitoring Period:** {Config.MONITORING_PERIOD_DAYS} days (Mon-Sun)")
    
    # Feature flags
    st.markdown("### Feature Flags")

    # Debug: Show the actual value being read
    st.write(f"**DEBUG:** ENABLE_EMAIL_ALERTS = {Config.ENABLE_EMAIL_ALERTS} (type: {type(Config.ENABLE_EMAIL_ALERTS)})")

    # Debug: Show what get_env_var is returning
    import os
    import streamlit as st
    from config.settings import get_env_var

    env_value = os.getenv('ENABLE_EMAIL_ALERTS', 'NOT_SET')
    try:
        secrets_value = st.secrets.get('ENABLE_EMAIL_ALERTS', 'NOT_SET')
    except:
        secrets_value = 'ERROR_READING_SECRETS'

    get_env_result = get_env_var('ENABLE_EMAIL_ALERTS', 'DEFAULT_FALSE')

    st.write(f"**DEBUG:** OS Environment = '{env_value}'")
    st.write(f"**DEBUG:** Streamlit Secrets = '{secrets_value}'")
    st.write(f"**DEBUG:** get_env_var result = '{get_env_result}'")
    st.write(f"**DEBUG:** get_env_var.lower() == 'true' = {get_env_result.lower() == 'true' if get_env_result else 'N/A'}")

    features = {
        "Email Alerts": Config.ENABLE_EMAIL_ALERTS,
        "AI Intelligence": Config.ENABLE_OPENAI_ENHANCEMENT,
        "Slack Notifications": Config.ENABLE_SLACK_NOTIFICATIONS,
        "Activity Monitoring": Config.ENABLE_ACTIVITY_MONITORING,
        "Combined Monitoring": Config.ENABLE_COMBINED_MONITORING,
        "Generate PDF Reports": Config.GENERATE_PDF_REPORTS
    }

    cols = st.columns(3)
    for idx, (feature, enabled) in enumerate(features.items()):
        with cols[idx % 3]:
            if enabled:
                if feature == "AI Intelligence":
                    st.success(f"🤖 {feature}")
                else:
                    st.success(f"✅ {feature}")
            else:
                if feature == "Email Alerts":
                    st.error(f"❌ {feature} (DISABLED)")
                elif feature == "AI Intelligence":
                    st.error(f"🤖 {feature}")
                else:
                    st.error(f"❌ {feature}")
    
    # Excluded employees section
    st.markdown("### Excluded Employees")
    st.warning("⚠️ The following employees will NOT receive alert emails:")
    for employee in Config.EXCLUDED_EMPLOYEES:
        st.write(f"- **{employee}**")

with tab2:
    st.markdown("### AI-Enhanced 5-Day Work System Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Work Schedule Settings**")
        st.write(f"- **System Type:** AI-Enhanced 5-Day Work System")
        st.write(f"- **Work Days:** {Config.WORK_DAYS_PER_WEEK} days (Monday-Friday)")
        st.write(f"- **Required Hours:** {Config.MINIMUM_HOURS_PER_WEEK} hours per week")
        st.write(f"- **Hours per Day:** {Config.HOURS_PER_WORKING_DAY} hours per working day")  # ✅ Now shows 8
        st.write(f"- **Buffer:** {Config.HOURS_BUFFER} hours (flexibility allowance)")
        st.write(f"- **Acceptable Hours:** {Config.ACCEPTABLE_HOURS_PER_WEEK}+ hours (with buffer)")
        st.write(f"- **Weekend Policy:** Saturday-Sunday available for completion")
        st.write(f"- **Monitoring Period:** {Config.MONITORING_PERIOD_DAYS} days (Mon-Sun)")
    
    with col2:
        st.markdown("**Execution Schedule**")
        st.write(f"- **Primary Execution:** Monday at {Config.EXECUTION_HOUR:02d}:{Config.EXECUTION_MINUTE:02d}")
        st.write(f"- **Backup Execution:** Tuesday at {Config.EXECUTION_HOUR:02d}:{Config.EXECUTION_MINUTE:02d}")
        st.write(f"- **Preview Schedule:** Friday at 18:00")
        st.write(f"- **Check Interval:** Every {Config.CHECK_INTERVAL_HOURS} hours")
        st.write(f"- **Timezone:** {Config.TIMEZONE}")
        st.write(f"- **Alert Days:** Monday/Tuesday only")
        st.write(f"- **Min Shortfall:** {Config.MINIMUM_SHORTFALL_MINUTES} minutes")
    
    # Leave calculation examples
    st.markdown("### Leave Day Calculations (AI-Enhanced 5-Day Work System)")
    st.info("💡 **✅ Corrected Formula:** Required Hours = 8 × (5 - leave_days)")
    
    leave_calc_data = []
    for days in range(6):
        required = Config.calculate_required_hours_for_leave_days(days)
        acceptable = Config.calculate_acceptable_hours_for_leave_days(days)
        
        if days == 5:
            note = '🏖️ Full week leave - NO ALERT SENT'
            status = '✅ Protected'
        elif days == 0:
            note = '📋 Full work week'
            status = '⚡ Standard'
        else:
            note = f'{5-days} working days available'
            status = '📉 Reduced'
        
        leave_calc_data.append({
            'Leave Days': days,
            'Working Days': max(0, 5 - days),
            'Required Hours': required,
            'Acceptable Hours': acceptable if required > 0 else 0,
            'Status': status,
            'Note': note
        })
    
    st.dataframe(leave_calc_data, width="stretch", hide_index=True)
    
    # Alert logic explanation
    st.markdown("### Alert Logic")
    st.success("✅ **No Alert Conditions:**")
    st.write("- Employee on full week leave (5 days)")
    st.write("- Hours worked ≥ acceptable hours (with 3-hour buffer)")
    st.write("- Shortfall less than 10 minutes (negligible)")
    st.write("- Employee in excluded list")
    st.write("- 🤖 AI intelligent override (context-aware)")
    
    st.error("🚨 **Alert Sent Conditions:**")
    st.write("- Hours worked < acceptable hours (after buffer)")
    st.write("- Shortfall ≥ 10 minutes")
    st.write("- Less than 5 days leave taken")
    st.write("- Employee not in excluded list")
    st.write("- 🤖 AI confirms alert is constructive")

with tab3:
    st.markdown("### 🤖 AI Intelligence Configuration")
    
    # AI Status
    ai_status = Config.get_ai_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**AI Configuration**")
        if ai_status['enabled']:
            st.success("🤖 **AI Intelligence:** ✅ Enabled")
            st.success(f"🔑 **API Key:** {'✅ Configured' if ai_status['api_key_configured'] else '❌ Missing'}")
        else:
            st.error("🤖 **AI Intelligence:** ❌ Disabled")
            st.error("🔑 **API Key:** ❌ Not Configured")
        
        if Config.OPENAI_API_KEY:
            st.text_input("OpenAI API Key", value=mask_sensitive_value(Config.OPENAI_API_KEY), disabled=True)
        else:
            st.warning("⚠️ Add OPENAI_API_KEY to enable AI features")
    
    with col2:
        st.markdown("**AI Features**")
        features = ai_status['features']
        
        for feature, enabled in features.items():
            feature_name = feature.replace('_', ' ').title()
            if enabled:
                st.success(f"✅ {feature_name}")
            else:
                st.error(f"❌ {feature_name}")
    
    # AI Capabilities
    st.markdown("### 🧠 AI Capabilities")
    
    if ai_status['enabled']:
        st.info("🤖 **AI-Enhanced Decision Making:**")
        st.write("- **Context Analysis:** Analyzes employee situations beyond just numbers")
        st.write("- **Smart Overrides:** Prevents unnecessary alerts for edge cases")
        st.write("- **Confidence Scoring:** Provides High/Medium/Low confidence ratings")
        st.write("- **Personalized Messages:** Generates custom email content")
        st.write("- **Pattern Recognition:** Learns from employee work patterns")
        st.write("- **Constructive Alerts:** Only sends alerts that would be helpful")
    else:
        st.warning("🤖 **AI Features Disabled:**")
        st.write("- Standard rule-based alert system active")
        st.write("- No intelligent overrides or personalized messages")
        st.write("- Add OPENAI_API_KEY to environment to enable AI features")
    
    # AI Examples
    st.markdown("### 🧪 AI Decision Examples")
    
    example_scenarios = [
        {
            "scenario": "Employee worked 36h with 0 leave days",
            "standard": "🚨 Send Alert (36h < 37h threshold)",
            "ai": "🤖 May override if good faith effort detected"
        },
        {
            "scenario": "Employee worked 35h with 1 leave day",
            "standard": "🚨 Send Alert (35h < 29h threshold)",
            "ai": "🤖 Likely alert with personalized context"
        },
        {
            "scenario": "Employee worked 21.5h with 2 leave days",
            "standard": "✅ No Alert (21.5h > 21h threshold)",
            "ai": "✅ Confirms no alert needed"
        }
    ]
    
    for example in example_scenarios:
        with st.expander(f"Scenario: {example['scenario']}"):
            st.write(f"**Standard Logic:** {example['standard']}")
            st.write(f"**AI Enhanced:** {example['ai']}")

with tab4:
    st.markdown("### API Connections")
    
    # TeamLogger Configuration
    st.markdown("#### 🔗 TeamLogger API")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.text_input("API URL", value=Config.TEAMLOGGER_API_URL or "", disabled=True)
        st.text_input("Bearer Token", value=mask_sensitive_value(Config.TEAMLOGGER_BEARER_TOKEN), disabled=True)
    
    # Google Sheets Configuration
    st.markdown("#### 📊 Google Sheets")
    st.text_input("Sheet ID", value=Config.GOOGLE_SHEETS_ID or "", disabled=True)
    st.text_input("Sheet URL", value=Config.GOOGLE_SHEETS_URL or "", disabled=True)
    if Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL:
        st.text_input("Published CSV URL", value=Config.GOOGLE_SHEETS_PUBLISHED_CSV_URL, disabled=True)
    
    # OpenAI Configuration
    st.markdown("#### 🤖 OpenAI (AI Intelligence)")
    if Config.OPENAI_API_KEY:
        st.text_input("API Key", value=mask_sensitive_value(Config.OPENAI_API_KEY), disabled=True)
        st.success("🔥 AI-enhanced email generation and decision making is enabled")
    else:
        st.warning("⚠️ OpenAI integration is disabled - Add OPENAI_API_KEY to enable")

with tab5:
    st.markdown("### Email Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**SMTP Settings**")
        st.write(f"- Host: **{Config.SMTP_HOST}**")
        st.write(f"- Port: **{Config.SMTP_PORT}**")
        st.write(f"- Username: **{Config.SMTP_USERNAME}**")
        st.write(f"- Password: {mask_sensitive_value(Config.SMTP_PASSWORD)}")
    
    with col2:
        st.markdown("**Email Settings**")
        st.write(f"- From Email: **{Config.FROM_EMAIL}**")
        st.write(f"- Constant CC: **{Config.CONSTANT_CC_EMAIL}**")
        st.write(f"- Additional CC: **{len(Config.ALERT_CC_EMAILS)}** recipients")
        st.write(f"- Manager CC: **✅ Enabled** (auto-added per employee)")
        
        if Config.ALERT_CC_EMAILS:
            with st.expander("View CC Recipients"):
                for email in Config.ALERT_CC_EMAILS:
                    st.write(f"- {email}")
    
    # Email flow explanation
    st.markdown("### Email Flow (AI-Enhanced 5-Day Work System)")
    st.info("📧 **Email Recipients for Each Alert:**")
    st.write("1. **To:** Employee who needs alert")
    st.write("2. **CC:** Employee's assigned manager (from manager mapping)")
    st.write("3. **CC:** teamhr@rapidinnovation.dev (always included)")
    st.write("4. **CC:** Additional CC emails (if configured)")
    st.write("5. **🤖 AI Enhancement:** Personalized message content based on context")
    
    st.warning("🚫 **Excluded from Emails:**")
    for employee in Config.EXCLUDED_EMPLOYEES:
        st.write(f"- {employee}")
    
    # Test email section
    st.markdown("---")
    st.markdown("### 📧 Send Test Email")
    
    test_email = st.text_input("Recipient Email for Test", placeholder="test@example.com")
    if st.button("Send AI-Enhanced Test Email", disabled=not test_email):
        with st.spinner("Sending AI-enhanced test email..."):
            success, message = send_test_email(test_email)
            if success:
                st.success(message)
            else:
                st.error(message)

with tab6:
    st.markdown("### 🧪 Component Connection Tests")
    
    # Test all connections button
    if st.button("🔄 Run All Tests", width="stretch"):
        with st.spinner("Testing all connections..."):
            
            # TeamLogger Test
            st.markdown("#### TeamLogger API")
            teamlogger_result = test_teamlogger_connection()
            if teamlogger_result['status'] == 'success':
                st.success(f"✅ {teamlogger_result['message']}")
                with st.expander("View Details"):
                    st.json(teamlogger_result['details'])
            else:
                st.error(f"❌ {teamlogger_result['message']}")
            
            # Google Sheets Test
            st.markdown("#### Google Sheets")
            sheets_result = test_google_sheets_connection()
            if sheets_result['status'] == 'success':
                st.success(f"✅ {sheets_result['message']}")
                with st.expander("View Details"):
                    st.json(sheets_result['details'])
            else:
                st.error(f"❌ {sheets_result['message']}")
            
            # Email Service Test
            st.markdown("#### Email Service")
            email_result = test_email_service()
            if email_result['status'] == 'success':
                st.success(f"✅ {email_result['message']}")
                with st.expander("View Details"):
                    st.json(email_result['details'])
            else:
                st.error(f"❌ {email_result['message']}")
            
            # AI Intelligence Test
            st.markdown("#### 🤖 AI Intelligence")
            ai_result = test_ai_intelligence()
            if ai_result['status'] == 'success':
                st.success(f"✅ {ai_result['message']}")
                with st.expander("View AI Test Details"):
                    st.json(ai_result['details'])
            elif ai_result['status'] == 'warning':
                st.warning(f"⚠️ {ai_result['message']}")
                with st.expander("View AI Status"):
                    st.json(ai_result['details'])
            else:
                st.error(f"❌ {ai_result['message']}")
    
    # Individual test buttons
    st.markdown("---")
    st.markdown("### Individual Tests")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Test TeamLogger", width="stretch"):
            result = test_teamlogger_connection()
            if result['status'] == 'success':
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    with col2:
        if st.button("Test Google Sheets", width="stretch"):
            result = test_google_sheets_connection()
            if result['status'] == 'success':
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    with col3:
        if st.button("Test Email", width="stretch"):
            result = test_email_service()
            if result['status'] == 'success':
                st.success(result['message'])
            else:
                st.error(result['message'])
    
    with col4:
        if st.button("🤖 Test AI", width="stretch"):
            result = test_ai_intelligence()
            if result['status'] == 'success':
                st.success("🤖 AI Intelligence Working!")
                st.json(result['details']['test_decision'])
            elif result['status'] == 'warning':
                st.warning(result['message'])
            else:
                st.error(result['message'])

# Configuration validation
st.markdown("---")
st.subheader("🔍 Configuration Validation")

is_valid, missing_configs = Config.validate()

if is_valid:
    st.success("✅ All required configurations are properly set!")
else:
    st.error(f"❌ Missing required configurations: {', '.join(missing_configs)}")
    
    with st.expander("How to fix"):
        st.markdown("""
        1. Create or update your `.env` file in the project root
        2. Add the missing configuration values:
        """)
        for config in missing_configs:
            st.code(f"{config}=your_value_here")

# System Summary
st.markdown("---")
st.subheader("📊 System Summary")

config_summary = Config.get_config_summary()
ai_status = Config.get_ai_status()

col1, col2 = st.columns(2)

with col1:
    st.markdown("**System Information**")
    st.write(f"- **App:** {config_summary['app_name']}")
    st.write(f"- **Version:** {config_summary['app_version']}")
    st.write(f"- **System:** {config_summary['work_schedule']['system_type']}")
    st.write(f"- **Work Days:** {config_summary['work_schedule']['work_days_per_week']} (Mon-Fri)")
    st.write(f"- **Required Hours:** {config_summary['work_schedule']['minimum_hours_per_week']}h/week")
    st.write(f"- **Hours per Day:** {config_summary['work_schedule']['hours_per_working_day']}h/day")  # ✅ Now shows 8h
    st.write(f"- **Acceptable:** {config_summary['work_schedule']['acceptable_hours_per_week']}h+ (buffer: {config_summary['work_schedule']['hours_buffer']}h)")

with col2:
    st.markdown("**Operational Status**")
    if config_summary['features']['email_alerts']:
        st.write(f"- **Email Alerts:** ✅ Enabled")
    else:
        st.write(f"- **Email Alerts:** 🔍 Preview Mode (No emails sent)")
    st.write(f"- **🤖 AI Intelligence:** {'✅ Enabled' if config_summary['features']['openai_enhancement'] else '❌ Disabled'}")
    st.write(f"- **Slack Notifications:** {'✅ Enabled' if config_summary['features']['slack_notifications'] else '❌ Disabled'}")
    st.write(f"- **Excluded Employees:** {len(Config.EXCLUDED_EMPLOYEES)} employees")
    st.write(f"- **Execution Day:** {config_summary['execution_schedule']['day']}")
    st.write(f"- **Execution Time:** {config_summary['execution_schedule']['time']}")
    st.write(f"- **CC Recipients:** {config_summary['cc_emails_count']} + managers + HR")

# AI Status Summary
if ai_status['enabled']:
    st.success("🤖 **AI Intelligence Summary**")
    st.write("- Smart decision making for edge cases")
    st.write("- Personalized email content generation")
    st.write("- Confidence scoring for all decisions")
    st.write("- Intelligent override capabilities")
    st.write("- Context-aware pattern analysis")
else:
    st.warning("🤖 **AI Intelligence Disabled**")
    st.write("- Using standard rule-based system")
    st.write("- No personalized messages")
    st.write("- No intelligent overrides")
    st.write("- Add OPENAI_API_KEY to enable AI features")

# Help section
with st.expander("❓ Help - AI-Enhanced Configuration"):
    st.markdown("""
    ### AI-Enhanced Configuration Management Guide
    
    **Viewing Settings**
    - All sensitive values (tokens, passwords) are masked for security
    - Configuration is loaded from environment variables and .env file
    - AI features automatically enable when OPENAI_API_KEY is configured
    
    **Testing Connections**
    - Use the test buttons to verify each component is properly configured
    - Run all tests to get a complete system health check
    - 🤖 AI test validates OpenAI integration and decision making
    
    **5-Day Work System Features**
    - Work 5 days (Monday-Friday) but have full week to complete 40 hours
    - **✅ Corrected:** 8 hours per working day (fixed calculation)
    - Weekend days (Saturday-Sunday) available for hour completion
    - 3-hour buffer provides flexibility (37+ hours acceptable)
    - Only working day leaves (Mon-Fri) reduce required hours
    - Full week leave (5 days) = no alert sent automatically
    
    **🤖 AI Intelligence Features**
    - **Smart Decisions:** Context-aware analysis beyond just numbers
    - **Confidence Scoring:** High/Medium/Low confidence in decisions
    - **Intelligent Overrides:** Prevent unnecessary alerts for edge cases
    - **Personalized Messages:** Custom email content based on situation
    - **Pattern Recognition:** Learn from employee work patterns
    - **Constructive Alerts:** Only send alerts that would be helpful
    
    **Alert System**
    - Alerts sent only on Monday/Tuesday for previous week
    - Each alert CC'd to employee's manager + HR team
    - Excluded employees never receive alerts
    - Negligible shortfalls (<10 minutes) ignored
    - 🤖 AI can intelligently override alerts when appropriate
    
    **Modifying Configuration**
    - Edit the `.env` file in your project root to change settings
    - Restart the application after making changes
    - Add OPENAI_API_KEY to enable AI features
    
    **Common Issues**
    - **TeamLogger fails**: Check API URL and bearer token
    - **Google Sheets fails**: Verify sheet ID and permissions
    - **Email fails**: Check SMTP settings and app password
    - **AI fails**: Verify OPENAI_API_KEY and network connectivity
    - **No manager CC**: Verify manager mapping configuration
    
    ### Environment Variables
    All configuration is managed through environment variables. 
    See the `.env.example` file for required variables.
    
    ### Excluded Employees
    The following employees are excluded from receiving alert emails:
    - Aishik Chatterjee
    - Tirtharaj Bhoumik  
    - Vishal Kumar
    
    To modify this list, update the `EXCLUDED_EMPLOYEES` list in `settings.py`.
    
    ### AI Configuration
    To enable AI features:
    1. Get an OpenAI API key from https://platform.openai.com/
    2. Add `OPENAI_API_KEY=your_key_here` to your .env file
    3. Restart the application
    4. AI features will automatically activate
    """)