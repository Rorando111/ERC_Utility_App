import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_code():
    return str(random.randint(100000, 999999))

def send_verification_email(recipient_email, code, username):
    sender_email = "erc.pdfut.authenticator@gmail.com"
    sender_password = "wcta nqtb unol msco"

    smtp_server = "smtp.gmail.com"
    port = 587

    subject = "ERC Login Verification Code"

    html = f"""
    <html>
    <body style="font-family: Segoe UI, sans-serif; background-color: #f8f9fa; padding: 0; margin: 0;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding: 20px;">
        <tr>
            <td align="center">
            <table style="max-width: 500px; background: #ffffff; padding: 25px 20px 10px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); text-align: left;">
                <tr>
                <td>
                    <h2 style="color: #333; margin: 0 0 10px;">Hi {username}, 👋</h2>
                    <p style="font-size: 15px; color: #555; margin-top: 0;">
                    Here is your login verification code:
                    </p>
                </td>
                </tr>
                <tr>
                <td>
                    <div style="font-size: 28px; font-weight: bold; background-color: #eaf4fe; color: #007bff; text-align: center; padding: 14px; border-radius: 8px; letter-spacing: 2px; margin: 20px 0;">
                    {code}
                    </div>
                </td>
                </tr>
                <tr>
                <td>
                    <p style="font-size: 13px; color: #888; margin: 0 0 10px;">
                    This code will expire in a few minutes. If you didn’t request it, you can safely ignore this message.
                    </p>
                </td>
                </tr>
            </table>
            </td>
        </tr>
        </table>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(html, "html"))

        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        print(f"✅ Sent 2FA code to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False
