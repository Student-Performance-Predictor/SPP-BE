from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Email Sender
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
        error_message = f"Email sending failed for {recipient_email}. Error: {e}"
        print(error_message)