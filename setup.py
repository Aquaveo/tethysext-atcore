import os
from setuptools import setup, find_namespace_packages


def find_resource_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


# -- Extension Definition -- #
ext_package = 'atcore'
release_package = 'tethysext-' + ext_package

# -- Get Resource File -- #
resource_files = find_resource_files('tethysext/' + ext_package + '/templates')
resource_files += find_resource_files('tethysext/' + ext_package + '/public')
resource_files += find_resource_files('tethysext/' + ext_package + '/resources')

setup(
    name=release_package,
    version='0.11.1',
    description='',
    long_description='',
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_namespace_packages(
        exclude=['ez_setup', 'examples', 'docker', '.github', 'docs', 'helm',
                 'tethysext/' + ext_package + '/tests',
                 'tethysext/' + ext_package + '/tests.*']
    ),
    package_data={'': resource_files},
    include_package_data=True,
    zip_safe=False,
    install_requires=[],  # IMPORTANT: LIST DEPENDENCIES IN install.yml INSTEAD OF HERE
    test_suite='tethysext.atcore.tests',
    entry_points={
        'console_scripts': ['atcore=tethysext.atcore.cli:atcore_command'],
    },
)
