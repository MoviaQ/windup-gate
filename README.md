# WindUp Gate

Hobbystyczny projekt: małe lokalne modele wspierają duży LLM, który jest końcowym
wykonawcą zadań. Gate przejmuje rutynowe decyzje (rozpoznanie intencji i języka),
zanim żądanie trafi do LLM. Integracja z LLM nie jest obecnie zaimplementowana:
Gate nie generuje odpowiedzi i nie wywołuje zewnętrznych API.

Pierwsza wersja działa: TF-IDF + regresja logistyczna rozpoznaje pięć intencji i zwraca
decyzję `assist` lub `fallback`. Opcjonalny adapter istniejącego
[Wind-Up Language Recognition](https://github.com/MoviaQ/windup-language-recog)
potrafi też zakończyć rozpoznawanie języka lokalnie: `local`, `completed=true`.

Zacznij od [zakresu projektu](docs/project-scope.md): wyjaśnia cel, obecny stan,
przepływ decyzji i granice pierwszej wersji. Następnie zobacz
[tablicę zadań](KANBAN.md) i [szczegółowe karty zadań](docs/tasks.md).
[Instrukcja dla OpenCode](docs/opencode-handoff.md) zawiera kontrakt API i gotowe
polecenie do nowej sesji. Szerszy kontekst nauki jest w [planie](plans/windup-gate-plan.md).

## Start

Potrzebne: Python 3.11+ i `uv`. Uruchamiaj polecenia w katalogu projektu.

```bash
uv sync --locked
.venv/bin/windup-gate train
.venv/bin/windup-gate analyze 'Przetłumacz proszę wiadomość na angielski'
.venv/bin/windup-gate analyze 'qxzvjk 987654321'
```

Instalacja wymaga pobrania zależności. Trening i predykcja na dołączonych danych są lokalne
i nie wymagają sieci ani GPU. `uv.lock` zapisuje wersje zależności.

Model powstaje dopiero po `train` (domyślnie `models/intent.joblib`) i nie jest
częścią repozytorium — po sklonowaniu wykonaj trening albo podaj własną ścieżkę:

```bash
.venv/bin/windup-gate train --output models/intent-v2.joblib
```

Trening nie nadpisuje istniejącego modelu. Wagi są ignorowane przez Git i można je
odtworzyć z danych. Brak modelu przy `analyze` zwraca jawny fallback oraz komunikat na stderr.

## Co oznacza wynik

- `prediction.label`: przewidywana intencja (`translate`, `summarize`, `code_help`,
  `detect_language` lub `other`).
- `score`: niekalibrowana estymata prawdopodobieństwa, a nie gwarancja poprawności.
- `margin`: różnica wyniku pierwszej i drugiej klasy.
- `route: assist`: sugerowana ścieżka; zadanie nadal musi wykonać inny komponent.
- `route: fallback`: Gate odstępuje od kierowania zadania; `reason` wyjaśnia przyczynę.
- `route: local`: istniejący detektor wykonał rozpoznawanie języka; `result` zawiera wynik.
- `completed`: `true` wyłącznie dla poprawnie zakończonego lokalnego zadania;
  `assist` i `fallback` mają zawsze `false` oraz `result: null`.
- `request`: oryginalne żądanie, zachowane bez skracania.

Domyślne progi wynoszą `min_score=0.6`, `min_margin=0.15`. Są demonstracyjne,
nie zostały skalibrowane. Możesz je zmieniać przez `--min-score` i `--min-margin`.
Niższy próg zwiększa liczbę zaakceptowanych predykcji, ale może zwiększyć liczbę pomyłek.

```bash
.venv/bin/windup-gate analyze 'Jaki to język?' --target-text 'Bonjour tout le monde'
.venv/bin/windup-gate analyze 'Zrób to samo' --requires-history
```

Pierwsza komenda zwraca fallback bez konfiguracji opcjonalnego adaptera opisanej poniżej.
Druga jawnie wskazuje, że potrzebna jest historia rozmowy. Gate sam nie rozpoznaje
niezawodnie wszystkich zależności od historii, wielu intencji ani nieznanych języków.
Puste żądania i wejścia dłuższe niż 20 000 znaków również trafiają do fallbacku.

## Istniejący detektor języka

Nie trenujemy drugiego detektora. Adapter używa `LanguageDetector.predict_details()`
z Twojego repo `MoviaQ/windup-language-recog`, przekazuje `target_text` i zachowuje jego
decyzję `und`. Nie zastępuje jej najbardziej prawdopodobnym językiem.

Przygotowanie: jawnie sklonuj publiczne repo detektora obok katalogu Gate
i doinstaluj opcjonalne zależności. Gate nie pobiera źródeł ani wag automatycznie:

```bash
git clone https://github.com/MoviaQ/windup-language-recog.git ../windup-language-recog
uv sync --locked --extra language
```

Działające polecenie z katalogu Gate:

```bash
PYTHONPATH="../windup-language-recog" \
  .venv/bin/windup-gate analyze 'Jaki to język?' \
  --target-text 'Nie mogę zalogować się do mojego konta po zmianie hasła.' \
  --language-model '../windup-language-recog/model.pt'
```

Wagi `model.pt` pochodzą ze sklonowanego repo; Gate nie pobiera ich z sieci.
Przetestowana wersja źródeł to `6504cfb2efe23eaf7ccc2009b3c97881e1e00309`; szczegóły
wag, licencji i weryfikacji są w [raporcie integracji](reports/language-integration.md).
Repo nie jest jeszcze instalowalnym pakietem Pythona, dlatego jego katalog umieszczamy
na `PYTHONPATH`, zgodnie z instrukcją upstream. Wczytuj wyłącznie zaufany kod i wagi.

Zależności PyTorch/ftfy i wagi ładowane są dopiero przy zaakceptowanej intencji
`detect_language` z podanym tekstem. Bez `--language-model` działa dotychczasowy routing.
Uruchamianie `uv sync` bez `--extra language` może usunąć opcjonalne zależności.

Adapter wymaga kalibracji w checkpointcie i respektuje niepewność upstream. Jego confidence
jest osobnym wynikiem niż score intencji; nie daje gwarancji poprawności na nowych danych.
Tekst bez wystarczających liter, brak wag/zależności i odrzucenie modelu powodują fallback.
Adapter odrzuca także wejście przekraczające limit upstream (v21: 2000 znaków), również
po normalizacji, aby nie klasyfikować po cichu uciętego fragmentu. Oryginał nadal jest w `request`.

Wynik lokalny zawiera `result.language`, `best_language`, `confidence`, `margin`,
`uncertain`, `calibrated`, `score_kind` i identyfikator SHA-256 pliku wag.
`prediction` nadal opisuje intencję. Pole `error` wyjaśnia błędy przygotowania/modelu;
CLI wypisuje je również na stderr.

## Dane i ewaluacja

`data/demo/` zawiera **100 przykładów syntetycznych przygotowanych przez Codex**:
60 treningowych, 20 walidacyjnych i 20 testowych. To dane do demonstracji procesu,
nie rzeczywiste wiadomości użytkownika. Pochodzenie i ograniczenia opisuje
[karta danych](docs/dataset-card.md); reguły etykietowania opisuje [taksonomia](docs/taxonomy.md).

```bash
.venv/bin/windup-gate evaluate --output reports/my-validation.json
```

Domyślnie oceniany jest zbiór walidacyjny. Raport zawiera macro-F1, metryki klas,
macierz pomyłek, baseline najczęstszej klasy oraz coverage i poprawność zaakceptowanych
predykcji intencji. Te dwie ostatnie miary dotyczą **klasyfikacji**, nie zakończonych zadań.
Zobacz [raport startowy](reports/demo-validation.md).

Końcowy zbiór testowy jest odłożony i nie został użyty do strojenia ani oceny startowej.
Do jednorazowej oceny zamrożonego wariantu służy `evaluate --split test`.
Nie dobieraj progów na końcowym teście. Po wykorzystaniu go do poprawiania modelu
potrzebny będzie nowy odłożony zbiór.

Wyniki syntetycznego demo nie określają jakości na prawdziwych danych. Szczególnie
krótkie, złożone lub nietypowo sformułowane żądania mogą zostać błędnie sklasyfikowane
także z wysokim score. Wersja startowa nie osiąga celów jakości z planu.

## Użycie z Pythona

```python
from pathlib import Path

from windup_gate import Gate, Request
from windup_gate.specialists.intent import IntentClassifier
from windup_gate.specialists.language import WindupLanguageSpecialist

intent = IntentClassifier.load(Path("models/intent.joblib"))
language = WindupLanguageSpecialist(Path("../windup-language-recog/model.pt"))
gate = Gate(intent, language=language)  # katalog repo detektora musi być na PYTHONPATH
decision = gate.analyze(Request("Jaki to język?", target_text="Nie mogę się zalogować."))
print(decision.route, decision.reason)
```

Wczytuj wyłącznie własne lub zaufane pliki `joblib`: ten format używa pickle i podczas
odczytu może wykonywać kod. Model wymaga tej samej wersji scikit-learn; w innym środowisku
należy odtworzyć środowisko z lockfile albo ponownie wytrenować model.
Zobacz [oficjalne zasady zapisu modeli scikit-learn](https://scikit-learn.org/stable/model_persistence.html).

## Sprawdzenie zmian

```bash
.venv/bin/python -m pytest -q --cov=windup_gate --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pyright
uv build
```

Testy sprawdzają zachowanie kodu. Ich pokrycie nie mierzy skuteczności klasyfikatora.
Domyślnie test rzeczywistych wag jest pomijany. Aby uruchomić go offline po przygotowaniu:

```bash
PYTHONPATH="../windup-language-recog" \
  WINDUP_LANGUAGE_TEST_MODEL="../windup-language-recog/model.pt" \
  .venv/bin/python -m pytest -q tests/test_language.py
```

## Układ

```text
src/windup_gate/
  types.py               # Request, Prediction, Decision i protokół specjalisty
  data.py                # JSONL, walidacja podziałów, fingerprint danych
  training.py            # trening i zapis modelu
  specialists/intent.py  # odczyt modelu i predykcja
  specialists/language.py # adapter istniejącego detektora, ładowany na żądanie
  policy.py              # progi i powody odstąpienia od decyzji
  gate.py                # routing i wykonanie lokalnej identyfikacji języka
  evaluation.py          # raport klasyfikacji
  cli.py                 # train / analyze / evaluate
```

Zamiast osobnych skryptów z pierwotnego planu używamy jednego CLI, żeby nie dublować
logiki treningu i ewaluacji. Serwer HTTP, LLM i frontend nie są wymagane na tym etapie.

## Dokumentacja

- [Zakres projektu](docs/project-scope.md) — cel, obecny stan, przepływ decyzji, granice.
- [Karty zadań](docs/tasks.md) — wymagania WG-007–016; statusy tylko w [KANBAN.md](KANBAN.md).
- [Przejęcie pracy w OpenCode](docs/opencode-handoff.md) — kontrakt API i gotowe polecenie.
- [Taksonomia](docs/taxonomy.md) — reguły etykietowania pięciu intencji.
- [Karta danych](docs/dataset-card.md) — pochodzenie i ograniczenia danych demo.
- [Jak współtworzyć](CONTRIBUTING.md) — zgłaszanie zmian i wymagane sprawdzenia.
- [Jak wydać wersję](docs/release.md) — kroki publikacji wydania GitHub z paczkami.

## Licencja

Ten program jest wolnym oprogramowaniem na licencji
[GNU General Public License v3 (lub późniejszej)](LICENSE).
Pełny tekst licencji jest w pliku `LICENSE`; internetowa kopia:
<https://www.gnu.org/licenses/gpl-3.0.html>.
Repozytorium publiczne: <https://github.com/MoviaQ/windup-gate>.
