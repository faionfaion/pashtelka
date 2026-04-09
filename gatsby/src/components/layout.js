import React from "react";
import { Link } from "gatsby";
import "./layout.css";

const Layout = ({ children }) => (
  <div className="site">
    <header className="site-header">
      <div className="container">
        <Link to="/" className="site-logo">
          <span className="logo-icon">🇵🇹</span>
          <span className="logo-text">Пастелка</span>
        </Link>
        <nav className="site-nav">
          <Link to="/">Головна</Link>
          <a
            href="https://t.me/pashtelka_news"
            target="_blank"
            rel="noopener noreferrer"
            className="tg-btn"
          >
            Telegram
          </a>
        </nav>
      </div>
    </header>
    <main className="container">{children}</main>
    <footer className="site-footer">
      <div className="container">
        <p className="footer-brand">Пастелка</p>
        <p>Новини Португалії для українців. Автор: Оксана Литвин.</p>
        <p style={{ marginTop: 8 }}>
          <a href="https://t.me/pashtelka_news">@pashtelka_news</a>
          {" | "}
          <a href="/sitemap-index.xml">Sitemap</a>
        </p>
      </div>
    </footer>
  </div>
);

export default Layout;
