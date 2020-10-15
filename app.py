import discord
from discord.ext import commands
from json import loads as js_load, dumps as js_dump

client = commands.Bot(command_prefix = '')

# takhle funkce existuje jenom proto, abych toho nemusel vypisovat tolik
def embed(t,d,c):
    return discord.Embed(title=t,description=d,color=c)

# takhle funkce extistuje ze stejného důvodu embed()
def sndembd(m,e,z=''):
    return m.channel.send(z, embed=e)

# objekt "Hrac" obsahuje nějaké důležité inforamce o hráčovi (nečekaně)
class Hrac:
    def __init__(self, hrac):
        self.hrac = hrac
        self.name = str(hrac)[:-5]
        self.mention = hrac.mention
        self.notify = False
        self.nick = hrac.nick if hrac.nick else hrac.name


asciovac = {'á':'a','č':'c','ď':'d','é':'e','ě':'e','í':'i','ň':'n','ó':'o','ř':'r','š':'s','ť':'t','ú':'u','ů':'u','ý':'y','ž':'z'} # tento dictionary se používá na "odháčkování" slov při kontrole
etapa = '' # Variable "etapa" znázorňuje jaká část hry právě probíhá. Může nabývat těchto hodnot - "": žádná hra neprobíhá, "hraci": zájemci o hru mohou zareagovat na určitou zprávu a být přidáni do hry, "hra": logicky probíhá hra
editor = None
hraci = []
hraje = 0
pismeno = ''
penalizace = False
slova = []
zprava = None # tento vairable se používá, když se má na nějakou zprávu zareagovat
gray = 0x4F545C
vsechna_slova = []
prefixy = {}

def update_all_words(d = False):
    global vsechna_slova
    obsah = []
    with open('allWords.json', 'r', encoding='utf-8') as f:
        obsah = js_load(f.read())
    if d:
        for slovo in d:
            if not slovo in obsah: obsah.append(slovo)
        with open('allWords.json', 'w', encoding='utf-8') as f:
            f.write(js_dump(obsah))
    vsechna_slova = obsah

update_all_words()

def update_prefixy(s = None, p = None):
    global prefixy
    obsah = {}
    with open('prefixy.json', 'r', encoding='utf-8') as f:
        obsah = js_load(f.read())
    if p:
        obsah[s] = p
        with open('prefixy.json', 'w', encoding='utf-8') as f:
            f.write(js_dump(obsah))
    prefixy = obsah

update_prefixy()

async def on_error(m, p, v, vv, vp):
    global hraci, hraje
    if p:
        await sndembd(m, embed(f'{v} Seš z kola ven!', vv, discord.Color.red()))
        hraci.pop(hraje)
    else:
        await sndembd(m, embed(f'{v} Ještě jednou a seš z kola ven!', vp, discord.Color.red()))
        return True

# resetuje všechny variebly týkající se hry a odešle embed
async def konec(mes):
    global etapa, hraci, slova, pismeno, penalizace, zprava, vsechna_slova
    etapa = ''
    hraci = []
    pismeno = ''
    penalizace = False
    update_all_words(slova)
    slova = []

# upravuje list "hraci" a variable "hraje", když někdo vypadne
async def pokracovat(mes):
    global penalizace, hraci, hraje
    penalizace = False
    hraje = 0 if hraje == len(hraci) else hraje
    await sndembd(mes, embed(f'Íčkon hraje {hraci[hraje]}', '', discord.Color.green()))

@client.event
async def on_ready():
    print('Jsem ready jak dva vředy :HAHaa:')

@client.event
async def on_message(mes):
    if mes.author == client.user: return
    global etapa, hraje, editor, hraci, prefixy

    if mes.content.startswith('py'):
        if str(mes.author) != 'Histmy#4295':
            await mes.channel.send('<:FU:674649887090147355>')
            return
        eval(mes.content[3:])

    prefix = prefixy.get(str(mes.guild.id), 'fotbal')
    # pokud zpráva začíná na prefix, a nebo tagnutím bota, přeskočí tento blok
    if not (mes.content.startswith(prefix) or mes.content.replace('!', '').startswith(f'<@{client.user.id}>')):
        if etapa == 'hraci' and mes.content.lower() == 'start' and (editor == mes.author.name or editor == mes.author.nick):
            if len(hraci) > 1:
                etapa = 'hra'
                hraje = 0
                z = hraci[hraje].mention if hraci[hraje].notify else ''
                await sndembd(mes, embed('Tož hra může začít!', 'Začíná: **' + hraci[hraje].name + '**!', discord.Color.green()), z)
                return
            await sndembd(mes, embed('Tak jste ptácí?', 'Dá se to hrát jenom ve **DVOU a více** hráčích!', discord.Color.red()))
        if etapa == 'hra' and mes.author.name == hraci[hraje].name:
            global pismeno, penalizace, slova
            slovo = mes.content.lower()
            veta_ven = f'{hraci[hraje].nick} left the game. *No Jo No*'
            veta_pozor = f'Pro ukončení, **{editor}**, napiš *"fotbal konec"*'
            if slovo.find(' ') != -1:
                if await on_error(mes, penalizace, 'Tak seš kokot? Má to bej **JEDNO** slovo!', veta_ven, veta_pozor):
                    penalizace = True
                    return
            if not slovo.isalpha():
                if await on_error(mes, penalizace, 'Tak seš kokot? Přijde ti že tohle je slovo?', veta_ven, veta_pozor):
                    penalizace = True
                    return
            if pismeno == '': pismeno = slovo[0]
            if asciovac.get(slovo[0], slovo[0]) != pismeno:
                if await on_error(mes, penalizace, f'Tak seš kokot? Šlak to má začínat na "**{pismeno.upper()}**", ne na "**{slovo[0].upper()}**"!', veta_ven, veta_pozor):
                    penalizace = True
                    return
            if slovo in slova:
                if await on_error(mes, penalizace, 'Super! Ale tohle slovo už **BYLO**!', veta_ven, veta_pozor):
                    penalizace = True
                    return

            if len(hraci) == 1:
                await sndembd(mes, embed('GG! **' + hraci[0].nick + '** vyhrál tůtu zkurvenost a získává **úplný hovno**!', '👏👏👏', discord.Color.gold()))
                await konec(mes)
                return

            slova.append(slovo)
            hraje = 0 if hraje + 1 == len(hraci) else hraje + 1
            pismeno = asciovac.get(slovo[-1], slovo[-1])
            penalizace = False
            await sndembd(mes, embed(f'Super! Nyní hraje: **{hraci[hraje].nick}**!', f'Napiš slovo začínající na: **{pismeno.upper()}**', discord.Color.green()))

        return

    args = mes.content.split(' ')[1:]
    if args == []:
        await sndembd(mes, embed('Chceš něco, more?', 'Pokud tě nedávno navštívil němec, nebo nemáš šajn oč tu běží, napiš *fotbal pomoc*', discord.Color.red()))
        return
    elif args[0] == 'konec':
        if etapa == '':
            await sndembd(mes, embed('Tak seš kokot?', 'Šlak není co ukončovat, ne?', discord.Color.red()))
        if etapa == 'hraci':
            etapa = ''
            hraci = []
            slova = []
            await sndembd(mes, embed('', 'Nastavování hry ukončeno', gray))
        if etapa == 'hra':
            if mes.author.name == editor:
                await sndembd(mes, embed('Konec hry!', 'nevyhrál **nikdo**', gray))
                await konec(mes)
            else:
                await sndembd(mes, embed('Co zkoušíš?', f'Tůto může jenom **{editor}**!', discord.Color.red()))
    elif args[0] == 'hra':
        if etapa != '':
            await sndembd(mes, embed('Tak seš kokot?', 'Šlak hra íčkon jede. A dvě se mi kontrolovat nechce.', discord.Color.red()))
        else:
            editor = ''
            if mes.author.nick: editor = mes.author.nick
            else: editor = mes.author.name
            await sndembd(mes, embed('**Nastavení hry**', editor + ' je správcem následující hry', discord.Color.blue()))
            global zprava
            zprava = await sndembd(mes, embed('Jesli chceš hrát i *ty*, kokote, klikni na ten zkurvnej míč. Jesli chceš abych na tebe řval, klikni na vyjebanej zvonec. Sráč **' + editor + '** může odstarovat tudle pičovinu napsáním "start"', 'Pro ukončení stačí napsat "fotbal konec"', discord.Color.blue()))
            await zprava.add_reaction('⚽')
            await zprava.add_reaction('🔔')
            etapa = 'hraci'
    elif args[0] == 'pomoc':
        embd = embed('Nápověda k fotbal botoj', 'Tady jsou všecky komandy, kterým bych měl rozumět', 0x7289DA)
        embd.add_field(name=f'{prefix} pomoc', value='Jakoby nečekaně mě to donutí poslat ti tuhle dokurveninu.', inline=False)
        embd.add_field(name=f'{prefix} hra', value='Tímto příkazem spustíš hru. Ale jenom když žádná další neběží!', inline=False)
        embd.add_field(name=f'{prefix} konec', value='Pokud nějaká hra běží, ukončí jí.', inline=False)
        embd.add_field(name=f'{prefix} prefix *[nový_prefix]*', value='změní prefix pro tento server na nově specifikovaný prefix', inline= False)
        embd.add_field(name=f'{prefix} leave', value='Když budeš chcet opustit probíhající hru jako nějaká kunda, použij tento komand.')
        embd.set_footer(text='to je všechno')
        await sndembd(mes, embd)
    elif args[0] == 'prefix':
        update_prefixy(str(mes.guild.id), args[1])
        await sndembd(mes, embed('Hotovo!', f'Úspěšně se ti povedlo změnit prefix z *{prefix}* na *{args[1]}*', discord.Color.green()))
    elif args[0] == 'leave':
        if etapa != 'hra':
            await sndembd(mes, embed('Tak seš kokot?', 'Nejenom že to chceš opustit jako nějká děvka, ale teď dokonce není ani z čeho utíkat! *tfuj*', discord.Color.red()))
        else:
            for i in range(len(hraci)):
                if mes.author != hraci[i].hrac: continue
                hraci.pop(i)
                break
            await sndembd(mes, embed('Jen si běž!', 'Ale ne, že tě tu uvidím příště! *tfuj*', gray))
            await pokracovat(mes)
    else: await sndembd(mes, embed('Co to bleješ za hovna?', f'Jestli nevíš která byje, nebo tě nedávno navštívil němec, napiš *{prefix} pomoc*', discord.Color.red()))

@client.event
async def on_reaction_add(reaction, user):
    # TODO přidat statistiku
    global zprava, etapa, hraci
    if str(reaction.message) == str(zprava) and user != client.user and etapa == 'hraci':
        if reaction.emoji == '⚽': hraci.append(Hrac(user))
        if reaction.emoji == '🔔':
            for i in range(len(hraci)):
                if hraci[i].hrac == user: hraci[i].notify = True;break

@client.event
async def on_reaction_remove(reaction, user):
    global zprava, hraci
    if str(reaction.message) == str(zprava) and etapa == 'hraci':
        for i in range(len(hraci)):
            if hraci[i].hrac != user: continue
            if reaction.emoji == '⚽': hraci.pop(i)
            if reaction.emoji == '🔔': hraci[i].notify = False
            break

client.run('TOKEN')

# TODOS:
    # TODO: vrátit na předchozího člověka
    # TODO: (vote-)kick
    # TODO: statistiky
    # TODO: pouze známá slova (asi za hodně dlouho, možná nidky ¯\_(ツ)_/¯)
    # TODO: podpora více serverů