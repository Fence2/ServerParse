MAIN_URL = "https://servergate.ru"
CATALOG_COMPONENTS_URL = MAIN_URL + "/components/"
CATALOG_CONFIGURATORS_URL = MAIN_URL + "/configure/"

PAGEN = "?PAGEN_1="  # noqa

CATEGORIES = {
    "Процессоры": "cpu",
    "Память": "ram",
    # "Сетевые карты": "network",
    'Контроллеры': "raid",
    "Рельсы для серверов": "rails",
    "Салазки для дисков": "tray",
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
