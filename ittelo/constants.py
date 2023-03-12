MAIN_URL = "https://www.ittelo.ru"
CATALOG_COMPONENTS_URL = MAIN_URL + "/partsittelo"
CATALOG_CONFIGURATORS_URL = MAIN_URL + "/server"


PAGEN = "?PAGEN_1="  # noqa

CATEGORIES = {
    'Процессоры': "cpu",
    'Оперативная память': "ram",
    # 'Сетевая карта': "network",
    'RAID-контроллер': "raid",
    "Рельсы": "rails",
    "Салазки": "tray",
}

CONFIG_CATEGORIES = {
    'Процессоры': "cpu",
    'Оперативная память': "ram",
    # 'Сетевая карта': "network",
    'RAID-контроллер': "raid",
    "Рельсы": "rails",
    "Салазки": "tray",
}

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    'origin': MAIN_URL,
    'referer': MAIN_URL + "/",
    "sec-ch-ua": "\"Chromium\";v=\"110\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1"
}
