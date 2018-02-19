# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# error junk
# from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py

import logging
import time
from collections import Counter
from datetime import datetime

import discord
import humanize
from discord.ext import commands

from cogs.utils.checks import has_permissions

log = logging.getLogger(__name__)


class Mod:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, discord.Forbidden):
                await ctx.send(
                    'I do not have permission to execute this action.'
                )
            elif isinstance(original, discord.NotFound):
                await ctx.send(
                    f'This entity does not exist: {original.text}'
                )
            elif isinstance(original, discord.HTTPException):
                await ctx.send(
                    'Somehow, an unexpected error occurred. Try again later?'
                )

    @commands.command()
    @has_permissions(manage_messages=True)
    async def clean(self, ctx, limit: int = 20):
        """Delete all the messages from this bot, and commands that may have
        invoked this bot from the channel.

        You must have Manage Messages permissions"""

        # noinspection PyShadowingNames
        async def cleanup(ctx, limit):
            count = 0
            async for message in ctx.channel.history(
                    limit=limit, before=ctx.message
            ):
                if message.author == ctx.me:
                    await message.delete()
                    count += 1

            return {'Self': count}

        # noinspection PyShadowingNames
        async def complex_cleanup(ctx, limit):
            # `startswith` can't take a list, but it can take a tuple...
            prefix_tuple = tuple(self.bot.get_guild_prefixes(ctx.guild))

            deleted = await ctx.channel.purge(
                limit=limit,
                check=(
                    lambda m:
                    m.content.startswith(prefix_tuple)
                    or m.author == ctx.me
                )
            )

            return Counter(m.author.display_name for m in deleted)

        fun = cleanup
        if ctx.me.permissions_in(ctx.channel).manage_messages:
            fun = complex_cleanup

        users = await fun(ctx, limit)
        total_count = sum(users.values())
        messages = [
            f'{total_count} message'
            f'{" was" if total_count == 1 else "s were"} removed.'
        ]

        if total_count:
            messages.append('')  # newline
            users = sorted(
                users.items(),
                key=lambda c: c[1],
                reverse=True
            )
            messages.extend(f'**{name}**: {count}' for name, count in users)

        message = '\n'.join(messages)

        if len(message) > 2000:
            await ctx.send(
                f'Successfully removed {total_count} messages.',
                delete_after=10
            )
        else:
            await ctx.send(message, delete_after=10)

    @commands.command()
    @has_permissions(manage_messages=True)
    async def lockdown(self, ctx):
        channel_ld = self.bot.lockdown.get(ctx.channel, None)
        if channel_ld:
            # There is a lockdown on the channel, turn it off
            del self.bot.lockdown[ctx.channel]
        else:
            # turn on lockdown
            self.bot.lockdown[ctx.channel] = time.time()

        await ctx.auto_react()

    async def __global_check(self, ctx):
        owner = await self.bot.is_owner(ctx.author)
        if owner:
            return True

        if ctx.author.permissions_in(ctx.channel).manage_messages:
            return True

        channel_ld = self.bot.lockdown.get(ctx.channel, None)
        if channel_ld:
            if time.time() - channel_ld > 60:
                # It's been a minute
                del self.bot.lockdown[ctx.channel]
                return True

            time_to_wait = humanize.naturaldelta(
                datetime.fromtimestamp(channel_ld + 60)
            )
            await ctx.author.send(
                f'Sorry, but the bot is on lockdown because some people were '
                f'spamming it. Please wait {time_to_wait}.'
            )
            return False
        else:
            # No lockdown active, continue
            return True


def setup(bot):
    bot.add_cog(Mod(bot))
