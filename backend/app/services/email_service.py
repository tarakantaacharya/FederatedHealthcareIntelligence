"""
Email notification service (Phase 31)
Sends email alerts for critical events
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_email(
        to_emails: List[str],
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send email notification via SMTP
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text fallback (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        # Check if email is configured
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            logger.warning("Email not configured. Skipping email send.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Attach plain text version
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)
            
            # Attach HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)
            
            # Connect to SMTP server
            if settings.SMTP_USE_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            
            # Login if credentials provided
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # Send email
            server.sendmail(settings.SMTP_FROM_EMAIL, to_emails, msg.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_capacity_alert_email(
        hospital_name: str,
        hospital_email: str,
        utilization: float,
        severity: str
    ) -> bool:
        """Send capacity alert email"""
        subject = f"[{severity.upper()}] Hospital Capacity Alert - {hospital_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: {'#dc2626' if severity == 'CRITICAL' else '#f59e0b'};">
                    ⚠️ Hospital Capacity Alert
                </h2>
                <p><strong>Hospital:</strong> {hospital_name}</p>
                <p><strong>Current Utilization:</strong> {utilization:.1f}%</p>
                <p><strong>Severity:</strong> <span style="color: {'#dc2626' if severity == 'CRITICAL' else '#f59e0b'};">{severity}</span></p>
                
                <div style="background: #fef3c7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <strong>Action Required:</strong>
                    <ul>
                        <li>Review current bed occupancy</li>
                        <li>Consider patient discharge planning</li>
                        <li>Prepare overflow protocols</li>
                    </ul>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This is an automated alert from Federated Healthcare Intelligence Platform.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        HOSPITAL CAPACITY ALERT
        
        Hospital: {hospital_name}
        Current Utilization: {utilization:.1f}%
        Severity: {severity}
        
        Action Required:
        - Review current bed occupancy
        - Consider patient discharge planning
        - Prepare overflow protocols
        
        ---
        Federated Healthcare Intelligence Platform
        """
        
        return EmailService.send_email([hospital_email], subject, html_body, text_body)
    
    @staticmethod
    def send_forecast_degradation_email(
        hospital_name: str,
        hospital_email: str,
        accuracy_drop: float
    ) -> bool:
        """Send forecast degradation alert email"""
        subject = f"[WARNING] Model Performance Degradation - {hospital_name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #f59e0b;">📉 Model Performance Degradation Detected</h2>
                <p><strong>Hospital:</strong> {hospital_name}</p>
                <p><strong>Accuracy Drop:</strong> {accuracy_drop:.1f}%</p>
                
                <div style="background: #fef3c7; padding: 15px; border-radius: 4px; margin: 20px 0;">
                    <strong>Recommended Actions:</strong>
                    <ul>
                        <li>Retrain local model with recent data</li>
                        <li>Check for data quality issues</li>
                        <li>Participate in next federated round</li>
                    </ul>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This is an automated alert from Federated Healthcare Intelligence Platform.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        MODEL PERFORMANCE DEGRADATION DETECTED
        
        Hospital: {hospital_name}
        Accuracy Drop: {accuracy_drop:.1f}%
        
        Recommended Actions:
        - Retrain local model with recent data
        - Check for data quality issues
        - Participate in next federated round
        
        ---
        Federated Healthcare Intelligence Platform
        """
        
        return EmailService.send_email([hospital_email], subject, html_body, text_body)
    
    @staticmethod
    def send_model_approval_email(
        admin_email: str,
        round_number: int,
        accuracy: float,
        num_participants: int
    ) -> bool:
        """Send model approval notification to admin"""
        subject = f"Model Approval Required - Round {round_number}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #2563eb;">🔔 Model Approval Required</h2>
                <p><strong>Training Round:</strong> {round_number}</p>
                <p><strong>Global Model Accuracy:</strong> {accuracy:.2%}</p>
                <p><strong>Participating Hospitals:</strong> {num_participants}</p>
                
                <div style="margin: 20px 0;">
                    <a href="http://localhost:3000/governance" 
                       style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                        Review & Approve Model
                    </a>
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    This is an automated notification from Federated Healthcare Intelligence Platform.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        MODEL APPROVAL REQUIRED
        
        Training Round: {round_number}
        Global Model Accuracy: {accuracy:.2%}
        Participating Hospitals: {num_participants}
        
        Please review and approve the model at:
        http://localhost:3000/governance
        
        ---
        Federated Healthcare Intelligence Platform
        """
        
        return EmailService.send_email([admin_email], subject, html_body, text_body)
