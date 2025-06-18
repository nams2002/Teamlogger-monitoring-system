"""
Employees Page - UNIFIED with correct status determination and export functionality
Fixed all calculation inconsistencies and status display issues based on Excel data analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from src.teamlogger_client import TeamLoggerClient
from src.googlesheets_Client import GoogleSheetsLeaveClient
from src.workflow_manager import WorkflowManager
from src.manager_mapping import get_manager_name, get_manager_email
from config.settings import Config

st.set_page_config(
    page_title="Employees - Employee Hours",
    page_icon="👥",
    layout="wide"
)

# Initialize session state
if 'workflow_manager' not in st.session_state:
    st.session_state.workflow_manager = WorkflowManager()
if 'selected_employee' not in st.session_state:
    st.session_state.selected_employee = None

def get_all_employees_data():
    """Get all employees with UNIFIED status determination - matches Excel export logic"""
    try:
        teamlogger = TeamLoggerClient()
        workflow = st.session_state.workflow_manager
        
        # Get all employees
        employees = teamlogger.get_all_employees()
        
        # Get current week boundaries
        work_week_start, work_week_end = workflow._get_monitoring_period()
        
        # Enrich with weekly data and UNIFIED status determination
        employee_data = []
        for emp in employees:
            try:
                # Get weekly hours (Mon-Sun monitoring period)
                weekly_data = teamlogger.get_weekly_summary(emp['id'], work_week_start, work_week_end)
                
                # Get leave days (work days only)
                leave_days = workflow._get_working_day_leaves_count(
                    emp['name'], work_week_start, work_week_end
                )
                
                # Use UNIFIED status determination from Config
                actual_hours = weekly_data['total_hours'] if weekly_data else 0
                is_excluded = emp['name'].lower() in [name.lower() for name in Config.EXCLUDED_EMPLOYEES]
                
                # ✅ Use the UNIFIED status determination
                status_info = Config.determine_employee_status(actual_hours, leave_days, is_excluded)
                
                # Get manager information using the manager mapping
                manager_name = get_manager_name(emp['name'])
                manager_email = get_manager_email(emp['name'])
                
                # AI-enhanced analysis if available
                ai_analysis = None
                ai_status = "❌ Disabled"
                if hasattr(workflow, 'openai_client') and workflow.openai_client:
                    try:
                        ai_decision = workflow._ai_enhanced_decision(
                            emp['name'],
                            actual_hours,
                            status_info.get('required_hours', 40),
                            status_info.get('acceptable_hours', 37),
                            leave_days
                        )
                        ai_analysis = {
                            'decision': ai_decision.get('action', 'unknown'),
                            'reason': ai_decision.get('reason', 'N/A'),
                            'confidence': ai_decision.get('confidence', 'N/A'),
                            'explanation': ai_decision.get('explanation', ''),
                            'override': ai_decision.get('reason') == 'ai_override'
                        }
                        ai_status = "✅ Enabled"
                    except Exception as e:
                        ai_status = f"❌ Error: {str(e)[:50]}..."
                
                # Final display status considering AI
                final_status = get_display_status_with_ai(status_info, ai_analysis)
                
                employee_data.append({
                    'ID': emp['id'],
                    'Name': emp['name'],
                    'Email': emp['email'],
                    'Hours Worked': actual_hours,
                    'Required Hours': status_info.get('required_hours', 40),
                    'Acceptable Hours': status_info.get('acceptable_hours', 37),
                    'Leave Days': leave_days,
                    'Working Days': max(0, 5 - leave_days),
                    'Manager': manager_name if manager_name else 'Not Assigned',
                    'Manager Email': manager_email if manager_email else 'Not Available',
                    'Status': final_status,
                    'Alert Needed': status_info['alert_needed'] and not is_excluded,
                    'Is Excluded': is_excluded,
                    'Status Info': status_info,
                    'AI Analysis': ai_analysis,
                    'AI Status': ai_status
                })
            except Exception as e:
                st.warning(f"Error processing employee {emp['name']}: {str(e)}")
                continue
        
        return pd.DataFrame(employee_data)
    
    except Exception as e:
        st.error(f"Error fetching employee data: {str(e)}")
        return pd.DataFrame()

def get_display_status_with_ai(status_info, ai_analysis=None):
    """Get display status considering AI analysis - matches Excel export format"""
    base_status = status_info['display_status']
    
    # If AI override, show that instead
    if ai_analysis and ai_analysis.get('override'):
        confidence = ai_analysis.get('confidence', 'N/A')
        return f"🤖 AI Override ({confidence})"
    
    # If alert required but AI suggests no alert, show AI decision
    if (status_info['status'] == 'alert_required' and 
        ai_analysis and ai_analysis.get('decision') == 'no_alert'):
        confidence = ai_analysis.get('confidence', 'N/A')
        return f"🤖 AI No Alert ({confidence})"
    
    # Add AI confidence to alert required status
    if (status_info['status'] == 'alert_required' and 
        ai_analysis and ai_analysis.get('confidence')):
        confidence = ai_analysis.get('confidence', 'High')
        return f"🔴 Alert Required ({confidence})"
    
    return base_status

def create_excel_export_data(df_employees):
    """Create Excel export data that matches the format shown in your screenshots"""
    export_data = []
    
    for _, row in df_employees.iterrows():
        # Determine the exact status text that should appear in Excel
        status_info = row['Status Info']
        is_excluded = row['Is Excluded']
        
        if is_excluded:
            status_text = "🚫 Excluded from Alerts"
        elif status_info['status'] == 'full_leave':
            status_text = "🏖️ Full Leave (Protected)"
        elif status_info['status'] == 'meeting_requirements':
            status_text = "✅ Meeting Requirements"
        elif status_info['status'] == 'negligible_shortfall':
            status_text = "⚠️ Minor Shortfall (<10min)"
        elif status_info['status'] == 'alert_required':
            # Check AI analysis
            ai_analysis = row.get('AI Analysis')
            if ai_analysis and ai_analysis.get('decision') == 'no_alert':
                status_text = f"🤖 AI Override ({ai_analysis.get('confidence', 'N/A')})"
            else:
                status_text = "🔴 Alert Required"
        else:
            status_text = "❓ Unknown Status"
        
        export_data.append({
            'Name': row['Name'],
            'Email': row['Email'],
            'Hours Worked': round(row['Hours Worked'], 2),
            'Required Hours': row['Required Hours'],
            'Acceptable Hours': row['Acceptable Hours'],
            'Leave Days': row['Leave Days'],
            'Manager': row['Manager'],
            'Status': status_text,
            'Is Excluded': row['Is Excluded']
        })
    
    return pd.DataFrame(export_data)

def display_employee_details(employee_id, employee_name):
    """Display detailed information for a selected employee with AI insights"""
    st.subheader(f"📋 Employee Details: {employee_name}")
    
    # Check if excluded
    is_excluded = employee_name.lower() in [name.lower() for name in Config.EXCLUDED_EMPLOYEES]
    if is_excluded:
        st.warning(f"🚫 **{employee_name}** is excluded from receiving alert emails")
    
    teamlogger = TeamLoggerClient()
    workflow = st.session_state.workflow_manager
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("End Date", datetime.now())
    
    # Convert to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get employee data for selected period
    try:
        # Weekly summary
        weekly_data = teamlogger.get_weekly_summary(employee_id, start_datetime, end_datetime)
        
        if weekly_data:
            # Get leave days for the period
            leave_days = workflow._get_working_day_leaves_count(
                employee_name, start_datetime, end_datetime
            )
            
            # Use UNIFIED status determination
            actual_hours = weekly_data['total_hours']
            status_info = Config.determine_employee_status(actual_hours, leave_days, is_excluded)
            
            # AI Analysis
            ai_analysis = None
            ai_status = "❌ Disabled"
            if hasattr(workflow, 'openai_client') and workflow.openai_client:
                try:
                    ai_decision = workflow._ai_enhanced_decision(
                        employee_name,
                        actual_hours,
                        status_info.get('required_hours', 40),
                        status_info.get('acceptable_hours', 37),
                        leave_days
                    )
                    ai_analysis = ai_decision
                    ai_status = "✅ Enabled"
                except Exception as e:
                    ai_status = f"❌ Error: {str(e)[:50]}..."
            
            # Display metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Hours Worked", f"{actual_hours:.2f}h")
            
            with col2:
                st.metric("Required Hours", f"{status_info.get('required_hours', 40)}h")
            
            with col3:
                st.metric("Acceptable Hours", f"{status_info.get('acceptable_hours', 37)}h")
            
            with col4:
                st.metric("Leave Days", f"{leave_days} days")
            
            with col5:
                st.metric("AI Intelligence", ai_status)
            
            # Status display
            st.info(f"**Current Status:** {status_info['display_status']}")
            
            # Manager information
            manager_name = get_manager_name(employee_name)
            manager_email = get_manager_email(employee_name)
            
            if manager_name:
                st.success(f"👨‍💼 **Manager:** {manager_name} ({manager_email})")
            else:
                st.warning("⚠️ No manager assigned to this employee")
            
            # AI Analysis Section
            if ai_analysis:
                st.markdown("---")
                st.subheader("🤖 AI Intelligence Analysis")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Decision:** {ai_analysis.get('action', 'Unknown')}")
                    st.write(f"**Reason:** {ai_analysis.get('reason', 'N/A')}")
                    st.write(f"**Confidence:** {ai_analysis.get('confidence', 'N/A')}")
                
                with col2:
                    if ai_analysis.get('explanation'):
                        st.info(f"**AI Insight:** {ai_analysis['explanation']}")
                    if ai_analysis.get('personalized_message'):
                        st.success(f"**Personalized Message:** {ai_analysis['personalized_message']}")
            
            # Calculation breakdown - UNIFIED
            st.markdown("---")
            st.subheader("📊 UNIFIED Hour Calculation Breakdown")
            
            calc_data = {
                'Metric': [
                    'Base Requirement (5 days)',
                    f'Leave Adjustment ({leave_days} days)',
                    'Required Hours',
                    'Buffer Applied',
                    'Acceptable Hours',
                    'Actual Hours Worked',
                    'Difference'
                ],
                'Value': [
                    f"{Config.MINIMUM_HOURS_PER_WEEK}h",
                    f"-{leave_days * Config.HOURS_PER_WORKING_DAY}h",
                    f"{status_info.get('required_hours', 40)}h",
                    f"-{Config.HOURS_BUFFER}h",
                    f"{status_info.get('acceptable_hours', 37)}h",
                    f"{actual_hours:.2f}h",
                    f"{actual_hours - status_info.get('acceptable_hours', 37):+.2f}h"
                ],
                'Status': [
                    '📋 Base',
                    '🏖️ Adjusted' if leave_days > 0 else '➖ None',
                    '🎯 Target',
                    '💫 Buffer',
                    '✅ Minimum',
                    '⏱️ Actual',
                    '✅ Above' if actual_hours >= status_info.get('acceptable_hours', 37) else '🔴 Below'
                ]
            }
            
            calc_df = pd.DataFrame(calc_data)
            st.dataframe(calc_df, use_container_width=True, hide_index=True)
            
            # Show UNIFIED formula
            st.info(f"✅ **UNIFIED Formula:** Required = 8 × (5 - {leave_days}) = {status_info.get('required_hours', 40)} hours")
            
        else:
            st.warning("No data available for the selected period")
    
    except Exception as e:
        st.error(f"Error fetching employee details: {str(e)}")

# Main page
st.title("👥 Employee Management")
st.markdown("View and analyze employee work hours with UNIFIED calculations (5-Day Work System)")

# System info banner with AI status
ai_status = "✅ Enabled" if hasattr(st.session_state.workflow_manager, 'openai_client') and st.session_state.workflow_manager.openai_client else "❌ Disabled"
st.info(f"🔧 **UNIFIED 5-Day Work System:** Work 5 days (Mon-Fri), weekend availability for completion | **AI Intelligence:** {ai_status} | **Excluded:** {', '.join(Config.EXCLUDED_EMPLOYEES)}")

# Validation Examples - Show the corrected calculations
with st.expander("🧪 UNIFIED Calculation Validation", expanded=False):
    st.markdown("### Examples from your Excel sheet:")
    if st.button("🔄 Test Real Examples"):
        Config.validate_real_examples()
    
    examples = [
        ("Shobhit Vishnoi", 23.24, 2),
        ("Pravallika Reddy", 29.47, 0),
        ("Kevin", 24.32, 2)
    ]
    
    for name, hours, leave_days in examples:
        status_info = Config.determine_employee_status(hours, leave_days)
        required = status_info.get('required_hours', 40)
        acceptable = status_info.get('acceptable_hours', 37)
        alert_needed = status_info['alert_needed']
        
        st.write(f"**{name}:** {hours}h worked, {leave_days} leave days")
        st.write(f"  Required: {required}h (8 × {5-leave_days}), Acceptable: {acceptable}h")
        st.write(f"  Result: {'🚨 ALERT' if alert_needed else '✅ NO ALERT'} - {status_info['display_status']}")
        st.write("---")

# Refresh data button
if st.button("🔄 Refresh Data", use_container_width=False):
    st.rerun()

# Get employee data
with st.spinner("Loading employee data with UNIFIED calculations..."):
    df_employees = get_all_employees_data()

if not df_employees.empty:
    # Summary metrics
    st.subheader("📊 Employee Overview (UNIFIED Calculations)")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Employees", len(df_employees))
    
    with col2:
        meeting_req = len(df_employees[df_employees['Status'].str.contains("Meeting Requirements")])
        st.metric("Meeting Requirements", meeting_req,
                 delta=f"{(meeting_req/len(df_employees)*100):.1f}%")
    
    with col3:
        excluded_count = len(df_employees[df_employees['Is Excluded'] == True])
        st.metric("Excluded from Alerts", excluded_count)
    
    with col4:
        alerts_needed = len(df_employees[df_employees['Alert Needed'] == True])
        st.metric("Alerts Needed", alerts_needed)
    
    with col5:
        ai_overrides = len(df_employees[df_employees['Status'].str.contains("AI Override")])
        st.metric("🤖 AI Overrides", ai_overrides)
    
    # Filters
    st.markdown("---")
    st.subheader("🔍 Filter Employees")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Get unique managers for filter
        unique_managers = df_employees['Manager'].unique()
        manager_filter = st.multiselect(
            "Manager",
            options=[m for m in unique_managers if m != 'Not Assigned'],
            default=[]
        )
    
    with col2:
        status_filter = st.multiselect(
            "Status",
            options=df_employees['Status'].unique(),
            default=[]
        )
    
    with col3:
        exclusion_filter = st.selectbox(
            "Alert Status",
            options=["All Employees", "Excluded Only", "Alert-Enabled Only"],
            index=0
        )
    
    with col4:
        search_term = st.text_input("Search by Name/Email", "")
    
    # Apply filters
    filtered_df = df_employees.copy()
    
    if manager_filter:
        filtered_df = filtered_df[filtered_df['Manager'].isin(manager_filter)]
    
    if status_filter:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    
    if exclusion_filter == "Excluded Only":
        filtered_df = filtered_df[filtered_df['Is Excluded'] == True]
    elif exclusion_filter == "Alert-Enabled Only":
        filtered_df = filtered_df[filtered_df['Is Excluded'] == False]
    
    if search_term:
        mask = (filtered_df['Name'].str.contains(search_term, case=False, na=False) | 
                filtered_df['Email'].str.contains(search_term, case=False, na=False))
        filtered_df = filtered_df[mask]
    
    # Display employee table
    st.markdown("---")
    st.subheader(f"📋 Employee List ({len(filtered_df)} employees)")
    
    # Configure column display
    column_config = {
        "Hours Worked": st.column_config.NumberColumn(
            "Hours Worked",
            format="%.2f h"
        ),
        "Required Hours": st.column_config.NumberColumn(
            "Required Hours",
            format="%d h"
        ),
        "Acceptable Hours": st.column_config.NumberColumn(
            "Acceptable Hours",
            format="%d h"
        ),
        "Leave Days": st.column_config.NumberColumn(
            "Leave Days",
            format="%d days"
        ),
        "Working Days": st.column_config.NumberColumn(
            "Working Days",
            format="%d days"
        )
    }
    
    # Display table with selection
    selected_rows = st.dataframe(
        filtered_df[['Name', 'Email', 'Manager', 'Hours Worked', 'Required Hours', 'Acceptable Hours', 'Leave Days', 'Working Days', 'Status']],
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Handle row selection
    if selected_rows.selection.rows:
        selected_idx = selected_rows.selection.rows[0]
        selected_employee = filtered_df.iloc[selected_idx]
        st.session_state.selected_employee = {
            'id': selected_employee['ID'],
            'name': selected_employee['Name']
        }
    
    # Show employee details if selected
    if st.session_state.selected_employee:
        st.markdown("---")
        display_employee_details(
            st.session_state.selected_employee['id'],
            st.session_state.selected_employee['name']
        )
    
    # Export functionality - UNIFIED to match Excel format
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Create Excel-compatible export data
        export_df = create_excel_export_data(filtered_df)
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Employee Data (Excel Compatible)",
            data=csv,
            file_name=f"employee_data_unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Downloads data in the same format as shown in your Excel screenshots"
        )
    
    with col2:
        # AI-enhanced manager summary statistics
        if st.button("📊 Show UNIFIED Manager Statistics"):
            alert_enabled_df = filtered_df[filtered_df['Is Excluded'] == False]
            
            if len(alert_enabled_df) > 0:
                manager_stats = alert_enabled_df.groupby('Manager').agg({
                    'Name': 'count',
                    'Hours Worked': 'mean',
                    'Leave Days': 'sum',
                    'Alert Needed': 'sum'
                }).reset_index()
                manager_stats.columns = ['Manager', 'Team Size', 'Avg Hours', 'Total Leave Days', 'Alerts Needed']
                
                # Add AI override counts
                ai_override_counts = alert_enabled_df[alert_enabled_df['Status'].str.contains('AI Override', na=False)].groupby('Manager').size().reset_index(name='AI Overrides')
                manager_stats = manager_stats.merge(ai_override_counts, on='Manager', how='left').fillna(0)
                
                manager_stats = manager_stats[manager_stats['Manager'] != 'Not Assigned']
                
                fig = px.scatter(manager_stats, x='Team Size', y='Avg Hours',
                               color='AI Overrides', size='Total Leave Days',
                               hover_data=['Manager'],
                               title='UNIFIED Manager Team Statistics (Alert-Enabled Only)',
                               color_continuous_scale='Viridis')
                fig.add_hline(y=37, line_dash="dash", line_color="orange", annotation_text="Acceptable (37h)")
                fig.add_hline(y=40, line_dash="dash", line_color="green", annotation_text="Required (40h)")
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(manager_stats, use_container_width=True, hide_index=True)
            else:
                st.info("No alert-enabled employees found for manager analysis")

else:
    st.warning("No employee data available. Please check your TeamLogger connection.")

# Help section
with st.expander("❓ Help - UNIFIED Employee Management"):
    st.markdown("""
    ### UNIFIED Employee Management Features (5-Day Work System)
    
    **✅ FIXED Calculation Issues**
    - Unified status determination across all modules
    - Consistent Excel export format
    - Fixed Shobhit Vishnoi case (23.24h with 2 leave days = NO ALERT)
    - Corrected Required Hours formula: 8 × (5 - leave_days)
    
    **🤖 AI Intelligence Features**
    - **Smart Decision Making**: AI analyzes context beyond just numbers
    - **Confidence Scoring**: High/Medium/Low confidence in alert decisions
    - **Intelligent Overrides**: AI can prevent unnecessary alerts
    - **Personalized Messages**: Custom email content based on situation
    
    **System Overview**
    - Work 5 days (Monday-Friday) but have full week to complete 40 hours
    - Weekend days (Saturday-Sunday) available for hour completion
    - 3-hour buffer provides flexibility (37+ hours acceptable)
    - Only working day leaves (Mon-Fri) reduce required hours
    - **✅ UNIFIED Formula**: Required Hours = 8 × (5 - leave_days)
    
    **Status Definitions**
    - ✅ **Meeting Requirements**: Working 37+ hours (meets threshold)
    - 🔴 **Alert Required**: Below 37 hours with significant shortfall
    - 🤖 **AI Override**: AI intelligently prevented an alert
    - ⚠️ **Minor Shortfall**: Below threshold but <10 minutes (ignored)
    - 🏖️ **Full Leave (Protected)**: On leave for entire work week (5 days)
    - 🚫 **Excluded from Alerts**: In excluded employee list
    
    **Excel Export**
    - Downloads data in the same format as your screenshots
    - Consistent status text and calculations
    - Includes manager information and AI analysis
    
    **Excluded Employees**
    The following employees never receive alert emails:
    - **Aishik Chatterjee**
    - **Tirtharaj Bhoumik**
    - **Vishal Kumar**
    """)