"""
Stripe Service - Интеграция с Stripe для платежей
"""
import stripe
from config import Config
from decimal import Decimal

stripe.api_key = Config.STRIPE_SECRET_KEY


class StripeService:
    """
    Сервис для работы со Stripe API
    """
    
    @staticmethod
    def create_payment_intent(amount, customer_email, payment_method_id, metadata=None):
        """
        Создать Payment Intent
        
        Args:
            amount: Decimal - сумма в евро
            customer_email: str - email пациента
            payment_method_id: str - Stripe payment method ID
            metadata: dict - дополнительные данные
        
        Returns:
            dict: Payment Intent object
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # конвертация в центы
                currency='eur',
                payment_method=payment_method_id,
                customer_email=customer_email,
                confirm=True,  # автоматическое подтверждение
                metadata=metadata or {},
                description=f"Terminreservierung - {customer_email}",
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'  # только прямые платежи
                }
            )
            
            return intent
            
        except stripe.error.CardError as e:
            # Карта отклонена
            raise Exception(f"Card declined: {e.user_message}")
        
        except stripe.error.StripeError as e:
            # Другие ошибки Stripe
            raise Exception(f"Stripe error: {str(e)}")
    
    @staticmethod
    def create_refund(payment_intent_id, amount):
        """
        Создать возврат средств
        
        Args:
            payment_intent_id: str - ID Payment Intent
            amount: Decimal - сумма возврата в евро
        
        Returns:
            dict: Refund object
        """
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id,
                amount=int(amount * 100),  # конвертация в центы
                reason='requested_by_customer'
            )
            
            return refund
            
        except stripe.error.StripeError as e:
            raise Exception(f"Refund failed: {str(e)}")
    
    @staticmethod
    def get_payment_intent(payment_intent_id):
        """
        Получить информацию о Payment Intent
        
        Args:
            payment_intent_id: str
        
        Returns:
            dict: Payment Intent object
        """
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to retrieve payment: {str(e)}")
    
    @staticmethod
    def create_customer(email, name=None):
        """
        Создать Stripe Customer (опционально для будущего)
        
        Args:
            email: str
            name: str
        
        Returns:
            dict: Customer object
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'source': 'terminfinder'}
            )
            
            return customer
            
        except stripe.error.StripeError as e:
            raise Exception(f"Failed to create customer: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(payload, signature):
        """
        Верификация webhook signature от Stripe
        
        Args:
            payload: bytes - request body
            signature: str - Stripe-Signature header
        
        Returns:
            dict: Event object
        
        Raises:
            ValueError: если signature невалидная
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                Config.STRIPE_WEBHOOK_SECRET
            )
            
            return event
            
        except ValueError as e:
            # Invalid payload
            raise
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise ValueError("Invalid signature")
