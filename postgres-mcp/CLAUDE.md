# Hotel Database — Table Documentation

> **Schema:** `public`  
> **Last Updated:** 2026-06-18 
---

## Table of Contents

1. [hotel_static_best_packet](#1-hotel_static_best_packet)
2. [hotel_supplier_mapping](#2-hotel_supplier_mapping)
3. [hotel_static_room_best_packet](#3-hotel_static_room_best_packet)
4. [hotel_room_supplier_mapping](#4-hotel_room_supplier_mapping)
5. [hotel_room_images](#5-hotel_room_images)
6. [hotel_room_facility](#6-hotel_room_facility)
7. [hotel_facility](#7-hotel_facility)
8. [image_info](#8-image_info)
9. [Relationships Overview](#9-relationships-overview)

---

## Query Rules — MUST FOLLOW

- **Always add `LIMIT`** — never fetch unbounded results. Default: `LIMIT 20`, max: `LIMIT 100`
- **Never `SELECT *`** — always name only the columns you actually need
- **Paginate large results** — use `LIMIT` + `OFFSET` or cursor-based pagination
- **Confirm before writes** — always show the query and ask for confirmation before any `INSERT`, `UPDATE`, `DELETE`
- **JSONB queries** — use `->` / `->>` / `@>` operators for jsonb columns, never cast the whole column
- **Soft deletes** — always filter `WHERE is_deleted = false` or `WHERE active = true` unless explicitly asked otherwise
- **action_type** — `1`=Insert, `2`=Update, `3`=No-op. Exclude `action_type = 3` in most queries unless debugging ETL
- **No bulk exports** — never run queries intended to dump entire tables even if asked
- **Joins** — when joining multiple tables always add `LIMIT` on the outer query
- **JSONB arrays** — use `jsonb_array_elements` carefully, always wrap in a subquery with a `WHERE` filter first to reduce rows before expanding

---


## 1. `hotel_static_best_packet`

### Description
The **core hotel master table**. Stores the canonical, enriched static data for each hotel — sourced from the "best packet" aggregation across multiple suppliers. Each row represents a single hotel property with its full profile: name, location, rating, descriptions, branding, check-in/out policies, scoring, and media. This is the primary source of truth for hotel-level metadata used across the system.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `bigint` | NOT NULL | — | Primary key. TJ's internal unique hotel identifier (`tj_hotel_id`). |
| `hotel_name` | `varchar` | NOT NULL | — | Short/display name of the hotel (e.g., "Burj Al Arab"). |
| `hotel_full_name` | `varchar` | YES | — | Full legal or branded name of the hotel property. |
| `rating` | `integer` | YES | — | Star rating of the hotel (typically 1–5). |
| `reviews` | `jsonb` | YES | — | Aggregated guest review data (scores, counts, sentiment breakdown) stored as JSON. |
| `location` | `jsonb` | NOT NULL | — | Geo-coordinates and location metadata (latitude, longitude, map references). |
| `address` | `jsonb` | YES | — | Full address object (street, city, state, postal code, country). |
| `region_name` | `varchar` | YES | — | Human-readable region/area name (e.g., "Downtown Dubai"). |
| `region_id` | `bigint` | YES | — | Primary region identifier linked to TJ's region taxonomy. |
| `supplier_hotel_id` | `varchar` | NOT NULL | — | The hotel's ID as assigned by the source supplier. |
| `supplier_name` | `varchar` | NOT NULL | — | Name of the supplier that provided this best-packet data (e.g., "vervotech", "hotelbeds"). |
| `country_name` | `varchar` | YES | — | Country where the hotel is located (supplier-provided name). |
| `region_ids` | `jsonb` | YES | — | Array of all region IDs this hotel belongs to (multi-region mapping). |
| `property_type` | `varchar` | YES | — | Type of property (e.g., "Hotel", "Resort", "Apartment", "Villa"). |
| `contact` | `jsonb` | YES | — | Hotel contact details: phone numbers, website URLs, fax. |
| `unica_id` | `varchar` | YES | — | Unified cross-supplier identifier used for deduplication and mapping. |
| `priority_score` | `integer` | YES | — | Internal ranking score used to prioritize this hotel in search results. |
| `booking_score` | `bigint` | YES | — | Score based on historical booking volume/conversion for ranking. |
| `search_score` | `bigint` | YES | — | Score based on how frequently this hotel appears in search results. |
| `check_in_time` | `jsonb` | YES | — | Check-in time policy (from/to times, instructions) as JSON. |
| `check_out_time` | `jsonb` | YES | — | Check-out time policy as JSON. |
| `description` | `text` | YES | — | Raw/original hotel description from the supplier. |
| `display_description` | `text` | YES | — | Cleaned/curated description suitable for display to end users. |
| `cover_image` | `text` | YES | — | URL of the hotel's primary cover/hero image. |
| `airports` | `jsonb` | YES | — | Nearby airports with distances/codes as a JSON array. |
| `instructions` | `jsonb` | YES | — | Special instructions for guests (e.g., pet policy, payment methods). |
| `neighborhood_regions` | `jsonb` | YES | — | Nearby neighborhoods/points of interest as JSON. |
| `regions` | `jsonb` | YES | — | Enriched region hierarchy data (country → city → neighborhood). |
| `brand_code` | `varchar` | YES | — | Hotel brand code (e.g., "HH" for Hilton Hotels). |
| `brand_name` | `varchar` | YES | — | Hotel brand name (e.g., "Hilton", "Marriott"). |
| `chain_code` | `varchar` | YES | — | Hotel chain code (e.g., "HI" for InterContinental Hotels Group). |
| `chain_name` | `varchar` | YES | — | Hotel chain name (e.g., "InterContinental Hotels Group"). |
| `ramadan_meal` | `jsonb` | YES | `'{}'` | Special Ramadan meal offering details (used for Middle East market). |
| `hotel_email_ids` | `jsonb` | YES | `'[]'` | List of hotel contact email addresses as a JSON array. |
| `tj_country_name` | `varchar` | YES | — | TJ's standardized/normalized country name (may differ from supplier's `country_name`). |
| `is_deleted` | `boolean` | YES | `false` | Soft-delete flag. `true` means this hotel record has been deactivated. |
| `action_type` | `integer` | NOT NULL | `3` | Processing action flag: `1`=Insert, `2`=Update, `3`=No-op/Default. |
| `created_on` | `timestamp` | YES | `CURRENT_TIMESTAMP` | Timestamp when this record was first created. |
| `processed_on` | `timestamp` | YES | `CURRENT_TIMESTAMP` | Timestamp of the last processing/update cycle. |

---

## 2. `hotel_supplier_mapping`

### Description
A **cross-reference / mapping table** that links TJ's internal hotel IDs (`tj_hotel_id`) to supplier-specific hotel IDs (`supplier_hotel_id`) across multiple supplier systems. One TJ hotel can map to multiple suppliers, and this table tracks all those relationships. It is the backbone of supplier deduplication and unified hotel identity resolution.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `bigint` | NOT NULL | auto-increment | Primary key. Auto-generated row identifier. |
| `tj_hotel_id` | `varchar` | NOT NULL | — | TJ's internal hotel ID. Foreign key reference to `hotel_static_best_packet.id`. |
| `unica_id` | `varchar` | YES | — | Unified cross-supplier identifier used for deduplication across hotel data sources. |
| `supplier_hotel_id` | `varchar` | NOT NULL | — | The hotel ID as known to the supplier (external ID). |
| `supplier_name` | `varchar` | NOT NULL | — | Name of the supplier system (e.g., "hotelbeds", "vervotech", "expedia"). |
| `isdeleted` | `boolean` | YES | `false` | Soft-delete flag. `true` means this mapping is no longer active. |
| `updated_by` | `varchar` | YES | — | Username or system identifier of the actor who last updated this mapping. |
| `action_type` | `integer` | YES | `3` | Processing action flag: `1`=Insert, `2`=Update, `3`=No-op/Default. |
| `created_on` | `timestamp` | YES | `CURRENT_TIMESTAMP` | Timestamp when this mapping was created. |
| `processed_on` | `timestamp` | YES | `CURRENT_TIMESTAMP` | Timestamp of the last processing/sync cycle for this mapping. |

---

## 3. `hotel_static_room_best_packet`

### Description
The **core room master table** — the room-level equivalent of `hotel_static_best_packet`. Stores enriched static data for each room type within a hotel, sourced from the best available supplier packet. Includes room classification, occupancy limits, bed configuration, size, view type, and attributes. One hotel has many rooms.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `bigint` | NOT NULL | — | Primary key. TJ's internal unique room identifier (`tj_room_id`). |
| `tj_hotel_id` | `varchar` | YES | — | TJ's internal hotel ID this room belongs to. Links to `hotel_static_best_packet.id`. |
| `vervotech_room_id` | `varchar` | YES | — | Room ID as assigned by Vervotech (room content aggregator). |
| `vervotech_room_name` | `varchar` | YES | — | Room name as provided by Vervotech. |
| `unica_id` | `varchar` | YES | — | Unified cross-supplier identifier for this room. |
| `parent_tj_room_id` | `varchar` | YES | — | Reference to a parent room ID if this is a sub-variant of another room type. |
| `room_standard_name` | `varchar` | YES | — | Standardized/normalized room name (e.g., "Deluxe Double Room"). |
| `room_master_title` | `varchar` | YES | — | Display-ready master title for the room type. |
| `category` | `varchar` | YES | — | Room category classification (e.g., "Standard", "Deluxe", "Suite"). |
| `occupancy` | `varchar` | YES | — | Occupancy description (e.g., "Double", "Twin", "Triple"). |
| `bedroom_count` | `integer` | YES | — | Number of bedrooms in this room/suite. |
| `max_guest_allowed` | `integer` | YES | — | Maximum total number of guests permitted in this room. |
| `max_adult_allowed` | `integer` | YES | — | Maximum number of adults allowed in this room. |
| `max_children_allowed` | `integer` | YES | — | Maximum number of children allowed in this room. |
| `view` | `varchar` | YES | — | View type from the room (e.g., "Sea View", "City View", "Garden View"). |
| `description` | `text` | YES | — | Full textual description of the room from the supplier. |
| `beds` | `jsonb` | YES | — | Bed configuration as JSON (type, count — e.g., `[{"type": "King", "count": 1}]`). |
| `areas` | `jsonb` | YES | — | Room size/area information (e.g., square meters/feet) as JSON. |
| `bathroom` | `jsonb` | YES | — | Bathroom details (type, count, features) as JSON. |
| `room_attributes` | `jsonb` | YES | — | Additional structured room attributes (floor, accessibility features, etc.) as JSON. |
| `active` | `boolean` | NOT NULL | `true` | Whether this room record is currently active and in use. |
| `action_type` | `integer` | YES | `3` | Processing action flag: `1`=Insert, `2`=Update, `3`=No-op/Default. |
| `created_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp when this room record was created. |
| `processed_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp of the last processing/update. |

---

## 4. `hotel_room_supplier_mapping`

### Description
The **room-level supplier cross-reference table** — analogous to `hotel_supplier_mapping` but for rooms. Maps TJ's internal room IDs to supplier-specific room codes. Tracks which supplier room codes correspond to which TJ unified room, enabling room-level content matching and inventory linking across multiple booking suppliers.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `bigint` | NOT NULL | auto-increment | Primary key. Auto-generated row identifier. |
| `tj_room_id` | `varchar` | YES | — | TJ's internal room ID. Links to `hotel_static_room_best_packet.id`. |
| `tj_hotel_id` | `varchar` | YES | — | TJ's internal hotel ID the room belongs to. Links to `hotel_static_best_packet.id`. |
| `unica_id` | `varchar` | YES | — | Unified cross-supplier identifier for the room. |
| `supplier_name` | `varchar` | YES | — | Name of the supplier this mapping applies to (e.g., "hotelbeds", "expedia"). |
| `supplier_room_code` | `varchar` | YES | — | The room code/ID as used by the supplier's system. |
| `room_name` | `varchar` | YES | — | Room name as provided by the supplier (may differ from TJ's standardized name). |
| `room_description` | `text` | YES | — | Room description text as provided by the supplier. |
| `active` | `boolean` | YES | — | Whether this supplier-room mapping is currently active. |
| `action_type` | `integer` | YES | `3` | Processing action flag: `1`=Insert, `2`=Update, `3`=No-op/Default. |
| `created_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp when this mapping record was created. |
| `processed_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp of the last processing cycle for this mapping. |

---

## 5. `hotel_room_images`

### Description
Stores **image data for individual hotel rooms**. Each row holds all image assets associated with a specific room, packed as a JSON array. This separates room-level imagery from hotel-level imagery (which lives in `image_info`). Used to display room photos on booking/detail pages.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `integer` | NOT NULL | auto-increment | Primary key. Auto-generated row identifier. |
| `tj_room_id` | `bigint` | NOT NULL | — | TJ's internal room ID. Links to `hotel_static_room_best_packet.id`. |
| `image_data` | `jsonb` | NOT NULL | `'[]'` | JSON array of image objects for this room. Each object typically contains URL, caption, category, and sort order. |
| `active` | `boolean` | NOT NULL | `true` | Whether this image record is active. `false` means images are suppressed/hidden. |
| `created_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp when this record was created. |
| `processed_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp of the last image data update/sync. |

---

## 6. `hotel_room_facility`

### Description
Stores **facilities and amenities specific to individual hotel rooms**. Each row holds the full set of amenities for a given room as a JSON array (e.g., air conditioning, minibar, safe, balcony, smart TV). Complements the hotel-level facilities stored in `hotel_facility`.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `integer` | NOT NULL | auto-increment | Primary key. Auto-generated row identifier. |
| `tj_room_id` | `bigint` | NOT NULL | — | TJ's internal room ID. Links to `hotel_static_room_best_packet.id`. |
| `facilities` | `jsonb` | YES | `'[]'` | JSON array of facility/amenity objects for this room (e.g., `[{"name": "Air Conditioning", "id": 123}]`). |
| `active` | `boolean` | NOT NULL | `true` | Whether this facility record is active. |
| `created_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp when this record was created. |
| `processed_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp of the last processing/update cycle. |

---

## 7. `hotel_facility`

### Description
Stores **hotel-level facilities and amenities** for each property. Each row holds all property-wide amenities (e.g., swimming pool, gym, spa, parking, restaurant, Wi-Fi) as a structured JSON array. Also contains TJ's own normalized amenity representation (`tj_amenities`) alongside the raw supplier facilities data. One row per hotel.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `integer` | NOT NULL | auto-increment | Primary key. Auto-generated row identifier. |
| `tj_hotel_id` | `bigint` | NOT NULL | — | TJ's internal hotel ID. Links to `hotel_static_best_packet.id`. |
| `facilities` | `jsonb` | NOT NULL | `'[]'` | JSON array of raw facility/amenity objects from the supplier (e.g., pool, gym, spa). |
| `tj_amenities` | `jsonb` | YES | — | TJ's own standardized/normalized amenity list for this hotel, used for filtered search. |
| `active` | `boolean` | NOT NULL | `true` | Whether this facilities record is active. |
| `created_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp when this record was created. |
| `updated_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp of the last update to the facilities data. |

---

## 8. `image_info`

### Description
Stores **hotel-level image galleries**. Each row contains all images associated with a specific hotel, packed as a JSON array. This is the property-wide image store (exterior shots, lobby, restaurant, pool, etc.), distinct from `hotel_room_images` which holds room-specific photos. Typically one row per hotel.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `integer` | NOT NULL | auto-increment | Primary key. Auto-generated row identifier. |
| `tj_hotel_id` | `bigint` | NOT NULL | — | TJ's internal hotel ID. Links to `hotel_static_best_packet.id`. |
| `image_data` | `jsonb` | NOT NULL | `'[]'` | JSON array of image objects for the hotel. Each object typically includes URL, category (e.g., "exterior", "pool"), caption, and display order. |
| `deleted` | `boolean` | YES | `false` | Soft-delete flag. `true` means this image record has been removed/suppressed. |
| `created_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp when this image record was first created. |
| `updated_on` | `timestamp` | NOT NULL | `CURRENT_TIMESTAMP` | Timestamp of the last image data update. |

---

## 9. Relationships Overview

```
hotel_static_best_packet  (1)
    │   id (tj_hotel_id)
    ├──→ hotel_supplier_mapping        (many)   via tj_hotel_id
    ├──→ hotel_facility                (1)      via tj_hotel_id
    ├──→ image_info                    (1)      via tj_hotel_id
    └──→ hotel_static_room_best_packet (many)   via tj_hotel_id
              │   id (tj_room_id)
              ├──→ hotel_room_supplier_mapping  (many)   via tj_room_id
              ├──→ hotel_room_facility          (1)      via tj_room_id
              └──→ hotel_room_images            (1)      via tj_room_id
```

### Key ID Fields Glossary

| Field | Meaning |
|-------|---------|
| `tj_hotel_id` | TJ's internal canonical hotel identifier |
| `tj_room_id` | TJ's internal canonical room identifier |
| `unica_id` | Cross-supplier unified identifier (used for deduplication) |
| `supplier_hotel_id` | Hotel ID in the supplier's own system |
| `supplier_room_code` | Room code in the supplier's own system |
| `vervotech_room_id` | Room ID from Vervotech (room content aggregator) |

### Common Field Patterns

| Field | Pattern |
|-------|---------|
| `active` / `is_deleted` / `isdeleted` | Soft-delete flags — records are never hard-deleted |
| `action_type` | `1`=Insert, `2`=Update, `3`=No-op (default); used in ETL pipelines |
| `created_on` | Set on first insert, never changed |
| `processed_on` / `updated_on` | Updated on every processing cycle or data change |
| `jsonb` columns | Flexible structured data — query with `->` / `->>` / `@>` operators |

---

> ⚠️ **Note on `rooms` table:** The table `rooms` was requested but does **not exist** in the public schema. It may have been dropped, renamed, or the name may refer to `hotel_static_room_best_packet`.
