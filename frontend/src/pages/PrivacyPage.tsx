import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function PrivacyPage() {
  const { t } = useTranslation();
  return (
    <main className="admin-layout">
      <div className="admin-card">
        <h1>{t("privacy")}</h1>
        <p>{t("privacyBody")}</p>
        <Link className="btn secondary" to="/">
          {t("brand")}
        </Link>
      </div>
    </main>
  );
}
