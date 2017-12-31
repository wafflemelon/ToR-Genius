# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT


from discord.ext import commands


# noinspection PyProtectedMember
class _ContextDBAcquire:
    __slots__ = ('ctx', 'timeout')

    def __init__(self, ctx, timeout):
        self.ctx = ctx
        self.timeout = timeout

    def __await__(self):
        return self.ctx._acquire(self.timeout).__await__()

    async def __aenter__(self):
        await self.ctx._acquire(self.timeout)
        return self.ctx.db

    async def __aexit__(self, *args):
        await self.ctx.release()


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool = self.bot.pool
        self.db = None

    async def _acquire(self, timeout):
        if self.db is None:
            self.db = await self.pool.acquire(timeout=timeout)
        return self.db

    # async def acquire(self, timeout=None):
    #     return _ContextDBAcquire(self, timeout)

    @property
    def acquire(self):
        return _ContextDBAcquire

    async def release(self):
        """
        Releases the database connection from the pool.
        Useful if needed for "long" interactive commands where
        we want to release the connection and re-acquire later.
        Otherwise, this is called automatically by the bot.
        """

        if self.db is not None:
            await self.bot.pool.release(self.db)
            self.db = None

    async def auto_react(self, emoji='👌'):
        # noinspection PyBroadException
        try:
            await self.message.add_reaction(emoji)
        except:
            # No reaction perms probably
            await self.send(emoji)

    async def show_help(self, command=None):
        """
        Show help for a command
        :param command: String, command name
        :return: None
        """

        cmd = self.bot.get_command('help')
        command = command or self.command.qualified_name
        await self.invoke(cmd, command=command)
