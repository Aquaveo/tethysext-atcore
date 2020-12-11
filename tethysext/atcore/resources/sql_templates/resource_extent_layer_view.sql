SELECT id, name, description, ST_Transform(extent, 4326) as geometry
FROM app_users_resources
WHERE id::text = '%resource_id%'
