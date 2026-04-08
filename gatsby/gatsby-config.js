module.exports = {
  siteMetadata: {
    title: "Пастелка — Новини Португалії українською",
    description: "Українськомовне медіа для українців у Португалії. Новини, аналітика, корисна інформація.",
    siteUrl: "https://pashtelka.faion.net",
    author: "Оксана Литвин",
  },
  plugins: [
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "content",
        path: `${__dirname}/../content`,
      },
    },
    {
      resolve: "gatsby-source-filesystem",
      options: {
        name: "images",
        path: `${__dirname}/static/images`,
      },
    },
    "gatsby-transformer-remark",
    "gatsby-plugin-sharp",
    "gatsby-transformer-sharp",
  ],
};
