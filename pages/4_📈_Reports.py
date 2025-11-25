"""
Reports Page - Analytics and reporting for employee hours
UPDATED: 5-Day Work System with weekend availability and excluded employees
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

from src.workflow_manager import WorkflowManager
from src.teamlogger_client import TeamLoggerClient
from config.settings import Config

st.set_page_config(
    page_title="Reports - Employee Hours",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'workflow_manager' not in st.session_state:
    st.session_state.workflow_manager = WorkflowManager()

def generate_mock_historical_data(weeks=12):
    """Generate mock historical data for demonstration - updated for 5-day system"""
    data = []
    teamlogger = TeamLoggerClient()
    employees = teamlogger.get_all_employees()[:20]  # Limit for demo
    excluded_employees = [name.lower() for name in Config.EXCLUDED_EMPLOYEES]
    
    for week in range(weeks):
        week_start = datetime.now() - timedelta(weeks=week)
        week_start = week_start - timedelta(days=week_start.weekday())  # Monday
        
        for emp in employees:
            # Generate realistic hour distribution for 5-day system
            base_hours = np.random.normal(38, 5)
            hours = max(0, min(50, base_hours))
            
            # Random leave days (0-5, weighted toward lower values)
            leave_days = np.random.choice([0, 0, 0, 0, 1, 2, 3, 5], p=[0.6, 0.15, 0.1, 0.05, 0.05, 0.03, 0.01, 0.01])
            
            # Adjust hours based on leave using Config logic
            required_hours = Config.calculate_required_hours_for_leave_days(leave_days)
            acceptable_hours = Config.calculate_acceptable_hours_for_leave_days(leave_days)
            
            # Determine status using Config logic
            should_alert, calculation = Config.should_send_alert(hours, leave_days)
            is_excluded = emp['name'].lower() in excluded_employees
            
            # Determine final alert status
            alert_sent = should_alert and not is_excluded
            
            data.append({
                'Week': week_start.strftime('%Y-%m-%d'),
                'Employee': emp['name'],
                'Department': emp.get('department', 'Engineering'),
                'Hours': round(hours, 1),
                'Required Hours': required_hours,
                'Acceptable Hours': acceptable_hours,
                'Leave Days': leave_days,
                'Met Requirements': calculation['status'] in ['hours_met', 'full_leave'],
                'Alert Sent': alert_sent,
                'Is Excluded': is_excluded,
                'Status': calculation['status']
            })
    
    return pd.DataFrame(data)

def create_overview_metrics(df):
    """Create overview metrics from dataframe for 5-day system"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_hours = df['Hours'].mean()
        st.metric("Average Hours/Week", f"{avg_hours:.1f}h")
    
    with col2:
        # Calculate compliance rate (excluding full leave and excluded employees)
        eligible_employees = df[~df['Is Excluded'] & (df['Status'] != 'full_leave')]
        if len(eligible_employees) > 0:
            compliance_rate = (eligible_employees['Met Requirements'].sum() / len(eligible_employees) * 100)
        else:
            compliance_rate = 100
        st.metric("Compliance Rate", f"{compliance_rate:.1f}%")
    
    with col3:
        # Only count actual alerts sent (excluding excluded employees)
        total_alerts = df['Alert Sent'].sum()
        st.metric("Total Alerts Sent", total_alerts)
    
    with col4:
        avg_leave = df['Leave Days'].mean()
        st.metric("Avg Leave Days/Week", f"{avg_leave:.1f}")

# Main page
st.title("📈 Reports & Analytics")
st.markdown("Analyze employee hours trends and generate insights (5-Day Work System)")

# System info banner
st.info(f"🔧 **5-Day Work System:** Work 5 days (Mon-Fri), weekend availability | **Excluded:** {', '.join(Config.EXCLUDED_EMPLOYEES)}")

# Date range selector
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(weeks=12))
with col2:
    end_date = st.date_input("End Date", datetime.now())
with col3:
    if st.button("🔄 Refresh Data", width="stretch"):
        st.rerun()

# Generate data
with st.spinner("Loading report data..."):
    df = generate_mock_historical_data(12)
    
    # Filter by date range
    df['Week'] = pd.to_datetime(df['Week'])
    mask = (df['Week'].dt.date >= start_date) & (df['Week'].dt.date <= end_date)
    df = df.loc[mask]

# Overview metrics
st.subheader("📊 Overview Metrics")
create_overview_metrics(df)

# Create tabs for different report types
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Trends Analysis", 
    "👥 Department Reports", 
    "🎯 Individual Performance",
    "📊 Compliance Dashboard",
    "📥 Export Reports"
])

with tab1:
    st.subheader("Weekly Hours Trend (5-Day Work System)")
    
    # Aggregate data by week - separate excluded employees
    weekly_stats = df.groupby(['Week', 'Is Excluded']).agg({
        'Hours': 'mean',
        'Met Requirements': 'mean',
        'Alert Sent': 'sum',
        'Leave Days': 'mean'
    }).reset_index()
    
    # Focus on alert-enabled employees for main trends
    alert_enabled = weekly_stats[weekly_stats['Is Excluded'] == False]
    
    if len(alert_enabled) > 0:
        # Hours trend
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=alert_enabled['Week'],
            y=alert_enabled['Hours'],
            mode='lines+markers',
            name='Average Hours (Alert-Enabled)',
            line=dict(color='blue', width=2)
        ))
        fig1.add_hline(y=40, line_dash="dash", line_color="green", 
                       annotation_text="Required (40h)")
        fig1.add_hline(y=37, line_dash="dash", line_color="orange", 
                       annotation_text="Acceptable (37h)")
        fig1.update_layout(
            title="Average Weekly Hours Trend (Alert-Enabled Employees)",
            xaxis_title="Week",
            yaxis_title="Hours",
            hovermode='x'
        )
        st.plotly_chart(fig1, width="stretch")
        
        # Compliance trend
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=alert_enabled['Week'],
            y=alert_enabled['Met Requirements'] * 100,
            name='Compliance Rate %',
            marker_color='lightgreen'
        ))
        fig2.update_layout(
            title="Weekly Compliance Rate (5-Day Work System)",
            xaxis_title="Week",
            yaxis_title="Compliance %",
            yaxis_range=[0, 100]
        )
        st.plotly_chart(fig2, width="stretch")
        
        # Alert trend
        col1, col2 = st.columns(2)
        with col1:
            fig3 = px.line(alert_enabled, x='Week', y='Alert Sent',
                          title='Weekly Alerts Sent (Excluding Protected)',
                          markers=True)
            st.plotly_chart(fig3, width="stretch")
        
        with col2:
            # Leave days distribution
            leave_dist = df.groupby('Leave Days').size().reset_index(name='Count')
            fig4 = px.pie(leave_dist, values='Count', names='Leave Days',
                         title='Leave Days Distribution')
            st.plotly_chart(fig4, width="stretch")
    
    # Show exclusion impact
    st.markdown("### 📊 Exclusion Impact Analysis")
    excluded_stats = df[df['Is Excluded'] == True]
    if len(excluded_stats) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Excluded Employees", len(excluded_stats['Employee'].unique()))
        with col2:
            avg_excluded_hours = excluded_stats['Hours'].mean()
            st.metric("Avg Hours (Excluded)", f"{avg_excluded_hours:.1f}h")
        with col3:
            alerts_prevented = len(excluded_stats[excluded_stats['Hours'] < 37])
            st.metric("Alerts Prevented", alerts_prevented)

with tab2:
    st.subheader("Department Analysis (5-Day Work System)")
    
    # Filter to alert-enabled employees for fair comparison
    alert_enabled_df = df[df['Is Excluded'] == False]
    
    if len(alert_enabled_df) > 0:
        # Department summary
        dept_summary = alert_enabled_df.groupby('Department').agg({
            'Hours': ['mean', 'std'],
            'Met Requirements': 'mean',
            'Alert Sent': 'sum',
            'Leave Days': 'mean'
        }).round(2)
        
        dept_summary.columns = ['Avg Hours', 'Std Dev', 'Compliance Rate', 'Total Alerts', 'Avg Leave Days']
        dept_summary['Compliance Rate'] = (dept_summary['Compliance Rate'] * 100).round(1)
        
        # Display table
        st.dataframe(dept_summary, width="stretch")
        
        # Department comparison chart
        fig = px.bar(dept_summary.reset_index(), 
                     x='Department', 
                     y='Avg Hours',
                     color='Compliance Rate',
                     title='Department Hours Comparison (Alert-Enabled Only)',
                     color_continuous_scale='RdYlGn',
                     labels={'Avg Hours': 'Average Hours/Week'})
        fig.add_hline(y=37, line_dash="dash", line_color="orange", annotation_text="Acceptable (37h)")
        fig.add_hline(y=40, line_dash="dash", line_color="green", annotation_text="Required (40h)")
        st.plotly_chart(fig, width="stretch")
        
        # Box plot for hours distribution
        fig_box = px.box(alert_enabled_df, x='Department', y='Hours',
                        title='Hours Distribution by Department (5-Day System)',
                        points="outliers")
        fig_box.add_hline(y=37, line_dash="dash", line_color="orange",
                         annotation_text="Acceptable threshold")
        fig_box.add_hline(y=40, line_dash="dash", line_color="green",
                         annotation_text="Required threshold")
        st.plotly_chart(fig_box, width="stretch")
    else:
        st.warning("No alert-enabled employees found for department analysis")

with tab3:
    st.subheader("Individual Performance Analysis")
    
    # Employee selector - exclude protected employees by default
    show_excluded = st.checkbox("Include excluded employees in analysis", value=False)
    
    if show_excluded:
        available_employees = df['Employee'].unique()
        note = "🚫 Red names are excluded from alerts"
    else:
        available_employees = df[df['Is Excluded'] == False]['Employee'].unique()
        note = "✅ Showing alert-enabled employees only"
    
    st.info(note)
    
    selected_employees = st.multiselect(
        "Select Employees to Analyze",
        options=available_employees,
        default=list(available_employees)[:5]  # Default to first 5
    )
    
    if selected_employees:
        # Filter data
        emp_df = df[df['Employee'].isin(selected_employees)]
        
        # Individual trends
        fig = px.line(emp_df, x='Week', y='Hours',
                     color='Employee',
                     title='Individual Hours Trend (5-Day Work System)',
                     markers=True)
        fig.add_hline(y=37, line_dash="dash", line_color="orange", annotation_text="Acceptable (37h)")
        fig.add_hline(y=40, line_dash="dash", line_color="green", annotation_text="Required (40h)")
        st.plotly_chart(fig, width="stretch")
        
        # Performance summary
        emp_summary = emp_df.groupby(['Employee', 'Is Excluded']).agg({
            'Hours': ['mean', 'min', 'max'],
            'Met Requirements': 'mean',
            'Alert Sent': 'sum',
            'Leave Days': 'sum'
        }).round(2)
        
        emp_summary.columns = ['Avg Hours', 'Min Hours', 'Max Hours', 
                              'Compliance %', 'Alerts Sent', 'Total Leave Days']
        emp_summary['Compliance %'] = (emp_summary['Compliance %'] * 100).round(1)
        emp_summary = emp_summary.reset_index()
        
        # Add status column
        emp_summary['Alert Status'] = emp_summary['Is Excluded'].apply(
            lambda x: '🚫 Excluded' if x else '✅ Alert-Enabled'
        )
        
        st.dataframe(emp_summary.drop('Is Excluded', axis=1), width="stretch", hide_index=True)
        
        # Heatmap of weekly hours
        pivot_df = emp_df.pivot(index='Employee', columns='Week', values='Hours')
        if len(pivot_df) > 0:
            fig_heat = px.imshow(pivot_df,
                               labels=dict(x="Week", y="Employee", color="Hours"),
                               title="Weekly Hours Heatmap",
                               color_continuous_scale='RdYlGn',
                               aspect="auto")
            st.plotly_chart(fig_heat, width="stretch")

with tab4:
    st.subheader("Compliance Dashboard (5-Day Work System)")
    
    # Current week status - focus on alert-enabled employees
    current_week = df[df['Week'] == df['Week'].max()]
    alert_enabled_current = current_week[current_week['Is Excluded'] == False]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Compliance gauge for alert-enabled employees
        if len(alert_enabled_current) > 0:
            compliance_rate = alert_enabled_current['Met Requirements'].mean() * 100
        else:
            compliance_rate = 100
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = compliance_rate,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Current Week Compliance Rate (Alert-Enabled)"},
            delta = {'reference': 90},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen" if compliance_rate > 90 else "orange"},
                'steps': [
                    {'range': [0, 70], 'color': "lightgray"},
                    {'range': [70, 90], 'color': "lightyellow"},
                    {'range': [90, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, width="stretch")
    
    with col2:
        # Quick stats
        st.metric("Alert-Enabled Employees", len(alert_enabled_current))
        st.metric("Below Threshold", 
                 len(alert_enabled_current[~alert_enabled_current['Met Requirements']]))
        st.metric("Alerts Sent This Week", 
                 alert_enabled_current['Alert Sent'].sum())
        st.metric("Excluded (Protected)", 
                 len(current_week[current_week['Is Excluded'] == True]))
    
    # Risk analysis
    st.markdown("### Risk Analysis (5-Day Work System)")
    
    # Identify at-risk employees (consistently below threshold, excluding protected)
    alert_enabled_df = df[df['Is Excluded'] == False]
    
    if len(alert_enabled_df) > 0:
        risk_analysis = alert_enabled_df.groupby('Employee').agg({
            'Met Requirements': 'mean',
            'Hours': 'mean',
            'Alert Sent': 'sum'
        })
        
        at_risk = risk_analysis[risk_analysis['Met Requirements'] < 0.5]
        
        if len(at_risk) > 0:
            st.warning(f"⚠️ {len(at_risk)} alert-enabled employees are consistently below threshold")
            
            at_risk_display = at_risk.copy()
            at_risk_display['Compliance %'] = (at_risk_display['Met Requirements'] * 100).round(1)
            at_risk_display = at_risk_display.drop('Met Requirements', axis=1)
            at_risk_display.columns = ['Avg Hours', 'Total Alerts', 'Compliance %']
            
            st.dataframe(at_risk_display, width="stretch")
        else:
            st.success("✅ No alert-enabled employees identified as consistently at-risk")
    
    # Show exclusion protection stats
    st.markdown("### 🛡️ Exclusion Protection Stats")
    excluded_df = df[df['Is Excluded'] == True]
    
    if len(excluded_df) > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Protected Employees", len(excluded_df['Employee'].unique()))
        with col2:
            would_be_alerts = len(excluded_df[excluded_df['Hours'] < 37])
            st.metric("Alerts Prevented", would_be_alerts)
        with col3:
            avg_protected_hours = excluded_df['Hours'].mean()
            st.metric("Avg Hours (Protected)", f"{avg_protected_hours:.1f}h")

with tab5:
    st.subheader("Export Reports (5-Day Work System)")
    
    # Report type selector
    report_type = st.selectbox(
        "Select Report Type",
        ["Weekly Summary", "Department Report", "Individual Report", "Compliance Report", "Full Data Export", "Exclusion Analysis"]
    )
    
    # Date range for export
    col1, col2 = st.columns(2)
    with col1:
        export_start = st.date_input("Export Start Date", start_date, key="export_start")
    with col2:
        export_end = st.date_input("Export End Date", end_date, key="export_end")
    
    # Generate report button
    if st.button("📄 Generate Report", width="stretch"):
        with st.spinner("Generating report..."):
            
            # Filter data for export
            export_df = df[(df['Week'].dt.date >= export_start) & 
                          (df['Week'].dt.date <= export_end)]
            
            if report_type == "Weekly Summary":
                report_data = export_df.groupby(['Week', 'Is Excluded']).agg({
                    'Hours': ['mean', 'std'],
                    'Met Requirements': 'mean',
                    'Alert Sent': 'sum',
                    'Leave Days': 'mean'
                }).round(2)
                filename = f"weekly_summary_5day_{export_start}_{export_end}.csv"
                
            elif report_type == "Department Report":
                alert_enabled = export_df[export_df['Is Excluded'] == False]
                report_data = alert_enabled.groupby(['Department', 'Week']).agg({
                    'Hours': 'mean',
                    'Met Requirements': 'mean',
                    'Alert Sent': 'sum'
                }).round(2)
                filename = f"department_report_5day_{export_start}_{export_end}.csv"
                
            elif report_type == "Individual Report":
                report_data = export_df.groupby(['Employee', 'Week', 'Is Excluded']).agg({
                    'Hours': 'first',
                    'Required Hours': 'first',
                    'Acceptable Hours': 'first',
                    'Met Requirements': 'first',
                    'Leave Days': 'first',
                    'Alert Sent': 'first'
                }).round(2)
                filename = f"individual_report_5day_{export_start}_{export_end}.csv"
                
            elif report_type == "Compliance Report":
                # Only non-compliant alert-enabled employees
                alert_enabled = export_df[export_df['Is Excluded'] == False]
                report_data = alert_enabled[~alert_enabled['Met Requirements']]
                filename = f"compliance_report_5day_{export_start}_{export_end}.csv"
                
            elif report_type == "Exclusion Analysis":
                # Focus on excluded employees and their stats
                report_data = export_df[export_df['Is Excluded'] == True]
                filename = f"exclusion_analysis_5day_{export_start}_{export_end}.csv"
                
            else:  # Full Data Export
                report_data = export_df
                filename = f"full_export_5day_{export_start}_{export_end}.csv"
            
            # Convert to CSV
            csv = report_data.to_csv()
            
            # Download button
            st.download_button(
                label=f"📥 Download {report_type}",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
            
            st.success(f"✅ {report_type} generated successfully!")
            
            # Show preview of data
            with st.expander("Preview Report Data"):
                st.dataframe(report_data.head(20), width="stretch")

# Help section
with st.expander("❓ Help"):
    st.markdown("""
    ### Reports & Analytics Guide (5-Day Work System)
    
    **System Overview**
    - Work 5 days (Monday-Friday) but have full week to complete 40 hours
    - Weekend days (Saturday-Sunday) available for hour completion
    - 3-hour buffer (37+ hours acceptable)
    - Excluded employees protected from alerts
    
    **Trends Analysis**
    - View weekly averages and compliance trends for alert-enabled employees
    - Monitor alert patterns over time
    - Analyze leave distribution and exclusion impact
    
    **Department Reports**
    - Compare performance across departments (alert-enabled only)
    - Identify departments needing attention
    - View hours distribution patterns
    
    **Individual Performance**
    - Track specific employee trends
    - Compare multiple employees
    - Option to include/exclude protected employees
    - Identify consistent performers or those needing support
    
    **Compliance Dashboard**
    - Real-time compliance metrics for alert-enabled employees
    - Risk analysis for consistently underperforming employees
    - Exclusion protection statistics
    
    **Export Options**
    - Generate various report types
    - Separate analysis for excluded vs alert-enabled employees
    - Customize date ranges
    - Export to CSV for further analysis
    
    ### Key Metrics Explained
    - **Compliance Rate**: % of alert-enabled employees meeting 37+ hours requirement
    - **At-Risk Employees**: Alert-enabled employees with <50% compliance rate
    - **Alerts Prevented**: Number of alerts that would have been sent to excluded employees
    - **Alert Trends**: Pattern of actual alerts sent (excluding protected employees)
    
    ### 5-Day Work System Features
    - **Leave Calculation**: Required hours = 8 × (5 - working_day_leaves)
    - **Weekend Work**: Hours worked Saturday/Sunday count toward requirement
    - **Full Leave Protection**: 5-day leave = automatic protection
    - **Exclusion Protection**: Certain employees never receive alerts
    - **Buffer System**: 3-hour flexibility buffer for all employees
    
    ### Excluded Employees
    The following employees are excluded from all alert calculations:
    - **Aishik Chatterjee**
    - **Tirtharaj Bhoumik**
    - **Vishal Kumar**
    
    These employees' data is tracked but they never receive alerts regardless of hours worked.
    """)