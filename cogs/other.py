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

                # I'm sorry. (Ok not as bad now)

                # idk why, but topics seems to disappear sometimes
                data.extend([(f't/{t["id"]}', t['title'])
                             for t in r.get('topics', [])])

                data.extend([(f'u/{u["username"]}',
                              f'{u["username"]} ({u["name"]})')
                             for u in r['users']])

                data.extend([(f'c/{c.id}', c['name'])
                             for c in r['categories']])

                data.extend([(f'tags/{t["name"]}', t['name'])
                             for t in r['tags']])

                data.extend([(f'p/{p["id"]}', p['blurb'])
                             for p in r['posts']])

                if not data:
                    return await ctx.send('No results found.')

                p = Pages(
                    ctx,
                    entries=[f'[{d[1]}](https://forums.swift.org/{d[0]})'
                             for d in data]
                )

                await p.paginate()


def setup(bot):
    bot.add_cog(Other(bot))
