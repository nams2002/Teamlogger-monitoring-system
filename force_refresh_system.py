#!/usr/bin/env python3
"""
Force Refresh System - Clear all caches and force refresh
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.manager_mapping import refresh_manager_mapping
from src.workflow_manager import WorkflowManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_refresh_all():
    """Force refresh all system components"""
    print("🔄 FORCING COMPLETE SYSTEM REFRESH")
    print("="*50)
    
    try:
        # 1. Force refresh manager mapping
        print("1️⃣ Refreshing Manager Mapping from Google Sheets...")
        mapping = refresh_manager_mapping()
        print(f"   ✅ Loaded {len(mapping)} manager mappings")
        
        # 2. Force refresh workflow manager
        print("\n2️⃣ Refreshing Workflow Manager...")
        workflow = WorkflowManager()
        
        # Get fresh employee data
        work_week_start, work_week_end = workflow._get_monitoring_period()
        all_employees = workflow.teamlogger.get_all_employees()
        filtered_employees = workflow._filter_active_employees(all_employees, work_week_start, work_week_end)
        
        print(f"   📊 TeamLogger employees: {len(all_employees)}")
        print(f"   ✅ Active employees: {len(filtered_employees)}")
        print(f"   ❌ Filtered out: {len(all_employees) - len(filtered_employees)}")
        
        # 3. Show current active employees
        print(f"\n3️⃣ Current Active Employees (first 20):")
        active_names = [emp.get('name', '') for emp in filtered_employees]
        for i, name in enumerate(active_names[:20]):
            print(f"   {i+1:2d}. {name}")
        if len(active_names) > 20:
            print(f"   ... and {len(active_names) - 20} more")
        
        print(f"\n✅ System refresh completed successfully!")
        print(f"📈 Your Streamlit app should now show only {len(filtered_employees)} active employees")
        
        return {
            'success': True,
            'total_employees': len(all_employees),
            'active_employees': len(filtered_employees),
            'filtered_out': len(all_employees) - len(filtered_employees),
            'manager_mappings': len(mapping)
        }
        
    except Exception as e:
        print(f"❌ Error during refresh: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = force_refresh_all()
    print("\n" + "="*50)
    if result['success']:
        print("🎉 REFRESH COMPLETED - Your system is now up to date!")
    else:
        print(f"💥 REFRESH FAILED: {result['error']}")
