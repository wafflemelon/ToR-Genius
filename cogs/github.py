import discord
import requests
from discord.ext import commands

import config
from cogs.utils.paginator import Pages


class Github:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tor_repo(self, ctx, *, search: str = None):
        """Search for a ToR related github repo. Search string can be "all"."""
        if not search:
            await ctx.send(
                embed=discord.Embed(
                    description=
                    '[GrafeasGroup](https://github.com/GrafeasGroup)'
                )
            )

            return

        graphql_query = """
query {
    organization(login: "GrafeasGroup") {
        repositories(last: 100) {
            edges {
                node {
                    resourcePath
                }
            }
        }
    }
}

 """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + config.github_token,
            'Accept': 'application/json'
        }

        r = requests.post(
            'https://api.github.com/graphql',
            headers=headers,
            json={'query': graphql_query}
        )
        repos = ['/perryprog/tor-genius']
        repos.extend([
            item['node']['resourcePath']
            for item in r.json()['data']['organization']
            ['repositories']['edges']
        ])

        if search.lower() == 'all':
            p = Pages(
                ctx,
                entries=[
                    f'[{re[1:]}](https://github.com{re})' for re in repos
                ]
            )

            await p.paginate()
            return

        results = []

        for re in repos:
            if search in re:
                results.append(f'[{re[1:]}](https://github.com{re})')

        if not results:
            await ctx.send('No results found.')
            return

        p = Pages(ctx, entries=results)
        await p.paginate()


def setup(bot):
    bot.add_cog(Github(bot))
