#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim:fileencoding=utf-8
import random
import sys
import time
import telepot as tp
from telepot.loop import MessageLoop
import io
import datetime
import requests

def set_telepot_socks_proxy(url, username=None, password=None):
    from urllib3.contrib.socks import SOCKSProxyManager
    from telepot.api import _default_pool_params, _onetime_pool_params
    tp.api._onetime_pool_spec = (SOCKSProxyManager, dict(proxy_url=url, username=username, password=password, **_onetime_pool_params))
    tp.api._pools['default'] = SOCKSProxyManager(url, username=username, password=password, **_default_pool_params)

set_telepot_socks_proxy("socks5h://94.103.81.38:1088")

#global variables
__SESSIONS__ = []
__TOKEN__    = 'token_here'
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
            new_word += '[*] '
    return new_word

def handle(msg):
    global __SESSIONS__
    content_type, chat_type, chat_id = tp.glance(msg)
    #debug output
    print(content_type, chat_type, chat_id, end=" ")
    if "username" in msg['from'].keys():
        print(msg['from']['username'], end=" ")
    if content_type == "text":
        print(msg['text'])
    
    if findSessionByID(chat_id).chat_id == -1:
        insertSession(session(chat_type, chat_id))
    sender = ""
    if "username" in msg['from'].keys():
        sender = str(msg['from']['username'])
    current_session = findSessionByID(chat_id)
    message = ""

    if (content_type == 'text'):
        #handling the command
        message = msg['text']
        #hidden commands
        if message == "/nudes":
            stickerpack = JustBot.getStickerSet('erotyanstickers')
            sticker = random.choice(stickerpack['stickers'])
            JustBot.sendSticker(chat_id, sticker['file_id'])
            return
        if message[0] == '/':
            if (message[1:6] == 'start' or message[1:5] == 'help'):
                printHelp(chat_id)
                return
            
            if (message[1:5] == 'infa'):
                JustBot.sendMessage(chat_id, '@' + sender + u', напиши факт')
                current_session.IQ_insert(sender)
                return
            
            #creating polechudes session
            if (message[0:11] == '/polechudes'):
                if current_session.polechudes_status == 'not_playing':
                    JustBot.sendMessage(chat_id, 'Начинаем игру.\nТе, кто хотят играть, пишите + в чат.\nЧтобы начать игру, создатель текущей игры должен написать /begin\nДля того, чтобы кикнуть игрока из игры, создатель лобби должен написать /kick @username до того, как игра начнется.\nВы можете выйти из игры в любой момент, написав /exit.')
                    current_session.polechudes_status = 'creating_lobby'
                    current_session.polechudes_lobbycreator = sender
                    current_session.polechudes_players.append(sender)

                elif current_session.polechudes_status == 'playing':
                    JustBot.sendMessage(chat_id, 'Поле Чудес уже идет. Дождитесь конца текущей игры.')

                elif current_session.polechudes_status == 'creating_lobby':
                    JustBot.sendMessage(chat_id, 'Уже идет создание лобби. Присоединяйтесь быстрее!')
            
            if message == '/exit' and sender in current_session.polechudes_players:
                if current_session.polechudes_status == 'creating_lobby':
                    del current_session.polechudes_players[current_session.polechudes_players.index(sender)]
                    JustBot.sendMessage(chat_id, 'Игрок @' + sender + ' вышел.')
                    if len(current_session.polechudes_players) == 0:
                        JustBot.sendMessage(chat_id, 'Так как все игроки вышли, игра окончена.')
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
                    JustBot.sendMessage(chat_id, 'Игрок @' + sender + ' вышел')
                    if len(current_session.polechudes_players) == 0:
                        JustBot.sendMessage(chat_id, 'Так как все игроки вышли, игра окончена.')
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
                    JustBot.sendMessage(chat_id, 'Текущий ход передается @' + current_session.polechudes_players[current_session.polechudes_current_turn] + '.\nНазывайте букву!')
                    return
            if message[1:10] == "resetcity":
                if sender in __USERNAME_TIMES__.keys():
                    del __USERNAME_TIMES__[sender]
                    JustBot.sendMessage(chat_id, "Ваш город был сброшен.")
                else:
                    JustBot.sendMessage(chat_id, "Я и так не знаю вашего города. Не стоит беспокоиться за анонимность)")
                return
            if message[1:5] == "time":
                if not sender in __USERNAME_TIMES__.keys():
                    JustBot.sendMessage(chat_id, "@"+sender+", какой у вас город?")
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
                        JustBot.sendMessage(chat_id, "Не могу найти такой город. Попробуйте другой поблизости с вашим.")
                        f.close()
                        return
                    response = requests.get("https://yandex.com/time/sync.json?geo=" + city_code)
                    json = response.json()
                    t_str = datetime.datetime.fromtimestamp((json["time"] + json["clocks"][city_code]["offset"] - msk_offset) / 1000).strftime('%d-%m-%Y %H:%M:%S')
                    dateend = t_str.index(" ")
                    month = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
                    day = int(t_str[0:2])
                    year = int(t_str[6:10])
                    JustBot.sendMessage(chat_id, "Данные предоставлены сервисом Яндекс.Время\n\nГород: " + __USERNAME_TIMES__[sender] + "\nВремя: " + t_str[dateend+1:] + "\nДата: " + str(day) + " " + month[int(t_str[3:5])] + ", " + str(year) + "\n\nЧтобы сбросить ваш город, отправьте команду /resetcity")
                    return

        #setting city to nickname
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
                JustBot.sendMessage(chat_id, "Не могу найти такой город. Попробуйте другой поблизости с вашим.")
                f.close()
                return
            response = requests.get("https://yandex.com/time/sync.json?geo=" + city_code)
            json = response.json()
            t_str = datetime.datetime.fromtimestamp((json["time"] + json["clocks"][city_code]["offset"] - msk_offset) / 1000).strftime('%d-%m-%Y %H:%M:%S')
            dateend = t_str.index(" ")
            month = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            day = int(t_str[0:2])
            year = int(t_str[6:10])
            JustBot.sendMessage(chat_id, "Данные предоставлены сервисом Яндекс.Время\n\nГород: " + message + "\nВремя: " + t_str[dateend+1:] + "\nДата: " + str(day) + " " + month[int(t_str[3:5])] + ", " + str(year) + "\n\nЧтобы сбросить ваш город, отправьте команду /resetcity")
            current_session.listen_citytime = False
            current_session.listen_citytime_username = None
            __USERNAME_TIMES__[sender] = message
            return


    #checking the infa queue
    if current_session.IQ_find_user_ind(sender) != -1:
        fact = msg['text']
        sm_let_fact = rus_letters_lower(fact)
        danil_names = ['даня', 'данил', 'даниил', 'данила', 'данон']
        answers = ['Вероятность того, что ' + fact, fact + ' с вероятностью', 'Шанс того, что ' + fact]
        infa = random.randint(0, 100)

        for i in range(len(danil_names)):
            if sm_let_fact.find(danil_names[i], 0, len(sm_let_fact)) != -1:
                infa = 100
                break
        phrase = answers[random.randint(0, 2)] + ' ' + str(infa) + '%'

        JustBot.sendMessage(chat_id, phrase)
        current_session.IQ_delete_user(sender)
        return

    #playing polechudes
    if current_session.polechudes_status == 'creating_lobby':
        if message == '+':
            if sender in current_session.polechudes_banlist:
                JustBot.sendMessage(chat_id, '@' + sender + ', Так как вы были кикнуты из лобби, вы не можете зайти туда же. Дождитесь начала следующей игры.')
                return
            
            if sender in current_session.polechudes_players:
                JustBot.sendMessage(chat_id, '@' + sender + ', вы уже играете. Нет смысла добавляться дважды.')
                return

            current_session.polechudes_players.append(sender)
            JustBot.sendMessage(chat_id, 'Игрок @' + sender + ' добавлен в лобби')
            return
        
        if message[0:5] == '/kick':
            player_kicked = 0
            player = message[7:len(message)]
            if (player == sender):
                JustBot.sendMessage(chat_id, '@' + sender + ', вы не можете кикнуть самого себя.')
                return

            if sender == current_session.polechudes_lobbycreator:
                if player in current_session.polechudes_players:
                    del current_session.polechudes_players[current_session.polechudes_players.index(player)]
                    JustBot.sendMessage(chat_id, 'Игрок @' + player + ' был кикнут лидером лобби.')
                    current_session.polechudes_banlist.append(player)
                    player_kicked = 1
            else:
                JustBot.sendMessage(chat_id, 'Вы не можете кикать игроков, так как не являетесь создателем лобби.')
                return
            
            if player_kicked == 0:
                JustBot.sendMessage(chat_id, 'Не удалось кикнуть игрока @' + player + '. Возможно, он сейчас не играет.')
                return

        if message == '/begin':
            if sender == current_session.polechudes_lobbycreator:
                current_session.polechudes_status = 'playing'
                JustBot.sendMessage(chat_id, 'Начинаем игру!')
            else:
                JustBot.sendMessage(chat_id, '@' + sender + ', вы не можете начать игру, так как не являетесь лидером лобби.')
    
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
            JustBot.sendMessage(chat_id, 'Внимание, вопрос!\n' + current_session.polechudes_question + '\n' + str(len(current_session.polechudes_word) - 1) + ' букв.\nСейчас очередь @' + current_session.polechudes_players[0] + '\nНазывайте букву!\nВы так же можете ввести слово, введя команду /word слово.')
            current_session.polechudes_current_turn = 0
            return
        
        if sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
            if len(message) > 1 and sender == current_session.polechudes_players[current_session.polechudes_current_turn] and message[0:5] != u'/word':
                JustBot.sendMessage(chat_id, '@' + sender + ', введите русскую букву, чтобы ответ был засчитан.')
                return
            if len(message) == 1 and not message in 'ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮйцукенгшщзхъфывапролджэячсмитьбю':
                JustBot.sendMessage(chat_id, '@' + sender + ', введите русскую букву, чтобы ответ был засчитан.')
        if message[0:5] == u'/word' and sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
            word = rus_letters_upper(message[6:len(message)])
            if word + '\n' == current_session.polechudes_word:
                JustBot.sendMessage(chat_id, 'Верно, это слово ' + rus_letters_upper(word) + '!\nИгра окончена')
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
                JustBot.sendMessage(chat_id, 'Нет, это не то слово.')
                current_session.polechudes_current_turn += 1
            if (len(current_session.polechudes_players) == current_session.polechudes_current_turn):
                current_session.polechudes_current_turn = 0
                
            JustBot.sendMessage(chat_id, '@' + current_session.polechudes_players[current_session.polechudes_current_turn] + ', ваш ход. Называйте букву!\nВы так же можете ввести слово, введя команду /word слово.')
            return

        if len(message) == 1 and sender == current_session.polechudes_players[current_session.polechudes_current_turn]:
            upper_message = rus_letters_upper(message)
        
            if upper_message in current_session.polechudes_guessed_letters:
                JustBot.sendMessage(chat_id, 'Буква ' + upper_message + ' уже была отгадана')
                return
            
            if upper_message in current_session.polechudes_used_letters:
                JustBot.sendMessage(chat_id, 'Вы уже называли букву ' + upper_message)
                return

            if upper_message in current_session.polechudes_word:
                current_session.polechudes_guessed_letters += upper_message * current_session.polechudes_word.count(upper_message)
                unguessed_word = PC_word_to_unguessed(current_session.polechudes_word, current_session.polechudes_guessed_letters)
                JustBot.sendMessage(chat_id, 'Откройте букву ' + upper_message + '!\n' + unguessed_word)
            else:
                JustBot.sendMessage(chat_id, 'Извините, буквы ' + upper_message + ' нет в слове.')
                current_session.polechudes_used_letters += upper_message
                
            current_session.polechudes_current_turn += 1
            if (len(current_session.polechudes_players) == current_session.polechudes_current_turn):
                current_session.polechudes_current_turn = 0
                
            if len(current_session.polechudes_guessed_letters) < len(current_session.polechudes_word) - 1:
                JustBot.sendMessage(chat_id, '@' + current_session.polechudes_players[current_session.polechudes_current_turn] + ', ваш ход. Называйте букву!\nВы так же можете ввести слово, введя команду /word слово.')
            else:
                JustBot.sendMessage(chat_id, 'Слово разгадано! Это ' + current_session.polechudes_word + '\nИгра окончена!')
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
        


def printHelp(chat_id):
    JustBot.sendMessage(chat_id, 'Доступные команды:\n\n1) /infa - Выводит вероятность названного события/факта. Прям как шар-гадалка\n\n2) /polechudes - Запуск игры Поле Чудес. Можно играть как в приватном чате, так и в групповом с друзьями. Крутите барабан!\n\n3) /time - Узнать точное время в вашем городе.\n\n4) /help - Вывести список команд бота.')

class session(object):
    def __init__(self, chat_type, chat_id):
        self.chat_type=                     chat_type
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
    return session('null', -1)

random.seed(time.time())
JustBot = tp.Bot(__TOKEN__)
MessageLoop(JustBot, handle).run_as_thread()
print("JustBot started")
while 1:
    time.sleep(10)
