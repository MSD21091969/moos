INSERT INTO containers (
  urn,
  parent_urn,
  kind,
  interface_json,
  kernel_json,
  permissions_json,
  version
)
VALUES
  (
    'urn:moos:root',
    NULL,
    'composite',
    '{"inputs":[],"outputs":[]}'::jsonb,
    '{"name":"Root","description":"System root container"}'::jsonb,
    '{"visibility":"system"}'::jsonb,
    1
  ),
  (
    'urn:moos:app:2XZ',
    'urn:moos:root',
    'composite',
    '{"inputs":[],"outputs":[]}'::jsonb,
    '{"name":"App 2XZ","template":true}'::jsonb,
    '{"visibility":"workspace"}'::jsonb,
    1
  ),
  (
    'urn:moos:user:admin',
    'urn:moos:root',
    'identity',
    '{"inputs":[],"outputs":[]}'::jsonb,
    '{"display_name":"Admin User","role":"admin"}'::jsonb,
    '{"visibility":"private"}'::jsonb,
    1
  ),
  (
    'urn:moos:user:demo',
    'urn:moos:root',
    'identity',
    '{"inputs":[],"outputs":[]}'::jsonb,
    '{"display_name":"Demo User","role":"member"}'::jsonb,
    '{"visibility":"private"}'::jsonb,
    1
  )
ON CONFLICT (urn) DO NOTHING;
