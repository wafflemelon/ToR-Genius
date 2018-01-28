import wolframalpha
from discord.ext import commands

import config


class Search:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, err):
        if isinstance(err, commands.CommandOnCooldown):
            await ctx.send(err)

    @commands.command()
    @commands.cooldown(rate=1, per=20, type=commands.BucketType.user)
    async def wolfram(self, ctx, *, query: str):
        await ctx.channel.trigger_typing()

        client = wolframalpha.Client(config.wolfram)
        res = client.query(query)
        await ctx.send('_____________'.join([s.text for s in res.results]))


def setup(bot):
    bot.add_cog(Search(bot))
