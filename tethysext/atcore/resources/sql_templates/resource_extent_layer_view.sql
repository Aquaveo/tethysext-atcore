SELECT id, name, description, ST_Transform(extent, 4326) as geometry
FROM app_users_resources
WHERE "resource_id" = %resource_id%
