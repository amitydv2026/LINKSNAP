"""Short code generation: random base62 string with collision retry."""
import random
import string

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Link

_ALPHABET = string.ascii_letters + string.digits  # 62 characters -> base62


def generate_short_code(length: int) -> str:
    """Return a random base62 string of the given length."""
    return "".join(random.choices(_ALPHABET, k=length))


def create_unique_short_code(db: Session, length: int | None = None, max_retries: int = 10) -> str:
    """Generate a unique short code, retrying on collision.

    With a 7-char base62 code there are 62^7 ~= 3.5 trillion combinations, so
    collisions are vanishingly rare; we still retry to be safe.
    """
    length = length or settings.short_code_length
    for _ in range(max_retries):
        code = generate_short_code(length)
        if not db.query(Link).filter(Link.short_code == code).first():
            return code
    raise RuntimeError("Could not generate a unique short code after retries")
