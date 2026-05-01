---
id: concepts-file-database
title: File Database
sidebar_label: File Database
sidebar_position: 9
---

# File database

A SQL-tracked filesystem store. Use it when a `Resource` needs to own files on disk and you want to look them up through the database instead of walking directories.

## Anatomy

Models in [`tethysext.atcore.models.file_database`](../api/models/file_database/index.mdx):

- [`FileDatabase`](../api/models/file_database/file_database-module.mdx) — the top-level container. Carries a `meta` JSON blob and corresponds to a single root directory on disk.
- [`FileCollection`](../api/models/file_database/file_collection.mdx) — a named bucket of files within a `FileDatabase`. Backed by a UUID-named subdirectory.
- [`ResourceFileCollectionAssociation`](../api/models/file_database/resource_file_collection_association.mdx) — link table tying a `Resource` to one or more `FileCollection`s.

Clients in [`tethysext.atcore.services.file_database`](../api/services/file_database.mdx):

- [`FileDatabaseClient`](../api/services/file_database.mdx#filedatabaseclient) — bind / create file databases.
- [`FileCollectionClient`](../api/services/file_database.mdx#filecollectionclient) — bind / create file collections within a database.

## When to use it

- A `Resource` owns input files (uploaded shapefiles, rasters, parameter files) that need to live on disk because they're large or non-relational.
- A workflow step produces output files that should remain accessible after the step finishes.
- You want a uniform listing UI for "all the files this resource owns" via [`ResourceFilesTab`](../api/controllers/resources/tabs/files_tab.mdx).

If you only need a single root directory of free-form files and don't care about per-collection grouping, fall back to the Tethys app workspace. Use `FileDatabase` when you want SQL to remember which collection each file belongs to and which resource owns each collection.

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

On-disk layout: `<root_directory>/<file_database_id>/`. `write_meta()` persists the `meta` dict to a sidecar file alongside the database directory.

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

Exceptions are listed in the [exceptions reference](../reference/exceptions.md):

- `UnboundFileDatabaseError`, `UnboundFileCollectionError` — operating on a deleted client.
- `FileDatabaseNotFoundError`, `FileCollectionNotFoundError` — the requested id doesn't exist.
- `FileCollectionItemNotFoundError`, `FileCollectionItemAlreadyExistsError` — item-level mismatches.

## Wiring a Resource to its files

Two mixins help your `Resource` subclass own collections:

- [`FileCollectionMixin`](../api/mixins/file_collection_mixin.mdx) — model-level helper methods.
- [`FileCollectionsControllerMixin`](../api/mixins/file_collection_controller_mixin.mdx) — controller-level helpers for upload/download views.

Neither mixin is re-exported from `tethysext.atcore.mixins.__init__` — a comment in the source warns "DO NOT IMPORT ... CAUSES CIRCULAR IMPORT ISSUES". Import them directly from their submodules:

```python
from tethysext.atcore.mixins.file_collection_mixin import FileCollectionMixin
from tethysext.atcore.mixins.file_collection_controller_mixin import FileCollectionsControllerMixin
```

### Pattern A: per-resource `FileDatabase`

When a resource owns a whole tree of files (e.g., a `Project` with many input files and output collections), give it its own `FileDatabase` and grow `FileCollection`s underneath:

```python
# myapp_adapter/resources/project.py
import os
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.models.file_database import FileDatabase
from tethysext.atcore.models.types.guid import GUID
from tethysext.atcore.services.file_database import FileDatabaseClient


class Project(Resource):
    TYPE = 'project'
    __mapper_args__ = {'polymorphic_identity': TYPE}

    file_database_id = Column(GUID, ForeignKey('file_databases.id'))
    file_database = relationship(FileDatabase)

    @classmethod
    def new(cls, session, name, **kwargs):
        project = cls(name=name, **kwargs)
        client = FileDatabaseClient.new(
            session=session,
            root_directory=os.environ['FDB_ROOT_DIR'],
            meta={'project_name': name},
        )
        project.file_database = client.instance
        session.add(project)
        return project
```

The `FDB_ROOT_DIR` environment variable is one convention for pointing all `FileDatabase`s at a shared root volume. Replace it with whatever fits your deployment.

### Pattern B: per-collection attachment

When a resource needs a single collection (no nested grouping), use `FileCollectionMixin` to attach `FileCollection`s without a top-level `FileDatabase`:

```python
# myapp_adapter/resources/dataset.py
from tethysext.atcore.mixins.file_collection_mixin import FileCollectionMixin
from tethysext.atcore.models.app_users import Resource


class Dataset(Resource, FileCollectionMixin):
    TYPE = 'dataset'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

The mixin adds a `file_collections` relationship to `ResourceFileCollectionAssociation` and exposes `dataset.file_collection_client` once a collection is attached.

### Controller-side: file upload/download

To get upload/download views for a resource with collections, mix `FileCollectionsControllerMixin` into the matching `Manage*` controller:

```python
# tethysapp/myapp/controllers/resources/manage_datasets.py
from tethysext.atcore.controllers.app_users import ManageResources
from tethysext.atcore.mixins.file_collection_controller_mixin import (
    FileCollectionsControllerMixin,
)


class ManageDatasets(ManageResources, FileCollectionsControllerMixin):
    pass
```

It wires `_handle_delete` to drop the on-disk collection directory when the resource is deleted and provides the helpers [`ResourceFilesTab`](../api/controllers/resources/tabs/files_tab.mdx) uses to render the file listing.

## See also

- [Add a custom resource type](../how-to/add-a-resource-type.md) — combines `FileCollectionMixin` with a custom resource.
- [Wire up a file database](../how-to/wire-up-a-file-database.md) — end-to-end walkthrough.
