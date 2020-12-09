SELECT id, name, description, extent as geometry
FROM app_users_resources
WHERE "resource_id" = %resource_id%
