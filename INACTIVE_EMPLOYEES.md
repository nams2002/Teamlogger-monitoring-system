# Inactive Employees Documentation

## Overview
This document tracks employees who have left the organization but may still appear in TeamLogger data. The system automatically filters these employees from monitoring, alerts, and reports.

## Current Inactive Employees (Left Organization)

### As of July 2025:

1. **Priya Bhadauria** - Left organization, removed from Google Sheets
2. **aishik chatterjee** - Left organization, removed from Google Sheets  
3. **Ashique Mohammed C** - Left organization, removed from Google Sheets
4. **Aayush Limbbad** (also spelled "Aayush Limbad") - Left organization, removed from Google Sheets
5. **Kajol Jaiswal** - Left organization, removed from Google Sheets
6. **Tirtharaj Bhowmik** - Left organization, removed from Google Sheets
7. **Neeraj Deshpande** - Left organization, removed from Google Sheets and manager mapping
8. **Arsh Sohal** - Left organization, removed from Google Sheets

## System Behavior

### Automatic Filtering
The system automatically filters out inactive employees from:
- ✅ Email alerts and notifications
- ✅ Monitoring workflows and statistics
- ✅ Employee reports and dashboards
- ✅ Manager CC lists
- ✅ Leave tracking calculations

### Detection Method
Employees are considered inactive if they:
1. Exist in TeamLogger (still have historical data)
2. Do NOT exist in current Google Sheets leave tracker
3. Are listed in the known inactive employees list

### Manager Email Cleanup
- **Neeraj Deshpande's email** (`neerajdeshpande@rapidinnovation.dev`) has been removed from manager email mapping
- Employees previously reporting to Neeraj have been reassigned to other managers
- No alerts will be sent to Neeraj's email address

## Technical Implementation

### Code Locations
- **Employee Filtering**: `src/workflow_manager.py` - `_filter_active_employees()` method
- **Manager Mapping**: `src/manager_mapping.py` - Dynamic Google Sheets integration
- **Known Inactive List**: Hardcoded in workflow manager for performance

### Verification Commands
```bash
# Check inactive employees
python show_inactive_employees.py

# Check specific employee status
python check_arsh_and_neeraj.py

# Force system refresh
python force_refresh_system.py
```

## Statistics

### Current Numbers (July 2025)
- **Total TeamLogger Employees**: 94
- **Active Employees**: 86
- **Inactive Employees**: 8
- **Filtering Efficiency**: 100% (all inactive employees properly excluded)

## Maintenance

### Adding New Inactive Employees
1. Add employee name to `KNOWN_INACTIVE_EMPLOYEES` set in `workflow_manager.py`
2. Remove from Google Sheets leave tracker
3. Update manager mapping if they were a manager
4. Remove manager email if applicable

### Verification Process
1. Run `show_inactive_employees.py` to verify current status
2. Check Streamlit app employee count matches active employees
3. Verify no alerts are sent to inactive employee emails
4. Confirm manager mappings are updated

## Last Updated
- **Date**: July 14, 2025
- **Updated By**: System Administrator
- **Reason**: Arsh Sohal and Neeraj Deshpande departure confirmation
