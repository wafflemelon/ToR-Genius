from datetime import datetime

import pytz
from dateutil import tz
from discord.ext import commands

from cogs.utils import db


class TimezoneDB(db.Table, table_name='timezones'):
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    timezone = db.Column(db.String)


class TimezoneConverter(commands.Converter):

    async def convert(self, ctx, argument):
        if argument not in pytz.all_timezones:
            raise commands.BadArgument('Could not parse timezone')
        else:
            return argument


class Timezones:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(invoke_without_command=True)
    async def timezone(self, ctx):
        """Get the timezone of other people and more!"""
        query = """
SELECT timezone
FROM timezones
WHERE user_id = $1;
                """

        result = await ctx.db.fetchval(query, ctx.author.id)
        if result is None:
            return await ctx.send(f'You haven\'t set up your timezone yet. '
                                  f'You can do this with `{ctx.prefix}'
                                  f'timezone set EST`')

        timezone = tz.gettz(result)
        formatter = datetime.now(tz=timezone)
        await ctx.send(f'Your time is: {formatter.strftime("%X, %Z")}.')

    @timezone.command()
    async def set(self, ctx, *, zone: TimezoneConverter):
        """Set your current timezone. Doesn't yet support UTC offsets."""
        query = """
INSERT INTO timezones (user_id, timezone) VALUES ($1, $2)
ON CONFLICT (user_id)
  DO UPDATE SET
    timezone = EXCLUDED.timezone;"""

        await ctx.db.execute(query, ctx.author.id, zone)
        await ctx.auto_react()


def setup(bot):
    bot.add_cog(Timezones(bot))
