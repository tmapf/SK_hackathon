import { FormEvent, useEffect, useId, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../api/client";
import type { OfferType } from "../types";

export interface FiltersState {
  offerType: OfferType;
  q: string;
  district: string;
  minArea: string;
  maxArea: string;
}

export interface AddressSuggestion {
  id: number;
  address_label: string;
  district: string | null;
  street: string | null;
}

interface FilterBarProps {
  filters: FiltersState;
  districts: string[];
  onChange: (next: FiltersState) => void;
  onSubmit: () => void;
  onClear: () => void;
  onSelectSuggestion: (suggestion: AddressSuggestion) => void;
}

export function FilterBar({
  filters,
  districts,
  onChange,
  onSubmit,
  onClear,
  onSelectSuggestion,
}: FilterBarProps) {
  const { t } = useTranslation();
  const listId = useId();
  const rootRef = useRef<HTMLLabelElement | null>(null);
  const [open, setOpen] = useState(false);
  const [debouncedQ, setDebouncedQ] = useState(filters.q);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedQ(filters.q.trim()), 200);
    return () => window.clearTimeout(timer);
  }, [filters.q]);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  const suggestionsQuery = useQuery({
    queryKey: ["address-suggestions", filters.offerType, debouncedQ],
    enabled: debouncedQ.length >= 2,
    queryFn: () => {
      const params = new URLSearchParams({
        q: debouncedQ,
        offer_type: filters.offerType,
        limit: "8",
      });
      return apiFetch<AddressSuggestion[]>(`/api/address-suggestions?${params}`);
    },
  });

  const suggestions = suggestionsQuery.data ?? [];
  const showSuggestions = open && debouncedQ.length >= 2 && suggestions.length > 0;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setOpen(false);
    onSubmit();
  }

  function pickSuggestion(suggestion: AddressSuggestion) {
    onChange({
      ...filters,
      q: suggestion.street || suggestion.address_label,
      district: suggestion.district || filters.district,
    });
    setOpen(false);
    onSelectSuggestion(suggestion);
  }

  return (
    <form className="filters" onSubmit={handleSubmit}>
      <label className="filter-field search-field" ref={rootRef}>
        <span className="filter-label">{t("search")}</span>
        <input
          value={filters.q}
          role="combobox"
          aria-expanded={showSuggestions}
          aria-controls={listId}
          aria-autocomplete="list"
          autoComplete="off"
          onFocus={() => setOpen(true)}
          onChange={(event) => {
            onChange({ ...filters, q: event.target.value });
            setOpen(true);
          }}
          placeholder={t("searchPlaceholder")}
        />
        {showSuggestions && (
          <ul id={listId} className="search-suggestions" role="listbox">
            {suggestions.map((suggestion) => (
              <li key={suggestion.id} role="option">
                <button
                  type="button"
                  className="search-suggestion"
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => pickSuggestion(suggestion)}
                >
                  <span>{suggestion.address_label}</span>
                  {suggestion.district ? (
                    <small>{suggestion.district}</small>
                  ) : null}
                </button>
              </li>
            ))}
          </ul>
        )}
      </label>
      <label className="filter-field">
        <span className="filter-label">{t("district")}</span>
        <select
          value={filters.district}
          onChange={(event) =>
            onChange({ ...filters, district: event.target.value })
          }
        >
          <option value="">{t("allDistricts")}</option>
          {districts.map((district) => (
            <option key={district} value={district}>
              {district}
            </option>
          ))}
        </select>
      </label>
      <label className="filter-field">
        <span className="filter-label">{t("minArea")}</span>
        <input
          type="number"
          min={0}
          value={filters.minArea}
          onChange={(event) =>
            onChange({ ...filters, minArea: event.target.value })
          }
        />
      </label>
      <label className="filter-field">
        <span className="filter-label">{t("maxArea")}</span>
        <input
          type="number"
          min={0}
          value={filters.maxArea}
          onChange={(event) =>
            onChange({ ...filters, maxArea: event.target.value })
          }
        />
      </label>
      <div className="filter-field actions">
        <span className="filter-label" aria-hidden="true">
          &nbsp;
        </span>
        <div className="action-buttons">
          <button className="btn" type="submit">
            {t("applyFilters")}
          </button>
          <button className="btn secondary" type="button" onClick={onClear}>
            {t("clearFilters")}
          </button>
        </div>
      </div>
    </form>
  );
}
