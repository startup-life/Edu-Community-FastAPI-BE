# utils/validators.py
import re

EMAIL_RE = re.compile(
    r'^[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*\.[a-zA-Z]{2,3}$',
    re.IGNORECASE,
)
PASSWORD_RE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,20}$'
)
NICKNAME_RE = re.compile(
    r'^[가-힣a-zA-Z0-9]{2,10}$'
)

def valid_email(email: str | None) -> bool:
    return bool(email and EMAIL_RE.match(email))

def valid_password(password: str | None) -> bool:
    return bool(password and PASSWORD_RE.match(password))

def valid_nickname(nickname: str | None) -> bool:
    return bool(nickname and NICKNAME_RE.match(nickname))
