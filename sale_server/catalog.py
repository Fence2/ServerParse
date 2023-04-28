import re

from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup, Tag


class Catalog(AbstractCatalog):
    delay = 1.5

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_components_categories() -> dict[str, str]:
        def _valid_category(tag: Tag):
            if tag.name != 'a':
                return False

            ul = tag.parent.find("ul")
            if ul is not None:
                if len(ul.find_all('a')):
                    return False

            return True

        print("Получение категорий комплектующих - ", end="")
        categories = dict()
        html = requests_try_to_get_max_5x(CATALOG_COMPONENTS_URL, HEADERS)
        if html is None:
            return {}
        try:
            soup = BeautifulSoup(html.text, "lxml")
            categories_html = soup.body.find("div", class_="category-menu").find_all(_valid_category)
            for category_html in categories_html:
                if len(category_html.attrs.get('href', '')) > 1:
                    category_name = category_html.text.strip()
                    category_name = normalize_category_name(category_name)
                    category_url = category_html.attrs['href']
                    i = 2
                    correct_name = category_name
                    while correct_name in categories:
                        correct_name = f"{category_name}_{i}"
                        i += 1

                    categories[correct_name] = category_url

            print(f"Успех\nПолучено категорий: {len(categories)}\n")
            return categories

        except Exception as e:
            print(e)
        return {}

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
        # return components  # TODO DELETE BEFORE RELEASE

        categories = Catalog.get_components_categories()

        # В каждой категории
        for category_name, category_url in categories.items():
            print("Получение комплектующих категории:", category_name)
            category_url = category_url + PAGEN
            category_total = 0
            current_page = total_pages = 1
            while current_page <= total_pages:
                print(f"\tСтраница {current_page} - получение")
                req = requests_try_to_get_max_5x(category_url + str(current_page), HEADERS)
                if req is None:
                    print("Не удалось загрузить страницу", category_url + str(current_page))
                    continue

                soup = BeautifulSoup(req.text, "lxml")
                if current_page == 1:
                    total_pages = Catalog.get_pages_amount(soup)

                products = soup.body.find("div", class_="products").find_all(class_="product-item", recursive=False)

                # Пройтись по каждому товару и сохранить информацию о нём
                for item in products:
                    item_category = category_name
                    name = item.find_all("a")[-1].text.strip()
                    name = format_name(name)
                    if "кэш" in category_name.lower():
                        is_cache = name[0].isnumeric() and "кэш" in name.lower()
                        if is_cache:
                            item_category = "Кэш-память"

                    try:
                        price_tag = item.find(class_="prices")
                        price = re.sub(r"\s+", "", price_tag.text.strip())
                        price = re.match(r"\d+(?:[.,]\d+)?", price)
                        price = format_price(price.group())
                    except Exception as e:
                        print(f"\t!Не удалось получить цену товара: {name}\n\t\t{e}")
                        price = 0

                    comp = Component(
                        category=item_category,
                        name=name,
                        new=new_or_ref(name),
                        price=price
                    )

                    components.append(comp)
                    category_total += 1

                current_page += 1
                # Задержка в конце запроса
                time.sleep(Catalog.delay)

            print(f"\t\tВсего в категории - {category_total}\n")

        sort_products_by_category_and_name(components)
        print("Всего получено комплектующих:", len(components))
        print_dict(products_group_by_category(components), offset="\t")

        return components

    @staticmethod
    def get_servers() -> list[Server]:
        servers = list()

        print("Получение списка серверов")
        servers_url = CATALOG_CONFIGURATORS_URL + PAGEN
        current_page = total_pages = 1
        while current_page <= total_pages:
            print(f"\tСтраница {current_page} - получение")
            req = requests_try_to_get_max_5x(servers_url + str(current_page), HEADERS)
            if req is None:
                print("Не удалось загрузить страницу", servers_url + str(current_page))
                continue

            soup = BeautifulSoup(req.text, "lxml")
            if current_page == 1:
                total_pages = Catalog.get_pages_amount(soup)

            products = soup.body.find("div", class_="products").find_all(class_="product-item", recursive=False)

            for item in products:
                a_tag = item.find_all("a")[-1]
                name = a_tag.text.strip()
                name = format_name(name)

                try:
                    url = a_tag.attrs.get("href", None).strip()
                except Exception as e:
                    print("\tОшибка в получении ссылки на сервер")
                    print(e)
                    url = None

                try:
                    price_tag = item.find(class_="prices")
                    price = re.sub(r"\s+", "", price_tag.text.strip())
                    price = re.match(r"\d+(?:[.,]\d+)?", price)
                    price = format_price(price.group())
                except Exception as e:
                    print(f"\t!Не удалось получить цену товара: {name}\n\t\t{e}")
                    price = 0

                server = Server(
                    name=name,
                    new=new_or_ref(name),
                    card_price=price,
                    config_url=url
                )

                server.get_specs_from_name()

                servers.append(server)

            current_page += 1
            # Задержка в конце запроса
            time.sleep(Catalog.delay)

        print()
        sort_products_by_category_and_name(servers)
        for server in servers:
            print(server)

        print("\nНайдено серверов:", len(servers))
        return servers

    @staticmethod
    def get_pages_amount(soup: BeautifulSoup):
        pagination = soup.find("ul", class_="paginator")
        if pagination is None:
            return 1

        pages = pagination.find_all(lambda tag: tag.name == "a" and str(tag.text).strip().isnumeric())
        pages_digits = [int(page.text.strip()) for page in pages]
        return max(pages_digits)
