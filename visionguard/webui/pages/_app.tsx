import type { AppProps } from "next/app";
import Link from "next/link";
import "../styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <>
      <nav>
        <span className="brand">VisionGuard</span>
        <Link href="/">Inspect</Link>
        <Link href="/trends">Trends</Link>
      </nav>
      <main>
        <Component {...pageProps} />
      </main>
    </>
  );
}
