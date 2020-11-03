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
    path = '../models/file_database'
    meta = dict()

    def write_meta(self):
        """Write a __meta__.json file. Create it if it does not exist."""
        with open(os.path.join(self.path, '__meta__.json'), 'w') as f:
            json.dump(self.meta, f)

    def read_meta(self):
        """Read a __meta__.json file."""
        meta_path = os.path.join(self.path, '__meta__.json')
        if os.path.exists(meta_path):
            try:
                with open(os.path.join(self.path, '__meta__.json'), 'r') as f:
                    meta_json = f.read()
                    if not meta_json == '':
                        self.meta = json.loads(meta_json)
                        return
            except json.JSONDecodeError:
                log.warning(f'Unable to read json for meta: {self.path}')

        else:
            with open(meta_path, 'w'):
                pass
        # If the meta file doesn't exist, or it is empty. Set meta to be an empty dictionary.
        self.meta = {}
        return
