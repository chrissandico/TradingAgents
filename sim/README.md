# Prof's simulated portfolio — TradingAgents fork

Fork: `chrissandico/TradingAgents` (personal) · Upstream: `TauricResearch/TradingAgents`

**Simulation only.** This repo has no broker connection. Decisions are
ratings + reports; nothing here can place a real order or move real money.
Wiring a real portfolio is a separate, explicitly approved step — do not
add broker code to this branch without that decision.

## Branch model

- `main` — pristine upstream. Never commit to it directly; it only
  fast-forwards from upstream, so upstream updates never conflict.
- `prof/sim-portfolio` — all of Prof's changes (this `sim/` folder, config,
  experiments). Keep changes confined to `sim/` where possible so merges
  from `main` stay clean.

## Syncing upstream

```bash
git checkout main
git fetch upstream
git merge --ff-only upstream/main
git push origin main

git checkout prof/sim-portfolio
git merge main        # bring the new upstream into the working branch
git push origin prof/sim-portfolio
```

If `main` ever refuses a fast-forward, stop — it means something was
committed to `main` directly. Move that commit to `prof/sim-portfolio`
instead of force-pushing.

## Setup

```bash
cd ~/workspace/tradingagents
python3 -m venv .venv && source .venv/bin/activate   # Python 3.11+ (3.13 upstream-recommended)
pip install .
```

The Anthropic key is NOT in `.env`. It lives in the Secure Vault under the
`custom.anthropic-tradingagents` connector (a dedicated key named
ANTHROPIC_API_KEY_TRADINGAGENTS_SIM), and `sim/run.py` fetches a
short-lived surrogate for it at launch. The real key never touches disk.
Defaults set by the launcher (cheap test tier): provider anthropic,
deep claude-sonnet-5, quick claude-haiku-5-5, 1 debate + 1 risk round.

Any other provider works via `.env` the upstream way (OpenAI, Google,
DeepSeek, Ollama…); see `.env.example`. Only the Anthropic path uses the
vault launcher.

## Running the sim

Copy an example book, edit the cash/positions to the *simulated* book you
want to test, then run against it through the launcher:

```bash
cp sim/portfolio.example.json sim/my_book.json
.venv/bin/python sim/run.py --ticker NVDA --date 2026-11-04 --portfolio sim/my_book.json --save
```

- An empty `positions` list is a flat book — different from omitting
  `--portfolio`, which means "no book, generic advice".
- Canadian tickers use `.TO` (e.g. `SHOP.TO`), crypto uses `BTC-USD`.
- Reports land in `reports/` (git-ignored); the decision memory log lives
  at `~/.tradingagents/memory/trading_memory.md` and settles past
  decisions against real closes + benchmark alpha on later runs.

Backtest a grid without touching the live memory log:

```bash
.venv/bin/python sim/run.py backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --every 7
```

First live proof (2026-11-05): NVDA as of 2026-11-04, flat US$25,000 book,
analysts market/news/fundamentals — full pipeline completed, Portfolio
Manager rated **Hold** (target 204.39), report + memory-log entry saved.
Known gaps in that run, honestly flagged by the system itself: no
FRED_API_KEY (macro data skipped) and Yahoo company-news timed out
(news analyst worked from macro headlines and said so in its report).

## Files

- `portfolio.example.json` — flat simulated book (cash only, no positions)
- `portfolio.sample-holdings.json` — example book with sample positions,
  to see the shape; the numbers are illustrative, not Prof's holdings
- `my_book.json` — your working book (create it; do not commit real
  holdings — add it to `.gitignore` if you put real figures in it)
