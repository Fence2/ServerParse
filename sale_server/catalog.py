from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup, Tag


def get_pages_amount(html: BeautifulSoup):
    pagination = html.find(class_="pagination")
    if pagination is None:
        return 1

    def get_only_pages_digits_clickable(tag):
        only_one_class = len(tag.attrs['class']) == 1
        page_item_class = 'page-item' in tag.attrs['class']
        digits_button = str(tag.text).strip().isnumeric()
        if all([only_one_class, page_item_class, digits_button]):
            return True
        else:
            return False

    pages = pagination.find_all(get_only_pages_digits_clickable)
    pages_digits = list()
    for page in pages:
        pages_digits.append(int(page.text.strip()))
    return max(pages_digits)


def get_category_formatted_name(html: BeautifulSoup):
    h1 = html.find("h1").text.strip()
    category_name = h1.replace("Комплектующие - ", "")
    category_name = category_name.replace("Запчасти к серверам - ", "")
    return category_name


class Catalog(AbstractCatalog):
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

        overall_info = dict()

        categories = Catalog.get_components_categories()

        # В каждой категории
        for category_name, category_url in categories.items():
            print("Получение комплектующих категории:", category_name)
            html = requests_try_to_get_max_5x(category_url, HEADERS)
            if html is None:
                print("Не удалось загрузить страницу", category_url)
                continue

            total_pages = get_pages_amount(BeautifulSoup(html.text, "lxml"))
            total_components_count_before = len(components)

            # Загрузить каждую страницу товаров
            for page in range(1, total_pages + 1):
                print(f"\tСтраница {page} - получение")
                time.sleep(1.5)
                if page != 1:
                    url = category_url + PAGEN + str(page)
                    html = requests_try_to_get_max_5x(url, HEADERS)
                    if html is None:
                        print("Не удалось загрузить страницу", category_url)
                        continue

                soup = BeautifulSoup(html.text, "lxml")
                body = soup.find("body")
                category_name = get_category_formatted_name(body)

                products = body.find("div", class_="products").find_all("div", class_="product card")

                # Пройтись по каждому товару и сохранить информацию о нём
                for item in products:
                    item_category = category_name
                    name = item.find(class_="card-title").text.strip()
                    if 'HОВЫЙ' in name:
                        name = re.sub('HОВЫЙ', "НОВЫЙ", name, re.I)
                    name = format_name(name)
                    if "кэш" in category_name.lower():
                        is_cache = name[0].isnumeric() and "кэш" in name.lower()
                        if is_cache:
                            item_category = "Кэш-память"

                    try:
                        price = item.find(class_="card-footer").text.strip()
                        price = format_price(price)
                    except Exception as e:
                        print(e)
                        price = 0

                    comp = Component(
                        category=item_category,
                        name=name,
                        new=new_or_ref(name),
                        price=price
                    )

                    components.append(comp)

                overall_info[category_name] = 0

            overall_info[category_name] += len(components) - total_components_count_before
            print(f"\t\tВсего в категории - {overall_info[category_name]}\n")

        print("Всего найдено комплектующих:", len(components))
        categories_sorted_by_amount = sorted(overall_info, key=lambda x: overall_info[x], reverse=True)
        overall_info = {k: overall_info[k] for k in categories_sorted_by_amount}
        print_dict(overall_info)

        print("Получено комплектующих:", len(components))
        components.sort(key=lambda comp: (comp.category, comp.name))
        return components


    @staticmethod
    def get_servers() -> list[Server]:
        servers = list()

        response = requests_try_to_get_max_5x(CATALOG_CONFIGURATORS_URL, HEADERS)
        if response is None:
            print("Не удалось загрузить страницу", CATALOG_CONFIGURATORS_URL)
            return []
        html = BeautifulSoup(response.text, "lxml")
        total_pages = get_pages_amount(html)

        # Загрузить каждую страницу серверов
        for page in range(1, total_pages + 1):
            print(f"\tСтраница {page} - получение")
            time.sleep(1.5)
            if page != 1:
                url = CATALOG_CONFIGURATORS_URL + PAGEN + str(page)
                response = requests_try_to_get_max_5x(url, HEADERS)
                if response is None:
                    print("Не удалось загрузить страницу", url)
                    continue
                html = BeautifulSoup(response.text, "lxml")

            body = html.find("body")
            products = body.find("div", class_="products").find_all("div", class_="product card")
            for item in products:
                item_header = item.find(class_="card-title")
                name = format_name(item_header.text.strip())

                try:
                    url = item_header.find("a")
                    url = url.attrs.get("href", None).strip()
                except Exception as e:
                    print(e)
                    url = None

                try:
                    price = item.find(class_="card-footer").text.strip()
                    price = format_price(price)
                except Exception as e:
                    print(e)
                    price = 0

                server = Server(
                    name=name,
                    new=new_or_ref(name),
                    card_price=price,
                    config_url=url
                )

                server.get_specs_from_name()

                servers.append(server)

        print()
        sort_servers_by_category_and_name(servers)
        for server in servers:
            print(server)

        print("\nНайдено серверов:", len(servers))
        return servers
