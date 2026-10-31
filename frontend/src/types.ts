export type OfferType = "wynajem" | "sprzedaz";

export interface PropertyFeatureProperties {
  id: number;
  offer_type: OfferType;
  source_id: number;
  street: string | null;
  district: string | null;
  city: string | null;
  house_number: string | null;
  unit_number: string | null;
  area_m2: number | null;
  intended_use: string | null;
  development_state: string | null;
  longitude: number;
  latitude: number;
  address_label: string;
}

export interface PropertyFeature {
  type: "Feature";
  id: number;
  geometry: {
    type: "Point";
    coordinates: [number, number];
  };
  properties: PropertyFeatureProperties;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: PropertyFeature[];
}

export interface Category {
  id: number;
  slug: string;
  label_pl: string;
  label_en: string;
  sort_order: number;
  is_active: boolean;
}

export interface PublicConfig {
  turnstile_site_key: string;
  tile_url: string;
  tile_attribution: string;
  privacy_policy_url: string;
  contact_email: string;
  last_successful_sync_at: string | null;
}

export interface Suggestion {
  id: number;
  property_id: number;
  category_id: number;
  proposal_text: string;
  email: string | null;
  property_snapshot: Record<string, unknown>;
  created_at: string;
  category?: Category | null;
}

export interface SyncRun {
  id: number;
  status: string;
  offer_types: string;
  properties_upserted: number;
  properties_skipped: number;
  error_message: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface PopularProperty {
  property_id: number;
  offer_type: OfferType;
  address_label: string;
  district: string | null;
  area_m2: number | null;
  intended_use: string | null;
  development_state: string | null;
  longitude: number;
  latitude: number;
  suggestion_count: number;
  announcement_url?: string | null;
}

export interface Translation {
  id: number;
  field_name: string;
  source_value: string;
  value_en: string;
}

export interface AdminUser {
  id: number;
  username: string;
}
