import { useTranslation } from "react-i18next";
import { useTranslatedValue } from "../hooks/useTranslatedValue";
import type { Category, PropertyFeatureProperties } from "../types";
import { SuggestionForm } from "./SuggestionForm";

interface PropertyPanelProps {
  property: PropertyFeatureProperties;
  categories: Category[];
  turnstileSiteKey: string;
  onClose: () => void;
  compact?: boolean;
  visible?: boolean;
}

export function PropertyPanel({
  property,
  categories,
  turnstileSiteKey,
  onClose,
  compact = false,
  visible = true,
}: PropertyPanelProps) {
  const { t } = useTranslation();
  const intendedUse = useTranslatedValue("intended_use", property.intended_use);
  const developmentState = useTranslatedValue(
    "development_state",
    property.development_state,
  );

  const useLabel =
    property.offer_type === "wynajem" ? t("intendedUse") : t("developmentState");
  const useValue =
    property.offer_type === "wynajem" ? intendedUse : developmentState;

  return (
    <aside
      className={
        compact
          ? "panel panel-compact"
          : `panel desktop-panel${visible ? " is-visible" : ""}`
      }
      aria-label={t("selectedProperty")}
    >
      <div className="panel-header">
        <h2>{t("selectedProperty")}</h2>
        <button className="btn secondary" type="button" onClick={onClose}>
          {t("close")}
        </button>
      </div>
      <dl className="detail-grid">
        <div>
          <dt>{t("address")}</dt>
          <dd>{property.address_label}</dd>
        </div>
        <div>
          <dt>{t("district")}</dt>
          <dd>{property.district || t("unknown")}</dd>
        </div>
        <div>
          <dt>{t("area")}</dt>
          <dd>
            {property.area_m2 != null
              ? `${property.area_m2} ${t("m2")}`
              : t("unknown")}
          </dd>
        </div>
        <div>
          <dt>{useLabel}</dt>
          <dd>{useValue || t("unknown")}</dd>
        </div>
      </dl>
      <SuggestionForm
        key={property.id}
        property={property}
        categories={categories}
        turnstileSiteKey={turnstileSiteKey}
      />
    </aside>
  );
}
