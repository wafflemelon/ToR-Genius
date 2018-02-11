from datetime import datetime

import discord
import humanize
from discord.ext import commands

from cogs.utils.paginator import Pages

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
    async def permissions(self, ctx, member: commands.MemberConverter = None,
                          channel: commands.TextChannelConverter = None,
                          *, query: str.lower = ''):
        """Get the permissions of a member in a certain channel"""
        channel = channel or ctx.channel
        user = member or ctx.author

        perms = user.permissions_in(channel)

        desc = []

        # I'm sorry
        desc.extend(
            f'**{p.replace("_", " ").title()}**: {"Yes" if v else "No"}'
            for p, v in perms
            if query in p.lower().replace("_", " ")
            or query in ("Yes" if v else "No")
        )

        if not desc:
            return await ctx.send('No results found.')

        e = discord.Embed(
            description='\n'.join(desc),
            color=user.color,
            title=f'Permissions for {user.display_name}'
        )

        await ctx.send(embed=e)

    # noinspection PyUnresolvedReferences
    @commands.command()
    async def joined(self, ctx, member: commands.MemberConverter = None):
        """Find out concisely when a member joined."""
        member = member or ctx.author
        await ctx.send(f'{member.display_name} joined '
                       f'{format_time(member.joined_at)}')

    @commands.command()
    async def emojis(self, ctx, *, query=''):
        """List the servers emojis without spamming."""
        entries = [f'{str(e)}, :{e.name}:, `{str(e)}`' for e in
                   ctx.guild.emojis if query in e.name]

        if not entries:
            return await ctx.send('No results found for query.')

        p = Pages(ctx, entries=entries)
        await p.paginate()


def setup(bot):
    bot.add_cog(Info(bot))
