import discord
from discord.ext import commands, tasks
import sqlite3
import os
import random
from flask import Flask
from threading import Thread
import datetime

# ==========================================
# 0. SISTEMA DE SUPERVIVENCIA (KEEP ALIVE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return f"⭐ NACE SYSTEM: Online - Pulso: {datetime.datetime.now().strftime('%H:%M:%S')}"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ==========================================
# 1. CONFIGURACIÓN DEL BOT
# ==========================================
MAIN_COLOR = 0x6a0dad 
RANK_COLORS = {
    'C': 0x95a5a6, 'B': 0x2ecc71, 'A': 0x3498db, 'S': 0xe67e22, 'SS': 0xf1c40f
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command('help')

# ==========================================
# 2. BASE DE DATOS
# ==========================================
db_connection = sqlite3.connect('system.db', check_same_thread=False)
db_cursor = db_connection.cursor()
db_cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id TEXT PRIMARY KEY, inventory TEXT, lang TEXT DEFAULT 'EN')''')
db_connection.commit()

# ==========================================
# 3. TRADUCCIONES
# ==========================================
strings = {
    'EN': {
        'help_title': "📖 Help Center - NACE",
        'help_desc': "Welcome! I am **NACE**, your photocard assistant.",
        'help_cmds': "🚀 Commands",
        'help_rarity_title': "📊 Rarity Probabilities",
        'help_rarity_list': "⬜ **Rank C:** 40%\n🟩 **Rank B:** 30%\n🟦 **Rank A:** 20%\n🟧 **Rank S:** 8%\n⭐ **Rank SS:** 2%",
        'create_ok': "✅ Profile created! Welcome to NACE.",
        'create_exists': "⚠️ Profile already exists.",
        'claim_no_acc': "❌ Use `/create` first.",
        'claim_success': "🎉 NEW PHOTOCARD!",
        'claim_found': "You found",
        'cooldown': "⏳ Wait **{} minutes** before claiming again.",
        'inv_title': "🗃️ {}'s Album",
        'inv_empty': "📂 Your inventory is empty.",
        'lang_change': "✅ Language changed to **English**!",
        'lang_error': "🌐 Usage: `/language EN` or `/language ES`.",
        'footer': "Good luck!"
    },
    'ES': {
        'help_title': "📖 Centro de Ayuda - NACE",
        'help_desc': "¡Bienvenido! Soy **NACE**, tu asistente de photocards.",
        'help_cmds': "🚀 Comandos",
        'help_rarity_title': "📊 Probabilidades de Rareza",
        'help_rarity_list': "⬜ **Rango C:** 40%\n🟩 **Rango B:** 30%\n🟦 **Rango A:** 20%\n🟧 **Rango S:** 8%\n⭐ **Rango SS:** 2%",
        'create_ok': "✅ ¡Perfil creado! Bienvenido a NACE.",
        'create_exists': "⚠️ El perfil ya existe.",
        'claim_no_acc': "❌ Usa `/create` primero.",
        'claim_success': "🎉 ¡NUEVA PHOTOCARD!",
        'claim_found': "Has encontrado a",
        'cooldown': "⏳ Espera **{} minutos**.",
        'inv_title': "🗃️ Álbum de {}",
        'inv_empty': "📂 Tu inventario está vacío.",
        'lang_change': "✅ ¡Idioma cambiado a **Español**!",
        'lang_error': "🌐 Uso: `/language ES` o `/language EN`.",
        'footer': "¡Buena suerte!"
    }
}

# ==========================================
# 4. TRUCO DE ACTIVIDAD (BUCLE)
# ==========================================
@tasks.loop(minutes=2)
async def stay_awake():
    # Esto imprime en consola cada 2 minutos para que Replit vea flujo de datos
    print(f"⏰ [PULSO] Manteniendo conexión viva: {datetime.datetime.now().strftime('%H:%M:%S')}")

# ==========================================
# 5. EVENTOS Y COMANDOS
# ==========================================

@bot.event
async def on_ready():
    print(f'⭐ NACE SYSTEM READY: {bot.user.name} is now online.')
    if not stay_awake.is_running():
        stay_awake.start()

@bot.command()
async def language(ctx, lang: str = None):
    user_id = str(ctx.author.id)
    if lang is None:
        db_cursor.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        res = db_cursor.fetchone()
        current_lang = res[0] if res else 'EN'
        return await ctx.send(strings[current_lang]['lang_error'])

    lang = lang.upper()
    if lang not in ['EN', 'ES']:
        return await ctx.send("🌐 Usage: `/language EN` | `/language ES`")

    db_cursor.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))
    db_connection.commit()
    await ctx.send(strings[lang]['lang_change'])

@bot.command()
async def help_me(ctx):
    user_id = str(ctx.author.id)
    db_cursor.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
    res = db_cursor.fetchone()
    lang = res[0] if res else 'EN'
    s = strings[lang]

    embed = discord.Embed(title=s['help_title'], description=s['help_desc'], color=MAIN_COLOR)
    cmd_text = "`/create` - Registrarse\n`/language` - Idioma\n`/claim` - Carta\n`/inventory` - Álbum"
    embed.add_field(name=s['help_cmds'], value=cmd_text, inline=False)
    embed.add_field(name=s['help_rarity_title'], value=s['help_rarity_list'], inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.cooldown(1, 3600, commands.BucketType.user)
async def claim(ctx):
    user_id = str(ctx.author.id)
    db_cursor.execute("SELECT inventory, lang FROM users WHERE user_id=?", (user_id,))
    row = db_cursor.fetchone()
    if not row:
        ctx.command.reset_cooldown(ctx)
        return await ctx.send(strings['EN']['claim_no_acc'])

    inv, lang = row
    s = strings[lang]
    pool = ['C']*40 + ['B']*30 + ['A']*20 + ['S']*8 + ['SS']*2
    rank = random.choice(pool)
    folder = f'cartas/{rank}'

    if not os.path.exists(folder) or not os.listdir(folder):
        ctx.command.reset_cooldown(ctx)
        return await ctx.send(f"⚠️ Error: Folder {rank} empty.")

    photos = [f for f in os.listdir(folder) if f.endswith(('.jpg', '.png', '.jpeg'))]
    chosen_photo = random.choice(photos)
    idol = chosen_photo.split('.')[0].replace('_', ' ').capitalize()

    card_id = f"[{rank}] {idol}"
    new_inv = (inv or "") + f"{card_id}, "
    db_cursor.execute("UPDATE users SET inventory=? WHERE user_id=?", (new_inv, user_id))
    db_connection.commit()

    embed = discord.Embed(title=s['claim_success'], description=f"{s['claim_found']} **{idol}**", color=RANK_COLORS[rank])
    file = discord.File(f"{folder}/{chosen_photo}", filename="card.png")
    embed.set_image(url="attachment://card.png")
    await ctx.send(file=file, embed=embed)

@claim.error
async def claim_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        user_id = str(ctx.author.id)
        db_cursor.execute("SELECT lang FROM users WHERE user_id=?", (user_id,))
        res = db_cursor.fetchone()
        lang = res[0] if res else 'EN'
        await ctx.send(strings[lang]['cooldown'].format(round(error.retry_after / 60)))

@bot.command()
async def create(ctx):
    user_id = str(ctx.author.id)
    db_cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if db_cursor.fetchone():
        await ctx.send(strings['EN']['create_exists'])
    else:
        db_cursor.execute("INSERT INTO users (user_id, inventory, lang) VALUES (?, ?, ?)", (user_id, "", "EN"))
        db_connection.commit()
        await ctx.send(strings['EN']['create_ok'])

@bot.command()
async def inventory(ctx):
    user_id = str(ctx.author.id)
    db_cursor.execute("SELECT inventory, lang FROM users WHERE user_id=?", (user_id,))
    row = db_cursor.fetchone()
    if not row or not row[0]:
        lang = row[1] if row else 'EN'
        return await ctx.send(strings[lang]['inv_empty'])

    lang = row[1]
    cards = [c for c in row[0].split(", ") if c]
    cards.sort()

    album_list = "\n".join([f"• {c}" for c in cards])
    embed = discord.Embed(title=strings[lang]['inv_title'].format(ctx.author.display_name), 
                          description=album_list[:2048], color=MAIN_COLOR)
    await ctx.send(embed=embed)

# ==========================================
# 6. LANZAMIENTO
# ==========================================
keep_alive()

try:
    bot.run(os.environ['DISCORD_TOKEN'])
except Exception as e:
    print(f"❌ Error: {e}")