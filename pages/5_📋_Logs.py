"""
Logs Page - View system logs and alert history
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import re

from config.settings import Config

st.set_page_config(
    page_title="Logs - Employee Hours",
    page_icon="📋",
    layout="wide"
)

def read_log_file(filepath, max_lines=1000):
    """Read log file and return last n lines"""
    try:
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-max_lines:]  # Return last n lines
    except Exception as e:
        st.error(f"Error reading log file: {str(e)}")
        return []

def parse_log_line(line):
    """Parse a log line into components"""
    # Pattern for typical log format: YYYY-MM-DD HH:MM:SS - LEVEL - MESSAGE
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*-\s*(\w+)\s*-\s*(.+)'
    match = re.match(pattern, line.strip())
    
    if match:
        return {
            'timestamp': match.group(1),
            'level': match.group(2),
            'message': match.group(3)
        }
    else:
        # Fallback for lines that don't match the pattern
        return {
            'timestamp': '',
            'level': 'INFO',
            'message': line.strip()
        }

def filter_logs(logs, level_filter, search_term, date_filter):
    """Filter logs based on criteria"""
    filtered_logs = []
    
    for log in logs:
        parsed = parse_log_line(log)
        
        # Apply level filter
        if level_filter != "All" and parsed['level'] != level_filter:
            continue
        
        # Apply search filter
        if search_term and search_term.lower() not in parsed['message'].lower():
            continue
        
        # Apply date filter
        if date_filter and parsed['timestamp']:
            try:
                log_date = datetime.strptime(parsed['timestamp'].split()[0], '%Y-%m-%d')
                if log_date.date() != date_filter:
                    continue
            except:
                pass
        
        filtered_logs.append(parsed)
    
    return filtered_logs

def generate_mock_alert_history():
    """Generate mock alert history for demonstration"""
    data = []
    
    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        
        # Skip weekends
        if date.weekday() in [5, 6]:
            continue
        
        # Only generate for Mondays
        if date.weekday() == 0:
            num_alerts = 5 + (hash(str(date)) % 10)
            
            for i in range(num_alerts):
                data.append({
                    'Date': date.strftime('%Y-%m-%d'),
                    'Time': '08:00:00',
                    'Employee': f"Employee {(i + days_ago) % 20 + 1}",
                    'Hours Worked': 30 + (hash(f"{date}{i}") % 10),
                    'Required': 40,
                    'Status': 'Sent',
                    'Email': f"emp{(i + days_ago) % 20 + 1}@company.com"
                })
    
    return pd.DataFrame(data)

# Main page
st.title("📋 System Logs & Alert History")
st.markdown("View application logs and email alert history")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📄 Application Logs", "📧 Alert History", "📊 Log Analytics"])

with tab1:
    st.subheader("Application Logs")
    
    # Log file selector
    log_files = {
        "Application Log": Config.LOG_FILE,
        "Personal Test Log": "logs/personal_test.log",
        "Test Results": "test_results.log"
    }
    
    selected_log = st.selectbox("Select Log File", list(log_files.keys()))
    log_path = log_files[selected_log]
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        level_filter = st.selectbox(
            "Log Level",
            ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
    
    with col2:
        search_term = st.text_input("Search", placeholder="Search in logs...")
    
    with col3:
        date_filter = st.date_input("Date Filter", value=None)
    
    with col4:
        max_lines = st.number_input("Max Lines", value=500, min_value=100, max_value=5000, step=100)
    
    # Read and display logs
    if st.button("🔄 Refresh Logs"):
        st.rerun()
    
    # Read log file
    log_lines = read_log_file(log_path, max_lines)
    
    if log_lines:
        # Filter logs
        filtered_logs = filter_logs(log_lines, level_filter, search_term, date_filter)
        
        # Display summary
        st.info(f"Showing {len(filtered_logs)} log entries (from last {max_lines} lines)")
        
        # Color coding for log levels
        level_colors = {
            'DEBUG': '#6c757d',
            'INFO': '#0d6efd',
            'WARNING': '#ffc107',
            'ERROR': '#dc3545',
            'CRITICAL': '#721c24'
        }
        
        # Display logs in reverse order (newest first)
        for log in reversed(filtered_logs[-100:]):  # Show last 100 filtered entries
            color = level_colors.get(log['level'], '#000000')
            
            if log['timestamp']:
                st.markdown(
                    f"<div style='margin: 5px 0; padding: 5px; border-left: 3px solid {color};'>"
                    f"<span style='color: #666;'>{log['timestamp']}</span> "
                    f"<span style='color: {color}; font-weight: bold;'>[{log['level']}]</span> "
                    f"{log['message']}"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.text(log['message'])
        
        # Download logs button
        if filtered_logs:
            log_text = "\n".join([
                f"{log['timestamp']} - {log['level']} - {log['message']}"
                for log in filtered_logs
            ])
            
            st.download_button(
                "📥 Download Filtered Logs",
                data=log_text,
                file_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    else:
        st.warning(f"No logs found in {log_path}")

with tab2:
    st.subheader("Alert History")
    
    # Generate mock alert history
    alert_df = generate_mock_alert_history()
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        alert_start = st.date_input("Start Date", datetime.now() - timedelta(days=30), key="alert_start")
    with col2:
        alert_end = st.date_input("End Date", datetime.now(), key="alert_end")
    
    # Filter data
    alert_df['Date'] = pd.to_datetime(alert_df['Date'])
    mask = (alert_df['Date'].dt.date >= alert_start) & (alert_df['Date'].dt.date <= alert_end)
    filtered_alerts = alert_df.loc[mask]
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", len(filtered_alerts))
    
    with col2:
        unique_employees = filtered_alerts['Employee'].nunique()
        st.metric("Unique Employees", unique_employees)
    
    with col3:
        avg_hours = filtered_alerts['Hours Worked'].mean()
        st.metric("Avg Hours (Alerted)", f"{avg_hours:.1f}h")
    
    with col4:
        success_rate = (filtered_alerts['Status'] == 'Sent').mean() * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    # Alert table
    st.markdown("---")
    st.markdown("### Alert Details")
    
    # Configure column display
    column_config = {
        "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
        "Hours Worked": st.column_config.NumberColumn("Hours Worked", format="%.1f h"),
        "Required": st.column_config.NumberColumn("Required", format="%d h"),
        "Status": st.column_config.TextColumn("Status", help="Alert delivery status")
    }
    
    st.dataframe(
        filtered_alerts.sort_values('Date', ascending=False),
        width="stretch",
        hide_index=True,
        column_config=column_config
    )
    
    # Download alert history
    csv = filtered_alerts.to_csv(index=False)
    st.download_button(
        "📥 Download Alert History",
        data=csv,
        file_name=f"alert_history_{alert_start}_{alert_end}.csv",
        mime="text/csv"
    )

with tab3:
    st.subheader("Log Analytics")
    
    # Read logs for analytics
    log_lines = read_log_file(Config.LOG_FILE, max_lines=5000)
    
    if log_lines:
        # Parse all logs
        all_logs = [parse_log_line(line) for line in log_lines]
        logs_df = pd.DataFrame(all_logs)
        
        # Clean up data
        logs_df = logs_df[logs_df['timestamp'] != '']
        logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'], errors='coerce')
        logs_df = logs_df.dropna(subset=['timestamp'])
        
        # Log level distribution
        st.markdown("### Log Level Distribution")
        level_counts = logs_df['level'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                values=level_counts.values, 
                names=level_counts.index,
                title="Log Levels",
                color_discrete_map={
                    'DEBUG': '#6c757d',
                    'INFO': '#0d6efd',
                    'WARNING': '#ffc107',
                    'ERROR': '#dc3545',
                    'CRITICAL': '#721c24'
                }
            )
            st.plotly_chart(fig_pie, width="stretch")
        
        with col2:
            # Hourly distribution
            logs_df['hour'] = logs_df['timestamp'].dt.hour
            hourly_counts = logs_df['hour'].value_counts().sort_index()
            
            fig_bar = px.bar(
                x=hourly_counts.index,
                y=hourly_counts.values,
                title="Logs by Hour of Day",
                labels={'x': 'Hour', 'y': 'Count'}
            )
            st.plotly_chart(fig_bar, width="stretch")
        
        # Time series of logs
        st.markdown("### Log Activity Over Time")
        
        # Group by date and level
        daily_logs = logs_df.groupby([logs_df['timestamp'].dt.date, 'level']).size().reset_index(name='count')
        daily_logs.columns = ['date', 'level', 'count']
        
        fig_line = px.line(
            daily_logs, 
            x='date', 
            y='count',
            color='level',
            title="Daily Log Activity by Level",
            color_discrete_map={
                'DEBUG': '#6c757d',
                'INFO': '#0d6efd',
                'WARNING': '#ffc107',
                'ERROR': '#dc3545',
                'CRITICAL': '#721c24'
            }
        )
        st.plotly_chart(fig_line, width="stretch")
        
        # Error analysis
        errors_df = logs_df[logs_df['level'].isin(['ERROR', 'CRITICAL'])]
        
        if len(errors_df) > 0:
            st.markdown("### Error Analysis")
            st.warning(f"Found {len(errors_df)} error/critical logs in the selected period")
            
            # Show recent errors
            st.markdown("**Recent Errors:**")
            for _, error in errors_df.tail(5).iterrows():
                st.error(f"{error['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {error['message'][:200]}...")
        else:
            st.success("✅ No errors found in the logs!")
        
        # Common log patterns
        st.markdown("### Common Log Patterns")
        
        # Extract common phrases (simple approach)
        common_patterns = {
            'Workflow Started': logs_df['message'].str.contains('Starting Employee Hours', case=False).sum(),
            'Alerts Sent': logs_df['message'].str.contains('Alert sent', case=False).sum(),
            'Connection Tests': logs_df['message'].str.contains('Testing.*connection', case=False).sum(),
            'Errors': logs_df['message'].str.contains('Error|Failed', case=False).sum(),
            'Warnings': logs_df['message'].str.contains('Warning', case=False).sum()
        }
        
        pattern_df = pd.DataFrame(list(common_patterns.items()), columns=['Pattern', 'Count'])
        
        fig_patterns = px.bar(
            pattern_df, 
            x='Pattern', 
            y='Count',
            title="Common Log Patterns",
            color='Count',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_patterns, width="stretch")
    
    else:
        st.warning("No logs available for analytics")

# Help section
with st.expander("❓ Help"):
    st.markdown("""
    ### Logs & Alert History Guide
    
    **Application Logs**
    - View real-time system logs
    - Filter by log level, date, or search terms
    - Download filtered logs for offline analysis
    - Color-coded by severity level
    
    **Alert History**
    - Track all sent email alerts
    - View employee alert patterns
    - Export history for compliance
    
    **Log Analytics**
    - Visualize log patterns over time
    - Identify error trends
    - Monitor system health
    
    ### Log Levels Explained
    - **DEBUG**: Detailed debugging information
    - **INFO**: General informational messages
    - **WARNING**: Warning messages for potential issues
    - **ERROR**: Error messages for failures
    - **CRITICAL**: Critical issues requiring immediate attention
    
    ### Tips
    - Use search to find specific events
    - Filter by ERROR/CRITICAL to find issues quickly
    - Check hourly distribution to understand system usage patterns
    - Regular log review helps maintain system health
    """)
