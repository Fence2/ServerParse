from pathlib import Path
from openpyxl import Workbook
from modules.parser.tools import get_today_full_date_str, format_excel_columns_width, get_sheets


def process_components(
        cpu: list,
        ram: list,
        # network: list,
        raid: list,
        rails: list,
        tray: list,

        other_comp: list,
        folder_to_save,
        filename: str
):
    import modules.galtsystems_data_processor.process_by_category as process_by_category

    # CPU OK
    cpu = list(sorted(cpu, key=lambda x: x.price))
    gs_cpu_final, cpu = process_by_category.cpu_process(cpu)

    # RAM OK
    ram = list(sorted(ram, key=lambda x: x.price))
    gs_ram_final, ram = process_by_category.ram_process(ram)

    # # network OK
    # network = list(sorted(network, key=lambda x: x.price))
    # # gs_network_final, network_parser_data = process_by_category.network_process(network)

    # raid OK
    raid = list(sorted(raid, key=lambda x: x.price))
    gs_raid_final, raid = process_by_category.raid_process(raid)

    # rails OK
    rails = list(sorted(rails, key=lambda x: x.price))
    gs_rails_final, rails = process_by_category.rails_process(rails)

    # tray OK
    tray = list(sorted(tray, key=lambda x: x.price))
    gs_tray_final, tray = process_by_category.tray_process(tray)

    wb = Workbook()
    ws_gs = wb.active
    ws_gs.title = "ГалтСистемс"  # noqa
    ws_parser = wb.create_sheet(title="Все комплектующие конкурента")

    ws_gs.append(["Категория", "Название", "Цена"])
    ws_parser.append(["Категория", "Название", "Цена", "Цена без скидки"])

    def write_to_book(category, gs_data, parser_data):
        for gs_comp, gs_price in gs_data.items():
            line = [category, gs_comp, gs_price if str(gs_price).isnumeric() else str(gs_price)]
            ws_gs.append(line)

        for parser_comp in parser_data:
            line = [category, parser_comp.name, parser_comp.price, parser_comp.no_sale_price]
            ws_parser.append(line)

    sheet_names = get_sheets(Path.cwd() / "Options.xlsx")

    processing_dict = dict()
    if sheet_names is not None:
        for name in sheet_names:
            match name:
                case "RAM":
                    processing_dict['Оперативная память'] = (gs_ram_final, ram)
                case "CPU":
                    processing_dict['Процессоры'] = (gs_cpu_final, cpu)
                case "RAID":
                    processing_dict['Контроллер'] = (gs_raid_final, raid)
                case "RAILS":
                    processing_dict['Рельсы под серверы'] = (gs_rails_final, rails)
                case "OPTIONS":
                    processing_dict['Салазки для жестких дисков'] = (gs_tray_final, tray)

    for category, data in processing_dict.items():
        write_to_book(category, data[0], data[1])

    for comp in other_comp:
        line = [comp.category, comp.name, comp.price, comp.no_sale_price]
        ws_parser.append(line)

    ws_gs = format_excel_columns_width(ws_gs)
    ws_parser = format_excel_columns_width(ws_parser)

    filename = filename + "_" + get_today_full_date_str() + ".xlsx"

    wb.save(folder_to_save / filename)

    print("Успешное сохранение данных с парсера в файл: ", folder_to_save / filename)  # noqa
    return True
