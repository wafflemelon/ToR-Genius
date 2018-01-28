from datetime import datetime

import discord
import humanize
from discord.ext import commands

# following is from
# https://github.com/khazhyk/dango.py/blob/master/plugins/info.py
# Discord epoch
UNKNOWN_CUTOFF = datetime.utcfromtimestamp(1420070400.000)


def format_time(time):
    if time is None or time < UNKNOWN_CUTOFF:
        return "Unknown"
    return "{} ({} UTC)".format(
        humanize.naturaltime(time + (datetime.now() - datetime.utcnow())), time)


class Info:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, err):
        if isinstance(err, commands.BadArgument):
            await ctx.send(err)

    @commands.command(aliases=['perms'])
    async def permissions(self, ctx, member: commands.MemberConverter = None, *,
                          channel: commands.TextChannelConverter = None):
        channel = ctx.channel if not channel else channel
        user = ctx.author if not member else member

        perms = user.permissions_in(channel)

        desc = []

        for p, v in perms:
            desc.append(f'**{p}**: {v}')

        e = discord.Embed(
            description='\n'.join(desc),
            color=user.top_role.color,
            title=f'Permissions for {user.display_name}'
        )

        await ctx.send(embed=e)

    # noinspection PyUnresolvedReferences
    @commands.command()
    async def joined(self, ctx, member: commands.MemberConverter=None):
        member = member or ctx.author
        await ctx.send(f'{member.display_name} joined  '
                       f'{format_time(member.joined_at)}')


def setup(bot):
    bot.add_cog(Info(bot))
