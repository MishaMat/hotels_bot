import telebot
import requests
import os
from flask import Flask, request

TOKEN = "2115889189:AAHEN0nscnZzTFcEXOTUTvzKxLRcVYcXRfY"
url = "https://hotels4.p.rapidapi.com/locations/v2/search"
url2 = "https://hotels4.p.rapidapi.com/properties/list"
photo_url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': "da80c3142emsh88cb3bd3e4b0ae8p150e0ajsn445a6569ca9c"
}

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
history = ""


def menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    lowprice = telebot.types.KeyboardButton("lowprice")
    highprice = telebot.types.KeyboardButton("highprice")
    bestdeal = telebot.types.KeyboardButton("bestdeal")
    history = telebot.types.KeyboardButton("history")
    end_program = telebot.types.KeyboardButton("Exit")
    markup.add(lowprice, highprice, bestdeal, history, end_program)
    return markup


def exception_decorator(func):
    def wrapped(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            bot.send_message(args[0].chat.id, "Something went wrong\n try again")
            bot.send_message(args[0].chat.id, "Select button:", reply_markup=menu())

    return wrapped


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Hello✌️\n"
                                      "I'm bot which will help you to find best hotels all around the world.")
    global history
    history = ""
    bot.send_message(message.chat.id, "Select button:", reply_markup=menu())


@bot.message_handler(commands=['help'])
def help_info(message):
    bot.send_message(message.chat.id, "type command - /start\n"
                                      " lowprice  - show the cheapest hotels\n"
                                      " highprice - show the most expensive hotels\n"
                                      " bestdeal  - show most comfortable hotels for you\n"
                                      " history   - show your search history\n"
                                      " exit      - bye-bye\n"
                                      "\nLet's go! ")


@exception_decorator
@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == "lowprice" or message.text == "highprice" or message.text == "bestdeal":
        msg = bot.send_message(message.chat.id, "type city:")
        bot.register_next_step_handler(msg, get_city_name, sort_type=message.text)
    elif message.text == "history":
        global history
        bot.send_message(message.chat.id, history)
    elif message.text == "Exit":
        bot.send_message(message.chat.id, "See ya!")
    else:
        bot.send_message(message.chat.id, "Select button:", reply_markup=menu())


@exception_decorator
def get_city_name(message, sort_type):
    response = requests.request("GET", url, headers=headers, params={"query": message.text})
    if response.json()['moresuggestions'] == 10:
        if sort_type == 'bestdeal':
            msg = bot.send_message(message.chat.id, "type price diapason:\n"
                                                    "example: 50-100")
            bot.register_next_step_handler(msg, get_price_for_bestdeal, city=message.text.lower())
        else:
            querystring = {"query": message.text.lower()}
            response = requests.request("GET", url, headers=headers, params=querystring)
            querystring2 = {"destinationId": response.json()["suggestions"][0]["entities"][0]["destinationId"]}
            response2 = requests.request("GET", url2, headers=headers, params=querystring2)
            max_num = len(response2.json()['data']['body']['searchResults']['results'])
            msg = bot.send_message(message.chat.id, "how many hotels to show:\n"
                                                    f"(not more than {max_num})")
            bot.register_next_step_handler(msg, get_hotels_by_city, city=message.text.lower(), sort_type=sort_type,
                                           max_num=max_num)
    else:
        msg = bot.send_message(message.chat.id, "wrong city name\ntry again:")
        bot.register_next_step_handler(msg, get_city_name, sort_type=sort_type)


@exception_decorator
def get_price_for_bestdeal(message, city):
    price = [int(i) for i in message.text.split('-')]
    msg = bot.send_message(message.chat.id, 'type distance from citycentre in miles\n'
                                            'or zero if doesn\'t matters:')
    bot.register_next_step_handler(msg, get_diapason_for_bestdeal, city=city, price=price)


def get_diapason_for_bestdeal(message, city, price):
    try:
        diapason = float(message.text)
    except ValueError:
        diapason = ''
        for i in message.text:
            if i.isdigit():
                diapason += i
            else:
                diapason += '.'
    querystring = {"query": city}
    response = requests.request("GET", url, headers=headers, params=querystring)
    querystring2 = {"destinationId": response.json()["suggestions"][0]["entities"][0]["destinationId"]}
    response2 = requests.request("GET", url2, headers=headers, params=querystring2)
    max_num = len(response2.json()['data']['body']['searchResults']['results'])
    msg = bot.send_message(message.chat.id, "how many hotels to show:\n"
                                            f"(not more than {max_num})")
    bot.register_next_step_handler(msg, get_hotels_by_city, city=city, price=price,
                                   diapason=float(diapason), max_num=max_num)


@exception_decorator
def get_hotels_by_city(message, city, max_num, sort_type=None, diapason=None, price=None):
    if int(message.text) <= int(max_num):
        querystring = {"query": city}
        response = requests.request("GET", url, headers=headers, params=querystring)
        querystring2 = {"destinationId": response.json()["suggestions"][0]["entities"][0]["destinationId"]}
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        yes = telebot.types.KeyboardButton("Yes")
        no = telebot.types.KeyboardButton("No")
        markup.add(yes, no)
        msg = bot.send_message(message.chat.id, "Show photo:", reply_markup=markup)
        global history
        history += f"------------------\nCity: {city}\n"
        if sort_type:
            if sort_type == "lowprice":
                querystring2["sortOrder"] = "PRICE"
            elif sort_type == "highprice":
                querystring2["sortOrder"] = "PRICE_HIGHEST_FIRST"
            history += f"Sort: {sort_type} first\n"
            bot.register_next_step_handler(msg, show_hotels, query=querystring2, number=message.text)
        elif diapason:
            history += f"Sort: bestdeal\n" \
                       f"Price: {price[0]}-{price[1]}\n" \
                       f"City centre: {diapason} miles\n"
            bot.register_next_step_handler(msg, show_hotels, query=querystring2, number=message.text, diapason=diapason,
                                           max_num=max_num, price=price)
    else:
        msg = bot.send_message(message.chat.id, f"(not more than {max_num})")
        bot.register_next_step_handler(msg, get_hotels_by_city, city=message.text.lower(), sort_type=sort_type,
                                       max_num=max_num)


@exception_decorator
def show_hotels(message, query, number, diapason=None, max_num=None, price=None):
    response2 = requests.request("GET", url2, headers=headers, params=query)
    global history
    if diapason:
        counter = 0
        for i in range(int(max_num)):
            if counter == int(number):
                break
            hotel_info = response2.json()['data']['body']["searchResults"]["results"][i]
            if 'ratePlan' in hotel_info and \
                    'price' in hotel_info['ratePlan'] and \
                    'current' in hotel_info['ratePlan']['price']:
                if not price[0] <= int(hotel_info['ratePlan']['price']['current'][1:]) <= price[1]:
                    continue
            if 'landmarks' in hotel_info:
                for elem in hotel_info['landmarks']:
                    if elem['label'] == 'City center' and float(elem['distance'][:-5]) <= diapason:
                        break
                else:
                    continue
            counter += 1
            history += f" {counter}.{hotel_info['name']}\n"
            collecting_data(message.chat.id, hotel_info=hotel_info, show_photos=message.text)
    else:
        for i in range(int(number)):
            hotel_info = response2.json()['data']['body']["searchResults"]["results"][i]
            history += f" {i + 1}.{hotel_info['name']}\n"
            collecting_data(message.chat.id, hotel_info=hotel_info, show_photos=message.text)
    bot.send_message(message.chat.id, "Select button:", reply_markup=menu())


def collecting_data(chat_id, hotel_info, show_photos):
    if show_photos.lower() == 'yes':
        photo_query = {'id': str(hotel_info['id'])}
        photo_response = requests.request("GET", photo_url, headers=headers, params=photo_query)
        photo_result = str(photo_response.json()['hotelImages'][0]['baseUrl'])[:-11:] + '.jpg'
        bot.send_photo(chat_id, photo_result)
    result = f"{hotel_info['name']}\n" \
             f" -stars: {hotel_info['starRating']}\n"
    if 'streetAddress' in hotel_info['address']:
        result += f" -address:{hotel_info['address']['streetAddress']}\n"
    else:
        result += f" -address:{hotel_info['address']['locality']}\n"
    for j in hotel_info['landmarks']:
        result += f" -{j['distance']} from {j['label']}\n"
    if 'ratePlan' in hotel_info and \
            'price' in hotel_info['ratePlan'] and \
            'current' in hotel_info['ratePlan']['price']:
        result += f" -average price per night: {hotel_info['ratePlan']['price']['current']}"
    bot.send_message(chat_id, result)


# bot.polling(none_stop=True)
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://mysterious-falls-17582.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
