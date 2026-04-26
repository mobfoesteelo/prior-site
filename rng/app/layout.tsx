import type { Metadata } from "next";
import { WalletProviders } from "@/components/WalletProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "PRIOR · RNG",
  description:
    "payment-gated random number generator. 0.1 SOL → number from 0 to 1000. " +
    "settled on-chain via @pump-fun/agent-payments-sdk.",
  robots: { index: false, follow: false },
  openGraph: {
    title: "PRIOR · RNG",
    description: "0.1 SOL. one number. 0 to 1000. settled on-chain.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" type="image/jpeg" href="/prior-pfp.jpg" />
      </head>
      <body>
        <div className="scanlines" />
        <div className="vignette" />
        <WalletProviders>{children}</WalletProviders>
      </body>
    </html>
  );
}
