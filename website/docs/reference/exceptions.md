---
id: reference-exceptions
title: Exceptions
sidebar_label: Exceptions
sidebar_position: 2
---

# Exceptions

Quick reference for the exceptions defined in [`tethysext.atcore.exceptions`](../api/exceptions/index.mdx). All eleven live in a single module; class hierarchy and "raised when" notes below.

## Class hierarchy

```text
Exception
├── ATCoreException
│   └── ModelDatabaseError
│       ├── ModelDatabaseInitializationError
│       └── ModelFileDatabaseInitializationError
├── UnboundFileCollectionError
├── UnboundFileDatabaseError
├── FileCollectionNotFoundError
├── FileCollectionItemNotFoundError
├── FileDatabaseNotFoundError
├── FileCollectionItemAlreadyExistsError
└── InvalidSpatialResourceExtentTypeError
```

## When each is raised

| Exception | Raised when |
| --- | --- |
| `ATCoreException` | Base class. Catch this to catch any atcore-specific error that shouldn't crash the request. The [`resource_controller`](../api/services/app_users/decorators.mdx) decorator handles it by surfacing `str(e)` as a Django message. |
| `ModelDatabaseError` | Generic problem talking to a `ModelDatabase`. |
| `ModelDatabaseInitializationError` | A `ModelDatabase` could not be created or initialized. |
| `ModelFileDatabaseInitializationError` | A `ModelFileDatabase` could not be created or initialized. |
| `UnboundFileDatabaseError` | A `FileDatabaseClient` operation ran after the underlying database was deleted. See [`FileDatabaseClient.instance`](../api/services/file_database.mdx#filedatabaseclient). |
| `UnboundFileCollectionError` | A `FileCollectionClient` operation ran after the underlying collection was deleted. |
| `FileDatabaseNotFoundError` | The id passed to `FileDatabaseClient` did not match any row. |
| `FileCollectionNotFoundError` | The id passed to `FileCollectionClient` did not match any row. |
| `FileCollectionItemNotFoundError` | The requested item is not in the collection. |
| `FileCollectionItemAlreadyExistsError` | An item with that name is already in the collection. |
| `InvalidSpatialResourceExtentTypeError` | `SpatialResource.set_extent` got an `object_format` other than `'wkt'`, `'geojson'`, or `'dict'`. See [`SpatialResource`](../api/models/app_users/spatial_resource.mdx). |

## Catching them

The most common pattern: let the [`resource_controller`](../api/services/app_users/decorators.mdx) decorator catch `ATCoreException` so it shows up as a user-visible warning. Raise `ATCoreException("Reason")` from your view code when the failure is expected and user-actionable.

```python
from tethysext.atcore.exceptions import ATCoreException

if some_invariant_violated:
    raise ATCoreException('Project must have a region before submitting an analysis.')
```

For file database operations, catch the specific `Not Found` / `AlreadyExists` errors:

```python
from tethysext.atcore.exceptions import (
    FileCollectionItemNotFoundError, FileCollectionItemAlreadyExistsError,
)

try:
    collection_client.add_item(path)
except FileCollectionItemAlreadyExistsError:
    ...
```

## See also

- [File Database](../concepts/file-database.md) — uses most of the file-related exceptions.
- [Resources](../concepts/resources.md) — `SpatialResource` raises `InvalidSpatialResourceExtentTypeError`.
