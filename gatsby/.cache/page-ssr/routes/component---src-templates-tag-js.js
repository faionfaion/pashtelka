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
const TagTemplate=({data,pageContext})=>{const{tag}=pageContext;const articles=data.allMarkdownRemark.nodes;return/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(_components_layout__WEBPACK_IMPORTED_MODULE_2__/* ["default"] */ .A,null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h1",null,"#",tag),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,articles.length," \u0441\u0442\u0430\u0442\u0435\u0439"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"articles-grid"},articles.map(article=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("article",{key:article.frontmatter.slug,className:"article-card"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:`/${article.frontmatter.slug}/`},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("h3",null,article.frontmatter.title),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",{className:"description"},article.frontmatter.description),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("time",null,article.frontmatter.date))))));};const query="444913933";/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (TagTemplate);const Head=({pageContext})=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement((react__WEBPACK_IMPORTED_MODULE_0___default().Fragment),null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("title",null,"#",pageContext.tag," \u2014 \u041F\u0430\u0441\u0442\u0435\u043B\u043A\u0430"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("html",{lang:"uk"}));

/***/ }),

/***/ 3895:
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   A: () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(2006);
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var gatsby__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(123);
const Layout=({children})=>/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"site"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("header",{className:"site-header"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"container"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:"/",className:"site-logo"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",{className:"logo-icon"},"\uD83C\uDDF5\uD83C\uDDF9"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("span",{className:"logo-text"},"\u041F\u0430\u0441\u0442\u0435\u043B\u043A\u0430")),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("nav",{className:"site-nav"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement(gatsby__WEBPACK_IMPORTED_MODULE_1__.Link,{to:"/"},"\u0413\u043E\u043B\u043E\u0432\u043D\u0430"),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{href:"https://t.me/pashtelka_news",target:"_blank",rel:"noopener noreferrer"},"Telegram")))),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("main",{className:"container"},children),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("footer",{className:"site-footer"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("div",{className:"container"},/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,"\u041F\u0430\u0441\u0442\u0435\u043B\u043A\u0430 \u2014 \u043D\u043E\u0432\u0438\u043D\u0438 \u041F\u043E\u0440\u0442\u0443\u0433\u0430\u043B\u0456\u0457 \u0434\u043B\u044F \u0443\u043A\u0440\u0430\u0457\u043D\u0446\u0456\u0432. \u0410\u0432\u0442\u043E\u0440: \u041E\u043A\u0441\u0430\u043D\u0430 \u041B\u0438\u0442\u0432\u0438\u043D."),/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("p",null,/*#__PURE__*/react__WEBPACK_IMPORTED_MODULE_0___default().createElement("a",{href:"https://t.me/pashtelka_news"},"@pashtelka_news")))));/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (Layout);

/***/ })

};
;
//# sourceMappingURL=component---src-templates-tag-js.js.map