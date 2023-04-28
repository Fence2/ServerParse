import random
import re

import bs4
from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    delay = 1.5

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_config_components(servers: list[Server]):
        servers_with_config = list()

        good_servers = [s for s in servers if s.category < 4]
        for count, server in enumerate(good_servers):
            print(f"Осталось получить: {len(servers) - count} конфигураторов")
            if server.config_url is None:
                continue

            print("Получение -", server.name)
            response = requests_try_to_get_max_5x(server.config_url, HEADERS)
            if response is None:
                print("Не удалось загрузить страницу", server.config_url)
                continue

            soup = BeautifulSoup(response.text, "lxml")
            form = soup.body.find("table", class_="product-specifications")

            price = soup.find("meta", attrs={"itemprop": "price", "content": True}).attrs.get("content")
            price = format_price(price)

            server.config_price = price
            print(f"\t{price}")

            categories_html = Configurator.get_config_components_categories_html(form)

            cfg_components = Configurator.get_components_from_categories(categories_html, server)
            server.components = cfg_components

            servers_with_config.append(server)

            print("    Найдено комплектующих:", len(cfg_components))
            print()
            time.sleep(Configurator.delay)

        return servers_with_config + [s for s in servers if s.category > 3]

    @staticmethod
    def get_config_components_categories_html(config_soup: BeautifulSoup) -> dict[str, dict]:
        """
        Функция собирает категории комплектующих конфигуратора и возвращает их в виде словаря:

        {
            "Оперативная память": category -> BeautifulSoup,

            "Процессоры": category -> BeautifulSoup,

            ...
        }
        """
        categories = dict()

        tbody = config_soup.find("tbody")
        table_items = tbody.find_all("tr", recursive=False)
        for row in table_items:
            columns = row.find_all("td", recursive=False)
            name_tag = columns[0]
            name = format_name(name_tag.text.strip())
            name = normalize_category_name(name)

            cat_tag = columns[1]
            category_options = cat_tag.find_all("option")
            amount = 0
            if len(category_options[0].text.strip()):
                amount = 1
                if len(columns) > 2:
                    amount_tag = columns[2]
                    amount_text = amount_tag.find("select").find("option").text.strip()
                    if len(amount_text) and amount_text.isnumeric():
                        amount = int(amount_text)
            else:
                del category_options[0]

            categories[name] = dict(options=category_options, checked_amount=amount)

        return categories

    @staticmethod
    def get_components_from_categories(categories_html: dict, server: Server) -> list[Component]:
        """
        Метод для получения комплектующих из каждой категории конфигуратора
        """

        cfg_components = list()
        for category_name, category_data in categories_html.items():
            checked_amount = category_data['checked_amount']
            category_html = category_data['options']
            for option in category_html:
                try:
                    name = option.text.strip()
                    name = format_name(name)
                    name = re.sub(r" - \d.*$", "", name.strip(), re.I)
                    if re.search("Нет в наличии", name, re.I) is not None:
                        continue

                except Exception as e:
                    print("Ошибка: Неправильное имя комплектующего", str(option))
                    continue

                try:
                    price = option.attrs.get('data-price')
                    price = format_price(price)
                except Exception as e:
                    print("Ошибка: Неправильная цена комплектующего", str(option))
                    price = 0

                comp = Component(
                    category=category_name,
                    name=name,
                    new=new_or_ref(name),
                    checked=bool(checked_amount),
                    checked_amount=checked_amount,
                    price=price,
                    resource=f"{server.name}|{server.config_url}"
                )
                if "салазки" in category_name.lower() or "рельсы" in category_name.lower():
                    comp.name = add_info_to_trays_and_rails(category_name, comp, server)

                cfg_components.append(comp)

        return cfg_components
