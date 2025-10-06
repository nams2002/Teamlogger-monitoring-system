"""
Monitoring Page - OPTIMIZED for speed and accuracy
Fixed: Excluded employees, real-time data, removed negligible shortfall
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

from src.workflow_manager import WorkflowManager
from src.manager_mapping import get_manager_name, get_manager_email
from config.settings import Config

st.set_page_config(
    page_title="Monitoring - Employee Hours",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'workflow_manager' not in st.session_state:
    st.session_state.workflow_manager = WorkflowManager()
if 'monitoring_results' not in st.session_state:
    st.session_state.monitoring_results = None

def run_monitoring_workflow(force=False):
    """Run the monitoring workflow - OPTIMIZED"""
    try:
        workflow = st.session_state.workflow_manager

        if not force and not workflow.should_send_alerts_today():
            today = datetime.now().strftime('%A')
            st.warning(f"⚠️ Today is {today}. Alerts are only sent on Monday/Tuesday.")
            if st.button("Force Run Anyway", type="secondary"):
                run_monitoring_workflow(force=True)
            return None

        # Create progress placeholder
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🔄 Starting monitoring workflow...")
            progress_bar.progress(20)
            
            status_text.text("📊 Processing employees...")
            progress_bar.progress(50)
            
            # Run the actual workflow
            results = workflow.run_workflow()
            
            progress_bar.progress(80)
            status_text.text("📧 Sending alerts...")
            
            progress_bar.progress(100)
            status_text.text("✅ Workflow completed!")
            time.sleep(1)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            return results
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error running workflow: {str(e)}")
            return None

    except Exception as e:
        st.error(f"❌ Error in monitoring: {e}")
        raise

def display_monitoring_results(results):
    """Display monitoring workflow results"""
    if not results:
        return
    
    st.success("✅ Monitoring workflow completed successfully!")
    
    # Display summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Employees", results['total_employees'])
    
    with col2:
        st.metric("Alerts Sent", results['alerts_sent'], 
                 delta=f"{(results['alerts_sent']/results['total_employees']*100):.1f}%" if results['total_employees'] > 0 else "0%")
    
    with col3:
        st.metric("Excluded", results.get('excluded', 0),
                 help="Aishik, Tirtharaj, Vishal")
    
    with col4:
        st.metric("On Full Leave", results['on_leave'])
    
    with col5:
        st.metric("Meeting Requirements", results['hours_met'])
    
    # Additional details
    if results.get('execution_time'):
        st.info(f"⏱️ Execution time: {results['execution_time']}")
    
    if results.get('errors', 0) > 0:
        st.warning(f"⚠️ {results['errors']} errors occurred during processing")

def preview_hours_alerts():
    """Preview hours-based alerts only"""
    workflow = st.session_state.workflow_manager

    st.subheader("⏰ Hours-Based Alerts Preview")

    with st.spinner("🔍 Analyzing employee hours with real-time data..."):
        employees_needing_alerts = workflow.get_employees_needing_real_alerts()

    if not employees_needing_alerts:
        st.success("✅ No employees need hours alerts for the previous work week!")

        work_week_start, work_week_end = workflow._get_monitoring_period()
        st.info(f"All employees met their hour requirements for {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')}")

    else:
        st.warning(f"⚠️ {len(employees_needing_alerts)} employees would receive hours alerts")

        # Create tabs
        tab1, tab2, tab3 = st.tabs(["📋 Employee List", "📊 Visualizations", "📧 Email Preview"])
        
        with tab1:
            # Display employee data
            alert_data = []
            for item in employees_needing_alerts:
                employee = item['employee']
                weekly_data = item['weekly_data']
                
                # Get manager information
                manager_name = get_manager_name(employee['name'])
                manager_email = get_manager_email(employee['name'])
                
                alert_data.append({
                    'Name': employee['name'],
                    'Email': employee['email'],
                    'Manager': manager_name if manager_name else 'Not Assigned',
                    'Manager Email': manager_email if manager_email else 'Not Available',
                    'Hours Worked': f"{weekly_data['total_hours']:.2f}",
                    'Required Hours': f"{item['required_hours']:.1f}",
                    'Acceptable Hours': f"{item['acceptable_hours']:.1f}",
                    'Shortfall (hours)': f"{item['shortfall']:.2f}",
                    'Leave Days': Config.format_leave_days(item['leave_days']),
                    'Working Days': item['working_days'],
                    'Status': '🚨 Alert Required'
                })
            
            df = pd.DataFrame(alert_data)
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                manager_filter = st.multiselect("Filter by Manager",
                                               options=[m for m in df['Manager'].unique() if m != 'Not Assigned'],
                                               default=[],
                                               key="hours_manager_filter")
            
            with col2:
                min_shortfall = st.slider("Min shortfall (hours)",
                                        min_value=0.0,
                                        max_value=20.0,
                                        value=0.0,
                                        step=0.5,
                                        key="hours_shortfall_slider")
            
            with col3:
                search_term = st.text_input("Search employee", "", key="hours_search")
            
            # Apply filters
            filtered_df = df.copy()
            if manager_filter:
                filtered_df = filtered_df[filtered_df['Manager'].isin(manager_filter)]
            if min_shortfall > 0:
                filtered_df = filtered_df[filtered_df['Shortfall (hours)'].astype(float) >= min_shortfall]
            if search_term:
                filtered_df = filtered_df[filtered_df['Name'].str.contains(search_term, case=False, na=False)]
            
            # Display filtered data
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download button
            if len(filtered_df) > 0:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Alert List (CSV)",
                    data=csv,
                    file_name=f"employee_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="hours_download_button"
                )
        
        with tab2:
            # Visualizations
            if len(df) > 0:
                # Shortfall distribution
                fig1 = px.histogram(
                    df, 
                    x='Shortfall (hours)',
                    nbins=20,
                    title='Shortfall Distribution'
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # Manager breakdown
                manager_counts = df['Manager'].value_counts()
                fig2 = px.bar(
                    x=manager_counts.index,
                    y=manager_counts.values,
                    labels={'x': 'Manager', 'y': 'Alert Count'},
                    title='Alerts by Manager'
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        with tab3:
            # Email preview
            st.info("📧 Email that would be sent:")
            
            if len(alert_data) > 0:
                sample = alert_data[0]
                
                email_preview = f"""
                **To:** {sample['Email']}
                **CC:** {sample['Manager Email']}, teamhr@rapidinnovation.dev
                **Subject:** Work Hours Reminder
                
                Dear {sample['Name']},
                
                This is a notification regarding your work hours for the week.
                
                **Week Period:** {workflow._get_monitoring_period()[0].strftime('%Y-%m-%d')} to {workflow._get_monitoring_period()[1].strftime('%Y-%m-%d')}
                
                **Your Statistics:**
                - Hours Worked: {sample['Hours Worked']}h
                - Required Hours: {sample['Required Hours']}h
                - Acceptable Hours: {sample['Acceptable Hours']}h (with 3-hour buffer)
                - Shortfall: {sample['Shortfall (hours)']}h
                - Leave Days: {sample['Leave Days']}
                - Working Days Available: {sample['Working Days']}
                
                **Manager:** {sample['Manager']}
                
                Please ensure you meet the minimum hour requirements in the coming weeks.
                
                Best regards,
                HR Team
                """
                
                st.markdown(email_preview)

# Main page content
st.title("⏰ Employee Hours Monitoring")
st.markdown("Monitor employee work hours and send alerts for insufficient hours - Optimized for accuracy")

# Show preview mode notice if email alerts are disabled
if not Config.ENABLE_EMAIL_ALERTS:
    st.info("🔍 **Preview Mode Active** - No emails will be sent. The system will show who would receive alerts.")

# System info
col1, col2, col3 = st.columns(3)
with col1:
    st.info("**System:** 5-Day Work Week (40h required, 37h+ acceptable)")
with col2:
    st.info("**Buffer:** 3 hours only (no 10-min check)")
with col3:
    st.warning("**Excluded:** Aishik, Tirtharaj, Vishal")

# Display current week info
workflow = st.session_state.workflow_manager
work_week_start, work_week_end = workflow._get_monitoring_period()
st.info(f"📅 Monitoring Period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')} (Previous Week)")

# Action buttons
st.subheader("🎯 Hours Monitoring Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔍 Preview Hours Alerts", use_container_width=True, type="primary",
                help="SAFE: Shows who would receive alerts - NEVER sends emails"):
        preview_hours_alerts()

with col2:
    # Show different button text based on email settings
    if Config.ENABLE_EMAIL_ALERTS:
        button_text = "📧 Run Hours Monitoring"
        button_help = "LIVE MODE: Will actually send emails to employees and managers"
        button_type = "secondary"
    else:
        button_text = "🔍 Run Hours Monitoring"
        button_help = "PREVIEW MODE: Will show results but NOT send emails"
        button_type = "primary"

    if st.button(button_text, use_container_width=True, type=button_type, help=button_help):
        if st.session_state.get('confirm_run', False):
            results = run_monitoring_workflow()
            if results:
                st.session_state.monitoring_results = results
                display_monitoring_results(results)
            st.session_state.confirm_run = False
        else:
            if Config.ENABLE_EMAIL_ALERTS:
                st.warning("⚠️ **LIVE MODE**: This will send actual emails to employees and managers. Click again to confirm.")
            else:
                st.info("🔍 **PREVIEW MODE**: This will show results but NOT send emails. Click again to confirm.")
            st.session_state.confirm_run = True

with col3:
    if st.button("💪 Force Run", use_container_width=True,
                help="Force run regardless of the day"):
        results = run_monitoring_workflow(force=True)
        if results:
            st.session_state.monitoring_results = results
            display_monitoring_results(results)

# Display previous results
if st.session_state.monitoring_results and not st.session_state.get('confirm_run', False):
    st.markdown("---")
    st.subheader("📊 Last Run Results")
    display_monitoring_results(st.session_state.monitoring_results)

# Settings section
with st.expander("⚙️ Monitoring Settings"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Work System**")
        st.write(f"- Required: {Config.MINIMUM_HOURS_PER_WEEK}h/week")
        st.write(f"- Acceptable: {Config.ACCEPTABLE_HOURS_PER_WEEK}h+ (3h buffer)")
        st.write(f"- Working Days: {Config.WORK_DAYS_PER_WEEK} (Mon-Fri)")
        st.write(f"- Hours/Day: {Config.HOURS_PER_WORKING_DAY}h")
        st.write(f"- Half Day: {Config.HOURS_PER_HALF_DAY}h")
        st.write("- **Formula:** Required = 8 × (5 - leave_days)")
    
    with col2:
        st.markdown("**Configuration**")
        st.write(f"- Alert Days: Monday/Tuesday")
        st.write(f"- Execution Time: {Config.EXECUTION_HOUR:02d}:{Config.EXECUTION_MINUTE:02d}")
        st.write(f"- Email Alerts: {'✅' if Config.ENABLE_EMAIL_ALERTS else '❌'}")
        st.write(f"- Real-time Data: ✅ Always")
        
        st.markdown("**Excluded Employees**")
        for emp in Config.EXCLUDED_EMPLOYEES:
            st.write(f"- {emp}")

# Help section
with st.expander("❓ Help"):
    st.markdown("""
    ### Monitoring System - Optimized
    
    **Key Changes:**
    - ✅ Excluded employees (Aishik, Tirtharaj, Vishal) never get alerts
    - ✅ Real-time Google Sheets data (no caching)
    - ✅ Only 3-hour buffer matters (removed 10-min check)
    - ✅ Faster processing with batch operations
    - ✅ Half-day leave support (0.5 days = 4 hours)
    
    **Alert Logic:**
    - Required: 40 hours/week
    - Acceptable: 37+ hours (3-hour buffer)
    - Formula: Required = 8 × (5 - leave_days)
    - Half days count as 0.5 (4 hours reduction)
    
    **When Alerts are Sent:**
    - Employee worked < 37 hours (after leave adjustment)
    - Employee is NOT in excluded list
    - Employee NOT on full leave (5+ days)
    """)