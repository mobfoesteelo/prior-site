# PRIOR · RNG

Payment-gated random number generator for the **$PRIOR** memecoin.

- Connect a Solana wallet (Phantom / Solflare / Backpack)
- Pay **0.1 SOL** via the pump.fun tokenized-agents invoice flow
- Receive a cryptographically random integer **between 0 and 1000**, generated server-side after the payment is verified on-chain

Built with Next.js 14 (App Router) + `@pump-fun/agent-payments-sdk@3.0.2`.

## Architecture

```
┌── browser ───────────────────┐         ┌── /api/invoice (server) ────┐
│                              │ POST    │ build buildAcceptPayment    │
│  WalletMultiButton           │ ──────▶ │ instructions                │
│  Roller component            │         │ return base64(unsigned tx)  │
│                              │ ◀────── │   + invoice {memo, times}   │
│  signTransaction (wallet UI) │         └─────────────────────────────┘
│  sendRawTransaction          │
│                              │ POST    ┌── /api/verify (server) ─────┐
│  fetch /api/verify with the  │ ──────▶ │ validateInvoicePayment      │
│  exact same invoice fields   │         │ retry up to 10× / 2s        │
│                              │ ◀────── │ on success: csprng 0-1000   │
└──────────────────────────────┘         └─────────────────────────────┘
```

The six invoice parameters (`tokenMint`, `currencyMint`, `amount`, `memo`, `startTime`, `endTime`) **must be byte-identical** between build and verify — the on-chain PDA is derived from them.

## Quick start (local)

```bash
cd rng
cp .env.example .env.local       # edit if you want to override anything
npm install
npm run dev                      # http://localhost:3000
```

You'll need a Solana wallet with at least 0.1 SOL on mainnet to actually complete the flow. For a UI-only test, just leave the wallet disconnected.

## Environment

| var | scope | purpose |
|---|---|---|
| `SOLANA_RPC_URL` | server | RPC for tx building + verification |
| `NEXT_PUBLIC_SOLANA_RPC_URL` | client | RPC for wallet adapter + send |
| `NEXT_PUBLIC_AGENT_TOKEN_MINT_ADDRESS` | client+server | PRIOR mint (`6JMRacQ3…HDpump`) |
| `NEXT_PUBLIC_CURRENCY_MINT` | client+server | wSOL or USDC mint |
| `NEXT_PUBLIC_PRICE_AMOUNT` | client+server | smallest-unit price (`100_000_000` for 0.1 SOL) |
| `NEXT_PUBLIC_PRICE_LABEL` | client | display label (`"0.1 SOL"`) |
| `INVOICE_TTL_SECONDS` | server | invoice validity window (default 86400) |

The `NEXT_PUBLIC_*` vars are exposed to the browser. The plain `SOLANA_RPC_URL` and `INVOICE_TTL_SECONDS` are server-only.

## Where the SOL goes

This app uses pump.fun's `AgenTMiC2hvxGebTsgmsD4HHBa8WEcqGFf87iwRRxLo7` program. Payments are routed by that program based on the **agent token mint** (PRIOR's CA). The SDK does not let us specify a destination wallet; funds flow per pump.fun's tokenized-agents distribution mechanic for the configured token mint.

If you want direct-to-wallet payments instead, that's a different (non-skill) implementation — would need a custom Solana program or simple SPL transfer instead of `buildAcceptPaymentInstructions`.

## Deploy on Vercel

This is a sub-project inside the larger `prior-site` repo. To deploy it as a separate Vercel project pointed at a subdomain (e.g. `rng.priorprotocol.fun`):

1. **Vercel dashboard → Add New Project → Import** the `mobfoesteelo/prior-site` repo
2. **Framework Preset:** Next.js
3. **Root Directory:** `rng`
4. **Environment Variables:** copy from `.env.example` (overriding any you care to)
5. **Deploy**, then in *Settings → Domains* add `rng.priorprotocol.fun` and update the DNS CNAME

## Future hardening

The current verify endpoint generates a fresh number every time the same paid invoice is verified. For a production app:

- Cache `(memo → number)` in a KV store (Vercel KV / Upstash). On second verify, return the cached number instead of drawing again.
- Bind the result to a session cookie or signed JWT so a paid user keeps their number across reloads without re-querying chain.
- Rate-limit `/api/invoice` per IP to prevent invoice-spam.
- Use a paid RPC (Helius / Triton) for production traffic — the public RPCs in `.env.example` are fine for testing but unreliable at volume.

## Skill source

Built from the SKILL.md at https://raw.githubusercontent.com/pump-fun/pump-fun-skills/refs/heads/main/tokenized-agents/SKILL.md (commit on `main` as of 2026-04-26).

Key SDK classes/functions used:
- `PumpAgent` (constructor with optional `Connection` for on-chain fallback)
- `PumpAgent#buildAcceptPaymentInstructions()` (server-side tx assembly)
- `PumpAgent#validateInvoicePayment()` (server-side on-chain verification)
- `getInvoiceIdPDA()` (not used directly here — the SDK derives it internally)
