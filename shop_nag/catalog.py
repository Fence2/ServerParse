import re

from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup, Tag


class Catalog(AbstractCatalog):
    delay = 3

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def _page_loaded(tag: Tag):
        main_tag = tag.find(id='main')
        if main_tag:
            atleast_one_item_on_page = main_tag.find("div", class_="setout__item")
            if atleast_one_item_on_page:
                return True

        return False

    @staticmethod
    def get_components_categories() -> dict[str, str]:
        def _valid_category(tag: Tag):
            if tag.name != 'a':
                return False

            if len(tag.text.strip()) == 0:
                return False

            li = tag.parent
            if li is not None and li.name == 'li' and "filter-category" in li.attrs.get("class", []):
                return True
            else:
                return False

        print("Получение категорий комплектующих - ", end="")
        categories = dict()

        result = selenium_try_to_get_max_5x(Catalog.driver, CATALOG_COMPONENTS_URL, Catalog._page_loaded)
        time.sleep(Catalog.delay)

        if result is None:
            return {}
        else:
            Catalog.driver = result

        try:
            soup = BeautifulSoup(Catalog.driver.page_source, "lxml")
            main = soup.body.find("div", id="main")
            categories_html = soup.find_all(_valid_category)
            for category_html in categories_html:
                if len(category_html.attrs.get('href', '').strip()) > 1:
                    category_name = category_html.text.strip()
                    if category_name == "Контроллеры дисков":
                        category_name = "RAID-контроллер"
                    category_name = normalize_category_name(category_name)
                    category_url = category_html.attrs['href'].strip()
                    if not category_url.startswith("http"):
                        category_url = MAIN_URL + (category_url if category_url[0] in "/\\" else f"/{category_url}")

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

        categories = Catalog.get_components_categories()

        # В каждой категории
        for category_name, category_url in categories.items():
            print("Получение комплектующих категории:", category_name)
            category_url = category_url + PAGEN

            category_total = 0
            current_page = total_pages = 1
            while current_page <= total_pages:
                print(f"\tСтраница {current_page} - получение")
                result = selenium_try_to_get_max_5x(Catalog.driver, category_url + str(current_page),
                                                    Catalog._page_loaded)

                if result is None:
                    print("Не удалось загрузить страницу", category_url + str(current_page))
                    continue
                else:
                    Catalog.driver = result

                soup = BeautifulSoup(Catalog.driver.page_source, "lxml")
                total_pages = Catalog.get_pages_amount(soup, category_url, current_page)

                try:
                    products = soup.body.find_all("div", class_="setout__item")
                except Exception as e:
                    print("!!!!!!!! Ошибка: Не найдена страница с товарами:", e)
                    products = []

                # Пройтись по каждому товару и сохранить информацию о нём
                for item in products:
                    try:
                        item_category = category_name
                        name = item.find_all("a")[-1].text.strip()
                        name = re.sub(" FС ", " FC ", name, flags=re.I)
                        name = re.sub("хS", "xS", name, flags=re.I)
                        name = re.sub("хR", "xR", name, flags=re.I)
                        name = format_name(name)
                        bad_category = re.match("батар|адаптер|кэш|модуль|ключ|конденсатор", name, flags=re.I)
                        if "RAID" in item_category and bad_category:
                            item_category = "Аксессуары для RAID-контроллеров"

                        try:
                            price_tag = item.find("span", class_="our-price").find("span")
                            price = re.sub(r"\s+", "", price_tag.text.strip())
                            price = format_price(price)
                        except Exception as e:
                            price = 0

                        try:
                            sale_price_tag = item.find("span", class_="sale-price").find("span")
                            sale_price = re.sub(r"\s+", "", sale_price_tag.text.strip())
                            sale_price = format_price(sale_price)
                        except Exception as e:
                            sale_price = 0

                        comp = Component(
                            category=item_category,
                            name=name,
                            new=new_or_ref(name),
                            price=price,
                            no_sale_price=sale_price
                        )

                        components.append(comp)
                        category_total += 1
                    except Exception as e:
                        print("Ошибка при получении информации о комплектующем", e)

                current_page += 1
                # Задержка в конце запроса
                time.sleep(Catalog.delay)

            print(f"\t\tВсего в категории - {category_total}\n")

        sort_products_by_category_and_name(components)
        print("Всего получено комплектующих:", len(components))
        print("\tИз них комплектующих без цены:", len([c for c in components if c.price == 0]))
        print_dict(products_group_by_category(components), offset="\t")

        return components

    @staticmethod
    def get_servers() -> list[Server]:
        servers = list()
        return servers

    @staticmethod
    def get_pages_amount(soup: BeautifulSoup, current_url: str, current_page: int):
        next_page = current_page + 1
        next_page_url = re.sub(MAIN_URL, "", current_url, flags=re.I)

        there_is_next_page = True
        while there_is_next_page:
            there_is_next_page = soup.find("a", attrs={'href': next_page_url + str(next_page)})
            next_page += 1

        return next_page - 2
