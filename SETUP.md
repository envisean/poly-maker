# SETUP — poly-maker fork

## What you need to run the backbone

1. **Polymarket-enabled wallet**
   - Fresh Polygon wallet (MetaMask or equivalent)
   - Fund it with USDC.e on Polygon
   - Visit [polymarket.com](https://polymarket.com), connect the wallet, and
     **place at least one manual trade** — this sets the CLOB permissions the
     bot needs
   - Export the private key for `PK` in `.env`
   - Wallet address → `BROWSER_ADDRESS` in `.env`

2. **Google Sheets config**
   - Copy the upstream [sample sheet](https://docs.google.com/spreadsheets/d/1Kt6yGY7CZpB75cLJJAdWo7LSp9Oz7pjqfuVWwgtn7Ns/edit)
   - Create a Google Service Account in any GCP project; download the JSON key
   - Place the JSON as `credentials.json` in the repo root
   - Share your copied sheet with the service account email (editor)
   - Put the sheet URL in `SPREADSHEET_URL`

3. **`.env`**

   ```
   PK=<your_private_key>
   BROWSER_ADDRESS=<your_wallet_address>
   SPREADSHEET_URL=<your_sheet_url>
   ```

## Running

```bash
# Fetch all markets into the sheet (background process, different IP preferred)
uv run python update_markets.py

# Start the market maker
uv run python main.py
```

## signals/ scaffold

The `signals/` package is the 8-detector grid layered on top of poly-maker.
All 8 are stubs that return `None`. Wire them in one at a time:

```python
from signals import ConfluenceEngine
from signals.velocity import VelocitySignal
from signals.volume import VolumeSignal
# ...

engine = ConfluenceEngine(
    signals=[VelocitySignal(), VolumeSignal(), ...],
    threshold=3,
)

hit = engine.evaluate(market, state)
if hit:
    # route hit to order placement
    ...
```

Tests:
```bash
uv run pytest signals/
```

## What's NOT included yet

- Sentiment feeds (X/Reddit/Telegram/Discord)
- Whale wallet list + on-chain event stream
- Cross-venue price feeds (Kalshi/PredictIt/Manifold APIs)
- News feed adapters (NOAA/AP/Reuters/CoinGecko)
- Integration into `main.py` tick loop

These are the next builds once the backbone is confirmed running.
