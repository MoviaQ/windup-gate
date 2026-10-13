# WindUp Gate — plan nauki i wdrożenia

Data: 8 października 2026 r.
Status: implementacja rozpoczęta 9 października 2026 r.; postęp poniżej.

Charakter: projekt hobbystyczny, edukacyjny i potencjalnie open source.

## Postęp implementacji — 2026-10-09

Aktualizacja 2026-10-10: model języka już istnieje w
[MoviaQ/windup-language-recog](https://github.com/MoviaQ/windup-language-recog).
WG-006 integruje jego API i wagi, bez treningu kolejnego detektora. Adapter,
lokalny handler w `Gate.analyze` i opcjonalne CLI zostały dodane; szczegóły:
[raport integracji](../reports/language-integration.md). Poniższa tabela zachowuje
stan startowy z 9 października, a aktualny status pokazuje Kanban.

Aktualne zadania i właściciele: [KANBAN.md](../KANBAN.md). Instrukcja uruchomienia:
[README.md](../README.md). Plan pozostaje kierunkiem rozwoju; prototyp nie oznacza
ukończenia całego MVP ani osiągnięcia docelowej jakości.

| Etap | Stan techniczny |
|---|---|
| 0 | Środowisko, repozytorium lokalne, pakiet i CLI gotowe; nauka użytkownika pozostaje osobną ścieżką |
| 1 | Taksonomia i 100 przykładów syntetycznych demo; docelowe dane nadal do zebrania |
| 2 | TF-IDF + regresja logistyczna, zapis/odczyt; baseline większościowy gotowy, regułowy do zrobienia |
| 3 | Progi i fallback działają; bez kalibracji i niezawodnego rozpoznawania nieznanych zadań |
| 4 | Wspólny kontrakt gotowy; detektor języka i lokalny handler do zrobienia (WG-006) |
| 5 | CLI `train`, `analyze`, `evaluate` działa; obsługuje `assist` i `fallback`, jeszcze bez `local` |
| 6 | Raport walidacji demo gotowy; cele jakości, wydajność i końcowy test pozostają otwarte |

Zmiana organizacyjna: wspólne CLI zastępuje osobne skrypty treningu i ewaluacji, aby
nie dublować logiki. [Raport startowy](../reports/demo-validation.md) pokazuje także
błędną predykcję z wysokim score; dane syntetyczne nie dowodzą realnej skuteczności.

## 1. Co budujemy

WindUp Gate to lokalna biblioteka, która używa małych klasyfikatorów do rozpoznawania żądań i wybierania dalszej ścieżki obsługi. Klasyfikator zwraca etykiety i wyniki liczbowe; nie generuje odpowiedzi tekstowej jak ChatGPT.

Docelowy przepływ:

```text
Żądanie użytkownika
        |
        v
Reguły + potrzebne mini klasyfikatory
        |
        v
Polityka decyzji
        |
        +--> lokalny handler, jeśli potrafi wykonać całe zadanie
        |
        +--> wybrane narzędzia i instrukcje dla LLM
        |
        +--> fallback: pełna ścieżka obsługi, gdy Gate nie wie
```

Przykład: prośba „jaki to język?” może zostać obsłużona lokalnie. Prośba „przetłumacz ten tekst” może zostać sklasyfikowana lokalnie, ale samo tłumaczenie wymaga osobnego wykonawcy. Rozpoznanie intencji nie oznacza wykonania zadania.

Hipoteza projektu: część rutynowych decyzji da się podejmować lokalnie, szybciej lub z mniejszym kosztem niż przez dodatkowe wywołanie generatywnego modelu. To hipoteza do zmierzenia, a nie obietnica wyników.

## 2. Zakres pierwszej wersji

Pierwszy prototyp ma działać w terminalu, na CPU, bez wymagania płatnego API. Pobranie bibliotek lub gotowych wag może wymagać internetu; późniejsze wnioskowanie ma działać offline.

MVP obejmuje:

- klasyfikator kilku intencji trenowany na własnych przykładach;
- drugi specjalista: identyfikacja języka;
- wspólny format wyników;
- decyzję `local`, `assist` albo `fallback`;
- obsługę niepewności, nieznanych i złożonych żądań;
- raport jakości, czasu działania i rozmiaru modeli;
- opcjonalny eksperyment z wyborem instrukcji/narzędzi dla agenta.

Na początku pomijamy automatyczną kompresję treści prompta, setki modeli, panel WWW, serwer produkcyjny i trening dużego modelu od zera. Oryginalny tekst żądania pozostaje dostępny dla wykonawcy.

## 3. Podstawy AI potrzebne do projektu

Nie trzeba najpierw opanować całej dziedziny. Każde pojęcie warto poznać przez mały eksperyment.

| Pojęcie | Znaczenie w WindUp Gate | Ćwiczenie |
|---|---|---|
| Uczenie nadzorowane | Model uczy się z par: tekst i poprawna etykieta | Oznacz kilkadziesiąt własnych próśb |
| Cechy | Liczbowa reprezentacja tekstu | Zobacz wektor TF-IDF dla dwóch zdań |
| Parametry i trening | Dopasowanie wag na podstawie przykładów | Wytrenuj regresję logistyczną |
| Funkcja straty | Liczba opisująca, jak źle model przewiduje podczas treningu | Porównaj wynik modelu przed i po uczeniu |
| Wnioskowanie | Użycie już wytrenowanego modelu | Zapisz model, wczytaj go i sklasyfikuj nowy tekst |
| Uogólnianie | Poprawność na nowych, niewidzianych przykładach | Testuj parafrazy i inne słownictwo |
| Przeuczenie | Zapamiętanie zbioru zamiast nauczenia się użytecznej reguły | Porównaj jakość na treningu i teście |
| Embedding | Gęsty wektor reprezentujący tekst | Porównaj podobieństwo kilku parafraz |
| Encoder i model generatywny | Encoder reprezentuje wejście; model generatywny tworzy kolejne tokeny | Rozrysuj ich wejścia i wyjścia |
| Kalibracja | Sprawdzenie, czy deklarowana pewność odpowiada częstości trafień | Porównaj wyniki modelu z rzeczywistą poprawnością |
| Routing | Wybór wykonawcy na podstawie wyników | Mapuj etykiety na lokalny handler lub fallback |

TF-IDF waży wystąpienia słów lub fragmentów tekstu; sam nie jest siecią neuronową. Regresja logistyczna, mimo nazwy, może służyć do klasyfikacji. To pełnoprawny punkt startowy w machine learning. Dokumentacja opisuje reprezentacje tekstu i ich ograniczenia: [scikit-learn — feature extraction](https://scikit-learn.org/stable/modules/feature_extraction.html).

Embeddingi mogą reprezentować podobieństwo znaczenia, lecz samo podobieństwo wektorów nie dowodzi, że dwa żądania wymagają tej samej akcji. Praktyczny punkt wejścia: [Sentence Transformers — Quickstart](https://www.sbert.net/docs/quickstart.html).

Własny klasyfikator intencji można trenować bez LLM. Gotowy encoder był wcześniej trenowany przez jego autorów, a Ty możesz użyć go do budowy swojego specjalisty. Opcjonalne użycie LLM do przygotowania danych jest osobną decyzją; nie jest wymaganiem tego planu.

## 4. Proponowane narzędzia

| Narzędzie | Rola | Kiedy |
|---|---|---|
| Python, `venv`, `pip` | Środowisko i skrypty | Od początku |
| scikit-learn | TF-IDF, klasyfikator i metryki | Pierwszy model |
| JSONL | Dane: jeden przykład w każdym wierszu | Od początku |
| pytest | Testy istotnych zachowań Gate | Przy budowie routingu |
| fastText | Gotowy detektor języka lub alternatywny klasyfikator | Drugi specjalista |
| Sentence Transformers albo SetFit | Eksperyment z reprezentacją semantyczną | Po działającym MVP |
| ONNX / kwantyzacja | Ewentualne usprawnienie wdrożenia | Dopiero po pomiarach |

Wybór Pythona jest propozycją dla nauki i prototypowania. Wersje bibliotek należy dobrać i zapisać podczas implementacji; plan nie zakłada konkretnego numeru wersji ani wymaga GPU. SetFit służy do uczenia klasyfikatorów opartych na Sentence Transformers: [dokumentacja SetFit](https://huggingface.co/docs/setfit/index).

## 5. Etapy realizacji

Etapy są celowo sekwencyjne: `0 → 1 → 2 → 3 → 4 → 5 → 6`. Eksperymenty z etapu 7 są opcjonalne. Nie ma terminu wykonania; przechodzimy dalej po spełnieniu warunków ukończenia.

### Etap 0 — środowisko i pierwsze pojęcia

**Kontekst:** katalog projektu jest pusty, nie ma jeszcze kodu ani repozytorium Git. Celem jest przygotowanie warsztatu do eksperymentów.

Zadania:

- Utworzyć lokalne repozytorium Git, środowisko Pythona i `.gitignore`.
- Dodać `pyproject.toml` oraz krótki README z celem projektu.
- Nauczyć się czytać JSONL, uruchamiać skrypt i instalować zależności w środowisku.
- Opisać własnymi słowami różnicę między treningiem, wnioskowaniem, klasyfikacją i generowaniem.

**Rezultat:** działające środowisko i `docs/learning-notes.md`.

**Weryfikacja:** skrypt odczytuje przykładowe dane i wypisuje liczbę rekordów. Potrafisz wyjaśnić, z czego model się uczy i co oddaje na wyjściu.

### Etap 1 — zadanie i zbiór danych

**Kontekst:** budujemy rozpoznawanie intencji samodzielnego żądania. Rozmowy wymagające wcześniejszych wiadomości będą początkowo kierowane do fallbacku.

Proponowana taksonomia:

| Etykieta | Znaczenie | Przykład |
|---|---|---|
| `detect_language` | Pytanie o język załączonego tekstu | „W jakim języku jest: Bonjour tout le monde?” |
| `translate` | Prośba o tłumaczenie | „Przetłumacz ten mail na polski” |
| `summarize` | Prośba o streszczenie | „Skróć ten artykuł do trzech zdań” |
| `code_help` | Pomoc z kodem | „Wyjaśnij ten błąd Pythona” |
| `other` | Pozostałe lub złożone zadanie | „Przetłumacz i napisz odpowiedź” |

`other` jest etykietą treningową. `fallback` jest decyzją systemu. Model może z dużą pewnością przewidzieć `other`, a Gate nadal powinien przekazać zadanie dalej.

Zadania:

- Zapisać definicje, przykłady i kontrprzykłady w `docs/taxonomy.md`.
- Zacząć od orientacyjnie 50–100 różnorodnych przykładów na klasę. To budżet startowy, nie gwarancja jakości.
- W pierwszym eksperymencie używać próśb po polsku; język tekstu będącego przedmiotem prośby może być inny. Rozszerzenie języków poleceń to osobny eksperyment.
- Dodać literówki, negacje, cytaty, krótkie prośby i przykłady spoza klas.
- Przechowywać `id`, `text`, `label`, `group_id` i pochodzenie przykładu.
- Podzielić dane orientacyjnie na 60% treningu, 20% walidacji i 20% testu. Zachować reprezentację klas.

**Ważne:** parafrazy tego samego przykładu, wiadomości z jednej rozmowy i warianty jednego szablonu należą do jednej grupy i jednego podzbioru. W przeciwnym razie wynik może mierzyć zapamiętanie wzorców. Wektorizer dopasowujemy wyłącznie na treningu. Test odkładamy do końcowej oceny; nie dobieramy na nim parametrów.

**Rezultat:** taksonomia, dane i zapisany podział.

**Weryfikacja:** brak duplikatów i przecieków grup między podzbiorami. Każdy rekord ma poprawną etykietę. Da się konsekwentnie rozstrzygnąć granice klas.

### Etap 2 — pierwszy własny klasyfikator

**Kontekst:** dane i etykiety są gotowe. Uczymy się całego procesu na prostym modelu, którego błędy łatwo analizować.

Zadania:

- Zbudować punkt odniesienia: reguły oparte na słowach kluczowych oraz przewidywanie najczęstszej klasy.
- Wytrenować pipeline `TF-IDF → LogisticRegression`.
- Na walidacji porównać cechy słowne i ewentualnie znakowe; ograniczyć liczbę eksperymentów.
- Zapisać model wraz z wektoryzerem, etykietami i konfiguracją.
- Dodać `train.py`, `evaluate.py` i skrypt pojedynczej predykcji.
- Przejrzeć błędne predykcje i opisać ich przyczyny.

**Rezultat:** pierwszy działający specjalista intencji.

**Weryfikacja:** zapisany model działa w nowym procesie bez treningu. Raport zawiera macro-F1, precision/recall per klasa i macierz pomyłek. Te metryki są opisane w [dokumentacji scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html).

Jeżeli reguły są równie dobre na niezależnych danych, mogą pozostać właściwym rozwiązaniem dla danej decyzji. Nauka polega również na odkryciu, kiedy model nie jest potrzebny.

### Etap 3 — niepewność i odmowa decyzji

**Kontekst:** klasyfikator wybiera jedną ze znanych etykiet nawet dla wejścia, którego nie rozumie. Gate potrzebuje możliwości odstąpienia od routingu.

Zadania:

- Zbadać wyniki `predict_proba`; nie interpretować ich automatycznie jako gwarancji poprawności.
- Na walidacji dobrać próg akceptacji oraz ewentualny wymagany odstęp między dwiema najlepszymi klasami.
- Gdy dane to uzasadniają, użyć kalibracji z oddzielnymi danymi lub walidacją krzyżową wewnątrz treningu.
- Dodać przypadki: pusty tekst, nieznany język polecenia, wiele intencji, tekst zależny od historii i przekroczony limit wejścia.
- Dla zbyt długiego tekstu zwracać fallback zamiast po cichu ucinać ważne fragmenty.

Kalibracja wymaga danych niezależnych od dopasowania klasyfikatora. Próg pewności sam w sobie nie rozwiązuje wykrywania nieznanych zadań: model może mylić się z wysoką pewnością. Źródło: [scikit-learn — probability calibration](https://scikit-learn.org/stable/modules/calibration.html).

**Rezultat:** polityka abstencji z uzasadnieniami decyzji.

**Weryfikacja:** raport pokazuje zarówno poprawność zaakceptowanych decyzji, jak i coverage, czyli odsetek wejść, które Gate zaakceptował. System odsyłający wszystko dalej ma coverage 0% i nie spełnia celu projektu.

### Etap 4 — drugi specjalista i wspólny interfejs

**Kontekst:** klasyfikator intencji już działa. Dodajemy identyfikację języka i oddzielamy predykcję od polityki wykonania.

Zadania:

- Wybrać gotowy detektor języka; kandydatem jest fastText. Dostępne są gotowe warianty wag: [fastText — language identification](https://fasttext.cc/docs/en/language-identification.html).
- Jeśli istniejący własny detektor jest dostępny, porównać go na tych samych danych; plan nie zakłada, że znajduje się w tym katalogu.
- Zdefiniować wynik specjalisty: identyfikator, etykiety, score, rodzaj score, wersja modelu i czas wykonania.
- Zdefiniować decyzję Gate: ścieżka, handler, uzasadnienie i opcjonalne identyfikatory instrukcji/narzędzi.
- Uruchamiać tylko potrzebnych specjalistów. Detektor języka nie musi pracować nad każdym żądaniem.

Rozróżniamy język polecenia od języka analizowanego tekstu. Lokalny handler `detect_language` początkowo wymaga jawnego pola z tekstem do analizy. Bez tego pola Gate może wykryć intencję, ale odsyła wykonanie dalej. Nie dodajemy na tym etapie trudnej ekstrakcji dowolnego fragmentu z rozmowy.

**Rezultat:** dwa wymienne moduły i centralna polityka decyzji.

**Weryfikacja:** osobne testy potwierdzają działanie detektora na tekście docelowym, abstencję na bardzo krótkich/niejednoznacznych wejściach oraz czytelny błąd lub fallback przy braku wag. Nie porównujemy score różnych modeli tak, jakby miały wspólną skalę.

### Etap 5 — działające MVP w terminalu

**Kontekst:** specjaliści i polityka są gotowi. Łączymy ich w bibliotekę oraz CLI.

Zadania:

- Dodać funkcję `analyze(request)` i komendę wypisującą JSON.
- Dla obsługiwanego `detect_language` wykonać lokalny handler.
- Dla `translate`, `summarize` i `code_help` zwrócić `assist` oraz sugerowaną ścieżkę. Samo wykonanie może pozostać poza MVP.
- Dla niepewnych, złożonych i nieznanych żądań zwrócić `fallback`.
- Przekazywać oryginalne żądanie bez usuwania jego szczegółów.
- Przygotować przykłady oraz testy zachowania routingu.

`fallback` w wersji offline jest wynikiem „przekaż do wykonawcy”, a nie ukrytym wywołaniem płatnego API. Wynik `assist` również nie oznacza, że zadanie zostało wykonane.

**Rezultat:** użyteczny prototyp lokalny.

**Weryfikacja:** po pobraniu zależności i modeli demo działa bez sieci. Testy obejmują poprawny handler, fallback, brak potrzebnego pola oraz brak modelu. Uruchomienie `pytest` powinno przejść; dokładną komendę CLI zapisujemy w README po implementacji.

### Etap 6 — uczciwa ocena

**Kontekst:** MVP działa. Oceniamy zamrożony model i politykę na odłożonych wcześniej danych testowych.

Zadania:

- Porównać reguły, klasyfikator i Gate z abstencją na tych samych wejściach.
- Oddzielić błędy rozpoznania intencji od błędów wykonania lokalnego handlera.
- Zmierzyć medianę i p95 czasu, start procesu, ładowanie wag, RAM oraz rozmiar artefaktów.
- Zapisać sprzęt, wersje bibliotek, seed, wersję danych i konfigurację.
- Sporządzić raport błędów z przykładami oraz ograniczeniami zakresu.

**Proponowany cel edukacyjny:** co najmniej 95% poprawnych decyzji w zaakceptowanym podzbiorze przy coverage co najmniej 30%. Te liczby są wstępnymi celami dla tego zadania, nie standardem ani gwarancją. Raport musi podać liczebność zaakceptowanego podzbioru i niepewność oszacowania; kilka trafień nie wystarcza do mocnego wniosku.

**Rezultat:** `reports/mvp-evaluation.md`.

**Weryfikacja:** wynik jest odtwarzalny z zapisanej konfiguracji i opisuje również nieudane przypadki. Jeżeli po obejrzeniu testu zmieniamy model, kolejna końcowa ocena wymaga nowego odłożonego zbioru.

### Etap 7 — eksperymenty po MVP

Każdy eksperyment wykonujemy osobno i porównujemy z poprzednią wersją.

1. **Embedding + mała głowica klasyfikacyjna:** sprawdzić, czy encoder poprawia rozpoznawanie parafraz na tyle, by uzasadnić większy RAM i czas.
2. **SetFit:** sprawdzić uczenie encodera na własnych przykładach, bez generowania odpowiedzi podczas predykcji.
3. **Wybór skilli i narzędzi:** przygotować mały katalog, poprawne zestawy dla każdego zadania i oceniać recall potrzebnych elementów oraz rozmiar wybranego zestawu. `code_help` jest zbyt ogólną etykietą dla dużego katalogu; potrzebne będą bardziej szczegółowe dane.
4. **Wiele intencji:** przejść na klasyfikację wieloetykietową, gdy przykłady złożone uzasadnią tę zmianę.
5. **Wspólny encoder:** współdzielić reprezentację tekstu między specjalistami zamiast uruchamiać osobny encoder dla każdego.
6. **Optymalizacja:** rozważyć lżejsze wagi, kwantyzację lub ONNX dopiero po znalezieniu faktycznego wąskiego gardła.

Kompresja prompta pozostaje osobnym kierunkiem badawczym. LLMLingua-2 pokazuje podejście oparte na klasyfikacji tokenów, ale nie dowodzi, że mini klasyfikator zachowa wszystkie istotne szczegóły dowolnego zadania: [publikacja LLMLingua-2](https://arxiv.org/abs/2403.12968).

## 6. Jak mierzyć korzyści bez płatnego API

W pierwszej wersji mierzymy jakość routingu, czas, pamięć i liczbę zadań poprawnie zakończonych lokalnie. Oszczędność pieniędzy pozostaje niezweryfikowana, dopóki nie porównamy kompletnej obsługi z rzeczywistym modelem.

W eksperymencie z narzędziami możemy policzyć tokeny opisów przed i po selekcji przy użyciu tego samego tokenizera. Mniejszy kontekst nie dowodzi jeszcze lepszej odpowiedzi ani mniejszego czasu całej obsługi.

Opcjonalna integracja z LLM powinna porównać te same zadania z Gate i bez Gate: jakość końcowego wyniku, wszystkie wywołania, tokeny wejścia/wyjścia i pełny czas. Uwzględniamy koszt Gate oraz ponowienia po błędnym routingu. Wywołanie pominięte liczymy jako sukces dopiero wtedy, gdy lokalna ścieżka poprawnie zakończyła zadanie.

## 7. Docelowa struktura projektu

To propozycja; poniższe pliki powstaną podczas implementacji.

```text
windup-gate/
├── README.md
├── pyproject.toml
├── plans/windup-gate-plan.md
├── docs/
│   ├── learning-notes.md
│   └── taxonomy.md
├── data/
│   ├── raw/
│   └── splits/
├── src/windup_gate/
│   ├── types.py
│   ├── gate.py
│   ├── policy.py
│   ├── cli.py
│   ├── specialists/
│   │   ├── intent.py
│   │   └── language.py
│   └── handlers/
│       └── detect_language.py
├── scripts/
│   ├── train.py
│   ├── evaluate.py
│   └── benchmark.py
├── tests/
├── models/
└── reports/
```

Wagi i dane prywatne nie muszą trafiać do Git. Jeśli udostępniamy projekt, przygotowujemy neutralne przykłady i instrukcję pozyskania modeli z uwzględnieniem ich licencji.

## 8. Zasady prowadzenia eksperymentów

- Zmieniać jedną istotną rzecz naraz i zapisywać jej wpływ.
- Nowego specjalistę dodawać dopiero po opisaniu jego zadania, danych i metryki.
- Zachowywać poprzedni artefakt modelu i konfigurację, aby wrócić do lepszego wariantu.
- Jeżeli etap nie spełnia kryteriów, poprawić dane lub uprościć zakres przed dokładaniem kolejnego modelu.
- Zmiany taksonomii wymagają przeglądu etykiet oraz ponownej ewaluacji.
- Dla zmiany planu zapisać datę, powód i wpływ na kolejne etapy.

Nie trzeba poznawać rachunku tensorowego, implementować transformera ani trenować modelu generatywnego, aby ukończyć pierwszą wersję. Pierwszy właściwy krok po tym dokumencie to **zdefiniowanie kilku intencji i zebranie danych**, następnie własny klasyfikator TF-IDF. Dzięki temu reszta nauki będzie miała konkretne odniesienie do działającego projektu.

## 9. Lista ukończenia MVP

- [ ] Rozumiem trening, wnioskowanie i podział danych.
- [ ] Mam spójną taksonomię oraz odłożony zbiór testowy.
- [ ] Mam punkt odniesienia oparty na regułach.
- [ ] Potrafię wytrenować, zapisać i wczytać własny klasyfikator.
- [ ] Gate potrafi odstąpić od decyzji.
- [ ] Działają dwa specjaliści i jeden lokalny handler.
- [ ] Demo działa offline po przygotowaniu środowiska.
- [ ] Mam odtwarzalny raport jakości i wydajności.
- [ ] Potrafię wskazać, które zadania Gate faktycznie wykonuje lokalnie, a które tylko kieruje dalej.
