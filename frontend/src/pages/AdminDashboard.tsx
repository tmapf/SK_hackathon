import { FormEvent, useMemo, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MapContainer, Marker, TileLayer } from "react-leaflet";
import L from "leaflet";
import { apiFetch, ApiError } from "../api/client";
import type {
  AdminUser,
  Category,
  PopularProperty,
  Suggestion,
  SyncRun,
  Translation,
} from "../types";

function popularityIcon(count: number) {
  const size = Math.min(36, 16 + count * 2);
  return L.divIcon({
    className: "",
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:#c8102e;color:white;display:grid;place-items:center;font-size:12px;font-weight:700;border:2px solid white;box-shadow:0 4px 12px rgba(0,0,0,.25)">${count}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

export function AdminDashboard() {
  const queryClient = useQueryClient();
  const [categoryFilter, setCategoryFilter] = useState("");
  const [query, setQuery] = useState("");
  const [popularCategory, setPopularCategory] = useState("");
  const [newCategory, setNewCategory] = useState({
    slug: "",
    label_pl: "",
    label_en: "",
    sort_order: 100,
  });
  const [translationForm, setTranslationForm] = useState({
    field_name: "intended_use",
    source_value: "",
    value_en: "",
  });

  const meQuery = useQuery({
    queryKey: ["admin-me"],
    queryFn: () => apiFetch<AdminUser>("/api/admin/me"),
    retry: false,
  });

  const suggestionsQuery = useQuery({
    queryKey: ["admin-suggestions", categoryFilter, query],
    enabled: meQuery.isSuccess,
    queryFn: () => {
      const params = new URLSearchParams();
      if (categoryFilter) params.set("category_id", categoryFilter);
      if (query.trim()) params.set("q", query.trim());
      return apiFetch<Suggestion[]>(`/api/admin/suggestions?${params}`);
    },
  });

  const categoriesQuery = useQuery({
    queryKey: ["admin-categories"],
    enabled: meQuery.isSuccess,
    queryFn: () => apiFetch<Category[]>("/api/admin/categories"),
  });

  const translationsQuery = useQuery({
    queryKey: ["admin-translations"],
    enabled: meQuery.isSuccess,
    queryFn: () => apiFetch<Translation[]>("/api/admin/translations"),
  });

  const syncQuery = useQuery({
    queryKey: ["admin-sync"],
    enabled: meQuery.isSuccess,
    queryFn: () => apiFetch<SyncRun[]>("/api/admin/sync"),
  });

  const popularQuery = useQuery({
    queryKey: ["admin-popular", popularCategory],
    enabled: meQuery.isSuccess,
    queryFn: () => {
      const params = new URLSearchParams();
      if (popularCategory) params.set("category_id", popularCategory);
      return apiFetch<PopularProperty[]>(`/api/admin/popular?${params}`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/api/admin/suggestions/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin-suggestions"] });
      void queryClient.invalidateQueries({ queryKey: ["admin-popular"] });
    },
  });

  const syncMutation = useMutation({
    mutationFn: () => apiFetch<SyncRun>("/api/admin/sync", { method: "POST" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin-sync"] });
    },
  });

  const createCategoryMutation = useMutation({
    mutationFn: () =>
      apiFetch<Category>("/api/admin/categories", {
        method: "POST",
        body: JSON.stringify(newCategory),
      }),
    onSuccess: () => {
      setNewCategory({ slug: "", label_pl: "", label_en: "", sort_order: 100 });
      void queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
      void queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const updateCategoryMutation = useMutation({
    mutationFn: (payload: { id: number; body: Partial<Category> }) =>
      apiFetch<Category>(`/api/admin/categories/${payload.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload.body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["admin-categories"] });
      void queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const translationMutation = useMutation({
    mutationFn: () =>
      apiFetch<Translation>("/api/admin/translations", {
        method: "POST",
        body: JSON.stringify(translationForm),
      }),
    onSuccess: () => {
      setTranslationForm({ field_name: "intended_use", source_value: "", value_en: "" });
      void queryClient.invalidateQueries({ queryKey: ["admin-translations"] });
      void queryClient.invalidateQueries({ queryKey: ["translations"] });
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => apiFetch("/api/admin/logout", { method: "POST" }),
    onSuccess: () => {
      void queryClient.resetQueries({ queryKey: ["admin-me"] });
    },
  });

  const ranked = useMemo(() => popularQuery.data ?? [], [popularQuery.data]);

  if (meQuery.isLoading) {
    return <main className="admin-layout">Loading…</main>;
  }

  if (meQuery.isError) {
    if (meQuery.error instanceof ApiError && meQuery.error.status === 401) {
      return <Navigate to="/admin/login" replace />;
    }
  }

  async function exportCsv() {
    const params = new URLSearchParams();
    if (categoryFilter) params.set("category_id", categoryFilter);
    const response = await fetch(`/api/admin/suggestions/export?${params}`, {
      credentials: "include",
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "suggestions.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function createCategory(event: FormEvent) {
    event.preventDefault();
    createCategoryMutation.mutate();
  }

  function saveTranslation(event: FormEvent) {
    event.preventDefault();
    translationMutation.mutate();
  }

  return (
    <main className="admin-layout">
      <div className="admin-nav">
        <div>
          <h1>Administration</h1>
          <p>Signed in as {meQuery.data?.username}</p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <Link className="btn secondary" to="/">
            Public map
          </Link>
          <button className="btn secondary" type="button" onClick={() => exportCsv()}>
            Export CSV
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            {syncMutation.isPending ? "Syncing…" : "Refresh properties"}
          </button>
          <button
            className="btn secondary"
            type="button"
            onClick={() => logoutMutation.mutate()}
          >
            Log out
          </button>
        </div>
      </div>

      <section className="admin-card">
        <h2>Suggestions</h2>
        <div className="filters" style={{ padding: 0, border: 0, background: "transparent" }}>
          <label>
            Category
            <select
              value={categoryFilter}
              onChange={(event) => setCategoryFilter(event.target.value)}
            >
              <option value="">All</option>
              {(categoriesQuery.data ?? []).map((category) => (
                <option key={category.id} value={category.id}>
                  {category.label_en}
                </option>
              ))}
            </select>
          </label>
          <label>
            Search
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Text or email"
            />
          </label>
        </div>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Created</th>
              <th>Category</th>
              <th>Property</th>
              <th>Email</th>
              <th>Proposal</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {(suggestionsQuery.data ?? []).map((suggestion) => (
              <tr key={suggestion.id}>
                <td>{new Date(suggestion.created_at).toLocaleString()}</td>
                <td>{suggestion.category?.label_en || suggestion.category_id}</td>
                <td>
                  {(suggestion.property_snapshot.address_label as string) ||
                    suggestion.property_id}
                  {suggestion.property_snapshot.announcement_url ? (
                    <>
                      <br />
                      <a
                        href={String(suggestion.property_snapshot.announcement_url)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Official announcement
                      </a>
                    </>
                  ) : null}
                </td>
                <td>{suggestion.email || "—"}</td>
                <td>{suggestion.proposal_text}</td>
                <td>
                  <button
                    className="btn secondary"
                    type="button"
                    onClick={() => deleteMutation.mutate(suggestion.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="admin-card">
        <h2>Popular places by category</h2>
        <label>
          Category
          <select
            value={popularCategory}
            onChange={(event) => setPopularCategory(event.target.value)}
          >
            <option value="">All categories</option>
            {(categoriesQuery.data ?? []).map((category) => (
              <option key={category.id} value={category.id}>
                {category.label_en}
              </option>
            ))}
          </select>
        </label>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: "1rem" }}>
          <ol>
            {ranked.map((item) => (
              <li key={item.property_id}>
                <strong>{item.suggestion_count}</strong> · {item.address_label}
                {item.announcement_url ? (
                  <>
                    {" "}
                    <a href={item.announcement_url} target="_blank" rel="noreferrer">
                      announcement
                    </a>
                  </>
                ) : null}
              </li>
            ))}
          </ol>
          <div style={{ minHeight: 360 }}>
            <MapContainer
              center={[52.2297, 21.0122]}
              zoom={11}
              style={{ height: 360, width: "100%", borderRadius: 16 }}
            >
              <TileLayer
                attribution="Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), Esri (Thailand), TomTom"
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
              />
              {ranked.map((item) => (
                <Marker
                  key={item.property_id}
                  position={[item.latitude, item.longitude]}
                  icon={popularityIcon(item.suggestion_count)}
                />
              ))}
            </MapContainer>
          </div>
        </div>
      </section>

      <section className="admin-card">
        <h2>Categories</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Slug</th>
              <th>PL</th>
              <th>EN</th>
              <th>Order</th>
              <th>Active</th>
            </tr>
          </thead>
          <tbody>
            {(categoriesQuery.data ?? []).map((category) => (
              <tr key={category.id}>
                <td>{category.slug}</td>
                <td>
                  <input
                    defaultValue={category.label_pl}
                    onBlur={(event) =>
                      updateCategoryMutation.mutate({
                        id: category.id,
                        body: { label_pl: event.target.value },
                      })
                    }
                  />
                </td>
                <td>
                  <input
                    defaultValue={category.label_en}
                    onBlur={(event) =>
                      updateCategoryMutation.mutate({
                        id: category.id,
                        body: { label_en: event.target.value },
                      })
                    }
                  />
                </td>
                <td>{category.sort_order}</td>
                <td>
                  <button
                    className="btn secondary"
                    type="button"
                    onClick={() =>
                      updateCategoryMutation.mutate({
                        id: category.id,
                        body: { is_active: !category.is_active },
                      })
                    }
                  >
                    {category.is_active ? "Disable" : "Enable"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <form className="form-stack" onSubmit={createCategory}>
          <h3>Add category</h3>
          <input
            placeholder="slug"
            value={newCategory.slug}
            onChange={(event) =>
              setNewCategory({ ...newCategory, slug: event.target.value })
            }
            required
          />
          <input
            placeholder="Polish label"
            value={newCategory.label_pl}
            onChange={(event) =>
              setNewCategory({ ...newCategory, label_pl: event.target.value })
            }
            required
          />
          <input
            placeholder="English label"
            value={newCategory.label_en}
            onChange={(event) =>
              setNewCategory({ ...newCategory, label_en: event.target.value })
            }
            required
          />
          <button className="btn" type="submit">
            Create category
          </button>
        </form>
      </section>

      <section className="admin-card">
        <h2>Translations</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Source (PL)</th>
              <th>English</th>
            </tr>
          </thead>
          <tbody>
            {(translationsQuery.data ?? []).map((row) => (
              <tr key={row.id}>
                <td>{row.field_name}</td>
                <td>{row.source_value}</td>
                <td>{row.value_en}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <form className="form-stack" onSubmit={saveTranslation}>
          <h3>Upsert translation</h3>
          <select
            value={translationForm.field_name}
            onChange={(event) =>
              setTranslationForm({
                ...translationForm,
                field_name: event.target.value,
              })
            }
          >
            <option value="intended_use">intended_use</option>
            <option value="development_state">development_state</option>
          </select>
          <input
            placeholder="Polish source value"
            value={translationForm.source_value}
            onChange={(event) =>
              setTranslationForm({
                ...translationForm,
                source_value: event.target.value,
              })
            }
            required
          />
          <input
            placeholder="English value"
            value={translationForm.value_en}
            onChange={(event) =>
              setTranslationForm({
                ...translationForm,
                value_en: event.target.value,
              })
            }
            required
          />
          <button className="btn" type="submit">
            Save translation
          </button>
        </form>
      </section>

      <section className="admin-card">
        <h2>Sync history</h2>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Started</th>
              <th>Status</th>
              <th>Upserted</th>
              <th>Skipped</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {(syncQuery.data ?? []).map((run) => (
              <tr key={run.id}>
                <td>{new Date(run.started_at).toLocaleString()}</td>
                <td>{run.status}</td>
                <td>{run.properties_upserted}</td>
                <td>{run.properties_skipped}</td>
                <td>{run.error_message || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
