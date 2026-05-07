import React from "react";
import { Link } from "gatsby";
import "./layout.css";
import uk from "../i18n/uk.json";
import pt from "../i18n/pt.json";

// Locale-aware Layout. Pass `lang` ("uk" | "pt") explicitly; defaults to "uk"
// so the legacy callers (index page, tag pages) keep working unchanged.
// otherLocaleHref is the link the lang-switcher chip points at; defaults to
// the matching locale homepage.
const Layout = ({ children, lang = "uk", otherLocaleHref }) => {
  const i18n = lang === "pt" ? pt : uk;
  const otherLang = lang === "pt" ? "uk" : "pt";
  const otherI18n = lang === "pt" ? uk : pt;
  const switchHref = otherLocaleHref || (lang === "pt" ? "/uk/" : "/pt/");
  const homeHref = lang === "pt" ? "/pt/" : "/uk/";
  const tgHandle = lang === "pt" ? "pashtelka_pt" : "pashtelka_news";

  return (
    <div className="site">
      <header className="site-header">
        <div className="container">
          <Link to={homeHref} className="site-logo">
            <img
              src="/images/logo-pashtelka-200.png"
              alt=""
              className="logo-icon"
              width="36"
              height="36"
            />
            <span className="logo-text">{i18n.siteName}</span>
          </Link>
          <a
            className="site-lang-chip"
            href={switchHref}
            rel="alternate"
            hrefLang={otherLang}
            aria-label={otherI18n.siteName}
          >
            {i18n.switchToOtherLocale}
          </a>
        </div>
      </header>
      <main className="container">{children}</main>
      <footer className="site-footer">
        <div className="container">
          <p className="footer-brand">{i18n.siteName}</p>
          <p className="footer-desc">{i18n.siteDescription}</p>
          <a
            href={`https://t.me/${tgHandle}`}
            target="_blank"
            rel="noopener noreferrer"
            className="footer-tg"
          >
            {lang === "pt" ? "Seguir no Telegram" : "Підписатися в Telegram"}
          </a>
          <div className="footer-links">
            <a href={`/sitemap-${lang}.xml`}>Sitemap</a>
          </div>
          <p className="footer-copyright">
            &copy; {new Date().getFullYear()} {i18n.siteName}
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
