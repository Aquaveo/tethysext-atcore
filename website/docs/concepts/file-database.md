---
id: concepts-file-database
title: File Database
sidebar_label: File Database
sidebar_position: 9
---

# File database

The file database is a SQL-tracked filesystem store. Use it when a `Resource` (or other model) needs to own a versioned set of files on disk and you want to look those files up via the database rather than walking directories.

## Anatomy

Models in [`tethysext.atcore.models.file_database`](../api/models/file_database/index.mdx):

- [`FileDatabase`](../api/models/file_database/file_database-module.mdx) — the top-level container. Carries a `meta` JSON blob.
- [`FileCollection`](../api/models/file_database/file_collection.mdx) — a named bucket of files within a `FileDatabase`.
- [`ResourceFileCollectionAssociation`](../api/models/file_database/resource_file_collection_association.mdx) — link table tying a `Resource` to a `FileCollection`.

Clients in [`tethysext.atcore.services.file_database`](../api/services/file_database.mdx):

- [`FileDatabaseClient`](../api/services/file_database.mdx#filedatabaseclient) — bind / create file databases.
- [`FileCollectionClient`](../api/services/file_database.mdx#filecollectionclient) — bind / create file collections within a database.

## Creating a file database

```python
# example — services
from tethysext.atcore.services.file_database import FileDatabaseClient

# Create on disk + in DB
client = FileDatabaseClient.new(
    session=session,
    root_directory='/var/lib/myapp/file_dbs',
    meta={'project': 'demo'},
)

# ...later, bind to an existing one by id:
client = FileDatabaseClient(
    session=session,
    root_directory='/var/lib/myapp/file_dbs',
    file_database_id=existing_id,
)
```

The on-disk layout is `<root_directory>/<file_database_id>/`. Calling `write_meta()` on the client persists the `meta` dict to a sidecar file alongside the database directory.

## Working with collections

```python
# example — services
from tethysext.atcore.services.file_database import FileCollectionClient

collection_client = FileCollectionClient.new(
    session=session,
    file_database_client=client,
    meta={'kind': 'inputs'},
)
collection_client.add_item('/tmp/some_input.txt')
items = list(collection_client.files)
```

The available exceptions are documented in the [exceptions reference](../reference/exceptions.md):

- `UnboundFileDatabaseError`, `UnboundFileCollectionError` — operating on a deleted client.
- `FileDatabaseNotFoundError`, `FileCollectionNotFoundError` — the requested id doesn't exist.
- `FileCollectionItemNotFoundError`, `FileCollectionItemAlreadyExistsError` — item-level mismatches.

## Mixins for `Resource`

Two mixins help your `Resource` subclass own collections:

- [`FileCollectionMixin`](../api/mixins/file_collection_mixin.mdx) — model-level helper methods.
- [`FileCollectionsControllerMixin`](../api/mixins/file_collection_controller_mixin.mdx) — controller-level helpers for upload/download views.

:::caution Verification needed
The `FileCollectionMixin` and `FileCollectionsControllerMixin` are intentionally _not_ re-exported from `tethysext.atcore.mixins.__init__` (a comment in the source notes "DO NOT IMPORT ... CAUSES CIRCULAR IMPORT ISSUES"). Import them directly from their submodules — `from tethysext.atcore.mixins.file_collection_mixin import FileCollectionMixin`. We have not validated end-to-end that subclassing `Resource` with these mixins is the recommended pattern; this should be confirmed by the maintainers.
:::
