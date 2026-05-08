# from fastapi_mail import FastMail, MessageSchema
# from src.services.mail.config_mail import conf 


# async def send_verification_email(email: str, token: str):
#     try:
#         verification_link = (
#             f"http://localhost:8000/auth/verify-email?token={token}"
#         )

#         message = MessageSchema(
#             subject="Verify your account",
#             recipients=[email],
#             body=f"""
# Hello,

# Click the link below to verify your account:

# {verification_link}
# """,
#             subtype="plain"
#         )

#         fm = FastMail(conf)
#         await fm.send_message(message)

#         print("Email sent successfully")

#     except Exception as e:
#         print("EMAIL FAILED:", e)