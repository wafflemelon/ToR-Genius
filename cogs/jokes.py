import random

import aiohttp
from discord.ext import commands

# noinspection SpellCheckingInspection
opf_list = [
    "Sent from AOL Mobile Mail",
    "John had surgery Friday and he's with the lord now.",
    "Lovely pics as alway, Janice. I have terminal brain cancer.",
    "DISCUSTING",
    "I DID NOT POST THAT! SOMEONE HAS HACKED MY ACCOUNT",
    "LOVE ETHYL",
    "All kittens are dead.",
    "Just got back from the doctor. I have Ebola. See you at church on Sunday!",
    "1.	Preheat oven to 350 degrees F (175 degrees C).2.	Stir cream cheese, milk, butter, and garlic salt together in a saucepan over low heat. Cook, stirring frequently, until the cheese has melted completely and the sauce is smooth, about 5 minutes. Stir corn, green chilies, and jalapeno peppers into the sauce. Pour corn mixture into a baking dish. 3.	Bake in preheated oven for 30 minutes.",
    "ADULT ONLY",
    "Are you my grandson?",
    "http://m.facebook.com",
    "Going to have tornadoes tomorrow.",
    "WISH GOD WOULD TAKE ME.",
    "YOU SURE ARE A LONG BABY",
    "covfefe",
    "REFURBISHD +OK?"
]


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

    @commands.command(aliases=['opf'])
    async def oldpeoplefacebook(self, ctx, query: str.lower = ''):
        final_list = [x for x in opf_list if query in x.lower()]
        if not final_list:
            return await ctx.send('No results found.')
        await ctx.send(
            random.choice(final_list)
        )


def setup(bot):
    bot.add_cog(Jokes(bot))
