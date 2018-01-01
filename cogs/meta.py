# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# Help command from R. Danny, along with feedback, pm, and prefixes

import discord
from discord.ext import commands

from cogs.utils.checks import is_mod
from .utils.paginator import HelpPaginator


class Prefix(commands.Converter):
    async def convert(self, ctx, argument):
        user_id = ctx.bot.user.id
        if argument.startswith((f'<@{user_id}>', f'<@!{user_id}>')):
            raise commands.BadArgument(
                'That is a reserved prefix already in use.'
            )
        return argument


class Meta:
    """Meta stuff geddit haha so funny ikr"""

    def __init__(self, bot):
        self.bot = bot
        bot.remove_command('help')

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.command(name='help')
    async def _help(self, ctx, *, command: str = None):
        """Helps you out a bit ;)"""
        # noinspection PyBroadException
        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) \
                         or self.bot.get_command(command)

                if entity is None:
                    clean = command.replace('@', '@ ')  # non breaking space
                    return await ctx.send(
                        f'Command or category "{clean} not found'
                    )
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            ctx.send(f'```\n{e}\n```')

    @commands.group(name='prefix', invoke_without_command=True)
    async def prefix(self, ctx):
        """Customize the prefixes

        Calling without a subcommand lists prefixes
        """
        prefixes = self.bot.get_guild_prefixes(ctx.guild)

        # Don't list the mention prefix twice
        del prefixes[1]

        embed = discord.Embed(
            title='Prefixes',
            color=discord.Color.dark_teal(),
            description='\n'.join(
                f'#{index}: {elem}' for index, elem in enumerate(prefixes, 1)
            )
        ).set_footer(
            text=f'I have {len(prefixes)} prefixes'
        )

        await ctx.send(embed=embed)

    # Ignore extra for when people forget to quote
    #
    # We won't catch the rest of args because it's ambiguous if they wanted to
    # add multiple prefixes or they wanted to add one multi-word prefix.
    @is_mod()
    @prefix.command(name='add', ignore_extra=False)
    async def prefix_add(self, ctx, prefix: Prefix):
        """Appends a prefix to the list of custom prefixes.


        Previously set prefixes are not overridden.


        To have a word prefix, you should quote it and end it with
        a space, e.g. "hello " to set the prefix to "hello ". This
        is because Discord removes spaces when sending messages so
        the spaces are not preserved.


        Multi-word prefixes must be quoted also.


        You must have Manage Server permission to use this command.
        """

        # yeah I'm copying docstrings now woot woot
        # https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/meta.py#L96

        # Error checking in Prefix class (top o' file)

        prefixes = self.bot.get_other_prefixes(ctx.guild)
        prefixes.append(prefix)

        try:
            await self.bot.set_guild_prefixes(ctx.guild, prefixes)
        except RuntimeError as e:
            await ctx.auto_react('🚫')
            await ctx.send(e)
        else:
            await ctx.auto_react()

    @prefix_add.error
    async def prefix_add_error(self, ctx, error):
        if isinstance(error, commands.TooManyArguments):
            await ctx.auto_react('🚫')
            await ctx.send(
                "You can only add one prefix at a time. If you are trying to "
                "use a multi-word prefix "
            )

    @is_mod()
    @prefix.command(
        name='remove', aliases=['delete', 'del', 'rm'], ignore_extra=False
    )
    async def prefix_remove(self, ctx, prefix: Prefix):
        """Removes a prefix from the list of custom prefixes

        You can use this to remove any custom or default prefix, it is the
        opposite of prefix add.
        """

        prefixes = self.bot.get_other_prefixes(ctx.guild)

        try:
            prefixes.remove(prefix)
        except KeyError:
            await ctx.auto_react('🚫')
            await ctx.send("That's not one of my prefixes, sorry!")
            return

        try:
            await self.bot.set_guild_prefixes(ctx.guild, prefixes)
        except RuntimeError as e:
            await ctx.auto_react('🚫')
            await ctx.send(e)
        else:
            await ctx.auto_react()

    @is_mod()
    @prefix.command(name='clear')
    async def prefix_clear(self, ctx):
        """Clears all prefixes, custom and default except for direct mentions"""

        await self.bot.set_guild_prefixes(ctx.guild, [])
        await ctx.auto_react()

    @is_mod()
    @prefix.command(name='reset')
    async def prefix_reset(self, ctx):
        """Resets to the default prefix, `;`."""

        await self.bot.set_guild_prefixes(ctx.guild, [';'])
        await ctx.auto_react()

    @commands.command(aliases=['pong'])
    async def ping(self, ctx):
        await ctx.send(f'Pong! {self.bot.latency*1000:,.2}ms of latency! 🏓')

    @commands.command(aliases=['fb'])
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def feedback(self, ctx, *, body: str):
        """PM the owner with feedback, questions and more.

        Feel free to use this to contact me (the owner) about anything and stuff.

        You can use this once every two minutes.
        """

        embed = discord.Embed(
            color=0x2db5e2,
            description=body,
            timestamp=ctx.message.created_at
        )

        me = await self.bot.application_info()
        me = me.owner

        embed.set_author(
            name=ctx.author.name,
            icon_url=ctx.author.avatar_url_as(format='png')
        )

        if ctx.guild is None:
            embed.set_footer(text='DM')
        else:
            embed.add_field(
                name='Server',
                value=f'{ctx.guild.name} (ID: `{ctx.guild.id}`)',
                inline=False
            )

        if ctx.channel is not None:
            embed.add_field(
                name='Channel',
                value=f'{ctx.channel} (ID: `{ctx.channel.id}`)',
                inline=False
            )

        if not isinstance(embed.footer.text, str):
            embed.set_footer(
                text=f'Author ID: {ctx.author.id}'
            )
        else:
            embed.set_footer(
                text=f'{embed.footer.text} | Author ID: {ctx.author.id}'
            )

        await me.send(embed=embed)
        await ctx.auto_react(emoji='✅')

    @commands.command()
    @commands.is_owner()
    async def pm(self, ctx, user_id: int, *, content: str):
        user = self.bot.get_user(user_id)

        content = content + '\n\nThis DM is in response to your recent ' \
                            'feedback. If you want to reply, make sure you ' \
                            'use the `!feedback` command again. (One use ' \
                            'every two minutes) '

        # noinspection PyBroadException
        try:
            await user.send(content)
        except:
            await ctx.send(f'Could not PM User (ID: {user_id})')
        else:
            await ctx.auto_react()


def setup(bot):
    bot.add_cog(Meta(bot))
