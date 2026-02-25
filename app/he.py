import base64
import tenseal as ts

_CONTEXT: ts.Context | None = None

def init_context() -> ts.Context:
    """
    CKKS: szyfrowanie liczb rzeczywistych (przybliżone).
    W sam raz do sumy/średniej.
    """
    global _CONTEXT
    if _CONTEXT is not None:
        return _CONTEXT

    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    ctx.global_scale = 2**40

    # klucze ewaluacyjne (na przyszłość)
    ctx.generate_galois_keys()
    ctx.generate_relin_keys()

    _CONTEXT = ctx
    return ctx


def encrypt_number(value: float) -> str:
    ctx = init_context()
    vec = ts.ckks_vector(ctx, [float(value)])
    raw = vec.serialize()
    return base64.b64encode(raw).decode("utf-8")


def add_ciphertexts(ciphertexts_b64: list[str]) -> str:
    if not ciphertexts_b64:
        raise ValueError("Brak danych do agregacji.")

    ctx = init_context()

    def load_vec(b64: str) -> ts.CKKSVector:
        raw = base64.b64decode(b64.encode("utf-8"))
        return ts.ckks_vector_from(ctx, raw)

    acc = load_vec(ciphertexts_b64[0])
    for b in ciphertexts_b64[1:]:
        acc += load_vec(b)

    return base64.b64encode(acc.serialize()).decode("utf-8")


def decrypt_number_demo(ciphertext_b64: str) -> float:
    """
    Tylko do weryfikacji w demo.
    Docelowo odszyfrowanie powinno być po stronie klienta (klucz prywatny poza serwerem).
    """
    ctx = init_context()
    raw = base64.b64decode(ciphertext_b64.encode("utf-8"))
    vec = ts.ckks_vector_from(ctx, raw)
    return float(vec.decrypt()[0])