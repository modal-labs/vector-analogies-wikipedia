import { useState, useEffect } from "react";
import { Box, Typography } from "@mui/material";
import { Article } from "../types/article";
import WeaviateAutocomplete from "./WeaviateAutocomplete";
import { getNearest } from "../services/weaviateService.ts";
import ArticleCard from "./ArticleCard";
import helpArticle from "./helpArticle";
import "./VectorAnalogySolver.css";

function VectorAnalogySolver() {
  const [a, setA] = useState<Article | null>(null);
  const [b, setB] = useState<Article | null>(null);
  const [c, setC] = useState<Article | null>(null);
  const [result, setResult] = useState<Article>(helpArticle);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    const fetchVectorAnalogyResult = async () => {
      if (!a || !b || !c) {
        return;
      }

      setIsSearching(true);
      const article = await getNearest(
        a.vector.map((_, i) => a.vector[i] + b.vector[i] - c.vector[i])
      );
      setIsSearching(false);

      setResult(article);
    };

    if (a && b && c) {
      fetchVectorAnalogyResult();
    }
  }, [a, b, c]);

  return (
    <div>
      <Box className="vectorInputs">
        <Typography className="operator" variant="h3">
          What is to
        </Typography>
        <WeaviateAutocomplete
          label="this snippet"
          onArticleSelect={(article: Article) => setA(article)}
        />
        <Typography className="operator" variant="h3">
          as
        </Typography>
        <WeaviateAutocomplete
          label="this snippet"
          onArticleSelect={(article: Article) => setB(article)}
          initialInputValue="Albert Einstein"
        />
        <Typography className="operator" variant="h3">
          is to
        </Typography>
        <WeaviateAutocomplete
          label="this snippet"
          onArticleSelect={(article: Article) => setC(article)}
          initialInputValue="Physics"
        />
      </Box>
      {isSearching ? (
        <Typography variant="h4">
          <br />
          <br />
          completing analogy...
        </Typography>
      ) : (
        <ArticleCard
          article={result}
          withEllipses={result.identifier !== helpArticle.identifier}
        />
      )}
    </div>
  );
}

export default VectorAnalogySolver;
