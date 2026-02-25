import base64
from pathlib import Path
import tenseal as ts

PUBLIC_CTX_PATH = Path("client_keys/ctx_public.bin")

_CTX: ts.Context | None = None

def load_public_context() -> ts.Context:
    global _CTX
    if _CTX is not None:
        return _CTX

    if not PUBLIC_CTX_PATH.exists():
        raise RuntimeError(
            "Brak client_keys/ctx_public.bin. Najpierw uruchom: python client/client.py keygen"
        )

    _CTX = ts.context_from(PUBLIC_CTX_PATH.read_bytes())
    return _CTX

def add_ciphertexts(ciphertexts_b64: list[str]) -> str:
    if not ciphertexts_b64:
        raise ValueError("Brak danych do agregacji.")

    ctx = load_public_context()

    def load_vec(b64: str) -> ts.CKKSVector:
        raw = base64.b64decode(b64.encode("utf-8"))
        return ts.ckks_vector_from(ctx, raw)

    acc = load_vec(ciphertexts_b64[0])
    for b in ciphertexts_b64[1:]:
        acc += load_vec(b)

    return base64.b64encode(acc.serialize()).decode("utf-8")