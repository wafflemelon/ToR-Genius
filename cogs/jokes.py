import random

import aiohttp
from discord.ext import commands


# noinspection SpellCheckingInspection
class Jokes:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['git', 'gjoke', 'gitjoke'])
    async def git_jokes(self, ctx, query=None):
        """Get a random joke about git"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            async with s.get('https://raw.githubusercontent.com/EugeneKay/'
                             'git-jokes/lulz/Jokes.txt') as res:
                content = await res.text()
                jokes = content.splitlines()
                if not query:
                    return await ctx.send(random.choice(jokes))
                try:
                    return await ctx.send(jokes[int(query) - 1])
                except (IndexError, ValueError):
                    # shuffle in case it's a short search so you don't
                    # always get the same results
                    random.shuffle(jokes)
                    result = None
                    for joke in jokes:
                        if query.lower() in joke.lower():
                            result = joke

                    if result is None:
                        return await ctx.send('No results found.')
                    else:
                        await ctx.send(result)

    @commands.command(aliases=['djoke', 'dad', 'dadjoke'])
    async def dad_jokes(self, ctx):
        """Get a random dad joke"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://icanhazdadjoke.com/',
                    headers={'Accept': 'text/plain'}
            ) as res:
                joke = await res.text()
                await ctx.send(joke)

    @commands.command(aliases=['cnorris', 'chuck', 'cjoke'])
    async def chuck_norris_jokes(self, ctx, query=None):
        """Get a random chuck norris joke, with an optional search"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            if not query:
                async with s.get(
                        'https://api.chucknorris.io/jokes/random'
                ) as res:
                    joke = await res.json()
                    await ctx.send(joke['value'])

            else:
                async with s.get(
                        'https://api.chucknorris.io/jokes/search',
                        params={'query': query}
                ) as res:
                    jokes = await res.json()
                    jokes = jokes['result']
                    if not jokes:
                        return await ctx.send('No results found')
                    response = [j['value'] for j in jokes][:5]
                    await ctx.send('\n\n'.join(response))

    @commands.command(aliases=['yo', 'mamma', 'mom'])
    async def yo_mamma(self, ctx):
        """Yo mom jokes"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            async with s.get(
                    'http://api.yomomma.info'
            ) as res:
                text = await res.json(content_type='text/html')
                text = text['joke']
                await ctx.send(text)


def setup(bot):
    bot.add_cog(Jokes(bot))
