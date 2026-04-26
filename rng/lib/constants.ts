// Public constants shared across client + server.
//
// Anything mutable (RPC, mint, price) is read from env so this file can be
// committed without secrets. Defaults match the .env.example values.

import { PublicKey } from "@solana/web3.js";

export const AGENT_TOKEN_MINT = new PublicKey(
  process.env.NEXT_PUBLIC_AGENT_TOKEN_MINT_ADDRESS ||
    "6JMRacQ3JJdTNQ1qtg59f8h91aAPMjNhTtkixQHDpump",
);

// wSOL by default. To use USDC, set NEXT_PUBLIC_CURRENCY_MINT to
// EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v.
export const CURRENCY_MINT = new PublicKey(
  process.env.NEXT_PUBLIC_CURRENCY_MINT ||
    "So11111111111111111111111111111111111111112",
);

// Price in smallest currency units. wSOL = 9 decimals, USDC = 6.
export const PRICE_AMOUNT = Number(
  process.env.NEXT_PUBLIC_PRICE_AMOUNT || 100_000_000,
);

// Display label.
export const PRICE_LABEL =
  process.env.NEXT_PUBLIC_PRICE_LABEL || "0.1 SOL";

// Public RPC for the browser/wallet adapter.
export const RPC_URL =
  process.env.NEXT_PUBLIC_SOLANA_RPC_URL ||
  "https://rpc.solanatracker.io/public";

// Invoice window length, server-side only.
export const INVOICE_TTL_SECONDS = Number(
  process.env.INVOICE_TTL_SECONDS || 86400,
);
