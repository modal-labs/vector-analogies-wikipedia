import { Article } from "../types/article";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { styled } from "@mui/material/styles";

interface ArticleCardProps {
  article: Article;
  withEllipses: boolean;
}

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  margin: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
}));

const ReadMoreButton = styled(Button)(({ theme }) => ({
  marginTop: theme.spacing(2),
}));

const ArticleCard: React.FC<ArticleCardProps> = ({ article, withEllipses }) => {
  const snippet = article.content.slice(0, 750) + (withEllipses ? "..." : "");

  return (
    <StyledPaper elevation={3} sx={{ marginTop: "4rem" }}>
      <Typography variant="h5" component="h2" gutterBottom>
        {article.title}
      </Typography>
      <Typography variant="body1" gutterBottom style={{ textAlign: "left" }}>
        {snippet}
      </Typography>
      <ReadMoreButton
        variant="contained"
        color="primary"
        href={article.url}
        rel="noopener noreferrer"
      >
        Read more
      </ReadMoreButton>
    </StyledPaper>
  );
};

export default ArticleCard;
