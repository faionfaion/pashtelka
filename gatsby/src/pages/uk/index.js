import React from "react";
import { graphql, Link } from "gatsby";
import Layout from "../../components/layout";
import uk from "../../i18n/uk.json";

const UkIndex = ({ data }) => {
  const articles = data.allMarkdownRemark.nodes;

  const grouped = {};
  articles.forEach((article) => {
    const date = article.frontmatter.date;
    if (!grouped[date]) grouped[date] = [];
    grouped[date].push(article);
  });

  const formatDate = (dateStr) => {
    const d = new Date(dateStr + "T12:00:00");
    return d.toLocaleDateString("uk-UA", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <Layout lang="uk" otherLocaleHref="/pt/">
      <div className="hero-section">
        <span className="badge">{uk.siteTagline}</span>
        <p className="subtitle">{uk.heroSubtitle}</p>
      </div>

      {Object.entries(grouped).map(([date, posts]) => (
        <div key={date} className="date-group">
          <h2 className="date-header">{formatDate(date)}</h2>
          <div className="articles-grid">
            {posts.map((article) => (
              <article key={article.frontmatter.slug} className="article-card">
                <Link to={`/uk/${article.frontmatter.slug}/`}>
                  {article.frontmatter.image && (
                    <img
                      className="card-image"
                      src={article.frontmatter.image}
                      alt=""
                      loading="lazy"
                    />
                  )}
                  <div className="card-content">
                    <span className={`type-badge type-${article.frontmatter.type}`}>
                      {article.frontmatter.type}
                    </span>
                    <h3>{article.frontmatter.title}</h3>
                    <p className="description">{article.frontmatter.description}</p>
                    <div className="meta">
                      <span>{Math.ceil(article.wordCount.words / 200)} {uk.minRead}</span>
                    </div>
                  </div>
                </Link>
              </article>
            ))}
          </div>
        </div>
      ))}
    </Layout>
  );
};

export const query = graphql`
  {
    allMarkdownRemark(
      filter: { frontmatter: { lang: { in: ["ua", "uk"] } } }
      sort: { frontmatter: { date: DESC } }
      limit: 60
    ) {
      nodes {
        frontmatter {
          slug
          title
          date
          type
          description
          tags
          image
          lang
        }
        wordCount {
          words
        }
      }
    }
  }
`;

export default UkIndex;

export const Head = () => (
  <>
    <title>{uk.homeTitle}</title>
    <meta name="description" content={uk.siteDescription} />
    <meta property="og:title" content={uk.homeTitle} />
    <meta property="og:description" content={uk.siteDescription} />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://pastelka.news/uk/" />
    <meta property="og:site_name" content={uk.siteName} />
    <meta property="og:locale" content="uk_UA" />
    <meta property="og:locale:alternate" content="pt_PT" />
    <link rel="canonical" href="https://pastelka.news/uk/" />
    <link rel="alternate" hrefLang="uk" href="https://pastelka.news/uk/" />
    <link rel="alternate" hrefLang="pt" href="https://pastelka.news/pt/" />
    <link rel="alternate" hrefLang="x-default" href="https://pastelka.news/uk/" />
    <html lang="uk" />
  </>
);
