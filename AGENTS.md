# WindUp Gate — wskazówki dla Codex i OpenCode

Projekt edukacyjny w Pythonie. Najpierw przeczytaj `README.md`, `docs/project-scope.md`,
`KANBAN.md`, dokumentację interfejsów w `docs/opencode-handoff.md` oraz kartę
wybranego zadania w `docs/tasks.md`. Karty opisują wymagania; tablica określa status
i właściciela. Nie implementuj całego backlogu w ramach jednego zadania.

## Wspólna praca

- `KANBAN.md` jest źródłem statusu i właścicieli zadań. Przejmij zadanie przed zmianą kodu.
- Sprawdź `git status` przed rozpoczęciem. W tym katalogu mogą pracować inne sesje.
- Nie cofaj cudzych zmian. Nie nadpisuj istniejących wag modelu.
- W różnych checkoutach najpierw zsynchronizuj tablicę; plik Markdown nie zapewnia blokady.
- Przy zakończeniu zadania dopisz dowód w tablicy i opisz ograniczenia.

## Zachowanie projektu

- Domyślne działanie jest lokalne, bez LLM i bez ukrytych wywołań sieciowych.
- Klasyfikacja nie jest wykonaniem zadania. `assist` i `fallback` nigdy nie oznaczają `completed`.
- Zachowuj oryginalne żądanie; nie ucinaj długich wejść po cichu.
- Trening używa wyłącznie zbioru `train`. Walidacja służy dobieraniu parametrów;
  końcowy `test` pozostaje odłożony do zamrożonej oceny.
- Nie przedstawiaj danych syntetycznych ani pokrycia testami jako realnej skuteczności AI.
- Wagi joblib są zaufanymi lokalnymi artefaktami. Nie pobieraj i nie wczytuj cudzych pickle.

## Komendy

```bash
uv sync --locked
.venv/bin/python -m pytest -q --cov=windup_gate --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pyright
uv build
```

Przy zmianie zależności zaktualizuj `uv.lock`. Testuj nowe zachowania i błędy, nie kopię
implementacji. Nie uruchamiaj końcowego testu modelu przy każdej zmianie aplikacji.
