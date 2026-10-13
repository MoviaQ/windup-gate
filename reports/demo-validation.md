# Pierwsza walidacja demo

Data: 2026-10-09 (Asia/Tokyo). Pełny wynik: [demo-validation.json](demo-validation.json).

## Uruchomienie

```bash
.venv/bin/windup-gate train --data data/demo --output models/intent.joblib
.venv/bin/windup-gate evaluate --data data/demo --model models/intent.joblib \
  --split validation --output reports/demo-validation.json
```

Model zapisano lokalnie; jest ignorowany przez Git. Do ponownego treningu wybierz nową
ścieżkę modelu i podaj ją w ewaluacji. Wersje bibliotek zapisuje `uv.lock`, a metadane
modelu, seed i fingerprinty znajdują się w JSON. Czas utworzenia zmieni się przy odtworzeniu.

## Wynik

| Miara | Wartość |
|---|---|
| Liczba przykładów treningowych | 60 |
| Liczba przykładów walidacyjnych | 20 |
| Accuracy wszystkich predykcji intencji | 70% (14/20) |
| Macro-F1 | 0,6976 |
| Baseline najczęstszej klasy | 20% |
| Próg score / margin | 0,60 / 0,15 |
| Zaakceptowane predykcje intencji | 2/20 |
| Coverage klasyfikacji | 10% |
| Poprawność zaakceptowanych predykcji | 50% (1/2) |
| Zadania wykonane przez lokalny handler | 0 — w tej walidacji nie podano adaptera języka |

To demonstracja procesu na małych danych syntetycznych, nie ocena realnej skuteczności.
Wynik 1/2 nie pozwala wiarygodnie oszacować przyszłej poprawności. Nie osiągnięto celów
edukacyjnych 95% poprawności przy 30% coverage zapisanych w planie.

## Co pokazały błędy

- „Umów rezerwację na kolację” otrzymało błędnie `translate`, score około 0,793 i zostało
  zaakceptowane przez politykę. Wysoki wynik modelu nie gwarantuje trafności.
- „Zrób angielską wersję ogłoszenia” zostało rozpoznane jako `summarize` z niskim score.
  Klasyfikator słów ma problemy z parafrazami, których nie widział w treningu.
- Nietypowy opis problemu z TypeScript trafił do `other` i został odrzucony.

Gate zwraca tylko sugestię ścieżki, więc te pomyłki nie uruchamiają zewnętrznych działań.
Nie zmieniano progów ani danych po obejrzeniu wyniku, aby poprawić opublikowane liczby.
Końcowego zbioru `test` nie oceniano.

## Następne kroki

- WG-008: bardziej różnorodne dane, kontrprzykłady i przegląd etykiet.
- WG-007: regułowy punkt odniesienia na tej samej walidacji.
- WG-010: sprawdzenie kalibracji i kompromisu coverage/poprawność na większych danych.
- WG-006: osobny detektor języka i poprawne wykonanie jednego zadania lokalnego.

Nie mierzyliśmy oszczędności LLM, czasu p50/p95 ani pamięci. To odrębne eksperymenty;
liczba zaakceptowanych intencji nie jest liczbą zaoszczędzonych wywołań.

## Weryfikacja aplikacji

Kod sprawdzono niezależnie od ewaluacji modelu:

- 46 testów przechodzi; pokrycie instrukcji: 98,94%.
- Ruff: sprawdzenie i formatowanie przechodzą.
- Pyright: 0 błędów.
- `uv build`: powstały wheel i archiwum źródeł.

Pokrycie testami mówi o wykonanych ścieżkach kodu, nie o jakości AI.
