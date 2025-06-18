"""
Employee Hours Monitoring System - AI-Enhanced Streamlit Dashboard
Main application entry point with AI intelligence and corrected hours display
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
from typing import Dict, List
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging first
from config.settings import Config
from src.utils import setup_logging
setup_logging(Config.LOG_LEVEL, Config.LOG_FILE)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI-Enhanced Employee Hours Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1) Setup OpenAI BEFORE importing WorkflowManager
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
ENABLE_OPENAI = st.secrets.get("ENABLE_OPENAI_ENHANCEMENT", os.getenv("ENABLE_OPENAI_ENHANCEMENT", "false")).lower() == "true"

# 2) If we have the key and it's enabled, set it up
if OPENAI_API_KEY and ENABLE_OPENAI:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        logger.info("OpenAI API key configured successfully")
    except Exception as e:
        logger.error(f"Error setting up OpenAI: {e}")
        st.error(f"Error setting up OpenAI: {e}")
else:
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not found in secrets or environment")
    if not ENABLE_OPENAI:
        logger.warning("ENABLE_OPENAI_ENHANCEMENT is not set to true")

# 3) NOW import WorkflowManager and other components AFTER OpenAI setup
from src.workflow_manager import WorkflowManager
from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from src.email_service import EmailService

# Initialize session state
if 'workflow_manager' not in st.session_state:
    st.session_state.workflow_manager = WorkflowManager()
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
if 'system_status' not in st.session_state:
    st.session_state.system_status = {}

# Custom CSS for AI theme
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-metric { color: #28a745; }
    .warning-metric { color: #ffc107; }
    .danger-metric { color: #dc3545; }
    .info-metric { color: #17a2b8; }
    .ai-metric { color: #6f42c1; }
    .ai-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def get_system_status():
    """Get current system status and connectivity including AI status"""
    status = {
        'teamlogger': False,
        'google_sheets': False,
        'email': False,
        'ai_intelligence': False,
        'current_time': datetime.now(),
        'next_run': None,
        'is_alert_day': False
    }
    
    try:
        # Check TeamLogger
        teamlogger = TeamLoggerClient()
        api_status = teamlogger.get_api_status()
        status['teamlogger'] = api_status.get('connected', False)
        status['employee_count'] = api_status.get('employee_count', 0)
        
        # Check Google Sheets
        sheets = GoogleSheetsLeaveClient()
        sheets_status = sheets.validate_google_sheets_connection()
        status['google_sheets'] = sheets_status.get('status') == 'success'
        
        # Check Email Service
        email = EmailService()
        status['email'] = email.test_email_configuration()
        
        # Check AI Intelligence - Updated check
        workflow = st.session_state.workflow_manager
        # Check if OpenAI is actually configured in the workflow manager
        status['ai_intelligence'] = (
            hasattr(workflow, 'openai_client') and 
            workflow.openai_client is not None and
            Config.ENABLE_OPENAI_ENHANCEMENT and
            bool(Config.OPENAI_API_KEY)
        )
        
        # Debug logging
        logger.info(f"AI Intelligence Status Check:")
        logger.info(f"  - Has openai_client: {hasattr(workflow, 'openai_client')}")
        logger.info(f"  - openai_client is not None: {hasattr(workflow, 'openai_client') and workflow.openai_client is not None}")
        logger.info(f"  - ENABLE_OPENAI_ENHANCEMENT: {Config.ENABLE_OPENAI_ENHANCEMENT}")
        logger.info(f"  - Has API Key: {bool(Config.OPENAI_API_KEY)}")
        logger.info(f"  - Final AI status: {status['ai_intelligence']}")
        
        # Check scheduling
        status['is_alert_day'] = workflow.should_send_alerts_today()
        status['is_optimal_time'] = workflow.is_optimal_execution_time()
        
        # Calculate next run time
        now = datetime.now()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.hour >= 8:
            days_until_monday = 7
        next_monday = now + timedelta(days=days_until_monday)
        status['next_run'] = next_monday.replace(hour=8, minute=0, second=0, microsecond=0)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        st.error(f"Error getting system status: {str(e)}")
    
    return status

def create_metric_card(title, value, delta=None, delta_color="normal", icon=None):
    """Create a styled metric card"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.metric(title, value, delta)
    with col2:
        if icon:
            st.markdown(f"<h1>{icon}</h1>", unsafe_allow_html=True)

def display_dashboard():
    """Display main AI-enhanced dashboard"""
    st.title("🤖 AI-Enhanced Employee Hours Monitoring System")
    st.markdown("### 5-Day Work Week Monitor with AI Intelligence (Monday-Friday)")
    
    # Get system status
    with st.spinner("Checking system status and AI intelligence..."):
        status = get_system_status()
        st.session_state.system_status = status
    
    # System Status Row with AI
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if status['teamlogger']:
            st.success(f"✅ TeamLogger Connected ({status.get('employee_count', 0)} employees)")
        else:
            st.error("❌ TeamLogger Disconnected")
    
    with col2:
        if status['google_sheets']:
            st.success("✅ Google Sheets Connected")
        else:
            st.error("❌ Google Sheets Disconnected")
    
    with col3:
        if status['email']:
            st.success("✅ Email Service Ready")
        else:
            st.error("❌ Email Service Error")
    
    with col4:
        if status['ai_intelligence']:
            st.success("🤖 AI Intelligence Active")
        else:
            st.warning("🤖 AI Intelligence Inactive")
    
    with col5:
        if status['is_alert_day']:
            st.info("📅 Alert Day (Monday/Tuesday)")
        else:
            st.info(f"⏰ Next Run: {status['next_run'].strftime('%A %H:%M')}")
    
    # AI Status Banner
    if status['ai_intelligence']:
        st.markdown("""
        <div class="ai-card">
            <h3>🤖 AI Intelligence Enabled</h3>
            <p>Smart decision making • Confidence scoring • Intelligent overrides • Personalized messages</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # More detailed message about why AI is disabled
        if not Config.OPENAI_API_KEY:
            st.warning("🤖 **AI Intelligence Disabled** - OPENAI_API_KEY not found in configuration")
        elif not Config.ENABLE_OPENAI_ENHANCEMENT:
            st.warning("🤖 **AI Intelligence Disabled** - ENABLE_OPENAI_ENHANCEMENT is not set to true")
        else:
            st.warning("🤖 **AI Intelligence Disabled** - WorkflowManager not properly initialized with OpenAI")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("🚀 AI-Enhanced Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 AI Preview Mode", use_container_width=True, help="See who would get alerts with AI analysis"):
            with st.spinner("Generating AI-enhanced preview..."):
                preview_alerts()
    
    with col2:
        if st.button("📊 Generate AI Report", use_container_width=True, help="Generate work week statistics with AI insights"):
            generate_work_week_report()
    
    with col3:
        if st.button("🧪 Test AI Components", use_container_width=True, help="Test all system components including AI"):
            test_system_components()
    
    with col4:
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.rerun()
    
    # Work Week Summary
    st.markdown("---")
    display_work_week_summary()
    
    # Configuration Summary
    st.markdown("---")
    display_configuration_summary()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Last refreshed: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        st.caption(f"Version: {Config.APP_VERSION} (AI-Enhanced)")
    with col3:
        ai_status = "AI-Enabled" if status['ai_intelligence'] else "Standard"
        st.caption(f"Mode: {ai_status}")

def preview_alerts():
    """Preview who would receive alerts with AI analysis"""
    workflow = st.session_state.workflow_manager
    
    try:
        # Get employees needing alerts
        employees_needing_alerts = workflow.get_employees_needing_real_alerts()
        
        if not employees_needing_alerts:
            st.success("✅ No employees need alerts for the previous work week!")
            work_week_start, work_week_end = workflow._get_monitoring_period()
            st.info(f"All employees met their hour requirements for {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")
        else:
            st.warning(f"⚠️ {len(employees_needing_alerts)} employees would receive alerts:")
            
            # Create DataFrame for display
            alert_data = []
            for item in employees_needing_alerts:
                employee = item['employee']
                weekly_data = item['weekly_data']
                
                alert_data.append({
                    'Name': employee['name'],
                    'Email': employee['email'],
                    'Hours Worked': f"{weekly_data['total_hours']:.2f}h",
                    'Required Hours': f"{item['required_hours']:.1f}h",
                    'Acceptable Hours': f"{item['acceptable_hours']:.1f}h",
                    'Shortfall': f"{item['shortfall']:.2f}h",
                    'Leave Days': Config.format_leave_days(item['leave_days']),
                    'Working Days': item['working_days']
                })
            
            df = pd.DataFrame(alert_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Alert List",
                data=csv,
                file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error generating preview: {str(e)}")
        logger.error(f"Preview error: {e}", exc_info=True)

def generate_work_week_report():
    """Generate and display work week statistics"""
    workflow = st.session_state.workflow_manager
    
    try:
        with st.spinner("Generating work week report..."):
            stats = workflow.get_work_week_statistics()
            
            if not stats:
                st.error("Failed to generate statistics")
                return
            
            # Display period info
            if 'period' in stats:
                st.info(f"📅 Report Period: {stats['period']['start']} to {stats['period']['end']} ({stats['period']['type']})")
            
            # Summary metrics
            if 'totals' in stats:
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Total Employees", stats['totals']['employees'])
                
                with col2:
                    meeting = stats['totals']['meeting_requirements']
                    total = stats['totals']['employees']
                    pct = (meeting/total*100) if total > 0 else 0
                    st.metric("Meeting Requirements", meeting, delta=f"{pct:.1f}%")
                
                with col3:
                    st.metric("Alerts Needed", stats['totals']['alerts_needed'])
                
                with col4:
                    st.metric("On Full Leave", stats['totals']['on_full_leave'])
                
                with col5:
                    st.metric("Excluded", stats['totals']['excluded_employees'])
            
            # Hour distribution
            if 'hour_distribution' in stats:
                st.subheader("📊 Hour Distribution")
                hour_dist_data = []
                for range_key, count in stats['hour_distribution'].items():
                    if count > 0:
                        hour_dist_data.append({'Range': range_key, 'Count': count})
                
                if hour_dist_data:
                    df_hours = pd.DataFrame(hour_dist_data)
                    fig = px.pie(df_hours, values='Count', names='Range', title='Employee Hour Distribution')
                    st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")
        logger.error(f"Report generation error: {e}", exc_info=True)

def test_system_components():
    """Test all system components including AI intelligence"""
    st.subheader("🧪 System Component Testing")
    
    # TeamLogger Test
    with st.expander("TeamLogger API Test", expanded=True):
        try:
            teamlogger = TeamLoggerClient()
            status = teamlogger.get_api_status()
            if status['connected']:
                st.success(f"✅ Connected - {status['employee_count']} employees found")
                st.json(status)
            else:
                st.error("❌ Connection failed")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Google Sheets Test
    with st.expander("Google Sheets Test", expanded=True):
        try:
            sheets = GoogleSheetsLeaveClient()
            validation = sheets.validate_google_sheets_connection()
            if validation['status'] == 'success':
                st.success(f"✅ Connected - {validation.get('rows_found', 0)} rows found")
                st.json(validation)
            else:
                st.error(f"❌ {validation['message']}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # Email Service Test
    with st.expander("Email Service Test", expanded=True):
        try:
            email = EmailService()
            if email.test_email_configuration():
                st.success("✅ Email service configured correctly")
                st.info(f"From: {Config.FROM_EMAIL}")
                st.info(f"CC Recipients: {', '.join(email.cc_emails)}")
            else:
                st.error("❌ Email configuration issues")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    # AI Intelligence Test - Enhanced
    with st.expander("🤖 AI Intelligence Test", expanded=True):
        try:
            st.write("**Configuration Check:**")
            st.write(f"- OPENAI_API_KEY present: {'✅' if Config.OPENAI_API_KEY else '❌'}")
            st.write(f"- ENABLE_OPENAI_ENHANCEMENT: {'✅' if Config.ENABLE_OPENAI_ENHANCEMENT else '❌'}")
            
            workflow = st.session_state.workflow_manager
            st.write("\n**WorkflowManager Check:**")
            st.write(f"- Has openai_client attribute: {'✅' if hasattr(workflow, 'openai_client') else '❌'}")
            st.write(f"- openai_client is configured: {'✅' if (hasattr(workflow, 'openai_client') and workflow.openai_client is not None) else '❌'}")
            
            if hasattr(workflow, 'openai_client') and workflow.openai_client:
                st.success("✅ AI Intelligence is properly configured and ready")
                
                # Test AI functionality
                if st.button("Test AI Message Generation"):
                    try:
                        test_message = workflow._generate_ai_enhanced_message(
                            "Test Employee",
                            35.0,
                            40.0,
                            0,
                            5.0
                        )
                        st.success("✅ AI message generation successful!")
                        st.text_area("Generated Message:", test_message, height=200)
                    except Exception as e:
                        st.error(f"❌ AI test failed: {str(e)}")
            else:
                st.warning("⚠️ AI Intelligence not configured")
                st.info("Ensure OPENAI_API_KEY and ENABLE_OPENAI_ENHANCEMENT are set in your configuration")
        except Exception as e:
            st.error(f"❌ Error testing AI: {str(e)}")
            logger.error(f"AI test error: {e}", exc_info=True)

def display_work_week_summary():
    """Display current work week summary with corrected hours"""
    st.subheader("📈 Current Work Week Overview")
    
    try:
        workflow = st.session_state.workflow_manager
        start, end = workflow.get_week_boundaries()
        
        st.info(f"Monitoring Period: {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')} (Previous Week)")
        
        # Display corrected metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Required Hours/Week", "40h", icon="⏰")
        
        with col2:
            create_metric_card("Acceptable Hours", "37h+", delta="3h buffer", icon="✅")
        
        with col3:
            create_metric_card("Working Days", "5 days", delta="Mon-Fri", icon="📅")
        
        with col4:
            create_metric_card("Hours per Day", "8h", icon="💼")
    except Exception as e:
        st.error(f"Error displaying work week summary: {str(e)}")

def display_configuration_summary():
    """Display configuration summary with AI status"""
    st.subheader("⚙️ Configuration Summary")
    
    try:
        config_summary = Config.get_config_summary()
        ai_status = Config.get_ai_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Work Schedule**")
            if 'work_schedule' in config_summary:
                ws = config_summary['work_schedule']
                st.write(f"- Work Days: {ws['work_days_per_week']} (Monday-Friday)")
                st.write(f"- Required: {ws['minimum_hours_per_week']}h/week")
                st.write(f"- Per Day: {ws['hours_per_working_day']}h/day")
                st.write(f"- Acceptable: {ws['acceptable_hours_per_week']}h+ (with {ws['hours_buffer']}h buffer)")
            
            st.markdown("**Execution Schedule**")
            if 'execution_schedule' in config_summary:
                es = config_summary['execution_schedule']
                st.write(f"- Day: {es['day']}")
                st.write(f"- Time: {es['time']} {es['timezone']}")
        
        with col2:
            st.markdown("**Features**")
            if 'features' in config_summary:
                features = config_summary['features']
                st.write(f"- Email Alerts: {'✅' if features['email_alerts'] else '❌'}")
                st.write(f"- 🤖 AI Intelligence: {'✅' if features.get('openai_enhancement', False) else '❌'}")
                st.write(f"- Slack Notifications: {'✅' if features.get('slack_notifications', False) else '❌'}")
            
            st.markdown("**🤖 AI Capabilities**")
            if ai_status['enabled']:
                st.write("- ✅ Smart Decision Making")
                st.write("- ✅ Intelligent Overrides")
                st.write("- ✅ Personalized Messages")
                st.write("- ✅ Context Analysis")
            else:
                st.write("- ❌ AI Disabled")
                if not ai_status['api_key_configured']:
                    st.write("  (Missing OPENAI_API_KEY)")
                elif not Config.ENABLE_OPENAI_ENHANCEMENT:
                    st.write("  (ENABLE_OPENAI_ENHANCEMENT not true)")
            
            st.markdown("**Excluded Employees**")
            if 'excluded_employees' in config_summary:
                for emp in config_summary['excluded_employees']:
                    st.write(f"- {emp}")
    except Exception as e:
        st.error(f"Error displaying configuration: {str(e)}")
        logger.error(f"Configuration display error: {e}", exc_info=True)

# Sidebar navigation
with st.sidebar:
    st.markdown("🤖 **AI-Enhanced Employee Hours Monitor**")
    st.title("Navigation")
    
    st.markdown("---")
    
    # System health indicator with AI
    if 'system_status' in st.session_state:
        status = st.session_state.system_status
        all_connected = (status.get('teamlogger', False) and 
                        status.get('google_sheets', False) and 
                        status.get('email', False))
        ai_enabled = status.get('ai_intelligence', False)
        
        if all_connected and ai_enabled:
            st.success("🟢 All Systems + AI Operational")
        elif all_connected:
            st.warning("🟡 Core Systems OK, AI Inactive")
        else:
            st.error("🔴 System Issues Detected")
    
    st.markdown("---")
    
    # AI Status
    workflow = st.session_state.workflow_manager
    if hasattr(workflow, 'openai_client') and workflow.openai_client:
        st.success("🤖 **AI Intelligence Active**")
        st.write("- Smart decision making")
        st.write("- Confidence scoring")
        st.write("- Intelligent overrides")
        st.write("- Personalized messages")
    else:
        st.warning("🤖 **AI Intelligence Inactive**")
        if not Config.OPENAI_API_KEY:
            st.write("- Missing OPENAI_API_KEY")
        elif not Config.ENABLE_OPENAI_ENHANCEMENT:
            st.write("- ENABLE_OPENAI_ENHANCEMENT not true")
        else:
            st.write("- WorkflowManager init issue")
    
    st.markdown("---")
    
    # Links to documentation
    st.markdown("### 📚 Resources")
    st.markdown("[📖 User Guide](https://github.com/your-repo/wiki)")
    st.markdown("[🤖 AI Features Guide](https://github.com/your-repo/wiki/ai)")
    st.markdown("[🐛 Report Issue](https://github.com/your-repo/issues)")
    st.markdown("[📧 Contact Support](mailto:support@example.com)")

# Main content
try:
    display_dashboard()
except Exception as e:
    st.error(f"Error loading dashboard: {str(e)}")
    logger.error(f"Dashboard error: {e}", exc_info=True)

# Auto-refresh functionality
if st.checkbox("Enable auto-refresh (30 seconds)", value=False):
    time.sleep(30)
    st.rerun()