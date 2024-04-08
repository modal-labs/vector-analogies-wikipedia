/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useRef } from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import ClearIcon from "@mui/icons-material/Clear";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { searchArticles } from "../services/weaviateService.ts";
import { Article } from "../types/article";

interface WeaviateAutocompleteProps {
  label: string;
  onArticleSelect: (article: Article) => void;
}

const WeaviateAutocomplete: React.FC<WeaviateAutocompleteProps> = ({
  label,
  onArticleSelect,
}) => {
  const [inputValue, setInputValue] = useState("");
  const [options, setOptions] = useState<Article[]>([]);
  const timer = useRef<number>();
  const [isLoading, setIsLoading] = useState(false);
  const [dotCount, setDotCount] = useState(0);

  useEffect(() => {
    const search = async (searchText: string) => {
      setIsLoading(true);
      const data = await searchArticles(searchText);
      setIsLoading(false);
      setOptions(data);
    };

    if (inputValue) {
      clearTimeout(timer.current);
      timer.current = window.setTimeout(() => search(inputValue), 300);
    } else {
      setOptions([]);
    }
  }, [inputValue]);

  useEffect(() => {
    let intervalId: number | undefined;

    if (isLoading) {
      intervalId = window.setInterval(() => {
        setDotCount((prevDotCount) => (prevDotCount + 1) % 4);
      }, 100);
    }

    return () => {
      if (intervalId !== undefined) {
        clearInterval(intervalId);
      }
    };
  }, [isLoading]);

  const getLoadingText = () =>
    `Searching Wikipedia articles on Weaviate${".".repeat(dotCount)}`;

  return (
    <Autocomplete
      options={options}
      getOptionLabel={(option) =>
        decodeURI(option.url.split(".org/")[1]) + "  ..." + option.content
      }
      isOptionEqualToValue={(option, value) => option.content === value.content}
      filterOptions={(x) => x}
      onInputChange={(_event, newInputValue) => {
        setInputValue(newInputValue);
      }}
      onChange={(_event, newValue) => {
        if (newValue) {
          onArticleSelect(newValue);
        }
      }}
      renderInput={(params) => (
        <TextField {...params} label={label} variant="outlined" />
      )}
      autoHighlight={true}
      noOptionsText={isLoading ? getLoadingText() : "No results"}
      clearIcon={<ClearIcon color="primary" />}
      popupIcon={<ArrowDropDownIcon color="primary" />}
    />
  );
};

export default WeaviateAutocomplete;
