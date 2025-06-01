import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- !clear команда ----------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ Очищено {amount} повідомлень.", delete_after=5)

# ---------- Активність ----------
reaction_options = ["👍🏻", "❓", "👎🏻"]

@bot.command()
async def активність(ctx, назва: str, *, опис: str):
    embed = discord.Embed(title=назва, description=опис, color=0x2ecc71)
    embed.add_field(name="Час", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)

    for emoji in reaction_options:
        embed.add_field(name=emoji, value="—", inline=True)

    message = await ctx.send(embed=embed)

    for emoji in reaction_options:
        await message.add_reaction(emoji)

    participants = {emoji: [] for emoji in reaction_options}

    await asyncio.sleep(1)  # пауза перед збором реакцій

    def check(reaction, user):
        return (
            reaction.message.id == message.id
            and str(reaction.emoji) in reaction_options
            and not user.bot
        )

    async def update_embed():
        for emoji in reaction_options:
            users = [user.mention for user in participants[emoji]]
            if not users:
                value = "—"
            else:
                value = " ".join(users)
            for field in embed.fields:
                if field.name == emoji:
                    field.value = value
        await message.edit(embed=embed)

    while True:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=180, check=check)

            # Зняти попередню реакцію, якщо є
            for emoji in reaction_options:
                if user in participants[emoji]:
                    participants[emoji].remove(user)
                    async for r in message.reactions:
                        if str(r.emoji) == emoji:
                            await r.remove(user)

            participants[str(reaction.emoji)].append(user)
            await update_embed()
        except asyncio.TimeoutError:
            break

# ---------- Твіни ----------
from discord import Embed

twin_names = [f"Твін {i}" for i in range(1, 10)]
twin_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
control_emojis = ["❌", "🔁"]
all_emojis = twin_emojis + control_emojis

twin_data = {}

@bot.command(name="твіни")
async def твіни(ctx):
    embed = Embed(title="Обери Твіна", color=0x3498db)
    embed.description = "\n".join(
        [f"{emoji} {name} —" for emoji, name in zip(twin_emojis, twin_names)]
    )
    message = await ctx.send(embed=embed)

    for emoji in all_emojis:
        await message.add_reaction(emoji)

    twin_data[message.id] = {
        "msg": message,
        "assignments": {},  # user_id -> index
    }

async def оновити_twin_embed(message, data):
    lines = []
    assigned = {i: None for i in range(9)}
    for user_id, index in data["assignments"].items():
        assigned[index] = f"<@{user_id}>"

    for i, (emoji, name) in enumerate(zip(twin_emojis, twin_names)):
        user_display = assigned[i] if assigned[i] else "—"
        lines.append(f"{emoji} {name} — {user_display}")

    embed = Embed(title="Обери Твіна", description="\n".join(lines), color=0x3498db)
    await message.edit(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.message.id not in twin_data:
        return

    data = twin_data[reaction.message.id]
    emoji = str(reaction.emoji)

    if emoji in twin_emojis:
        index = twin_emojis.index(emoji)
        # Видаляємо попередні вибори
        for e, i in list(data["assignments"].items()):
            if e == user.id or i == index:
                del data["assignments"][e]
        data["assignments"][user.id] = index
        await оновити_twin_embed(reaction.message, data)

    elif emoji == "❌":
        if user.id in data["assignments"]:
            del data["assignments"][user.id]
        await оновити_twin_embed(reaction.message, data)

    elif emoji == "🔁":
        data["assignments"].clear()
        await оновити_twin_embed(reaction.message, data)

    await reaction.remove(user)

# ---------- Запуск ----------
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)