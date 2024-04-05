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

  useEffect(() => {
    const search = async (searchText: string) => {
      setIsLoading(true);
      const data = await searchArticles(searchText);
      setOptions(data);
      setIsLoading(false);
    };

    if (inputValue) {
      clearTimeout(timer.current);
      timer.current = window.setTimeout(() => search(inputValue), 300);
    } else {
      setOptions([]);
    }
  }, [inputValue]);

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
      autoSelect={true}
      noOptionsText={isLoading ? "Searching..." : "No results"}
      clearIcon={<ClearIcon color="primary" />}
      popupIcon={<ArrowDropDownIcon color="primary" />}
    />
  );
};

export default WeaviateAutocomplete;
