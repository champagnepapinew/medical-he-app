import base64
from pathlib import Path
import tenseal as ts

KEY_DIR = Path("client_keys")
KEY_DIR.mkdir(exist_ok=True)

CTX_PUBLIC = KEY_DIR / "ctx_public.bin"
CTX_SECRET = KEY_DIR / "ctx_secret.bin"

def generate_context():
    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    ctx.global_scale = 2**40
    ctx.generate_galois_keys()
    ctx.generate_relin_keys()

    # zapis secret context
    CTX_SECRET.write_bytes(ctx.serialize(save_secret_key=True))

    # public context (bez secret key)
    ctx.make_context_public()
    CTX_PUBLIC.write_bytes(ctx.serialize())

    print("OK: wygenerowano klucze i konteksty w folderze client_keys/")

def load_secret_context() -> ts.Context:
    if not CTX_SECRET.exists():
        raise RuntimeError("Brak ctx_secret.bin. Uruchom: python client.py keygen")
    return ts.context_from(CTX_SECRET.read_bytes())

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
        print("  python client.py keygen")
        print("  python client.py enc 12.34")
        print("  python client.py dec <CIPHERTEXT_BASE64>")
        raise SystemExit(1)

    cmd = sys.argv[1].lower()

    if cmd == "keygen":
        generate_context()

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
