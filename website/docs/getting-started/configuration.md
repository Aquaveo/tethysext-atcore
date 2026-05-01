---
id: getting-started-configuration
title: Configuration
sidebar_label: Configuration
sidebar_position: 2
---

# Configuration

After [installing](./installation.md) atcore, you'll configure your Tethys portal and your app to use it.

## Tethys portal `settings.py`

Add the third-party Django apps that atcore depends on to `INSTALLED_APPS` in your portal's `settings.py` (e.g., `tethys/tethys_portal/settings.py`):

```python
INSTALLED_APPS += [
    'datetimewidget',
    'django_select2',
    'taggit',
]
```

Source: the project [README](https://github.com/Aquaveo/tethysext-atcore/blob/master/README.md#settingspy).

## Persistent stores

Your app needs at least one persistent store backed by PostgreSQL with the PostGIS extension. atcore's models live in this store. From your app's `app.py`:

```python
# example — app.py
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting


class MyFirstApp(TethysAppBase):
    name = 'My First App'
    package = 'my_first_app'
    namespace = 'my_first_app'

    def persistent_store_settings(self):
        return (
            PersistentStoreDatabaseSetting(
                name='app_users_db',
                description='Stores AppUsers, Organizations, Resources, Workflows.',
                initializer='my_first_app.app.init_app_users_db',
                spatial=True,
                required=True,
            ),
        )
```

`spatial=True` enables PostGIS, which `SpatialResource` and any GeoAlchemy2 model relies on.

## Initializer

The persistent-store initializer creates the atcore tables and seeds the staff/developer user:

```python
# example — app.py
from tethysext.atcore.models.app_users import initialize_app_users_db


def init_app_users_db(engine, first_time):
    initialize_app_users_db(engine, first_time=first_time)
```

If you've subclassed `AppUser`, pass it:

```python
from .models.users import MyAppUser

def init_app_users_db(engine, first_time):
    initialize_app_users_db(engine, first_time=first_time, app_user_model=MyAppUser)
```

Run the initializer with `tethys syncstores my_first_app`.

## Permissions

atcore's `PermissionsGenerator` produces the role/license permission groups. Wire it into your app's `permissions()` method:

```python
# example — app.py
from tethysext.atcore.permissions.app_users import PermissionsGenerator
from tethysext.atcore.services.app_users.permissions_manager import AppPermissionsManager


def permissions(self):
    pm = AppPermissionsManager(self.namespace)
    gen = PermissionsGenerator(pm)
    return gen.generate()
```

See [Permissions](../concepts/permissions.md) for what gets generated.

## URL maps

Each atcore subsystem ships a `urls(...)` factory under [`tethysext.atcore.urls`](../api/urls/index.mdx). Compose them in `register_url_maps`:

```python
# example — app.py
from tethysext.atcore.urls import (
    app_users as app_users_urls,
    resources as resources_urls,
    spatial_reference as sr_urls,
)


def register_url_maps(self):
    UrlMap = url_map_maker(self.root_url)
    url_maps = []

    url_maps += list(app_users_urls.urls(
        url_map_maker=UrlMap, app=self,
        persistent_store_name='app_users_db',
        base_template='my_first_app/base.html',
    ))
    url_maps += list(resources_urls.urls(
        url_map_maker=UrlMap, app=self,
        persistent_store_name='app_users_db',
        resource_model=Project,  # your Resource subclass
        base_template='my_first_app/base.html',
    ))
    url_maps += list(sr_urls.urls(
        url_map_maker=UrlMap, app=self,
        persistent_store_name='app_users_db',
    ))

    return tuple(url_maps)
```

## Test database (for running atcore's own tests)

If you intend to run atcore's test suite, set the `ATCORE_TEST_DATABASE` environment variable to a PostgreSQL connection string for an empty test database:

```bash
export ATCORE_TEST_DATABASE="postgresql://tethys_super:pass@172.17.0.1:5435/atcore_tests"
```

Default per the project README:

```text
postgresql://tethys_super:pass@172.17.0.1:5435/atcore_tests
```

## Next

Build a minimum-viable atcore app: [Your First atcore App](./first-app.md).
