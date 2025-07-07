#!/usr/bin/env python3
"""
Employee Hours Monitoring System - AI-Enhanced 5-Day Work System
Monitors employee work hours from TeamLogger and sends alerts
for low hours, considering approved leaves from Google Sheets.

Automatically triggers every Monday at 8 AM to check previous work week (Monday-Sunday).
Sends alerts only to employees who haven't met their adjusted hour requirement.

AI-Enhanced 5-Day Work System Configuration:
- Work 5 days (Monday-Friday) with 8 hours per day
- 40 hours required per week
- 3-hour buffer (37+ hours acceptable)
- Weekend availability for hour completion
- Only working day leaves count for adjustment
- Full week leave (5 days) = no alert
- 🤖 AI-enhanced decision making for edge cases
- Scheduled execution: Monday 8 AM
- Excluded employees: Aishik Chatterjee, Tirtharaj Bhoumik, Vishal Kumar
"""

import sys
import schedule
import time
import argparse
import logging
import signal
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.workflow_manager import WorkflowManager
from src.utils import setup_logging, validate_config
from config.settings import Config

# Load .env into os.environ
load_dotenv()

logger = logging.getLogger(__name__)
shutdown_requested = False


def signal_handler(signum, frame):
    """Graceful shutdown on SIGINT/SIGTERM."""
    global shutdown_requested
    logger.info(f"Received signal {signum}. Shutting down...")
    shutdown_requested = True


def run_monitoring():
    """Run the AI-enhanced monitoring workflow once for 5-day work system (real data)."""
    try:
        workflow = WorkflowManager()

        if not workflow.should_send_alerts_today():
            today = datetime.now().strftime('%A')
            logger.info(f"Today is {today}. Skipping alerts (only Monday/Tuesday for AI-enhanced 5-day work system).")
            return {'skipped': True, 'reason': f'Not alert day ({today})'}

        # Check AI status
        ai_status = "✅ Enabled" if hasattr(workflow, 'openai_client') and workflow.openai_client else "❌ Disabled"
        
        if workflow.is_optimal_execution_time():
            logger.info(f"🕰️ Optimal execution time (Monday 8 AM) - Running AI-enhanced 5-day work system monitoring (AI: {ai_status})")
        else:
            now = datetime.now().strftime('%A %H:%M')
            logger.info(f"Current time: {now} - Running AI-enhanced 5-day work system monitoring (AI: {ai_status})")

        logger.info("📅 Checking previous work week (Monday-Sunday) for AI-enhanced 5-day work system")
        logger.info(f"🤖 AI Intelligence: {ai_status}")
        logger.info("✅ Corrected Formula: Required Hours = 8 × (5 - leave_days)")
        
        results = workflow.run_workflow()
        
        if results:
            logger.info(f"📊 AI-Enhanced Workflow Summary:")
            logger.info(f"  📧 Alerts sent: {results['alerts_sent']} out of {results['total_employees']} employees")
            logger.info(f"  ✅ Meeting requirements: {results['hours_met']} employees")
            logger.info(f"  🏖️ On full leave: {results['on_leave']} employees")
            logger.info(f"  ⚠️ Negligible shortfalls: {results.get('negligible_shortfalls', 0)} ignored")
            if 'ai_overrides' in results:
                logger.info(f"  🤖 AI intelligent overrides: {results['ai_overrides']} cases")
            logger.info(f"  ⏱️ Execution time: {results['execution_time']}")
        return results

    except Exception as e:
        logger.error(f"❌ Error in AI-enhanced monitoring: {e}")
        raise


def preview_alerts():
    """Preview who would get alerts for AI-enhanced 5-day work system, without sending emails."""
    try:
        logger.info("🔍 AI-ENHANCED PREVIEW MODE — no emails will be sent (5-day work system)")
        workflow = WorkflowManager()
        workflow.run_preview_mode()
        return True
    except Exception as e:
        logger.error(f"❌ Error in AI-enhanced preview mode: {e}")
        return False


def test_system_components():
    """Test TeamLogger API, Email service, and AI intelligence for 5-day work system setup."""
    try:
        logger.info("🧪 TESTING SYSTEM COMPONENTS (AI-Enhanced 5-Day Work System)")
        logger.info("=" * 60)

        # Display configuration
        logger.info("📋 Configuration Summary:")
        config_summary = Config.get_config_summary()
        logger.info(f"  System: {config_summary['work_schedule']['system_type']}")
        logger.info(f"  Work Days: {config_summary['work_schedule']['work_days_per_week']} days (Monday-Friday)")
        logger.info(f"  Required Hours: {config_summary['work_schedule']['minimum_hours_per_week']}h/week")
        logger.info(f"  Hours per Day: {config_summary['work_schedule']['hours_per_working_day']}h/day")  # ✅ Now shows 8
        logger.info(f"  Acceptable: {config_summary['work_schedule']['acceptable_hours_per_week']}h+ (with buffer)")
        logger.info(f"  Monitoring Period: {config_summary['work_schedule']['monitoring_period_days']} days (Mon-Sun)")
        logger.info(f"  Weekend Availability: Saturday-Sunday can work to complete hours")
        logger.info(f"  Execution: {config_summary['execution_schedule']['day']} at {config_summary['execution_schedule']['time']}")
        logger.info(f"  Excluded Employees: {', '.join(config_summary['excluded_employees'])}")

        # TeamLogger
        from src.teamlogger_client import TeamLoggerClient
        teamlogger = TeamLoggerClient()
        logger.info("\n🔗 Testing TeamLogger API...")
        status = teamlogger.get_api_status()
        if status['connected']:
            logger.info(f"✅ TeamLogger API connected ({status['employee_count']} employees)")
        else:
            logger.error("❌ TeamLogger API failed")

        # Google Sheets
        from src.googlesheets_Client import GoogleSheetsLeaveClient
        sheets_client = GoogleSheetsLeaveClient()
        logger.info("\n📊 Testing Google Sheets connection...")
        validation = sheets_client.validate_google_sheets_connection()
        if validation['status'] == 'success':
            logger.info(f"✅ Google Sheets connected ({validation.get('rows_found', 0)} rows)")
        else:
            logger.error(f"❌ Google Sheets failed: {validation['message']}")

        # Email service
        from src.email_service import EmailService
        email_svc = EmailService()
        logger.info("\n📧 Testing Email service...")
        if email_svc.test_email_configuration():
            logger.info("✅ Email service configured")
            logger.info(f"   CC recipients: {', '.join(email_svc.cc_emails)}")
        else:
            logger.error("❌ Email service configuration issues")

        # AI Intelligence Test
        logger.info("\n🤖 Testing AI Intelligence...")
        workflow = WorkflowManager()
        if hasattr(workflow, 'openai_client') and workflow.openai_client:
            try:
                # Test AI decision making
                test_decision = workflow._ai_enhanced_decision(
                    employee_name="Test Employee",
                    actual_hours=35.5,
                    required_hours=40.0,
                    acceptable_hours=37.0,
                    leave_days=0
                )
                
                if test_decision and test_decision.get('action') in ['send_alert', 'no_alert']:
                    logger.info("✅ AI Intelligence working correctly")
                    logger.info(f"   Test Decision: {test_decision.get('action')}")
                    logger.info(f"   AI Reason: {test_decision.get('reason')}")
                    logger.info(f"   Confidence: {test_decision.get('confidence')}")
                else:
                    logger.error("❌ AI Intelligence test failed - invalid response")
                    
            except Exception as e:
                logger.error(f"❌ AI Intelligence test failed: {str(e)}")
        else:
            logger.warning("⚠️ AI Intelligence disabled - OPENAI_API_KEY not configured")

        # Show leave calculation examples
        logger.info("\n📊 Leave Day Calculation Examples (AI-Enhanced 5-Day Work System):")
        logger.info("✅ Corrected Formula: Required Hours = 8 × (5 - leave_days)")
        for leave_days in range(6):
            required = Config.calculate_required_hours_for_leave_days(leave_days)
            acceptable = Config.calculate_acceptable_hours_for_leave_days(leave_days)
            if leave_days == 5:
                logger.info(f"   {leave_days} leave days: Full week leave - no alert sent")
            else:
                logger.info(f"   {leave_days} leave day(s): {required}h required, {acceptable}h+ acceptable")

        logger.info("=" * 60)
        logger.info("🎯 AI-ENHANCED COMPONENT TESTING COMPLETE")
        return True

    except Exception as e:
        logger.error(f"❌ Error testing AI-enhanced components: {e}")
        return False


def test_ai_intelligence():
    """Test AI intelligence capabilities specifically."""
    try:
        logger.info("🤖 TESTING AI INTELLIGENCE CAPABILITIES")
        logger.info("=" * 50)
        
        workflow = WorkflowManager()
        
        if not hasattr(workflow, 'openai_client') or not workflow.openai_client:
            logger.error("❌ AI Intelligence not configured - OPENAI_API_KEY missing")
            return False
        
        logger.info("🔑 OpenAI API Key: ✅ Configured")
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Standard Alert Case",
                "hours": 30.0,
                "required": 40.0,
                "acceptable": 37.0,
                "leave_days": 0
            },
            {
                "name": "Edge Case - Close to Threshold", 
                "hours": 36.5,
                "required": 40.0,
                "acceptable": 37.0,
                "leave_days": 0
            },
            {
                "name": "Reduced Hours with Leave",
                "hours": 20.0,
                "required": 24.0,
                "acceptable": 21.0,
                "leave_days": 2
            }
        ]
        
        for scenario in test_scenarios:
            logger.info(f"\n🧪 Testing Scenario: {scenario['name']}")
            logger.info(f"   Hours: {scenario['hours']}, Required: {scenario['required']}, Acceptable: {scenario['acceptable']}, Leave: {scenario['leave_days']}")
            
            decision = workflow._ai_enhanced_decision(
                employee_name=f"Test Employee - {scenario['name']}",
                actual_hours=scenario['hours'],
                required_hours=scenario['required'],
                acceptable_hours=scenario['acceptable'],
                leave_days=scenario['leave_days']
            )
            
            if decision:
                logger.info(f"   🤖 AI Decision: {decision.get('action')}")
                logger.info(f"   📊 Reason: {decision.get('reason')}")
                logger.info(f"   🎯 Confidence: {decision.get('confidence')}")
                if decision.get('explanation'):
                    logger.info(f"   💡 Explanation: {decision.get('explanation')}")
            else:
                logger.error(f"   ❌ AI decision failed for scenario: {scenario['name']}")
        
        logger.info("\n🎯 AI INTELLIGENCE TEST COMPLETE")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing AI intelligence: {e}")
        return False


def schedule_monitoring():
    """Set up scheduled runs for AI-enhanced 5-day work system monitoring."""
    logger.info("⏰ Scheduling tasks for AI-enhanced 5-day work system monitoring...")
    
    # Main schedule: Every Monday at 8 AM (optimal time)
    schedule.every().monday.at("08:00").do(run_monitoring).tag('main')
    
    # Backup schedule: Every Tuesday at 8 AM (in case Monday is holiday)
    schedule.every().tuesday.at("08:00").do(run_monitoring).tag('backup')
    
    # Preview schedule: Every Friday at 6 PM (end of week preview)
    schedule.every().friday.at("18:00").do(preview_alerts).tag('preview')
    
    # Optional: AI test schedule (commented out by default)
    # schedule.every().day.at("09:00").do(test_ai_intelligence).tag('ai_health')

    logger.info("📅 Scheduled Jobs:")
    for job in schedule.jobs:
        tags = ", ".join(job.tags) if job.tags else "no tags"
        logger.info(f"  • {job} ({tags})")
    
    # Show next run times
    now = datetime.now()
    logger.info(f"\n⏰ Next scheduled runs:")
    for job in schedule.jobs:
        next_run = schedule.next_run()
        if next_run:
            time_until = next_run - now
            logger.info(f"  • {job.job_func.__name__}: {next_run.strftime('%A %Y-%m-%d at %H:%M')} (in {time_until})")
    
    return schedule


def run_scheduler():
    """Start the scheduler loop for AI-enhanced 5-day work system monitoring."""
    global shutdown_requested
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    schedule_monitoring()
    logger.info("🚀 Scheduler started for AI-enhanced 5-day work system monitoring.")

    # Immediate check if today is Monday or Tuesday
    workflow = WorkflowManager()
    if workflow.should_send_alerts_today():
        ai_status = "✅ Enabled" if hasattr(workflow, 'openai_client') and workflow.openai_client else "❌ Disabled"
        logger.info(f"📅 Today is an alert day - Running initial AI-enhanced check (AI: {ai_status})...")
        run_monitoring()

    # Main scheduler loop
    check_count = 0
    while not shutdown_requested:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
        
        check_count += 1
        # Log status every hour
        if check_count % 60 == 0:
            next_run = schedule.next_run()
            if next_run:
                time_until = next_run - datetime.now()
                logger.info(f"⏰ AI-Enhanced Scheduler active - Next run: {next_run.strftime('%A %H:%M')} (in {time_until})")

    logger.info("🛑 Scheduler stopped.")


def show_system_status():
    """Print current config and scheduling info for AI-enhanced 5-day work system."""
    logger.info("📊 SYSTEM STATUS (AI-Enhanced 5-Day Work System)")
    logger.info("=" * 60)
    
    # Configuration
    config_summary = Config.get_config_summary()
    ai_status = Config.get_ai_status()
    
    logger.info(f"TeamLogger URL: {Config.TEAMLOGGER_API_URL}")
    logger.info(f"SMTP Host:      {Config.SMTP_HOST}")
    logger.info(f"From Email:     {Config.FROM_EMAIL}")
    logger.info(f"🤖 AI Enabled:  {ai_status['enabled']}")
    
    # Work schedule
    logger.info(f"\n📅 Work Schedule:")
    logger.info(f"  System Type:   {config_summary['work_schedule']['system_type']}")
    logger.info(f"  Work Days:     {config_summary['work_schedule']['work_days_per_week']} days (Monday-Friday)")
    logger.info(f"  Required:      {config_summary['work_schedule']['minimum_hours_per_week']}h/week")
    logger.info(f"  Per Day:       {config_summary['work_schedule']['hours_per_working_day']}h/day")  # ✅ Now shows 8
    logger.info(f"  Acceptable:    {config_summary['work_schedule']['acceptable_hours_per_week']}h+ (with {config_summary['work_schedule']['hours_buffer']}h buffer)")
    logger.info(f"  Weekends:      Saturday-Sunday (available for completion)")
    logger.info(f"  Monitoring:    {config_summary['work_schedule']['monitoring_period_days']} days (Mon-Sun)")

    # Current time and execution
    now = datetime.now()
    logger.info(f"\n⏰ Timing:")
    logger.info(f"  Current Time:  {now.strftime('%A, %Y-%m-%d %H:%M:%S')}")
    logger.info(f"  Execution:     {config_summary['execution_schedule']['day']} at {config_summary['execution_schedule']['time']} {config_summary['execution_schedule']['timezone']}")

    workflow = WorkflowManager()
    ai_workflow_status = "✅ Enabled" if hasattr(workflow, 'openai_client') and workflow.openai_client else "❌ Disabled"
    logger.info(f"  Should Send:   {workflow.should_send_alerts_today()}")
    logger.info(f"  Optimal Time:  {workflow.is_optimal_execution_time()}")
    logger.info(f"  🤖 AI Status:  {ai_workflow_status}")

    # Work week boundaries
    start, end = workflow.get_week_boundaries()
    logger.info(f"  Monitoring:    {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')} (Mon-Sun)")
    
    # AI Features
    logger.info(f"\n🤖 AI Intelligence:")
    if ai_status['enabled']:
        logger.info(f"  Decision Making:     ✅ Enabled")
        logger.info(f"  Smart Overrides:     ✅ Active") 
        logger.info(f"  Personalized Msgs:   ✅ Generated")
        logger.info(f"  Context Analysis:    ✅ Available")
    else:
        logger.info(f"  Status:              ❌ Disabled (OPENAI_API_KEY missing)")
        logger.info(f"  Fallback:            Standard rule-based system")
    
    # Excluded employees
    logger.info(f"\n👥 Excluded Employees:")
    for employee in config_summary['excluded_employees']:
        logger.info(f"  - {employee}")
    
    # Leave calculation examples
    logger.info(f"\n📊 Leave Calculations (✅ Corrected):")
    for leave_days in [0, 1, 2, 3, 5]:
        required = Config.calculate_required_hours_for_leave_days(leave_days)
        acceptable = Config.calculate_acceptable_hours_for_leave_days(leave_days)
        if leave_days == 5:
            logger.info(f"  {leave_days} days: Full week leave - no alert sent")
        else:
            logger.info(f"  {leave_days} day(s): {required}h required, {acceptable}h+ acceptable")
    
    logger.info("=" * 60)


def show_work_week_summary():
    """Show comprehensive work week monitoring summary with AI insights."""
    try:
        workflow = WorkflowManager()
        workflow.print_work_week_summary()
    except Exception as e:
        logger.error(f"❌ Error generating AI-enhanced work week summary: {e}")


def main():
    """CLI entrypoint for AI-enhanced 5-day work system monitoring."""
    parser = argparse.ArgumentParser(
        description='Employee Hours Monitoring System - AI-Enhanced 5-Day Work System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --run-once          # Run once (Monday/Tuesday only)
  python main.py --schedule          # Start scheduler (Monday 8 AM)
  python main.py --preview           # Preview alerts (no emails)
  python main.py --force             # Force run (ignore day check)
  python main.py --test              # Test all components
  python main.py --test-ai           # Test AI intelligence only
  python main.py --status            # Show system status
  python main.py --summary           # Show work week summary

AI-Enhanced 5-Day Work System Configuration:
  - Work 5 days (Monday-Friday) with 8 hours per day
  - 40 hours required per week, 37+ hours acceptable (3h buffer)
  - Weekend availability for hour completion
  - 🤖 AI-enhanced decision making for edge cases
  - Automatic Monday 8 AM execution
  - Only working day leaves count for adjustment
  - Full week leave (5 days) = no alert sent
  - Excluded: Aishik Chatterjee, Tirtharaj Bhoumik, Vishal Kumar
        """
    )
    
    parser.add_argument('--run-once', action='store_true', help='Run once (Monday/Tuesday only)')
    parser.add_argument('--schedule', action='store_true', help='Start scheduler (Monday 8 AM)')
    parser.add_argument('--preview', action='store_true', help='Preview alerts (no emails)')
    parser.add_argument('--force', action='store_true', help='Force run (ignore day check)')
    parser.add_argument('--test', action='store_true', help='Test all system components')
    parser.add_argument('--test-ai', action='store_true', help='Test AI intelligence only')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--summary', action='store_true', help='Show work week summary')
    parser.add_argument('--quiet', action='store_true', help='Only WARN/ERROR logs')
    parser.add_argument('--verbose', action='store_true', help='DEBUG logging')

    args = parser.parse_args()

    # Set log level
    if args.quiet:
        level = 'WARNING'
    elif args.verbose:
        level = 'DEBUG'
    else:
        level = Config.LOG_LEVEL
    setup_logging(level, Config.LOG_FILE)

    # Config validation
    if not validate_config(Config):
        logger.error("❌ Invalid configuration. Check your .env file.")
        sys.exit(1)

    # Display startup info
    ai_status = "✅ Enabled" if Config.ENABLE_OPENAI_ENHANCEMENT else "❌ Disabled"
    logger.info("🚀 EMPLOYEE HOURS MONITORING (AI-Enhanced 5-Day Work System)")
    logger.info(f"Started at: {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info(f"🤖 AI Intelligence: {ai_status}")
    logger.info(f"Work schedule: 40h across 5 days (Mon-Fri) with weekend availability")
    logger.info(f"✅ Corrected formula: Required = 8 × (5 - leave_days)")
    logger.info(f"Excluded employees: {', '.join(Config.EXCLUDED_EMPLOYEES)}")
    logger.info("=" * 60)

    try:
        if args.status:
            show_system_status()
        elif args.summary:
            show_work_week_summary()
        elif args.test:
            success = test_system_components()
            sys.exit(0 if success else 1)
        elif args.test_ai:
            success = test_ai_intelligence()
            sys.exit(0 if success else 1)
        elif args.preview:
            success = preview_alerts()
            sys.exit(0 if success else 1)
        elif args.force:
            logger.info("💪 FORCE MODE - Running AI-enhanced monitoring regardless of day")
            results = WorkflowManager().run_workflow()
            sys.exit(0 if results else 1)
        elif args.run_once:
            results = run_monitoring()
            sys.exit(0 if results and not results.get('skipped') else 1)
        elif args.schedule:
            logger.info("⏰ Starting scheduler for automated Monday 8 AM AI-enhanced execution...")
            run_scheduler()
        else:
            # Default: run once respecting day rules
            results = run_monitoring()
            sys.exit(0 if results and not results.get('skipped') else 1)

    except KeyboardInterrupt:
        logger.info("⏹️ Interrupted by user.")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        logger.info("👋 Shutdown complete.")


if __name__ == "__main__":
    main()