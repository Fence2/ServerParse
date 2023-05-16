import re

import bs4
from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    delay = 3

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_config_components(servers: list[Server]) -> (list[Server], list[Component]):
        servers_with_config = list()

        good_servers = [s for s in servers if s.category < 4]
        for server_n, server in enumerate(good_servers):
            print(f"Обработка сервера {server_n + 1} / {len(good_servers)}")
            if server.config_url is None or not len(server.config_url):
                continue
            print(server.name)
            result = requests_try_to_get_max_5x(url=server.config_url, headers=HEADERS)
            if result is None:
                continue

            try:
                soup: bs4.Tag = BeautifulSoup(result.text, "lxml").body
            except Exception as e:
                print("Ошибка:", e)
                continue

            # Получение высоты сервера
            try:
                if server.units is None:
                    units = soup.find("td", text="Высота в юнитах")
                    units = units.next_sibling.next_sibling.text.strip()
                    if len(units):
                        server.units = units
                        print("\tУстановлена высота сервера:", units)
            except AttributeError:
                pass

            # Получение цен
            try:
                price_wrap = soup.find(class_="price-wrap")
                price = price_wrap.find("span", attrs={"itemprop": "price"}).attrs["content"]
                price = format_price(price)
            except AttributeError:
                price = 0

            try:
                no_sale_price = soup.find("div", attrs={"class": "old-price_el", "data-price": True}).attrs[
                    "data-price"]
                no_sale_price = format_price(no_sale_price)
            except AttributeError:
                no_sale_price = 0

            server.config_price = price
            server.no_sale_config_price = no_sale_price
            print(f"\t{price} руб.\n")
            if no_sale_price:
                print(f"\tПо скидке: {price} руб.")

            try:
                categories_html = Configurator.get_config_components_categories_html(soup)

                cfg_components = Configurator.get_components_from_categories(categories_html, server)
                server.components = cfg_components

                print("    Найдено комплектующих:", len(cfg_components))
                categories = set(i.category for i in cfg_components)
                components_dict = {c: 0 for c in categories}
                for comp in cfg_components:
                    components_dict[comp.category] += 1
                print_dict(components_dict, '\t')
            except Exception as e:
                print("Ошибка в получении комплектующих:", e)

            servers_with_config.append(server)
            print()
            time.sleep(Configurator.delay)

        return servers_with_config

    @staticmethod
    def get_config_components_categories_html(config_soup: bs4.Tag) -> dict[str, bs4.ResultSet]:
        """
        Функция собирает категории комплектующих конфигуратора и возвращает их в виде словаря:

        {
            "Оперативная память": category -> bs4.ResultSet,

            "Процессоры": category -> bs4.ResultSet,

            ...
        }
        """
        categories: dict[str, bs4.ResultSet] = dict()

        categories_html = config_soup.find_all("div", attrs={"class": "conf-item prop-cont"})
        c_html: bs4.Tag
        for c_html in categories_html:
            try:
                title = c_html.find(class_="conf-prop-title")
                category_name = title.find(class_="name").string.strip()
                category_name = format_name(category_name)
                lower_name = category_name.lower()
                if lower_name == "гарантия":
                    continue

                if re.search("Устройство резервного питания", lower_name, flags=re.I) is None:
                    category_name = normalize_category_name(category_name)

                items_soup = c_html.find(class_="conf-items")
                components_soups = items_soup.find_all(class_="conf-row")
            except Exception:
                print("Ошибка в получении товаров 1 категории {1}")
                continue
            try:
                if category_name not in categories:
                    categories[category_name] = components_soups
                else:
                    categories[category_name].extend(components_soups)
            except Exception:
                print("Ошибка в получении товаров 1 категории {2}")
                continue

        return categories

    @staticmethod
    def get_components_from_categories(categories_html: dict, server: Server) -> list[Component]:
        """
        Метод для получения комплектующих из каждой категории конфигуратора
        """
        components: list[Component] = list()
        for category_name, items in categories_html.items():
            original_category = category_name
            for item in items:
                category_name = original_category
                if not isinstance(item, bs4.Tag):
                    continue

                item: bs4.Tag

                # name
                try:
                    name = item.find(class_="name").text.strip()
                    name = format_name(name)
                except Exception:
                    print(f"Ошибка при поиске имени комплектующего:\n"
                          f"{category_name} {str(item)}")
                    continue

                if name.strip() == '':
                    print(f"Ошибка при поиске имени комплектующего - пустое имя:\n"
                          f"{category_name} {str(item)}")
                    continue

                # price
                price = 0
                try:
                    price = item.find(class_="price").string.strip()
                    price = format_price(price)
                except Exception as e:
                    print("Ошибка при поиске цены комплектующего:", e)
                    print(f"{category_name} {str(item)}")

                # is checked
                input_item = item.find("input")
                checked = 'checked' in input_item.attrs
                checked_amount = 0
                if checked:
                    amount = item.find('div', class_='num', recursive=False).find('input', {'type': 'text', 'value': True})
                    try:
                        checked_amount = amount.attrs['value'] or '1' if amount else '1'
                        checked_amount = int(checked_amount)
                    except Exception as e:
                        checked_amount = 1

                comp = Component(
                    category=category_name,
                    name=name,
                    new=new_or_ref(name),
                    checked=checked,
                    checked_amount=checked_amount,
                    price=price,
                    resource=f"{server.name}|{server.config_url}"
                )
                if category_name.title() in ["Салазки", "Рельсы"]:
                    comp.name = add_info_to_trays_and_rails(category_name, comp, server)

                components.append(comp)

        return components
