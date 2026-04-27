// The actual flow: connect → pay → verify → reveal.
//
// State machine:
//   idle        wallet not connected
//   ready       wallet connected, awaiting click
//   building    POST /api/invoice in flight
//   signing     wallet popup open
//   sending     tx submitted, awaiting confirmation
//   verifying   POST /api/verify polling on-chain
//   revealed    server returned the number
//   error       any step failed; show msg, allow retry

"use client";

import { useState } from "react";
import { useConnection, useWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { Transaction } from "@solana/web3.js";
import { PRICE_LABEL } from "@/lib/constants";

// Browser-safe base64 → Uint8Array (avoids Buffer which isn't a browser global)
function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

type Phase =
  | "idle"
  | "ready"
  | "building"
  | "signing"
  | "sending"
  | "verifying"
  | "revealed"
  | "error";

interface Invoice {
  amount: number;
  memo: number;
  startTime: number;
  endTime: number;
}

const PHASE_LABEL: Record<Phase, string> = {
  idle:      "// awaiting wallet connection",
  ready:     "// ready · click to roll",
  building:  "// building invoice · constructing tx...",
  signing:   "// awaiting signature in wallet...",
  sending:   "// broadcasting transaction...",
  verifying: "// verifying payment on-chain (this can take 10-30s)...",
  revealed:  "// payment verified · number drawn",
  error:     "// error",
};

export function Roller() {
  const { publicKey, signTransaction, connected } = useWallet();
  const { connection } = useConnection();

  const [phase, setPhase] = useState<Phase>(connected ? "ready" : "idle");
  const [number, setNumber] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [signature, setSignature] = useState<string>("");

  // Keep idle/ready in sync with the wallet state.
  if (!connected && phase === "ready") setPhase("idle");
  if (connected && phase === "idle") setPhase("ready");

  async function roll() {
    if (!publicKey || !signTransaction) {
      setPhase("error");
      setErrorMsg("wallet not connected");
      return;
    }

    setNumber(null);
    setErrorMsg("");
    setSignature("");

    let invoice: Invoice;

    // ── 1. build invoice ─────────────────────────────────────────────
    try {
      setPhase("building");
      const res = await fetch("/api/invoice", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ wallet: publicKey.toBase58() }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.error || `invoice build failed (${res.status})`);
      }
      const j = (await res.json()) as {
        transaction: string;
        invoice: Invoice;
      };

      invoice = j.invoice;

      // ── 2. sign in wallet ───────────────────────────────────────────
      setPhase("signing");
      const tx = Transaction.from(b64ToBytes(j.transaction));
      const signed = await signTransaction(tx);

      // ── 3. send to chain ────────────────────────────────────────────
      setPhase("sending");
      const sig = await connection.sendRawTransaction(signed.serialize(), {
        skipPreflight: false,
        preflightCommitment: "confirmed",
      });
      setSignature(sig);

      const latest = await connection.getLatestBlockhash("confirmed");
      await connection.confirmTransaction(
        { signature: sig, ...latest },
        "confirmed",
      );
    } catch (err) {
      setPhase("error");
      setErrorMsg(err instanceof Error ? err.message : "unknown error");
      return;
    }

    // ── 4. server-side verify + RNG draw ───────────────────────────
    try {
      setPhase("verifying");
      const res = await fetch("/api/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          wallet: publicKey.toBase58(),
          invoice,
        }),
      });
      const j = await res.json();
      if (!res.ok || !j.paid) {
        throw new Error(j.error || "verification failed");
      }
      setNumber(j.number);
      setPhase("revealed");
    } catch (err) {
      setPhase("error");
      setErrorMsg(err instanceof Error ? err.message : "verify failed");
    }
  }

  const busy =
    phase === "building" ||
    phase === "signing" ||
    phase === "sending" ||
    phase === "verifying";

  return (
    <div className="roller">
      <div className="roller-status">{PHASE_LABEL[phase]}</div>

      <div className="roller-frame">
        {phase === "revealed" && number !== null ? (
          <div className="roller-number">{number}</div>
        ) : (
          <div className="roller-placeholder">
            {phase === "error" ? "ERR" : "???"}
          </div>
        )}
      </div>

      {phase === "error" && (
        <div className="roller-error">~ {errorMsg}</div>
      )}

      {signature && (
        <div className="roller-tx">
          <span>~ tx: </span>
          <a
            href={`https://solscan.io/tx/${signature}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {signature.slice(0, 8)}…{signature.slice(-8)} ↗
          </a>
        </div>
      )}

      <div className="roller-actions">
        <WalletMultiButton className="prior-wallet-btn" />
        <button
          className="prior-roll-btn"
          onClick={roll}
          disabled={!connected || busy}
        >
          {busy
            ? "// processing..."
            : phase === "revealed"
              ? `> roll again · ${PRICE_LABEL}`
              : `> roll · ${PRICE_LABEL}`}
        </button>
      </div>
    </div>
  );
}
