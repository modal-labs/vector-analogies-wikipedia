import { Article } from "../types/article";

interface Results {
  results: Article[];
}

const urlStem = `https://${
  import.meta.env.VITE_MODAL_WORKSPACE
}--modal-weaviate`;

const urlSuffix =
  import.meta.env.VITE_DEV_BACKEND === "true" ? "-dev.modal.run" : `.modal.run`;

const searchArticles = async (searchText: string) => {
  const response = await fetch(
    `${urlStem}-query${urlSuffix}?q=${encodeURIComponent(searchText)}`
  );
  const data: Results = await response.json();
  return data["results"];
};

const getNearest = async (vector: number[]) => {
  const inData = {
    vector: vector,
  };
  const response = await fetch(`${urlStem}-vector${urlSuffix}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(inData),
  });
  const data: Results = await response.json();
  return data["results"][0];
};

export { searchArticles, getNearest };
