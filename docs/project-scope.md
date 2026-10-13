# WindUp Gate — zakres i sens projektu

Stan opisu: 2026-10-10. Ten dokument wyjaśnia projekt nowej osobie lub sesji agenta,
bez znajomości wcześniejszej rozmowy. Status i właścicieli pracy sprawdzaj w
[KANBAN.md](../KANBAN.md), a wymagania implementacyjne w [kartach zadań](tasks.md).

## 1. Co budujemy i po co

WindUp Gate to hobbystyczny, edukacyjny projekt w Pythonie. Sprawdzamy, ile prostych
decyzji przed dużym modelem generującym tekst można oddać małym lokalnym klasyfikatorom.
Chcemy przy okazji nauczyć się przygotowania danych, treningu, oceny błędów,
niepewności modelu i łączenia specjalistów w działający program.

Przykładowe decyzje: „jakie to zadanie?”, „w jakim języku jest tekst?”, a w dalszym
etapie „które instrukcje lub narzędzia są potrzebne do tego zadania?”. Klasyfikator
zwraca etykietę lub ocenę, zamiast pisać odpowiedź na dowolny temat.

Docelowa zasada:

```text
Oryginalne żądanie
  -> kontrola wejścia
  -> mały klasyfikator intencji
  -> polityka: przyjąć decyzję czy odstąpić?
       -> lokalny specjalista potrafi wykonać całe zadanie: local + wynik
       -> wiemy, do kogo skierować zadanie: assist + propozycja wykonawcy
       -> brak wystarczającej podstawy: fallback + powód
```

Duży model może kiedyś być odbiorcą `assist` lub `fallback`, ale obecnie Gate go nie
wywołuje. Fallback kończy się opisem decyzji w JSON. Nie oznacza automatycznego
wysłania danych do API. Potencjalne oszczędności czasu, tokenów i kosztów wymagają
osobnego eksperymentu; samo rozpoznanie intencji ich nie dowodzi.

## 2. Co już istnieje

| Element | Obecny stan | Ograniczenie |
|---|---|---|
| CLI `train`, `analyze`, `evaluate` | Działa lokalnie | Brak serwera HTTP i interfejsu graficznego |
| Klasyfikator intencji | TF-IDF + regresja logistyczna, pięć etykiet | Trening na małym syntetycznym demo; polecenia po polsku |
| Polityka decyzji | Progi score i margin, odrzucenie pustych/długich wejść i jawnej potrzeby historii | Progi demonstracyjne, brak niezawodnego wykrywania negacji i wielu intencji |
| Identyfikacja języka | Adapter istniejącego `MoviaQ/windup-language-recog` | Wymaga lokalnych źródeł, wag i opcjonalnych zależności |
| Wykonanie lokalne | Rozpoznanie języka podanego tekstu | Tłumaczenie, streszczanie i pomoc w kodzie nie mają wykonawców |
| Ewaluacja | Metryki intencji, błędy, baseline najczęstszej klasy | Nie mierzy skuteczności wykonania całych zadań |
| Dane | 100 przykładów demo: 60 train / 20 validation / 20 test | Syntetyczne, autor: Codex; brak rzeczywistych danych użytkownika |

Detektor języka jest już projektem użytkownika i został podłączony w WG-006.
Nie zaczynamy jego treningu od nowa. Źródła i wagi pozostają w osobnym repo:
[MoviaQ/windup-language-recog](https://github.com/MoviaQ/windup-language-recog).
Instrukcja konfiguracji jest w [README](../README.md#istniejący-detektor-języka),
a wersja, licencje i dowody integracji w [raporcie](../reports/language-integration.md).

Ważne rozróżnienie: język **polecenia** i język **analizowanego tekstu** to dwie rzeczy.
Intencję rozpoznajemy z `Request.text`; język z `Request.target_text`.
Obsługa wielu języków tekstu przez detektor nie czyni klasyfikatora intencji wielojęzycznym.

## 3. Zakres pierwszego etapu

Na tym etapie utrzymujemy jeden klasyfikator intencji, jednego istniejącego specjalistę
językowego i prostą, jawną politykę. Zanim dodamy kolejne modele, potrzebujemy:

1. Porównania klasyfikatora z prostymi regułami słów kluczowych (WG-007).
2. Lepszych, opisanych danych oraz przeglądu trudnych przykładów (WG-008).
3. Wyjaśnienia działania obecnego modelu na przykładach (WG-009).
4. Oceny progów na lepszych danych i pomiarów zasobów (WG-010, WG-011).

Pierwszy użyteczny punkt kontrolny: inna osoba potrafi odtworzyć trening i raport,
zobaczyć konkretne błędy, porównać reguły z modelem oraz wykonać rozpoznanie języka
bez sieci po przygotowaniu środowiska. Raport musi pokazywać, kiedy system odstępuje
od decyzji i ile zaakceptowanych decyzji jest błędnych.

Cel jakościowy z pierwotnego planu — co najmniej 95% poprawnych zaakceptowanych
intencji przy coverage co najmniej 30% — pozostaje hipotezą do sprawdzenia na
reprezentatywnych danych. Nie jest obietnicą ani warunkiem, który wolno osiągnąć
przez usuwanie trudnych przykładów. Rozpoznanie intencji i wykonanie zadania
oceniamy osobno.

## 4. Etykiety, trasy i wyniki

Nie mieszaj tych trzech poziomów:

| Poziom | Wartości | Znaczenie |
|---|---|---|
| Intencja | `detect_language`, `translate`, `summarize`, `code_help`, `other` | Co użytkownik prawdopodobnie chce zrobić |
| Trasa | `local`, `assist`, `fallback` | Co Gate faktycznie może zrobić z tym żądaniem |
| Wynik wykonania | Obecnie `LanguagePrediction` albo `None` | Rezultat zakończonego zadania |

`other` to etykieta obejmująca także zadania poza zakresem, złożone i zależne od historii.
`fallback` to decyzja polityki. Niskie score dla `translate` również może skończyć się
fallbackiem. Pełne zasady etykietowania są w [taksonomii](taxonomy.md).

Poniższe scenariusze opisują kontrakt programu. Nie gwarantują, że obecny model demo
poprawnie rozpozna każde podobne sformułowanie.

### A. Lokalna identyfikacja języka

Wejście: `Request("Jaki to język?", target_text="Nie mogę się zalogować.")`.
Jeśli intencja zostanie zaakceptowana, adapter jest skonfigurowany, a detektor zwróci
skalibrowany wynik bez niepewności: `route="local"`, `completed=True`,
`handler="detect_language"`, `result.language` zawiera wykryty język.

`prediction` opisuje decyzję modelu intencji; `result` opisuje wynik detektora języka.
Ich score nie są jedną wspólną skalą i nie należy ich uśredniać.

### B. Rozpoznana prośba o tłumaczenie

Wejście: `Request("Przetłumacz proszę wiadomość na angielski")`.
Jeśli model i polityka zaakceptują `translate`: `route="assist"`,
`handler="translate"`, `completed=False`, `result=None`.
Gate niczego jeszcze nie przetłumaczył. Rozpoznanie rodzaju zadania nie wymaga
kompletnego materiału do jego późniejszego wykonania.

### C. Odstąpienie od decyzji

Wejście: `Request("Zrób to samo", requires_history=True)`.
Gate zwraca `fallback` i `completed=False`, bo aplikacja jawnie wskazała potrzebę
historii. To pole nie jest automatycznym detektorem zależności od rozmowy.

Inne przyczyny fallbacku obejmują brak modelu, niską pewność, `other`, brak tekstu
docelowego dla rozpoznania języka, niepewność detektora i przekroczenie limitu wejścia.
Oryginalny `Request` pozostaje w decyzji. Nie skracamy go po cichu, by zmieścił się w modelu.

## 5. Jakie elementy odpowiadają za co

| Miejsce | Odpowiedzialność |
|---|---|
| `src/windup_gate/types.py` | Wspólny kontrakt żądania, predykcji i decyzji |
| `data.py` | Odczyt JSONL, sprawdzanie podziałów, fingerprint danych |
| `training.py` | Dopasowanie cech i regresji wyłącznie na `train`; nowy artefakt modelu |
| `specialists/intent.py` | Wczytanie zaufanego modelu i predykcja intencji |
| `specialists/language.py` | Leniwy adapter zewnętrznego lokalnego detektora |
| `policy.py` | Jawne zasady przyjęcia lub odrzucenia predykcji |
| `gate.py` | Połączenie kontroli wejścia, klasyfikacji, polityki i lokalnego wykonania |
| `evaluation.py` | Ocena intencji na wskazanym podziale, bez wykonywania zadań |
| `cli.py` | Argumenty użytkownika i prezentacja wyniku JSON |
| `data/demo/`, `docs/dataset-card.md` | Dane startowe oraz ich pochodzenie i ograniczenia |
| `reports/` | Wyniki konkretnych eksperymentów, nie deklaracje ogólnej jakości |

Model uczy zależność między tekstem a etykietą. Polityka korzysta z jego wyniku,
ale nie jest drugim modelem. Specjalista językowy wykonuje konkretne zadanie.
Reguły z WG-007 mają być metodą porównawczą, bez automatycznej zmiany routingu.

Nie tworzymy na zapas rozbudowanego systemu pluginów, rejestru setek specjalistów
ani osobnego frameworka agentów. Nową abstrakcję dodajemy, gdy konkretne zadanie
jej potrzebuje i istnieje sposób sprawdzenia jej zachowania.

## 6. Dane i uczciwa ocena

- `train` służy uczeniu słownika, cech i parametrów modelu.
- `validation` służy porównywaniu wariantów i doborowi progów. Wielokrotne poprawianie
  pod te same przykłady też może prowadzić do przeuczenia.
- `test` służy końcowej ocenie zamrożonego wariantu. Nie przeglądamy jego treści,
  żeby wymyślać reguły, przykłady treningowe ani poprawki modelu.
- Parafrazy i przykłady z tej samej rodziny/szablonu mają wspólny `group_id`
  i trafiają do jednego podziału. Podział robimy grupami, przed eksperymentami.
- Dane syntetyczne oznaczamy jako syntetyczne. Nie nazywamy ich wiadomościami użytkownika
  ani ręcznie zweryfikowanymi, jeżeli człowiek ich nie sprawdził.
- Prywatne materiały pozostają w ignorowanym `data/private/`; nie kopiujemy ich
  do publicznych przykładów lub raportów. Nowe dane dostają opis pochodzenia.

Walidator sprawdza m.in. powtórzone ID, teksty po normalizacji i grupy pomiędzy
podziałami. Nie wykryje wszystkich podobieństw znaczeniowych — grupowanie wymaga
świadomego przeglądu.

Aktualny raport demo: macro-F1 około 0,6976, zaakceptowane 2 z 20 predykcji,
poprawna 1 z tych 2. To słaby wynik na bardzo małej syntetycznej próbie.
Wysokie score wystąpiło również przy błędzie. Szczegóły w
[raporcie walidacyjnym](../reports/demo-validation.md).

`coverage` w obecnym evaluatorze oznacza udział predykcji intencji przyjętych przez
politykę. Nie jest udziałem wykonanych lokalnie zadań. Model może trafnie rozpoznać
`translate`, choć system nadal nie posiada tłumacza.
Pokrycie kodu testami również nie mierzy skuteczności AI.

## 7. Co odkładamy i czego teraz nie implementować

| Pomysł | Warunek rozpoczęcia |
|---|---|
| Kalibracja score i dobór progów | Lepsze dane z WG-008, osobny protokół oceny WG-010 |
| Selekcja narzędzi/instrukcji | Mały, opisany katalog i osobne etykiety; WG-012 |
| Embeddingi / SetFit | Wspólne dane i pomiary bazowe; WG-013 |
| Wiele języków polecenia, wiele intencji naraz | Nowa taksonomia i dane; WG-014 |
| Podłączony LLM, HTTP, GUI, publikacja usługi | Osobne uzgodnione zadanie; poza obecnym zakresem |
| Skracanie dowolnych promptów i historii | Osobny eksperyment z oceną utraty informacji; poza obecnym zakresem |
| Nowy trening detektora języka | Osobne zadanie w jego repo; nie jest częścią integracji Gate |

Samo istnienie pomysłu w backlogu nie oznacza zgody na wdrożenie wszystkich tych
elementów przy okazji najbliższego zadania.

## 8. Jak zacząć jako OpenCode

Przeczytaj [instrukcję przejęcia](opencode-handoff.md), wybierz jedno wolne zadanie
z tablicy i jego [kartę](tasks.md). Przed kodowaniem wpisz właściciela i zakres plików.
WG-007 to sugerowane pierwsze zadanie programistyczne. WG-009 nadaje się do nauki
obecnego modelu. WG-008 wymaga rzetelnego oznaczenia źródeł danych; brak prawdziwych
wiadomości nie upoważnia do wymyślenia ich pochodzenia.

Dokument [plan nauki i wdrożenia](../plans/windup-gate-plan.md) zachowuje szerszy
kontekst edukacyjny. Przy rozbieżności aktualnego statusu korzystaj z tablicy,
obecnego kodu i dokumentów zakresu, a nie z dawnych propozycji struktury plików.
