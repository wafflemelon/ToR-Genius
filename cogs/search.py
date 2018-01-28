import itertools

import aiohttp
import discord
import wolframalpha
from discord.ext import commands
from texttable import Texttable, ArraySizeError

import config
from cogs.admin import haste_upload
from cogs.utils.paginator import EmbedPages


def code_block(string, lang=''):
    if string.strip() == '':
        return ''
    return f'```{lang}\n{string}\n```'


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

        t = Texttable()
        data = []
        images = []
        for pod in res.pods:
            sub_data = []
            for sub in pod.subpods:
                if sub.plaintext:
                    sub_data.append(sub.plaintext)
                if hasattr(sub, 'img'):
                    images.append(sub['img']['@src'])
                    # sub_data.append(sub['img']['@alt'])
            data.append(sub_data)

        embed_images = [
            discord.Embed().set_image(url=image) for image in images
        ]

        try:
            t.add_rows(data)
        except ArraySizeError:
            # to_send = code_block('\n\n'.join([s.text for s in res.results]))
            to_send = code_block('\n\n'.join(
                itertools.chain.from_iterable(
                    data
                )
            ))
            if to_send != '':
                try:
                    await ctx.send(to_send)
                except discord.HTTPException:
                    key = await haste_upload(to_send + '\n' + '\n'.join(images))
                    await ctx.send(f'https://hastebin.com/{key}')
            if embed_images:
                p = EmbedPages(ctx, embeds=embed_images)
                await p.paginate()
            return

        try:
            await ctx.send(code_block(t.draw()))
        except discord.HTTPException:
            key = await haste_upload(code_block(t.draw()))
            await ctx.send(f'https://hastebin.com/{key}')
        if embed_images:
            p = EmbedPages(ctx, embeds=embed_images)
            await p.paginate()

    @commands.command()
    async def quick(self, ctx, *, query):
        await ctx.channel.trigger_typing()
        with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://api.wolframalpha.com/v2/result',
                    params={'i': query, 'appid': config.wolfram}
            ) as res:
                text = await res.text()
                await ctx.send(text)

def setup(bot):
    bot.add_cog(Search(bot))
