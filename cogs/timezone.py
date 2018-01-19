import re
from datetime import datetime

import pytz
from dateutil import tz
from discord.ext import commands

from cogs.utils import db
from cogs.utils.paginator import Pages


class TimezoneDB(db.Table, table_name='timezones'):
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    timezone = db.Column(db.String)


class TimezoneConverter(commands.Converter):

    async def convert(self, ctx, argument):
        if argument not in pytz.all_timezones:
            raise commands.BadArgument('Could not parse timezone')
        else:
            return argument


class TimezoneMember:

    @classmethod
    async def create(cls, ctx, member):
        self = TimezoneMember()

        query = """
SELECT timezone
FROM timezones
WHERE user_id = $1;
        """

        result = await ctx.db.fetchval(query, member.id)
        if result is None:
            raise LookupError()

        self.timezone = result
        self.user = member
        return self


def _get_from_guilds(bot, getter, argument):
    result = None
    for guild in bot.guilds:
        result = getattr(guild, getter)(argument)
        if result:
            return result
    return result


class TimezoneMemberConverter(commands.IDConverter):
    async def convert(self, ctx, argument):

        message = ctx.message
        bot = ctx.bot
        match = self._get_id_match(argument) \
                or re.match(
            r'<@!?([0-9]+)>$',
            argument
        )

        guild = message.guild
        if match is None:
            # not a mention...
            if guild:
                member = guild.get_member_named(argument)
            else:
                member = _get_from_guilds(bot, 'get_member_named', argument)
        else:
            user_id = int(match.group(1))
            if guild:
                member = guild.get_member(user_id)
            else:
                member = _get_from_guilds(bot, 'get_member', user_id)

        if member is None:
            raise commands.BadArgument(f'Member "{argument}" not found')

        try:
            timezone_member = await TimezoneMember.create(ctx, member)
        except LookupError:
            raise commands.BadArgument(f'No timezone set up for '
                                       f'{member.display_name}. They can create'
                                       f' one with `{ctx.prefix}timezone set '
                                       f'<timezone>username>`')
        else:
            return timezone_member


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
                                  f'timezone set <timezone>`')

        timezone = tz.gettz(result)
        formatter = datetime.now(tz=timezone)
        await ctx.send(f'Your time is: '
                       f'{formatter.strftime("%a %b %d %I:%M %p %Y, %Z")}.')

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

    @timezone.command()
    async def get(self, ctx, *, member: TimezoneMemberConverter = None):
        """Get the timezone of a user. If not specified, it's yourself."""

        member = await TimezoneMember.create(ctx, ctx.author) \
            if not member else member

        timezone = tz.gettz(member.timezone)
        formatter = datetime.now(tz=timezone)
        await ctx.send(
            f'{member.user.display_name}\'s time is:'
            f' {formatter.strftime("%a %b %d %I:%M %p %Y, %Z")}.'
        )

    @timezone.command()
    async def list(self, ctx, search: str = ''):
        """List all possible timezones, with an optional search string"""

        entries = [t for t in pytz.all_timezones if search in t.lower()]
        p = Pages(ctx, entries=entries)
        await p.paginate()


def setup(bot):
    bot.add_cog(Timezones(bot))
