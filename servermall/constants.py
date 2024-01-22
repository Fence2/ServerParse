MAIN_URL = "https://servermall.ru"
CATALOG_COMPONENTS_URL = MAIN_URL + "/components/"
CATALOG_CONFIGURATORS_HP_URL = MAIN_URL + "/catalog/servers/filter/manufacturer-is-hp/"
CATALOG_CONFIGURATORS_DELL_URL = MAIN_URL + "/catalog/servers/filter/manufacturer-is-dell/"
CATALOG_CONFIGURATORS_HP_URL_2 = MAIN_URL + "/config/category_hp/"
CATALOG_CONFIGURATORS_DELL_URL_2 = MAIN_URL + "/config/category_dell/"
RANDOM_URL = [
    MAIN_URL + "/about/",
    MAIN_URL + "/contacts/",
    MAIN_URL + "/about/warranty-conditions/",
    MAIN_URL + "/sets/kommutatory-hp/",
    MAIN_URL + "/personal/cart/",
    MAIN_URL + "/special/retail/",
    MAIN_URL + "/sets/skhd-dell/",
    MAIN_URL + "/include/modals/pricelist.php",
]

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

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    'origin': MAIN_URL,
    'referer': MAIN_URL + "/",
    "sec-ch-ua": """\"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114\"""",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
