import smtplib
import ssl
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


class Notification:
    def __init__(self):
        self.email = os.getenv("SMTP_EMAIL")
        self.password = os.getenv("SMTP_PASSWORD")

    def send_email(self, recipient, noise_level, threshold):
        message = EmailMessage()
        message["Subject"] = "Peringatan Tingkat Kebisingan!"
        message["From"] = self.email
        message["To"] = recipient
        message.set_content(
            f"Peringatan tingkat kebisingan!\n\n"
            f"Tingkat kebisingan terdeteksi: {noise_level} db\n\n"
            f"Ambang batas kebisingan: {threshold} db"
            f"Suara yang terekam telah mencapai ambang batas.\n\n"
            f"Silahkan cari tempat yang lebih tenang."
        )
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as connection:
            connection.starttls(context=ssl.create_default_context())
            connection.login(self.email, self.password)
            connection.send_message(message)