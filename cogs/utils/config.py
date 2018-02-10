# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# Config object for prefixes because reasons and I'm lazy
# From https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/config.py
import asyncio
import json
import os
import uuid


class Config:
    """Stuff that doesn't make sense in a db I guess"""

    def __init__(self, name):
        self.name = name
        self.load_from_file()
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()

    # noinspection PyAttributeOutsideInit
    def load_from_file(self):
        try:
            with open(self.name, 'r') as f:
                self._db = json.load(f)
        except FileNotFoundError:
            # no data, so leave it empty
            self._db = {}

    def get(self, key, default=None):
        """Get entry from config"""
        return self._db.get(str(key), default)

    async def put(self, key, value):
        """Edits config value"""
        self._db[str(key)] = value
        await self.save()

    async def delete(self, key):
        """Delete config value"""
        del self._db[str(key)]
        await self.save()

    def _dump(self):
        temp = '%s%s.tmp' % (uuid.uuid4(), self.name)
        with open(temp, 'w') as tmp:
            json.dump(
                self._db.copy(),
                tmp
            )

        # rek that file
        os.replace(temp, self.name)

    async def save(self):
        async with self.lock:
            self.loop.run_in_executor(None, self._dump)

    def __contains__(self, item):
        return str(item) in self._db

    def __getitem__(self, item):
        return self._db[str(item)]

    def __len__(self):
        return len(self._db)

    def __iter__(self):
        for k, v in self.all().items():
            yield (k, v)

    def all(self):
        return self._db
