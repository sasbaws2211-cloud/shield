"""Email service for sending notifications."""
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.models import EmailNotification, User
from datetime import datetime, timezone
import logging
import requests
import json

logger = logging.getLogger(__name__)

# Elastic Mail API configuration
ELASTICMAIL_API_URL = "https://api.elasticmail.com/v4/emails/send"


class EmailService:
    """Email service using Elastic Mail."""

    @staticmethod
    def _send_email(
        to_email: str,
        to_name: str,
        subject: str,
        body_text: str,
        body_html: str = None
    ) -> bool:
        """Send email via Elastic Mail API."""
        if not settings.elasticmail_api_key:
            logger.warning("Elastic Mail API key not configured. Email not sent.")
            return False

        try:
            headers = {
                "X-ElasticEmail-ApiKey": settings.elasticmail_api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "Recipients": {
                    "To": [
                        {
                            "Email": to_email,
                            "Name": to_name
                        }
                    ]
                },
                "Content": {
                    "From": settings.elasticmail_from_email,
                    "FromName": settings.elasticmail_from_name,
                    "Subject": subject,
                    "Body": [
                        {
                            "ContentType": "PlainText",
                            "Charset": "utf-8",
                            "Content": body_text
                        }
                    ]
                }
            }

            # Add HTML body if provided
            if body_html:
                payload["Content"]["Body"].append({
                    "ContentType": "HTML",
                    "Charset": "utf-8",
                    "Content": body_html
                })

            response = requests.post(
                ELASTICMAIL_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Elastic Mail API error: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email via Elastic Mail: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False

    @staticmethod
    def send_officer_approved_email(officer_email: str, officer_name: str) -> bool:
        """Send officer approved email."""
        subject = "Registration Approved - SwiftShield"
        body_text = f"""Dear {officer_name},

Great news! Your officer registration has been approved.

Your SIA badge has been verified and your account is now active. You can start applying for security jobs immediately.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Registration Approved!</h2>
<p>Dear {officer_name},</p>
<p>Great news! Your officer registration has been approved.</p>
<p>Your SIA badge has been verified and your account is now active. You can start applying for security jobs immediately.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            officer_email,
            officer_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_officer_rejected_email(
        officer_email: str,
        officer_name: str,
        reject_reason: str
    ) -> bool:
        """Send officer rejected email."""
        subject = "Registration Status - SwiftShield"
        body_text = f"""Dear {officer_name},

Unfortunately, your officer registration has been rejected.

Reason: {reject_reason}

If you believe this is an error or would like to appeal, please contact our support team.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Registration Status Update</h2>
<p>Dear {officer_name},</p>
<p>Unfortunately, your officer registration has been rejected.</p>
<p><strong>Reason:</strong> {reject_reason}</p>
<p>If you believe this is an error or would like to appeal, please contact our support team.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            officer_email,
            officer_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_job_accepted_email(
        business_email: str,
        company_name: str,
        job_title: str,
        start_time: str,
        end_time: str,
        guards_required: int,
        budget_gbp: float,
        payment_url: str = None
    ) -> bool:
        """Send job accepted email with payment link."""
        subject = f"Job Posting Approved - {job_title}"
        payment_section = f"""
Payment Link: {payment_url}
""" if payment_url else ""

        body_text = f"""Dear {company_name},

Your job posting has been approved and is now live!

Job Details:
- Title: {job_title}
- Start Time: {start_time}
- End Time: {end_time}
- Guards Required: {guards_required}
- Budget: £{budget_gbp}
{payment_section}
Officers can now apply for this position. You will receive notifications as applications come in.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Job Posting Approved!</h2>
<p>Dear {company_name},</p>
<p>Your job posting has been approved and is now live!</p>
<h3>Job Details:</h3>
<ul>
<li><strong>Title:</strong> {job_title}</li>
<li><strong>Start Time:</strong> {start_time}</li>
<li><strong>End Time:</strong> {end_time}</li>
<li><strong>Guards Required:</strong> {guards_required}</li>
<li><strong>Budget:</strong> £{budget_gbp}</li>
</ul>
{'<p><a href="' + payment_url + '">Complete Payment</a></p>' if payment_url else ''}
<p>Officers can now apply for this position. You will receive notifications as applications come in.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            business_email,
            company_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_job_rejected_email(
        business_email: str,
        company_name: str,
        job_title: str,
        reject_reason: str
    ) -> bool:
        """Send job rejected email."""
        subject = f"Job Posting Review - {job_title}"
        body_text = f"""Dear {company_name},

Your job posting has been reviewed.

Job: {job_title}
Status: Not Approved

Reason: {reject_reason}

Please review the feedback and resubmit if you have an updated job posting.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Job Posting Review</h2>
<p>Dear {company_name},</p>
<p>Your job posting has been reviewed.</p>
<p><strong>Job:</strong> {job_title}<br>
<strong>Status:</strong> Not Approved</p>
<p><strong>Reason:</strong> {reject_reason}</p>
<p>Please review the feedback and resubmit if you have an updated job posting.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            business_email,
            company_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_admin_notification_email(
        admin_email: str,
        subject: str,
        message: str
    ) -> bool:
        """Send admin notification email."""
        body_text = f"""[Admin Notification]

{message}

---
SwiftShield Admin System"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif; background-color: #f5f5f5;">
<div style="background-color: #fff; padding: 20px; border-radius: 8px;">
<h2>[Admin Notification]</h2>
<p>{message.replace(chr(10), '<br>')}</p>
<hr>
<p style="color: #666; font-size: 12px;">SwiftShield Admin System</p>
</div>
</body>
</html>"""

        return EmailService._send_email(
            admin_email,
            "Admin",
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_payment_reminder_email(
        business_email: str,
        company_name: str,
        invoice_number: str,
        amount_gbp: float,
        payment_method: str,
        due_date: str
    ) -> bool:
        """Send payment reminder email to business."""
        subject = f"Payment Reminder - Invoice {invoice_number}"
        body_text = f"""Dear {company_name},

This is a payment reminder for invoice {invoice_number}.

Invoice Details:
- Invoice Number: {invoice_number}
- Amount Due: £{amount_gbp}
- Payment Method: {payment_method}
- Due Date: {due_date}

Please ensure payment is made by the due date to maintain your account in good standing.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Payment Reminder</h2>
<p>Dear {company_name},</p>
<p>This is a payment reminder for invoice {invoice_number}.</p>
<table style="border-collapse: collapse;">
<tr>
<td style="padding: 8px;"><strong>Invoice Number:</strong></td>
<td style="padding: 8px;">{invoice_number}</td>
</tr>
<tr style="background-color: #f9f9f9;">
<td style="padding: 8px;"><strong>Amount Due:</strong></td>
<td style="padding: 8px;">£{amount_gbp}</td>
</tr>
<tr>
<td style="padding: 8px;"><strong>Payment Method:</strong></td>
<td style="padding: 8px;">{payment_method}</td>
</tr>
<tr style="background-color: #f9f9f9;">
<td style="padding: 8px;"><strong>Due Date:</strong></td>
<td style="padding: 8px;">{due_date}</td>
</tr>
</table>
<p>Please ensure payment is made by the due date to maintain your account in good standing.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            business_email,
            company_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_shift_confirmation_email(
        officer_email: str,
        officer_name: str,
        job_title: str,
        site_name: str,
        start_time: str,
        end_time: str,
        hourly_rate: float
    ) -> bool:
        """Send shift confirmation email to officer."""
        subject = f"Shift Confirmed - {job_title}"
        body_text = f"""Dear {officer_name},

Your shift has been confirmed!

Shift Details:
- Job: {job_title}
- Site: {site_name}
- Start Time: {start_time}
- End Time: {end_time}
- Hourly Rate: £{hourly_rate}

Please ensure you arrive 15 minutes early. If you have any questions, contact us immediately.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Shift Confirmed!</h2>
<p>Dear {officer_name},</p>
<p>Your shift has been confirmed!</p>
<h3>Shift Details:</h3>
<table style="border-collapse: collapse;">
<tr>
<td style="padding: 8px;"><strong>Job:</strong></td>
<td style="padding: 8px;">{job_title}</td>
</tr>
<tr style="background-color: #f9f9f9;">
<td style="padding: 8px;"><strong>Site:</strong></td>
<td style="padding: 8px;">{site_name}</td>
</tr>
<tr>
<td style="padding: 8px;"><strong>Start Time:</strong></td>
<td style="padding: 8px;">{start_time}</td>
</tr>
<tr style="background-color: #f9f9f9;">
<td style="padding: 8px;"><strong>End Time:</strong></td>
<td style="padding: 8px;">{end_time}</td>
</tr>
<tr>
<td style="padding: 8px;"><strong>Hourly Rate:</strong></td>
<td style="padding: 8px;">£{hourly_rate}</td>
</tr>
</table>
<p>Please ensure you arrive 15 minutes early. If you have any questions, contact us immediately.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            officer_email,
            officer_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_payday_confirmation_email(
        officer_email: str,
        officer_name: str,
        payment_amount: float,
        payment_date: str,
        payment_method: str
    ) -> bool:
        """Send payday confirmation email to officer (day before pay day)."""
        subject = f"Payday Confirmation - Payment of £{payment_amount}"
        body_text = f"""Dear {officer_name},

This is a confirmation that you will be paid tomorrow!

Payment Details:
- Amount: £{payment_amount}
- Payment Date: {payment_date}
- Payment Method: {payment_method}

Your payment will be processed according to the schedule. Please ensure your payment details are current.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2>Payday Confirmation ✓</h2>
<p>Dear {officer_name},</p>
<p>This is a confirmation that you will be paid tomorrow!</p>
<h3>Payment Details:</h3>
<table style="border-collapse: collapse;">
<tr>
<td style="padding: 8px;"><strong>Amount:</strong></td>
<td style="padding: 8px; color: #28a745; font-size: 18px;"><strong>£{payment_amount}</strong></td>
</tr>
<tr style="background-color: #f9f9f9;">
<td style="padding: 8px;"><strong>Payment Date:</strong></td>
<td style="padding: 8px;">{payment_date}</td>
</tr>
<tr>
<td style="padding: 8px;"><strong>Payment Method:</strong></td>
<td style="padding: 8px;">{payment_method}</td>
</tr>
</table>
<p>Your payment will be processed according to the schedule. Please ensure your payment details are current.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            officer_email,
            officer_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    def send_shift_alert_email(
        officer_email: str,
        officer_name: str,
        job_title: str,
        site_name: str,
        start_time: str
    ) -> bool:
        """Send shift alert/reminder email to officer."""
        subject = f"Shift Alert - {job_title} starts soon!"
        body_text = f"""Dear {officer_name},

Reminder: Your shift starts soon!

Job: {job_title}
Site: {site_name}
Start Time: {start_time}

Please ensure you are on your way. If you cannot make it, contact us immediately.

Best regards,
SwiftShield Team"""

        body_html = f"""<html>
<body style="font-family: Arial, sans-serif;">
<h2 style="color: #ff9800;">⏰ Shift Alert</h2>
<p>Dear {officer_name},</p>
<p><strong>Reminder: Your shift starts soon!</strong></p>
<h3>Shift Details:</h3>
<table style="border-collapse: collapse;">
<tr>
<td style="padding: 8px;"><strong>Job:</strong></td>
<td style="padding: 8px;">{job_title}</td>
</tr>
<tr style="background-color: #f9f9f9;">
<td style="padding: 8px;"><strong>Site:</strong></td>
<td style="padding: 8px;">{site_name}</td>
</tr>
<tr>
<td style="padding: 8px;"><strong>Start Time:</strong></td>
<td style="padding: 8px; color: #d32f2f;"><strong>{start_time}</strong></td>
</tr>
</table>
<p>Please ensure you are on your way. If you cannot make it, contact us immediately.</p>
<p>Best regards,<br>SwiftShield Team</p>
</body>
</html>"""

        return EmailService._send_email(
            officer_email,
            officer_name,
            subject,
            body_text,
            body_html
        )

    @staticmethod
    async def queue_email_notification(
        db: AsyncSession,
        recipient_email: str,
        recipient_id: str,
        notification_type: str,
        subject: str,
        body: str,
        job_id: str = None,
        scheduled_for: datetime = None
    ) -> bool:
        """Queue an email notification for later processing."""
        try:
            notification = EmailNotification(
                recipient_email=recipient_email,
                recipient_id=recipient_id,
                notification_type=notification_type,
                subject=subject,
                body=body,
                job_id=job_id,
                scheduled_for=scheduled_for,
                status="pending"
            )
            db.add(notification)
            await db.commit()
            logger.info(f"Email notification queued for {recipient_email} - Type: {notification_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue email notification: {e}")
            return False

    @staticmethod
    async def get_pending_notifications(db: AsyncSession) -> list:
        """Get all pending email notifications."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(EmailNotification).where(
                and_(
                    EmailNotification.status == "pending",
                    (EmailNotification.scheduled_for.is_(None)) | (EmailNotification.scheduled_for <= now)
                )
            )
        )
        return result.scalars().all()

    @staticmethod
    async def mark_notification_sent(db: AsyncSession, notification_id: str) -> bool:
        """Mark a notification as sent."""
        try:
            result = await db.execute(
                select(EmailNotification).where(
                    EmailNotification.id == notification_id
                )
            )
            notification = result.scalars().first()
            if notification:
                notification.status = "sent"
                notification.sent_at = datetime.now(timezone.utc)
                await db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark notification as sent: {e}")
            return False

    @staticmethod
    async def mark_notification_failed(db: AsyncSession, notification_id: str, error_message: str) -> bool:
        """Mark a notification as failed."""
        try:
            result = await db.execute(
                select(EmailNotification).where(
                    EmailNotification.id == notification_id
                )
            )
            notification = result.scalars().first()
            if notification:
                notification.status = "failed"
                notification.error_message = error_message
                await db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to mark notification as failed: {e}")
            return False
