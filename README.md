# Medical HE App

Projekt demonstracyjny do pracy dyplomowej: aplikacja do przetwarzania danych medycznych z wykorzystaniem szyfrowania homomorficznego.

## Cel projektu

Celem projektu jest pokazanie, ze dane medyczne moga byc:

- zapisywane w bazie w postaci ciphertext,
- agregowane bez odslaniania plaintextu po stronie serwera,
- przetwarzane w modelu klient-serwer z wykorzystaniem szyfrowania homomorficznego.

## Zakres aplikacji

- rejestr pacjentow,
- dodawanie pomiarow medycznych,
- automatyczne szyfrowanie danych liczbowych przed zapisem,
- przechowywanie wartosci jako ciphertext `base64`,
- obliczanie sumy i sredniej dla zaszyfrowanych pomiarow,
- prosty benchmark `plaintext vs HE`,
- dane demonstracyjne i smoke test.

## Stos technologiczny

- Python 3.11
- FastAPI
- SQLAlchemy
- Jinja2
- SQLite
- TenSEAL / CKKS

## Wymagania

- Python 3.11
- `pip`
- system zgodny z biblioteka `TenSEAL`

Uwaga: projekt byl weryfikowany na Pythonie `3.11`. Na Pythonie `3.13` zaleznosci nie byly gotowe do uruchomienia.

## Uruchomienie

### Windows

1. Utworz srodowisko:

```powershell
py -3.11 -m venv .venv
```

2. Aktywuj srodowisko:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Zainstaluj zaleznosci:

```powershell
pip install -r requirements.txt
```

4. Wygeneruj klucze:

```powershell
python client\client.py keygen
```

5. Wstaw dane demonstracyjne:

```powershell
python seed_demo.py --reset
```

6. Opcjonalnie uruchom benchmark:

```powershell
python run_benchmark_reps.py
```

7. Uruchom aplikacje:

```powershell
uvicorn app.main:app --reload
```

## Test dymny

```powershell
python smoke_test.py
```

## Architektura demo a architektura docelowa

Projekt prezentuje poprawny przeplyw dla operacji HE, ale aplikacja dziala w trybie demonstracyjnym:

- serwer przechowuje i agreguje ciphertext,
- publiczny kontekst HE jest udostepniany backendowi,
- klucz prywatny klienta powinien pozostawac poza repozytorium,
- w aktualnym demo wpisana liczba jest szyfrowana automatycznie po stronie aplikacji,
- opcjonalne odszyfrowanie wyniku po stronie serwera sluzy tylko do prezentacji lokalnej.

Docelowy wariant architektury:

- szyfrowanie wejscia powinno byc wykonywane po stronie klienta,
- serwer powinien operowac wylacznie na ciphertext,
- odszyfrowanie wyniku powinno odbywac sie po stronie klienta.

## Klucze

- publiczny kontekst HE: `client_keys/ctx_public.bin`
- prywatny kontekst klienta: `C:\Users\<user>\.medical_he_client\ctx_secret.bin`

Aplikacja zachowuje zgodnosc wsteczna ze starszym ukladem, ale preferowany jest zapis klucza prywatnego poza repozytorium.

## Szybki scenariusz do prezentacji

1. `py -3.11 -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. `python client\client.py keygen`
5. `python seed_demo.py --reset`
6. `python run_benchmark_reps.py`
7. `uvicorn app.main:app --reload`

## Wynik weryfikacji

Podczas lokalnej weryfikacji przechodzily:

- generowanie kluczy,
- seed danych demo,
- smoke test,
- benchmark,
- szyfrowanie i odszyfrowanie pojedynczej wartosci,
- suma HE dla wielu ciphertextow.
