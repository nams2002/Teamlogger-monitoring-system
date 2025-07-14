#!/usr/bin/env python3
"""
Check Manager Emails - Display all manager email IDs from the system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.manager_mapping import MANAGER_EMAILS, refresh_manager_mapping, get_manager_email
import logging

# Set up logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

def show_manager_emails():
    """Display all manager email IDs currently configured"""
    print("📧 MANAGER EMAIL MAPPING")
    print("="*60)
    print("All manager email addresses currently configured in the system")
    print("="*60)
    
    try:
        # Show static email mapping from code
        print("📋 STATIC EMAIL MAPPING (from code):")
        print("-" * 40)
        
        if MANAGER_EMAILS:
            for i, (manager_name, email) in enumerate(MANAGER_EMAILS.items(), 1):
                print(f"{i:2d}. {manager_name:<25} -> {email}")
        else:
            print("   ❌ No static email mappings found")
        
        print(f"\n📊 Total Static Email Mappings: {len(MANAGER_EMAILS)}")
        
        # Get dynamic manager mapping from Google Sheets
        print(f"\n🔄 DYNAMIC MANAGER MAPPING (from Google Sheets):")
        print("-" * 50)
        
        mapping = refresh_manager_mapping()
        if mapping:
            print(f"   ✅ Loaded {len(mapping)} employee-manager mappings from Google Sheets")
            
            # Get unique managers from the mapping
            unique_managers = set(mapping.values())
            print(f"   📊 Unique managers found: {len(unique_managers)}")
            
            # Check which managers have email addresses
            managers_with_emails = []
            managers_without_emails = []
            
            for manager in sorted(unique_managers):
                if manager in MANAGER_EMAILS:
                    managers_with_emails.append((manager, MANAGER_EMAILS[manager]))
                else:
                    managers_without_emails.append(manager)
            
            print(f"\n✅ MANAGERS WITH EMAIL ADDRESSES ({len(managers_with_emails)}):")
            print("-" * 45)
            for i, (manager, email) in enumerate(managers_with_emails, 1):
                print(f"{i:2d}. {manager:<25} -> {email}")
            
            if managers_without_emails:
                print(f"\n❌ MANAGERS WITHOUT EMAIL ADDRESSES ({len(managers_without_emails)}):")
                print("-" * 50)
                for i, manager in enumerate(managers_without_emails, 1):
                    print(f"{i:2d}. {manager}")
                print("   ⚠️  These managers won't receive CC emails!")
            
            # Show email domain breakdown
            print(f"\n📊 EMAIL DOMAIN BREAKDOWN:")
            print("-" * 30)
            domain_count = {}
            for _, email in managers_with_emails:
                domain = email.split('@')[1] if '@' in email else 'unknown'
                domain_count[domain] = domain_count.get(domain, 0) + 1
            
            for domain, count in sorted(domain_count.items()):
                print(f"   {domain:<30} : {count} emails")
            
        else:
            print("   ❌ Could not load manager mapping from Google Sheets")
        
        # Test a few employee-manager email lookups
        print(f"\n🔍 SAMPLE EMPLOYEE-MANAGER EMAIL LOOKUPS:")
        print("-" * 45)
        
        sample_employees = list(mapping.keys())[:5] if mapping else []
        for employee in sample_employees:
            manager_email = get_manager_email(employee, force_refresh=True)
            manager_name = mapping.get(employee, 'Unknown')
            if manager_email:
                print(f"   {employee:<20} -> {manager_name:<20} -> {manager_email}")
            else:
                print(f"   {employee:<20} -> {manager_name:<20} -> ❌ No email")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print("="*30)
        print(f"   📧 Total manager emails configured: {len(MANAGER_EMAILS)}")
        print(f"   👥 Total managers in Google Sheets: {len(unique_managers) if mapping else 0}")
        print(f"   ✅ Managers with emails: {len(managers_with_emails) if mapping else 0}")
        print(f"   ❌ Managers without emails: {len(managers_without_emails) if mapping else 0}")
        
        if mapping:
            coverage = (len(managers_with_emails) / len(unique_managers) * 100) if unique_managers else 0
            print(f"   📈 Email coverage: {coverage:.1f}%")
        
        return {
            'static_emails': len(MANAGER_EMAILS),
            'total_managers': len(unique_managers) if mapping else 0,
            'managers_with_emails': len(managers_with_emails) if mapping else 0,
            'managers_without_emails': len(managers_without_emails) if mapping else 0
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    result = show_manager_emails()
    print("\n" + "="*60)
