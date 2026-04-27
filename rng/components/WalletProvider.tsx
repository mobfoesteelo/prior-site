// Client-side wallet adapter context. Wraps the app so any child component
// can call useWallet() / useConnection().
//
// Lazy-imports heavy adapter packages to keep the JS payload small.

"use client";

import { useMemo } from "react";
import {
  ConnectionProvider as _ConnectionProvider,
  WalletProvider as _SolanaWalletProvider,
} from "@solana/wallet-adapter-react";
import { WalletModalProvider as _WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import {
  PhantomWalletAdapter,
  SolflareWalletAdapter,
} from "@solana/wallet-adapter-wallets";
// Backpack is now detected automatically via the Wallet Standard (window.solana
// providers) — no explicit adapter import needed in 2025+.

// Wallet-adapter's component types lag behind React 18.3+ strict ReactNode
// (which now includes Promise<ReactNode>). Cast to any to unblock the build —
// runtime behaviour is unchanged. The npm "overrides" in package.json pins
// @types/react to 18.2.x as the proper fix; this cast is belt-and-suspenders.
const ConnectionProvider: any = _ConnectionProvider;
const SolanaWalletProvider: any = _SolanaWalletProvider;
const WalletModalProvider: any = _WalletModalProvider;

import { RPC_URL } from "@/lib/constants";

// Default styles for the adapter modal — required for the connect button
// to render properly. Imported here so consumers don't have to remember.
import "@solana/wallet-adapter-react-ui/styles.css";

export function WalletProviders({ children }: { children: React.ReactNode }) {
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
      new SolflareWalletAdapter(),
    ],
    [],
  );

  return (
    <ConnectionProvider endpoint={RPC_URL}>
      <SolanaWalletProvider wallets={wallets} autoConnect>
        <WalletModalProvider>{children}</WalletModalProvider>
      </SolanaWalletProvider>
    </ConnectionProvider>
  );
}
