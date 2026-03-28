from dotenv import load_dotenv
import os

load_dotenv()

print("EMAIL:", os.getenv("PRODUCTIVITY_SMTP_EMAIL"))
print("PASSWORD:", os.getenv("PRODUCTIVITY_SMTP_APP_PASSWORD"))
print("HOST:", os.getenv("PRODUCTIVITY_SMTP_HOST"))
print("PORT:", os.getenv("PRODUCTIVITY_SMTP_PORT"))