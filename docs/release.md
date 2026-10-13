# Jak wydać wersję WindUp Gate

Wydanie to opublikowany tag w GitHub z dołączonymi paczkami (sdist i wheel).
Workflow [release.yml](../.github/workflows/release.yml) buduje je sam;
nie wysyłamy nic na PyPI i nie wdrażamy na serwery.

## Wymagania

- Zielone CI na `main` (workflow `CI`: pytest z pokryciem >= 80%, ruff,
  pyright, `uv build`).
- Uprawnienia do tworzenia wydań w repozytorium `MoviaQ/windup-gate`.

## Kroki

1. Upewnij się, że `main` jest zielony:

   ```bash
   uv sync --locked
   .venv/bin/python -m pytest -q --cov=windup_gate --cov-report=term-missing --cov-fail-under=80
   .venv/bin/ruff check src tests
   .venv/bin/ruff format --check src tests
   .venv/bin/pyright
   uv build
   ```

2. Ustaw numer wersji w `pyproject.toml` (np. `0.2.0`) i dopisz go razem
   z datą do notatek wydania. Bez tego paczka zbuduje się ze starą wersją.

3. Wypchnij zmianę na `main` i poczekaj na zielone CI.

4. Na GitHub: Releases → Draft a new release → Choose a tag → wpisz nowy tag
   (format `v0.2.0`) → opisz zmiany i ograniczenia (w tym status danych
   syntetycznych) → Publish release.

5. Po publikacji workflow `Release` sam przetestuje, zbuduje i dołączy
   pliki `dist/*.tar.gz` i `dist/*.whl` DO TEGO wydania. Postęp widać
   w zakładce Actions.

## Sprawdzenie

1. Otwórz stronę wydania i sprawdź, czy w załącznikach są oba pliki:
   sdist (`.tar.gz`) i wheel (`.whl`).
2. Pobierz wheel i zainstaluj lokalnie w czystym katalogu:

   ```bash
   pip install windup_gate-*.whl
   python -m windup_gate --help
   ```

3. Jeśli workflow się nie powiódł, popraw błąd na `main` i utwórz nowe
   wydanie z nowym tagiem (np. `v0.2.1`). Nie nadpisuj opublikowanego tagu.

Workflow używa tylko automatycznego tokenu `github.token`; nie trzeba
zakładać żadnych sekretów ani konfigurować PyPI.
