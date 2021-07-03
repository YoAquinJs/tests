import json
import math
import asyncio
import requests
from gtts import gTTS
from random import randint
from tube_dl import Youtube
from moviepy.editor import *
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option
from discord.ext import commands
from discord.ext.commands import Context, BadArgument

from bot.bot_utils import *
from bot.discord_client import get_client
from database.db_utils import *
from database.mongo_client import close_client

client = get_client()
slash = SlashCommand(client, sync_commands=True)
guild_ids = []
for guild in client.guilds:
    guild_ids.add(guild.id)

global_settings = get_global_settings()


@client.command(name="stop")
async def stop_bot(ctx: Context):
    """Envia un mensaje con el ping del bot

    Args:
        ctx (Context): Context de discord
    """
    for dev_id in global_settings["dev_ids"]:
        if dev_id == ctx.author.id:
            await client.logout()
            await client.close()
            close_client()



@slash.slash(name="ping", guild_ids=guild_ids, description="latencia del bot")
async def ping_chek(ctx: SlashContext):
    await send_message(ctx, f"latencia: {round(client.latency * 1000)}ms")


@client.command(name="unirse")
async def join(ctx: Context, called_in_play=False):
    if not ctx.message.author.voice:
        await send_message(ctx, "entra a un canal")
        return
    channel = ctx.message.author.voice.channel
    await channel.connect()

    try:
        await channel.connect()
        await send_message(ctx, f"unido a {channel}")
    except:
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if channel == voice.channel and not called_in_play:
            await send_message(ctx, f"ya estoy en {channel}")
            return
        if channel != voice.channel:
            await voice.move_to(channel)
            await send_message(ctx, f"unido a {channel}")

#@client.command(name="voz")
#async def tts(ct: Context, *, text: str):
#    await join(ctx, True)
#    voice = ctx.voice_client
#
#    with open(f"{get_current_dir()}/tts/queue.json") as file:
#        queue = json.load(file)
#
#    queue[f"{ctx.author.id}"] = text
#
#    text = f"{ctx.author.display_name} dice: {text}"
#
#  def finished(*opt):
#      if os.path.exists("tts.mp3"):
#          os.remove("tts.mp3")
#      del tts_queue[0]
#      if not len(tts_queue) == 0:
#          gTTS(tts_queue[0], lang="es", tld="com.mx").save("tts.mp3")
#          vc.play(discord.FFmpegPCMAudio("tts.mp3"), after=finished)
#
#    gTTS(text, lang="es", tld="com.mx").save(f"{get_current_dir()}/tts.mp3")
#    voice.play(discord.FFmpegPCMAudio(executable=f"{get_current_dir()}/ffmpeg/bin/ffmpeg.exe",
#                                      source=f"{get_current_dir()}/tts.mp3"))
#    voice.source = discord.PCMVolumeTransformer(voice.source)
#
#    if os.path.isfile(f"tts.mp3"):
#        await send_message(ctx, "se esta diciendo un mensaje")
#        return

@client.command(name="tocar")
async def play(ctx: Context, *, search: str):
    await join(ctx, True)
    try:
        await stop(ctx)
        if os.path.isfile(f"{get_current_dir()}/song.mp4"):
            os.remove(f"{get_current_dir()}/song.mp4")
            print("removed mp4")
    except:
        print("couldn't delete the mp4")
        return

    # region url
    search_url = 'https://www.youtube.com/results?q=' + search
    count = 0
    cont = requests.get(search_url)
    lst = str(cont.content).split('"')
    for i in lst:
        count += 1
        if i == 'WEB_PAGE_TYPE_WATCH':
            break
    if lst[count - 5] == "/results":
        raise Exception("No video found.")
    url = f"https://www.youtube.com{lst[count - 5]}"
    print("url loaded")
    # endregion
    # region Youtube DownLoad and Parse
    yt = Youtube(url)
    yt.formats.first().download()
    print("video downloaded")
    for file in os.listdir("./"):
        if file.endswith(".mp4"):
            os.rename(file, "song.mp4")
            os.rename(f"song.mp4", f"{get_current_dir()}/song.mp4")
            video = VideoFileClip(f"{get_current_dir()}/song.mp4")
            video.audio.write_audiofile("song.mp3")
            os.rename(f"song.mp3", f"{get_current_dir()}/song.mp3")
            video.close()
    print("mp4 converted to mp3")
    # endregion

    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.play(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=f"{get_current_dir()}/song.mp3"))
    voice.source = discord.PCMVolumeTransformer(voice.source)

    await send_message(ctx, f"Tocando: {yt.title}")

@client.command(name="parar")
async def stop(ctx: Context):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        await send_message(ctx, "paro")
    voice.stop()

@client.command(name="pausar")
async def pause(ctx: Context):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        await send_message(ctx, "pausado")
    else:
        await send_message(ctx, "no se esta tocando nada")

@client.command(name="resumir")
async def resume(ctx: Context):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        await send_message(ctx, "resumido")
    else:
        await send_message(ctx, "el audio no esta pausado")

@client.command(name="irse")
async def leave(ctx: Context):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
        await send_message(ctx, f"me fui de {ctx.message.author.voice.channel}")
    else:
        await send_message(ctx, "el bot no esta conectado a ningun canal")


@slash.slash(name="borrar", guild_ids=guild_ids, description="borra la cantidad de mensajes especificada",
    options=[create_option(name="cantidad", description="mensajes a borrar", option_type=4, required=True)], 
    connector={"cantidad": "del_lines"})
@commands.has_permissions(manage_messages=True)
async def delete_line(ctx: SlashContext, del_lines:int):
    if del_lines > 100:
        del_lines = 100

    messages = await ctx.channel.history(limit=del_lines).flatten()
    if del_lines > len(messages):
        del_lines = len(messages)

    await ctx.channel.purge(limit=del_lines)

    if del_lines > 1:
        await send_message(ctx, f"{del_lines} mensajes eliminados")
    else:
        await send_message(ctx, "1 mensaje eliminado")


@slash.slash(name="canalbienvenida", guild_ids=guild_ids, description="guarda el canal de bienvenida",
    options=[create_option(name="canal", description="", option_type=7, required=True)],
    connector={"canal": "channel"})
@commands.has_permissions(administrator=True)
async def set_welcome_channel(ctx: SlashContext, channel: discord.TextChannel):
    if exists("name", "welcome_stt", ctx.guild, Collection.general.value) is False:
        insert({"name": "welcome_stt", "welcome_channel":0, "welcome_msg":""}, ctx.guild, Collection.general.value)
    modify("name", "welcome_stt", "welcome_channel", channel.id, ctx.guild, Collection.general.value)
    await send_message(ctx, f"canal de bienvenida {channel}, guardado")


@slash.slash(name="msgbienvenida", guild_ids=guild_ids, description="guarda el mensaje de bienvenida",
    options=[create_option(name="mensaje", description="", option_type=3, required=True)], 
    connector={"mensaje": "msg"})
@commands.has_permissions(administrator=True)
async def set_welcome_msg(ctx: SlashContext, *, msg: str):
    if exists("name", "welcome_stt", ctx.guild, Collection.general.value) is False:
        insert({"name": "welcome_stt", "welcome_channel":0, "welcome_msg":""}, ctx.guild, Collection.general.value)
    modify("name", "welcome_stt", "welcome_msg", msg, ctx.guild, Collection.general.value)
    await send_message(ctx, f"""mensaje de bienvenida "{msg}", guardado""")


@slash.slash(name="operacion", guild_ids=guild_ids, description="realiza una operacion matematica",
    options=[create_option(name="num1", description="numero flotante", option_type=3, required=True), 
             create_option(name="operador", description="operador matematico", option_type=3, required=True),
             create_option(name="num2", description="numero flotante", option_type=4, required=False)], 
    connector={"num1": "num1", "operador": "operation", "num2": "num2"})
async def math_operation(ctx: SlashContext, num1: float, operator: str, num2=0.0):
    if operator == "+":
        await send_message(ctx, f"{num1 + num2}")
    elif operator == "-":
        await send_message(ctx, f"{num1 - num2}")
    elif operator == "*":
        await send_message(ctx, f"{num1 * num2}")
    elif operator == "/":
        await send_message(ctx, f"{num1 / num2}")
    elif operator == "^":
        await send_message(ctx, f"{pow(num1, num2)}")
    elif operator == "|":
        await send_message(ctx, f"{math.sqrt(num1)}")
    elif operator == "!":
        result = int(1)
        for i in range(1, int(num1)+1):
            result = result * i

        await send_message(ctx, f"{result}")
    elif operator == "%":
        await send_message(ctx, f"{num1 % num2}")
    else:
        await send_message(ctx, "operador invalido\noperadores validos: +, *, /, ^, |sqrt, !factorial, %modulo")


@client.command(name="votacion")
@commands.has_permissions(administrator=True)
async def poll(ctx: SlashContext, *, info: str):
    await ctx.channel.purge(limit=1)
    name_description = key_split(name_description, "/")

    if exists("name", name_description[0], ctx.guild, Collection.selectors.value) is True:
        await ctx.author.send(f"el nombre {name_description[0]} ya existe")
        return

    msg = await ctx.channel.send(embed=discord.Embed(title=name_description[0], description=name_description[1]))
    await msg.add_reaction("❌")
    _insert = insert({"msg_id": msg.id, "name": name_description[0], "description": name_description[1], 
        "emoji_role": {}},ctx.guild, Collection.selectors.value)
    await ctx.author.send(f"id del selector: {_insert.inserted_id}")


@slash.slash(name="rol", guild_ids=guild_ids, description="asigna o remueve el rol especificado",
    options=[create_option(name="rol", description="", option_type=8, required=True)], 
    connector={"rol": "role"})
async def toggle_role(ctx: SlashContext, role: discord.Role):
    for _role in query_all(ctx.guild, Collection.role_black_list.value):
        if _role["id"] == role.id:
            await send_message(ctx, f"el rol {role.mention} se encuentra en la lista negra")
            return

    if not(role in ctx.author.roles):
        await ctx.author.add_roles(role)
        await send_message(ctx, f"se te ha asignado el rol {role.mention}")
    else:
        await ctx.author.remove_roles(role)
        await send_message(ctx, f"se te ha removido el rol {role.mention}")


@slash.slash(name="rolpara", guild_ids=guild_ids, description="asigna o remueve el rol especificado en el usuario especificado",
    options=[create_option(name="rol", description="", option_type=8, required=True),
             create_option(name="usuario", description="", option_type=6, required=True)], 
    connector={"rol": "role", "usuario": "user"})
@commands.has_permissions(administrator=True)
async def toggle_role_to(ctx: SlashContext, role: discord.Role, user: discord.Member):
    if not role in user.roles:
        await user.add_roles(role)
        await send_message(ctx, f"se le ha asignado el rol {role.mention} a {user.mention}")
    else:
        await user.remove_roles(role)
        await send_message(ctx, f"se le ha removido el rol {role.mention} a {user.mention}")


@slash.slash(name="rolesnegros", guild_ids=guild_ids, description="lista de roles en la lista negra")
async def get_roles_black_list(ctx: SlashContext):
    role_black_list = query_all(ctx.guild, Collection.role_black_list.value)

    if role_black_list.count() == 0:
        await send_message(ctx, "no hay ningun rol en la lista negra")
    else:
        embed = discord.Embed(title=f"lista Nera de Roles", colour=discord.colour.Color.gold())
        
        for role in role_black_list:
            embed.add_field(
                name=role["name"],
                value=f"id: {role['id']}",
            )

        await ctx.channel.send(embed=embed)


@slash.slash(name="arolesnegros", guild_ids=guild_ids, description="asigna o remueve un rol de la lista negra",
    options=[create_option(name="rol", description="", option_type=8, required=True)], 
    connector={"rol": "role"})
@commands.has_permissions(administrator=True)
async def toggle_role_black_list(ctx: SlashContext, role: discord.Role):
    if exists("id", role.id, ctx.guild, Collection.role_black_list.value) is False:
        insert({"name": role.name, "id": role.id}, ctx.guild, Collection.role_black_list.value)
        await send_message(ctx, f"rol {role.mention} ha sido añadido a la lista negra de los roles")
    else:
        delete("id", role.id, ctx.guild, Collection.role_black_list.value)
        await send_message(ctx, f"rol {role.mention} ha sido removido a la lista negra de los roles")
    

@slash.slash(name="rolselec", guild_ids=guild_ids, description="crea un selector de roles",
    options=[create_option(name="nombre", description="nombre unico", option_type=3, required=True),
             create_option(name="descripcion", description="", option_type=3, required=True)], 
    connector={"nombre": "name", "descripcion": "description"})
@commands.has_permissions(administrator=True)
async def role_selector(ctx: SlashContext, name: str, description: str):
    await ctx.channel.purge(limit=1)

    if exists("name", name, ctx.guild, Collection.selectors.value) is True:
        await ctx.author.send(f"el nombre {name} ya existe")
        return

    msg = await ctx.channel.send(embed=discord.Embed(title=name, description=description))
    await msg.add_reaction("❌")
    _insert = insert({"msg_id": msg.id, "name": name, "description": description, "emoji_role": {}}, 
        ctx.guild, Collection.selectors.value)
    await ctx.author.send(f"id del selector: {_insert.inserted_id}")


@slash.slash(name="editrolselec", guild_ids=guild_ids, description="edita un selector de roles",
    options=[create_option(name="id", description="id del selector", option_type=3, required=True),
             create_option(name="nombre", description="nuevo nombre", option_type=3, required=False),
             create_option(name="descripcion", description="nueva descripcion", option_type=3, required=False)], 
    connector={"id": "_id", "nombre": "name", "descripcion": "description"})
@commands.has_permissions(administrator=True)
async def edit_role_selector(ctx: SlashContext, _id: str, name="", description=""):
    await ctx.channel.purge(limit=1)

    for selector in query_all(ctx.guild, Collection.selectors.value):
        if selector["name"] == name and selector["_id"] != _id and name != "":
            await ctx.author.send(f"el nombre {name} ya existe")
            return

    selector = query_id(_id, ctx.guild, Collection.selectors.value)

    if selector is None:
        await ctx.author.send("id invalido")
        return

    if name != "":
        modify("msg_id", selector["msg_id"], "name", name, ctx.guild, Collection.selectors.value)
    else:
        name = selector["name"]

    if description != "":
        modify("msg_id", selector["msg_id"], "description", description, ctx.guild, 
            Collection.selectors.value)
    else:
        description = selector["description"]

    selector = query_id(_id, ctx.guild, Collection.selectors.value)

    msg = await ctx.channel.fetch_message(selector["msg_id"])

    embed = discord.Embed(title=name, description=description)

    for key in selector["emoji_role"].keys():
        embed.add_field(name=f"Rol: {selector['emoji_role'][key][0]}", value=f"Emoji: {key}")

    await msg.edit(embed=embed)
    await ctx.author.send("edicion realizada")


@slash.slash(name="rolaselec", guild_ids=guild_ids, description="agrega un rol a un selector de roles",
    options=[create_option(name="id", description="id del selector", option_type=3, required=True),
             create_option(name="emoji", description="", option_type=3, required=True),
             create_option(name="rol", description="", option_type=8, required=True)], 
    connector={"id": "_id", "emoji": "eomji", "rol": "role"})
@commands.has_permissions(administrator=True)
async def toggle_role_to_selector(ctx: SlashContext, _id, emoji, role: discord.Role):
    await ctx.channel.purge(limit=1)
    selector = query_id(_id, ctx.guild, Collection.selectors.value)

    if selector is None:
        await ctx.author.send("id inalido")
        return

    if emoji == "❌":
        await ctx.author.send("el emoji no puede ser ❌, ya que esta en uso por el selector")
        return

    msg = await ctx.fetch_message(selector["msg_id"])
    action = ""

    if emoji in selector["emoji_role"].keys() and role.id == selector["emoji_role"][emoji][1]:
        del selector["emoji_role"][emoji]
        await msg.remove_reaction(emoji, client.user)
        action = "eliminado"
    else:
        for _emoji in selector["emoji_role"].keys():
            if emoji == _emoji:
                await ctx.author.send(f"el emoji {emoji} ya esta en uso")
                return
            if role.id == selector["emoji_role"][_emoji][1]:
                await ctx.author.send(f"el rol {role.mention} ya esta en uso")
                return
        selector["emoji_role"][emoji] = role.id
        action = "agregado"
        await msg.add_reaction(emoji)

    embed = discord.Embed(colour=discord.colour.Color.gold(), title=selector["name"], 
        description=selector["description"])
    for key in selector["emoji_role"].keys():
        embed.add_field(name=f"Rol: {discord.utils.get(guild.roles, id=selector['emoji_role'][key]).mention}", 
            value=f"Emoji: {key}")

    await msg.edit(embed=embed, content="")
    replace("msg_id", selector["msg_id"], selector, ctx.guild, Collection.selectors.value)
    await ctx.author.send(f"rol {role.mention}, emoi: {emoji} {action}")


@slash.slash(name="delrolselec", guild_ids=guild_ids, description="elimina un selector de roles",
    options=[create_option(name="id", description="id del selector", option_type=3, required=True)], 
    connector={"id": "_id"})
@commands.has_permissions(administrator=True)
async def delete_role_selector(ctx: SlashContext, _id):  
    await ctx.channel.purge(limit=1)

    selector = query_id(_id, ctx.guild, Collection.selectors.value)

    if selector is False:
        await send_message(ctx, "id invalido", "", 0, True)
        return

    try:
        msg = await ctx.fetch_message(selector["msg_id"])
        await msg.delete()
    except:
        pass

    delete("msg_id", selector["msg_id"], ctx.guild, Collection.selectors.value)
    await ctx.author.send(f"selector de roles {_id} eliminado")


@slash.slash(name="ayuda", guild_ids=guild_ids, description="comandos disponibles")
async def help_cmd(ctx: SlashContext):
    prefix = client.command_prefix
    embed = discord.Embed(title=f"Ayuda | MIGALA BOT {client.command_prefix}ayuda", 
        colour=discord.colour.Color.gold())

    embed.add_field(
        name=f"{prefix}rol",
        value="Añade o remueve un rol\n\nArgumentos: @rol: rol a agregar",
    )

    embed.add_field(
        name=f"{prefix}rolesnegros",
        value="Muestra la lista negra de roles\n\nArgumentos: N/A",
    )

    embed.add_field(
        name=f"{prefix}tocar",
        value="reproduce el primer video de la busqueda en youtube\n\nArgumentos: busqueda: la busqueda a realizar"
        "n youtube (se admiten multiples palabras)",
    )

    embed.add_field(
        name=f"{prefix}parar",
        value="detiene el contenido actual del bot (no puede ser reanudado)\n\nArgumentos: N/A",
    )

    embed.add_field(
        name=f"{prefix}pausar",
        value="pausa el bot\n\nArgumentos: N/A",
    )

    embed.add_field(
        name=f"{prefix}resumir",
        value="reanuda el bot\n\nArgumentos: N/A",
    )

    embed.add_field(
        name=f"{prefix}irse",
        value="El bot se retira del canal en el que se encuentre\n\nArgumentos: N/A",
    )

    embed.add_field(
    name=f"{prefix}unirse",
    value="el bot se une al canal en el cual se encuentre el usuario\n\nArgumentos: N/A",
    )

    embed.add_field(
        name=f"{prefix}operacion",
        value="Realiza una operacion matematica\n\nArgumentos: num1: un numero; operador: +, *, /, ^, |(sqrt), !(factorial), %(modulo), "
        "num2: un numero\n\nUsuarios: cualquiera",
    )

    embed.add_field(
        name=f"{prefix}adminayuda",
        value="Muestra los comandos que requieren permisos de administrator\n\nArgumneots: N/A",
    )

    await ctx.channel.send(embed=embed)


@slash.slash(name="adminayuda", guild_ids=guild_ids, description="comandos disponibles solo para admins")
@commands.has_permissions(administrator=True)
async def help_cmd(ctx: SlashContext):
    prefix = client.command_prefix
    embed = discord.Embed(title=f"Ayuda | MIGALA BOT {client.command_prefix}adminayuda", 
        colour=discord.colour.Color.gold())

    embed.add_field(
        name=f"{prefix}rolpara",
        value="Agrega o remueve un rol al usuario especificado\n\nArgumentos: @rol: rol; @user: usuariorios",
    )

    embed.add_field(
        name=f"{prefix}arolesnegros",
        value="Agrega o remueve un rol a la lista negra de roles\n\nArgumentos: @rol: el rol",
    )

    embed.add_field(
    name=f"{prefix}rolselec",
        value="""Genera un selector de roles\n\nArgumentos: info: titulo caracter separador "/" descripcion\n\n"""
        """Usuarios: Admin""",
    )

    embed.add_field(
        name=f"{prefix}rolaselec",
        value="Agrega un rol al selector de roles\n\nArgumentos: id: id del selector; emoji: el emoji "
               "representativo del rol; rol: el rol a añadir o eliminar al reaccionar\n\nUsuarios: Admin",
    )

    embed.add_field(
        name=f"{prefix}editrolselec",
        value="""Cambia el nombre a un selector de roles\n\nArgumentos: id: id del selector; info: titulo caracter 
                 separador "/" "descripcion, por defecto los valores son 0, si se dejan asi no cambiaran""",
    )

    embed.add_field(
        name=f"{prefix}delrolselec",
        value="Elimina un selector de roles\n\nArgumentos: id: id del selectorN/A",
    )

    embed.add_field(
        name=f"{prefix}msgbienvenida",
        value="Guarda el mensaje de bienvenida\n\nArgumentos: mensaje: parrafo con el mensaje",
    )

    embed.add_field(
        name=f"{prefix}canalbienvenida",
        value="Guarda el canal de bienvenida\n\nArgumentos: canal: #canal",
    )

    embed.add_field(
        name=f"{prefix}borrar",
        value="Elimina una cantidad de mensajes hacia arriba\n\nArgumentos: n: cantidad de mensajes a eliminar "
        "(maximo 100)",
    )

    await ctx.channel.send(embed=embed)