# Taksonomia intencji v1

Klasyfikujemy samodzielne polecenie użytkownika po polsku. Nie klasyfikujemy cytowanego
tekstu docelowego jako polecenia. Pole `target_text` jest przekazywane osobno.

| Etykieta | Znaczenie | Poza zakresem |
|---|---|---|
| `detect_language` | Ustalenie, w jakim języku jest tekst | Tłumaczenie i rozpoznawanie mowy z nagrania |
| `translate` | Jedno zadanie tłumaczenia tekstu | Tłumaczenie połączone z napisaniem odpowiedzi |
| `summarize` | Skrót, streszczenie, główne punkty | Streszczenie połączone z tłumaczeniem |
| `code_help` | Pisanie, objaśnianie, testowanie i debugowanie kodu | Pytanie teoretyczne bez związku z programowaniem |
| `other` | Pozostałe, złożone i zależne od historii żądania | Nie jest odpowiednikiem każdego niepewnego wyniku |

`fallback` jest decyzją polityki, nie klasą modelu. Wysokie score dla `other` nadal prowadzi
do fallbacku. Wynik modelu jest pojedynczą etykietą; wieloetykietowe zadania są dalszym etapem.

Przykłady graniczne:

- „Nie tłumacz, wymyśl tytuł” → `other`.
- „Przetłumacz i napisz odpowiedź” → `other`.
- „Co robi ta funkcja?” → `code_help`, jeżeli to samodzielny kontekst programistyczny.
- „Zrób tak jak wcześniej” → `other`; w API ustaw również `requires_history=True`.
- „Czy poniższy akapit jest francuski?” → `detect_language`.

To zasady oznaczania danych, nie gwarancje modelu. Prototyp nie ma niezawodnego detektora
negacji, złożonych intencji ani nieznanego języka polecenia.
