# Dashboard

Persoonlijk dashboard met WHOOP gezondheidsdata en GitHub activiteit.

## Setup

1. Zet je WHOOP credentials in je shell:
```bash
export WHOOP_CLIENT_ID="jouw_client_id"
export WHOOP_CLIENT_SECRET="jouw_client_secret"
```

2. Haal data op (eerste keer opent de browser voor WHOOP login):
```bash
python3 fetch_data.py
```

3. Open `index.html` in je browser.

## Data vernieuwen

```bash
python3 fetch_data.py
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
