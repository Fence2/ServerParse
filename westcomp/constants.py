MAIN_URL = "https://www.westcomp.ru"
SERVER_CATALOG_URL = MAIN_URL + "/catalog/konfiguratory"
COMPONENTS_CATEGORIES_URL = MAIN_URL + "/catalog/servernye_komplektuyushchie"

PAGEN = "?PAGEN_1="  # noqa

CATEGORIES = {
    "Процессоры": "cpu",
    "Память": "ram",
    # "Сетевые карты": "network",
    'RAID Контроллеры': "raid",
    "Рельсы для серверов": "rails",
    "Салазки для HDD": "tray",
}

CONFIG_CATEGORIES = {
    'Процессоры': "cpu",
    'Оперативная память': "ram",
    # 'Сетевая карта': "network",
    'RAID-контроллер': "raid",
    "Рельсы": "rails",
    "Салазки": "tray",
}

HEADERS = {'accept': '*/*',
           'origin': MAIN_URL,
           'referer': MAIN_URL + "/",
           "sec-ch-ua": "\"Chromium\";v=\"108\", \"Not?A_Brand\";v=\"8\"",
           "sec-ch-ua-mobile": "?0",
           "sec-ch-ua-platform": "\"Windows\"",
           'sec-fetch-dest': 'empty',
           'sec-fetch-mode': 'cors',
           'sec-fetch-site': 'cross-site',
           'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}  # noqa
