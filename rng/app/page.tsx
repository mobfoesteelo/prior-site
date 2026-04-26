import { Roller } from "@/components/Roller";
import { PRICE_LABEL } from "@/lib/constants";

export default function HomePage() {
  return (
    <main className="page">
      <header className="topbar">
        <a href="https://priorprotocol.fun" className="brand">
          <span className="brand-prompt">$</span>&nbsp;PRIOR
        </a>
        <div className="topbar-meta">
          <span>// rng</span>
          <span className="sep">│</span>
          <a href="https://priorprotocol.fun" target="_blank" rel="noopener">
            ← back to site
          </a>
        </div>
      </header>

      <section className="hero">
        <h1>
          THE WITNESS DOES NOT GUESS.
          <br />
          <span className="hero-sub">
            but the witness will roll for {PRICE_LABEL}.
          </span>
        </h1>

        <div className="hero-body">
          <p>
            one number, between <span className="hl">0</span> and{" "}
            <span className="hl">1,000</span>.
          </p>
          <p>
            settled on-chain. payment verified server-side via{" "}
            <code>@pump-fun/agent-payments-sdk</code>. no payment, no number.
          </p>
          <p className="dim">
            ~ the prior is the bet you make before the data lands.
            <br />
            ~ this is just an honest one.
          </p>
        </div>
      </section>

      <Roller />

      <section className="howto">
        <h2>HOW THIS WORKS</h2>
        <ol>
          <li>connect a solana wallet (phantom / solflare / backpack).</li>
          <li>
            click <em>roll</em>. a 0.1 SOL invoice is built server-side and
            handed to your wallet to sign.
          </li>
          <li>your wallet prompts you. sign. the tx is broadcast.</li>
          <li>
            the server polls the chain for the invoice ({"~"}10–30s). once
            confirmed, a cryptographically-random number 0–1000 is drawn and
            returned.
          </li>
          <li>
            no number is generated until the chain confirms the payment. the
            server never sees your seed phrase. it never could.
          </li>
        </ol>
      </section>

      <footer className="bottombar">
        <p>
          $PRIOR · 162 years on file ·{" "}
          <a href="https://priorprotocol.fun" target="_blank" rel="noopener">
            priorprotocol.fun
          </a>
        </p>
        <p className="fine">
          this is a memecoin utility. nothing on this page is financial advice.
          numbers are pseudo-random. the entropy source is the operating system.
        </p>
      </footer>
    </main>
  );
}
