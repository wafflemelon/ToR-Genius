# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# _Technically_ not copy pasted, but I skipped large chunks as they were
# unneeded (at the time of writing this)

import inspect
import logging
from collections import OrderedDict

import asyncpg

log = logging.getLogger(__name__)


class SchemaError(Exception):
    pass


class SQLType:
    python = None

    def to_sql(self):
        raise NotImplementedError()


class Boolean(SQLType):
    python = bool

    def to_sql(self):
        return 'BOOLEAN'


class Integer(SQLType):
    python = int

    def __init__(self, *, big=False):
        self.big = big

    def to_sql(self):
        if self.big:
            return 'BIGINT'

        return 'INTEGER'


class Column:
    __slots__ = (
        'column_type', 'index', 'primary_key', 'nullable', 'default', 'unique',
        'name', 'index_name'
    )

    def __init__(self, column_type, *, index=False, primary_key=False,
                 nullable=True, default=None, unique=False, name=None):

        if inspect.isclass(column_type):
            column_type = column_type()

        if not isinstance(column_type, SQLType):
            raise TypeError('The column type must be a SQLType, mate!')

        self.column_type = column_type
        self.index = index
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.unique = unique
        self.name = name
        self.index_name = None

        if sum(map(bool, (unique, primary_key, default is not None))) > 1:
            raise SchemaError(
                "'unique', 'primary_key', and 'default' are mutually exclusive."
            )

    def _create_table(self):
        builder = [self.name, self.column_type.to_sql()]

        default = self.default
        if default is not None:
            builder.append('DEFAULT')
            if isinstance(default, bool):
                builder.append(str(default).upper())
            else:
                builder.append(f'({default})')
        elif self.unique:
            builder.append('UNIQUE')
        elif self.primary_key:
            builder.append('PRIMARY KEY')

        if not self.nullable:
            builder.append('NOT NULL')

        return ' '.join(builder)


class MaybeAcquire:
    def __init__(self, connection, *, pool):
        self.connection = connection
        self.pool = pool
        self._cleanup = False

    async def __aenter__(self):
        if self.connection is None:
            self._cleanup = True
            self._connection = c = await self.pool.acquire()
            return c
        return self.connection

    async def __aexit__(self, *args):
        if self._cleanup:
            await self.pool.release(self._connection)


# noinspection PyMethodParameters
class TableMeta(type):
    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        return OrderedDict()

    def __new__(cls, name, parents, dct, **kwargs):
        columns = []

        try:
            table_name = kwargs['table_name']
        except KeyError:
            table_name = name.lower()

        dct['__tablename__'] = table_name

        for elem, value in dct.items():
            if isinstance(value, Column):
                if value.name is None:
                    value.name = elem

                if value.index:
                    value.index_name = '%s_%s_idx' % (table_name, value.name)

                columns.append(value)

        dct['columns'] = columns
        return super().__new__(cls, name, parents, dct)

    def __init__(self, name, parents, dct, **kwargs):
        super().__init__(name, parents, dct)


class Table(metaclass=TableMeta):
    _pool = None

    @classmethod
    async def create_pool(cls, uri, **kwargs):
        cls._pool = pool = await asyncpg.create_pool(uri, **kwargs)
        return pool

    @classmethod
    def acquire_connection(cls, connection):
        return MaybeAcquire(connection, pool=cls._pool)

    @classmethod
    async def create(cls, *, verbose=False, connection=None):
        async with MaybeAcquire(connection, pool=cls._pool) as con:
            sql = await cls.create_table(exists_ok=True)
            if verbose:
                print(sql)

            await con.execute(sql)

    @classmethod
    async def create_table(cls, *, exists_ok=True):
        statements = []
        builder = ['CREATE TABLE']

        if exists_ok:
            builder.append('IF NOT EXISTS')

        # noinspection PyUnresolvedReferences
        builder.append(cls.__tablename__)
        # noinspection PyProtectedMember
        builder.append(f'({", ".join(c._create_table() for c in cls.columns)})')
        statements.append(' '.join(builder) + ';')

        # Index time

        for column in cls.columns:
            if column.index:
                # noinspection PyUnresolvedReferences
                sql = f'CREATE INDEX IF NOT EXISTS {column.index_name} ON ' \
                      f'{cls.__tablename__} ({column.name});'

                statements.append(sql)

        return '\n'.join(statements)

    @classmethod
    def all_tables(cls):
        return cls.__subclasses__()
