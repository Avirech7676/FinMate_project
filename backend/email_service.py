"""
Email notification utilities
"""
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SMTP_USER", "")
        self.sender_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SENDER_EMAIL", "noreply@finmate.app")

    async def send_notification_email(self, recipient: str, title: str, message: str) -> bool:
        """Send a simple notification email"""
        if not self.sender_email or not self.sender_password:
            print("Email not configured. Skipping email send.")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient
            msg['Subject'] = f"FinMate: {title}"
            
            body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 20px auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                  <h2 style="color: #333; margin-bottom: 20px;">{title}</h2>
                  <p style="color: #666; line-height: 1.6; margin-bottom: 20px;">{message}</p>
                  <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    This is an automated message from FinMate. Please don't reply to this email.
                  </p>
                </div>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            async with aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port) as smtp:
                await smtp.login(self.sender_email, self.sender_password)
                await smtp.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    async def send_weekly_digest_email(self, recipient: str, full_name: str, digest_data: dict) -> bool:
        """Send weekly financial summary email"""
        if not self.sender_email or not self.sender_password:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient
            msg['Subject'] = f"FinMate: Your Weekly Financial Summary"
            
            highlights_html = "".join([
                f"<li style='margin-bottom: 8px;'>{highlight}</li>"
                for highlight in digest_data.get("highlights", [])
            ])
            
            body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <div style="max-width: 600px; margin: 20px auto;">
                  <div style="background-color: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                    <h1 style="color: #333; margin-bottom: 10px;">Weekly Summary</h1>
                    <p style="color: #666; font-size: 16px; margin-bottom: 30px;">{digest_data.get("summary", "")}</p>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                      <h3 style="color: #333; margin-top: 0;">Highlights</h3>
                      <ul style="color: #666; list-style-position: inside;">
                        {highlights_html}
                      </ul>
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                      <p style="margin: 0; font-size: 14px;">Total Spent This Week</p>
                      <h2 style="margin: 10px 0 0 0; font-size: 32px;">${digest_data.get("total_spent", 0):.2f}</h2>
                    </div>
                    
                    <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                      Keep tracking your finances with FinMate. <a href="http://localhost:5173/dashboard" style="color: #667eea; text-decoration: none;">View Dashboard</a>
                    </p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            async with aiosmtplib.SMTP(hostname=self.smtp_server, port=self.smtp_port) as smtp:
                await smtp.login(self.sender_email, self.sender_password)
                await smtp.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send weekly digest: {e}")
            return False

    def generate_email_template(self, template_type: str, **kwargs) -> dict:
        """Generate email templates for AI-suggested actions"""
        templates = {
            "subscription_cancellation": {
                "subject": f"Subscription Cancellation Request - {kwargs.get('service', 'Service')}",
                "body": f"""
Hi,

I would like to cancel my subscription to {kwargs.get('service', 'your service')} effective immediately.

Details:
- Current Plan: {kwargs.get('plan', 'Unknown')}
- Reason: {kwargs.get('reason', 'Personal reasons')}

Please confirm cancellation and provide any necessary next steps.

Thank you,
{kwargs.get('user_name', 'User')}
                """
            },
            "billing_dispute": {
                "subject": f"Billing Inquiry - Charge on {kwargs.get('date', 'Account')}",
                "body": f"""
Hi,

I noticed a charge of ${kwargs.get('amount', '0')} on my account dated {kwargs.get('date', '')}.

I would like to:
1. Understand what this charge is for
2. Request a refund if this was made in error

Service/Merchant: {kwargs.get('merchant', 'Unknown')}
Amount: ${kwargs.get('amount', '0')}

Please respond at your earliest convenience.

Thank you,
{kwargs.get('user_name', 'User')}
                """
            },
            "bill_negotiation": {
                "subject": f"Request for Better Rates - {kwargs.get('provider', 'Provider')}",
                "body": f"""
Hi {kwargs.get('provider_name', 'Sir/Madam')},

I have been a loyal customer of {kwargs.get('provider', 'your service')} for {kwargs.get('duration', 'some time')}.

I would like to discuss:
1. Current promotional rates
2. Loyalty discounts
3. Bundle options that might reduce my bill

Current Monthly Cost: ${kwargs.get('current_cost', '0')}

I'm interested in optimizing my service while maintaining the quality I value.

Thank you,
{kwargs.get('user_name', 'User')}
                """
            }
        }
        
        template = templates.get(template_type, {})
        return {
            "subject": template.get("subject", ""),
            "body": template.get("body", "")
        }


# Singleton instance
email_service = EmailService()
