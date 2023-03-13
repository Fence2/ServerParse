import re

import bs4
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from modules.parser import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def _page_loaded(tag: bs4.Tag):
        main_tag = tag.find(class_='main')
        if main_tag:
            price_tag = main_tag.find('span', attrs={'id': 'total_value'})
            if price_tag:
                return re.search(r"\d+", price_tag.text)

        return False

    @staticmethod
    def get_config_components(servers: list[Server]) -> (list[Server], list[Component]):
        servers_with_config = list()
        try:
            good_servers = [s for s in servers if s.category < 4]
            for server in good_servers:
                if server.config_url is None:
                    continue

                result = selenium_try_to_get_max_5x(
                    driver=Configurator.driver,
                    url=server.config_url,
                    lambda_condition=Configurator._page_loaded
                )
                if result is not None:
                    Configurator.driver = result
                else:
                    continue

                html = BeautifulSoup(Configurator.driver.page_source, "lxml")
                main = html.body.find("main", class_="main")

                configs = Configurator.get_other_configs(main)

                for i, config in enumerate(configs):
                    name = Configurator.get_server_name(main)
                    if len(configs) > 1:
                        try:
                            config_id = config.find("input", {"class": 'item-chassi', "id": True}).attrs['id']
                            config_name = config.find("span", class_="js-item-name")
                            config_name = config_name.string.strip()
                            config_name = format_name(config_name)

                            def is_page_loaded(html):
                                try:
                                    soup = BeautifulSoup(html.page_source, "lxml")
                                    soup_main = soup.find("main")
                                    soup_name = Configurator.get_server_name(soup_main)
                                    soup_name = format_name(soup_name)
                                    if config_name.lower() in soup_name.lower():
                                        return True
                                except Exception as e:
                                    print(e)
                                finally:
                                    return False

                            xpath = r"""//main//section//div[@class='container']//div[@class='conf-tabs-data']//div[@class='conf-section conf-section--chassi is-open']//ul[@class='conf-section__list']//li""" + f"[{str(i + 1)}]"

                            config_tag = Configurator.driver.find_element(By.XPATH, xpath)
                            span_input_tag = config_tag.find_element(
                                By.XPATH,
                                xpath + "//label[@class='radio']//span[@class='radio__label']")
                            k = 0
                            while k < 5:
                                span_input_tag.click()
                                time.sleep(2)
                                WebDriverWait(config_tag, 15).until(lambda word: is_page_loaded)

                                html = BeautifulSoup(Configurator.driver.page_source, "lxml")
                                main = html.body.find("main", class_="main")
                                name = Configurator.get_server_name(main)
                                if config_name.lower() in name.lower():
                                    break
                                k += 1

                        except Exception as e:
                            print(e)
                            continue

                    print(name)
                    price = Configurator.get_server_price(main)
                    print("   ", price)

                    new_server = Server(
                        name=name,
                        new=server.new,
                        card_price=price,
                        config_url=server.config_url,
                        category=server.category,
                        brand=server.brand,
                        model=server.model,
                        generation=server.generation,
                        units=server.units
                    )
                    categories_html = Configurator.get_config_components_categories_html(main)

                    cfg_components = Configurator.get_components_from_categories(categories_html, new_server)
                    new_server.components = cfg_components

                    servers_with_config.append(new_server)

                    print("    Найдено комплектующих:", len(cfg_components))
                    print()
                    time.sleep(0.7)

        except Exception as e:
            print(e)
        finally:
            Configurator.driver.close()
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
        bad_categories = [
            'шасси',
            # '',
            'гарантия',
        ]

        category_normal_name = {
            "процессоры": "Процессоры",
            "оперативная память": "Оперативная память",
            "корзина на": "Жёсткие диски",
            "салазки": "Салазки",
            "raid-контроллер": "RAID-контроллер",
            "сетевая карта": "Сетевая карта",
            "монтаж и подключение": "Рельсы",
            'удалённое администрирование': "Удалённое управление"
        }

        categories_html = config_soup.find("div", class_="conf-tabs-data")
        categories_html = categories_html.find(
            lambda tag: tag.string is not None and tag.string.upper() == "ПРОЦЕССОРЫ")
        categories_html = categories_html.parent.parent
        categories_html = categories_html.find_all("div", class_="conf-section")

        for c_html in categories_html:
            category_name = c_html.find("h4", class_="conf-section__title")
            category_name = format_name(category_name.text.strip())
            lower_name = category_name.lower()
            items = c_html.find("ul", class_="conf-section__list")

            if items.find("li", recursive=False) is None:
                continue

            if lower_name in bad_categories:
                continue

            for bad, good in category_normal_name.items():
                if bad in lower_name:
                    category_name = good
                    break

            categories[category_name] = items

        return categories

    @staticmethod
    def get_components_from_categories(categories_html: dict, server: Server) -> list[Component]:
        """
        Метод для получения комплектующих из каждой категории конфигуратора
        """

        def price_and_sale(tag: bs4.Tag):
            """
            Вспомогательный метод для поиска тега с ценами
            """
            parent = tag.parent
            parent_good_name = parent.name == "label"
            if not parent_good_name:
                return False

            parent_good_class = 'radio' in parent.attrs['class'] or 'checkbox' in parent.attrs['class']
            if not parent_good_class:
                return False

            good_name = tag.name == "input"
            if not good_name:
                return False

            has_type = tag.attrs.get('type') is not None
            has_value = tag.attrs.get('value') is not None
            if has_type:
                good_type = 'radio' in tag.attrs['type'] or 'checkbox' in tag.attrs['type']
            else:
                return False

            if not good_type or not has_value:
                return False

            # Good
            return True

        cfg_components = list()
        for category_name, category_html in categories_html.items():
            goods = category_html.find_all("li", class_="conf-section__item")

            for item in goods:
                temp_category_name = category_name
                if 'show-more' in item.attrs['class'] or 'list-info' in item.attrs['class']:
                    continue

                try:
                    name = item.find("span", class_="js-item-name")
                    name = name.find(text=True, recursive=False).text.strip()
                    if category_name.lower() == "процессоры":
                        if "Сore" in name:
                            name = re.sub("Сore", "Core", name, flags=re.I)

                    name = format_name(name)
                    if "питани" in category_name.lower() and "2 шт" in name.lower():
                        name = "2x " + name
                except Exception as e:
                    print("Ошибка: Неправильное имя комплектующего", str(item))
                    continue

                try:
                    input_tag = item.find(price_and_sale)

                    price = input_tag.attrs['value']
                    price = format_price(price)
                except Exception as e:
                    print("Ошибка: Неправильная цена комплектующего", str(item))
                    price = 0

                try:
                    if 'is-checked' in item.attrs['class']:
                        checked = True
                        if input_tag.attrs['type'] == "radio":
                            checked_amount = 1
                        else:
                            counter_tag = item.find("input", {'class': 'js-item-counter', 'type': 'number'})
                            checked_amount = counter_tag.attrs['value']
                            checked_amount = int(checked_amount)
                    else:
                        checked = False
                        checked_amount = 0
                except Exception as e:
                    checked = False
                    checked_amount = 0

                try:
                    sale = item.find("span", class_='discount-compl')
                    sale = sub_not_digits(sale.text)
                    no_sale_price = int(price * 100 / (100 - sale))
                except Exception as e:
                    no_sale_price = 0

                if "рельсы" in category_name.lower():
                    if "рельсы" not in name.lower():
                        temp_category_name = "Монтаж и подключение"

                comp = Component(
                    category=category_name if temp_category_name == category_name else temp_category_name,
                    name=name,
                    new=new_or_ref(name),
                    checked=checked,
                    checked_amount=checked_amount,
                    price=price,
                    no_sale_price=no_sale_price,
                    resource=f"{server.name} | {server.config_url}"
                )
                if "салазки" in temp_category_name.lower() or "рельсы" in temp_category_name.lower():
                    comp.name = add_info_to_trays_and_rails(temp_category_name, comp, server)

                cfg_components.append(comp)

        return cfg_components

    @staticmethod
    def get_server_name(container: bs4.Tag):
        configurator__title = container.find("div", class_="configurator__title")
        h1 = configurator__title.find("h1")
        name = format_name(h1.text.strip())
        return name

    @staticmethod
    def get_server_price(container: bs4.Tag):
        try:
            price = container.find("span", class_="total-value").text.strip()
            price = format_price(price)
            return price
        except Exception as e:
            return 0

    @staticmethod
    def get_other_configs(container: bs4.Tag):
        configs_h4 = container.find(lambda tag: tag.name == "h4" and tag.string.strip().lower() == "шасси")
        configs = configs_h4.parent
        configs = configs.find_all(class_="conf-section__item")
        return configs
