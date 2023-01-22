import datetime
from geopy.geocoders import Nominatim
import telebot
import requests
import os
from flask import Flask, request

TOKEN = "2115889189:AAHEN0nscnZzTFcEXOTUTvzKxLRcVYcXRfY"
url = "https://hotels4.p.rapidapi.com/locations/v3/search"
url2 = "https://hotels4.p.rapidapi.com/properties/v2/list"

headers = {
    "content-type": "application/json",
    "X-RapidAPI-Key": "da80c3142emsh88cb3bd3e4b0ae8p150e0ajsn445a6569ca9c",
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
}

bot = telebot.TeleBot(TOKEN)
# server = Flask(__name__)
history = ""


def menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    lowprice = telebot.types.KeyboardButton("lowprice")
    recommended = telebot.types.KeyboardButton("recommended")
    bestdeal = telebot.types.KeyboardButton("bestdeal")
    history = telebot.types.KeyboardButton("history")
    end_program = telebot.types.KeyboardButton("Exit")
    markup.add(lowprice, recommended, bestdeal, history, end_program)
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
                                      " recommended - show recommended hotels\n"
                                      " bestdeal  - show most comfortable hotels for you\n"
                                      " history   - show your search history\n"
                                      " exit      - bye-bye\n"
                                      "\nLet's go! ")


@exception_decorator
@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text == "lowprice" or message.text == "recommended" or message.text == "bestdeal":
        msg = bot.send_message(message.chat.id, "type city:")
        bot.register_next_step_handler(msg, get_city_name, sort_type=message.text)
    elif message.text == "history":
        global history
        if history:
            bot.send_message(message.chat.id, history)
        else:
            bot.send_message(message.chat.id, "-history is empty-")
    elif message.text == "Exit":
        bot.send_message(message.chat.id, "See ya!")
    else:
        bot.send_message(message.chat.id, "Select button:", reply_markup=menu())


@exception_decorator
def get_city_name(message, sort_type):
    response = requests.request("GET", url, headers=headers, params={"q": message.text.lower()})
    if response.text:
        if sort_type == 'bestdeal':
            msg = bot.send_message(message.chat.id, "type price diapason:\n"
                                                    "example: 50-100")
            bot.register_next_step_handler(msg, get_price_for_bestdeal, city=message.text.lower())
        else:
            querystring2 = {
                "currency": "USD",
                "destination": {
                    # "coordinates": {"latitude": 49.841537, "longitude": 24.03181}, "regionId": "2175"
                    "coordinates": {"latitude": float(response.json()['sr'][0]['coordinates']['lat']),
                                    "longitude": float(response.json()['sr'][0]['coordinates']['long']),
                                    "regionId": int(response.json()['sr'][0]['gaiaId'])}
                },
                "checkInDate": {
                    "day": datetime.datetime.now().date().day,
                    "month": datetime.datetime.now().date().month,
                    "year": datetime.datetime.now().date().year
                },
                "checkOutDate": {
                    "day": datetime.datetime.now().date().day + 1,
                    "month": datetime.datetime.now().date().month,
                    "year": datetime.datetime.now().date().year
                },
                "rooms": [
                    {
                        "adults": 1
                    }
                ],
                "resultsStartingIndex": 0,
                "resultsSize": 25
            }
            # querystring2 = {"destinationId": response.json()["suggestions"][0]["entities"][0]["destinationId"]}
            response2 = requests.request("POST", url2, headers=headers, json=querystring2)
            # pprint(response2)
            max_num = len(response2.json()['data']['propertySearch']['properties'])
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
    msg = bot.send_message(message.chat.id, 'type distance from citycentre in km\n'
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
    querystring = {"q": city}
    response = requests.request("GET", url, headers=headers, params=querystring)
    querystring2 = {
        "currency": "USD",
        "destination": {
            "coordinates": {"latitude": float(response.json()['sr'][0]['coordinates']['lat']),
                            "longitude": float(response.json()['sr'][0]['coordinates']['long']),
                            "regionId": int(response.json()['sr'][0]['gaiaId'])}
        },
        "checkInDate": {
            "day": datetime.datetime.now().date().day,
            "month": datetime.datetime.now().date().month,
            "year": datetime.datetime.now().date().year
        },
        "checkOutDate": {
            "day": datetime.datetime.now().date().day + 1,
            "month": datetime.datetime.now().date().month,
            "year": datetime.datetime.now().date().year
        },
        "rooms": [
            {
                "adults": 1
            }
        ],
        "resultsStartingIndex": 0,
        "resultsSize": 25,
        "filters": {
            "price": {
                "max": price[1],
                "min": price[0]
            }
        }
    }
    response2 = requests.request("POST", url2, headers=headers, json=querystring2)
    max_num = len(response2.json()['data']['propertySearch']['properties'])
    msg = bot.send_message(message.chat.id, "how many hotels to show:\n"
                                            f"(not more than {max_num})")
    bot.register_next_step_handler(msg, get_hotels_by_city, city=city, price=price,
                                   diapason=float(diapason), max_num=max_num)


@exception_decorator
def get_hotels_by_city(message, city, max_num, sort_type=None, diapason=None, price=None):
    if int(message.text) <= int(max_num):
        querystring = {"q": city}
        response = requests.request("GET", url, headers=headers, params=querystring)
        querystring2 = {
            "currency": "USD",
            "destination": {
                "coordinates": {"latitude": float(response.json()['sr'][0]['coordinates']['lat']),
                                "longitude": float(response.json()['sr'][0]['coordinates']['long']),
                                "regionId": int(response.json()['sr'][0]['gaiaId'])}
            },
            "checkInDate": {
                "day": datetime.datetime.now().date().day,
                "month": datetime.datetime.now().date().month,
                "year": datetime.datetime.now().date().year
            },
            "checkOutDate": {
                "day": datetime.datetime.now().date().day + 1,
                "month": datetime.datetime.now().date().month,
                "year": datetime.datetime.now().date().year
            },
            "rooms": [
                {
                    "adults": 1
                }
            ],
            "resultsStartingIndex": 0,
            "resultsSize": 25,
            "filters": {
                "price": {
                    "max": price[1],
                    "min": price[0]
                }
            }
        }
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        yes = telebot.types.KeyboardButton("Yes")
        no = telebot.types.KeyboardButton("No")
        markup.add(yes, no)
        msg = bot.send_message(message.chat.id, "Show photo:", reply_markup=markup)
        global history
        history += f"------------------\nCity: {city}\n"
        if sort_type:
            if sort_type == "lowprice":
                querystring2["sort"] = "PRICE_LOW_TO_HIGH"
            elif sort_type == "recommended":
                querystring2["sort"] = "PROPERTY_CLASS"
            history += f"Sort: {sort_type} first\n"
            bot.register_next_step_handler(msg, show_hotels, query=querystring2, number=message.text)
        elif diapason or diapason == 0:
            history += f"Sort: bestdeal\n" \
                       f"Price: {price[0]}-{price[1]}\n" \
                       f"City centre: {diapason} km\n"
            bot.register_next_step_handler(msg, show_hotels, query=querystring2, number=message.text, diapason=diapason,
                                           max_num=max_num, price=price)
    else:
        msg = bot.send_message(message.chat.id, f"(not more than {max_num})")
        bot.register_next_step_handler(msg, get_hotels_by_city, city=message.text.lower(), sort_type=sort_type,
                                       max_num=max_num)


@exception_decorator
def show_hotels(message, query, number, diapason=None, max_num=None, price=None):
    response2 = requests.request("POST", url2, headers=headers, json=query)
    global history
    if diapason != 0:
        counter = 0
        for i in range(int(max_num)):
            if counter == int(number):
                break
            hotel_info = response2.json()['data']['propertySearch']['properties'][i]
            if round(hotel_info['destinationInfo']['distanceFromDestination']['value'] * 1.6, 2) > diapason:
                break
            counter += 1
            history += f" {counter}.{hotel_info['name']}\n"
            collecting_data(message.chat.id, hotel_info=hotel_info, show_photos=message.text)
    else:
        for i in range(int(number)):
            hotel_info = response2.json()['data']['propertySearch']['properties'][i]
            history += f" {i + 1}.{hotel_info['name']}\n"
            collecting_data(message.chat.id, hotel_info=hotel_info, show_photos=message.text)
    bot.send_message(message.chat.id, "Select button:", reply_markup=menu())


def collecting_data(chat_id, hotel_info, show_photos):
    if show_photos.lower() == 'yes':
        photo_result = hotel_info['propertyImage']['image']['url']
        bot.send_photo(chat_id, photo_result)
    result = f"{hotel_info['name']}\n"
    geolocator = Nominatim(user_agent="main.py")
    location = geolocator.reverse(
        f"{hotel_info['mapMarker']['latLong']['latitude']}, {hotel_info['mapMarker']['latLong']['longitude']}")
    # address = " ".join(location.address.split(',')[:2])
    result += f" -address: {','.join(location.address.split(',')[1::-1])}\n" \
              f" -rating: {hotel_info['reviews']['score']}/10\n" \
              f" -{round(hotel_info['destinationInfo']['distanceFromDestination']['value'] * 1.6, 2)}" \
              f"km from city center\n"
    if hotel_info['price'] and hotel_info['price']['strikeOut'] and hotel_info['price']['strikeOut']['amount']:
        result += f" -average price per night: {round(hotel_info['price']['strikeOut']['amount'])}$\n"
    elif hotel_info['price']['lead']['amount']:
        result += f" -average price per night: {round(hotel_info['price']['lead']['amount'])}$\n"
    bot.send_message(chat_id, result)


bot.polling(none_stop=True)
# @server.route('/' + TOKEN, methods=['POST'])
# def getMessage():
#     json_string = request.get_data().decode('utf-8')
#     update = telebot.types.Update.de_json(json_string)
#     bot.process_new_updates([update])
#     return "!", 200
#
#
# @server.route("/")
# def webhook():
#     bot.remove_webhook()
#     bot.set_webhook(url='https://glacial-cliffs-29712.herokuapp.com/' + TOKEN)
#     return "!", 200
#
#
# if __name__ == "__main__":
#     server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
