# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# error junk
# from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py

import datetime
import logging
import re
import string
import time
from collections import Counter

import discord
import emoji
import humanize
from discord.ext import commands

from cogs.utils.checks import has_permissions

log = logging.getLogger(__name__)


def purge_count(arg):
    try:
        arg = int(arg)
    except ValueError:
        raise commands.BadArgument('The purge amount needs to be an int.')

    if arg > 300:
        raise commands.BadArgument('The purge amount can\'t be above 300')

    # add one because of the message sent to invoke the command
    return arg + 1


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
                datetime.datetime.fromtimestamp(channel_ld + 60)
            )
            await ctx.author.send(
                f'Sorry, but the bot is on lockdown because some people were '
                f'spamming it. Please wait {time_to_wait}.'
            )
            return False
        else:
            # No lockdown active, continue
            return True

    @commands.group(aliases=['delete', 'prune'],
                    invoke_without_command=True)
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, count: purge_count = None):
        """Purge X number of messages. 20 by default.

        Calling with no arguments shows help.

        Calling with a count will purge that count with no criteria."""
        if not count:
            return await ctx.show_help('purge')

        await ctx.channel.purge(limit=count)

    @purge.command(name='all')
    async def purge_all(self, ctx, count: purge_count = 20):
        """Alias for `purge 20`"""
        await ctx.channel.purge(limit=count)

    @purge.command(name='embeds', alises=['embed'])
    async def purge_embeds(self, ctx, count: purge_count = 20):
        """Purge any messages with an embed (image, link, or otherwise)"""
        await ctx.channel.purge(
            limit=count,
            check=lambda m: len(m.embeds) > 0 or len(m.attachments) > 0
        )

    @purge.command(name='with', aliases=['in', 'contains'])
    async def purge_with(self, ctx, content: str.lower,
                         count: purge_count = 20):
        """Purge any message containing a certain string."""
        await ctx.channel.purge(
            limit=count, check=lambda m: content in m.content.lower()
        )

    @purge.command(name='from', aliases=['author'])
    async def purge_from(self, ctx, user: commands.MemberConverter,
                         count: purge_count = 20):
        """Purge any messages from a user0"""
        await ctx.channel.purge(
            limit=count, check=lambda m: m.author is user
        )

    @purge.command(name='bots', aliases=['bot'])
    async def purge_bots(self, ctx, count: purge_count = 20, prefix: str = '!'):
        """Purge a message from any bots, and optionally starting with a
        certain prefix"""
        await ctx.channel.purge(
            limit=count,
            check=lambda m: m.author.bot or m.content.startswith(prefix)
        )

    @purge.command(name='regex', aliases=['re'])
    async def purge_regex(self, ctx, regex: str, count: purge_count = 20):
        """Advanced: Purge any message that matches a certain regex"""
        await ctx.channel.purge(
            limit=count,
            check=lambda m: re.match(regex, m.content)
        )

    @purge.command(name='emoji', alises=['emote', 'emojis'])
    async def purge_emojis(self, ctx, count: purge_count = 20):
        """Purge any message that contains emojis"""
        await ctx.channel.purge(
            limit=count,
            check=lambda m:
            any([c in emoji.UNICODE_EMOJI for c in m.content])
            or re.match(r'<:.+:[1-9]+>', m.content)
        )

    @purge.command(name='urls', aliases=['url', 'links', 'link'])
    async def purge_urls(self, ctx, count: purge_count = 20):
        """Purge any message that contains a certain URL"""
        regex = r'(?:https?:\/\/)?(?:[\w]+\.)(?:\.?[\w]{2,})+'

        await ctx.channel.purge(
            limit=count,
            check=lambda m: re.match(regex, m.content)
        )

    # noinspection SpellCheckingInspection
    @purge.command(name='nonascii', aliases=['noascii'])
    async def purge_non_ascii(self, ctx, count: purge_count = 20):
        """Purge any message not containing normal ascii charecters"""
        await ctx.channel.purge(
            limit=count,
            check=lambda m: any([c not in string.printable for c in m.content])
        )

    @purge.command(name='reactions', aliases=['react'])
    async def purge_reactions(self, ctx, count: purge_count = 20):
        """Clear all the reactions from messages"""
        [await m.clear_reactions()
         async for m in ctx.channel.history(limit=count)]

    # noinspection SpellCheckingInspection
    @purge.command(name='roleless', aliases=['whitenames'])
    async def purge_roleless(self, ctx, count: purge_count = 20):
        """Purge any messages from users with 0 roles"""
        await ctx.channel.purge(
            limit=count,
            check=lambda m: len(m.author.roles) < 1
        )

    # noinspection SpellCheckingInspection
    @purge.command(name='new', aliases=['newusers', 'raid'])
    async def purge_new(self, ctx, count: purge_count = 20,
                        time_ago: int = 60):
        """Purge any messages from members that joined X minutes ago
        (default 60)"""
        cutoff = datetime.datetime.now() - datetime.timedelta(
            minutes=time_ago)
        await ctx.channel.purge(
            limit=count,
            check=lambda m: m.author.joined_at > cutoff
        )

    @purge.command(name='me')
    async def purge_me(self, ctx, count: purge_count = 20):
        """Same as `clean`"""
        await ctx.run_command('clean', limit=count)


def setup(bot):
    bot.add_cog(Mod(bot))
