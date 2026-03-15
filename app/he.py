import base64
import tenseal as ts
from project_paths import resolve_secret_context_path

_CONTEXT: ts.Context | None = None

def load_secret_context() -> ts.Context:
    """
    Demo helper for local decryption. It reuses the same client-side secret context.
    """
    global _CONTEXT
    if _CONTEXT is not None:
        return _CONTEXT

    secret_path = resolve_secret_context_path()
    if not secret_path.exists():
        raise RuntimeError(
            "Brak secret context do demo odszyfrowania. Uruchom: python client/client.py keygen"
        )

    _CONTEXT = ts.context_from(secret_path.read_bytes())
    return _CONTEXT


def encrypt_number_demo(value: float) -> str:
    """
    Demo helper for automatic server-side encryption of numeric input.
    In the target architecture, encryption should happen on the client side.
    """
    ctx = load_secret_context()
    vec = ts.ckks_vector(ctx, [float(value)])
    return base64.b64encode(vec.serialize()).decode("utf-8")


def decrypt_number_demo(ciphertext_b64: str) -> float:
    """
    Tylko do weryfikacji w demo.
    Docelowo odszyfrowanie powinno być po stronie klienta (klucz prywatny poza serwerem).
    """
    ctx = load_secret_context()
    raw = base64.b64decode(ciphertext_b64.encode("utf-8"))
    vec = ts.ckks_vector_from(ctx, raw)
    return float(vec.decrypt()[0])
