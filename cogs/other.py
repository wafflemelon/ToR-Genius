import aiohttp
from discord.ext import commands

from cogs.utils.paginator import Pages


class Other:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def forum(self, ctx, *, search):
        """Search the Swift Discourse Forum for anything."""
        with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://forums.swift.org/search/query.json',
                    params={'term': search}
            ) as r:
                r = await r.json()

                if r['grouped_search_result'] is None:
                    return await ctx.send('No results found.')

                data = []

                data.extend([f'p/{i}'
                             for i in r['grouped_search_result']['post_ids']])
                data.extend([f'u/{i}'
                             for i in r['grouped_search_result']['user_ids']])
                data.extend([f'c/{i}'
                             for i in r['grouped_search_result']['category_ids']
                             ])
                data.extend([f't/{i}'
                             for i in r['grouped_search_result']['tag_ids']])

                if not data:
                    return await ctx.send('No results found.')

                p = Pages(
                    ctx,
                    entries=[f'[{d}](https://forums.swift.org/{d})'
                             for d in data]
                )

                await p.paginate()


def setup(bot):
    bot.add_cog(Other(bot))
