from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
PROJECT_KEY_DIR = ROOT_DIR / "client_keys"
PUBLIC_CTX_PATH = PROJECT_KEY_DIR / "ctx_public.bin"
LEGACY_SECRET_CTX_PATH = PROJECT_KEY_DIR / "ctx_secret.bin"
CLIENT_SECRET_DIR = Path.home() / ".medical_he_client"
SECRET_CTX_PATH = CLIENT_SECRET_DIR / "ctx_secret.bin"


def ensure_key_dirs() -> None:
    PROJECT_KEY_DIR.mkdir(parents=True, exist_ok=True)
    CLIENT_SECRET_DIR.mkdir(parents=True, exist_ok=True)


def resolve_secret_context_path() -> Path:
    if SECRET_CTX_PATH.exists():
        return SECRET_CTX_PATH
    if LEGACY_SECRET_CTX_PATH.exists():
        return LEGACY_SECRET_CTX_PATH
    return SECRET_CTX_PATH


def using_legacy_secret_path() -> bool:
    return not SECRET_CTX_PATH.exists() and LEGACY_SECRET_CTX_PATH.exists()
