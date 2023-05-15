MAIN_URL = "https://shop.nag.ru"
CATALOG_COMPONENTS_URL = MAIN_URL + "/catalog/31464.komplektuyuschie-dlya-serverov-i-shd"

PAGEN = "?sort=price_asc&count=0&page="  # noqa

CATEGORIES = {
    "Процессоры": "cpu",
    "Оперативная память": "ram",
    # "Сетевые карты": "network",
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
    "accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', # noqa
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    # 'origin': MAIN_URL,
    # 'referer': MAIN_URL + "/",
    "sec-ch-ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}
