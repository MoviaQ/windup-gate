# Jak współtworzyć WindUp Gate

Krótka instrukcja dla nowych osób. Projekt jest edukacyjny i po polsku;
pisz prosto i konkretnie.

## Przygotowanie

Potrzebne: Python 3.11+ i `uv`. Wszystkie komendy uruchamiaj w katalogu projektu.

```bash
uv sync --locked
.venv/bin/windup-gate train --output models/moj-eksperyment.joblib
.venv/bin/windup-gate analyze 'Przetłumacz proszę wiadomość na angielski'
```

Nigdy nie nadpisuj istniejącego `models/intent.joblib`.
Eksperymenty zapisuj pod nową nazwą przez `--output`.

## Zanim zaczniesz zmieniać kod

1. Przeczytaj `AGENTS.md`, `README.md`, `docs/project-scope.md` i `KANBAN.md`.
2. Sprawdź `git status` — w projekcie może pracować kilka osób naraz.
3. Przejmij jedno wolne zadanie w `KANBAN.md`: wpisz właściciela i przenieś
   do „W toku” przed zmianą kodu. Nie ruszaj zadań zajętych przez innych.
4. Szczegóły wymagań są w karcie zadania w `docs/tasks.md`.
   Rób tylko to, co jest w karcie — nie cały backlog naraz.

## Zasady

- Program działa lokalnie i nie wywołuje sieci przy treningu ani predykcji.
  Nie dodawaj wywołań LLM, API ani pobierania danych przy predykcji.
- Klasyfikacja to nie wykonanie zadania: `assist` i `fallback` nigdy
  nie oznaczają `completed`.
- Nie przeglądaj końcowego zbioru testowego (`evaluate --split test`),
  żeby wymyślać reguły lub poprawki. Służy jednorazowej ocenie zamrożonego modelu.
- Dane syntetyczne nazywaj syntetycznymi. Nie przedstawiaj pokrycia testów
  ani wyników na demie jako skuteczności na prawdziwych danych.
- Nie commituj sekretów (kluczy API, haseł, tokenów), wag modeli ani prywatnych
  danych. Wagi `joblib` wczytuj tylko z zaufanych lokalnych plików.

## Wymagane sprawdzenia

Przed zgłoszeniem zmiany uruchom wszystko z `AGENTS.md`:

```bash
uv sync --locked
.venv/bin/python -m pytest -q --cov=windup_gate --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pyright
uv build
```

Do zmian kodu dodaj testy zachowania, w tym przypadków błędów.
Przy niepełnym odbiorze wpisz wynik sprawdzeń i ograniczenia do `KANBAN.md`.

## Zgłaszanie zmiany

- Pracuj na osobnej gałęzi utworzonej ze świeżego `main`, nie bezpośrednio na `main`.
- Pull request otwieraj jako szkic (draft); opis powinien zawierać plan testów
  i faktyczne wyniki sprawdzeń.
- Samo mergeowanie robi właściciel repozytorium — w opisie PR napisz,
  czego potrzebujesz od niego.
