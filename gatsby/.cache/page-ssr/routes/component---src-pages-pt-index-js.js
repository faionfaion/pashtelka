"use strict";
exports.id = 386;
exports.ids = [386];
exports.modules = {

/***/ 688:
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
/* harmony import */ var _i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(4606);
const PtIndex=({data})=>{const articles=data.allMarkdownRemark.nodes;const grouped={};articles.forEach(article=>{const date=article.frontmatter.date;if(!grouped[date])grouped[date]=[];grouped[date].push(article);});const formatDate=dateStr=>{const d=new Date(dateStr+"T12:00:00");return d.toLocaleDateString("pt-PT",{weekday:"long",year:"numeric",month:"long",day:"numeric"});};return/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(_components_layout__WEBPACK_IMPORTED_MODULE_2__/* ["default"] */ .A,{lang:"pt",otherLocaleHref:"/uk/"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"hero-section"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",{className:"badge"},_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.siteTagline),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"subtitle"},_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.heroSubtitle)),articles.length===0&&/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"empty-state"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,"Em breve: artigos em portugu\xEAs simples (B1)."),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:"/uk/"},_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.switchToOtherLocale," \u2192"))),Object.entries(grouped).map(([date,posts])=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{key:date,className:"date-group"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h2",{className:"date-header"},formatDate(date)),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"articles-grid"},posts.map(article=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("article",{key:article.frontmatter.slug,className:"article-card"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:`/pt/${article.frontmatter.slug}/`},article.frontmatter.image&&/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("img",{className:"card-image",src:article.frontmatter.image,alt:"",loading:"lazy"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"card-content"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",{className:`type-badge type-${article.frontmatter.type}`},article.frontmatter.type),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h3",null,article.frontmatter.title),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"description"},article.frontmatter.description),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"meta"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",null,Math.ceil(article.wordCount.words/200)," ",_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.minRead))))))))));};const query="756547245";/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (PtIndex);const Head=()=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement((react__WEBPACK_IMPORTED_MODULE_0___default().Fragment),null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("title",null,_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.homeTitle),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"description",content:_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.siteDescription}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:title",content:_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.homeTitle}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:description",content:_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.siteDescription}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:type",content:"website"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:url",content:"https://pastelka.news/pt/"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:site_name",content:_i18n_pt_json__WEBPACK_IMPORTED_MODULE_3__.siteName}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:locale",content:"pt_PT"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:locale:alternate",content:"uk_UA"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"canonical",href:"https://pastelka.news/pt/"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"alternate",hrefLang:"uk",href:"https://pastelka.news/uk/"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"alternate",hrefLang:"pt",href:"https://pastelka.news/pt/"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"alternate",hrefLang:"x-default",href:"https://pastelka.news/uk/"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("html",{lang:"pt"}));

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
//# sourceMappingURL=component---src-pages-pt-index-js.js.map