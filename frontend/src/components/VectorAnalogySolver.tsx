import { useState, useEffect } from "react";
import { Box, Typography } from "@mui/material";
import { Article } from "../types/article";
import WeaviateAutocomplete from "./WeaviateAutocomplete";
import { getNearest } from "../services/weaviateService.ts";
import ArticleCard from "./ArticleCard.tsx";
import "./VectorAnalogySolver.css";

function VectorAnalogySolver() {
  const [a, setA] = useState<Article | null>(null);
  const [b, setB] = useState<Article | null>(null);
  const [c, setC] = useState<Article | null>(null);
  const [result, setResult] = useState<Article | null>(null);

  useEffect(() => {
    const fetchVectorAnalogyResult = async () => {
      if (!a || !b || !c) {
        return;
      }
      const article = await getNearest(
        a.vector.map((_, i) => a.vector[i] - b.vector[i] + c.vector[i])
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
        <WeaviateAutocomplete
          label="This article"
          onArticleSelect={(article: Article) => setA(article)}
        />
        <Typography className="operator" variant="h3">
          -
        </Typography>
        <WeaviateAutocomplete
          label="without the vibes of this article"
          onArticleSelect={(article: Article) => setB(article)}
        />
        <Typography className="operator" variant="h3">
          +
        </Typography>
        <WeaviateAutocomplete
          label="plus the vibes of this article"
          onArticleSelect={(article: Article) => setC(article)}
        />
      </Box>
      <Typography variant="h3" className="operator">
        =
      </Typography>
      {result && <ArticleCard article={result} />}
    </div>
  );
}

export default VectorAnalogySolver;
