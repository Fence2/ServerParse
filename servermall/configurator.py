import random
import re

import bs4
from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    delay = 20

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_config_components(servers: list[Server]) -> (list[Server], list[Component]):
        servers_with_config = list()

        Configurator.driver = selenium_try_to_get_max_5x(Configurator.driver, MAIN_URL, True)
        time.sleep(Configurator.delay)

        random.shuffle(RANDOM_URL)

        for url in RANDOM_URL[:random.randint(1, 3)]:
            Configurator.driver = selenium_try_to_get_max_5x(Configurator.driver, url, True)
            time.sleep(Configurator.delay)

        good_servers = [s for s in servers if s.category < 4]
        random.shuffle(good_servers)
        for server_n, server in enumerate(good_servers):
            print(f"Обработка сервера {server_n + 1} / {len(good_servers)}")
            if server.config_url is None or not len(server.config_url):
                continue
            print(server.name)
            result = selenium_try_to_get_max_5x(
                driver=Configurator.driver,
                url=server.config_url,
                lambda_condition=Configurator._get_price
            )
            if result is None:
                continue

            try:
                soup: bs4.Tag = BeautifulSoup(Configurator.driver.page_source, "lxml").body
            except Exception as e:
                print("Ошибка:", e)
                continue

            try:
                price = soup.find(Configurator._get_price).text
                price = format_price(price)
            except Exception:
                price = 0

            server.config_price = price
            print(f"\t{price} руб.")

            try:
                form = soup.find("form", attrs={'id': 'configurator-form'})
                categories_html = Configurator.get_config_components_categories_html(form)

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

        Configurator.driver.close()
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

        def _get_conf_groups(tag: bs4.Tag, cpu_amount):
            result = tag.name == 'div' and \
                     'configurator__field-group' in tag.attrs.get('class', '') and \
                     tag.attrs.get('data-proc-count', '') == str(cpu_amount)
            return result

        categories: dict[str, bs4.ResultSet] = dict()

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

        # Находим количество процессоров
        processor_count = 1
        try:
            processor_count_div = config_soup.find('div', attrs={'class': 'configurator__main-field'})
            processor_count = Configurator._get_processor_count(processor_count_div)
            for i in processor_count:
                if i[1]:
                    processor_count = i[0]
                    break
        except Exception:
            pass

        # Получение остальных комплектующих
        categories_html = config_soup.find_all("fieldset", recursive=False)
        c_html: bs4.Tag
        for c_html in categories_html:
            try:
                category_name = c_html.find(class_="accordion__summary").find('span', string=True)
                category_name = format_name(category_name.text.strip())
                lower_name = category_name.lower()
                for pattern, normal_name in category_normal_name.items():
                    if re.search(pattern, lower_name, flags=re.I) is not None:
                        category_name = normal_name
                        break
                items = c_html.find("div", class_="accordion__details")
            except Exception:
                print("Ошибка в получении товаров 1 категории {1}")
                continue

            try:
                depends_on_proc = items.find_all("div", class_="configurator__field-groups")

                if depends_on_proc is not None and len(depends_on_proc):
                    # CPU AND RAM
                    if category_name == "Оперативная память":
                        groups_items = items.find(lambda tag: _get_conf_groups(tag, processor_count))
                    else:
                        groups_items = items.find(lambda tag: _get_conf_groups(tag, 2))
                        if not groups_items:
                            groups_items = items.find(lambda tag: _get_conf_groups(tag, 1))

                    if groups_items:
                        items = groups_items

                items = items.find_all('div', class_="configurator__field")

                if category_name not in categories:
                    categories[category_name] = items
                else:
                    categories[category_name].extend(items)
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
                    label = item.find('label')
                    spans = label.find_all('span')
                    try:
                        name = [s for s in spans if len(s.text.strip())][0].text.strip()
                    except Exception:
                        name = label.text.strip()
                    name = re.sub("S[АA][ТT][АA]", "SATA", name, flags=re.I)
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
                    price_item = item.find('div', class_='configurator__field-value')
                    if price_item:
                        if price_item.has_attr('data-price'):
                            price = format_price(price_item.attrs['data-price'])
                        else:
                            price = format_price(price_item.text.strip())
                except Exception as e:
                    print("Ошибка при поиске цены комплектующего:", e)
                    print(f"{category_name} {str(item)}")

                # is checked
                input_item = label.find("input")
                checked = 'checked' in input_item.attrs
                checked_amount = 0
                if checked:
                    amount = item.find('input', {'type': 'number', 'value': True})
                    try:
                        checked_amount = amount.attrs['value'] or '1' if amount else '1'
                        checked_amount = int(checked_amount)
                    except Exception as e:
                        # print("Ошибка при поиске выбранности комплектующего:", e)
                        # print(f"{category_name} {str(item)}")
                        checked_amount = 1

                if category_name == "Жёсткие диски" and \
                    re.search(r"\d+\s*[MGT]B", name, flags=re.I) is None and \
                        re.search("салазк|переходник", name, flags=re.I) is not None:
                    category_name = "Салазки"

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

    @staticmethod
    def _get_price(tag: bs4.Tag) -> bool:
        tag_is_price = tag.name == "div" and \
                       'class' in tag.attrs and \
                       'js-offer-total-price' in tag.attrs['class'] and \
                       len(tag.text) and \
                       len(re.sub(r"\D", "", tag.text)) >= 3
        return tag_is_price

    @staticmethod
    def _get_processor_count(processor_count_div: bs4.Tag) -> list[tuple]:
        processor_count_div = processor_count_div.find(
            'div',
            attrs={'class': ['configurator__main-field-group', 'radio-group']}
        )
        processor_count_radio = processor_count_div.find_all(attrs={'class': 'radio'}, recursive=False)
        for radio in processor_count_radio:
            radio_elem = radio.find('input', attrs={'type': 'radio'})
            if radio_elem is not None:
                if 'checked' in radio_elem.attrs:
                    processor_default_amount = int(radio_elem.attrs.get('value', '1'))
                    break
        else:
            processor_default_amount = 1

        return [(i + 1, i + 1 == processor_default_amount) for i in range(len(processor_count_radio))]
