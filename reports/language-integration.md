# Integracja istniejącego modelu języka — WG-006

Data: 2026-10-10 (Asia/Tokyo).

## Wykorzystane repo i wagi

- Repo: [MoviaQ/windup-language-recog](https://github.com/MoviaQ/windup-language-recog).
- Testowana kopia lokalna: `../windup-language-recog` — jawny klon publicznego repo
  (`git clone https://github.com/MoviaQ/windup-language-recog.git ../windup-language-recog`).
  Weryfikację WG-006 wykonano na równoważnej lokalnej kopii tego repo (commit poniżej).
  Gate nie pobiera źródeł ani wag automatycznie.
- Commit źródeł: `6504cfb2efe23eaf7ccc2009b3c97881e1e00309`.
- Interfejs: `LanguageDetector(model_path).predict_details(text)`.
- Checkpoint: istniejący publiczny `model.pt`, v21; 67 879 025 bajtów (około 67,9 MB).
- SHA-256: `358586ac346be2f4c263d90a6c521cf766a94a3b60787e8efefd424e4337579b`.
- Zainstalowane zależności: Python 3.13.5, torch 2.14.1, ftfy 6.3.1; pełny lock w `uv.lock`.

Nie modyfikowano repo, kodu, wag ani kalibracji detektora. Nie kopiowano jego danych
treningowych ani prywatnych danych do Gate. Nie uruchamiano treningu ani końcowych testów modeli.

Upstream opisuje oprogramowanie jako MIT, a wkład w wagi jako CC BY-SA 4.0 z odrębnymi
zastrzeżeniami dotyczącymi źródeł danych. Linki: [licencja kodu](https://github.com/MoviaQ/windup-language-recog/blob/6504cfb2efe23eaf7ccc2009b3c97881e1e00309/LICENSE),
[wagi](https://github.com/MoviaQ/windup-language-recog/blob/6504cfb2efe23eaf7ccc2009b3c97881e1e00309/MODEL_LICENSE.md),
[atrybucja źródeł](https://github.com/MoviaQ/windup-language-recog/blob/6504cfb2efe23eaf7ccc2009b3c97881e1e00309/THIRD_PARTY_NOTICES.md).
Wagi pozostają w repo detektora, poza repo Gate.

## Zachowanie adaptera

- Ładowanie jest leniwe: tylko dla zaakceptowanej intencji językowej z `target_text`.
- Gate korzysta z publicznego API zamiast odtwarzać architekturę lub klasyfikować przez LLM.
- `und`, `uncertain` i flaga kalibracji pochodzą z upstream. Nie używamy surowego `predict()`,
  które zawsze wybiera obsługiwany język.
- Brak kalibracji, niepewność lub błąd modelu oznacza fallback i `completed=false`.
- Wynik poprawnego wykonania ma `route=local`, `completed=true` i osobne `result.language`.
- Identyfikator wersji w wyniku obejmuje SHA-256 faktycznie użytych wag.
- Oryginalny tekst jest zachowany. Wejście przekraczające limit modelu, również po normalizacji,
  jest odrzucane zamiast po cichu ucinane.
- Brak sieci podczas predykcji; przygotowanie zależności i kopii repo jest osobnym krokiem.
- Podstawowy import `windup_gate` nie importuje torch.

## Weryfikacja

```bash
uv sync --locked --extra language
PYTHONPATH="../windup-language-recog" \
  WINDUP_LANGUAGE_TEST_MODEL="../windup-language-recog/model.pt" \
  .venv/bin/python -m pytest -q --cov=windup_gate --cov-report=term-missing --cov-fail-under=80
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pyright
uv build
```

Wynik: **83 testy przechodzą**, pokrycie instrukcji 99,24%. Ruff i Pyright bez błędów,
wheel i archiwum źródeł zbudowane. Bez konfiguracji rzeczywistych wag: 82 testy automatyczne
i jeden pomijany test integracyjny. Stuby nie wymagają torch ani pobierania plików.

Smoke test istniejącego modelu: po jednym przykładzie PL, EN i DE dało oczekiwany język
oraz `local`; `123 !!!` dało fallback. Pełne CLI wraz z istniejącym modelem intencji
również zakończyło przykład PL lokalnie (`result.language=pl`).

Testy błędów obejmują brak wag i zależności, niezgodny checkpoint, błąd inferencji,
niepoprawne wyniki upstream, puste/metadane po czyszczeniu, zbyt krótki tekst,
limit długości oraz zachowanie `und` przy wysokim confidence.

To sprawdzenie integracji na kilku zdaniach, **nie nowy benchmark skuteczności modelu języka**.
Wyniki syntetycznego klasyfikatora intencji z wcześniejszego raportu nadal pozostają
ograniczeniem routingu. Progi Gate nie są progami detektora języka i nie są z nimi łączone.

## Dalsza praca

- Źródła detektora nadal muszą być dostępne na `PYTHONPATH`; Gate nie instaluje ich automatycznie.
- Pakiet instalowalny lub wersjonowane wydanie upstream można dodać osobno, aby uprościć setup.
- WG-007 / WG-008: baseline regułowy i poprawa danych intencji pozostają wolne dla OpenCode.
