import base64
from pathlib import Path
import sys

import tenseal as ts

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from project_paths import (
    LEGACY_SECRET_CTX_PATH,
    PUBLIC_CTX_PATH,
    resolve_secret_context_path,
    SECRET_CTX_PATH,
    ensure_key_dirs,
    using_legacy_secret_path,
)

def generate_context():
    ensure_key_dirs()
    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    ctx.global_scale = 2**40
    ctx.generate_galois_keys()
    ctx.generate_relin_keys()

    # Secret key stays outside the project directory; the repo only needs the public context.
    SECRET_CTX_PATH.write_bytes(ctx.serialize(save_secret_key=True))

    # Public context is shared with the backend for homomorphic evaluation.
    ctx.make_context_public()
    PUBLIC_CTX_PATH.write_bytes(ctx.serialize())

    print("OK: wygenerowano konteksty HE.")
    print(f"Public context: {PUBLIC_CTX_PATH}")
    print(f"Secret context: {SECRET_CTX_PATH}")
    if LEGACY_SECRET_CTX_PATH.exists():
        print(
            "Uwaga: znaleziono stare ctx_secret.bin w katalogu projektu. "
            "Nowe klucze są zapisywane poza repozytorium."
        )

def load_secret_context() -> ts.Context:
    secret_path = resolve_secret_context_path()
    if not secret_path.exists():
        raise RuntimeError(
            "Brak secret context. Uruchom: python client/client.py keygen"
        )
    return ts.context_from(secret_path.read_bytes())


def print_status():
    secret_path = resolve_secret_context_path()
    print(f"Public context: {PUBLIC_CTX_PATH} [{'OK' if PUBLIC_CTX_PATH.exists() else 'BRAK'}]")
    print(f"Secret context: {secret_path} [{'OK' if secret_path.exists() else 'BRAK'}]")
    if using_legacy_secret_path():
        print(
            "Uwaga: aplikacja używa starego położenia klucza prywatnego w katalogu projektu. "
            "Wygeneruj ponownie klucze, aby przenieść sekret poza repozytorium."
        )

def encrypt(value: float) -> str:
    ctx = load_secret_context()
    vec = ts.ckks_vector(ctx, [float(value)])
    raw = vec.serialize()
    return base64.b64encode(raw).decode("utf-8")

def decrypt(ciphertext_b64: str) -> float:
    ctx = load_secret_context()
    raw = base64.b64decode(ciphertext_b64.encode("utf-8"))
    vec = ts.ckks_vector_from(ctx, raw)
    return float(vec.decrypt()[0])
def encrypt_to_file(value: float, out_path: str = "cipher.txt"):
    ct = encrypt(value)
    Path(out_path).write_text(ct, encoding="utf-8")
    print(f"Zapisano ciphertext do pliku: {out_path}")

def decrypt_from_file(path: str) -> float:
    ct = Path(path).read_text(encoding="utf-8").strip()
    return decrypt(ct)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Użycie:")
        print("  python client/client.py keygen")
        print("  python client/client.py status")
        print("  python client/client.py enc 12.34")
        print("  python client/client.py dec <CIPHERTEXT_BASE64>")
        raise SystemExit(1)

    cmd = sys.argv[1].lower()

    if cmd == "keygen":
        generate_context()
    elif cmd == "status":
        print_status()

    elif cmd == "enc":
        val = float(sys.argv[2])
        print(encrypt(val))

    elif cmd == "dec":
        ct = sys.argv[2]
        print(decrypt(ct))
    elif cmd == "encfile":
        val = float(sys.argv[2])
        out = sys.argv[3] if len(sys.argv) > 3 else "cipher.txt"
        encrypt_to_file(val, out)

    elif cmd == "decfile":
        path = sys.argv[2]
        print(decrypt_from_file(path))

    else:
        raise SystemExit("Nieznana komenda.")
