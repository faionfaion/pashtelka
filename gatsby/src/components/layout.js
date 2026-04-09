import React from "react";
import { Link } from "gatsby";
import "./layout.css";

const Layout = ({ children }) => (
  <div className="site">
    <header className="site-header">
      <div className="container">
        <Link to="/" className="site-logo">
          <img
            src="/images/logo-pashtelka-200.png"
            alt=""
            className="logo-icon"
            width="36"
            height="36"
          />
          <span className="logo-text">Паштелька News</span>
        </Link>
      </div>
    </header>
    <main className="container">{children}</main>
    <footer className="site-footer">
      <div className="container">
        <p className="footer-brand">Паштелька News</p>
        <p className="footer-desc">
          Щоденні новини Португалії для українців.
          <br />
          Лісабон, Порту, Фару, Алгарве.
        </p>
        <a
          href="https://t.me/pashtelka_news"
          target="_blank"
          rel="noopener noreferrer"
          className="footer-tg"
        >
          Підписатися в Telegram
        </a>
        <div className="footer-links">
          <a href="/sitemap-index.xml">Sitemap</a>
        </div>
        <p className="footer-copyright">
          &copy; {new Date().getFullYear()} Паштелька News
        </p>
      </div>
    </footer>
  </div>
);

export default Layout;
