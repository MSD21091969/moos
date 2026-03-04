CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS containers (
  urn TEXT PRIMARY KEY,
  parent_urn TEXT REFERENCES containers(urn) ON DELETE SET NULL,
  kind TEXT NOT NULL,
  interface_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  kernel_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  permissions_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  version BIGINT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT containers_version_positive CHECK (version > 0)
);

CREATE INDEX IF NOT EXISTS idx_containers_parent_urn ON containers(parent_urn);
CREATE INDEX IF NOT EXISTS idx_containers_kind ON containers(kind);
CREATE INDEX IF NOT EXISTS idx_containers_kernel_gin ON containers USING GIN (kernel_json);

CREATE TABLE IF NOT EXISTS wires (
  id BIGSERIAL PRIMARY KEY,
  from_container_urn TEXT NOT NULL REFERENCES containers(urn) ON DELETE CASCADE,
  from_port TEXT NOT NULL,
  to_container_urn TEXT NOT NULL REFERENCES containers(urn) ON DELETE CASCADE,
  to_port TEXT NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(from_container_urn, from_port, to_container_urn, to_port)
);

CREATE INDEX IF NOT EXISTS idx_wires_from ON wires(from_container_urn, from_port);
CREATE INDEX IF NOT EXISTS idx_wires_to ON wires(to_container_urn, to_port);

CREATE TABLE IF NOT EXISTS morphism_log (
  id UUID PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('ADD', 'LINK', 'MUTATE', 'UNLINK')),
  actor_urn TEXT NOT NULL,
  scope_urn TEXT NOT NULL,
  expected_version BIGINT,
  payload_json JSONB NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  issued_at TIMESTAMPTZ NOT NULL,
  committed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_morphism_scope_time ON morphism_log(scope_urn, committed_at DESC);
CREATE INDEX IF NOT EXISTS idx_morphism_type_time ON morphism_log(type, committed_at DESC);

CREATE TABLE IF NOT EXISTS embeddings (
  urn TEXT PRIMARY KEY REFERENCES containers(urn) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  dimensions INTEGER NOT NULL,
  embedding vector(1536) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
  ON embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
