# WindUp Gate — tablica zadań

Aktualizacja: 2026-10-13 (Asia/Tokyo). Źródło prawdy o statusie i właścicielu pracy.

Cel i granice systemu: [zakres projektu](docs/project-scope.md).
Wymagania i odbiór: [karty zadań](docs/tasks.md).
Start nowej sesji: [instrukcja dla OpenCode](docs/opencode-handoff.md).

## Zasady przejmowania

1. Przed edycją sprawdź `git status` i tę tablicę.
2. Weź zadanie z „Gotowe do wzięcia”: ustaw właściciela (`Codex`, `OpenCode`, `Maciej`) i przenieś do „W toku”. Zapisz to przed zmianami w kodzie.
3. Jedno zadanie ma jednego właściciela. Nie cofaj zmian innych osób/agentów.
4. Szanuj zakres plików. Zmiana wspólnego interfejsu wymaga uzgodnienia z właścicielem zależnego zadania.
5. Przy ukończeniu wpisz dowód: komendę testową, wynik i opcjonalny commit. „Przegląd” oznacza, że autor skończył, ale odbiór jeszcze trwa.
6. Jeśli pracujemy w różnych checkoutach, sam Markdown nie jest blokadą: synchronizujemy tablicę przez Git przed przejęciem. Dwie sesje w jednym katalogu widzą zmiany od razu, lecz równoczesny zapis nadal może się zderzyć.

## W toku

Brak. Przygotowanie WG-016 ukończone; publikacja (push + release) i przebieg
Actions czekają na wykonanie przez OpenCode (zgoda jest).

## Gotowe do wzięcia

Zadania poniżej można przejąć. OpenCode nie ma jeszcze przypisanego zadania.
WG-007 i WG-008 można przejąć w OpenCode. Detektor języka jest już zintegrowany w WG-006.

| ID | Zadanie | Właściciel | Zakres | Zależność / odbiór |
|---|---|---|---|---|
| WG-007 | [Baseline regułowy](docs/tasks.md#wg-007--baseline-regułowy) | — | `baselines.py`, `evaluation.py`, testy baseline/raportu, nowy raport | WG-005 ukończone; ten sam zbiór i metryki, bez strojenia na teście; routing bez zmian |
| WG-008 | [Rozbudowa danych i przegląd etykiet](docs/tasks.md#wg-008--rozbudowa-danych-i-przegląd-etykiet) | — | `data/curated/`, `docs/dataset-card.md`, `docs/data-review.md` | WG-002; pochodzenie, grupowanie parafraz, osobny odłożony test; jawny status przeglądu |
| WG-009 | [Notatnik „jak działa nasz klasyfikator”](docs/tasks.md#wg-009--jak-działa-nasz-klasyfikator) | — | `docs/learning-notes.md`, link z README | WG-003; cechy, wagi, trening i predykcja na przykładzie; sprawdzone fragmenty |

## Backlog

| ID | Zadanie | Właściciel | Zależność |
|---|---|---|---|
| WG-010 | [Kalibracja i dobór progów na lepszych danych](docs/tasks.md#wg-010--kalibracja-i-dobór-progów) | — | WG-008; nie używać końcowego testu do strojenia |
| WG-011 | [Pomiar czasu ładowania, p50/p95, RAM](docs/tasks.md#wg-011--czas-i-zasoby) | — | WG-005 |
| WG-012 | [Selekcja instrukcji/narzędzi z małego katalogu](docs/tasks.md#wg-012--wybór-instrukcjinarzędzi) | — | WG-008; osobne etykiety i metryka recall |
| WG-013 | [Porównanie z embeddingami / SetFit](docs/tasks.md#wg-013--embeddingi--setfit-jako-porównanie) | — | WG-008, WG-011 |
| WG-014 | [Wielojęzyczne i wieloetykietowe intencje](docs/tasks.md#wg-014--wiele-języków-i-wiele-intencji) | — | WG-008; obecny model ma ograniczony zakres |

## Przegląd

Brak.

## Gotowe

| ID | Zadanie | Właściciel | Dowód |
|---|---|---|---|
| WG-000 | Plan nauki i wdrożenia | Codex | `plans/windup-gate-plan.md` |
| WG-001 | Środowisko i szkielet | Codex | `uv sync --locked`, CLI w nowym procesie, `uv build` — OK |
| WG-002 | Dane demo i walidator podziałów | Codex | 100 syntetycznych rekordów 60/20/20; `pytest tests/test_data.py` — 10 testów OK |
| WG-003 | Trening, zapis i odczyt klasyfikatora | Codex | `windup-gate train`; round-trip i brak dopasowania cech na walidacji/teście sprawdzone testami |
| WG-004 | Routing i CLI z fallbackiem | Codex | 46 testów OK, pokrycie 98,94%; Ruff i Pyright OK; `assist`/`fallback`, bez lokalnego wykonania |
| WG-005 | Raport demonstracyjny | Codex | `reports/demo-validation.md` i JSON; 20 przykładów walidacyjnych, jawne błędy; test modelu nadal odłożony |
| WG-006 | Integracja istniejącego `MoviaQ/windup-language-recog` | Codex | `reports/language-integration.md`; 83 testy z rzeczywistymi wagami OK, pokrycie 99,24%; CLI zwraca `local` i język; zachowane `und`, brak sieci i treningu |
| WG-015 | Rozpisanie zakresu i kart zadań dla OpenCode | Codex | `docs/project-scope.md`, karty WG-007–014 w `docs/tasks.md`, nowa instrukcja przejęcia i prompt; 43 lokalne linki/kotwice sprawdzone, `git diff --check` OK. Tylko dokumentacja; kod, dane i wagi bez zmian. Brak nowych pomiarów jakości AI. |
| WG-016 | Gotowa publikacja open-source rdzenia (przygotowanie) | OpenCode | 82 passed, 1 skipped, pokrycie 99,24%; ruff, pyright i `uv build` OK; poprawki testera naniesione (przenośna ścieżka detektora, pełna weryfikacja w CD, gitignore, cel w README). Bez commitów i pushy. Publikacja i przebieg Actions do wykonania przez OpenCode. |

## Blokady

- Brak rzeczywistych danych użytkownika. Przykłady demo są syntetyczne i służą uruchomieniu procesu.
- Lokalna identyfikacja języka wymaga jawnego skonfigurowania źródeł i wag istniejącego detektora; setup w README.
- Model demo nie spełnia docelowej jakości: macro-F1 0,6976, zaakceptowane 2/20, poprawne 1/2. Wysokie score może być błędne.

## Historia przekazania

- 2026-10-09: Codex rozpoczął i ukończył WG-001–005 na gałęzi `main`.
- Commity lokalne: `902ab2e` i `ff1259a` — testy RED; `30fa005` — działający prototyp GREEN.
- Repozytorium jest lokalne; nie skonfigurowano zdalnego repo ani nie wykonano push.
- 2026-10-10: WG-006 ukończone przez Codex; użyto istniejącego repo i wag użytkownika, bez budowy nowego detektora. Commity `ae9fb58`, `e73e04f`, `33925ba` opisują integrację i testy; `5058035` dodaje wyjaśniony fallback niezgodnego checkpointu.
- 2026-10-10: WG-015 ukończone; rozdzielono opis projektu, wymagania zadań i instrukcję OpenCode. WG-007–009 nadal wolne; nie przypisano pracy automatycznie.
- 2026-10-13: WG-016 (przygotowanie) ukończone przez OpenCode; dowody: 82 passed, 1 skipped, 99,24%, ruff/pyright/build OK. Publikacja i Actions do wykonania przez OpenCode (zgoda jest).
