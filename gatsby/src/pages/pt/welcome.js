import React, { useEffect } from "react";
import "../../components/welcome.css";
import heroPng from "../../images/welcome/hero-placeholder.png";
import heroWebp from "../../images/welcome/hero-placeholder.webp";
import heroAvif from "../../images/welcome/hero-placeholder.avif";

const TG_HANDLE = "pashtelka_pt";
const SITE_URL = "https://pastelka.news";
const PAGE_PATH = "/pt/welcome/";
const OG_IMAGE = `${SITE_URL}/og/welcome-pt.png`;
const SWITCH_TO = "/uk/welcome/";

const WelcomePt = () => {
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
        <a className="wl-logo" href="/" aria-label="Pastelka News">
          <img src="/images/logo-pashtelka-200.png" alt="" width="28" height="28" />
          <span>Pastelka</span>
        </a>
        <a
          className="wl-lang"
          href={SWITCH_TO}
          onClick={onSwitchClick}
          aria-label="Українська"
          rel="alternate"
          hrefLang="uk"
        >
          🇺🇦 Українська
        </a>
      </header>

      <section className="wl-hero">
        <h1>Notícias de Portugal em ucraniano — para a comunidade.</h1>
        <p>Em 10 segundos, sabe o que se passa onde você vive.</p>
        <picture>
          <source srcSet={heroAvif} type="image/avif" />
          <source srcSet={heroWebp} type="image/webp" />
          <img
            src={heroPng}
            alt="Mascote Pastelka com fundo de Lisboa"
            width="940"
            height="940"
            fetchpriority="high"
            decoding="async"
          />
        </picture>
      </section>

      <section className="wl-what">
        <ul>
          <li>Todos os dias: as notícias principais de Portugal, em poucas linhas.</li>
          <li>Todas as semanas: guias úteis — impostos, AIMA, escolas, saúde.</li>
          <li>Imigração: prazos, multas, recursos.</li>
        </ul>
      </section>

      <nav className="wl-ctas">
        <a
          className="wl-cta-primary plausible-event-name=welcome_tg_click"
          href={`https://t.me/${TG_HANDLE}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          Seguir no Telegram → @{TG_HANDLE}
        </a>
        <a
          className="wl-cta-secondary plausible-event-name=welcome_site_click"
          href="/"
        >
          Ler os artigos mais recentes →
        </a>
      </nav>

      <footer className="wl-trust">
        Redação desde 2026 · Ruslan · <a href="mailto:hello@pastelka.news">hello@pastelka.news</a>
      </footer>
    </div>
  );
};

export default WelcomePt;

export const Head = () => (
  <>
    <html lang="pt" />
    <title>Pastelka — Notícias de Portugal em ucraniano</title>
    <meta name="description" content="Notícias de Portugal em ucraniano, para a comunidade. Siga no Telegram ou leia no site." />
    <meta name="theme-color" content="#d97706" />
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
    <link rel="canonical" href={`${SITE_URL}${PAGE_PATH}`} />
    <link rel="alternate" hrefLang="uk" href={`${SITE_URL}${SWITCH_TO}`} />
    <link rel="alternate" hrefLang="pt" href={`${SITE_URL}${PAGE_PATH}`} />
    <meta property="og:title" content="Pastelka — Notícias de Portugal em ucraniano" />
    <meta property="og:description" content="Notícias de Portugal em ucraniano, para a comunidade." />
    <meta property="og:image" content={OG_IMAGE} />
    <meta property="og:image:width" content="1200" />
    <meta property="og:image:height" content="630" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content={`${SITE_URL}${PAGE_PATH}`} />
    <meta property="og:site_name" content="Pastelka News" />
    <meta property="og:locale" content="pt_PT" />
    <meta property="og:locale:alternate" content="uk_UA" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:image" content={OG_IMAGE} />
    <meta name="twitter:title" content="Pastelka — Notícias de Portugal em ucraniano" />
    <meta name="twitter:description" content="Notícias de Portugal em ucraniano, para a comunidade." />
    <script
      defer
      data-domain="pastelka.news"
      src="https://plausible.io/js/script.tagged-events.outbound-links.js"
    />
  </>
);
