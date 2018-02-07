# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT
import asyncio

import praw
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
        self.token = 'A dead meme'

        self.r = praw.Reddit('main', user_agent='ToR Discord Bot')

    async def _acquire(self, timeout):
        if self.db is None:
            self.db = await self.pool.acquire(timeout=timeout)
        return self.db

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

    async def prompt(self, message, *, timeout=60.0, delete_after=True,
                     reacquire=True, author_id=None, needs_mod=False):
        """An interactive reaction confirmation dialog.
        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        reacquire: bool
            Whether to release the database connection and then acquire it
            again when we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author
            of the Context's message.
        needs_mod: bool
            If the person doing the reaction needs mod perms, i.e. for
            something that needs verified
        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        if not self.channel.permissions_for(self.me).add_reactions:
            await self.send(
                'Bot does not have Add Reactions permission.'
            )
            return None

        fmt = f'{message}\n\nReact with \N{WHITE HEAVY CHECK MARK} to ' \
              f'confirm or \N{CROSS MARK} to deny.'

        author_id = author_id or self.author.id
        msg = await self.send(fmt)

        confirm = None

        def check(e, message_id, channel_id, user_id):
            nonlocal confirm

            # ugly but idc
            if needs_mod and not self.guild.get_channel(
                    channel_id).permissions_for(
                    self.guild.get_member(user_id).ban_members is True):
                return False

            if message_id != msg.id or user_id != author_id:
                return False

            code_point = str(e)

            if code_point == '\N{WHITE HEAVY CHECK MARK}':
                confirm = True
                return True
            elif code_point == '\N{CROSS MARK}':
                confirm = False
                return True

            return False

        for emoji in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}'):
            await msg.add_reaction(emoji)

        if reacquire:
            await self.release()

        try:
            await self.bot.wait_for(
                'raw_reaction_add',
                check=check,
                timeout=timeout
            )
        except asyncio.TimeoutError:
            confirm = None

        try:
            if reacquire:
                await self.acquire()

            if delete_after:
                await msg.delete()
        finally:
            return confirm
