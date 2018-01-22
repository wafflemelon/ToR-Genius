import discord
from discord.ext import commands


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


def setup(bot):
    bot.add_cog(Info(bot))
