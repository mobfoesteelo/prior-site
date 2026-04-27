// POST /api/invoice
//
// Body:    { wallet: string }   user's pubkey (base58)
// Returns: {
//   transaction: string         base64 of the unsigned legacy Transaction
//   invoice: { amount, memo, startTime, endTime }
// }
//
// The invoice fields MUST be passed back to /api/verify exactly. The PDA
// derivation depends on every byte being identical between the build and
// verify steps.

import { NextRequest, NextResponse } from "next/server";
import { PublicKey, Transaction } from "@solana/web3.js";
import { getAgent, getConnection } from "@/lib/pump-agent";
import {
  CURRENCY_MINT,
  INVOICE_TTL_SECONDS,
  PRICE_AMOUNT,
} from "@/lib/constants";

export const dynamic = "force-dynamic";   // never cache, always rebuild
export const runtime = "nodejs";          // SDK uses Node crypto + bn.js, not Edge-compatible

export async function POST(req: NextRequest) {
  let body: { wallet?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "invalid json" }, { status: 400 });
  }

  if (!body.wallet || typeof body.wallet !== "string") {
    return NextResponse.json(
      { error: "missing 'wallet' field" },
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

  // Fresh memo per request — the SKILL requires uniqueness or the program
  // rejects with InvoiceAlreadyExists. Random 32-bit unsigned int gives 4B
  // possibilities; collisions are negligible for the launch volume.
  const memo = Math.floor(Math.random() * 0xff_ff_ff_ff);
  const now = Math.floor(Date.now() / 1000);
  const startTime = now;
  const endTime = now + INVOICE_TTL_SECONDS;
  const amount = PRICE_AMOUNT;

  if (amount <= 0) {
    return NextResponse.json({ error: "invalid amount" }, { status: 500 });
  }
  if (endTime <= startTime) {
    return NextResponse.json(
      { error: "invalid time window" },
      { status: 500 },
    );
  }

  try {
    const agent = getAgent();
    const connection = getConnection();

    const instructions = await agent.buildAcceptPaymentInstructions({
      user,
      currencyMint: CURRENCY_MINT,
      amount,
      memo,
      startTime,
      endTime,
    });

    const { blockhash } = await connection.getLatestBlockhash("confirmed");
    const tx = new Transaction();
    tx.recentBlockhash = blockhash;
    tx.feePayer = user;
    tx.add(...instructions);

    const serialized = tx
      .serialize({ requireAllSignatures: false })
      .toString("base64");

    return NextResponse.json({
      transaction: serialized,
      invoice: { amount, memo, startTime, endTime },
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "unknown";
    console.error("[invoice] build error:", msg);
    return NextResponse.json(
      { error: `failed to build invoice: ${msg}` },
      { status: 500 },
    );
  }
}
