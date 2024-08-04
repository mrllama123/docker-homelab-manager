from passlib.context import CryptContext
import functools

@functools.cache
def create_crypto_context(
    schemes: list[str] = ["bcrypt"], deprecated: str = "auto", **kwargs
) -> CryptContext:
    return CryptContext(schemes=schemes, deprecated=deprecated, **kwargs)


def hash_string(str_var) -> str:
    crypto_context = create_crypto_context()
    return crypto_context.hash(str_var)


def verify_hash_string(str_var, hashed_str_var) -> bool:
    crypto_context = create_crypto_context()
    return crypto_context.verify(str_var, hashed_str_var)



