// POST /api/verify
//
// Body: {
//   wallet: string,                 base58 pubkey of the payer
//   invoice: {
//     amount: number,
//     memo: number,
//     startTime: number,
//     endTime: number,
//   }
// }
//
// Polls validateInvoicePayment with retries to absorb confirmation lag.
// On success, generates a server-side RNG in [0, 1000] (inclusive) and
// returns it. The RNG is only generated AFTER on-chain verification.
//
// Note: this endpoint is naive — it generates a fresh number every time
// the same paid invoice is verified. For a production app you'd cache
// the (memo → number) mapping so a refresh doesn't reveal a new draw.
// For the launch demo, the cost-of-replay is one paid SOL, so we leave
// it simple. See README "Future hardening" section.

import { NextRequest, NextResponse } from "next/server";
import { PublicKey } from "@solana/web3.js";
import crypto from "crypto";
import { getAgent } from "@/lib/pump-agent";
import { CURRENCY_MINT } from "@/lib/constants";

export const dynamic = "force-dynamic";

const MAX_ATTEMPTS = 10;
const RETRY_DELAY_MS = 2000;

function secureRandom0to1000(): number {
  // crypto-grade: 4 bytes → uint32 → mod 1001. Slight modulo bias is
  // negligible for a 1001-sided die from a 32-bit space.
  const buf = crypto.randomBytes(4);
  const u32 = buf.readUInt32BE(0);
  return u32 % 1001;
}

export async function POST(req: NextRequest) {
  let body: {
    wallet?: string;
    invoice?: {
      amount?: number;
      memo?: number;
      startTime?: number;
      endTime?: number;
    };
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  if (!body.wallet) {
    return NextResponse.json({ error: "missing wallet" }, { status: 400 });
  }
  const inv = body.invoice;
  if (
    !inv ||
    typeof inv.amount !== "number" ||
    typeof inv.memo !== "number" ||
    typeof inv.startTime !== "number" ||
    typeof inv.endTime !== "number"
  ) {
    return NextResponse.json(
      { error: "missing or malformed invoice" },
      { status: 400 },
    );
  }

  let user: PublicKey;
  try {
    user = new PublicKey(body.wallet);
  } catch {
    return NextResponse.json(
      { error: "invalid wallet pubkey" },
      { status: 400 },
    );
  }

  const agent = getAgent();

  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
      const verified = await agent.validateInvoicePayment({
        user,
        currencyMint: CURRENCY_MINT,
        amount: inv.amount,
        memo: inv.memo,
        startTime: inv.startTime,
        endTime: inv.endTime,
      });
      if (verified) {
        const number = secureRandom0to1000();
        return NextResponse.json({
          paid: true,
          number,
          attempts: attempt + 1,
        });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "unknown";
      console.error(`[verify] attempt ${attempt + 1} error:`, msg);
      // fall through to retry
    }
    if (attempt < MAX_ATTEMPTS - 1) {
      await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
    }
  }

  return NextResponse.json(
    {
      paid: false,
      error:
        "payment not found on-chain after " +
        MAX_ATTEMPTS +
        " attempts. " +
        "if you just signed, retry in ~10 seconds.",
    },
    { status: 402 },
  );
}
