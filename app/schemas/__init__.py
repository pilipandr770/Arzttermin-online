"""
Input Validation Schemas using Marshmallow
Provides centralized validation for all API inputs
"""
from marshmallow import Schema, fields, validates, ValidationError, validate
import re


class EmailField(fields.Email):
    """Enhanced email field with additional validation"""
    def _deserialize(self, value, attr, data, **kwargs):
        email = super()._deserialize(value, attr, data, **kwargs)
        # Additional sanitization
        return email.lower().strip()


class PasswordValidator:
    """Password strength validator"""
    @staticmethod
    def validate(password):
        """
        Validate password strength
        Requirements:
        - Minimum 8 characters
        - Maximum 72 characters (bcrypt limit)
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        """
        if len(password) < 8:
            raise ValidationError("Passwort muss mindestens 8 Zeichen lang sein")
        
        if len(password) > 72:
            raise ValidationError("Passwort ist zu lang (maximal 72 Zeichen)")
        
        if not re.search(r"[a-z]", password):
            raise ValidationError("Passwort muss mindestens einen Kleinbuchstaben enthalten")
        
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Passwort muss mindestens einen Großbuchstaben enthalten")
        
        if not re.search(r"\d", password):
            raise ValidationError("Passwort muss mindestens eine Ziffer enthalten")
        
        return True


class PatientLoginSchema(Schema):
    """Patient login validation"""
    phone = fields.Str(required=True, validate=validate.Length(min=7, max=20))
    
    @validates('phone')
    def validate_phone(self, value):
        # Remove spaces and common separators
        clean_phone = re.sub(r'[\s\-\(\)]+', '', value)
        
        # Should contain only digits and optional +
        if not re.match(r'^\+?[\d]+$', clean_phone):
            raise ValidationError('Ungültiges Telefonnummernformat')
        
        if len(clean_phone) < 7:
            raise ValidationError('Telefonnummer ist zu kurz')


class PatientRegisterSchema(Schema):
    """Patient registration validation"""
    phone = fields.Str(required=True)
    name = fields.Str(validate=validate.Length(min=2, max=100))
    email = EmailField()
    
    @validates('phone')
    def validate_phone(self, value):
        clean_phone = re.sub(r'[\s\-\(\)]+', '', value)
        if not re.match(r'^\+?[\d]+$', clean_phone):
            raise ValidationError('Ungültiges Telefonnummernformat')


class DoctorLoginSchema(Schema):
    """Doctor login validation"""
    email = EmailField(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1, max=72))


class DoctorRegisterSchema(Schema):
    """Doctor registration validation"""
    email = EmailField(required=True)
    password = fields.Str(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=2, max=50))
    speciality = fields.Str(required=True)
    tax_number = fields.Str(validate=validate.Length(max=50))
    city = fields.Str(validate=validate.Length(max=100))
    practice_id = fields.Str()
    
    @validates('password')
    def validate_password(self, value):
        return PasswordValidator.validate(value)


class PracticeRegisterSchema(Schema):
    """Practice registration validation"""
    name = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    vat_number = fields.Str(validate=validate.Length(max=50))
    owner_email = EmailField(required=True)
    phone = fields.Str(validate=validate.Length(max=20))
    address = fields.Str(validate=validate.Length(max=500))
    
    @validates('phone')
    def validate_phone(self, value):
        if value:
            clean_phone = re.sub(r'[\s\-\(\)]+', '', value)
            if not re.match(r'^\+?[\d]+$', clean_phone):
                raise ValidationError('Ungültiges Telefonnummernformat')


class ChatMessageSchema(Schema):
    """Chat message validation"""
    message = fields.Str(required=True, validate=validate.Length(min=1, max=2000))
    session_id = fields.Str()
    current_page = fields.Str()
    
    @validates('message')
    def validate_message(self, value):
        # Strip HTML tags for security
        clean_message = re.sub(r'<[^>]+>', '', value)
        if len(clean_message.strip()) == 0:
            raise ValidationError('Nachricht darf nicht leer sein')


class BookingCreateSchema(Schema):
    """Booking creation validation"""
    timeslot_id = fields.Str(required=True)
    notes = fields.Str(validate=validate.Length(max=1000))
    
    @validates('notes')
    def validate_notes(self, value):
        if value:
            # Strip HTML tags
            clean_notes = re.sub(r'<[^>]+>', '', value)
            return clean_notes


class AlertCreateSchema(Schema):
    """Patient alert creation validation"""
    doctor_id = fields.Str()
    speciality = fields.Str()
    city = fields.Str(validate=validate.Length(max=100))
    
    @validates('speciality')
    def validate_speciality(self, value):
        # Validate against allowed specialities
        if value:
            # Import here to avoid circular dependency
            from app.constants.specialities import SPECIALITIES
            if value not in SPECIALITIES:
                raise ValidationError('Ungültige Fachrichtung')
