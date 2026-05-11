---
id: how-to-wire-up-a-file-database
title: Wire Up a File Database
sidebar_label: Wire up a file database
sidebar_position: 9
---

# Wire up a file database

Attach a [`FileDatabase`](../concepts/file-database.md) to a custom `Resource` and expose its files through `ResourceFilesTab` and the upload/download views.

The pattern below fits apps that own large input/output trees per resource. For a simpler "one collection of files per resource," skip the per-resource `FileDatabase` and mix in `FileCollectionMixin` instead — see Pattern B in the [File Database concept page](../concepts/file-database.md#pattern-b-per-collection-attachment).

## 1. Configure the file-database root

Pick a location on disk for the file databases. The convention is an `FDB_ROOT_DIR` env var pointing at a shared volume:

```bash
export FDB_ROOT_DIR=/var/lib/myapp/file_dbs
```

Add the directory to your deployment manifest (Helm chart, Compose file, etc.) and make sure the Tethys process can write to it.

## 2. Add a `file_database` relationship to your `Resource`

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
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'
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

    @property
    def file_database_client(self):
        return FileDatabaseClient(
            session=Session.object_session(self),
            root_directory=os.environ['FDB_ROOT_DIR'],
            file_database_id=self.file_database_id,
        )
```

`Project.new()` creates the on-disk database alongside the row. Call it from your `ModifyResource` controller's `handle_resource_finished_processing` hook so new projects always have a backing `FileDatabase`.

## 3. Add child resources that own their own collections

When the project has datasets that each own a collection of files, define a `Dataset` that mixes in `FileCollectionMixin`:

```python
# myapp_adapter/resources/dataset.py
from tethysext.atcore.mixins.file_collection_mixin import FileCollectionMixin
from tethysext.atcore.models.app_users import Resource


class Dataset(Resource, FileCollectionMixin):
    TYPE = 'dataset'
    DISPLAY_TYPE_SINGULAR = 'Dataset'
    DISPLAY_TYPE_PLURAL = 'Datasets'
    __mapper_args__ = {'polymorphic_identity': TYPE}
```

Import the mixin from the submodule directly — it isn't re-exported from `tethysext.atcore.mixins.__init__` to avoid a circular import.

## 4. Create collections under the project's file database

In a workflow step or controller, attach a `FileCollection` to a `Dataset` under the parent `Project`'s `FileDatabase`:

```python
# myapp/controllers/datasets/upload_dataset.py
from tethysext.atcore.services.file_database import FileCollectionClient


def attach_dataset_files(session, project, dataset, uploaded_files):
    client = FileCollectionClient.new(
        session=session,
        file_database_client=project.file_database_client,
        meta={'kind': 'inputs', 'dataset_id': str(dataset.id)},
    )
    for upload in uploaded_files:
        # add_item takes a path on disk and copies the file into
        # the collection's UUID-named directory.
        client.add_item(upload.temporary_file_path())

    dataset.file_collections.append(client.instance)
    session.commit()
```

The on-disk layout becomes:

```
$FDB_ROOT_DIR/
  <project.file_database_id>/
    <collection_uuid_1>/   ← Dataset A
      input.tif
      boundary.shp
    <collection_uuid_2>/   ← Dataset B
      meteo.nc
```

## 5. Wire the `Manage*` controller for cleanup

Mix `FileCollectionsControllerMixin` into the dataset's `ManageResources` controller so deleting a `Dataset` also drops the collection directory:

```python
# myapp/controllers/datasets/manage_datasets.py
from tethysext.atcore.controllers.app_users import ManageResources
from tethysext.atcore.mixins.file_collection_controller_mixin import (
    FileCollectionsControllerMixin,
)


class ManageDatasets(ManageResources, FileCollectionsControllerMixin):
    pass
```

Register it via the per-resource controller list when wiring URLs:

```python
# myapp/app.py
from myapp_adapter.resources.project import Project
from myapp_adapter.resources.dataset import Dataset
from .controllers.projects.manage_projects import ManageProjects, ModifyProject
from .controllers.datasets.manage_datasets import ManageDatasets
from .controllers.datasets.modify_dataset import ModifyDataset

url_maps += list(app_users_urls.urls(
    url_map_maker=UrlMap, app=self,
    persistent_store_name='primary_db',
    custom_resources={
        Project: [ManageProjects, ModifyProject],
        Dataset: [ManageDatasets, ModifyDataset],
    },
    base_template='myapp/base.html',
))
```

## 6. Show the files on the dataset's tabbed details page

Add `ResourceFilesTab` to the dataset's `TabbedResourceDetails` (see [Add a tabbed resource details page](./add-a-tabbed-resource-details-page.md) for the full pattern):

```python
class DatasetDetails(TabbedResourceDetails):
    template_name = 'myapp/dataset_details.html'
    tabs = (
        {'slug': 'summary', 'title': 'Summary', 'view': DatasetSummaryTab},
        {'slug': 'files', 'title': 'Files', 'view': ResourceFilesTab},
    )
```

`ResourceFilesTab` reads `dataset.file_collections` (from `FileCollectionMixin`) and renders an upload/download UI per collection.

## 7. Async deletion for big projects

Deleting a `Project` with hundreds of datasets and gigabytes of files can take a while. Override `ManageResources._handle_delete` to flip the status to `STATUS_DELETING` and spawn a daemon `Thread` for the cleanup:

```python
# myapp/controllers/projects/manage_resource_delete_mixin.py
import threading
from tethysext.atcore.mixins.status_mixin import StatusMixin


class ManageResourceDeleteMixin:
    def _handle_delete(self, request, session, resource, *args, **kwargs):
        resource.set_status(StatusMixin.STATUS_DELETING)
        session.commit()
        threading.Thread(
            target=self.delete_resource_artifacts,
            args=(resource.id,),
            daemon=True,
        ).start()
        return self._delete_response(request, resource)

    def delete_resource_artifacts(self, resource_id):
        # Drop on-disk collections, GeoServer layers, Condor workspaces, ...
        ...
```

Mix it into your `ManageProjects` controller. The user gets an immediate redirect and the cleanup runs in the background.

## See also

- [File Database concept page](../concepts/file-database.md) — the underlying models and exception types.
- [Add a custom resource type](./add-a-resource-type.md) — for the basic Resource subclassing recipe.
