"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: November 2, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import json
import logging
import os

log = logging.getLogger('tethys.' + __name__)


class MetaMixin(object):
    path = '.'
    meta = dict()

    def write_meta(self, path=None):
        """
        Write a __meta__.json file. Create it if it does not exist.

        Arguments:
            path(str): A path to where the meta file is.
        """
        meta_path = path
        if meta_path is None:
            meta_path = self.path
        with open(os.path.join(meta_path, '__meta__.json'), 'w') as f:
            json.dump(self.meta, f)

    def read_meta(self, path=None):
        """Read a __meta__.json file."""
        meta_path = path
        if meta_path is None:
            meta_path = self.path
        meta_file = os.path.join(meta_path, '__meta__.json')
        if os.path.exists(meta_file):
            try:
                with open(os.path.join(meta_file), 'r') as f:
                    meta_json = f.read()
                    if not meta_json == '':
                        self.meta = json.loads(meta_json)
                        return
            except json.JSONDecodeError:
                log.warning(f'Unable to read json for meta: {meta_file}')

        else:
            with open(meta_file, 'w'):
                pass
        # If the meta file doesn't exist, or it is empty. Set meta to be an empty dictionary.
        self.meta = {}
        return
