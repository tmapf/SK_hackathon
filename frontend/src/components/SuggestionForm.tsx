import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslation } from "react-i18next";
import { apiFetch } from "../api/client";
import type { Category, PropertyFeatureProperties } from "../types";
import { TurnstileWidget } from "./TurnstileWidget";

const schema = z.object({
  category_id: z.coerce.number().int().positive(),
  proposal_text: z.string().min(10).max(1000),
  email: z
    .string()
    .email()
    .optional()
    .or(z.literal("")),
  website: z.string().max(0).optional(),
});

type FormValues = z.infer<typeof schema>;

interface SuggestionFormProps {
  property: PropertyFeatureProperties;
  categories: Category[];
  turnstileSiteKey: string;
}

export function SuggestionForm({
  property,
  categories,
  turnstileSiteKey,
}: SuggestionFormProps) {
  const { t, i18n } = useTranslation();
  const captchaEnabled = Boolean(turnstileSiteKey);
  const [token, setToken] = useState(captchaEnabled ? "" : "demo-bypass");
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      category_id: categories[0]?.id,
      proposal_text: "",
      email: "",
      website: "",
    },
  });

  useEffect(() => {
    reset({
      category_id: categories[0]?.id,
      proposal_text: "",
      email: "",
      website: "",
    });
    setStatus("idle");
    setErrorMessage("");
    setToken(captchaEnabled ? "" : "demo-bypass");
  }, [property.id, categories, reset, captchaEnabled]);

  async function onSubmit(values: FormValues) {
    const submitToken = captchaEnabled ? token : "demo-bypass";
    if (captchaEnabled && !submitToken) {
      setStatus("error");
      setErrorMessage("CAPTCHA required");
      return;
    }
    try {
      await apiFetch("/api/suggestions", {
        method: "POST",
        body: JSON.stringify({
          property_id: property.id,
          category_id: values.category_id,
          proposal_text: values.proposal_text,
          email: values.email || null,
          turnstile_token: submitToken,
          website: values.website || "",
        }),
      });
      setStatus("success");
      reset({
        category_id: categories[0]?.id,
        proposal_text: "",
        email: "",
        website: "",
      });
      setToken(captchaEnabled ? "" : "demo-bypass");
    } catch (error) {
      setStatus("error");
      setErrorMessage(error instanceof Error ? error.message : t("submitError"));
    }
  }

  return (
    <form className="form-stack" onSubmit={handleSubmit(onSubmit)} noValidate>
      <h3>{t("suggestTitle")}</h3>
      <label>
        {t("category")}
        <select {...register("category_id")}>
          <option value="">{t("chooseCategory")}</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {i18n.language === "en" ? category.label_en : category.label_pl}
            </option>
          ))}
        </select>
        {errors.category_id && <p className="error">{errors.category_id.message}</p>}
      </label>
      <label>
        {t("proposal")}
        <textarea rows={5} {...register("proposal_text")} />
        <p className="help">{t("proposalHelp")}</p>
        {errors.proposal_text && (
          <p className="error">{errors.proposal_text.message}</p>
        )}
      </label>
      <label>
        {t("email")}
        <input type="email" {...register("email")} />
        <p className="help">{t("emailHelp")}</p>
        {errors.email && <p className="error">{errors.email.message}</p>}
      </label>
      <p className="help">{t("privacyNotice")}</p>
      <label className="honeypot" aria-hidden="true">
        Website
        <input tabIndex={-1} autoComplete="off" {...register("website")} />
      </label>
      {captchaEnabled ? (
        <TurnstileWidget siteKey={turnstileSiteKey} onToken={setToken} />
      ) : null}
      <button className="btn" type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("submitting") : t("submit")}
      </button>
      {status === "success" && <p className="status-success">{t("submitSuccess")}</p>}
      {status === "error" && (
        <p className="status-error">{errorMessage || t("submitError")}</p>
      )}
    </form>
  );
}
