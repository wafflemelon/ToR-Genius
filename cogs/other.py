import io
import re
from math import floor

import aiohttp
import discord
from PIL import Image, ImageFont, ImageDraw
from discord.ext import commands

from cogs.utils.paginator import Pages


async def download(url):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as r:
            return io.BytesIO(await r.read())


class LinkOrAvatar(commands.Converter):
    special_cases = {
        'itsthejoker': 'https://avatars0.githubusercontent.com/u/5179553'
    }

    async def convert(self, ctx, argument):
        try:
            possible_member = await commands.MemberConverter() \
                .convert(ctx, argument)
            if possible_member.name not in self.special_cases:
                url = possible_member.avatar_url_as(format='png')
                url = url.replace('gif', 'png').strip('<>')
            else:
                url = self.special_cases[possible_member.name]

            img = await download(url)

            img = Image.open(img)

            return img.convert('RGBA'), possible_member.name
        except commands.BadArgument:
            pass

        # from https://stackoverflow.com/questions/169625/
        # regex-to-check-if-valid-url-that-ends-in-jpg-png-or-gif
        # (Sorry about breaking the URL)

        # will add more image formats as time goes on
        regex = r'<?(?:([^:/?#]+):)?(?://([^/?#]*))?([^?#]*\.' \
                r'(?:jpg|png|jpeg))(?:\?([^#]*))?(?:#(.*))?>?'

        regex = re.compile(regex, re.IGNORECASE)

        if re.fullmatch(regex, argument.split(' ')[0]):
            img = await download(argument.split(' ')[0].strip('<>'))

            img = Image.open(img)

            text = ' '.join(argument.split(' ')[1:])
            if not text:
                raise commands.BadArgument('No text supplied for image')
            return img.convert('RGBA'), text
        else:
            raise commands.BadArgument(
                "That URL doesn't seem to lead to a valid image"
                # if possible_member else "I couldn't find that user"
            )


class Other:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, err):
        if isinstance(err, commands.BadArgument):
            await ctx.send(err)

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

    # noinspection PyUnresolvedReferences,PyPep8Naming
    @commands.command()
    async def blame(self, ctx, *, img: LinkOrAvatar = None):
        """Blame everyone! Defaults to perryprog.

        Will also accept image urls ending in jpg, png, and jpeg."""
        # hardcoded because I want to be blamed even in forks ;)
        img, name = img or await LinkOrAvatar() \
            .convert(ctx, '280001404020588544')
        # special cases for usernames
        special_cases = {
            'perryprog': 'perry',
            'itsthejoker': 'joker'
        }

        # :no_entry: emoji
        emoji = 'https://emojipedia-us.s3.amazonaws.com/thumbs/240/twitter/' \
                '120/no-entry-sign_1f6ab.png'
        emoji = await download(emoji)
        emoji = Image.open(emoji)
        emoji = emoji.convert('RGBA')

        # make the image 3 times larger than the avatar
        large_image = Image.new('RGBA', [3 * x for x in img.size], (0,) * 4)
        lW, lH = large_image.size
        W, H = img.size
        # the center box for the avatar
        box = (W, H, W * 2, H * 2)

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

        name = special_cases.get(
            name,
            re.sub(r'\W', '', name).lower()
        )

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

    # noinspection PyPep8Naming
    @commands.command(aliases=['floor'])
    async def the_floor(self, ctx, img: LinkOrAvatar, *, what):
        """Generate a the floor is lava meme."""

        if len(what) > 23:
            return await ctx.send("The floor isn't that long. (max 29 chars)")

        img, name = img

        meme_format = Image.open('floor.png')

        # == Text ==
        fnt = ImageFont.truetype('Arial.ttf', 50)
        d = ImageDraw.Draw(meme_format)

        d.text(
            (20, 30),
            f'The floor is {what}',
            font=fnt,
            fill=(0,) * 4
        )

        # == Avatars ==
        first = img.resize((20, 20))
        second = img.resize((40, 40))

        meme_format.paste(first, (140, 137))
        meme_format.paste(second, (460, 137))

        # == Sending ==
        bio = io.BytesIO()
        meme_format.save(bio, 'PNG')
        bio.seek(0)
        await ctx.send(file=discord.File(bio, filename='floor.png'))


def setup(bot):
    bot.add_cog(Other(bot))
