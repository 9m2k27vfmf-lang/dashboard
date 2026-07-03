# Dashboard

Persoonlijk dashboard met WHOOP gezondheidsdata, GitHub activiteit en Claude resourcegebruik.

## Setup

1. Zet je WHOOP credentials in je shell (eenmalig — staan ook in `~/.zprofile`):
```bash
export WHOOP_CLIENT_ID="jouw_client_id"
export WHOOP_CLIENT_SECRET="jouw_client_secret"
```

2. Maak een virtuele omgeving en installeer dependencies:
```bash
python3 -m venv .venv
.venv/bin/pip install requests
```

3. Start het dashboard met één commando — dit vernieuwt de data, start een lokale server en opent je browser:
```bash
./start.sh
```

> **Belangrijk:** open `index.html` NIET direct via `file://` — dan kan de browser `data.json` niet ophalen (CORS-blokkade) en zie je alleen demo-data.

## Data vernieuwen

Gewoon `./start.sh` opnieuw draaien, of handmatig:
```bash
.venv/bin/python fetch_data.py
```

Na de eerste login wordt het token lokaal gecached — je hoeft niet elke keer opnieuw in te loggen.

## Wat zie je

- **Recovery score** — dagelijks herstel percentage
- **Slaap** — uren + slaapprestatie
- **HRV** — hartslagvariabiliteit (RMSSD)
- **Rusthartslag** — beats per minuut
- **Strain grafiek** — 7 dagen belasting
- **Hartslag grafiek** — 7 dagen gemiddelde
- **GitHub** — repos en pull requests
- **Claude** — CPU%, RAM-gebruik en aantal actieve processen
