#!/usr/bin/env python3
"""
Debug script to test preview mode behavior
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
from src.workflow_manager import WorkflowManager
from src.email_service import EmailService

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_preview_mode():
    """Test if preview mode actually prevents emails from being sent"""
    print("🔍 Testing Preview Mode Behavior")
    print("=" * 50)
    
    # Create workflow manager
    workflow = WorkflowManager()
    
    # Test 1: Check email service configuration
    print("\n1. Checking email service configuration...")
    email_service = workflow.email_service
    is_configured = email_service._is_email_configured()
    print(f"   Email configured: {is_configured}")
    
    if is_configured:
        print(f"   SMTP Host: {email_service.smtp_host}")
        print(f"   SMTP Username: {email_service.smtp_username}")
        print(f"   From Email: {email_service.from_email}")
    
    # Test 2: Test preview mode directly
    print("\n2. Testing email service preview mode...")
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
    
    print("   Calling send_low_hours_alert with preview_mode=True...")
    result = email_service.send_low_hours_alert(test_data, preview_mode=True)
    print(f"   Result: {result}")
    print(f"   Emails sent counter: {email_service.emails_sent}")
    
    # Test 3: Test workflow preview mode
    print("\n3. Testing workflow preview mode...")
    print("   Calling workflow.run_preview_mode()...")
    
    # Capture the initial email count
    initial_count = email_service.emails_sent
    
    # Run preview mode
    workflow.run_preview_mode()
    
    # Check if any emails were sent
    final_count = email_service.emails_sent
    emails_sent_during_preview = final_count - initial_count
    
    print(f"   Initial email count: {initial_count}")
    print(f"   Final email count: {final_count}")
    print(f"   Emails sent during preview: {emails_sent_during_preview}")
    
    if emails_sent_during_preview > 0:
        print("   ❌ ERROR: Emails were sent during preview mode!")
    else:
        print("   ✅ SUCCESS: No emails sent during preview mode")
    
    # Test 4: Check if there's any confusion between methods
    print("\n4. Checking method calls...")
    print("   Available workflow methods:")
    methods = [method for method in dir(workflow) if not method.startswith('_') and callable(getattr(workflow, method))]
    for method in methods:
        if 'run' in method.lower() or 'preview' in method.lower():
            print(f"     - {method}")

if __name__ == "__main__":
    test_preview_mode()
