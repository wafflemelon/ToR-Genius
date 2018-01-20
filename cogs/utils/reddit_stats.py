import discord

from cogs.utils.config import Config
from cogs.utils.strings import footer


async def get_flair_count(ctx, redditor, limit=None):
    buffer = Config('redditors.json')

    if redditor in buffer:
        return int(
            ctx.r.comment(buffer[redditor]).author_flair_text.split(" ")[0]
        )

    for comment in ctx.r.redditor(redditor).comments.new(limit=limit):
        if comment.subreddit == 'TranscribersOfReddit':
            await buffer.put(redditor, comment.id)
            return int(comment.author_flair_text.split(" ")[0])

    return None


def last_trans(ctx, redditor):
    u = ctx.r.redditor(redditor)
    comments = list(u.comments.new(limit=10))

    tr = [t for t in comments if footer in t.body]

    if len(tr) == 0:
        return "No transcription found."
    else:
        return tr[0].permalink


async def stats(ctx, redditor):
    u = ctx.r.redditor(redditor)
    comments = list(u.comments.new(limit=None))

    tr = [t for t in comments if footer in t.body]

    if len(tr) == 0:
        return discord.Embed(
            title=f"I see no Transcriptions from /u/{redditor}"
        )

    e = discord.Embed(
        title=f'Stats for /u/{redditor}',
    )

    f_c = await get_flair_count(ctx, redditor, 100)
    if f_c:
        e.add_field(name='Official Γ count', value=str(f_c))

    e.add_field(name='Number of comments (max. 1000)', value=str(len(comments)))

    e.add_field(name='Number of transcriptions', value=str(len(tr)))

    e.add_field(
        name='Total chars in transcriptions',
        value=str(sum([len(t.body) for t in tr]))
    )

    e.add_field(
        name='Chars per transcription',
        value=str(round(sum([len(t.body) for t in tr]) / len(tr), 2))
    )

    e.add_field(
        name='Total chars without footer',
        value=str(sum([len(t.body) - 280 for t in tr]))
    )

    e.add_field(
        name='Chars per Transcription without footer',
        value=str(round(sum([len(t.body) - 280 for t in tr]) / len(tr), 2))
    )

    e.add_field(
        name='Upvotes on transcriptions',
        value=str(sum([t.score for t in tr]))
    )

    e.add_field(
        name='Avg. Upvotes per transcription',
        value=str(round(sum([t.score for t in tr]) / len(tr), 2))
    )

    return e


def goodbad(ctx, redditor):
    u = ctx.r.redditor(redditor)
    comments = list(u.comments.new(limit=None))

    tr = [t for t in comments if footer in t.body]

    if len(tr) == 0:
        return discord.Embed(title="No transcriptions found.")

    good_bad_stats = {
        'good bot': 0,
        'bad bot': 0,
        'good human': 0,
        'bad human': 0
    }

    for t in tr:
        t.refresh()
        for r in t.replies:
            rep = r.body.lower()
            if "good bot" in rep:
                good_bad_stats['good bot'] += 1
            if "bad bot" in rep:
                good_bad_stats['bad bot'] += 1
            if "good human" in rep:
                good_bad_stats['good human'] += 1
            if "bad human" in rep:
                good_bad_stats['bad human'] += 1

    e = discord.Embed(
        title=f'Results for {redditor}'
    )

    e.add_field(name='Good bot', value=str(good_bad_stats['good bot']))
    e.add_field(name='Bad bot', value=str(good_bad_stats['bad bot']))
    e.add_field(name='Good human', value=str(good_bad_stats['good human']))
    e.add_field(name='Bad human', value=str(good_bad_stats['bad human']))

    return e
