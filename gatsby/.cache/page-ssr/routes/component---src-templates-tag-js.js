"use strict";
exports.id = 502;
exports.ids = [502];
exports.modules = {

/***/ 1804:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Head: () => (/* binding */ Head),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(2006);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var gatsby__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(123);
/* harmony import */ var _components_layout__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(3895);
// Tag pages are UA-only for v1 (taxonomy translation is out of scope).
// Always render in UA, link to /uk/<slug>/.
const TagTemplate=({data,pageContext})=>{const{tag}=pageContext;const articles=data.allMarkdownRemark.nodes;return/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(_components_layout__WEBPACK_IMPORTED_MODULE_2__/* ["default"] */ .A,{lang:"uk",otherLocaleHref:"/pt/"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h1",null,"#",tag),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,articles.length," \u0441\u0442\u0430\u0442\u0435\u0439"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"articles-grid"},articles.map(article=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("article",{key:article.frontmatter.slug,className:"article-card"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:`/uk/${article.frontmatter.slug}/`},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h3",null,article.frontmatter.title),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"description"},article.frontmatter.description),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("time",null,article.frontmatter.date))))));};const query="867972430";/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (TagTemplate);const Head=({pageContext})=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement((react__WEBPACK_IMPORTED_MODULE_0___default().Fragment),null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("title",null,"#",pageContext.tag," \u2014 \u041F\u0430\u0448\u0442\u0435\u043B\u044C\u043A\u0430"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("html",{lang:"uk"}));

/***/ }),

/***/ 3882:
/***/ ((module) => {

module.exports = /*#__PURE__*/JSON.parse('{"siteName":"Паштелька News","siteDescription":"Українськомовне медіа для українців у Португалії. Новини, аналітика, корисна інформація.","siteTagline":"Новини Португалії українською","minRead":"хв читання","sources":"Джерела","tags":"Теги","back":"← Назад","switchToOtherLocale":"🇵🇹 Português","homeTitle":"Паштелька News — Новини Португалії українською","heroSubtitle":"Щоденні новини, аналітика та корисна інформація для українців у Португалії"}');

/***/ }),

/***/ 3895:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   A: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(2006);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var gatsby__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(123);
/* harmony import */ var _i18n_uk_json__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(3882);
/* harmony import */ var _i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(4606);
// Locale-aware Layout. Pass `lang` ("uk" | "pt") explicitly; defaults to "uk"
// so the legacy callers (index page, tag pages) keep working unchanged.
// otherLocaleHref is the link the lang-switcher chip points at; defaults to
// the matching locale homepage.
const Layout=({children,lang="uk",otherLocaleHref})=>{const i18n=lang==="pt"?_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__:_i18n_uk_json__WEBPACK_IMPORTED_MODULE_2__;const otherLang=lang==="pt"?"uk":"pt";const otherI18n=lang==="pt"?_i18n_uk_json__WEBPACK_IMPORTED_MODULE_2__:_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__;const switchHref=otherLocaleHref||(lang==="pt"?"/uk/":"/pt/");const homeHref=lang==="pt"?"/pt/":"/uk/";const tgHandle=lang==="pt"?"pastelka_pt":"pashtelka_news";return/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"site"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("header",{className:"site-header"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"container"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:homeHref,className:"site-logo"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("img",{src:"/images/logo-pashtelka-200.png",alt:"",className:"logo-icon",width:"36",height:"36"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",{className:"logo-text"},i18n.siteName)),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{className:"site-lang-chip",href:switchHref,rel:"alternate",hrefLang:otherLang,"aria-label":otherI18n.siteName},i18n.switchToOtherLocale))),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("main",{className:"container"},children),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("footer",{className:"site-footer"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"container"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"footer-brand"},i18n.siteName),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"footer-desc"},i18n.siteDescription),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{href:`https://t.me/${tgHandle}`,target:"_blank",rel:"noopener noreferrer",className:"footer-tg"},lang==="pt"?"Seguir no Telegram":"Підписатися в Telegram"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"footer-links"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{href:`/sitemap-${lang}.xml`},"Sitemap")),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"footer-copyright"},"\xA9 ",new Date().getFullYear()," ",i18n.siteName))));};/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (Layout);

/***/ }),

/***/ 4606:
/***/ ((module) => {

module.exports = /*#__PURE__*/JSON.parse('{"siteName":"Pastelka News","siteDescription":"Notícias de Portugal em português simples (B1). Para residentes, imigrantes e estudantes da língua.","siteTagline":"Notícias de Portugal em português simples","minRead":"min de leitura","sources":"Fontes","tags":"Etiquetas","back":"← Voltar","switchToOtherLocale":"🇺🇦 Українська","homeTitle":"Pastelka News — Notícias de Portugal em português simples","heroSubtitle":"Todos os dias: as notícias principais de Portugal, em frases curtas e claras."}');

/***/ })

};
;
//# sourceMappingURL=component---src-templates-tag-js.js.map