import bs4

from modules.parser_tools import *
from modules.parser_dataclasses import *
from .constants import *
from bs4 import BeautifulSoup


def categories_and_components(tag):
    if 'class' in tag.attrs:
        class_ = tag['class']
        if "items-counter" in class_ and tag.text != "":
            return True

        if "items-grid" in class_:
            return True


class Catalog:
    def __init__(self, webdriver_path: str = None, launch=True):
        if webdriver_path is not None and launch:
            from selenium.webdriver.support.ui import Select  # noqa
            from selenium.webdriver.common.by import By  # noqa
            from selenium.webdriver.chrome.service import Service  # noqa
            from selenium.webdriver.chrome.options import Options  # noqa
            from selenium import webdriver  # noqa

            options = Options()
            options.page_load_strategy = 'eager'
            options.add_argument("window-size=1800,1000")
            try:
                self.driver = webdriver.Chrome(service=Service(webdriver_path), options=options)
            except Exception as e:
                print("ERROR\nОбновите ваш chromedriver драйвер!\nERROR\n")
                print(e)
                import os
                os.system("pause")
                exit(-1)

    @staticmethod
    def get_components() -> list[Component]:
        """
        Функция возвращает комплектующие в виде списка:
        [
            Component,

            Component,

            ...
        ]
        Заполняемые поля данной функцией:
        category,
        name,
        condition,
        price,
        no_sale_price

        """
        components = list()

        i = 1
        groups = list()
        while True:
            url = CATALOG_COMPONENTS_URL
            if i != 1:
                url += PAGEN + str(i)

            i += 1
            response = requests_try_to_get_max_5x(url, HEADERS)
            if response is None:
                print("Не удалось загрузить страницу:", url)
                continue

            html = BeautifulSoup(response.text, "lxml")
            pages = html.find("div", class_="pagination")
            groups += html.find(class_="parts").find_all(categories_and_components)

            if "следующая" not in pages.text.lower():
                break

        category_name = "Неизвестно"
        for group in groups:
            if "items-counter" in group['class']:
                category_name = group.find(text=True, recursive=False).rstrip(": \r\n")
            else:
                items = group.find_all("div", class_="item-card")
                for item in items:
                    name = item.find("a", class_="item-card__body").find(class_="item-card__name").find("h3")
                    name = name.text.strip()
                    name = format_name(name)

                    price = item.find("div", class_="item-card__price").text
                    price = format_price(price)

                    comp = Component(
                        category=category_name,
                        name=name,
                        new=False,
                        price=price
                    )
                    components.append(comp)

        print("Получено комплектующих:", len(components))
        return components

    @staticmethod
    def get_servers() -> list[Server]:
        servers = list()

        i = 1
        servers_cards = list()
        while True:
            url = CATALOG_CONFIGURATORS_URL
            if i != 1:
                url += PAGEN + str(i)

            i += 1
            response = requests_try_to_get_max_5x(url, HEADERS)
            if response is None:
                print("Не удалось загрузить страницу:", url)
                continue

            html = BeautifulSoup(response.text, "lxml")
            pages = html.find("div", class_="pagination")
            servers_cards += html.find(class_="servers__grid").find_all(class_="item-card--conf")

            if "следующая" not in pages.text.lower():
                break

        card: bs4.Tag
        for card in servers_cards:
            name = card.find("h3").text.strip()
            name = format_name(name)

            try:
                condition = card.find(class_="item-card__name").find("span").text.strip()
                new = new_or_ref(condition)
            except Exception as e:
                new = False

            try:
                server_specs = card.find(class_='item-card__list').find_all('li', recursive=False)
                form_factor = server_specs[0].text.strip()
                units = search_from_pattern(Patterns.SERVER.units, form_factor)
                if units is None:
                    units = ""
                    if "tower" in form_factor.lower():
                        units = "Tower"

                name += " " + units
            except Exception as e:
                pass

            try:
                price = card.find(class_='item-card__price').text.strip()
                price = format_price(price)
            except Exception as e:
                price = 0

            try:
                url = card.find(class_="item-card__buy")
                if "href" in url.attrs and url.attrs['href'] is not None:
                    url = MAIN_URL + url.attrs['href']
            except Exception as e:
                url = None

            server = Server(
                name=name,
                new=new,
                card_price=price,
                config_url=url
            )

            server.get_specs_from_name()

            servers.append(server)

        sort_servers_by_category_and_name(servers)
        print("\nНайдено серверов:", len(servers))
        for server in servers:
            print(server)

        return servers
