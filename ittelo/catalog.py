import re

import bs4
from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup


class Catalog(AbstractCatalog):
    delay = 3

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_components_categories() -> dict[str, str]:
        """
        Функция возвращает ссылки на категории комплектующих в виде словаря

        {
            "RAID Контроллер": "https://www.ittelo.ru/partsittelo/raid/",

            "Процессоры": "https://www.ittelo.ru/partsittelo/cpu/",

            ...
        }
        """
        print("Получение категорий комплектующих...", end="")
        categories: dict[str, str] = dict()

        category_normal_name = {
            r"\bcpu\b|процессор": "Процессоры",
            r"(.*оперативн[а-яё]+\s+памят[а-яё]+|.*\bram\b)(?!.*контрол+[а-яё]+|.*к[эе]ш)": "Оперативная память",
            r"корзин[\wа-яё] на|hdd": "Жёсткие диски",
            r"салазк[\wа-яё]": "Салазки",
            r"raid|р[еэ][ий]д": "RAID-контроллер",
            r"сетев[\wа-яё]+ карт[\wа-яё]|network": "Сетевая карта",
            r"монтаж и подключение|рельс|креплен[а-яё]+ для сервер[а-яё]+ в стойк[а-яё]+": "Рельсы",
            r"удал[её]нн[\wа-яё]+ управлен[\wа-яё]+": "Удалённое управление"
        }

        catalog_html = requests_try_to_get_max_5x(CATALOG_COMPONENTS_URL, headers=HEADERS)
        soup = BeautifulSoup(catalog_html.text, "lxml")

        categories_wrapper = soup.find(class_="category-list_new")
        categories_cards = categories_wrapper.find_all(class_="category-list_new_item")

        for card in categories_cards:
            a_tag = card.find("a")
            if a_tag:
                link = a_tag.attrs.get("href", '') or ''
                if link:
                    link = MAIN_URL + link
                    category_name = a_tag.find(class_="category_card__name").string.strip()
                    lower_name = category_name.lower()
                    for pattern, normal_name in category_normal_name.items():
                        if re.search(pattern, lower_name, flags=re.I) is not None:
                            category_name = normal_name
                            break
                    categories[category_name] = link

        print(".Успех\n")

        return categories

    @staticmethod
    def get_components() -> list[Component]:
        """
        Функция возвращает комплектующие в виде списка:
        [
            Component,

            Component,

            ...
        ]
        """
        components = list()

        categories = Catalog.get_components_categories()

        for category_name, category_url in categories.items():
            original_category = category_name
            total_in_category = 0
            print("Категория:", category_name)
            print("\tПолучение страницы 1")
            page_1_html = requests_try_to_get_max_5x(category_url, headers=HEADERS)
            if not page_1_html:
                continue

            page_1_soup = BeautifulSoup(page_1_html.text, "lxml").body

            number_of_pages = Catalog.get_number_of_pages(page_1_soup)
            page_num = 1
            for page_url in [category_url + PAGEN + str(page_n) for page_n in range(1, number_of_pages + 1)]:
                if page_num == 1:
                    page_soup = page_1_soup
                else:
                    print("\tПолучение страницы", page_num)
                    time.sleep(Catalog.delay)
                    page_html = requests_try_to_get_max_5x(page_url, HEADERS)
                    if not page_html:
                        continue
                    page_soup = BeautifulSoup(page_html.text, "lxml").body

                catalog_wrapper = page_soup.find(class_="catalog_block_list")
                items = catalog_wrapper.find_all(class_="catalog_block_item")
                for item in items:
                    category_name = original_category
                    name, new = Catalog.get_name_and_condition(item)
                    price = Catalog.get_price(item, name)
                    no_sale_price = Catalog.get_no_sale_price(item)
                    if re.search("диски|hdd|ssd", category_name, flags=re.I) is not None and \
                            re.search(r"\d+\s*[MGT]B", name, flags=re.I) is None and \
                            re.search("салазк|переходник", name, flags=re.I) is not None:
                        category_name = "Салазки"
                    comp = Component(
                        category=category_name,
                        name=name,
                        new=new,
                        price=price,
                        no_sale_price=no_sale_price,
                    )

                    components.append(comp)
                    total_in_category += 1
                page_num += 1
            print(f"\t\tВсего: {total_in_category} комплектующих\n")
        components.sort(key=lambda comp: (comp.category, comp.name, comp.price))
        return components

    @staticmethod
    def get_servers() -> list[Server]:
        servers = list()
        print("Получение списка серверов")
        print("\tПолучение страницы 1")
        main_server_page_html = requests_try_to_get_max_5x(CATALOG_CONFIGURATORS_URL, HEADERS)
        main_server_page_soup = BeautifulSoup(main_server_page_html.text, "lxml").body
        number_of_pages = Catalog.get_number_of_pages(main_server_page_soup)
        page_num = 1

        for page_link in [CATALOG_CONFIGURATORS_URL + PAGEN + str(page_n) for page_n in range(1, number_of_pages + 1)]:

            if page_num == 1:
                page_soup = main_server_page_soup
            else:
                print(f"\tПолучение страницы {page_num}")
                time.sleep(Catalog.delay)
                page_html = requests_try_to_get_max_5x(page_link, HEADERS)
                page_soup = BeautifulSoup(page_html.text, "lxml").body

            catalog_wrapper = page_soup.find(class_="catalog_block_list")
            items = catalog_wrapper.find_all(class_="catalog_block_item")
            for item in items:
                url = Catalog.get_url(item)
                name, new = Catalog.get_name_and_condition(item)
                if re.search(
                        r"(?:для|под)\s*1С|(?:до|на).{0,9}пользоват[а-яё]*|до\s*\d+\s*камер|комплект|виртуализ[а-яё]*|(?:начальный|профессиональный)\s*уровень|высоконагруженные",
                        name,
                        flags=re.I
                ) is not None:
                    continue
                price = Catalog.get_price(item, name)
                no_sale_price = Catalog.get_no_sale_price(item)
                server = Server(
                    name=name,
                    new=new,
                    card_price=price,
                    no_sale_card_price=no_sale_price,
                    config_url=url,
                )
                server.get_specs_from_name()
                servers.append(server)
            page_num += 1

        servers.sort(key=lambda server: (server.category, server.name, server.card_price))
        print("Получено ОК серверов:", len(servers))
        return servers

    @staticmethod
    def get_number_of_pages(soup: BeautifulSoup):
        """
        Функция получает количество страниц каталога
        """
        try:
            cat_page = soup.find("div", attrs={"id": "cat-page"})
            pages_input = cat_page.find("input", attrs={"id": "pages"})
            pages = pages_input.attrs.get("value", '1') or '1'
            pages = int(pages)
            return pages
        except AttributeError:
            return 1
        except Exception as e:
            print("Ошибка в методе get_pages:")
            print(e)
            return 1

    @staticmethod
    def get_name_and_condition(item):
        try:
            condition = item.find(class_="catalog_block_item_lable_by").string.strip()  # noqa
            new = new_or_ref(condition)
        except AttributeError:
            new = None

        name = item.find("span", attrs={"itemprop": "name"}).string.strip()  # noqa
        name = re.sub(r"0сG", '0c G', name, flags=re.I)
        name = re.sub(r"1хMini", "1x Mini", name, flags=re.I)
        name = re.sub(r"[cс][aа][cс]h[eе]", "Cache", name, flags=re.I)
        name = format_name(name)
        if new is None:
            new = new_or_ref(name)
        if new and re.search(r"\bNEW|\bНОВ[А-ЯЁ]+", name, flags=re.I):
            name += " NEW"

        return name, new

    @staticmethod
    def get_price(item, name):
        try:
            price = item.find(class_="catalog_block_item_price").text.strip()
            return format_price(price)
        except AttributeError:
            if item.find(text="цену уточняйте у менеджера").parent is not None:
                return 0
            else:
                print("Не найдена цена и сообщение о ней?")
                print("Товар:", name)
                return 0

    @staticmethod
    def get_no_sale_price(item):
        try:
            no_sale_price = item.find(class_="old-price_el").text.strip()
            return format_price(no_sale_price)
        except AttributeError:
            return 0

    @staticmethod
    def get_url(item):
        try:
            url = item.find("div", attrs={"data-href": True}).attrs["data-href"]
            return MAIN_URL + url
        except Exception:
            return ''
