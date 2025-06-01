import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from keep_alive import keep_alive

TOKEN = "TOKEN"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

twins_mention_message = None
activity_messages = {}

@bot.event
async def on_ready():
    print(f"✅ Бот запущено як {bot.user}")

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Очищено {amount} повідомлень.", delete_after=5)

@bot.command(name="твіни")
async def twins(ctx):
    global twins_mention_message
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "❌", "🔁"]
    twin_names = [f"Твін {i+1}" for i in range(9)]
    twin_users = [None] * 9

    embed = discord.Embed(title="Вибір твінів", color=discord.Color.green())
    for name in twin_names:
        embed.add_field(name=name, value="‎", inline=False)

    msg = await ctx.send(embed=embed)
    for emoji in emojis:
        await msg.add_reaction(emoji)

    if twins_mention_message:
        try:
            await twins_mention_message.delete()
        except:
            pass
    twins_mention_message = await ctx.send("@Zero Tolerance оберіть твіна")
    await asyncio.sleep(14400)
    await twins_mention_message.delete()

    def check(reaction, user):
        return user != bot.user and reaction.message.id == msg.id

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=14400.0, check=check)
            emoji = reaction.emoji

            if emoji in emojis[:9]:
                idx = emojis.index(emoji)
                if twin_users[idx] and twin_users[idx] != user:
                    await msg.remove_reaction(reaction, user)
                    continue

                for i, u in enumerate(twin_users):
                    if u == user:
                        twin_users[i] = None
                        await msg.remove_reaction(emojis[i], user)

                twin_users[idx] = user

            elif emoji == "❌":
                for i, u in enumerate(twin_users):
                    if u == user:
                        twin_users[i] = None
                        await msg.remove_reaction(emojis[i], user)

            elif emoji == "🔁":
                if twins_mention_message:
                    try:
                        await twins_mention_message.delete()
                    except:
                        pass
                twins_mention_message = await ctx.send("@Zero Tolerance оберіть твіна (оновлено)")
                await asyncio.sleep(14400)
                await twins_mention_message.delete()
                twin_users = [None] * 9
                for emoji in emojis[:9]:
                    await msg.clear_reaction(emoji)
                    await msg.add_reaction(emoji)

            new_embed = discord.Embed(title="Вибір твінів", color=discord.Color.green())
            for i, name in enumerate(twin_names):
                if twin_users[i]:
                    new_embed.add_field(name=name, value=twin_users[i].mention, inline=False)
                else:
                    new_embed.add_field(name=name, value="‎", inline=False)
            await msg.edit(embed=new_embed)

        except asyncio.TimeoutError:
            break

@bot.command(name="активність")
async def activity(ctx, *, content):
    try:
        title, description, time_str = map(str.strip, content.split("|"))
        event_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        timestamp = int(event_time.timestamp())

        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        embed.add_field(name="Час", value=f"<t:{timestamp}:F> (<t:{timestamp}:R>)", inline=False)
        embed.add_field(name="👍🏻", value="‎", inline=True)
        embed.add_field(name="❓", value="‎", inline=True)
        embed.add_field(name="👎🏻", value="‎", inline=True)

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍🏻")
        await msg.add_reaction("❓")
        await msg.add_reaction("👎🏻")
        mention_msg = await ctx.send("@Zero Tolerance подія створена")

        participants = {"👍🏻": [], "❓": [], "👎🏻": []}

        def check(reaction, user):
            return user != bot.user and reaction.message.id == msg.id

        while True:
            reaction, user = await bot.wait_for("reaction_add", timeout=7200, check=check)
            for emoji in participants:
                if user in participants[emoji]:
                    participants[emoji].remove(user)
            if str(reaction.emoji) in participants:
                participants[str(reaction.emoji)].append(user)

            new_embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
            new_embed.add_field(name="Час", value=f"<t:{timestamp}:F> (<t:{timestamp}:R>)", inline=False)
            for emoji in ["👍🏻", "❓", "👎🏻"]:
                users = participants[emoji]
                names = ", ".join(user.mention for user in users) if users else "‎"
                new_embed.add_field(name=emoji, value=names, inline=True)
            await msg.edit(embed=new_embed)

    except ValueError:
        await ctx.send("⚠️ Формат: `!активність Назва | Опис | 2025-06-02 18:00`")

keep_alive()
bot.run("TOKEN")