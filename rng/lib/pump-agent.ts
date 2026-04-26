// Server-side singleton for the @pump-fun/agent-payments-sdk PumpAgent.
//
// Keeps a single Connection alive across requests in the same warm lambda /
// node instance. The RPC URL must be set in env (SOLANA_RPC_URL).
//
// IMPORTANT: never import this file from a client component. It uses the
// server-only env var SOLANA_RPC_URL.

import { Connection } from "@solana/web3.js";
import { PumpAgent } from "@pump-fun/agent-payments-sdk";
import { AGENT_TOKEN_MINT } from "./constants";

let _agent: PumpAgent | null = null;
let _connection: Connection | null = null;

function rpcUrl(): string {
  const url = process.env.SOLANA_RPC_URL;
  if (!url) {
    throw new Error(
      "SOLANA_RPC_URL is not set on the server. Configure it in .env.local " +
        "or Vercel project settings.",
    );
  }
  return url;
}

export function getConnection(): Connection {
  if (!_connection) {
    _connection = new Connection(rpcUrl(), "confirmed");
  }
  return _connection;
}

export function getAgent(): PumpAgent {
  if (!_agent) {
    _agent = new PumpAgent(AGENT_TOKEN_MINT, "mainnet", getConnection());
  }
  return _agent;
}
