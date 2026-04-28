---
id: getting-started-installation
title: Installation
sidebar_label: Installation
sidebar_position: 1
---

# Installation

`tethysext-atcore` is a [Tethys Platform](https://docs.tethysplatform.org) extension. You install it into an existing Tethys environment.

## Requirements

From [`install.yml`](https://github.com/Aquaveo/tethysext-atcore/blob/master/install.yml) and [`pyproject.toml`](https://github.com/Aquaveo/tethysext-atcore/blob/master/pyproject.toml):

- **Tethys Platform** — the docker base image pins **Tethys 4.5.1**. Older 4.x versions may work but are not tested.
- **Python 3** — declared in classifiers.
- **PostgreSQL** with **PostGIS** for the app-users persistent store and any spatial models.
- **GeoServer** for spatial layer publishing (used by the spatial managers).
- **HTCondor** for batch / long-running jobs (used by the workflow managers).

Conda dependencies (auto-installed via `tethys install`):

```text
django>=3.2,<6
django-select2<8.3.0
django-taggit
geojson, jinja2, pandas, panel, param
pyshp>=3.0.0, requests
sqlalchemy<2
```

Pip dependencies:

```text
django-datetime-widget2
geoserver-restconfig>=2.0.10
```

## OS dependencies

On Debian / Ubuntu:

```bash
sudo apt update
sudo apt install gcc libgdal-dev g++ libhdf5-dev
```

These are required for building the spatial Python deps.

## Activate the Tethys environment

```bash
conda activate tethys
```

## Install the extension

Clone the repo and run `tethys install` from the project root:

```bash
git clone https://github.com/Aquaveo/tethysext-atcore.git
cd tethysext-atcore
tethys install -d   # development (editable install)
# OR
tethys install      # production
```

`tethys install` reads [`install.yml`](https://github.com/Aquaveo/tethysext-atcore/blob/master/install.yml) and resolves both conda and pip dependencies.

## Initialize the GeoServer workspace

atcore ships an `atcore init` console command that creates a default GeoServer workspace and uploads the bundled SLD styles:

```bash
atcore init --gsurl http://admin:geoserver@localhost:8181/geoserver/rest/
```

`--gsurl` defaults to `http://admin:geoserver@localhost:8181/geoserver/rest/`. The command is implemented in [`tethysext.atcore.cli.init_command`](../api/cli/init_command.mdx).

## Verify the install

```python
import tethysext.atcore  # noqa
from tethysext.atcore.models.app_users import AppUser, Resource  # noqa
from tethysext.atcore.controllers.map_view import MapView  # noqa
```

If those imports succeed, you're ready to wire atcore into a Tethys app — see [Configuration](./configuration.md) and [Your First atcore App](./first-app.md).
