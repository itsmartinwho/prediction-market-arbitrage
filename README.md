# Prediction Market Arbitrage

Real-time arbitrage detection for Polymarket prediction markets.

## Features

- **YES+NO Arbitrage Detection**: Finds markets where YES + NO prices sum to less than $1.00
- **Real-time Scanning**: Continuous monitoring with 5-second scan intervals
- **Telegram Alerts**: Instant notifications when opportunities are detected
- **Cyberpunk Dashboard**: Futuristic UI with real-time WebSocket updates
- **Conservative Risk Management**: Designed for paper trading with $100-500

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example .env
# Edit .env with your Telegram bot token (optional)

# Run the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000 to see the dashboard.

## Architecture

```
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI endpoints
│   │   ├── clients/         # Polymarket API clients
│   │   ├── core/arbitrage/  # Detection logic
│   │   ├── models/          # Data models
│   │   └── services/        # Scanner, notifications
│   └── main.py              # Application entry
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── lib/             # API client
│   └── tailwind.config.ts   # Cyberpunk theme
```

## How Arbitrage Works

In a binary prediction market:
- YES token pays $1 if the event happens
- NO token pays $1 if the event doesn't happen
- One outcome is **guaranteed** to pay out

**The Strategy:**
1. Find markets where `YES ask + NO ask < $1.00`
2. Buy both tokens
3. Guaranteed profit = `$1.00 - combined cost - fees`

**Example:**
- YES @ $0.48 + NO @ $0.49 = $0.97
- Buy both for $0.97
- Payout: $1.00 (one token wins)
- Gross profit: $0.03 (3.09%)
- After 2% fee: ~$0.01 net profit

## API Endpoints

- `GET /api/markets` - List active markets
- `GET /api/arbitrage/opportunities` - Current opportunities
- `POST /api/arbitrage/scan` - Trigger manual scan
- `WS /ws/opportunities` - Real-time opportunity feed

## Configuration

Environment variables:

```bash
# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Detection
MIN_PROFIT_THRESHOLD=0.025  # 2.5% minimum edge
SCAN_INTERVAL_SECONDS=5

# Risk (for future auto-execution)
MAX_POSITION_SIZE=50
ENABLE_AUTO_EXECUTE=false
```

## Deployment

### Railway

1. Connect your GitHub repo to Railway
2. Add PostgreSQL addon
3. Set environment variables
4. Deploy!

Estimated cost: ~$5/month

## Future Enhancements

- [ ] Auto-execution (scaffolded, not implemented)
- [ ] Kalshi cross-platform arbitrage
- [ ] Whale tracking
- [ ] AI probability models

## Disclaimer

This tool is for educational purposes. Arbitrage opportunities may disappear quickly. Always verify prices before trading. Not financial advice.
