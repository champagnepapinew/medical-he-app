# Medical HE App

Projekt demonstracyjny do pracy dyplomowej: aplikacja do przetwarzania danych medycznych z wykorzystaniem szyfrowania homomorficznego.

## Zakres projektu

- rejestr pacjentów i pomiarów medycznych,
- wprowadzanie pomiarów jako zwykłych liczb i automatyczne szyfrowanie przed zapisem,
- przechowywanie pomiarów w bazie jako ciphertext `base64`,
- agregacja sumy i średniej na zaszyfrowanych danych,
- prosty benchmark `plaintext vs HE`,
- dane demonstracyjne i smoke test aplikacji.

## Stos technologiczny

- Python 3.11
- FastAPI
- SQLAlchemy
- Jinja2
- SQLite
- TenSEAL / CKKS

## Uruchomienie

1. Aktywuj środowisko:

```bash
source .venv/bin/activate
```

2. Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

3. Wygeneruj klucze:

```bash
python client/client.py keygen
```

4. Wstaw dane demo:

```bash
python seed_demo.py --reset
```

5. Opcjonalnie uruchom benchmark:

```bash
python run_benchmark_reps.py
```

6. Start aplikacji:

```bash
uvicorn app.main:app --reload
```

## Test dymny

```bash
python smoke_test.py
```

## Uwagi do demo

- publiczny kontekst HE jest trzymany w `client_keys/ctx_public.bin`,
- klucz prywatny klienta powinien być trzymany poza repozytorium; aplikacja wspiera też stary układ dla zgodności wstecznej,
- w obecnym trybie demo wpisana liczba jest szyfrowana automatycznie po stronie aplikacji,
- odszyfrowanie po stronie serwera jest używane wyłącznie jako pomocniczy tryb demo.
