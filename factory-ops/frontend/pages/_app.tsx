import type { AppProps } from "next/app";
import Link from "next/link";
import "../styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <nav>
        <span className="brand">FactoryOps</span>
        <Link href="/">Dashboard</Link>
        <Link href="/chat">Copilot</Link>
        <Link href="/shift-summary">Shift Summary</Link>
      </nav>
      <main>
        <Component {...pageProps} />
      </main>
    </>
  );
}
