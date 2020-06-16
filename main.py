TOKEN = "token_here"
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

import discord
import io
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
        sender = str(msg.author)
        if findSessionByID(reply_channel.id) == None:
            insertSession(session(reply_channel.id))
        current_session = findSessionByID(reply_channel.id)
        #debug output
        #print(current_session.chat_id)
        #print(current_session.infa_queue)
        print("Message from {0.author}: {0.content}".format(msg))

        #hidden messages
        if message == "/stop":
            try:
                voice_channel = msg.author.voice.channel
            except:
                await reply_channel.send("Войдите в голосовой канал, чтобы использовать эту команду")
                return

            current_session.is_playing_gachi = False
            return

        if message == "/gachi":
            if current_session.is_playing_gachi:
                reply_channel.send("Я уже воспроизвожу")
                return
            try:
                temp = msg.author.voice.channel
            except Not:
                await reply_channel.send("Войдите в голосовой канал, чтобы использовать эту команду")
                return
            songs = [
                "MORGENSHTERN feat. Элджей - ♂Cock♂dillac",
                "Нурминский - Валим на ♂gay party♂",
                "♂Cumming♂ in the 90s",
                "Бутырка - ♂Cum♂ттестат"
            ]
            song = random.choice(songs)
            # try:
            #     voice_channel = msg.author.voice.channel
            # except:
            #     await reply_channel.send("♂♂♂Я уже воспроизвожу♂♂♂")
            #     return
            voice_channel = msg.author.voice.channel
            await reply_channel.send("Сейчас играет: " + song)
            vc = await voice_channel.connect()
            vc.play(discord.FFmpegPCMAudio(source='GachiSongs/' + song + ".mp3", executable="C:/ffmpeg/ffmpeg.exe"), after=lambda e: print('done', e))
            current_session.is_playing_gachi = True
            while vc.is_playing() and current_session.is_playing_gachi:
                await asyncio.sleep(1)
            vc.stop()
            await reply_channel.send("♂Gay party♂ кончилась")
            await vc.disconnect()
            return
        if message[0] == '/':
            if (message[1:6] == 'start' or message[1:5] == 'help'):
                await reply_channel.send('Доступные команды:\n\n1) /infa - Выводит вероятность названного события/факта. Прям как шар-гадалка\n\n2) /polechudes - Запуск игры Поле Чудес. Можно играть как в приватном чате, так и в групповом с друзьями. Крутите барабан!\n\n3) /time - Узнать точное время в вашем городе.\n\n4) /help - Вывести список команд бота.')
                return

            if (message[1:5] == 'infa'):
                current_session.IQ_insert(sender)
                print(current_session.infa_queue)
                await reply_channel.send('@' + sender + u', напиши факт')
                return

            #creating polechudes session
            if (message[0:11] == '/polechudes'):
                if current_session.polechudes_status == 'not_playing':
                    await reply_channel.send('Начинаем игру.\nТе, кто хотят играть, пишите + в чат.\nЧтобы начать игру, создатель текущей игры должен написать /begin\nДля того, чтобы кикнуть игрока из игры, создатель лобби должен написать /kick @username до того, как игра начнется.\nВы можете выйти из игры в любой момент, написав /exit.')
                    current_session.polechudes_status = 'creating_lobby'
                    current_session.polechudes_lobbycreator = sender
                    current_session.polechudes_players.append(sender)
                elif current_session.polechudes_status == 'playing':
                    await reply_channel.send('Поле Чудес уже идет. Дождитесь конца текущей игры.')

                elif current_session.polechudes_status == 'creating_lobby':
                    await reply_channel.send('Уже идет создание лобби. Присоединяйтесь быстрее!')

            if message == '/exit' and sender in current_session.polechudes_players:
                if current_session.polechudes_status == 'creating_lobby':
                    del current_session.polechudes_players[current_session.polechudes_players.index(sender)]
                    await reply_channel.send('Игрок @' + sender + ' вышел.')
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
                    await reply_channel.send('Игрок @' + sender + ' вышел')
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
                    await reply_channel.send("@"+sender+", какой у вас город?")
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
                    await reply_channel.send("Данные предоставлены сервисом Яндекс.Время\n\nГород: " + __USERNAME_TIMES__[sender] + "\nВремя: " + t_str[dateend+1:] + "\nДата: " + str(day) + " " + month[int(t_str[3:5])] + ", " + str(year) + "\n\nЧтобы сбросить ваш город, отправьте команду /resetcity")
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
            await reply_channel.send("Данные предоставлены сервисом Яндекс.Время\n\nГород: " + message + "\nВремя: " + t_str[dateend+1:] + "\nДата: " + str(day) + " " + month[int(t_str[3:5])] + ", " + str(year) + "\n\nЧтобы сбросить ваш город, отправьте команду /resetcity")
            current_session.listen_citytime = False
            current_session.listen_citytime_username = None
            __USERNAME_TIMES__[sender] = message
            return
    
        if current_session.IQ_find_user_ind(sender) != -1:
            #print("I'm here")
            fact = message
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
            current_session.IQ_delete_user(sender)
            return
    
        if current_session.polechudes_status == 'creating_lobby':
            if message == '+':
                if sender in current_session.polechudes_banlist:
                    await reply_channel.send('@' + sender + ', Так как вы были кикнуты из лобби, вы не можете зайти туда же. Дождитесь начала следующей игры.')
                    return
                
                if sender in current_session.polechudes_players:
                    await reply_channel.send('@' + sender + ', вы уже играете. Нет смысла добавляться дважды.')
                    return

                current_session.polechudes_players.append(sender)
                await reply_channel.send('Игрок @' + sender + ' добавлен в лобби')
                return
            
            if message[0:5] == '/kick':
                player_kicked = 0
                player = message[7:len(message)]
                if (player == sender):
                    await reply_channel.send('@' + sender + ', вы не можете кикнуть самого себя.')
                    return

                if sender == current_session.polechudes_lobbycreator:
                    if player in current_session.polechudes_players:
                        del current_session.polechudes_players[current_session.polechudes_players.index(player)]
                        await reply_channel.send('Игрок @' + player + ' был кикнут лидером лобби.')
                        current_session.polechudes_banlist.append(player)
                        player_kicked = 1
                else:
                    await reply_channel.send('Вы не можете кикать игроков, так как не являетесь создателем лобби.')
                    return
                
                if player_kicked == 0:
                    await reply_channel.send('Не удалось кикнуть игрока @' + player + '. Возможно, он сейчас не играет.')
                    return

            if message == '/begin':
                if sender == current_session.polechudes_lobbycreator:
                    current_session.polechudes_status = 'playing'
                    await reply_channel.send('Начинаем игру!')
                else:
                    await reply_channel.send('@' + sender + ', вы не можете начать игру, так как не являетесь лидером лобби.')

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
                await reply_channel.send('Внимание, вопрос!\n' + current_session.polechudes_question + '\n' + str(len(current_session.polechudes_word) - 1) + ' букв.\nСейчас очередь @' + current_session.polechudes_players[0] + '\nНазывайте букву!\nВы так же можете ввести слово, введя команду /word слово.')
                current_session.polechudes_current_turn = 0
                return

            if sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
                if len(message) > 1 and sender == current_session.polechudes_players[current_session.polechudes_current_turn] and message[0:5] != u'/word':
                    await reply_channel.send('@' + sender + ', введите русскую букву, чтобы ответ был засчитан.')
                    return
                if len(message) == 1 and not message in 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮйцукенгшщзхъфывапролджэячсмитьбю':
                    await reply_channel.send('@' + sender + ', введите русскую букву, чтобы ответ был засчитан.')
            if message[0:5] == u'/word' and sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
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
                    
                await reply_channel.send('@' + current_session.polechudes_players[current_session.polechudes_current_turn] + ', ваш ход. Называйте букву!\nВы так же можете ввести слово, введя команду /word слово.')
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
                    await reply_channel.send('@' + current_session.polechudes_players[current_session.polechudes_current_turn] + ', ваш ход. Называйте букву!\nВы так же можете ввести слово, введя команду /word слово.')
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
        self.infa_queue=                    []
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
        self.is_playing_gachi = False
    
    def IQ_insert(self, username):
        self.infa_queue.append(username)

    def IQ_find_user_ind(self, username):
        for i in range(len(self.infa_queue)):
            if self.infa_queue[i] == username:
                return i
        return -1

    def IQ_delete_user(self, username):
        del self.infa_queue[self.IQ_find_user_ind(username)]

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
