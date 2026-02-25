import time
import csv
import random
from pathlib import Path
import base64

import tenseal as ts
from app.he_server import add_ciphertexts

# load secret context once to speed up encrypt/decrypt in benchmark
SECRET_PATH = Path("client_keys/ctx_secret.bin")
if not SECRET_PATH.exists():
    raise RuntimeError("Brak client_keys/ctx_secret.bin — uruchom najpierw keygen")
_SECRET_CTX = ts.context_from(SECRET_PATH.read_bytes())

def encrypt_fast(ctx, value: float) -> str:
    vec = ts.ckks_vector(ctx, [float(value)])
    return base64.b64encode(vec.serialize()).decode("utf-8")

def decrypt_fast(ctx, ciphertext_b64: str) -> float:
    raw = base64.b64decode(ciphertext_b64.encode("utf-8"))
    vec = ts.ckks_vector_from(ctx, raw)
    return float(vec.decrypt()[0])


def run_once(n, seed=42):
    random.seed(seed)
    values = [random.uniform(1, 100) for _ in range(n)]

    # plaintext sum time
    t0 = time.perf_counter()
    plain_sum = sum(values)
    t_plain = (time.perf_counter() - t0) * 1000.0

    # encrypt (client) using preloaded secret context
    t0 = time.perf_counter()
    cts = [encrypt_fast(_SECRET_CTX, v) for v in values]
    t_enc = (time.perf_counter() - t0) * 1000.0

    # HE sum (server-side function)
    t0 = time.perf_counter()
    result_ct = add_ciphertexts(cts)
    t_he = (time.perf_counter() - t0) * 1000.0

    # decrypt (client)
    t0 = time.perf_counter()
    dec = decrypt_fast(_SECRET_CTX, result_ct)
    t_dec = (time.perf_counter() - t0) * 1000.0

    err = abs(plain_sum - dec) if dec is not None else None

    return {
        "n": n,
        "t_plain_ms": t_plain,
        "t_enc_ms": t_enc,
        "t_he_ms": t_he,
        "t_dec_ms": t_dec,
        "plain_sum": plain_sum,
        "dec_sum": dec,
        "error": err,
    }


def main():
    ns = [10, 100, 500]
    results = []
    for n in ns:
        print(f"Running benchmark n={n}...")
        res = run_once(n, seed=12345)
        results.append(res)
        print(res)
        # write/appending CSV after each run to avoid data loss on interruption
        keys = ["n", "t_plain_ms", "t_enc_ms", "t_he_ms", "t_dec_ms", "plain_sum", "dec_sum", "error"]
        write_header = False
        try:
            with open("benchmark_results.csv", "x", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerow({k: res.get(k) for k in keys})
        except FileExistsError:
            with open("benchmark_results.csv", "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writerow({k: res.get(k) for k in keys})

    print("Wyniki zapisane do benchmark_results.csv")


if __name__ == "__main__":
    main()
