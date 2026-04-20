<div align="center">

<img src="docs/flow-diagram.svg" alt="Kisan Mausam Alert — System Flow" width="100%"/>

<br/>

# 🌾 Kisan Mausam Alert

**v2.0 — April 2026**

Automated AI weather alerts for Indian farmers — in their own language, on their phone, only when there's real risk.

<br/>

[![Pipeline](https://img.shields.io/badge/Pipeline-GitHub%20Actions-2088ff?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/yogeshwankhede007/kisan-mausam-alert/actions)
[![AI](https://img.shields.io/badge/AI-Ollama%20%7C%20Free-7c3aed?style=for-the-badge&logo=llama&logoColor=white)](https://ollama.com)
[![Languages](https://img.shields.io/badge/Languages-11%20Indian-f97316?style=for-the-badge)](https://github.com/yogeshwankhede007/kisan-mausam-alert)
[![Data](https://img.shields.io/badge/Data-IMD%20%7C%20data.gov.in-16a34a?style=for-the-badge)](https://mausam.imd.gov.in)
[![Delivery](https://img.shields.io/badge/Delivery-WhatsApp%20%7C%20SMS-25d366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://www.twilio.com)
[![License](https://img.shields.io/badge/License-MIT-64748b?style=for-the-badge)](LICENSE)

</div>

---

## What's New in v2.0

> **Three new advisory engines** ship in this release — all running as part of the existing daily pipeline with no extra configuration needed.

| Feature | Status |
|---------|--------|
| 🌱 Planting & Sowing Advisory | ✅ Live |
| 🌾 Harvest Timing Recommendations | ✅ Live |
| 🐄 Livestock Protection Alerts | ✅ Live |
| 💬 WhatsApp composite messages | ✅ Live |

---

## 🌱 Planting & Sowing Advisory

The pipeline now detects sowing season by district and generates **optimal sowing window recommendations** per crop — factoring in the 7-day precipitation forecast, temperature trends, and the Indian crop calendar.

Active months: **kharif** May–Jul · **rabi** Oct–Nov · **zaid** Feb–Apr

| Advice type | Example |
|-------------|---------|
| Best sowing window | "Sow cotton between 12–18 Jun — monsoon onset expected by 10 Jun in Warangal" |
| Delay warning | "Avoid sowing wheat before 20 Nov — soil temperature still too high in Lucknow" |
| Variety recommendation | Drought-tolerant vs water-intensive based on predicted seasonal rainfall |

Delivered as part of the WhatsApp message — appended after the main weather alert. SMS gets the core alert only (character limit preserved).

---

## 🌾 Harvest Timing Recommendations

Crop maturity calendars are now combined with the short-range forecast to advise the **safest harvest window** — avoiding rain, humidity, and wind damage to standing crops.

Active months: **kharif** Sep–Nov · **rabi** Mar–May · **zaid** May–Jun

| Advice type | Example |
|-------------|---------|
| Cut before rain | "Harvest onion by Thursday — heavy rain from Friday, risk of rot" |
| Delay for dry window | "Wait 3 days for wheat — dry sunny spell opens Wednesday, better grain moisture" |
| Post-harvest protection | "Store sugarcane in shade — 5 days of 40°C+ ahead, quality risk" |

---

## 🐄 Livestock Protection Alerts

Farmers registered with `--cattle` now receive a **dedicated livestock advisory** whenever the forecast triggers a significant risk. Generated for every language group that has cattle farmers, in one batched LLM call.

| Weather event | Advisory covers |
|---------------|----------------|
| Heatwave ≥ 40 °C | Shade structures, water schedule, heat stress signs |
| Cold wave ≤ 10 °C | Shelter requirements, bedding, newborn animal care |
| Thunderstorm | Safe enclosure, avoid open fields |
| Heavy rain / floods | Elevated shelter, emergency feed, disease prevention |

---

## 💬 Composite WhatsApp Messages

Advisory addons are appended to the WhatsApp message after the main weather alert — separated by blank lines for readability. SMS delivery is unchanged (320-char core alert only).

```text
[Main weather alert — 320 chars, all channels]

[Planting advisory — WhatsApp only, if sowing season]

[Harvest advisory — WhatsApp only, if harvest season]

[Livestock advisory — WhatsApp only, if farmer has cattle]
```

All three addons are generated in **a single LLM call per language group** — no extra API overhead per farmer.

---

## ⚡ How It Works

The pipeline runs automatically on GitHub Actions every day at 11 AM IST. It fetches live data, asks the AI to find real risks, and sends targeted advisories. When the week looks calm, it stays silent.

```text
📡 IMD + Open-Meteo data  →  🌾 Crop calendar per district  →  🤖 AI writes advisory
                                                                         ↓
👨‍🌾 Farmer reads it in their language  ←  💬 WhatsApp / SMS  ←  🔍 Send only if real risk
```

**No human trigger. No daily spam. No English-only dashboard. No app to install.**

---

## 🌦 Alert Thresholds

| Weather event | Threshold | Advice example |
|---------------|-----------|----------------|
| 🌡 Heatwave | ≥ 40 °C | Irrigate sugarcane at dawn · shelter cattle · delay sowing |
| 🌧 Heavy rain | ≥ 64.5 mm | Advance wheat harvest · hold pesticide spraying · check drainage |
| 🥶 Cold wave | ≤ 10 °C | Cover mustard/gram seedlings · protect cattle overnight |
| ⛈ Thunderstorm | WMO 95/96/99 | Keep cattle indoors · avoid open fields |
| 💨 High wind | ≥ 60 km/h | Stake tall crops · secure storage covers |

---

## 🗣 11 Indian Languages

| हिंदी | मराठी | తెలుగు | ಕನ್ನಡ | ਪੰਜਾਬੀ | ગુજરાતી | বাংলা | ଓଡ଼ିଆ | தமிழ் | മലയാളം | English |
|-------|-------|--------|-------|--------|---------|-------|-------|-------|--------|---------|

---

## 📱 Sample Alerts

**Marathi — Pune heatwave**

```text
उष्णतेची लाट येणार!
१४–१७ एप्रिल रोजी ४१°C.
ऊस-कांदा: पहाटे पाणी द्या.
जनावरांना सावलीत ठेवा.
– IMD हवामान इशारा
```

**Telugu — Warangal heatwave**

```text
హెచ్చరిక! ఏప్రిల్ 14–18
వరంగల్‌లో 40°C+.
పత్తి: తెల్లవారుజామున నీరు.
పశువులకు నీడ ఇవ్వండి.
– IMD వాతావరణ హెచ్చరిక
```

---

## 🗺 Districts Covered

80+ farming districts across **Maharashtra, Karnataka, Telangana, Andhra Pradesh, Uttar Pradesh, Punjab, Haryana, Gujarat, West Bengal, Odisha, Tamil Nadu, Kerala** and more.

```bash
python main.py --list-districts   # prints the full list
```

---

## 🚀 Getting Started

### Option A — GitHub Actions (recommended)

**1. Push to GitHub**

```bash
git clone https://github.com/yogeshwankhede007/kisan-mausam-alert.git
cd kisan-mausam-alert
git push -u origin main
```

**2. Add Secrets** — repo → Settings → Secrets and variables → Actions

| Secret | Where to get it |
|--------|----------------|
| `TWILIO_ACCOUNT_SID` | Twilio Console → Account Info |
| `TWILIO_AUTH_TOKEN` | Twilio Console → Account Info |
| `TWILIO_MESSAGING_SERVICE_SID` | Twilio Console → Messaging → Services |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` |
| `DATA_GOV_IN_API_KEY` | [data.gov.in](https://data.gov.in/user/register) *(optional)* |

**3. Add farmers** — edit `farmers_sample.json`, commit and push. The pipeline seeds the DB on every run.

**4. Done.** Pipeline runs at **11 AM IST daily**. Trigger manually: Actions → Daily Weather Alerts → Run workflow.

---

### Option B — Local

```bash
# One-time: pull the AI model (~2 GB)
ollama pull llama3.2:3b

# Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in Twilio credentials

# Add farmers
python scripts/bulk_add_farmers.py --file farmers_sample.json

# Preview — no messages sent
python main.py --now --dry-run

# Send now
python main.py --now

# Run on schedule (11 AM IST)
python main.py
```

---

## 👨‍🌾 Managing Farmers

**Add a single farmer**

```bash
python scripts/add_farmer.py \
  --name "Ramesh Patil" \
  --phone "+919800001111" \
  --language marathi \
  --state Maharashtra \
  --district pune \
  --crops "sugarcane,onion" \
  --cattle \
  --channel whatsapp
```

**Bulk import from JSON**

```bash
python scripts/bulk_add_farmers.py --file farmers_sample.json
```

`farmers_sample.json` includes 5 example farmers across Pune, Warangal, Lucknow, Dharwad, Ludhiana.

---

## 🧪 Testing

```bash
# Preview 7-day forecast for any district (no messages sent)
python main.py --test-forecast pune
python main.py --test-forecast warangal

# Full pipeline dry run — prints all messages to stdout
python main.py --now --dry-run
```

---

## ⚙️ Architecture

```text
  GitHub Actions cron (05:30 UTC = 11 AM IST)
              │
    ┌─────────▼──────────┐
    │   alert_pipeline   │  per active district
    └──┬──────┬──────┬───┘
       │      │      │
  ┌────▼──┐ ┌─▼──┐ ┌─▼──────────────┐
  │ Open- │ │IMD │ │  crop_fetcher  │
  │ Meteo │ │CAP │ │  data.gov.in   │
  │ 7-day │ │RSS │ │  + season cal  │
  └────┬──┘ └─┬──┘ └─┬──────────────┘
       └──────┴───────┘
              │
    ┌─────────▼──────────────────────────┐
    │         weather_analyzer           │
    │  analyse_and_generate_alert()      │  main alert + risk JSON
    │  generate_advisory_addons()        │  planting / harvest / livestock
    └─────────┬──────────────────────────┘
              │  only when real risk found
    ┌─────────▼──────────┐
    │     notifier       │  WhatsApp (full composite) · SMS (core alert)
    └─────────┬──────────┘
              │
    ┌─────────▼──────────┐
    │  SQLite log_alert  │
    └────────────────────┘
```

**Models**

| Environment | Model | Size |
|-------------|-------|------|
| GitHub Actions | `llama3.2:3b` | 2 GB — fits 7 GB runner RAM |
| Local (recommended) | `qwen2.5:7b` | 5 GB — better multilingual quality |

---

## 🏗 Project Structure

```text
kisan-mausam-alert/
├── .github/workflows/
│   ├── daily-alerts.yml        # cron — sends real alerts at 11 AM IST
│   └── test-pipeline.yml       # dry run on every push / PR
├── main.py                     # CLI entry point
├── config/settings.py          # all config from .env
├── src/
│   ├── alert_pipeline.py       # orchestration
│   ├── weather_analyzer.py     # AI risk analysis + advisory addons
│   ├── imd_fetcher.py          # Open-Meteo + IMD CAP RSS
│   ├── crop_fetcher.py         # data.gov.in + seasonal crop calendar
│   ├── notifier.py             # Twilio WhatsApp / SMS dispatch
│   ├── database.py             # SQLite farmer registry
│   └── scheduler.py            # daily scheduler
├── data/district_coords.py     # lat/lon for 80+ districts
├── scripts/
│   ├── add_farmer.py
│   ├── bulk_add_farmers.py
│   ├── test_alert.py
│   └── send_test_sms.py
├── farmers_sample.json
├── requirements.txt
└── .env.example
```

---

## 💰 Running Cost

| Component | Cost |
|-----------|------|
| Weather data (Open-Meteo) | **Free** |
| IMD CAP alerts | **Free** — government RSS feed |
| Crop data (data.gov.in) | **Free** — register for API key |
| AI model (Ollama) | **Free** — runs inside GitHub Actions |
| GitHub Actions | **Free** tier — 2,000 min/month |
| Twilio WhatsApp sandbox | Free for testing · ~₹0.60–₹1 / message in production |
| Twilio SMS | ~₹0.40–₹0.80 / message |

---

## 📲 Cheaper Delivery Alternatives

### WhatsApp — Meta Cloud API

Meta provides the WhatsApp Business API directly at **no cost for the first 1,000 conversations/month** — no Twilio markup.

| | Twilio WhatsApp | Meta Cloud API |
|-|-----------------|----------------|
| Cost | ~₹0.60–₹1 / message | **Free** up to 1,000/month, then ~₹0.30–₹0.50 |
| Setup | Easy (sandbox ready) | Moderate (Meta Business account + webhook) |
| Unicode / Indian scripts | ✅ | ✅ |

[Get started with Meta Cloud API →](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

### SMS — Fast2SMS

[Fast2SMS](https://www.fast2sms.com) is an Indian BSP that supports Devanagari/regional scripts in SMS — unlike Twilio via Indian carriers.

| | Twilio SMS | Fast2SMS |
|-|------------|----------|
| Cost | ~₹0.40–₹0.80 / SMS | ~₹0.07–₹0.15 / SMS |
| Unicode / Hindi / Marathi | ❌ Blocked by carriers | ✅ Supported |
| Free credits | Sandbox only | ~₹50 on signup |
| India-specific support | ❌ | ✅ |

**Migration path:** set `NOTIFICATION_PROVIDER=fast2sms` or `NOTIFICATION_PROVIDER=meta_whatsapp` in `.env` — no code change needed.

---

## 📝 Known Behaviours

- **WhatsApp over SMS for scripts** — Indian carriers block Devanagari/regional scripts in SMS (Twilio error 30044). WhatsApp delivers all 11 scripts without issue.
- **Offline fallback** — if Ollama is unreachable, the pipeline sends a plain-English risk summary automatically.
- **Rate limiting** — a 300 ms gap between Twilio calls is enforced to prevent throttling.
- **Advisory addons skip gracefully** — if the addons LLM call fails, the main alert is still sent; a `WARNING` is logged.
- **Model cache in CI** — Ollama model is cached in GitHub Actions after the first download; subsequent runs skip it entirely.

---

<div align="center">

Built for India's 140 million farming families.<br/>
**The forecast exists. The gap is always the last mile.**

[![Star this repo](https://img.shields.io/github/stars/yogeshwankhede007/kisan-mausam-alert?style=social)](https://github.com/yogeshwankhede007/kisan-mausam-alert)

</div>
