#!/usr/bin/env python3
"""
Comprehensive test to verify if emails are actually sent in preview mode
This will help identify if the issue is cache, multiple processes, or actual bugs
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
import time
from datetime import datetime
from src.workflow_manager import WorkflowManager
from src.email_service import EmailService

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_email_service_preview():
    """Test email service preview mode directly"""
    print("🔍 Testing Email Service Preview Mode")
    print("=" * 50)
    
    email_service = EmailService()
    
    # Check initial state
    initial_count = email_service.emails_sent
    print(f"Initial emails sent count: {initial_count}")
    
    # Test data
    test_data = {
        'email': 'test@example.com',
        'name': 'Test Employee',
        'week_start': '2025-01-01',
        'week_end': '2025-01-07',
        'total_hours': 30.0,
        'required_hours': 40.0,
        'acceptable_hours': 37.0,
        'shortfall': 10.0,
        'shortfall_minutes': 600,
        'days_worked': 5,
        'leave_days': 0
    }
    
    print("\n1. Testing with preview_mode=True...")
    result = email_service.send_low_hours_alert(test_data, preview_mode=True)
    after_preview_count = email_service.emails_sent
    
    print(f"   Result: {result}")
    print(f"   Emails sent count after preview: {after_preview_count}")
    print(f"   Emails sent during preview: {after_preview_count - initial_count}")
    
    if after_preview_count > initial_count:
        print("   ❌ ERROR: Emails were sent during preview mode!")
        return False
    else:
        print("   ✅ SUCCESS: No emails sent during preview mode")
        return True

def test_workflow_preview():
    """Test workflow preview mode"""
    print("\n🔍 Testing Workflow Preview Mode")
    print("=" * 50)
    
    workflow = WorkflowManager()
    email_service = workflow.email_service
    
    # Check initial state
    initial_count = email_service.emails_sent
    print(f"Initial emails sent count: {initial_count}")
    
    print("\n2. Running workflow.run_preview_mode()...")
    start_time = time.time()
    
    try:
        workflow.run_preview_mode()
        end_time = time.time()
        
        after_preview_count = email_service.emails_sent
        print(f"   Execution time: {end_time - start_time:.2f} seconds")
        print(f"   Emails sent count after preview: {after_preview_count}")
        print(f"   Emails sent during preview: {after_preview_count - initial_count}")
        
        if after_preview_count > initial_count:
            print("   ❌ ERROR: Emails were sent during workflow preview mode!")
            return False
        else:
            print("   ✅ SUCCESS: No emails sent during workflow preview mode")
            return True
            
    except Exception as e:
        print(f"   ❌ ERROR: Exception during preview: {str(e)}")
        return False

def test_real_vs_preview():
    """Test the difference between real and preview mode"""
    print("\n🔍 Testing Real vs Preview Mode Difference")
    print("=" * 50)
    
    # Create two separate workflow instances to avoid state contamination
    workflow1 = WorkflowManager()
    workflow2 = WorkflowManager()
    
    print("\n3. Testing real mode (but with fake data to avoid actual emails)...")
    
    # Test with a fake employee that doesn't exist
    fake_employee_data = {
        'email': 'fake.employee@test.com',
        'name': 'Fake Employee',
        'week_start': '2025-01-01',
        'week_end': '2025-01-07',
        'total_hours': 20.0,
        'required_hours': 40.0,
        'acceptable_hours': 37.0,
        'shortfall': 20.0,
        'shortfall_minutes': 1200,
        'days_worked': 5,
        'leave_days': 0
    }
    
    # Test preview mode
    initial_count = workflow1.email_service.emails_sent
    print(f"   Initial count: {initial_count}")
    
    result_preview = workflow1.email_service.send_low_hours_alert(fake_employee_data, preview_mode=True)
    after_preview = workflow1.email_service.emails_sent
    
    print(f"   Preview result: {result_preview}")
    print(f"   Count after preview: {after_preview}")
    
    # Test real mode (should fail due to fake email, but we can see if it tries)
    result_real = workflow2.email_service.send_low_hours_alert(fake_employee_data, preview_mode=False)
    after_real = workflow2.email_service.emails_sent
    
    print(f"   Real mode result: {result_real}")
    print(f"   Count after real mode: {after_real}")
    
    return True

def check_for_background_processes():
    """Check if there are any background processes that might send emails"""
    print("\n🔍 Checking for Background Processes")
    print("=" * 50)
    
    import psutil
    import os
    
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    
    print(f"Current process PID: {current_pid}")
    print(f"Current process name: {current_process.name()}")
    
    # Look for other Python processes that might be running the monitoring system
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                if proc.info['pid'] != current_pid:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'monitoring' in cmdline.lower() or 'workflow' in cmdline.lower() or 'main.py' in cmdline.lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline
                        })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if python_processes:
        print("   ⚠️  Found other monitoring processes:")
        for proc in python_processes:
            print(f"     PID {proc['pid']}: {proc['cmdline']}")
        return False
    else:
        print("   ✅ No other monitoring processes found")
        return True

def main():
    """Main test function"""
    print("🧪 COMPREHENSIVE PREVIEW MODE EMAIL TEST")
    print("=" * 60)
    print("⚠️  This test will help identify why emails might be sent in preview mode")
    print("=" * 60)
    
    results = []
    
    # Test 1: Email service preview
    try:
        result1 = test_email_service_preview()
        results.append(("Email Service Preview", result1))
    except Exception as e:
        print(f"❌ Error in email service test: {e}")
        results.append(("Email Service Preview", False))
    
    # Test 2: Workflow preview
    try:
        result2 = test_workflow_preview()
        results.append(("Workflow Preview", result2))
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        results.append(("Workflow Preview", False))
    
    # Test 3: Real vs Preview comparison
    try:
        result3 = test_real_vs_preview()
        results.append(("Real vs Preview", result3))
    except Exception as e:
        print(f"❌ Error in comparison test: {e}")
        results.append(("Real vs Preview", False))
    
    # Test 4: Background processes
    try:
        result4 = check_for_background_processes()
        results.append(("Background Processes", result4))
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        results.append(("Background Processes", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Preview mode is working correctly")
        print("📧 If you're still receiving emails, the issue might be:")
        print("   1. Browser cache showing old results")
        print("   2. Multiple browser tabs/sessions")
        print("   3. Someone else running the real monitoring")
        print("   4. Scheduled tasks running in background")
    else:
        print("❌ SOME TESTS FAILED - There may be a bug in preview mode")
        print("📧 Emails might actually be sent during preview mode")
    print("=" * 60)

if __name__ == "__main__":
    main()
