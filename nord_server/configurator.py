from modules.parser import *
from nord_server.constants import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_config_components(servers: list[Server]):
        servers_with_config = list()

        good_servers = [s for s in servers if s.category < 4]
        for server in good_servers:
            if server.config_url is None:
                continue

            print(server.name)
            response = requests_try_to_get_max_5x(server.config_url, HEADERS)
            if response is None:
                print("Не удалось загрузить страницу", server.config_url)
                continue

            html = BeautifulSoup(response.text, "lxml")
            form = html.body.find("form", {
                'method': 'POST',
                'action': 'https://nord-server.ru/order'
            })

            price = form.find("meta", {'itemprop': "price"})
            price = format_price(price.attrs.get('content', 0))

            server.config_price = price
            print(f"    {price}")

            categories_html = Configurator.get_config_components_categories_html(form)

            cfg_components = Configurator.get_components_from_categories(categories_html, server)
            server.components = cfg_components

            servers_with_config.append(server)

            print("    Найдено комплектующих:", len(cfg_components))
            print()
            time.sleep(1.5)

        return servers_with_config + [s for s in servers if s.category > 3]

    @staticmethod
    def get_config_components_categories_html(config_soup: BeautifulSoup) -> dict[str, BeautifulSoup]:
        """
        Функция собирает категории комплектующих конфигуратора и возвращает их в виде словаря:

        {
            "Оперативная память": category -> BeautifulSoup,

            "Процессоры": category -> BeautifulSoup,

            ...
        }
        """
        categories = dict()

        category_normal_name = {
            "процессор": "Процессоры",
            "салазки": "Салазки",
            "рельсы": "Рельсы",
        }

        table = config_soup.find("table")
        tbody = table.find("tbody")
        table_items = tbody.find_all("tr", recursive=False)
        for item in table_items:
            name_tag = item.find('td', string=True)
            comps_tag = item.find('select', class_="form-control")

            name = name_tag.string
            name = format_name(name.strip())

            comps = comps_tag.find_all("option", text=True)

            lower_name = name.lower()

            for bad, good in category_normal_name.items():
                if bad in lower_name:
                    name = good
                    break

            categories[name] = comps

        return categories

    @staticmethod
    def get_components_from_categories(categories_html: dict, server: Server) -> list[Component]:
        """
        Метод для получения комплектующих из каждой категории конфигуратора
        """

        cfg_components = list()
        for category_name, category_html in categories_html.items():
            for option in category_html:
                try:
                    name = option.string
                    name = re.sub(r" - \d.*$", "", name.strip(), re.I)
                    if 'HОВЫЙ' in name:
                        name = re.sub('HОВЫЙ', "НОВЫЙ", name, re.I)
                    name = format_name(name)
                    if re.search("Нет в наличии", name, re.I) is not None:
                        continue

                except Exception as e:
                    print("Ошибка: Неправильное имя комплектующего", str(option))
                    continue

                try:
                    price = option.attrs.get('data-price', 0)
                    price = format_price(price)
                except Exception as e:
                    print("Ошибка: Неправильная цена комплектующего", str(option))
                    price = 0

                comp = Component(
                    category=category_name,
                    name=name,
                    new=new_or_ref(name),
                    checked=False,
                    checked_amount=0,
                    price=price,
                    resource=f"{server.name}|{server.config_url}"
                )
                if "салазки" in category_name.lower() or "рельсы" in category_name.lower():
                    comp.name = add_info_to_trays_and_rails(category_name, comp, server)

                cfg_components.append(comp)

        return cfg_components
