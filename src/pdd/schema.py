"""Observation schema (requirement R1, protocol section 2).

The v0 schema had seven columns and no run identity. Rows within one sweep carried
timestamps spread over minutes, so runs could not even be reconstructed after the fact,
and the analysis pooled every observation ever recorded for a SKU into one median. A
$100 to $115 retailer price change then flagged all three personas at once.

`sweep_id` is therefore not a convenience column. It is the unit of comparison, and the
schema enforces that nothing enters the panel without one.

Everything else follows from the audit: integer minor units instead of REAL, factor
levels stored decomposed so main effects are recoverable, and explicit status columns
for the two failure modes v0 hid — parse ambiguity and bot pages.
"""

from __future__ import annotations

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS sweeps (
    sweep_id        TEXT PRIMARY KEY,
    retailer_id     TEXT    NOT NULL,
    started_at      TEXT    NOT NULL,
    ended_at        TEXT,
    seed            INTEGER NOT NULL,
    window_seconds  INTEGER,
    qc_status       TEXT    NOT NULL DEFAULT 'pending'
                    CHECK (qc_status IN ('pending','pass','fail')),
    qc_detail       TEXT
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id    INTEGER PRIMARY KEY AUTOINCREMENT,

    -- R1: the comparison unit. NOT NULL is the point of this table.
    sweep_id          TEXT    NOT NULL REFERENCES sweeps(sweep_id),
    replicate_idx     INTEGER NOT NULL,

    retailer_id       TEXT    NOT NULL,
    product_id        TEXT    NOT NULL,

    persona_id        TEXT    NOT NULL,
    is_control        INTEGER NOT NULL DEFAULT 0 CHECK (is_control IN (0,1)),
    -- Factors stored decomposed, not baked into a persona name: the v0 personas each
    -- varied four attributes at once, so no effect was attributable to any of them.
    factor_geo        TEXT,
    factor_dev        TEXT,
    factor_loc        TEXT,
    factor_tz         TEXT,
    factor_hist       TEXT,

    observed_at       TEXT    NOT NULL,

    -- Integer minor units, never float. Currency is a grouping key (R4), so it is
    -- NOT NULL whenever a price exists.
    price_minor_units INTEGER,
    currency          TEXT,
    price_kind        TEXT    CHECK (price_kind IN ('sale','list','struck_through','unknown')),
    raw_price_text    TEXT,

    -- R7: ambiguity is a status, never a silent number.
    parse_status      TEXT    NOT NULL
                      CHECK (parse_status IN ('ok','ambiguous','no_match','multiple_candidates','not_attempted')),
    parse_detail      TEXT,

    -- R6: without this, "no discrimination" and "everyone was blocked" are the same row.
    canary_status     TEXT    NOT NULL DEFAULT 'unknown'
                      CHECK (canary_status IN ('real_page','bot_page','unknown')),

    http_status       INTEGER,
    load_ms           INTEGER,
    proxy_exit_region TEXT,
    proxy_exit_id     TEXT,

    -- R5: failures are recorded and read, not filtered away.
    error             TEXT,
    capture_ref       TEXT,

    CHECK (price_minor_units IS NULL OR currency IS NOT NULL),
    CHECK (parse_status != 'ok' OR price_minor_units IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_obs_cohort
    ON observations (sweep_id, product_id, currency);
CREATE INDEX IF NOT EXISTS idx_obs_persona
    ON observations (sweep_id, persona_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_cell
    ON observations (sweep_id, product_id, persona_id, replicate_idx);

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# The two CHECK constraints at the end of `observations` are the schema-level
# expression of the audit's two silent-corruption defects:
#
#   price without currency   -> B2, currency parsed then ignored
#   parse_status 'ok' without a price -> B1/B3, a row that claims success but holds nothing
#
# SQLite will reject both, so neither can reach the analysis layer.
