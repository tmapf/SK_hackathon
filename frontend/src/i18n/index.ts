import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import pl from "./pl.json";

const saved = localStorage.getItem("warsaw-lang");

void i18n.use(initReactI18next).init({
  resources: {
    pl: { translation: pl },
    en: { translation: en },
  },
  lng: saved || "pl",
  fallbackLng: "pl",
  interpolation: { escapeValue: false },
});

export default i18n;
