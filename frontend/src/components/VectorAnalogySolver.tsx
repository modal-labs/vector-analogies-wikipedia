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
  const [result, setResult] = useState<Article | null>(helpArticle);

  useEffect(() => {
    const fetchVectorAnalogyResult = async () => {
      if (!a || !b || !c) {
        return;
      }
      const article = await getNearest(
        a.vector.map((aValue, i) => aValue + b.vector[i] - c.vector[i])
      );

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
          label="This snippet"
          onArticleSelect={(article: Article) => setA(article)}
        />
        <Typography className="operator" variant="h3">
          as
        </Typography>
        <WeaviateAutocomplete
          label="this snippet"
          onArticleSelect={(article: Article) => setB(article)}
        />
        <Typography className="operator" variant="h3">
          is to
        </Typography>
        <WeaviateAutocomplete
          label="this snippet"
          onArticleSelect={(article: Article) => setC(article)}
        />
      </Box>
      {result && (
        <ArticleCard
          article={result}
          withEllipses={result.identifier !== helpArticle.identifier}
        />
      )}
    </div>
  );
}

export default VectorAnalogySolver;
