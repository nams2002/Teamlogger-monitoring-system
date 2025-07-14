#!/usr/bin/env python3
"""
Test script to verify that preview mode doesn't send emails
"""

from src.workflow_manager import WorkflowManager
from src.email_service import EmailService
import logging

# Set up logging to see what happens
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_preview_mode():
    print("🔍 Testing Preview Mode - NO EMAILS SHOULD BE SENT")
    print("=" * 60)
    
    try:
        # Test 1: Direct email service preview mode
        print("\n1️⃣ Testing Email Service Preview Mode...")
        email_service = EmailService()
        
        # Create test email data
        test_data = {
            'email': 'test@example.com',
            'name': 'Test Employee',
            'week_start': '2025-07-01',
            'week_end': '2025-07-07',
            'total_hours': 35.5,
            'required_hours': 40.0,
            'acceptable_hours': 37.0,
            'shortfall': 4.5,
            'shortfall_minutes': 270,
            'days_worked': 5,
            'leave_days': 0
        }
        
        # Test preview mode (should NOT send email)
        print("Testing with preview_mode=True (should NOT send email):")
        result = email_service.send_low_hours_alert(test_data, preview_mode=True)
        print(f"Result: {result} (should be True for successful preview)")
        
        # Test 2: Workflow Manager Preview Mode
        print("\n2️⃣ Testing Workflow Manager Preview Mode...")
        workflow = WorkflowManager()
        
        print("Running workflow.run_preview_mode() - NO EMAILS SHOULD BE SENT:")
        workflow.run_preview_mode()
        
        print("\n✅ Preview mode test completed!")
        print("📧 Check the logs above - you should see 'PREVIEW MODE' messages")
        print("❌ If you see any actual email sending, there's still an issue")
        
    except Exception as e:
        print(f"❌ Error during preview mode test: {str(e)}")
        import traceback
        traceback.print_exc()

def test_regular_mode_warning():
    print("\n⚠️  Testing Regular Mode (for comparison)")
    print("=" * 60)
    print("NOTE: This would normally send emails, but should be blocked by email configuration")
    
    try:
        workflow = WorkflowManager()
        
        # Get employees who would need alerts
        employees_needing_alerts = workflow.get_employees_needing_real_alerts()
        
        if employees_needing_alerts:
            print(f"Found {len(employees_needing_alerts)} employees who would need alerts")
            print("If you ran workflow.run_workflow(), emails would be sent to these employees")
            
            # Show first few employees
            for i, emp_data in enumerate(employees_needing_alerts[:3]):
                employee = emp_data['employee']
                print(f"  {i+1}. {employee.get('name')} ({employee.get('email')})")
        else:
            print("No employees currently need alerts")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_preview_mode()
    test_regular_mode_warning()
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print("✅ Preview mode should show email previews but NOT send emails")
    print("⚠️  Regular mode would send actual emails (if email config is set up)")
    print("🔍 Check the logs above to verify no actual emails were sent")
