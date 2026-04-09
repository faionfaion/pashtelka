import React from "react";
import { graphql, Link } from "gatsby";
import Layout from "../components/layout";

const IndexPage = ({ data }) => {
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
    <Layout>
      <div className="hero-section">
        <span className="badge">Новини Португалії українською</span>
        <h1>Пастелка</h1>
        <p className="subtitle">
          Щоденні новини, аналітика та корисна інформація для українців у Португалії
        </p>
      </div>

      {Object.entries(grouped).map(([date, posts]) => (
        <div key={date} className="date-group">
          <h2 className="date-header">{formatDate(date)}</h2>
          <div className="articles-grid">
            {posts.map((article) => (
              <article key={article.frontmatter.slug} className="article-card">
                <Link to={`/${article.frontmatter.slug}/`}>
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
                      <span>{article.frontmatter.author}</span>
                      <span>{Math.ceil(article.wordCount.words / 200)} хв</span>
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
      sort: { frontmatter: { date: DESC } }
      limit: 50
    ) {
      nodes {
        frontmatter {
          slug
          title
          date
          type
          author
          description
          tags
          image
        }
        wordCount {
          words
        }
      }
    }
  }
`;

export default IndexPage;

export const Head = () => (
  <>
    <title>Пастелка — Новини Португалії українською</title>
    <meta name="description" content="Щоденні новини Португалії для українців. Лісабон, Порту, Фару, Алгарве." />
    <meta property="og:title" content="Пастелка — Новини Португалії українською" />
    <meta property="og:description" content="Щоденні новини Португалії для українців. Аналітика, дайджести, корисна інформація." />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://pashtelka.faion.net" />
    <meta property="og:site_name" content="Пастелка" />
    <html lang="uk" />
  </>
);
