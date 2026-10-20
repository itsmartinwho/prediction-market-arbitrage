# prediction-market-arbitrage

A Polymarket scanner and dashboard. It looks for markets where YES and NO together cost less than a dollar, follows the largest recent trades, and sends an alert when it finds an edge. It reads public data only and cannot place a trade.

[![The dashboard's Markets tab](docs/dashboard.jpg)](docs/dashboard.jpg)

Built in January 2026. The hosted page is [prediction-market-arbitrage.vercel.app](https://prediction-market-arbitrage.vercel.app). Its hosted backend is not running at the moment, so that page opens without data; the screenshot is from a local run.

## What it does

- **Arbitrage scan.** Checks every active two-outcome market for YES ask + NO ask under $1.00 after an assumed fee, and alerts on the ones above a threshold.
- **Dashboard.** Five tabs: Markets (by volume, price movers and closing soon, each with a recent news headline), Whale trades, Signals, Search and Arbitrage.
- **Whale trades.** Recent trades of $1,000 or more from Polymarket's Data API, with trader, side, size and price.
- **Signals.** Heuristics read off the same data: a trade over $5,000, a market priced above 90% or below 10%, a market with over $100,000 of volume.
- **Alerts.** Printed to the console, and sent to Telegram if you configure it.

## Research only

This is for research and paper trading. It is not financial advice. The code only calls public GET endpoints: it has no wallet key setting, no signing and no order placement, and a test fails if any of that is added. If you build trading on top of it, doing so with real money is entirely your own risk. Signals are rules of thumb, not predictions.

## How it works

**Data.** Markets and prices come from Polymarket's Gamma API (`/events`; the scanner reads up to 500 events). Order books come from the CLOB API (`/book`). Trades come from the Data API (`/trades`). News headlines come from Google News RSS, one search per event, cached for five minutes. None of them needs a key.

**What counts as an opportunity.** For each two-outcome market the scanner takes the best (lowest) ask for each side:

```
cost  = yes_ask + no_ask
gross = 1.00 - cost
net   = gross - 0.02
edge  = net / cost
```

It keeps the market if `net` is positive and `edge` is at least `MIN_PROFIT_THRESHOLD` (1% by default). Example: YES 0.48 and NO 0.49 cost 0.97, which is 0.03 gross, 0.01 net, and a 1.03% edge.

**Scan cadence.** One pass fetches the market list, then requests two order books per market, one after another. On 20 October 2026 that was 1,809 markets and took 114 seconds. `SCAN_INTERVAL_SECONDS` (5) is the wait between passes, not their length. In that pass no market cleared the bar, and the Arbitrage tab is often empty.

**Fees and slippage.** The 0.02 is an assumption written into `yes_no_arb.py`, a flat two cents per dollar of payout. It is not read from Polymarket, so check the current fee schedule before trusting a number. Slippage is not modelled: only the best ask is used, order size and depth are ignored, and the two legs are fetched one after the other, so prices can move between them.

**The alert.** Plain text: the market question, the YES and NO asks and their sum, gross and net profit with the edge percentage, the time it was detected and the platform. An opportunity is alerted once while its combined cost stays the same; a new cost is a new alert. State is in memory, so a restart alerts again.

## Stack

FastAPI, Next.js 14 (React 18, Tailwind, TanStack Query, Framer Motion), httpx, and aiogram for Telegram.

## Run it

You need Python 3.9 or newer and Node 20 or newer. It was tested on Python 3.9 and 3.13 and Node 22; the Dockerfile uses Python 3.11.

### Backend

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env        # optional, every value has a default
uvicorn app.main:app --port 8000
```

The API is then at `http://localhost:8000`, with its docs at `/docs` and a health check at `/health`. The scanner starts with it.

### Frontend

```
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The dashboard looks for the backend at `http://localhost:8000`. To point it elsewhere, set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` before it starts or builds, for example in `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8103
NEXT_PUBLIC_WS_URL=ws://localhost:8103
```

### Tests

```
cd backend
pip install -r requirements-dev.txt
pytest
```

They stub the price sources, so they need no network.

### Deploy

The backend has a `Dockerfile` (Python 3.11, build context `backend/`) and a `railway.json` with its start command and `/health` check. The frontend is a plain Next.js app; on Vercel set its root directory to `frontend/` and the two `NEXT_PUBLIC_*` variables to the backend's `https://` and `wss://` addresses.

## Environment variables

| Variable | Where | Default | What it does |
| --- | --- | --- | --- |
| `TELEGRAM_BOT_TOKEN` | backend | none | Bot token from @BotFather. Telegram is on only when this and the chat id are both set. |
| `TELEGRAM_CHAT_ID` | backend | none | The chat the alerts go to. |
| `MIN_PROFIT_THRESHOLD` | backend | `0.01` | Smallest net edge to alert on, as a fraction of cost. |
| `SCAN_INTERVAL_SECONDS` | backend | `5` | Wait between scans. |
| `GAMMA_API_URL` | backend | `https://gamma-api.polymarket.com` | Market list and prices. |
| `CLOB_API_URL` | backend | `https://clob.polymarket.com` | Order books. |
| `NEXT_PUBLIC_API_URL` | frontend | `http://localhost:8000` | Where the dashboard fetches from. |
| `NEXT_PUBLIC_WS_URL` | frontend | `ws://localhost:8000` | Where it opens its WebSocket. |

The Data API address (`https://data-api.polymarket.com`) is fixed in `data_client.py`.

## API

- `GET /health`
- `GET /api/arbitrage/opportunities`, `/stats`, `/diagnostics` and `POST /api/arbitrage/scan`
- `GET /api/market-activity/hot`, `/movers`, `/closing-soon`, `/new`, `/search?q=`
- `GET /api/markets`, `/api/markets/{id}`, `/api/markets/{id}/orderbook`
- `GET /api/whales/activity`, `/api/whales/top-movers`
- `GET /api/news` (the signals) and `POST /api/news/refresh`
- `WS /ws/opportunities`, `/ws/stats`

## Project structure

```
backend/
  app/
    main.py              FastAPI app, starts the scanner
    config.py            settings from the environment
    clients/polymarket/  Gamma, CLOB and Data API clients
    core/                the detector, whale tracker, signals, news
    services/            background scanner, Telegram and console alerts
    api/routes/          REST and WebSocket endpoints
  tests/                 offline tests
frontend/src/            the dashboard: app/, components/, hooks/, lib/
docs/dashboard.jpg       the screenshot
```

## Limits

- It treats the first outcome of a two-outcome market as YES. The sum-to-one check holds either way, but a tennis match reads `BUY_PATRICK SCHOEN` in the signals rather than `BUY_YES`.
- When a market's order book is empty or fails, the scanner falls back to the prices Gamma lists, which are last or mid prices, not asks. You cannot buy at those. `/api/arbitrage/diagnostics` counts how often it happens.
- The API has no authentication and allows any origin, and `POST /api/arbitrage/scan` runs a full pass. Do not expose it publicly without limits.
- Next.js is on 14.2.28, which `npm audit` flags. Moving to a current release is not done.

## Licence

MIT, see [LICENSE](LICENSE).

By José (JJ) Martín Quesada, [@itsmartinwho](https://github.com/itsmartinwho).
