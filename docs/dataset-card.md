# Karta danych: synthetic-codex-demo-v1

- Autor: Codex, przykłady wygenerowane na potrzeby uruchomienia projektu 2026-10-09.
- Pochodzenie: syntetyczne polecenia; nie są pobranymi wiadomościami ani zbiorem użytkownika.
- Zakres: pięć etykiet intencji; polecenia w języku polskim.
- Liczebność: 100 rekordów, po 20 na klasę.
- Podział: 60 treningowych, 20 walidacyjnych, 20 testowych; klasy zrównoważone w każdym.
- Grupy: 50 par przykładów, każda para przypisana do jednego podzbioru.
- Zastosowanie: sprawdzenie technicznego procesu uczenia, zapisu, predykcji i raportowania.

Każdy plik JSONL ma pola `id`, `text`, `label`, `group_id`, `source`.
Parafrazy lub warianty tego samego zadania powinny mieć wspólne `group_id`, również po
dodaniu nowych danych. Walidator wykrywa powtórzone ID, znormalizowane teksty i grupy
przeciekające między podzbiorami. Nie wykrywa wszystkich podobieństw semantycznych;
grupowanie wymaga przeglądu człowieka.

Zbiór jest mały, sztuczny i stylistycznie jednorodny. Nie odzwierciedla częstości intencji,
długich promptów, historii rozmów ani rozkładu rzeczywistych użytkowników. Także przykłady
walidacyjne pochodzą od tego samego generatora, więc nie są niezależnym audytem jakości.

W modelu wektoryzer jest dopasowany wyłącznie do `train`. Przykłady walidacyjne służą
obserwacji zachowania. Wynik końcowego `test` nie został wyliczony podczas startu projektu;
walidator odczytuje go tylko w celu kontroli schematu i przecieków.

Następny krok WG-008: osobny katalog `data/curated/`, różnorodne przykłady, weryfikacja
etykiet i nowe grupy. Prywatne dane trzymaj w ignorowanym `data/private/`; nie dodawaj ich
do repozytorium wraz z przykładami publicznymi.
