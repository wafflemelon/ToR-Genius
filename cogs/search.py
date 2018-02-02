import itertools

import aiohttp
import discord
import wikipedia
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
        """Do a full wolframalpha query, with a very verbose response."""
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
        """Do a quick wolframalpha query, with a short response"""
        await ctx.channel.trigger_typing()
        with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://api.wolframalpha.com/v2/result',
                    params={'i': query, 'appid': config.wolfram}
            ) as res:
                text = await res.text()
                await ctx.send(text)

    @commands.command(aliases=['wiki'])
    async def wikipedia(self, ctx, *, query: str):
        """Search wikipedia for a page"""
        await ctx.channel.trigger_typing()
        pages = wikipedia.search(query)
        page = wikipedia.page(pages[0])
        # space after colon because Discord sucks
        response = f'From <{page.url}>:\n\n'
        response += (page.summary[:1750] + "...") \
            if len(page.summary) > 1750 else page.summary

        if len(pages) > 1:
            response += f'\n\nOther possibilities:\n'
            other_results = pages[1:min(len(pages), 3)]
            for resp in other_results:
                response += \
                    f'**{resp}**: {wikipedia.summary(resp, sentences=1)}\n'

        try:
            await ctx.send(response)
        except discord.HTTPException:
            await ctx.send(page.url)

    # noinspection SpellCheckingInspection
    @commands.command(aliases=['ddg', 'duck', 'google', 'goog'])
    async def duckduckgo(self, ctx, *, query: str):
        """Search the DuckDuckGo IA API"""
        await ctx.channel.trigger_typing()
        with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://api.duckduckgo.com',
                    params={'q': query, 't': 'ToR Genius Discord Bot',
                            'format': 'json', 'no_html': '1'}
            ) as res:
                resp_json = await res.json(
                    content_type='application/x-javascript'
                )
                embeds = {}

                if resp_json['AbstractURL'] != '':
                    embeds[f'Abstract: {resp_json["Heading"]}'
                           f' ({resp_json["AbstractSource"]})'] = {
                        'image': resp_json['Image'],
                        'desc': f'{resp_json.get("AbstractText", "")}\n\n'
                                f'{resp_json["AbstractURL"]}'
                    }

                if resp_json['Definition'] != '':
                    embeds['Definition'] = {
                        'desc': f'{resp_json["Definition"]}\n'
                                f'([{resp_json["DefinitionSource"]}]'
                                f'({resp_json["DefinitionURL"]}))'
                    }

                if resp_json['RelatedTopics']:
                    desc = []
                    for topic in resp_json['RelatedTopics']:
                        try:
                            if len('\n'.join(desc)) > 1000:
                                break
                            desc.append(
                                f'[**{topic["Text"]}**]({topic["FirstURL"]})'
                            )
                        except KeyError:
                            # some weird subtopic thing I guess
                            continue

                    embeds['Related'] = {
                        'desc': '\n'.join(desc),
                        'image': resp_json['RelatedTopics'][0]['Icon']['URL']
                    }

                if resp_json['Results']:
                    desc = []
                    for result in resp_json['Results']:
                        desc.append(
                            f'[**{result["Text"]}**]({result["FirstURL"]})'
                        )
                    embeds['Top Results'] = {
                        'desc': '\n'.join(desc),
                        'image': resp_json['Results'][0]['Icon']['URL']
                    }

                final_embeds = []

                for embed_title, embed_content in embeds.items():
                    final_embeds.append(
                        discord.Embed(
                            title=embed_title,
                            description=embed_content['desc'],
                            color=ctx.author.color
                        ).set_image(
                            url=embed_content['image']
                        ).set_thumbnail(
                            url='https://i.imgur.com/CVogaGL.png'
                        )
                    )

                p = EmbedPages(ctx, embeds=final_embeds)
                await p.paginate()


def setup(bot):
    bot.add_cog(Search(bot))
