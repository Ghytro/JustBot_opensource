TOKEN = "TOKEN HERE"
vk_access_token = "TOKEN HERE"
__SESSIONS__ = []
__USERNAME_TIMES__ = {}
msk_offset = 10800000

def rus_letters_lower(line):
    big = u'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ'
    small = u'йцукенгшщзхъфывапролджэячсмитьбю'
    for i in range(len(line)):
        f = big.find(line[i])
        if f != -1:
            line = line[0:i] + small[f] + line[i + 1:len(line)]
    return line

def rus_letters_upper(line):
    big = u'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ'
    small = u'йцукенгшщзхъфывапролджэячсмитьбю'
    for i in range(len(line)):
        f = small.find(line[i])
        if f != -1:
            line = line[0:i] + big[f] + line[i + 1:len(line)]
    return line

def PC_word_to_unguessed(word, guessed_letters):
    new_word = ''
    for i in range(len(word) - 1):
        if word[i] in guessed_letters:
            new_word += '[' + word[i] + '] '
        else:
            new_word += '[?] '
    return new_word

def is_wrong_kb_layout(text):
    return False
    rus = "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
    eng = "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>"
    #print(text)

    if "http://" in text or "https://" in text:
        return False

    if len(text) == 0:
        return False
    for i in rus:
        if i in text:
            return False
    
    for i in eng:
        if i in text:
            break
    else:
        return False
    
    vow = 'eyuioa'
    vow_counter = 0
    for i in text:
        vow_counter += int(i in vow)
    return vow_counter / len(text) <= .2

def change_layout_torus(text):
    eng = "qwertyuiop[]asdfghjkl;'zxcvbnm,.QWERTYUIOP{}ASDFGHJKL:\"ZXCVBNM<>/?"
    rus = "йцукенгшщзхъфывапролджэячсмитьбюЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ.,"
    for i in range(len(eng)):
        text = text.replace(eng[i], rus[i])
    return text

import discord
import io
import os
import datetime
import requests
import random
import sys
import time
import asyncio

class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as {0}".format(self.user))

    async def on_message(self, msg):
        global __SESSIONS__
        if msg.author == JustBot.user:
            return
        
        reply_channel = msg.channel
        message = msg.content
        if len(message) == 0:
            return
        sender = str(msg.author)
        if findSessionByID(reply_channel.id) == None:
            insertSession(session(reply_channel.id))
        current_session = findSessionByID(reply_channel.id)
        if message != ".ru":
            current_session.last_message[sender] = message
        else:
            repl = change_layout_torus(current_session.last_message[sender])
            await reply_channel.send(f"{msg.author.mention}, перевожу на русскую раскладку: " + repl)
            return
        #debug output
        #print(current_session.chat_id)
        #print(current_session.infa_queue)
        print("Message from {0.author}: {0.content}".format(msg))

        if message == ".voicesettings":
            speaker_sex = None
            speaker_emotion = None

            if current_session.speechsettings.speaker[0] == "a":
                speaker_sex = "мужской"
            else:
                speaker_sex = "женский"

            if current_session.speechsettings.emotion == "neutral":
                speaker_emotion = "нейтральный"
            elif current_session.speechsettings.emotion == "good":
                speaker_emotion = "дружеский"
            else:
                speaker_emotion = "раздраженный"

            emb = discord.Embed(title="Настройки синтезатора речи", colour=discord.Colour.green())
            emb.add_field(name = "Голос:", value = speaker_sex, inline = True)
            emb.add_field(name = "Скорость:", value = current_session.speechsettings.speed, inline = True)
            emb.add_field(name = "Тон:", value = speaker_emotion, inline = True)
            emb.add_field(name = "Команды для изменения настроек синтезатора", value = "**.changespeaker** - изменение голоса с мужского на женский и наоборот\n\n**.changemood <настроение>** - изменение тона речи в соответствии с настроением.\n**Настроения:** **neutral** (нейтральный), **good** (дружеский), **evil** (раздраженный)\n\n**.changespeed <скорость речи>** - изменить скорость говорения (от 0.1 до 2.0)", inline=False)
            emb.set_footer(text="Синтезатор речи предоставлен сервисом apihost.ru")
            await reply_channel.send(embed = emb)
            return

        if message == ".changespeaker":
            speaker_sex = None
            if current_session.speechsettings.speaker[0] == 'a':
                current_session.speechsettings.speaker = "oksana"
                speaker_sex = "женский"
            else:
                current_session.speechsettings.speaker = "anton_samokhvalov"
                speaker_sex = "мужской"
            await reply_channel.send(f"Голос изменен на {speaker_sex}")
            return

        if message[:len(".changemood")] == ".changemood":
            new_mood = message.split(" ")[1]
            allowed_moods = ["good",      "neutral",     "evil"]
            rus =           ["дружеский", "нейтральный", "раздраженный"]
            
            if new_mood not in allowed_moods:
                await reply_channel.send("Неверно введен тон речи.\nТоны: neutral, good, evil")
                return

            current_session.speechsettings.emotion = new_mood
            await reply_channel.send(f"Тон изменен на {rus[allowed_moods.index(new_mood)]}")
            return

        if message[:len(".changespeed")] == ".changespeed":
            speed = message.split(" ")[1]
            fsp = None
            try:
                fsp = float(speed)
            except ValueError:
                await reply_channel.send("Скорость введена в неверном формате (должно быть число с точкой)")
                return
            
            current_session.speechsettings.speed = min(round(fsp, 1), 2.0)
            await reply_channel.send(f"Скорость речи изменена на {current_session.speechsettings.speed}")
            return
        #hidden messages
        if message == ".stop":
            try:
                voice_channel = msg.author.voice.channel
            except NameError:
                await reply_channel.send("Войдите в голосовой канал, чтобы использовать эту команду")
                return

            current_session.is_playing_gachi = False
            return

        if message == ".meme":
            if len(current_session.meme_publics) == 0:
                await reply_channel.send("Вы не добавили ни одного паблика. Добавьте их при помощи команды .memepublic. Смотрите .help")
                return
            posts_quantity = 100
            public = random.choice(current_session.meme_publics)
            #старая версия api была 5.122
            posts = requests.get("https://api.vk.com/method/wall.get?v=5.122&domain="+public+"&count="+str(posts_quantity)+"&access_token="+vk_access_token).json()['response']
            post_num = random.randint(0, posts_quantity - 1)

            while True:
                try:
                    while len(posts['items'][post_num]['attachments']) > 1 or posts['items'][post_num]['attachments'][0]['type'] != 'photo':
                        post_num = random.randint(0, posts_quantity - 1)
                    break
                except KeyError:
                    post_num = random.randint(0, posts_quantity - 1)
                    continue

            picture_link = posts['items'][post_num]['attachments'][0]['photo']['sizes'][-1]['url']
            pic_query = requests.get(picture_link)

            try:
                post_caption = posts['items'][post_num]['text']
            except KeyError:
                post_caption = ""

            emb = discord.Embed(colour=discord.Colour.green(), description=post_caption)
            emb.set_image(url=picture_link)
            emb.set_footer(text=f"Взято из паблика {public}")
            await reply_channel.send(embed=emb)
            return
        
        if message.startswith('.memepublic'):
            lexems = message.split()
            if len(lexems) == 1:
                #выводим список пабликов для данного канала
                if len(current_session.meme_publics) == 0:
                    await reply_channel.send("Еще ни одного паблика не было добавлено")
                else:
                    rep_message = "```css\nСписок пабликов:\n"
                    num = 1
                    for i in current_session.meme_publics:
                        rep_message += f"{num}. {i}\n"
                        num += 1
                    rep_message += "```"
                    await reply_channel.send(rep_message)

            elif len(lexems) == 2:
                if lexems[1] == "add":
                    await reply_channel.send(f"{msg.author.mention}, вы не указали, какой паблик нужно добавить. Смотрите .help")
                elif lexems[1] == "remove":
                    await reply_channel.send(f"{msg.author.mention}, вы не указали какой паблик нужно удалить. Смотрите .help")
                else:
                    await reply_channel.send(f"{msg.author.mention}, вы неправильно используете эту команду. Смотрите .help")

            elif len(lexems) == 3:
                if lexems[1] == "add":
                    if lexems[2] in current_session.meme_publics:
                        await reply_channel.send(f"{msg.author.mention}, этот паблик уже есть в списке")
                    else:
                        try:
                            public_info = requests.get(f"https://api.vk.com/method/groups.getById?v=5.21&group_id={lexems[2]}&access_token={vk_access_token}").json()["response"]
                        except KeyError:
                            await reply_channel.send(f"{msg.author.mention}, к сожалению я не нашел такого паблика. Проверьте, правильно ли вы ввели его короткий адрес.")
                        else:
                            current_session.meme_publics.append(lexems[2])
                            await reply_channel.send(f"{msg.author.mention}, паблик {lexems[2]} добавлен в список")
                
                elif lexems[1] == "remove":
                    try:
                        current_session.meme_publics.remove(lexems[2])
                    except ValueError:
                        await reply_channel.send(f"{msg.author.mention}, этого паблика и так не было в списке")
                    else:
                        await reply_channel.send(f"{msg.author.mention}, паблик {lexems[2]} был удален из списка")
            return
                    

        if message == ".earrape":
            if current_session.is_playing_gachi:
                await reply_channel.send("Я уже воспроизвожу")
                return
            try:
                temp = msg.author.voice.channel
            except AttributeError:
                await reply_channel.send("Войдите в голосовой канал, чтобы использовать эту команду")
                return
            
            song = random.choice(os.listdir("Earrape"))
            voice_channel = msg.author.voice.channel
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(source='Earrape/' + song, executable="C:/ffmpeg/ffmpeg.exe"), after=lambda e: print('done', e))
            while vc.is_playing():
                await asyncio.sleep(1)
            vc.stop()
            await vc.disconnect()
            return

        if message[0:4] == ".say":
            return
            text = message[5:]
            if len(text) > 1000:
                await reply_channel.send("Длина фразы больше 1000. Попробуйте покороче")
                return
            #print(text)
            req = requests.get(current_session.speechsettings.gen_http_request(text))
            if not os.path.exists(str(current_session.chat_id)):
                os.mkdir(str(current_session.chat_id))
            with open(str(current_session.chat_id)+"/speech.mp3", "wb") as mp3file:
                mp3file.write(req.content)
            mp3file.close()
            await reply_channel.send(file=discord.File(str(current_session.chat_id)+"/speech.mp3"))
            os.remove(os.getcwd()+"/"+str(current_session.chat_id)+"/speech.mp3")
            return

        if message[0] == '.':
            if (message[1:5] == 'help'):
                emb = discord.Embed(title="Доступные команды", colour=discord.Colour.green())
                emb.add_field(name=".meme", value="Присылает случайный мем", inline=False)
                emb.add_field(name=".infa <Какая-то фраза>", value="Выводит вероятность названного события/факта. Прям как шар-гадалка", inline=False)
                emb.add_field(name=".polechudes", value=" Запуск игры Поле Чудес. Можно играть как в приватном чате, так и в групповом с друзьями. Крутите барабан!", inline=False)
                emb.add_field(name=".time", value="Узнать точное время в вашем городе", inline=False)
                emb.add_field(name=".ru", value="Перевести ваше последнее сообщение с английской раскладки на русскую. Jxtym j,blyj tckb ds ljkuj gbcfkb nfr)", inline=False)
                emb.add_field(name=".help", value="Вывести список команд бота")
                emb.add_field(name=".earrape", value="Введи и посмотри что будет. (Headphones warning)", inline=False)
                await reply_channel.send(embed = emb)
                return

            if (message[1:5] == 'infa'):
                fact = message[6:]
                if fact == "":
                    await reply_channel.send(f"{msg.author.mention}, вы не написали факт")
                    return
                sm_let_fact = rus_letters_lower(fact)
                danil_names = ['даня', 'данил', 'даниил', 'данила', 'данон']
                answers = ['Вероятность того, что ' + fact, fact + ' с вероятностью', 'Шанс того, что ' + fact]
                infa = random.randint(0, 100)

                for i in range(len(danil_names)):
                    if sm_let_fact.find(danil_names[i], 0, len(sm_let_fact)) != -1:
                        infa = 100
                        break
                phrase = answers[random.randint(0, 2)] + ' ' + str(infa) + '%'

                await reply_channel.send(phrase)
                return

            #creating polechudes session
            if (message[0:11] == '.polechudes'):
                if current_session.polechudes_status == 'not_playing':
                    await reply_channel.send('Начинаем игру.\nТе, кто хотят играть, пишите + в чат.\nЧтобы начать игру, создатель текущей игры должен написать .begin\nДля того, чтобы кикнуть игрока из игры, создатель лобби должен написать .kick @username до того, как игра начнется.\nВы можете выйти из игры в любой момент, написав .exit.')
                    current_session.polechudes_status = 'creating_lobby'
                    current_session.polechudes_lobbycreator = sender
                    current_session.polechudes_players.append(sender)
                elif current_session.polechudes_status == 'playing':
                    await reply_channel.send('Поле Чудес уже идет. Дождитесь конца текущей игры.')

                elif current_session.polechudes_status == 'creating_lobby':
                    await reply_channel.send('Уже идет создание лобби. Присоединяйтесь быстрее!')

            if message == '.exit' and sender in current_session.polechudes_players:
                if current_session.polechudes_status == 'creating_lobby':
                    del current_session.polechudes_players[current_session.polechudes_players.index(sender)]
                    await reply_channel.send(f'Игрок {msg.author.mention} вышел.')
                    if len(current_session.polechudes_players) == 0:
                        await reply_channel.send('Так как все игроки вышли, игра окончена.')
                        current_session.polechudes_status=             u'not_playing'
                        current_session.polechudes_lobbycreator=       u'null'
                        current_session.polechudes_players=            []
                        current_session.polechudes_banlist=            []
                        current_session.polechudes_word=               u'null'
                        current_session.polechudes_current_turn=       -1
                        current_session.polechudes_question=           u'null'
                        current_session.polechudes_guessed_letters=    u''
                        current_session.polechudes_used_letters=       u''
                    return
                
                if current_session.polechudes_status == 'playing':
                    del current_session.polechudes_players[current_session.polechudes_players.index(sender)]
                    await reply_channel.send(f'Игрок {msg.author.mention} вышел')
                    if len(current_session.polechudes_players) == 0:
                        await reply_channel.send('Так как все игроки вышли, игра окончена.')
                        current_session.polechudes_status=             u'not_playing'
                        current_session.polechudes_lobbycreator=       u'null'
                        current_session.polechudes_players=            []
                        current_session.polechudes_banlist=            []
                        current_session.polechudes_word=               u'null'
                        current_session.polechudes_current_turn=       -1
                        current_session.polechudes_question=           u'null'
                        current_session.polechudes_guessed_letters=    u''
                        current_session.polechudes_used_letters=       u''
                        return
                    
                    if current_session.polechudes_current_turn == len(current_session.polechudes_players):
                        current_session.polechudes_current_turn = 0
                    await reply_channel.send('Текущий ход передается @' + current_session.polechudes_players[current_session.polechudes_current_turn] + '.\nНазывайте букву!')
                    return
                
            if message[1:10] == "resetcity":
                if sender in __USERNAME_TIMES__.keys():
                    del __USERNAME_TIMES__[sender]
                    await reply_channel.send("Ваш город был сброшен.")
                else:
                    await reply_channel.send("Я и так не знаю вашего города. Не стоит беспокоиться за анонимность)")
                return
            
            if message[1:5] == "time":
                if not sender in __USERNAME_TIMES__.keys():
                    await reply_channel.send(f"{msg.author.mention}, какой у вас город?")
                    current_session.listen_citytime = True
                    current_session.listen_citytime_username = sender
                    return
                else:
                    city_name = rus_letters_lower(__USERNAME_TIMES__[sender])
                    f = io.open("citycodes_yatime.txt", mode="r", encoding="utf-8")
                    city_code = None
                    for line in f:
                        line = rus_letters_lower(line[:-1])
                        sp = line.index(" ")
                        if line[sp+1:] == city_name:
                            city_code = line[:sp]
                            f.close()
                            break
                    else:
                        await reply_channel.send("Не могу найти такой город. Попробуйте другой поблизости с вашим.")
                        f.close()
                        return
                    response = requests.get("https://yandex.com/time/sync.json?geo=" + city_code)
                    json = response.json()
                    t_str = datetime.datetime.fromtimestamp((json["time"] + json["clocks"][city_code]["offset"] - msk_offset) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    dateend = t_str.index(" ")
                    month = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
                    day = int(t_str[0:2])
                    year = int(t_str[6:10])
                    emb = discord.Embed(title="Точное время", colour=discord.Colour.green())
                    emb.add_field(name="Город:", value=__USERNAME_TIMES__[sender], inline=True)
                    emb.add_field(name="Время:", value=t_str[dateend+1:], inline=True)
                    emb.add_field(name="Дата:", value=f"{day} {month[int(t_str[3:5])]}, {year}")
                    emb.add_field(name="Сбросить город", value="Чтобы сбросить свой город, отправьте команду .resetcity",inline=False)
                    emb.set_footer(text="Данные предоставлены сервисом Яндекс.Время")
                    await reply_channel.send(embed=emb)
                    return

        
        if sender == current_session.listen_citytime_username:
            city_name = rus_letters_lower(message)
            f = io.open("citycodes_yatime.txt", mode="r", encoding="utf-8")
            city_code = None
            for line in f:
                line = rus_letters_lower(line[:-1])
                sp = line.index(" ")
                if line[sp+1:] == city_name:
                    city_code = line[:sp]
                    f.close()
                    break
            else:
                await reply_channel.send("Не могу найти такой город. Попробуйте другой поблизости с вашим.")
                f.close()
                return
            response = requests.get("https://yandex.com/time/sync.json?geo=" + city_code)
            json = response.json()
            t_str = datetime.datetime.fromtimestamp((json["time"] + json["clocks"][city_code]["offset"] - msk_offset) / 1000).strftime('%d-%m-%Y %H:%M:%S')
            dateend = t_str.index(" ")
            month = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            day = int(t_str[0:2])
            year = int(t_str[6:10])
            emb = discord.Embed(title="Точное время", colour=discord.Colour.green())
            emb.add_field(name="Город:", value=message, inline=True)
            emb.add_field(name="Время:", value=t_str[dateend+1:], inline=True)
            emb.add_field(name="Дата:", value=f"{day} {month[int(t_str[3:5])]}, {year}", inline=True)
            emb.add_field(name="Сбросить город", value="Чтобы сбросить свой город, отправьте команду .resetcity",inline=False)
            emb.set_footer(text="Данные предоставлены сервисом Яндекс.Время")
            await reply_channel.send(embed=emb)
            current_session.listen_citytime = False
            current_session.listen_citytime_username = None
            __USERNAME_TIMES__[sender] = message
            return
    
        if current_session.polechudes_status == 'creating_lobby':
            if message == '+':
                if sender in current_session.polechudes_banlist:
                    await reply_channel.send(f'{msg.author.mention}, Так как вы были кикнуты из лобби, вы не можете зайти туда же. Дождитесь начала следующей игры.')
                    return
                
                if sender in current_session.polechudes_players:
                    await reply_channel.send(f'{msg.author.mention}, вы уже играете. Нет смысла добавляться дважды.')
                    return

                current_session.polechudes_players.append(sender)
                await reply_channel.send(f'{msg.author.mention} добавлен в лобби')
                return
            
            if message[0:5] == '.kick':
                player_kicked = 0
                player = message[7:len(message)]
                if (player == sender):
                    await reply_channel.send(f'{msg.author.mention}, вы не можете кикнуть самого себя.')
                    return

                if sender == current_session.polechudes_lobbycreator:
                    if player in current_session.polechudes_players:
                        del current_session.polechudes_players[current_session.polechudes_players.index(player)]
                        await reply_channel.send(f'{msg.author.mention} был кикнут лидером лобби.')
                        current_session.polechudes_banlist.append(player)
                        player_kicked = 1
                else:
                    await reply_channel.send('Вы не можете кикать игроков, так как не являетесь создателем лобби.')
                    return
                
                if player_kicked == 0:
                    await reply_channel.send(f'Не удалось кикнуть игрока {msg.author.mention}. Возможно, он сейчас не играет.')
                    return

            if message == '.begin':
                if sender == current_session.polechudes_lobbycreator:
                    current_session.polechudes_status = 'playing'
                    await reply_channel.send('Начинаем игру!')
                else:
                    await reply_channel.send(f'{msg.author.mention}, вы не можете начать игру, так как не являетесь лидером лобби.')

        if current_session.polechudes_status == 'playing':
            if current_session.polechudes_current_turn == -1:
                questionfile=                           io.open('polechudes_questions.txt', mode='r', encoding='utf-8')
                answerfile=                             io.open('polechudes_answers.txt', mode='r', encoding='utf-8')
                lines_questionfile=                     questionfile.readlines()
                lines_answerfile=                       answerfile.readlines()
                question_num=                           random.randint(0, len(lines_questionfile) - 1)
                current_session.polechudes_question=    lines_questionfile[question_num]
                current_session.polechudes_word=        lines_answerfile[question_num]
                
                questionfile.close()
                answerfile.close()
                await reply_channel.send('Внимание, вопрос!\n' + current_session.polechudes_question + '\n' + str(len(current_session.polechudes_word) - 1) + ' букв.\nСейчас очередь @' + current_session.polechudes_players[0] + '\nНазывайте букву!\nВы так же можете ввести слово, введя команду .word слово.')
                current_session.polechudes_current_turn = 0
                return

            if message[0:5] == '.kick':
                player_kicked = 0
                player = message[7:len(message)]
                if (player == sender):
                    await reply_channel.send(f'{msg.author.mention}, вы не можете кикнуть самого себя.')
                    return

                if sender == current_session.polechudes_lobbycreator:
                    if player in current_session.polechudes_players:
                        del current_session.polechudes_players[current_session.polechudes_players.index(player)]
                        await reply_channel.send(f'{msg.author.mention} был кикнут лидером лобби.')
                        current_session.polechudes_banlist.append(player)
                        player_kicked = 1
                else:
                    await reply_channel.send('Вы не можете кикать игроков, так как не являетесь создателем лобби.')
                    return
                
                if player_kicked == 0:
                    await reply_channel.send(f'Не удалось кикнуть игрока {msg.author.mention}. Возможно, он сейчас не играет.')
                    return

            if sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
                if len(message) > 1 and sender == current_session.polechudes_players[current_session.polechudes_current_turn] and message[0:5] != u'.word':
                    await reply_channel.send(f'{msg.author.mention}, введите русскую букву, чтобы ответ был засчитан.')
                    return
                if len(message) == 1 and  message not in 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮйцукенгшщзхъфывапролджэячсмитьбю':
                    await reply_channel.send(f'{msg.author.mention}, введите русскую букву, чтобы ответ был засчитан.')
                    return
            if message[0:5] == u'.word' and sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
                word = rus_letters_upper(message[6:len(message)])
                if word + '\n' == current_session.polechudes_word:
                    await reply_channel.send('Верно, это слово ' + rus_letters_upper(word) + '!\nИгра окончена')
                    current_session.polechudes_status=             u'not_playing'
                    current_session.polechudes_lobbycreator=       u'null'
                    current_session.polechudes_players=            []
                    current_session.polechudes_banlist=            []
                    current_session.polechudes_word=               u'null'
                    current_session.polechudes_current_turn=       -1
                    current_session.polechudes_question=           u'null'
                    current_session.polechudes_guessed_letters=    u''
                    current_session.polechudes_used_letters=       u''
                    return
                else:
                    await reply_channel.send('Нет, это не то слово.')
                    current_session.polechudes_current_turn += 1
                if (len(current_session.polechudes_players) == current_session.polechudes_current_turn):
                    current_session.polechudes_current_turn = 0
                    
                await reply_channel.send('@' + current_session.polechudes_players[current_session.polechudes_current_turn] + ', ваш ход. Называйте букву!\nВы так же можете ввести слово, введя команду .word слово.')
                return

            if len(message) == 1 and sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
                upper_message = rus_letters_upper(message)
            
                if upper_message in current_session.polechudes_guessed_letters:
                    await reply_channel.send('Буква ' + upper_message + ' уже была отгадана')
                    return
                
                if upper_message in current_session.polechudes_used_letters:
                    await reply_channel.send('Вы уже называли букву ' + upper_message)
                    return

                if upper_message in current_session.polechudes_word:
                    current_session.polechudes_guessed_letters += upper_message * current_session.polechudes_word.count(upper_message)
                    unguessed_word = PC_word_to_unguessed(current_session.polechudes_word, current_session.polechudes_guessed_letters)
                    await reply_channel.send('Откройте букву ' + upper_message + '!\n' + unguessed_word)
                else:
                    await reply_channel.send('Извините, буквы ' + upper_message + ' нет в слове.')
                    current_session.polechudes_used_letters += upper_message
                    
                current_session.polechudes_current_turn += 1
                if (len(current_session.polechudes_players) == current_session.polechudes_current_turn):
                    current_session.polechudes_current_turn = 0
                    
                if len(current_session.polechudes_guessed_letters) < len(current_session.polechudes_word) - 1:
                    await reply_channel.send('@' + current_session.polechudes_players[current_session.polechudes_current_turn] + ', ваш ход. Называйте букву!\nВы так же можете ввести слово, введя команду .word слово.')
                else:
                    await reply_channel.send('Слово разгадано! Это ' + current_session.polechudes_word + '\nИгра окончена!')
                    current_session.polechudes_status=             u'not_playing'
                    current_session.polechudes_lobbycreator=       u'null'
                    current_session.polechudes_players=            []
                    current_session.polechudes_banlist=            []
                    current_session.polechudes_word=               u'null'
                    current_session.polechudes_current_turn=       -1
                    current_session.polechudes_question=           u'null'
                    current_session.polechudes_guessed_letters=    u''
                    current_session.polechudes_used_letters=       u''
                return
        

class session(object):
    def __init__(self, chat_id):
        self.chat_id=                       chat_id
        self.polechudes_status=             u'not_playing'
        self.polechudes_lobbycreator=       u'null'
        self.polechudes_players=            []
        self.polechudes_banlist=            []
        self.polechudes_word=               u'null'
        self.polechudes_current_turn=       -1
        self.polechudes_question=           u'null'
        self.polechudes_guessed_letters=    u''
        self.polechudes_used_letters=       u''
        self.listen_citytime=               False
        self.listen_citytime_username=      None
        self.is_playing_gachi=              False
        self.last_message=                  {}
        self.speechsettings=                apihost_voice_settings()
        #self.meme_publics=                  ["eternalclassic", "reddit", "roflds", "jumoreski", "kartinkothread", "afrosidemoon", "lookpage", "qubllc", "ru2ch", "cringey", "karkb", "ru9gag"]
        self.meme_publics=                  []

class apihost_voice_settings(object):
    speaker = "anton_samokhvalov"
    speed = 1.0
    emotion = "good" #emotions: neutral, good, evil
    def set_settings(self, **kwargs):
        for k in kwargs.keys():
            val = kwargs[k]

            if k == "speaker":
                if val == "male":
                    self.speaker = "anton_samokhvalov"
                if val == "female":
                    self.speaker = "oksana"

            if k == "speed":
                self.speed = val

            if k == "emotion":
                self.emotion = val

    def gen_http_request(self, text):
        #text = text.replace(" ", "%20")
        return f"https://apihost.ru/php/app.php?&text={text}&format=mp3&lang=ru-RU&speed={self.speed}&emotion={self.emotion}&speaker={self.speaker}&robot=1"

def insertSession(ssn):
    global __SESSIONS__
    __SESSIONS__.append(ssn)

def findSessionByID(session_id):
    global __SESSIONS__
    for i in range(len(__SESSIONS__)):
        if (__SESSIONS__[i].chat_id == session_id):
            return __SESSIONS__[i]
    return None


JustBot = MyClient()
JustBot.run(TOKEN)
