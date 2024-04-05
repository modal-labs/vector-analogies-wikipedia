import { Article } from "../types/article";

interface Results {
  results: Article[];
}

const searchArticles = async (searchText: string) => {
  const response = await fetch(
    `https://charles-modal-labs--modal-weaviate-query.modal.run?q=${encodeURIComponent(
      searchText
    )}`
  );
  const data: Results = await response.json();
  return data["results"];
};

const getNearest = async (vector: number[]) => {
  const inData = {
    vector: vector,
  };
  const response = await fetch(
    `https://charles-modal-labs--modal-weaviate-vector.modal.run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(inData),
    }
  );
  const data: Results = await response.json();
  return data["results"][0];
};

export { searchArticles, getNearest };
