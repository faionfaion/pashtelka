"use strict";
exports.id = 18;
exports.ids = [18];
exports.modules = {

/***/ 80:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   A: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ("/static/hero-placeholder-341a126dfbe356b1b86f862909771e12.avif");

/***/ }),

/***/ 3154:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   A: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ("/static/hero-placeholder-36fb8ba4f1107c02f8ade03e8411b1de.webp");

/***/ }),

/***/ 5417:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   A: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = ("/static/hero-placeholder-f40f5fbf3cff877cf7445e7970885e48.png");

/***/ }),

/***/ 5904:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Head: () => (/* binding */ Head),
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(2006);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _images_welcome_hero_placeholder_png__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(5417);
/* harmony import */ var _images_welcome_hero_placeholder_webp__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(3154);
/* harmony import */ var _images_welcome_hero_placeholder_avif__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(80);
const TG_HANDLE="pastelka_pt";const SITE_URL="https://pastelka.news";const PAGE_PATH="/pt/welcome/";const OG_IMAGE=`${SITE_URL}/og/welcome-pt.png`;const SWITCH_TO="/uk/welcome/";const WelcomePt=()=>{(0,react__WEBPACK_IMPORTED_MODULE_0__.useEffect)(()=>{if(typeof window!=="undefined"&&typeof window.plausible==="function"){window.plausible("welcome_view");}},[]);const onSwitchClick=e=>{if(typeof window==="undefined")return;const search=window.location.search;if(!search)return;e.preventDefault();window.location.href=SWITCH_TO+search;};return/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"wl-page"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("header",{className:"wl-header"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{className:"wl-logo",href:"/","aria-label":"Pastelka News"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("img",{src:"/images/logo-pashtelka-200.png",alt:"",width:"28",height:"28"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",null,"Pastelka")),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{className:"wl-lang",href:SWITCH_TO,onClick:onSwitchClick,"aria-label":"\u0423\u043A\u0440\u0430\u0457\u043D\u0441\u044C\u043A\u0430",rel:"alternate",hrefLang:"uk"},"\uD83C\uDDFA\uD83C\uDDE6 \u0423\u043A\u0440\u0430\u0457\u043D\u0441\u044C\u043A\u0430")),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("section",{className:"wl-hero"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h1",null,"Not\xEDcias de Portugal em ucraniano \u2014 para a comunidade."),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,"Em 10 segundos, sabe o que se passa onde voc\xEA vive."),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("picture",null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("source",{srcSet:_images_welcome_hero_placeholder_avif__WEBPACK_IMPORTED_MODULE_1__/* ["default"] */ .A,type:"image/avif"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("source",{srcSet:_images_welcome_hero_placeholder_webp__WEBPACK_IMPORTED_MODULE_2__/* ["default"] */ .A,type:"image/webp"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("img",{src:_images_welcome_hero_placeholder_png__WEBPACK_IMPORTED_MODULE_3__/* ["default"] */ .A,alt:"Mascote Pastelka com fundo de Lisboa",width:"940",height:"940",fetchpriority:"high",decoding:"async"}))),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("section",{className:"wl-what"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("ul",null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("li",null,"Todos os dias: as not\xEDcias principais de Portugal, em poucas linhas."),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("li",null,"Todas as semanas: guias \xFAteis \u2014 impostos, AIMA, escolas, sa\xFAde."),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("li",null,"Imigra\xE7\xE3o: prazos, multas, recursos."))),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("nav",{className:"wl-ctas"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{className:"wl-cta-primary plausible-event-name=welcome_tg_click",href:`https://t.me/${TG_HANDLE}`,target:"_blank",rel:"noopener noreferrer"},"Seguir no Telegram \u2192 @",TG_HANDLE),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{className:"wl-cta-secondary plausible-event-name=welcome_site_click",href:"/"},"Ler os artigos mais recentes \u2192")),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("footer",{className:"wl-trust"},"Reda\xE7\xE3o desde 2026 \xB7 Ruslan \xB7 ",/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{href:"mailto:hello@pastelka.news"},"hello@pastelka.news")));};/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (WelcomePt);const Head=()=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement((react__WEBPACK_IMPORTED_MODULE_0___default().Fragment),null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("html",{lang:"pt"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("title",null,"Pastelka \u2014 Not\xEDcias de Portugal em ucraniano"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"description",content:"Not\xEDcias de Portugal em ucraniano, para a comunidade. Siga no Telegram ou leia no site."}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"theme-color",content:"#d97706"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"viewport",content:"width=device-width,initial-scale=1,viewport-fit=cover"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"canonical",href:`${SITE_URL}${PAGE_PATH}`}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"alternate",hrefLang:"uk",href:`${SITE_URL}${SWITCH_TO}`}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("link",{rel:"alternate",hrefLang:"pt",href:`${SITE_URL}${PAGE_PATH}`}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:title",content:"Pastelka \u2014 Not\xEDcias de Portugal em ucraniano"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:description",content:"Not\xEDcias de Portugal em ucraniano, para a comunidade."}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:image",content:OG_IMAGE}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:image:width",content:"1200"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:image:height",content:"630"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:type",content:"website"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:url",content:`${SITE_URL}${PAGE_PATH}`}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:site_name",content:"Pastelka News"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:locale",content:"pt_PT"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{property:"og:locale:alternate",content:"uk_UA"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"twitter:card",content:"summary_large_image"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"twitter:image",content:OG_IMAGE}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"twitter:title",content:"Pastelka \u2014 Not\xEDcias de Portugal em ucraniano"}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("meta",{name:"twitter:description",content:"Not\xEDcias de Portugal em ucraniano, para a comunidade."}),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("script",{defer:true,"data-domain":"pastelka.news",src:"https://plausible.io/js/script.tagged-events.outbound-links.js"}));

/***/ })

};
;
//# sourceMappingURL=component---src-pages-pt-welcome-js.js.map