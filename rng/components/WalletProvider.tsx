// Client-side wallet adapter context. Wraps the app so any child component
// can call useWallet() / useConnection().
//
// Lazy-imports heavy adapter packages to keep the JS payload small.

"use client";

import { useMemo } from "react";
import {
  ConnectionProvider,
  WalletProvider as SolanaWalletProvider,
} from "@solana/wallet-adapter-react";
import { WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import {
  PhantomWalletAdapter,
  SolflareWalletAdapter,
  BackpackWalletAdapter,
} from "@solana/wallet-adapter-wallets";

import { RPC_URL } from "@/lib/constants";

// Default styles for the adapter modal — required for the connect button
// to render properly. Imported here so consumers don't have to remember.
import "@solana/wallet-adapter-react-ui/styles.css";

export function WalletProviders({ children }: { children: React.ReactNode }) {
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
      new SolflareWalletAdapter(),
      new BackpackWalletAdapter(),
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
