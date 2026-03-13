# Licencja i model biznesowy

## Struktura licencyjna

### Core — Apache 2.0 (bezpłatnie)

Publiczne repozytorium: `github.com/czarneniebo/czarneniebo-ai`

Obejmuje:
- `pipeline.py` — archiwum RAG
- `whisper_transkrypcja.py` — transkrypcja
- `graf_powiazań.py` — OSINT
- `file_watcher.py` — auto-indeksowanie
- `web_ui.py` — interfejs
- Automatyczny installer
- Dokumentacja

### Premium — Licencja komercyjna

Prywatne repozytorium dostępne przez **fork z pull access**.

Obejmuje:
- `forensics_pipeline.py` — wielosygnałowy detektor deepfake'ów
- `dezinformacja.py` — klasyfikator dezinformacji
- `restauracja_mediow.py` — restauracja archiwalii
- Bug fixes z głównej gałęzi (pull access)

**Cena:** 0.1 ETH/rok (Polygon/Base) lub faktura tradycyjna.

### Enterprise — Umowa indywidualna

- Admin access do repozytorium
- Możliwość własnych PR do main branch
- SLA support (48h odpowiedzi)
- Sesje szkoleniowe
- Dostosowanie do potrzeb redakcji

---

## Weryfikacja licencji (smart contract)

Licencja Premium jest weryfikowana on-chain przez kontrakt ERC-1155 na Polygon.

```
Network:  Polygon Mainnet (chain ID: 137) lub Base
Contract: CzarneNieboLicense (ERC-1155)
Token ID 1 = PREMIUM license

Sprawdź: isLicensed(twoj_wallet, 1) → bool
```

### Zakup licencji

1. Wejdź na stronę kontraktu (link po deploy)
2. Wywołaj `mintPremium()` z wartością 0.1 ETH
3. Wyślij adres portfela na czarneniebo@proton.me
4. Otrzymasz zaproszenie do prywatnego repo w ciągu 24h

### Weryfikacja w GitHub Actions

Każdy fork sprawdza licencję automatycznie:

```yaml
# .github/workflows/check-license.yml (w prywatnym repo)
- name: Verify Polygon license
  run: python scripts/verify_license.py ${{ secrets.WALLET_ADDRESS }}
```

---

## Zakup tradycyjny (bez blockchain)

Dla redakcji preferujących tradycyjny model:

**Kontakt:** czarneniebo@proton.me
**Patronite:** https://patronite.pl/CzarneNiebo

---

## Dlaczego blockchain?

> "Zamiast umowy PDF którą można zignorować — masz token NFT.
> Zamiast faktury którą trzeba przetwarzać ręcznie — masz transakcję on-chain.
> Junior programista z dostępem do repo i tokenem w portfelu
> = samodzielny klient który nie potrzebuje niczyjej zgody żeby działać."

Smart contract eliminuje:
- Ręczne zarządzanie dostępem
- Nieuregulowane używanie po wygaśnięciu licencji
- Konieczność interwencji przy odnowieniu
