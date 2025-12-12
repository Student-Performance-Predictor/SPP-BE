from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading

def send_email_sync(subject, template_name, context, recipient_email):
    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(
            subject,
            text_content,
            'EduMet <noreply@edumet.in>',
            [recipient_email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send()
        
    except Exception as e:
        print(f"Email sending failed for {recipient_email}. Error: {e}")

def send_email_background(subject, template_name, context, recipient_email):
    thread = threading.Thread(
        target=send_email_sync,
        args=(subject, template_name, context, recipient_email)
    )
    thread.daemon = True
    thread.start()
