# WindUp Gate — karty zadań

Wymagania dla wykonawcy, który nie zna wcześniejszej rozmowy. Statusy i właściciele
są wyłącznie w [KANBAN.md](../KANBAN.md). Ten plik opisuje zakres, nie rezerwuje pracy.
Kontekst systemu: [project-scope.md](project-scope.md). Kontrakt istniejącego kodu:
[opencode-handoff.md](opencode-handoff.md#kontrakt-istniejącego-kodu).

## Wspólny sposób odbioru

1. Przejmij jedno wolne zadanie i zarezerwuj wymienione pliki w tablicy.
2. Zaimplementuj jego wymagania bez dodawania funkcji z późniejszych kart.
3. Dla zmian kodu dodaj testy zachowania, w tym błędów. Uruchom sprawdzenia z
   [AGENTS.md](../AGENTS.md). Testy aplikacji to co innego niż końcowa ocena modelu.
4. Zapisz wyniki i ograniczenia. Zaktualizuj instrukcje, jeżeli zmieniło się użycie.
5. Dopisz dowód w tablicy; przy niepełnym odbiorze użyj „Przegląd”, nie „Gotowe”.

Nie nadpisuj `models/intent.joblib`, wag detektora ani cudzych zmian.
Eksperymenty zapisuj pod nowymi nazwami. Nie uruchamiaj `evaluate --split test`
przy rutynowej pracy. Dla samych zmian dokumentacji sprawdź treść i linki;
pełny trening ani ponowna ocena modelu nie są potrzebne.

## WG-007 — baseline regułowy

**Po co:** sprawdzić, czy mały model daje przewagę nad prostym rozpoznawaniem słów
kluczowych. Wynik może pokazać, że dla części zadań reguły wystarczą.

**Wejście:** obecne pięć etykiet, taksonomia, `data/demo/train.jsonl`, walidacja oraz
istniejący `evaluate()`. Nie czytaj treści końcowego testu do projektowania reguł.

**Pliki:** nowy `src/windup_gate/baselines.py`, `src/windup_gate/evaluation.py`,
nowe `tests/test_baselines.py`, odpowiednie testy raportu w `tests/test_pipeline.py`,
nowy raport `reports/rule-baseline-validation.md` i odpowiadający JSON.
Nie zmieniaj `Gate`, `Policy`, taksonomii, danych demo ani trenowania modelu.

**Wymagania:**

1. Dodaj deterministyczną klasyfikację regułową tekstu do jednej z obecnych etykiet.
   Opisz reguły: normalizację, granice słów, kolejność/konflikty i negację.
   Opieraj pierwszą wersję na taksonomii i `train`, nie na ID konkretnych rekordów.
2. Pusty lub nierozpoznany tekst daje `other`. Konflikt wskazujący kilka zadań
   również daje `other`. Uwzględnij jawne przypadki typu „nie tłumacz” i
   „przetłumacz i streść”; nie obiecuj pełnego rozumienia polskiej negacji.
3. Zwracaj etykietę i identyfikatory dopasowanych reguł, przydatne do analizy błędów.
   Nie wymyślaj prawdopodobieństwa `1.0` dla dopasowania słowa. To reguły, nie
   skalibrowany model. Wystarczy mały własny typ wyniku; nie zmieniaj `Prediction`.
4. Rozszerz raport `evaluate()` o pole `baselines` z częścią `keyword`.
   Zachowaj obecne pola i ich znaczenie oraz dotychczasowe argumenty CLI.
5. W części regułowej zapisz wersję reguł, accuracy, macro-F1, metryki klas,
   macierz pomyłek i błędy z dopasowaniami. Użyj tych samych rekordów i kolejności
   etykiet co dla modelu. Istniejący baseline najczęstszej klasy nadal pochodzi z `train`.
6. Dla reguł pokaż także udział wyników innych niż `other` oraz ich poprawność;
   nazwij je np. `non_other_coverage` i `non_other_accuracy`. Przy zerowej liczbie
   takich wyników poprawność to `null`. Wyjaśnij, że to nie to samo co przyjęcie
   wyniku modelu przez progi ani wykonanie zadania.
7. Uruchom porównanie na `validation` bez zmiany istniejących wag. Raport ma
   wymieniać źródła danych, fingerprint, wersje i ograniczenia. Nie wymagamy,
   żeby model lub reguły „wygrały”.

**Odbiór:** testy obejmują pojedyncze intencje, nieznany tekst, konflikt, negację,
wielkość liter/granice słów, deterministyczność oraz poprawne pola raportu, w tym
brak zaakceptowanych wyników. Dotychczasowy routing i raport nadal działają.
Raport porównuje trzy metody: model, najczęstsza klasa, reguły; nie przedstawia
walidacji syntetycznej jako skuteczności na rzeczywistych wiadomościach.

**Zakończenie:** link do nowego raportu i wynik sprawdzeń w tablicy.
Jeżeli po obejrzeniu walidacji zmienisz reguły, opisz to jako dobór na walidacji;
nie przedstawiaj kolejnego wyniku jako niezależnej oceny końcowej.

## WG-008 — rozbudowa danych i przegląd etykiet

**Po co:** obecny model uczy się na 60 syntetycznych przykładach. Kolejne
architektury nie zastąpią reprezentatywnych danych i poprawnych etykiet.

**Wejście:** taksonomia v1 i karta danych. Rzeczywiste wiadomości użytkownika
nie zostały jeszcze dostarczone. Nie korzystaj z prywatnych danych repo detektora.

**Pliki:** nowe `data/curated/`, aktualizacja `docs/dataset-card.md`,
nowy `docs/data-review.md`. Publiczne dane mają być neutralne i pozbawione
danych prywatnych. Prywatny zbiór, jeżeli powstanie, zostaje w `data/private/`.
Nie zmieniaj demo, `LABELS`, walidatora, modelu ani polityki przy okazji.

**Wymagania:**

1. Przygotuj dodatkowy zbiór w obecnym formacie. Każdy wiersz JSONL ma niepuste
   `id`, `text`, `label`, `group_id`, `source`. Pliki to `train.jsonl`,
   `validation.jsonl`, `test.jsonl`. Każdy podział zawiera wszystkie pięć klas.
2. Cel pierwszego zestawu: minimum 50 przykładów na klasę, czyli 250 łącznie.
   To rozmiar ćwiczenia, nie dowód wystarczającej reprezentatywności. Jeśli brak
   rzeczywistych danych, przygotuj jawnie syntetyczny zestaw i checklistę przeglądu
   dla Macieja. Nazwa katalogu `curated` nie oznacza automatycznie danych realnych
   ani sprawdzonych przez człowieka.
3. Rozszerz różnorodność sformułowań i długości. Uwzględnij pytania, literówki,
   negacje, zadania złożone, nieobsługiwane i zależne od historii. Etykietuj zgodnie
   z taksonomią, nie zgodnie z tym, co obecny model potrafi odgadnąć.
4. Grupuj parafrazy, warianty i rodziny szablonów przed podziałem. Warianty
   istniejących przykładów nie mogą trafić do innego podziału niż ich pierwowzory.
   Nie kopiuj demo do nowego zbioru; opisz ewentualne powiązania między zbiorami.
5. Ustal odtwarzalny podział grupami, orientacyjnie 60/20/20, z zapisanym seedem
   i rzeczywistymi liczebnościami. Zamroź podziały przed eksperymentami.
   Późniejsze dopisywanie danych wymaga nowej wersji zbioru.
6. Karta danych podaje autorstwo, sposób powstania, źródła i warunki użycia,
   liczebności, język poleceń, grupowanie, seed oraz fingerprinty. Przegląd człowieka
   oznacz jako oczekujący, dopóki rzeczywiście nie nastąpi.
7. W `docs/data-review.md` zapisz pytania o niejednoznaczne etykiety i instrukcję
   przeglądu. Nie zmieniaj definicji klas, żeby usunąć błędy modelu. Jeżeli potrzebna
   jest zmiana taksonomii, opisz propozycję i zależności jako osobne zadanie.
8. Uruchom istniejący `load_splits()` do kontroli struktury, duplikatów i grup.
   Nie trenuj automatycznie następnego modelu ani nie oceniaj końcowego testu.

**Odbiór:** poprawny format, komplet klas w podziałach, brak przeciekających grup,
udokumentowane pochodzenie i ograniczenia oraz lista przeglądu. Zbiór syntetyczny
może zakończyć zadanie przygotowania danych, ale nie usuwa blokady „brak danych realnych”.
Przy brakującym przeglądzie zaznacz to w dowodzie; nie deklaruj gotowości do
wiarygodnej oceny rzeczywistych zastosowań.

## WG-009 — jak działa nasz klasyfikator

**Po co:** dać Maciejowi materiał do nauki oparty na działającym kodzie projektu.

**Pliki:** nowy `docs/learning-notes.md`, link z README. Forma: Markdown
z krótkimi uruchamialnymi przykładami; Jupyter i nowe zależności nie są potrzebne.
Nie zmieniaj modelu, danych, progów ani CLI.

**Treść i odbiór:**

- Wyjaśnij na jednym polskim poleceniu: tekst -> tokeny -> unigramy/bigramy ->
  wektor TF-IDF -> wagi regresji -> score klas -> margin -> decyzja polityki.
- Wyjaśnij, co jest wyuczone, co jest ręczną regułą, co jest zapisane w joblib
  oraz czym różnią się `fit`, `predict` i `predict_proba`.
- Pokaż odczyt słownika przez krok `tfidf` oraz wag przez krok `classifier`
  istniejącego pipeline. Nie zgaduj indeksu klasy: korzystaj z `classes_`.
  Zaznacz, że waga cechy nie jest pełnym wyjaśnieniem znaczenia zdania.
- Pokaż obcy dla słownika tekst i błędną pewną predykcję z istniejącego raportu
  walidacyjnego. Wyjaśnij brak kalibracji oraz różnicę między accuracy,
  macro-F1, coverage i poprawnością przyjętych predykcji.
- Wyjaśnij podział train/validation/test, przeuczenie i przeciek parafraz.
  Nie otwieraj końcowego testu w celu przygotowania przykładów.
- Porównaj klasyfikator intencji z osobnym detektorem języka i z LLM:
  różne zadania, różne wyjścia, brak generowania tekstu w obecnym Gate.
- Każdy przykład ma wskazywać wymagane lokalne pliki. Sprawdź fragmenty
  na obecnym środowisku; zapisuj rzeczywiście otrzymane wyniki lub oznacz
  liczby jako ilustrację, nigdy jako wykonany pomiar.

**Zakończenie:** link do materiału, informacja o sprawdzeniu fragmentów i ograniczeniach.

## WG-010 — kalibracja i dobór progów

**Zależność:** WG-008; oceń też jakość/przegląd danych. Sama większa liczba syntetycznych
przykładów nie dowodzi wiarygodnej kalibracji w rzeczywistym użyciu.

**Planowany zakres:** `training.py`, `specialists/intent.py`, `evaluation.py`,
testy pipeline/polityki, osobny raport i nowe artefakty. Konkretny protokół i zajęte
pliki zapisz przed przejęciem. Nie kalibruj przy okazji detektora języka.

**Wymagania przyszłego zadania:** porównaj wariant niekalibrowany z kalibracją,
np. na wewnętrznych foldach części treningowej. Zachowaj grupy także w foldach;
słownik i wszystkie uczone kroki dopasuj wyłącznie na treningowej części foldu.
Progi wybieraj na walidacji według jawnego celu poprawności i coverage.
Nie dopasowuj kalibratora i nie oceniaj go jako niezależnego na tych samych rekordach.

**Odbiór:** odtwarzalny protokół, krzywa poprawność/coverage, liczebności próbek,
ocena kalibracji i jawne przypadki błędów. Zapisz nowe metadane/wersję artefaktu
i znaczenie `score_kind`, utrzymując odczyt dotychczasowych artefaktów albo
dokumentując migrację. Jeśli cel jakości nie jest osiągalny, raport ma to pokazać.
Końcowy test dopiero po zamrożeniu wariantu i protokołu; nie jest rutynowym krokiem tej karty.

## WG-011 — czas i zasoby

**Zależność:** WG-005 ukończone. Zadanie pozostaje w backlogu do przejęcia z tablicy.

**Planowany zakres:** nowy `benchmarks/benchmark_gate.py`, opis użycia oraz
`reports/performance.md` i surowy JSON. Bez zmiany aplikacji i jej polityki.

**Wymagania:** oddziel czas uruchomienia procesu, ładowania modelu intencji,
zimnego pierwszego wywołania detektora języka oraz rozgrzanej predykcji.
Zmierz p50/p95 na stałym zestawie jawnych lokalnych wejść, podaj rozgrzewkę,
liczbę powtórzeń, długości tekstów, sprzęt, system, wersje, CPU/wątki i metodę pomiaru.
Osobno raportuj pamięć procesu oraz rozmiar wag na dysku — to różne wielkości.

**Odbiór:** pomiary odtwarzalne, bez sieci podczas benchmarku. Ścieżka rzeczywistych
wag językowych opcjonalna i jawna; brak konfiguracji oznacza „nie zmierzono”,
nie wynik `0 ms`. Nie używaj końcowego testu modelu jako zestawu benchmarkowego.
Nie wyciągaj wniosków o oszczędnościach względem LLM bez porównywalnego pomiaru LLM.

## WG-012 — wybór instrukcji/narzędzi

**Zależność:** WG-008 oraz opis konkretnego małego katalogu. To nowe zadanie
klasyfikacyjne; pięć obecnych intencji nie wystarcza do wyboru dowolnego narzędzia.

**Planowany zakres:** osobny katalog danych, moduł selekcji i evaluator,
testy, opis katalogu oraz raport. Na początek 5–10 jednoznacznie opisanych pozycji.
Przed kodowaniem wpisz nazwy plików i proponowany kontrakt w tablicę/handoff.

**Wymagania:** wejście to oryginalne żądanie i katalog; wyjście to uporządkowane ID
kandydatów z powodem/oceną albo jawne odstąpienie od selekcji.
To wskazanie kandydatów, bez wykonywania narzędzi i bez `completed=True`.
Zbiór musi zawierać przypadki z kilkoma potrzebnymi pozycjami oraz bez pasującej pozycji.

**Odbiór:** porównanie z przekazaniem całego katalogu, recall@k, kompletność zestawu
potrzebnych pozycji, liczba kandydatów i koszt kontekstu przy opisanym sposobie liczenia.
Odstąpienie nie gubi oryginału ani nie udaje pustego poprawnego wyboru.
Nie dodawaj wykonywania poleceń, integracji API, przepisywania promptów ani selekcji
instrukcji bezpieczeństwa jako zwykłych opcjonalnych pozycji.

## WG-013 — embeddingi / SetFit jako porównanie

**Zależności:** WG-008 i WG-011. Najpierw mamy z czym porównywać wynik i koszt.

**Planowany zakres:** osobny eksperyment, nowy specjalista i jego testy,
zależności opcjonalne z aktualizacją lockfile, nowe artefakty i raport.
Nie zastępuj automatycznie obecnego modelu ani domyślnego trybu lokalnego.

**Wymagania i odbiór:** wybierz jeden konkretny mały encoder, zapisz wersję,
licencję, rozmiar i wymagania. Pobranie modelu to jawny krok przygotowania,
bez pobierania przy predykcji. Porównaj na identycznych podziałach i według
tych samych metryk co TF-IDF oraz reguły; dodatkowo czas, RAM i rozmiar.
Uczenie/fit tylko na `train`, decyzje na walidacji, końcowy test odłożony.
Nie oceniaj przewagi wyłącznie na accuracy ani nie zakładaj z góry, że większy
model jest lepszy. Wynik negatywny również kończy poprawny eksperyment.

## WG-014 — wiele języków i wiele intencji

**Zależność:** WG-008 i ustalenie nowej taksonomii. To rozszerzenie zakresu,
a nie drobna poprawka obecnej regresji.

**Pierwszy rezultat:** osobna propozycja danych, etykiet, kontraktu i migracji.
Zacznij od jednego podproblemu: dodatkowy język poleceń albo wiele etykiet.
Nie wdrażaj obu naraz bez rozpisania odrębnych etapów.

**Planowane zmiany po doprecyzowaniu:** taksonomia, format danych, `types.py`,
trening/predykcja, polityka, ewaluacja i testy kompatybilności. Dopiero wtedy
rezerwujemy konkretny zakres plików.

**Odbiór propozycji:** przykłady graniczne i zależności. **Odbiór implementacji:**
metryki osobno dla języków lub metryki wieloetykietowe (m.in. per-label recall
i exact match), jawne zachowanie dla zadań częściowo obsługiwanych i historia migracji.
Parafrazy i tłumaczenia tego samego przykładu nie mogą przeciekać między podziałami.
Rozpoznanie kilku intencji nie oznacza wykonania kilku zadań; dotychczasowy
`completed` zachowuje swoje znaczenie.

## WG-016 — gotowa publikacja open-source rdzenia

**Po co:** opublikować działający, śledzony w Gicie rdzeń projektu jako publiczne
repozytorium na licencji GPLv3, bez eksperymentalnych dodatków i cudzych danych.

**Wejście:** tracked rdzeń HEAD (kod, dane demo, dokumenty WG-015); publiczne
repozytorium `MoviaQ/windup-gate` na licencji GPLv3. Nie kopiuj niezintegrowanych
prac z innych checkoutów ani ich danych.

**Pliki:** `README.md`, `LICENSE`, `pyproject.toml`, `.gitignore`, `.github/workflows/`,
`CONTRIBUTING.md`, `docs/release.md`, `docs/project-scope.md`, `docs/tasks.md`,
`KANBAN.md`. Bez zmian kodu aplikacji, danych demo, wag i progów.

**Wymagania:**

1. Dokumentacja opisuje faktycznie publikowany kod, nie niezintegrowane funkcje
   z innych checkoutów. Backlog (WG-007–014) jest wyraźnie oddzielony od opisu
   działającej wersji.
2. `LICENSE` zawiera pełny tekst GPLv3 z oficjalnego źródła; `pyproject.toml`
   deklaruje licencję i adres repozytorium, bez zmyślonych autorów i wyników.
3. README jest po polsku i zawiera: cel (małe lokalne modele wspierające końcowy
   LLM), status i ograniczenia syntetycznych danych, instalację przez `uv`,
   kompletne działające przykłady CLI, testy, informację o braku domyślnej sieci
   oraz licencję i odnośniki do dokumentacji.
4. CI sprawdza to samo co lokalne komendy z `AGENTS.md`; CD na opublikowane
   wydanie GitHub dokleja sdist/wheel do tego wydania, bez PyPI i sekretów.
5. Nowe pliki nie zawierają sekretów ani absolutnych lokalnych ścieżek.

**Odbiór:** wszystkie komendy z `AGENTS.md` są zielone, workflow jest logicznie
poprawny, a instrukcja wydania działa. Bez commitów i pushy w ramach zadania.
