CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_containers_updated_at ON containers;
CREATE TRIGGER trg_containers_updated_at
BEFORE UPDATE ON containers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_embeddings_updated_at ON embeddings;
CREATE TRIGGER trg_embeddings_updated_at
BEFORE UPDATE ON embeddings
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
