import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import logging
from typing import List, Dict
from config.settings import Config
from datetime import datetime
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = Config.SMTP_HOST
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.from_email = Config.FROM_EMAIL
        
        # Get CC emails and always include teamhr@rapidinnovation.dev
        self.cc_emails = Config.ALERT_CC_EMAILS if Config.ALERT_CC_EMAILS != [''] else []
        
        # Always add teamhr@rapidinnovation.dev to CC list
        if Config.CONSTANT_CC_EMAIL not in self.cc_emails:
            self.cc_emails.append(Config.CONSTANT_CC_EMAIL)
        
        # Email sending statistics
        self.emails_sent = 0
        self.emails_failed = 0
        
        # Load email template
        self.email_template = self._load_email_template()
    
    def _load_email_template(self) -> str:
        """
        Load the email template from your existing low_hours_email.html file
        """
        try:
            # Look for the template in common locations
            template_paths = [
                'templates/low_hours_email.html',
                'low_hours_email.html',
                'src/templates/low_hours_email.html',
                Path(__file__).parent.parent / 'templates' / 'low_hours_email.html',
                Path(__file__).parent.parent / 'low_hours_email.html'
            ]
            
            for template_path in template_paths:
                if os.path.exists(template_path):
                    with open(template_path, 'r', encoding='utf-8') as f:
                        logger.info(f"Loaded email template from: {template_path}")
                        return f.read()
            
            # If template file not found, use a simple fallback
            logger.warning("Email template file not found. Using fallback template.")
            return self._get_fallback_template()
            
        except Exception as e:
            logger.error(f"Error loading email template: {str(e)}")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """
        Simple fallback template matching the requested format
        """
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <p>Hi <strong>{{ employee_name }}</strong>,</p>
            
                <p>I hope you are doing well.</p>
            
                <p>This email is a reminder that, as per company policy, it is mandatory to complete 40 working hours per week. 
                {% if leave_days > 0 %}We have considered your {{ leave_days }}-day leave. {% endif %}
                Currently, you have accrued <strong>{{ total_hours }} hours</strong>. This policy is in place to ensure that we maintain a high level of productivity and meet our company goals and deliverables.</p>
            
                <p>It has come to our attention that you did not meet the required working hours from <strong>{{ week_start }}</strong> to <strong>{{ week_end }}</strong>. Please help us understand why you did not complete the expected working hours. We understand that you might have some personal circumstances affecting your working hours. Feel free to discuss them with us. Please provide us with the reason by EOD today, <strong>{{ current_date_formatted }}</strong>, so we can discuss the same further.</p>
            
                <p>Regards,</p>
            </div>
        </body>
        </html>
        """
    
    def send_low_hours_alert(self, real_employee_data: Dict) -> bool:
        """
        Send email alert for low work hours using REAL employee data
        Uses your existing low_hours_email.html template
        """
        try:
            # Validate real employee data
            if not self._validate_real_employee_data(real_employee_data):
                logger.warning(f"Invalid employee data for {real_employee_data.get('email', 'unknown')}")
                return False
        
            # Check if email credentials are properly configured
            if not self._is_email_configured():
                logger.warning(f"Email not sent to {real_employee_data['email']} - Email credentials not configured")
                self._print_real_email_preview(real_employee_data)
                return False
        
            # Calculate shortfall in minutes (1 hour = 60 minutes)
            shortfall_hours = real_employee_data.get('shortfall', 0)
            shortfall_minutes = int(shortfall_hours * 60)
        
            # Skip if shortfall is less than 10 minutes
            if shortfall_minutes < 10:
                logger.info(f"Skipping alert for {real_employee_data['name']} - negligible shortfall: {shortfall_minutes} minutes")
                return True
        
            # Create email content using your template
            subject = self._create_real_email_subject(real_employee_data)
            html_body = self._create_email_body_from_template(real_employee_data)
        
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = real_employee_data['email']
        
            # Get manager email for CC
            from src.manager_mapping import get_manager_email
            cc_emails = list(self.cc_emails)  # Start with general CC emails (includes teamhr)
        
            manager_email = get_manager_email(real_employee_data['name'])
            if manager_email and manager_email not in cc_emails:
                cc_emails.append(manager_email)
                logger.info(f"Adding manager {manager_email} to CC for {real_employee_data['name']}")
            
            # Ensure teamhr@rapidinnovation.dev is always in CC
            if Config.CONSTANT_CC_EMAIL not in cc_emails:
                cc_emails.append(Config.CONSTANT_CC_EMAIL)
            
            logger.info(f"CC list for {real_employee_data['name']}: {', '.join(cc_emails)}")
        
            # Add CC emails if configured
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
        
            # Attach HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
            # Send email with retry logic
            recipients = [real_employee_data['email']] + cc_emails
            success = self._send_email_with_retry(msg, real_employee_data, recipients)
        
            if success:
                self.emails_sent += 1
                logger.info(f"Low hours alert sent to {real_employee_data['name']} ({real_employee_data['email']})")
                if manager_email:
                    logger.info(f"  CC'd to manager: {manager_email}")
                logger.info(f"  CC'd to teamhr: {Config.CONSTANT_CC_EMAIL}")
            else:
                self.emails_failed += 1
            
            return success
        
        except Exception as e:
            self.emails_failed += 1
            logger.error(f"Error sending email to {real_employee_data.get('email', 'unknown')}: {str(e)}")
            self._print_real_email_preview(real_employee_data)
            return False
    
    def _validate_real_employee_data(self, data: Dict) -> bool:
        """
        Validate that real employee data contains all required fields
        """
        required_fields = ['email', 'name', 'week_start', 'week_end', 'total_hours', 'required_hours', 'shortfall']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
            
        # Validate email format
        email = data['email']
        if '@' not in email or '.' not in email:
            logger.error(f"Invalid email format: {email}")
            return False
            
        return True
    
    def _is_email_configured(self) -> bool:
        """
        Check if email configuration is properly set up
        """
        return (self.smtp_username and 
                self.smtp_password and 
                self.smtp_host and 
                self.from_email and
                self.smtp_username != 'your_email@gmail.com' and 
                self.smtp_password != 'your_app_password')
    
    def _create_real_email_subject(self, real_employee_data: Dict) -> str:
        """
        Create email subject for work hours reminder
        """
        week_start = real_employee_data.get('week_start')
        return f"Work Hours Reminder - Week of {week_start}"
    
    def _send_email_with_retry(self, msg: MIMEMultipart, real_employee_data: Dict, recipients: list, max_retries: int = 2) -> bool:
        """
        Send email with retry logic and timeout handling
        """
        for attempt in range(max_retries + 1):
            try:
                # Test connectivity first
                if not self._test_smtp_connectivity():
                    logger.warning(f"SMTP connectivity issue on attempt {attempt + 1}")
                    if attempt == max_retries:
                        return False
                    continue
            
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg, from_addr=self.from_email, to_addrs=recipients)
            
                return True
            
            except socket.gaierror as e:
                logger.error(f"DNS resolution failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    return False
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Email authentication failed: {str(e)}")
                return False  # Don't retry auth failures
            
            except (smtplib.SMTPConnectError, socket.timeout) as e:
                logger.warning(f"Connection issue on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    import time
                    time.sleep(5)  # Wait before retry
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    return False
    
        return False
    
    def _create_email_body_from_template(self, real_employee_data: Dict) -> str:
        """
        Create HTML email body using your existing low_hours_email.html template
        """
        try:
            # Calculate shortfall in minutes correctly (60 minutes = 1 hour)
            shortfall_hours = real_employee_data.get('shortfall', 0)
            shortfall_minutes = int(shortfall_hours * 60)
        
            # Format current date for the email
            current_date = datetime.now()
            current_date_formatted = current_date.strftime('%B %d, %Y')  # e.g., "December 09, 2024"
        
            # Prepare template variables
            template_vars = {
                'employee_name': real_employee_data['name'],
                'week_start': real_employee_data['week_start'],
                'week_end': real_employee_data['week_end'],
                'total_hours': real_employee_data['total_hours'],  # Now represents active hours
                'original_total_hours': real_employee_data.get('original_total_hours', real_employee_data['total_hours']),
                'idle_hours': real_employee_data.get('idle_hours', 0),
                'required_hours': real_employee_data['required_hours'],
                'shortfall': round(shortfall_hours, 2),
                'shortfall_minutes': shortfall_minutes,
                'days_worked': real_employee_data.get('days_worked', 0),
                'leave_days': real_employee_data.get('leave_days', 0),
                'current_date': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                'current_date_formatted': current_date_formatted,
                # Add AI message if available
                'ai_personalized_message': real_employee_data.get('ai_personalized_message', '')
            }
        
            # Render template
            template = Template(self.email_template)
            rendered_html = template.render(**template_vars)
        
            return rendered_html
        
        except Exception as e:
            logger.error(f"Error rendering email template: {str(e)}")
            # Use fallback template
            fallback_template = Template(self._get_fallback_template())
            return fallback_template.render(**template_vars)
    
    def _test_smtp_connectivity(self) -> bool:
        """
        Quick test of SMTP connectivity
        """
        try:
            socket.gethostbyname(self.smtp_host)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.smtp_host, self.smtp_port))
            sock.close()
            
            return result == 0
        except Exception:
            return False
    
    def _print_real_email_preview(self, real_employee_data: Dict):
        """
        Print email preview when actual sending fails
        """
        shortfall_hours = real_employee_data.get('shortfall', 0)
        shortfall_minutes = int(shortfall_hours * 60)
        
        # Get manager email for display
        from src.manager_mapping import get_manager_email
        manager_email = get_manager_email(real_employee_data['name'])
        
        # Build CC list for display
        cc_list = list(self.cc_emails)
        if manager_email and manager_email not in cc_list:
            cc_list.append(manager_email)
        
        print("\n" + "="*70)
        print("EMAIL PREVIEW (Not sent due to configuration/network issues)")
        print("="*70)
        print(f"To: {real_employee_data['email']}")
        print(f"CC: {', '.join(cc_list)}")
        print(f"Subject: {self._create_real_email_subject(real_employee_data)}")
        print(f"Employee: {real_employee_data['name']}")
        print(f"Hours: {real_employee_data['total_hours']}/{real_employee_data['required_hours']}")
        print(f"Shortfall: {shortfall_hours:.2f} hours ({shortfall_minutes} minutes)")
        print(f"Period: {real_employee_data['week_start']} to {real_employee_data['week_end']}")
        if real_employee_data.get('leave_days', 0) > 0:
            print(f"Leave days: {real_employee_data['leave_days']}")
        print("="*70 + "\n")
    
    def get_email_statistics(self) -> Dict:
        """
        Get email sending statistics
        """
        total_attempts = self.emails_sent + self.emails_failed
        success_rate = (self.emails_sent / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            'emails_sent': self.emails_sent,
            'emails_failed': self.emails_failed,
            'total_attempts': total_attempts,
            'success_rate': round(success_rate, 2)
        }
    
    def test_email_configuration(self) -> bool:
        """
        Test email configuration and connectivity
        """
        logger.info("Testing email configuration...")
        
        # Check configuration
        if not self._is_email_configured():
            logger.error("Email configuration is incomplete")
            return False
        
        # Test SMTP connectivity
        if not self._test_smtp_connectivity():
            logger.error("Cannot connect to SMTP server")
            return False
        
        # Test authentication
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                logger.info("Email configuration test successful!")
                logger.info(f"Emails will be CC'd to: {', '.join(self.cc_emails)}")
                return True
        except Exception as e:
            logger.error(f"Email configuration test failed: {str(e)}")
            return False
    
    def send_test_email(self, test_recipient: str = None) -> bool:
        """
        Send a test email to verify configuration
        """
        try:
            if not test_recipient:
                test_recipient = self.from_email
            
            # Create test message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Test Email - Employee Hours Monitoring System"
            msg['From'] = self.from_email
            msg['To'] = test_recipient
            
            # Include standard CC recipients
            cc_emails = list(self.cc_emails)
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Test email body
            html_body = """
            <html>
            <body>
                <h2>Test Email - Employee Hours Monitoring System</h2>
                <p>This is a test email to verify the email configuration.</p>
                <p><strong>Configuration Details:</strong></p>
                <ul>
                    <li>SMTP Host: {smtp_host}</li>
                    <li>From Email: {from_email}</li>
                    <li>CC Recipients: {cc_list}</li>
                    <li>System Status: Active</li>
                </ul>
                <p>If you received this email, the configuration is working correctly.</p>
            </body>
            </html>
            """.format(
                smtp_host=self.smtp_host,
                from_email=self.from_email,
                cc_list=', '.join(cc_emails) if cc_emails else 'None'
            )
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            recipients = [test_recipient] + cc_emails
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg, from_addr=self.from_email, to_addrs=recipients)
            
            logger.info(f"Test email sent successfully to {test_recipient}")
            if cc_emails:
                logger.info(f"CC'd to: {', '.join(cc_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test email: {str(e)}")
            return False