# Przejęcie pracy w OpenCode

## Cel w jednym akapicie

Budujemy edukacyjną warstwę małych lokalnych klasyfikatorów przed ewentualnym LLM.
Obecny model rozpoznaje pięć intencji; polityka przyjmuje decyzję albo odstępuje.
Jedynym zakończonym lokalnie zadaniem jest rozpoznanie języka przez istniejący model
użytkownika. Pozostałe intencje jedynie wskazują dalszą ścieżkę. Nie implementuj
przy okazji czatu, generowania odpowiedzi, wywołań LLM ani nowego detektora języka.

## Kolejność czytania

1. [AGENTS.md](../AGENTS.md) — zasady pracy i sprawdzenia.
2. [README.md](../README.md) — uruchomienie i obecne zachowanie.
3. [Zakres projektu](project-scope.md) — cel, architektura, granice i przykłady.
4. [KANBAN.md](../KANBAN.md) — aktualny status i właściciele.
5. [Karta wybranego zadania](tasks.md) i kontrakt poniżej.

Otwórz ten sam katalog projektu albo osobny checkout zsynchronizowany przez Git.
Sprawdź status zmian, zanim zaczniesz. Zadanie nie jest przypisane do OpenCode,
dopóki nie wpiszesz właściciela i nie przeniesiesz go do „W toku”. Nie przejmuj
zadania zajętego w innej sesji. Karta zadania nie zastępuje rezerwacji w tablicy.

## Od czego zacząć

| Zadanie | Rezultat | Przed kodowaniem przeczytaj |
|---|---|---|
| WG-007 — zalecane pierwsze zadanie | Porównanie słów kluczowych z modelem, bez zmiany routingu | [Karta WG-007](tasks.md#wg-007--baseline-regułowy), `evaluation.py`, taksonomia |
| WG-008 — dane | Większy, opisany zbiór i lista przeglądu; realne dane nadal niedostępne | [Karta WG-008](tasks.md#wg-008--rozbudowa-danych-i-przegląd-etykiet), `data.py`, karta danych |
| WG-009 — nauka | Materiał wyjaśniający obecny model na przykładach | [Karta WG-009](tasks.md#wg-009--jak-działa-nasz-klasyfikator), `training.py`, `specialists/intent.py` |

Weź jedno zadanie. WG-007 i WG-008 mają rozłączne główne pliki, ale aktualizacje
tablicy nadal trzeba koordynować. Zmiany wspólnej ewaluacji, taksonomii, CLI lub
typów sprawdź względem rezerwacji innych sesji. WG-010–014 są dalszymi etapami,
nie częścią dorozumianego zakresu WG-007.

## Przygotowanie i sprawdzenia

Uruchamiaj komendy z katalogu Gate. Podstawowy wariant nie wymaga PyTorch:

```bash
uv sync --locked
```

Sprawdź, czy istnieje `models/intent.joblib`. Jeżeli tak, użyj go. Jeśli nie,
możesz odtworzyć model komendą `.venv/bin/windup-gate train`.
Nigdy nie nadpisuj istniejących wag. Nowy eksperyment zapisuj przez `--output`
pod nową nazwą. Raport walidacji można odtworzyć przez:

```bash
.venv/bin/windup-gate evaluate --output reports/opencode-validation.json
```

Nie używaj końcowego testu do projektowania reguł ani strojenia. Testy kodu
uruchamiaj poleceniami z AGENTS.md; obejmują kontrakty i błędy, nie dowód
realnej jakości modelu. W odbiorze podaj wynik faktycznie wykonanych sprawdzeń.

Detektor języka jest już zintegrowany w WG-006. Nie jest potrzebny do WG-007–009.
Jeśli pracujesz nad jego integracją, użyj instrukcji
[README](../README.md#istniejący-detektor-języka) i
[raportu integracji](../reports/language-integration.md).
Źródła detektora trafiają na `PYTHONPATH`, a `--language-model` wskazuje lokalne wagi.
Opcjonalne zależności instaluje `uv sync --locked --extra language`.
Zwykłe `uv sync` może je usunąć. Brak przygotowanego detektora oznacza pominięcie
opcjonalnego testu rzeczywistych wag, a nie budowanie modelu zastępczego.

## Kontrakt istniejącego kodu

To obecne API, nie lista planowanych nowych funkcji. W razie rozbieżności
sprawdź implementację i zaktualizuj dokumentację w ramach uzgodnionego zakresu.

- `Request(text, target_text=None, requires_history=False)`.
- Specjalista implementuje `predict(text) -> Prediction`.
- `Prediction`: `label`, `score`, `margin`, `model_version`, `scores`, `has_features`, `score_kind`.
- `Gate(intent, policy=None, *, language=None).analyze(request) -> Decision`.
- `Decision`: `request`, `route`, `reason`, `handler`, `prediction`, `completed`, `result`, `error`.
- `LanguagePrediction`: `language`, `best_language`, `confidence`, `margin`, `uncertain`,
  `calibrated`, `model_version`, `score_kind`.
- `WindupLanguageSpecialist(model_path).predict(text) -> LanguagePrediction`; ładowanie
  źródeł i wag jest leniwe, przy pierwszym potrzebnym wywołaniu.
- `result` ma wartość inną niż `None` wyłącznie dla udanego lokalnego wykonania,
  niezależnie od predykcji intencji. W JSON pole jest obecne także jako `null`.
- `Policy(min_score=0.6, min_margin=0.15, max_chars=20000)`.
- `train(directory, output, seed=42)` — wyłącznie trening; nie nadpisuje modelu.
- `evaluate(directory, model_path, split="validation", ...)` — ocena intencji, nie całego zadania.

Rozszerzenia kontraktu udokumentuj tutaj. Nie zmieniaj znaczenia istniejącego `completed`.
W trakcie wspólnej pracy uzgodnij zmiany interfejsu z właścicielem zależnego zadania.

Zachowaj następujące własności:

- `assist` i `fallback` zawsze mają `completed=False`; wskazanie wykonawcy nie jest wykonaniem.
- Zachowujemy oryginalne żądanie. Przekroczenie limitu daje jawne odstąpienie,
  nie klasyfikację po cichym obcięciu.
- Do detektora trafia `target_text`, nie całe polecenie. `und`/niepewność upstream
  muszą pozostać odstąpieniem; nie zastępuj ich `best_language`.
- Ładowanie adaptera językowego jest leniwe. Podstawowe testy i routing intencji
  nie wymagają jego wag, PyTorch ani sieci.
- Model intencji i detektor języka mają osobne identyfikatory i znaczenie score.
- `evaluate()` ocenia intencje. Jego coverage nie jest udziałem wykonanych zadań.

## Przykładowe polecenie dla OpenCode

Poniższy tekst można wkleić do nowej sesji otwartej w katalogu projektu:

```text
Pracujesz w projekcie WindUp Gate: edukacyjnej warstwie małych lokalnych
klasyfikatorów przed ewentualnym LLM. Przeczytaj AGENTS.md, README.md,
docs/project-scope.md, KANBAN.md, docs/opencode-handoff.md oraz kartę WG-007
w docs/tasks.md. Sprawdź git status i aktywne rezerwacje.

Jeśli WG-007 jest wolne, przejmij je jako OpenCode w KANBAN.md przed kodowaniem.
Jeżeli jest zajęte, zgłoś ten fakt i nie zmieniaj plików jego właściciela.
Wykonaj wyłącznie WG-007: deterministyczny baseline słów kluczowych, testy
i porównanie z modelem na walidacji. Zakres: baselines.py, evaluation.py,
testy baseline/raportu i nowy raport. Szczegóły oraz kryteria odbioru są w karcie.

Nie zmieniaj Gate, Policy, etykiet ani danych demo. Nie buduj nowego detektora
języka: istniejący model użytkownika jest już podłączony. Nie dodawaj LLM,
sieci przy predykcji ani wykonywania tłumaczeń. Nie nadpisuj istniejących wag.
Nie przeglądaj końcowego testu do projektowania reguł i nie oceniaj go podczas
tego zadania. Zachowaj cudze zmiany i zgodność istniejącego API/JSON.

Dodaj testy zachowania i błędów, uruchom sprawdzenia z AGENTS.md.
Zapisz porównanie i ograniczenia syntetycznych danych. Na koniec zaktualizuj
tablicę: rezultat, rzeczywiste wyniki sprawdzeń, link do raportu i ograniczenia.
Nie twierdź, że klasyfikacja intencji oznacza zakończenie zadania.
```
