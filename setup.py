import os
from setuptools import setup, find_packages


def find_resource_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


# -- Extension Definition -- #
ext_package = 'atcore'
release_package = 'tethysext-' + ext_package
ext_class = 'atcore.ext:Atcore'
ext_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysext', ext_package)

# -- Python Dependencies -- #
dependencies = [
    'sqlalchemy',
    'factory_boy',
    'jinja2',
    'requests',
    'param',
    'geojson',
    'pyshp',
    'django-datetime-widget',
    'django-select2',
    'django-taggit',
    'filelock'
]

# -- Get Resource File -- #
resource_files = find_resource_files('tethysext/' + ext_package + '/templates')
resource_files += find_resource_files('tethysext/' + ext_package + '/public')
resource_files += find_resource_files('tethysext/' + ext_package + '/resources')

setup(
    name=release_package,
    version='0.3.0',
    description='',
    long_description='',
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_packages(
        exclude=['ez_setup', 'examples', 'tethysext/' + ext_package + '/tests', 'tethysext/' + ext_package + '/tests.*']
    ),
    package_data={'': resource_files},
    namespace_packages=['tethysext', 'tethysext.' + ext_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    test_suite='tethysext.atcore.tests'
)
