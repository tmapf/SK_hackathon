import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MapPage } from "./MapPage";

const fetchMock = vi.fn();

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: { count?: number }) =>
      options?.count != null ? `${key}:${options.count}` : key,
    i18n: {
      language: "pl",
      changeLanguage: vi.fn(),
    },
  }),
}));

vi.mock("../components/PropertyMap", () => ({
  PropertyMap: ({
    onSelect,
  }: {
    onSelect: (feature: {
      id: number;
      properties: { id: number; offer_type: string; address_label: string };
    }) => void;
  }) => (
    <button
      type="button"
      onClick={() =>
        onSelect({
          id: 1,
          properties: {
            id: 1,
            offer_type: "wynajem",
            address_label: "Lipska 21",
          },
        })
      }
    >
      select-marker
    </button>
  ),
}));

vi.mock("../components/PropertyPanel", () => ({
  PropertyPanel: ({
    property,
  }: {
    property: { address_label: string } | null;
  }) => <div>{property ? property.address_label : "no-selection"}</div>,
}));

describe("MapPage", () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    localStorage.clear();

    fetchMock.mockImplementation(async (input: RequestInfo) => {
      const url = String(input);
      if (url.includes("/api/config")) {
        return Response.json({
          turnstile_site_key: "",
          tile_url: "https://tile.test/{z}/{x}/{y}.png",
          tile_attribution: "test",
          privacy_policy_url: "/privacy",
          contact_email: "",
          last_successful_sync_at: null,
        });
      }
      if (url.includes("/api/categories")) {
        return Response.json([]);
      }
      if (url.includes("/api/districts")) {
        return Response.json(["Wola"]);
      }
      if (url.includes("/api/properties")) {
        return Response.json({
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              id: 1,
              geometry: { type: "Point", coordinates: [21, 52] },
              properties: {
                id: 1,
                offer_type: "wynajem",
                source_id: 10,
                street: "Lipska",
                district: "Praga-Południe",
                city: "Warszawa",
                house_number: "21",
                unit_number: null,
                area_m2: 20,
                intended_use: "BIUROWA",
                development_state: null,
                longitude: 21,
                latitude: 52,
                address_label: "Lipska 21",
              },
            },
          ],
        });
      }
      return Response.json({});
    });
  });

  it("updates the selected property panel when a marker is chosen", async () => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <MapPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByText("select-marker")).toBeInTheDocument());
    fireEvent.click(screen.getByText("select-marker"));
    expect(screen.getAllByText("Lipska 21").length).toBeGreaterThan(0);
  });
});
