import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { PropertyPanel } from "./PropertyPanel";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: { language: "en" },
  }),
}));

vi.mock("../hooks/useTranslatedValue", () => ({
  useTranslatedValue: (_field: string, value: string | null | undefined) => value,
}));

vi.mock("./SuggestionForm", () => ({
  SuggestionForm: () => <div>suggestion-form</div>,
}));

describe("PropertyPanel", () => {
  it("renders property details and close action", () => {
    const onClose = vi.fn();
    const client = new QueryClient();
    render(
      <QueryClientProvider client={client}>
        <PropertyPanel
          property={{
            id: 1,
            offer_type: "wynajem",
            source_id: 10,
            street: "Lipska",
            district: "Praga-Południe",
            city: "Warszawa",
            house_number: "21",
            unit_number: null,
            area_m2: 19.5,
            intended_use: "BIUROWA",
            development_state: null,
            longitude: 21,
            latitude: 52,
            address_label: "Lipska 21, Praga-Południe",
          }}
          categories={[]}
          turnstileSiteKey=""
          onClose={onClose}
        />
      </QueryClientProvider>,
    );
    expect(screen.getByText("Lipska 21, Praga-Południe")).toBeInTheDocument();
    expect(screen.getByText("suggestion-form")).toBeInTheDocument();
    fireEvent.click(screen.getByText("close"));
    expect(onClose).toHaveBeenCalled();
  });
});
