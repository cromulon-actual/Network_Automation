import smtplib
from socket import gaierror
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from modules.nice import smtp_creds


class Email(object):
    def __init__(self, deviceName=None, switch=None, interface=None, ip=None):
        self.deviceName = deviceName
        self.switch = switch
        self.interface = interface
        self.ip = ip

    def notify(self):
        smtp_server = smtp_creds.url
        port = 25
        sender = smtp_creds.sender_email
        receiver = smtp_creds.receiver_email

        message = MIMEMultipart()
        message["From"] = sender
        message["To"] = receiver
        message["Subject"] = f"PRTG - Security Device '{self.deviceName}' Notification"
        body = f"""
        PRTG Detected that device "{self.deviceName}" was unreachable. A port-bounce has been performed and the device is back online.
       
        =============================
        Device: {self.deviceName}
        Switch: {self.switch}
        Interface: {self.interface}
        Device IP: {self.ip}
        =============================
        """
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(smtp_server, port) as server:
                server.sendmail(sender, receiver, message.as_string())
            print("Message was sent.")
        except (gaierror, ConnectionRefusedError):
            print("Failed to connect to the server. Bad connection settings?")
        except smtplib.SMTPException as e:
            print("SMTP error occurred: " + str(e))
