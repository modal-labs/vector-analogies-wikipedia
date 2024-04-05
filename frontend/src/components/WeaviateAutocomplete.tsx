/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect, useCallback } from "react";
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

  // TODO: fix this ugly debounce
  // eslint-disable-next-line @typescript-eslint/ban-types
  const debounce = useCallback((func: Function, delay: number) => {
    let timer: number;
    return (...args: any) => {
      clearTimeout(timer);
      timer = window.setTimeout(() => func(...args), delay);
    };
  }, []);

  const search = useCallback(async (searchText: string) => {
    const data = await searchArticles(searchText);
    setOptions(data);
  }, []);

  const debouncedSearch = useCallback(debounce(search, 300), [
    search,
    debounce,
  ]);

  useEffect(() => {
    if (inputValue) {
      debouncedSearch(inputValue);
    } else {
      setOptions([]);
    }
  }, [search, inputValue, debouncedSearch]);

  return (
    <Autocomplete
      options={options}
      getOptionLabel={(option) => decodeURI(option.url.split(".org/")[1])}
      isOptionEqualToValue={(option, value) =>
        option.identifier === value.identifier
      }
      onInputChange={(_event, newInputValue, reason) => {
        if (reason != "reset") {
          setInputValue(newInputValue);
        }
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
      clearIcon={<ClearIcon color="primary" />}
      noOptionsText="Loading..."
      popupIcon={<ArrowDropDownIcon color="primary" />}
    />
  );
};

export default WeaviateAutocomplete;
