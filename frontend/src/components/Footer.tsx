// Footer.tsx
import React from "react";
import { Box, Link, Typography } from "@mui/material";

const footerLinkStyles = {
  color: "primary.main",
  fontWeight: "600",
  textDecoration: "none",
  "&:hover": {
    textDecoration: "underline",
  },
};

const Footer: React.FC = () => (
  <Box
    component="footer"
    sx={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
    }}
  >
    <Typography variant="body1">
      Powered by{" "}
      <Link
        href="https://weaviate.io"
        target="_blank"
        rel="noopener noreferrer"
        sx={footerLinkStyles}
      >
        Weaviate
      </Link>{" "}
      and{" "}
      <Link
        href="https://modal.com"
        target="_blank"
        rel="noopener noreferrer"
        sx={footerLinkStyles}
      >
        Modal
      </Link>
      .
    </Typography>
  </Box>
);

export default Footer;
