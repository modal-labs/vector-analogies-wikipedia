/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from "react";
import Autocomplete from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import ClearIcon from "@mui/icons-material/Clear";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { searchArticles } from "../services/weaviateService.ts";
import { Article } from "../types/article";

interface WeaviateAutocompleteProps {
  label: string;
  onArticleSelect: (article: Article) => void;
  // include other props as needed
}

const WeaviateAutocomplete: React.FC<WeaviateAutocompleteProps> = ({
  label,
  onArticleSelect,
}) => {
  const [inputValue, setInputValue] = useState("");
  const [options, setOptions] = useState<Article[]>([]);

  useEffect(() => {
    const search = async (searchText: string) => {
      const data = await searchArticles(searchText);
      setOptions(data);
    };

    if (inputValue) {
      search(inputValue);
    } else {
      setOptions([]);
    }
  }, [inputValue]);

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
