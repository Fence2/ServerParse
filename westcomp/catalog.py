from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup


class Catalog(AbstractCatalog):
    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_components_categories(session) -> (dict, requests.Session):
        """
        Функция возвращает ссылки на категории комплектующих в виде словаря

        {
            "RAID Контроллер": "URL",

            "Процессоры": "URL",

            ...
        }
        """
        print("Получение категорий комплектующих - ", end="")

        categories: dict[str, str] = dict()

        try:
            response, session = requests_try_to_get_max_5x(COMPONENTS_CATEGORIES_URL, HEADERS, session)
            if response is None:
                print("Не удалось загрузить страницу:", COMPONENTS_CATEGORIES_URL)
                return {}
            html = BeautifulSoup(response.text, "lxml")
            categories_list = html.find("ul", attrs={'id': 'leftmenu'})
            categories_list = categories_list.find("a", string="Серверные комплектующие").parent.find("ul")

            categories_tags = categories_list.find_all("li", recursive=False)
            for li in categories_tags:
                link = li.find("a")
                if "href" in link.attrs:
                    category = link.string.strip()
                    category = category.replace("FС", "FC")
                    category = format_name(category)
                    link = MAIN_URL + link.attrs["href"] if link.attrs["href"].startswith("/") else link.attrs["href"]
                    categories[category] = link

            print("ОК\n")
            return categories, session

        except Exception as e:
            print(f"\nОШИБКА: {e}\n")

    @staticmethod
    def get_components() -> list[Component]:
        """
        Функция возвращает комплектующие в виде словаря:
            Название комплектующего: объект класса Component

        {
            "Процессор Intel Xeon E5-2680 v3 ...": obj -> Component,

            "DDR4 16gb 2666hz ECC REG БУ": obj -> Component,

            ...
        }
        Заполняемые поля данной функцией:
        category,
        name,
        condition,
        price,
        no_sale_price

        """
        components: list[Component] = list()

        session = requests.Session()
        categories, session = Catalog.get_components_categories(session)
        session.cookies.update({'wcshow': '999'})

        for category, category_url in categories.items():
            print(f"{category} - ", end="")
            time.sleep(2)
            response, session = requests_try_to_get_max_5x(category_url, HEADERS, session)
            if response is None:
                print("Не удалось загрузить страницу:", category_url)
                continue

            html = BeautifulSoup(response.text, "lxml")
            components_list = html.find("ul", class_="pics")
            components_html = components_list.find_all("li", recursive=False)
            category_comps_count = 0
            for comp_html in components_html:
                hr_li = "class" in comp_html.attrs and "hr" in comp_html.attrs["class"]
                if hr_li:
                    continue

                try:
                    name = comp_html.find("div").find("a").string.strip()
                    name = format_name(name)
                    price_span = comp_html.find("p", recursive=False).find("span", recursive=False)
                    price = price_span.contents[-1]
                    price = format_price(price.text.strip())

                    sale = price_span.find("del")
                    if sale is not None:
                        no_sale_price = format_price(sale.text.strip())
                    else:
                        no_sale_price = 0

                    comp = Component(category=category,
                                     name=name,
                                     new=new_or_ref(name),
                                     price=price,
                                     no_sale_price=no_sale_price)

                    category_comps_count += 1

                    components.append(comp)

                except AttributeError as e:
                    print(e)
                    print("Всего обработано", category_comps_count)
                    print(comp_html)

            print(f"Получено {category_comps_count} комплектующих")

        print(f"\nПолучено всего комплектующих: {len(components)}")
        return components

    @staticmethod
    def get_servers() -> list[str]:
        """
        Функция возвращает серверы в виде списка ссылок на конфигураторы:

        [
            url1,

            url2,

            ...
        ]

        """
        print("\nПолучение конфигураторов - ", end="")
        response = requests_try_to_get_max_5x(SERVER_CATALOG_URL, HEADERS)
        if response is None:
            print("Не удалось загрузить страницу:", SERVER_CATALOG_URL)
            return []

        main_server_page_soup = BeautifulSoup(response.text, "lxml")
        configurators = set()
        configurators_block = main_server_page_soup.find(class_="wcCalculator").find_all("a", recursive=False)
        for cfg_block in configurators_block:
            configurators.add(MAIN_URL + cfg_block.attrs["href"])

        configurators = list(configurators)

        print("OK\nПолучено серверов:", len(configurators))
        return configurators
