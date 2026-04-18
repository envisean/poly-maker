-- DuckDB schema for the signal state store.
-- Idempotent: safe to run on every service boot.

CREATE TABLE IF NOT EXISTS market_ticks (
    market_id  VARCHAR     NOT NULL,
    ts         TIMESTAMPTZ NOT NULL,
    yes_price  DOUBLE,
    no_price   DOUBLE,
    best_bid   DOUBLE,
    best_ask   DOUBLE,
    spread     DOUBLE,
    liquidity  DOUBLE
);
CREATE INDEX IF NOT EXISTS idx_market_ticks_lookup ON market_ticks (market_id, ts);

-- Individual trade prints (fills observed on the CLOB).
CREATE TABLE IF NOT EXISTS trade_prints (
    market_id VARCHAR     NOT NULL,
    ts        TIMESTAMPTZ NOT NULL,
    side      VARCHAR     NOT NULL,   -- 'BUY' | 'SELL'
    price     DOUBLE      NOT NULL,
    size      DOUBLE      NOT NULL,
    wallet    VARCHAR
);
CREATE INDEX IF NOT EXISTS idx_trade_prints_lookup ON trade_prints (market_id, ts);

-- Every detector fire, regardless of whether confluence was met.
CREATE TABLE IF NOT EXISTS signal_fires (
    ts          TIMESTAMPTZ NOT NULL,
    signal_name VARCHAR     NOT NULL,
    market_id   VARCHAR     NOT NULL,
    direction   VARCHAR     NOT NULL,
    confidence  DOUBLE      NOT NULL,
    evidence    JSON
);
CREATE INDEX IF NOT EXISTS idx_signal_fires_lookup ON signal_fires (market_id, ts);

-- Confluence hits (>= threshold detectors agreed).
CREATE TABLE IF NOT EXISTS confluence_hits (
    ts              TIMESTAMPTZ NOT NULL,
    market_id       VARCHAR     NOT NULL,
    direction       VARCHAR     NOT NULL,
    count           INTEGER     NOT NULL,
    mean_confidence DOUBLE      NOT NULL,
    fires           JSON
);
CREATE INDEX IF NOT EXISTS idx_confluence_hits_lookup ON confluence_hits (market_id, ts);

-- Our own orders placed on the CLOB.
CREATE TABLE IF NOT EXISTS orders (
    ts                 TIMESTAMPTZ NOT NULL,
    order_id           VARCHAR,
    market_id          VARCHAR     NOT NULL,
    side               VARCHAR     NOT NULL,   -- 'BUY' | 'SELL'
    price              DOUBLE      NOT NULL,
    size               DOUBLE      NOT NULL,
    status             VARCHAR     NOT NULL,   -- 'PLACED' | 'FILLED' | 'CANCELED' | 'ERROR'
    confluence_hit_ts  TIMESTAMPTZ,            -- link back to the hit that triggered it
    note               VARCHAR
);
CREATE INDEX IF NOT EXISTS idx_orders_lookup ON orders (market_id, ts);

-- Current position per market (upsert).
CREATE TABLE IF NOT EXISTS positions (
    market_id     VARCHAR PRIMARY KEY,
    side          VARCHAR,
    size          DOUBLE  NOT NULL DEFAULT 0,
    avg_price     DOUBLE,
    realized_pnl  DOUBLE  NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ NOT NULL
);

-- Key/value store for GlobalState — whale list, cross-venue prices, oracle prices, etc.
CREATE TABLE IF NOT EXISTS global_kv (
    key         VARCHAR PRIMARY KEY,
    value       JSON        NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- News items with content-hash dedup (Crucix pattern).
CREATE TABLE IF NOT EXISTS news_items (
    content_hash VARCHAR PRIMARY KEY,
    source       VARCHAR     NOT NULL,
    ts           TIMESTAMPTZ NOT NULL,
    title        VARCHAR,
    body         VARCHAR,
    url          VARCHAR,
    keywords     VARCHAR[]
);
CREATE INDEX IF NOT EXISTS idx_news_items_ts ON news_items (ts);

-- Trades from watched whale wallets.
CREATE TABLE IF NOT EXISTS whale_trades (
    ts         TIMESTAMPTZ NOT NULL,
    wallet     VARCHAR     NOT NULL,
    market_id  VARCHAR     NOT NULL,
    side       VARCHAR     NOT NULL,
    price      DOUBLE      NOT NULL,
    size_usd   DOUBLE      NOT NULL,
    tx_hash    VARCHAR
);
CREATE INDEX IF NOT EXISTS idx_whale_trades_lookup ON whale_trades (wallet, ts);

-- Service heartbeat — lets operators see if the loop is alive.
CREATE TABLE IF NOT EXISTS service_heartbeat (
    ts        TIMESTAMPTZ NOT NULL,
    component VARCHAR     NOT NULL,
    message   VARCHAR
);
