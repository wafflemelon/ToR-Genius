# Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT


import logging
import random

from discord.ext import commands

from cogs.utils.checks import tor_only
from cogs.utils.paginator import Pages

log = logging.getLogger(__name__)


class Discriminator(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            if not int(argument) in range(1, 10000):
                raise commands.BadArgument('That isn\'t a valid discriminator.')
        except ValueError:
            raise commands.BadArgument('That isn\'t a valid discriminator.')
        else:
            return int(argument)


class Selector(commands.Converter):
    async def convert(self, ctx, argument):
        if argument not in ['>', '>=', '<', '<=', '=']:
            raise commands.BadArgument('Not a valid selector')
        return argument


class Fun:
    """How much fun can a fun fun have if a fun fun could have fun?"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(invoke_without_command=True, disabled=True, hidden=True)
    async def awesome(self, ctx):
        """Tells you your awesome status"""
        query = 'SELECT is_awesome FROM fun_config WHERE guild_id = $1;'

        val = await ctx.db.fetchval(query, ctx.guild.id)
        if val is None or not val:
            result = 'Yeah. U Have No Awesome.'
        else:
            # noinspection SpellCheckingInspection
            result = 'Aww yiss'

        await ctx.send(result)

    @awesome.command(name='on', aliases=['yes', 'true'], disabled=True)
    async def awesome_on(self, ctx):
        """Turns on your awesome status"""
        query = """
    INSERT INTO fun_config (guild_id, is_awesome) VALUES ($1, TRUE)
    ON CONFLICT (guild_id)
      DO UPDATE SET
        is_awesome = EXCLUDED.is_awesome;"""

        await ctx.db.execute(query, ctx.guild.id)
        await ctx.send('ur s0 aw3som3')

    @awesome.command(name='off', aliases=['no', 'false'])
    async def awesome_off(self, ctx):
        """Turns off your awesome status"""
        query = """
    INSERT INTO fun_config (guild_id, is_awesome) VALUES ($1, FALSE)
    ON CONFLICT (guild_id)
      DO UPDATE SET
        is_awesome = EXCLUDED.is_awesome;"""

        await ctx.db.execute(query, ctx.guild.id)
        await ctx.send('ur dumb')

    @awesome.command(name='toggle')
    async def awesome_toggle(self, ctx):
        """TOGGLE that awesome status!"""
        # we're just going to see what the current state is, then call the
        # appropriate function so we don't have to deal with non-registered
        # guilds
        query = """
    SELECT is_awesome
    FROM fun_config
    WHERE guild_id = $1"""

        val = await ctx.db.fetchval(query, ctx.guild.id)

        if val:
            await ctx.invoke(self.awesome_off)
        else:
            await ctx.invoke(self.awesome_on)

    @commands.command(hidden=True, aliases=['nick', 'name'])
    @tor_only()
    async def display_name(self, ctx, *, user: commands.MemberConverter = None):
        """Made for fastfinge with <3"""
        user = ctx.author if not user else user
        await ctx.send(
            f'{user.name}\'s display name is {user.display_name}.'
        )

    @commands.command()
    async def choose(self, ctx, *choices: commands.clean_content):
        """Pick a random item from user input.

        For multiple items with multiple words, use double quotes."""

        if len(choices) < 2:
            # noinspection SpellCheckingInspection
            await ctx.send('You need at least two choices plskthx')
            return

        await ctx.send(
            f'Out of {", ".join(choices[:-1])}, and {choices[-1]}; I choose '
            f'{random.choice(choices)}.'
        )

    @commands.command()
    async def warn(self, ctx, member: commands.MemberConverter, *, _=None):
        """Meme warn. Doesn't actually do anything."""
        member = ctx.author if not member else member
        await ctx.send(
            f'<:tickYes:404815005423501313> **_'
            f'{member.name}#{member.discriminator} has been warned._**'
        )

    # It's a converter, not a type annotation in this case
    # noinspection PyTypeChecker
    @commands.command()
    async def discrim(self, ctx, discriminator: Discriminator,
                      *, selector: Selector = '='):
        """Search for specific discriminators.

        Optional parameter for ranges to be searched.

        It can be >, >=, <=, or <.

        Ranges between two numbers hasn't been implemented yet."""
        if selector == '>':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) > discriminator
            ])
        elif selector == '<':
            p = Pages(ctx, entries=[
                'f{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) < discriminator
            ])
        elif selector == '>=':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) >= discriminator
            ])
        elif selector == '<=':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) <= discriminator
            ])
        elif selector == '=':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) == discriminator
            ])
        else:
            raise commands.BadArgument('Could not parse arguments')

        if not p.entries:
            return await ctx.send('No results found.')

        await p.paginate()


def setup(bot):
    bot.add_cog(Fun(bot))
