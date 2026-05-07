
// prefer default export if available
const preferDefault = m => (m && m.default) || m


exports.components = {
  "component---src-pages-index-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/pages/index.js")),
  "component---src-pages-pt-index-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/pages/pt/index.js")),
  "component---src-pages-pt-welcome-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/pages/pt/welcome.js")),
  "component---src-pages-uk-index-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/pages/uk/index.js")),
  "component---src-pages-uk-welcome-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/pages/uk/welcome.js")),
  "component---src-templates-article-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/templates/article.js")),
  "component---src-templates-tag-js": preferDefault(require("/home/nero/workspace/projects/pashtelka-faion-net/gatsby/src/templates/tag.js"))
}

