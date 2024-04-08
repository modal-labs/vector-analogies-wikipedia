import { Article } from "../types/article";

const helpArticle: Article = {
  title: "What is this thing to me?",
  content:
    "This is a 'vector analogy' search engine. Use the search bars to find Wikipedia snippets to construct three of the four parts of an analogy, like 'What is to D as A is to B?'." +
    " The engine then uses the vector representations of the snippets to try to complete the analogy." +
    "Try 'What is to Paris as London is to England?'.",
  identifier: -1,
  vector: [0.0],
  url: "https://github.com/charlesfrye/vector-analogies-wikipedia",
};

export default helpArticle;
