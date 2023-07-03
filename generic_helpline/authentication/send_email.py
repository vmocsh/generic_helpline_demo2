import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import basename

from django.conf import settings


def email_to(recipient, subject, body, files):
    username = settings.EMAIL_USERNAME
    password = settings.EMAIL_PASSWORD
    host = settings.EMAIL_HOST
    FROM = settings.EMAIL_USERNAME
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body
    msg = MIMEMultipart()
    msg['From'] = FROM
    msg['To'] = ", ".join(TO)
    msg['Subject'] = SUBJECT

    msg.attach(MIMEText(TEXT))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    server = smtplib.SMTP(host,25)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(FROM, TO, msg.as_string())
    server.close()
