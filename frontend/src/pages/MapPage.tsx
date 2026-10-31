import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../api/client";
import {
  FilterBar,
  type AddressSuggestion,
  type FiltersState,
} from "../components/FilterBar";
import { PropertyMap } from "../components/PropertyMap";
import { PropertyPanel } from "../components/PropertyPanel";
import type {
  Category,
  FeatureCollection,
  OfferType,
  PropertyFeature,
  PublicConfig,
} from "../types";

const defaultFilters: FiltersState = {
  offerType: "wynajem",
  q: "",
  district: "",
  minArea: "",
  maxArea: "",
};

export function MapPage() {
  const { t, i18n } = useTranslation();
  const [filters, setFilters] = useState<FiltersState>(defaultFilters);
  const [applied, setApplied] = useState<FiltersState>(defaultFilters);
  const [selected, setSelected] = useState<PropertyFeature | null>(null);
  const [panelFeature, setPanelFeature] = useState<PropertyFeature | null>(null);
  const [panelVisible, setPanelVisible] = useState(false);
  const [pendingSelectionId, setPendingSelectionId] = useState<number | null>(null);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    params.set("offer_type", applied.offerType);
    if (applied.q.trim()) params.set("q", applied.q.trim());
    if (applied.district) params.set("district", applied.district);
    if (applied.minArea) params.set("min_area", applied.minArea);
    if (applied.maxArea) params.set("max_area", applied.maxArea);
    return params.toString();
  }, [applied]);

  const configQuery = useQuery({
    queryKey: ["config"],
    queryFn: () => apiFetch<PublicConfig>("/api/config"),
  });

  const categoriesQuery = useQuery({
    queryKey: ["categories"],
    queryFn: () => apiFetch<Category[]>("/api/categories"),
  });

  const districtsQuery = useQuery({
    queryKey: ["districts", applied.offerType],
    queryFn: () =>
      apiFetch<string[]>(`/api/districts?offer_type=${applied.offerType}`),
  });

  const propertiesQuery = useQuery({
    queryKey: ["properties", queryString],
    queryFn: () => apiFetch<FeatureCollection>(`/api/properties?${queryString}`),
  });

  const features = propertiesQuery.data?.features ?? [];
  const panelOpen = Boolean(panelFeature);

  useEffect(() => {
    if (pendingSelectionId == null || !propertiesQuery.data) return;
    const match = propertiesQuery.data.features.find(
      (feature) => feature.id === pendingSelectionId,
    );
    if (match) {
      setSelected(match);
      setPendingSelectionId(null);
    }
  }, [pendingSelectionId, propertiesQuery.data]);

  useEffect(() => {
    let timeoutId: number | undefined;
    let rafOuter = 0;
    let rafInner = 0;

    if (selected) {
      setPanelFeature(selected);
      rafOuter = window.requestAnimationFrame(() => {
        rafInner = window.requestAnimationFrame(() => setPanelVisible(true));
      });
    } else {
      setPanelVisible(false);
      timeoutId = window.setTimeout(() => setPanelFeature(null), 320);
    }

    return () => {
      window.cancelAnimationFrame(rafOuter);
      window.cancelAnimationFrame(rafInner);
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [selected]);

  function setOfferType(offerType: OfferType) {
    const next = { ...filters, offerType, district: "" };
    setFilters(next);
    setApplied(next);
    setSelected(null);
    setPendingSelectionId(null);
  }

  function switchLanguage(lang: "pl" | "en") {
    void i18n.changeLanguage(lang);
    localStorage.setItem("warsaw-lang", lang);
  }

  function handleSelectSuggestion(suggestion: AddressSuggestion) {
    const next = {
      ...filters,
      q: suggestion.street || suggestion.address_label,
      district: suggestion.district || "",
    };
    setFilters(next);
    setApplied(next);
    setPendingSelectionId(suggestion.id);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <h1>{t("brand")}</h1>
          <p>{t("tagline")}</p>
        </div>
        <div className="topbar-actions">
          <div className="offer-toggle" role="group" aria-label="Offer type">
            <button
              type="button"
              className={filters.offerType === "wynajem" ? "active" : ""}
              onClick={() => setOfferType("wynajem")}
            >
              {t("rent")}
            </button>
            <button
              type="button"
              className={filters.offerType === "sprzedaz" ? "active" : ""}
              onClick={() => setOfferType("sprzedaz")}
            >
              {t("sale")}
            </button>
          </div>
          <div className="lang-switch" role="group" aria-label={t("language")}>
            <button
              type="button"
              className={i18n.language === "pl" ? "active" : ""}
              onClick={() => switchLanguage("pl")}
            >
              PL
            </button>
            <button
              type="button"
              className={i18n.language === "en" ? "active" : ""}
              onClick={() => switchLanguage("en")}
            >
              EN
            </button>
          </div>
          <Link className="btn secondary" to="/admin">
            {t("admin")}
          </Link>
        </div>
      </header>

      <FilterBar
        filters={filters}
        districts={districtsQuery.data ?? []}
        onChange={setFilters}
        onSubmit={() => {
          setApplied(filters);
          setSelected(null);
          setPendingSelectionId(null);
        }}
        onClear={() => {
          const cleared = { ...defaultFilters, offerType: filters.offerType };
          setFilters(cleared);
          setApplied(cleared);
          setSelected(null);
          setPendingSelectionId(null);
        }}
        onSelectSuggestion={handleSelectSuggestion}
      />

      <div className={`workspace ${panelOpen ? "panel-open" : "panel-closed"}`}>
        <section className="map-pane" aria-label="Map">
          {(propertiesQuery.isLoading || propertiesQuery.isFetching) && (
            <div className="map-status">{t("loading")}</div>
          )}
          {propertiesQuery.isError && (
            <div className="map-status">
              <p>{t("error")}</p>
              <button className="btn" type="button" onClick={() => propertiesQuery.refetch()}>
                {t("retry")}
              </button>
            </div>
          )}
          {!propertiesQuery.isLoading && !features.length && !propertiesQuery.isError && (
            <div className="map-status">
              {applied.q || applied.district || applied.minArea || applied.maxArea
                ? t("emptyFiltered")
                : t("empty")}
            </div>
          )}
          <PropertyMap
            data={propertiesQuery.data}
            config={configQuery.data}
            selectedId={selected?.id ?? null}
            onSelect={setSelected}
          />
        </section>

        {panelFeature ? (
          <PropertyPanel
            property={panelFeature.properties}
            categories={categoriesQuery.data ?? []}
            turnstileSiteKey={configQuery.data?.turnstile_site_key || ""}
            visible={panelVisible}
            onClose={() => setSelected(null)}
          />
        ) : null}
      </div>

      <div className={`bottom-sheet ${panelVisible ? "open" : ""}`} aria-hidden={!panelVisible}>
        {panelFeature ? (
          <PropertyPanel
            compact
            property={panelFeature.properties}
            categories={categoriesQuery.data ?? []}
            turnstileSiteKey={configQuery.data?.turnstile_site_key || ""}
            onClose={() => setSelected(null)}
          />
        ) : null}
      </div>

      <footer className="footer">
        <span>
          {t("propertiesCount", { count: features.length })}
          {" · "}
          {t("lastSync")}:{" "}
          {configQuery.data?.last_successful_sync_at
            ? new Date(configQuery.data.last_successful_sync_at).toLocaleString(
                i18n.language,
              )
            : t("unknown")}
        </span>
        <Link to="/privacy">{t("privacy")}</Link>
      </footer>
    </div>
  );
}
