import React, { useEffect } from "react";
import "../../components/welcome.css";
import heroPng from "../../images/welcome/hero-placeholder.png";
import heroWebp from "../../images/welcome/hero-placeholder.webp";
import heroAvif from "../../images/welcome/hero-placeholder.avif";

const TG_HANDLE = "pashtelka_news";
const SITE_URL = "https://pastelka.news";
const PAGE_PATH = "/uk/welcome/";
const OG_IMAGE = `${SITE_URL}/og/welcome-uk.png`;
const SWITCH_TO = "/pt/welcome/";

function preserveSearch(href) {
  if (typeof window === "undefined") return href;
  const search = window.location.search || "";
  if (!search) return href;
  return href + search;
}

const WelcomeUk = () => {
  useEffect(() => {
    if (typeof window !== "undefined" && typeof window.plausible === "function") {
      window.plausible("welcome_view");
    }
  }, []);

  const onSwitchClick = (e) => {
    if (typeof window === "undefined") return;
    const search = window.location.search;
    if (!search) return;
    e.preventDefault();
    window.location.href = SWITCH_TO + search;
  };

  return (
    <div className="wl-page">
      <header className="wl-header">
        <a className="wl-logo" href="/" aria-label="Паштелька News">
          <img src="/images/logo-pashtelka-200.png" alt="" width="28" height="28" />
          <span>Паштелька</span>
        </a>
        <a
          className="wl-lang"
          href={SWITCH_TO}
          onClick={onSwitchClick}
          aria-label="Português"
          rel="alternate"
          hrefLang="pt"
        >
          🇵🇹 Português
        </a>
      </header>

      <section className="wl-hero">
        <h1>Новини Португалії українською, без води.</h1>
        <p>10 секунд — і ти в курсі, що відбувається там, де ти живеш.</p>
        <picture>
          <source srcSet={heroAvif} type="image/avif" />
          <source srcSet={heroWebp} type="image/webp" />
          <img
            src={heroPng}
            alt="Маскот Паштелька на фоні Лісабона"
            width="940"
            height="940"
            fetchpriority="high"
            decoding="async"
          />
        </picture>
      </section>

      <section className="wl-what">
        <ul>
          <li>Щодня — головні новини Португалії: коротко, ясно.</li>
          <li>Щотижня — гайди для життя: податки, AIMA, школи, медицина.</li>
          <li>Імміграційний трекер: дедлайни, штрафи, апеляції.</li>
        </ul>
      </section>

      <nav className="wl-ctas">
        <a
          className="wl-cta-primary plausible-event-name=welcome_tg_click"
          href={`https://t.me/${TG_HANDLE}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          Підписатися в Telegram → @{TG_HANDLE}
        </a>
        <a
          className="wl-cta-secondary plausible-event-name=welcome_site_click"
          href="/"
        >
          Читати останні статті →
        </a>
      </nav>

      <footer className="wl-trust">
        Редакція з 2026 · Руслан · <a href="mailto:hello@pastelka.news">hello@pastelka.news</a>
      </footer>
    </div>
  );
};

export default WelcomeUk;

export const Head = () => (
  <>
    <html lang="uk" />
    <title>Паштелька — Новини Португалії українською</title>
    <meta name="description" content="Новини Португалії українською, без води. Підписуйся в Telegram або читай на сайті." />
    <meta name="theme-color" content="#d97706" />
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
    <link rel="canonical" href={`${SITE_URL}${PAGE_PATH}`} />
    <link rel="alternate" hrefLang="uk" href={`${SITE_URL}${PAGE_PATH}`} />
    <link rel="alternate" hrefLang="pt" href={`${SITE_URL}${SWITCH_TO}`} />
    <meta property="og:title" content="Паштелька — Новини Португалії українською" />
    <meta property="og:description" content="Новини Португалії українською, без води." />
    <meta property="og:image" content={OG_IMAGE} />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content={`${SITE_URL}${PAGE_PATH}`} />
    <meta property="og:site_name" content="Паштелька News" />
    <meta property="og:locale" content="uk_UA" />
    <meta property="og:locale:alternate" content="pt_PT" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:image" content={OG_IMAGE} />
    <meta name="twitter:title" content="Паштелька — Новини Португалії українською" />
    <meta name="twitter:description" content="Новини Португалії українською, без води." />
    <script
      defer
      data-domain="pastelka.news"
      src="https://plausible.io/js/script.tagged-events.outbound-links.js"
    />
  </>
);
