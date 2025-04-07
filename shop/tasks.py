from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_order_confirmation_email(user_email):
    subject = 'Order Confirmation'
    message = 'Your order has been placed successfully!'
    from_email = 'muzaffar@example.com'
    recipient_list = [user_email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)