"""
Activity Tracking Page for TeamLogger Monitoring System

This page provides comprehensive activity tracking and analysis features,
including activity percentages, productivity trends, and detailed reports.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.teamlogger_client import TeamLoggerClient
from src.activity_analysis import ActivityAnalyzer
from src.activity_tracker import ActivityTracker

# Page configuration
st.set_page_config(
    page_title="Activity Tracking - TeamLogger Monitor",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Activity Tracking & Productivity Analysis")
st.markdown("Track activity percentages, analyze productivity patterns, and monitor team performance.")

# Initialize clients
@st.cache_resource
def get_clients():
    """Initialize and cache TeamLogger client and analyzer"""
    try:
        teamlogger = TeamLoggerClient()
        analyzer = ActivityAnalyzer(teamlogger)
        return teamlogger, analyzer
    except Exception as e:
        st.error(f"Failed to initialize clients: {e}")
        return None, None

teamlogger, analyzer = get_clients()

if not teamlogger or not analyzer:
    st.error("❌ Unable to connect to TeamLogger. Please check your configuration.")
    st.stop()

# Initialize workflow manager for monitoring functionality
@st.cache_resource
def get_workflow_manager():
    """Initialize and cache workflow manager"""
    try:
        from src.workflow_manager import WorkflowManager
        return WorkflowManager()
    except Exception as e:
        st.error(f"Failed to initialize workflow manager: {e}")
        return None

workflow = get_workflow_manager()

# Function definitions for activity monitoring
def preview_activity_alerts():
    """Preview activity alerts functionality"""
    if not workflow:
        st.error("❌ Workflow manager not available")
        return

    st.subheader("🔍 Activity Alerts Preview")

    with st.spinner("🔍 Analyzing employee activity levels..."):
        employees_needing_alerts = workflow.get_employees_needing_activity_alerts()

    if not employees_needing_alerts:
        st.success("✅ No employees need activity alerts for the previous work week!")
        st.info("All employees met the minimum activity threshold (50%)")
    else:
        st.warning(f"⚠️ {len(employees_needing_alerts)} employees would receive activity alerts")

        # Create tabs
        tab1, tab2, tab3 = st.tabs(["📋 Employee List", "📊 Analysis", "📧 Email Preview"])

        with tab1:
            # Convert to DataFrame
            activity_data = []
            for emp in employees_needing_alerts:
                activity_data.append({
                    'Name': emp['name'],
                    'Activity %': f"{emp['activity_percentage']:.1f}%",
                    'Threshold': f"{emp['activity_threshold']:.0f}%",
                    'Shortfall': f"{emp['activity_shortfall']:.1f}%",
                    'Hours Worked': f"{emp['hours_worked']:.1f}h",
                    'Leave Days': emp['leave_days'],
                    'Trend': emp['activity_trend'],
                    'Manager': emp['manager_name']
                })

            df = pd.DataFrame(activity_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Download button
            if len(df) > 0:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Activity Alert List (CSV)",
                    data=csv,
                    file_name=f"activity_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="activity_preview_download"
                )

        with tab2:
            # Activity analysis
            if len(employees_needing_alerts) > 0:
                activity_percentages = [emp['activity_percentage'] for emp in employees_needing_alerts]

                # Activity distribution chart
                fig = px.histogram(
                    x=activity_percentages,
                    nbins=10,
                    title='Activity Percentage Distribution (Below 50% Threshold)',
                    labels={'x': 'Activity Percentage', 'y': 'Count'}
                )
                fig.add_vline(x=50, line_dash="dash", line_color="red", annotation_text="Threshold (50%)")
                st.plotly_chart(fig, use_container_width=True)

                # Summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Activity", f"{sum(activity_percentages)/len(activity_percentages):.1f}%")
                with col2:
                    st.metric("Lowest Activity", f"{min(activity_percentages):.1f}%")
                with col3:
                    st.metric("Employees Below 30%", len([x for x in activity_percentages if x < 30]))

        with tab3:
            # Email preview
            if len(employees_needing_alerts) > 0:
                sample = employees_needing_alerts[0]

                st.markdown(f"""
                **To:** {sample['email']}
                **CC:** {sample['manager_email']}, teamhr@rapidinnovation.dev
                **Subject:** Activity Level Reminder - {sample['name']}

                ---

                Dear {sample['name']},

                This is a notification regarding your activity levels for the previous work week.

                **Activity Summary:**
                - Your Activity Level: **{sample['activity_percentage']:.1f}%**
                - Required Threshold: **{sample['activity_threshold']:.0f}%**
                - Activity Shortfall: **{sample['activity_shortfall']:.1f}%**
                - Hours Worked: {sample['hours_worked']:.1f}h
                - Activity Trend: {sample['activity_trend']}

                Your activity level was below our minimum threshold. Please review your work patterns and consider the recommendations in the full email.

                Best regards,
                HR Team
                """)

def run_activity_monitoring():
    """Run the activity monitoring workflow"""
    if not workflow:
        st.error("❌ Workflow manager not available")
        return None

    with st.spinner("🔄 Running activity monitoring workflow..."):
        try:
            results = workflow.run_activity_monitoring_workflow()
            return results
        except Exception as e:
            st.error(f"❌ Activity monitoring failed: {str(e)}")
            return None

def display_activity_monitoring_results(results):
    """Display activity monitoring results"""
    st.success("✅ Activity monitoring completed!")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Employees Checked", results.get('total_employees_checked', 0))
    with col2:
        st.metric("Activity Alerts Sent", results.get('activity_alerts_sent', 0))
    with col3:
        st.metric("Errors", results.get('activity_errors', 0))

    st.info(f"⏱️ Execution time: {results.get('execution_time', 'Unknown')}")

def show_activity_statistics():
    """Show activity statistics"""
    if not workflow:
        st.error("❌ Workflow manager not available")
        return

    st.subheader("📊 Activity Statistics")

    with st.spinner("📊 Generating activity statistics..."):
        employees_needing_alerts = workflow.get_employees_needing_activity_alerts()

        # Get all employees for comparison
        all_employees = workflow.teamlogger.get_all_employees()
        work_week_start, work_week_end = workflow._get_monitoring_period()
        active_employees = workflow._filter_active_employees(all_employees, work_week_start, work_week_end)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Active Employees", len(active_employees))
        with col2:
            st.metric("Need Activity Alerts", len(employees_needing_alerts))
        with col3:
            alert_rate = (len(employees_needing_alerts) / len(active_employees) * 100) if active_employees else 0
            st.metric("Alert Rate", f"{alert_rate:.1f}%")
        with col4:
            good_activity = len(active_employees) - len(employees_needing_alerts)
            st.metric("Good Activity (≥50%)", good_activity)

# Sidebar controls
st.sidebar.header("📅 Analysis Period")

# Date range selection
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=7),
        max_value=datetime.now().date()
    )

with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now().date(),
        max_value=datetime.now().date()
    )

# Convert to datetime
start_datetime = datetime.combine(start_date, datetime.min.time())
end_datetime = datetime.combine(end_date, datetime.max.time())

# Analysis type selection
analysis_type = st.sidebar.selectbox(
    "Analysis Type",
    ["Team Overview", "Individual Employee", "Productivity Patterns", "Detailed Reports"]
)

# Employee selection for individual analysis
selected_employee = None
if analysis_type == "Individual Employee":
    try:
        employees = teamlogger.get_all_employees()
        employee_names = [f"{emp['name']} ({emp['id']})" for emp in employees]
        selected_name = st.sidebar.selectbox("Select Employee", employee_names)
        
        if selected_name:
            employee_id = selected_name.split('(')[-1].rstrip(')')
            selected_employee = next(emp for emp in employees if emp['id'] == employee_id)
    except Exception as e:
        st.sidebar.error(f"Error loading employees: {e}")

# Main content area
if st.sidebar.button("🔄 Analyze Activity", type="primary"):
    
    if analysis_type == "Team Overview":
        st.header("🏢 Team Activity Overview")
        
        with st.spinner("Analyzing team activity..."):
            team_analysis = analyzer.analyze_team_activity(start_datetime, end_datetime)
        
        if team_analysis and team_analysis.get('team_statistics'):
            stats = team_analysis['team_statistics']
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Team Average Activity",
                    f"{stats.get('team_average_activity', 0):.1f}%",
                    help="Average activity percentage across all team members"
                )
            
            with col2:
                st.metric(
                    "High Performers",
                    stats.get('high_performers', 0),
                    help="Employees with >70% average activity"
                )
            
            with col3:
                st.metric(
                    "Employees Analyzed",
                    stats.get('total_analyzed', 0),
                    help="Number of employees with activity data"
                )
            
            with col4:
                improving = stats.get('improving_employees', 0)
                declining = stats.get('declining_employees', 0)
                trend_delta = improving - declining
                st.metric(
                    "Trend Balance",
                    f"+{trend_delta}" if trend_delta >= 0 else str(trend_delta),
                    delta=f"{improving} improving, {declining} declining",
                    help="Net difference between improving and declining employees"
                )
            
            # Team performance distribution
            st.subheader("📈 Team Performance Distribution")
            
            performance_data = {
                'Performance Level': ['High (>70%)', 'Medium (30-70%)', 'Low (<30%)'],
                'Count': [
                    stats.get('high_performers', 0),
                    stats.get('medium_performers', 0),
                    stats.get('low_performers', 0)
                ],
                'Color': ['#28a745', '#ffc107', '#dc3545']
            }
            
            fig_performance = px.bar(
                performance_data,
                x='Performance Level',
                y='Count',
                color='Performance Level',
                color_discrete_map={
                    'High (>70%)': '#28a745',
                    'Medium (30-70%)': '#ffc107',
                    'Low (<30%)': '#dc3545'
                },
                title="Employee Performance Distribution"
            )
            st.plotly_chart(fig_performance, use_container_width=True)
            
            # Activity insights
            st.subheader("💡 Activity Insights")
            insights = analyzer.generate_activity_insights(team_analysis)
            for insight in insights:
                st.info(insight)
            
            # Individual employee data
            st.subheader("👥 Individual Employee Activity")
            
            reports = team_analysis.get('team_reports', [])
            if reports:
                employee_data = []
                for report in reports:
                    employee_data.append({
                        'Employee': report.employee_name,
                        'Average Activity': f"{report.overall_average_activity:.1f}%",
                        'Trend': report.activity_trend,
                        'Low Periods': report.total_low_productivity_periods,
                        'High Periods': report.total_high_productivity_periods,
                        'Days with Data': len(report.daily_summaries)
                    })
                
                df_employees = pd.DataFrame(employee_data)
                st.dataframe(df_employees, use_container_width=True)
                
                # Download option
                csv = df_employees.to_csv(index=False)
                st.download_button(
                    label="📥 Download Team Activity Report",
                    data=csv,
                    file_name=f"team_activity_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("No activity data available for the selected period.")
    
    elif analysis_type == "Individual Employee" and selected_employee:
        st.header(f"👤 Individual Activity Analysis: {selected_employee['name']}")
        
        with st.spinner(f"Analyzing activity for {selected_employee['name']}..."):
            report = teamlogger.generate_employee_activity_report(
                selected_employee['id'], start_datetime, end_datetime
            )
        
        if report and report.daily_summaries:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Average Activity",
                    f"{report.overall_average_activity:.1f}%"
                )
            
            with col2:
                st.metric(
                    "Activity Trend",
                    report.activity_trend,
                    delta="Improving" if report.activity_trend == "Improving" else None
                )
            
            with col3:
                st.metric(
                    "Low Productivity Periods",
                    report.total_low_productivity_periods
                )
            
            with col4:
                st.metric(
                    "High Productivity Periods",
                    report.total_high_productivity_periods
                )
            
            # Daily activity chart
            st.subheader("📅 Daily Activity Breakdown")
            
            daily_data = []
            for daily in report.daily_summaries:
                daily_data.append({
                    'Date': daily.date.strftime('%Y-%m-%d'),
                    'Day': daily.date.strftime('%A'),
                    'Average Activity': daily.average_activity,
                    'Productivity Score': daily.productivity_score,
                    'Active Hours': daily.total_active_hours,
                    'Periods': daily.total_periods
                })
            
            df_daily = pd.DataFrame(daily_data)
            
            # Activity trend chart
            fig_trend = px.line(
                df_daily,
                x='Date',
                y='Average Activity',
                title=f"Daily Activity Trend - {selected_employee['name']}",
                markers=True
            )
            fig_trend.add_hline(y=70, line_dash="dash", line_color="green", annotation_text="High Performance (70%)")
            fig_trend.add_hline(y=30, line_dash="dash", line_color="red", annotation_text="Low Performance (30%)")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Daily breakdown table
            st.subheader("📊 Daily Activity Details")
            st.dataframe(df_daily, use_container_width=True)
            
            # Most/Least productive days
            if report.most_productive_day and report.least_productive_day:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success(f"🏆 Most Productive Day: {report.most_productive_day.strftime('%A, %B %d')}")
                
                with col2:
                    st.warning(f"📉 Least Productive Day: {report.least_productive_day.strftime('%A, %B %d')}")
        
        else:
            st.warning(f"No activity data available for {selected_employee['name']} in the selected period.")
    
    elif analysis_type == "Productivity Patterns":
        st.header("🔍 Productivity Patterns Analysis")
        
        with st.spinner("Analyzing productivity patterns..."):
            team_analysis = analyzer.analyze_team_activity(start_datetime, end_datetime)
        
        if team_analysis and team_analysis.get('team_reports'):
            reports = team_analysis['team_reports']
            patterns = analyzer.identify_productivity_patterns(reports)
            
            # Most/Least productive days analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Most Productive Days")
                most_productive = patterns.get('most_productive_days', {})
                if most_productive:
                    fig_most = px.bar(
                        x=list(most_productive.keys()),
                        y=list(most_productive.values()),
                        title="Most Productive Days of Week",
                        color=list(most_productive.values()),
                        color_continuous_scale="Greens"
                    )
                    st.plotly_chart(fig_most, use_container_width=True)
                else:
                    st.info("No data available")
            
            with col2:
                st.subheader("📉 Least Productive Days")
                least_productive = patterns.get('least_productive_days', {})
                if least_productive:
                    fig_least = px.bar(
                        x=list(least_productive.keys()),
                        y=list(least_productive.values()),
                        title="Least Productive Days of Week",
                        color=list(least_productive.values()),
                        color_continuous_scale="Reds"
                    )
                    st.plotly_chart(fig_least, use_container_width=True)
                else:
                    st.info("No data available")
            
            # High performers
            st.subheader("🌟 High Performers")
            high_performers = patterns.get('high_performers', [])
            if high_performers:
                hp_df = pd.DataFrame(high_performers)
                st.dataframe(hp_df, use_container_width=True)
            else:
                st.info("No high performers identified in this period")
            
            # Employees needing attention
            st.subheader("⚠️ Employees Needing Attention")
            attention_needed = patterns.get('employees_needing_attention', [])
            if attention_needed:
                attention_df = pd.DataFrame(attention_needed)
                st.dataframe(attention_df, use_container_width=True)
            else:
                st.success("No employees need immediate attention")
        
        else:
            st.warning("No data available for pattern analysis.")
    
    elif analysis_type == "Detailed Reports":
        st.header("📋 Detailed Activity Reports")
        
        with st.spinner("Generating detailed reports..."):
            team_analysis = analyzer.analyze_team_activity(start_datetime, end_datetime)
        
        if team_analysis:
            # Export to DataFrame
            df_export = analyzer.export_activity_data_to_dataframe(team_analysis)
            
            if not df_export.empty:
                st.subheader("📊 Comprehensive Activity Data")
                st.dataframe(df_export, use_container_width=True)
                
                # Download options
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = df_export.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv_data,
                        file_name=f"detailed_activity_report_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Convert to Excel format (simplified)
                    excel_data = df_export.to_csv(index=False)
                    st.download_button(
                        label="📊 Download as Excel-compatible CSV",
                        data=excel_data,
                        file_name=f"detailed_activity_report_{start_date}_{end_date}_excel.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No detailed data available for export.")
        else:
            st.error("Failed to generate detailed reports.")

else:
    # Default view - instructions
    st.info("👆 Select an analysis type and click 'Analyze Activity' to get started.")
    
    st.markdown("""
    ## 📊 Activity Tracking Features
    
    ### Team Overview
    - View team-wide activity statistics
    - Performance distribution analysis
    - Activity insights and recommendations
    
    ### Individual Employee Analysis
    - Detailed activity breakdown by employee
    - Daily activity trends
    - Productivity scoring
    
    ### Productivity Patterns
    - Identify most/least productive days
    - High performer recognition
    - Employees needing attention
    
    ### Detailed Reports
    - Comprehensive data export
    - CSV and Excel-compatible formats
    - Full activity metrics
    
    ## 📈 Activity Metrics Explained
    
    - **Activity Percentage**: Ratio of active time to total logged time
    - **Low Productivity**: < 30% activity in a period
    - **High Productivity**: > 70% activity in a period
    - **Productivity Score**: Overall assessment (Low/Medium/High)
    - **Activity Trend**: Direction of change (Improving/Declining/Stable)
    """)



# Activity Monitoring & Alerts Section
st.markdown("---")
st.header("🚨 Activity Monitoring & Alerts")

if workflow:
    # Get monitoring period
    work_week_start, work_week_end = workflow._get_monitoring_period()
    st.info(f"📅 Monitoring Period: {work_week_start.strftime('%Y-%m-%d')} to {work_week_end.strftime('%Y-%m-%d')} (Previous Week)")

    # Activity monitoring actions
    st.subheader("🎯 Activity Monitoring Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔍 Preview Activity Alerts", use_container_width=True, type="primary",
                    help="See who would receive activity alerts"):
            preview_activity_alerts()

    with col2:
        if st.button("📧 Run Activity Monitoring", use_container_width=True, type="secondary",
                    help="Run activity monitoring and send alerts"):
            if st.session_state.get('confirm_activity_run', False):
                results = run_activity_monitoring()
                if results:
                    st.session_state.activity_monitoring_results = results
                    display_activity_monitoring_results(results)
                st.session_state.confirm_activity_run = False
            else:
                st.warning("⚠️ This will send actual emails to employees with low activity!")
                if st.button("✅ Confirm and Run Activity Monitoring", type="primary"):
                    st.session_state.confirm_activity_run = True
                    st.rerun()

    with col3:
        if st.button("📊 Activity Statistics", use_container_width=True,
                    help="View activity statistics"):
            show_activity_statistics()

else:
    st.error("❌ Workflow manager not available. Activity monitoring disabled.")

# Footer
st.markdown("---")
st.markdown("*Activity tracking helps identify productivity patterns and optimize team performance.*")
