import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../api/client";

export function useTranslatedValue(fieldName: string, value: string | null | undefined) {
  const { i18n } = useTranslation();
  const { data } = useQuery({
    queryKey: ["translations"],
    queryFn: () => apiFetch<Record<string, Record<string, string>>>("/api/translations"),
    staleTime: 60_000,
  });

  if (!value) return null;
  if (i18n.language === "en") {
    return data?.[fieldName]?.[value] || value;
  }
  return value;
}
