#!/usr/bin/env python3
"""Launch TradingAgents with the vault-held Anthropic key — no key on disk.

Fetches a dynamic-credential surrogate for custom.anthropic-tradingagents
and hands it to TradingAgents as ANTHROPIC_API_KEY. The surrogate is not
the real key: the egress layer swaps it for the real credential only on
requests to api.anthropic.com. It is never printed, logged, or written to
any file (including .env).

Two shims make that work, both applied in-process before the CLI starts:

1. Auth header placement. The registered connector placement is the
   x-api-key header, and the egress swap only happens in that position.
   The installed Anthropic SDK sends its api_key as an Authorization
   Bearer token instead, which Anthropic rejects when the value is a
   surrogate ("Invalid bearer token"). This launcher patches the SDK's
   sync and async clients to send the key in X-Api-Key, which a raw-call
   probe verified returns 200.

2. Sandbox no_proxy. The ambient no_proxy list carries bracketed IPv6
   entries ([::1], [fd8b:...::1]) that crash httpx's URL parser
   (InvalidURL: Invalid port ':1]'). The child environment trims it to
   plain loopback names. The egress proxy itself is unaffected.

Run with the project venv:
    .venv/bin/python sim/run.py --ticker NVDA --date 2026-11-04 \
        --portfolio sim/portfolio.example.json --save
    .venv/bin/python sim/run.py backtest NVDA,AAPL --start 2026-06-01 --end 2026-08-01 --every 7

Defaults set here (any real environment variable wins):
    TRADINGAGENTS_LLM_PROVIDER=anthropic
    TRADINGAGENTS_DEEP_THINK_LLM=claude-sonnet-5
    TRADINGAGENTS_QUICK_THINK_LLM=claude-haiku-5-5
    TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
    TRADINGAGENTS_MAX_RISK_ROUNDS=1
    TRADINGAGENTS_OUTPUT_LANGUAGE=English
"""
import os
import sys

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/templates/skill/bin")
sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
sys.path.insert(0, "/opt/hatch/workflow-skills/custom-connector-setup/bin")
import dynamic_credentials as dc

CONNECTOR = "custom.anthropic-tradingagents"
FRED_CONNECTOR = "custom.fred"

DEFAULTS = {
    "TRADINGAGENTS_LLM_PROVIDER": "anthropic",
    "TRADINGAGENTS_DEEP_THINK_LLM": "claude-sonnet-5",
    "TRADINGAGENTS_QUICK_THINK_LLM": "claude-haiku-5-5",
    "TRADINGAGENTS_MAX_DEBATE_ROUNDS": "1",
    "TRADINGAGENTS_MAX_RISK_ROUNDS": "1",
    "TRADINGAGENTS_OUTPUT_LANGUAGE": "English",
}


def _x_api_key_auth(self):
    api_key = getattr(self, "api_key", None) or getattr(self, "_api_key", None)
    if api_key is None:
        return {}
    return {"X-Api-Key": api_key}


def _patch_anthropic_auth():
    import anthropic

    anthropic.Anthropic._api_key_auth = property(_x_api_key_auth)
    anthropic.AsyncAnthropic._api_key_auth = property(_x_api_key_auth)


def main(argv):
    entry = dc.dynamic_credential_entry(CONNECTOR)
    os.environ["ANTHROPIC_API_KEY"] = str(entry["surrogate"]).strip()
    # FRED macro data: the vendor reads FRED_API_KEY and sends it as the
    # api_key query param — exactly the registered placement for
    # custom.fred, so the egress swap works the same way.
    try:
        fred = dc.dynamic_credential_entry(FRED_CONNECTOR)
        os.environ["FRED_API_KEY"] = str(fred["surrogate"]).strip()
    except Exception:
        pass  # macro stays unconfigured; the vendor degrades honestly
    os.environ["no_proxy"] = "localhost,127.0.0.1"
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    for key, value in DEFAULTS.items():
        os.environ.setdefault(key, value)

    _patch_anthropic_auth()

    from cli.main import app

    sys.argv = ["tradingagents", *argv[1:]]
    app()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
