import random


def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"
