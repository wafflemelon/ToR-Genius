import io
import re
from math import floor

import aiohttp
import discord
from PIL import Image, ImageFont, ImageDraw
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

    @staticmethod
    async def download(url):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as r:
                return io.BytesIO(await r.read())

    # noinspection PyUnresolvedReferences,PyPep8Naming
    @commands.command()
    async def blame(self, ctx, *, member: commands.MemberConverter = None):
        """Blame everyone! Defaults to perryprog."""
        # hardcoded because I want to be blamed even in forks ;)
        member = member or self.bot.get_user(280001404020588544)
        if not member:
            return await ctx.send("No user specified, and owner couldn't "
                                  "be found")

        # special cases for usernames and avatars for people with
        # default avatars
        special_cases = {
            'names': {
                'perryprog': 'perry',
                'itsthejoker': 'joker'
            },
            'avatars': {
                'itsthejoker': 'https://avatars0.githubusercontent.com'
                               '/u/5179553'
            }
        }

        # :no_entry: emoji
        emoji = 'https://emojipedia-us.s3.amazonaws.com/thumbs/240/twitter/' \
                '120/no-entry-sign_1f6ab.png'
        emoji = await self.download(emoji)
        emoji = Image.open(emoji)
        emoji = emoji.convert('RGBA')

        if member.name not in special_cases['avatars']:
            url = member.avatar_url_as(format='png')
            url = url.replace('gif', 'png').strip('<>')
        else:
            url = special_cases['avatars'][member.name]

        img = await self.download(url)

        img = Image.open(img)
        img = img.convert('RGBA')

        # make the image 3 times larger than the avatar
        large_image = Image.new('RGBA', [3 * x for x in img.size], (0,)*4)
        lW, lH = large_image.size
        W, H = img.size
        # the center box for the avatar
        box = (W, W, W * 2, W * 2)

        # make the emoji 20% bigger than the avatar
        emoji = emoji.resize([floor(x * 1.2) for x in img.size])
        eW, eH = emoji.size

        large_image.paste(img.copy(), box)
        large_image.paste(
            emoji,

            (  # center the emoji
                floor((lW - eW) / 2),

                floor((lH - eH) / 2)
            ),

            emoji
        )

        # make the font size relative to the avatar size
        fnt = ImageFont.truetype('Arial.ttf', floor(img.size[0] / 4))
        d = ImageDraw.Draw(large_image)

        if member.name not in special_cases['names'].keys():
            name = re.sub(r'\W', '', member.name).lower()
        else:
            name = special_cases['names'][member.name]

        message = f'#blame{name}'
        tW, tH = d.textsize(message, fnt)

        d.text(
            (  # center the text
                floor((lW - tW) / 2),
                # make the text somewhat centered (a bit offset so it
                # looks good) in the first "row"
                floor(H / 2) - floor(W / 4)
            ),
            message,
            font=fnt,
            fill=(255,) * 4
        )

        bio = io.BytesIO()
        large_image.save(bio, 'PNG')
        bio.seek(0)
        await ctx.send(file=discord.File(bio, filename='blame.png'))


def setup(bot):
    bot.add_cog(Other(bot))
