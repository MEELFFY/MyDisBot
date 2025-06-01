import os
import discord
from discord.ext import commands
from keep_alive import keep_alive
from dotenv import load_dotenv

import discord
from discord.ext import commands
import datetime

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.command(name='активність')
async def create_activity(ctx, *, args):
    try:
        name, description, date_str = [part.strip() for part in args.split('|')]
        event_time = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        time_diff = event_time - datetime.datetime.now()
        unix_timestamp = int(event_time.timestamp())

        embed = discord.Embed(
            title=name,
            description=f"{description}\n\n📅 Дата: <t:{unix_timestamp}:f> (<t:{unix_timestamp}:R>)",
            color=0x00ff00
        )
        embed.add_field(name="👍🏻 Так", value="—", inline=True)
        embed.add_field(name="❓ Можливо", value="—", inline=True)
        embed.add_field(name="👎🏻 Ні", value="—", inline=True)

        message = await ctx.send(embed=embed)
        await message.add_reaction("👍🏻")
        await message.add_reaction("❓")
        await message.add_reaction("👎🏻")

        activity_data[message.id] = {"👍🏻": [], "❓": [], "👎🏻": []}

    except ValueError:
        await ctx.send("❌ Неправильний формат. Використай:\n`!активність Назва | Опис | 2025-06-01 22:22`")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message = reaction.message
    if message.id not in activity_data:
        return

    for emoji in ["👍🏻", "❓", "👎🏻"]:
        if user in activity_data[message.id][emoji]:
            return  # Користувач уже проголосував

    if str(reaction.emoji) in activity_data[message.id]:
        # Видаляємо попередню реакцію
        for emoji, users in activity_data[message.id].items():
            if user in users:
                users.remove(user)
        # Додаємо нову
        activity_data[message.id][str(reaction.emoji)].append(user)

        await update_activity_embed(message, activity_data[message.id])

async def update_activity_embed(message, data):
    embed = message.embeds[0]
    for i, emoji in enumerate(["👍🏻", "❓", "👎🏻"]):
        users = data[emoji]
        mentions = "—" if not users else '\n'.join(user.mention for user in users)
        embed.set_field_at(i, name=emoji, value=mentions, inline=True)
    await message.edit(embed=embed)
    
    twin_list = [f"Твін {i}" for i in range(1, 10)]
twin_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
special_emojis = ["❌", "🔁"]
twin_data = {}

@bot.command(name='твіни')
async def show_twins(ctx):
    embed = discord.Embed(title="Вибери свого Твіна", color=0x3498db)
    for i, name in enumerate(twin_list):
        embed.add_field(name=f"{twin_emojis[i]} {name}", value="—", inline=False)

    msg = await ctx.send(embed=embed)
    for emoji in twin_emojis + special_emojis:
        await msg.add_reaction(emoji)

    twin_data[msg.id] = {}

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    msg = reaction.message
    if msg.id not in twin_data:
        return

    emoji = str(reaction.emoji)

    if emoji == "🔁":
        twin_data[msg.id] = {}
        await update_twin_embed(msg, twin_data[msg.id])
        return

    if emoji == "❌":
        for k, v in twin_data[msg.id].items():
            if v == user:
                twin_data[msg.id][k] = None
        await update_twin_embed(msg, twin_data[msg.id])
        return

    if emoji in twin_emojis:
        twin_index = twin_emojis.index(emoji)

        # Видаляємо попередній вибір користувача
        for key, value in twin_data[msg.id].items():
            if value == user:
                twin_data[msg.id][key] = None

        # Якщо цей твіна вже обрав хтось інший — не даємо перезаписати
        if twin_index in twin_data[msg.id] and twin_data[msg.id][twin_index] is not None:
            return

        twin_data[msg.id][twin_index] = user
        await update_twin_embed(msg, twin_data[msg.id])

async def update_twin_embed(msg, data):
    embed = discord.Embed(title="Вибери свого Твіна", color=0x3498db)
    for i, name in enumerate(twin_list):
        user = data.get(i)
        display = f" — {user.mention}" if user else "—"
        embed.add_field(name=f"{twin_emojis[i]} {name}", value=display, inline=False)
    await msg.edit(embed=embed)
    
    @bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Видалено {amount} повідомлень.", delete_after=5)

import os
from dotenv import load_dotenv
load_dotenv()

activity_data = {}  # Для активностей
# twin_data = {} — уже є вище

bot.run(os.getenv("DISCORD_TOKEN"))