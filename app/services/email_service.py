"""
Email Service - Отправка email уведомлений
"""
from flask import render_template_string
from flask_mail import Message
from app import mail
from config import Config


class EmailService:
    """
    Сервис для отправки email уведомлений
    """
    
    @staticmethod
    def send_email(to, subject, body_html, body_text=None):
        """
        Базовый метод отправки email
        
        Args:
            to: str или list - получатели
            subject: str - тема
            body_html: str - HTML тело
            body_text: str - текстовое тело (fallback)
        """
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=body_html,
            body=body_text,
            sender=Config.MAIL_DEFAULT_SENDER
        )
        
        try:
            mail.send(msg)
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_booking_confirmation(booking):
        """
        Отправить подтверждение бронирования
        
        Args:
            booking: Booking object
        """
        slot = booking.timeslot
        doctor = slot.calendar.doctor
        practice = doctor.practice
        
        subject = f"✅ Termin bestätigt - {doctor.name}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Termin erfolgreich gebucht!</h2>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">📅 Termindetails</h3>
                <p><strong>Arzt:</strong> {doctor.name}<br>
                <strong>Fachrichtung:</strong> {doctor.display_speciality}<br>
                <strong>Datum:</strong> {slot.start_time.strftime('%A, %d.%m.%Y')}<br>
                <strong>Uhrzeit:</strong> {slot.start_time.strftime('%H:%M')} Uhr</p>
                
                <h3>🏥 Praxis</h3>
                <p><strong>{practice.name}</strong><br>
                {practice.full_address_string}<br>
                Tel: {practice.phone}</p>
                
                <h3>💳 Zahlung</h3>
                <p>Reservierungsgebühr: {float(booking.amount_paid):.2f}€ (bezahlt)</p>
            </div>
            
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>⚠️ Stornierungsbedingungen:</strong></p>
                <ul>
                    <li>Mehr als 24 Stunden: 100% Rückerstattung</li>
                    <li>1-24 Stunden: 50% Rückerstattung</li>
                    <li>Weniger als 1 Stunde: keine Rückerstattung</li>
                </ul>
                <p>Stornierung bis: {booking.cancellable_until.strftime('%d.%m.%Y um %H:%M')} Uhr</p>
            </div>
            
            <div style="margin: 30px 0;">
                <p><strong>Buchungscode:</strong> <code style="background: #e5e7eb; padding: 5px 10px; border-radius: 4px;">{booking.booking_code}</code></p>
                <p>Zum Stornieren: <a href="{Config.FRONTEND_URL}/booking/{booking.booking_code}">Termin stornieren</a></p>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">
                Sie erhalten 24 Stunden vor Ihrem Termin eine Erinnerung per E-Mail.
            </p>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="color: #9ca3af; font-size: 12px;">
                Mit freundlichen Grüßen,<br>
                Ihr TerminFinder Team
            </p>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=booking.patient.email,
            subject=subject,
            body_html=html_body
        )
    
    @staticmethod
    def send_reminder(booking):
        """
        Отправить напоминание за 24 часа
        
        Args:
            booking: Booking object
        """
        slot = booking.timeslot
        doctor = slot.calendar.doctor
        practice = doctor.practice
        
        subject = f"🔔 Erinnerung: Termin morgen um {slot.start_time.strftime('%H:%M')} Uhr"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Erinnerung an Ihren Termin morgen</h2>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>📅 {slot.start_time.strftime('%A, %d.%m.%Y')}</strong><br>
                <strong>⏰ {slot.start_time.strftime('%H:%M')} Uhr</strong></p>
                
                <p><strong>👨‍⚕️ {doctor.name}</strong><br>
                {doctor.display_speciality}</p>
                
                <p><strong>🏥 {practice.name}</strong><br>
                {practice.full_address_string}<br>
                Tel: {practice.phone}</p>
            </div>
            
            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <p><strong>⚠️ Bitte beachten:</strong></p>
                <p>Stornierung nur noch bis {booking.cancellable_until.strftime('%H:%M')} Uhr möglich.</p>
            </div>
            
            <p>Buchungscode: <code style="background: #e5e7eb; padding: 5px 10px; border-radius: 4px;">{booking.booking_code}</code></p>
            
            <div style="margin: 30px 0;">
                <a href="{Config.FRONTEND_URL}/booking/{booking.booking_code}" 
                   style="background: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Termin stornieren
                </a>
            </div>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="color: #9ca3af; font-size: 12px;">
                Wir freuen uns auf Ihren Besuch!<br>
                Ihr TerminFinder Team
            </p>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=booking.patient.email,
            subject=subject,
            body_html=html_body
        )
    
    @staticmethod
    def send_cancellation_confirmation(booking, refund_amount):
        """
        Подтверждение отмены бронирования
        
        Args:
            booking: Booking object
            refund_amount: Decimal - сумма возврата
        """
        subject = "✅ Termin storniert"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #dc2626;">Termin erfolgreich storniert</h2>
            
            <p>Ihr Termin wurde storniert.</p>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Buchungscode:</strong> {booking.booking_code}</p>
                <p><strong>Storniert am:</strong> {booking.cancelled_at.strftime('%d.%m.%Y um %H:%M')}</p>
            </div>
            
            <div style="background: #d1fae5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #059669;">💰 Rückerstattung</h3>
                <p><strong>Betrag:</strong> {float(refund_amount):.2f}€</p>
                <p>Die Rückerstattung wird in 5-10 Werktagen auf Ihrer Karte gutgeschrieben.</p>
            </div>
            
            <p>Möchten Sie einen neuen Termin buchen?</p>
            <a href="{Config.FRONTEND_URL}/search" 
               style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 20px 0;">
                Neuen Termin suchen
            </a>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="color: #9ca3af; font-size: 12px;">
                Mit freundlichen Grüßen,<br>
                Ihr TerminFinder Team
            </p>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=booking.patient.email,
            subject=subject,
            body_html=html_body
        )
    
    @staticmethod
    def send_email_verification(patient, token):
        """
        Email верификация для нового пациента
        
        Args:
            patient: Patient object
            token: str - verification token
        """
        subject = "Bitte bestätigen Sie Ihre E-Mail-Adresse"
        
        verification_link = f"{Config.FRONTEND_URL}/verify-email?token={token}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2563eb;">Willkommen bei TerminFinder!</h2>
            
            <p>Vielen Dank für Ihre Registrierung.</p>
            <p>Bitte bestätigen Sie Ihre E-Mail-Adresse, um fortzufahren:</p>
            
            <div style="margin: 30px 0;">
                <a href="{verification_link}" 
                   style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    E-Mail bestätigen
                </a>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">
                Oder kopieren Sie diesen Link in Ihren Browser:<br>
                <a href="{verification_link}">{verification_link}</a>
            </p>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="color: #9ca3af; font-size: 12px;">
                Falls Sie sich nicht registriert haben, ignorieren Sie diese E-Mail.<br>
                Ihr TerminFinder Team
            </p>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=patient.email,
            subject=subject,
            body_html=html_body
        )
