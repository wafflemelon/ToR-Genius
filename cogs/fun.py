# Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT


import logging

from discord.ext import commands

log = logging.getLogger(__name__)


# class FunConfig(db.Table, table_name='fun_config'):
#     guild_id = db.Column(db.Integer(big=True), primary_key=True)
#     is_awesome = db.Column(db.Boolean, default=False)


class Fun:
    """How much fun can a fun fun have if a fun fun could have fun?"""

    def __init__(self, bot):
        self.bot = bot

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
    async def display_name(self, ctx, *, user: commands.MemberConverter = None):
        """Made for fastfinge with <3"""
        user = ctx.author if not user else user
        await ctx.send(
            f'{user.name}\'s display name is {user.display_name}.'
        )


def setup(bot):
    bot.add_cog(Fun(bot))
