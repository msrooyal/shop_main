import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tempfile import template
from kavenegar import *

template = "msrooyal"

def send_email(to , subject, body):

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    user_email = 'msrooyal@gmail.com'
    user_password = 'hhgp ksxr ukbh ntnq'

    # ایجاد پیام
    to_email = to
    subject = subject
    body = body
    msg = MIMEMultipart()
    msg['From'] = user_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))



    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(user_email, user_password)
        server.sendmail(user_email, to_email, msg.as_string())
        print('Successfully sent email')
    except Exception as e:
        print(e)
        print('Failed to send email')


    finally:

        if server:
            server.quit()





def send_sms(to, code):
    try:
        api = KavenegarAPI('KAVE_API')
        params = {
            'receptor': 'to',
            'template': 'template',
            'token': 'code',
            'token2': '',
            'token3': '',
            'type': 'sms',  # sms vs call
        }
        response = api.verify_lookup(params)
        print(response)
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)