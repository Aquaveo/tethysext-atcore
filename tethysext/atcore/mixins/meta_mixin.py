"""
********************************************************************************
* Name: file_database.py
* Author: glarsen
* Created On: November 2, 2020
* Copyright: (c) Aquaveo 2020
********************************************************************************
"""
import copy
import json
import logging
import os

log = logging.getLogger('tethys.' + __name__)


class MetaMixin(object):
    path = '.'
    instance = None
    _session = None

    def write_meta(self):
        """Write a __meta__.json file. Create it if it does not exist."""
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with open(os.path.join(self.path, '__meta__.json'), 'w') as f:
            json.dump(self.instance.meta, f)

    def read_meta(self):
        """Read a __meta__.json file."""
        meta_path = os.path.join(self.path, '__meta__.json')
        if os.path.exists(meta_path):
            try:
                with open(os.path.join(self.path, '__meta__.json'), 'r') as f:
                    meta_json = f.read()
                    if not meta_json == '':
                        self.instance.meta = json.loads(meta_json)
                        return
            except json.JSONDecodeError:
                log.warning(f'Unable to read json for meta: {self.path}')

        else:
            with open(meta_path, 'w'):
                pass
        # If the meta file doesn't exist, or it is empty. Set meta to be an empty dictionary.
        self.instance.meta = {}
        return

    def get_meta(self, key):
        """Property to get the meta from the underlying instance."""
        return self.instance.meta[key]

    def set_meta(self, key, value):
        """Setter to set the meta on the underlying instance."""
        local_meta = copy.deepcopy(self.instance.meta)
        local_meta[key] = value
        self.instance.meta = local_meta
        self._session.commit()
        self.write_meta()
