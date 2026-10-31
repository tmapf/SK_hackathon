import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { FilterBar } from "./FilterBar";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe("FilterBar", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        Response.json([
          {
            id: 7,
            address_label: "Lipska 21, Praga-Południe",
            district: "Praga-Południe",
            street: "Lipska",
          },
        ]),
      ),
    );
  });

  it("submits current filters and shows address suggestions", async () => {
    const onSubmit = vi.fn();
    const onChange = vi.fn();
    const onSelectSuggestion = vi.fn();
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={client}>
        <FilterBar
          filters={{
            offerType: "wynajem",
            q: "Lip",
            district: "",
            minArea: "",
            maxArea: "",
          }}
          districts={["Wola"]}
          onChange={onChange}
          onSubmit={onSubmit}
          onClear={vi.fn()}
          onSelectSuggestion={onSelectSuggestion}
        />
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByText("applyFilters"));
    expect(onSubmit).toHaveBeenCalled();

    fireEvent.focus(screen.getByPlaceholderText("searchPlaceholder"));
    await waitFor(() =>
      expect(screen.getByText("Lipska 21, Praga-Południe")).toBeInTheDocument(),
    );
    fireEvent.click(screen.getByText("Lipska 21, Praga-Południe"));
    expect(onSelectSuggestion).toHaveBeenCalledWith(
      expect.objectContaining({ id: 7, street: "Lipska" }),
    );
  });
});
