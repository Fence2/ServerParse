from openpyxl import Workbook
from openpyxl.styles import Font

from modules.parser_tools import get_today_full_date_str, format_excel_columns_width


def process_servers(
        servers: list,

        other_servers: list,

        folder_to_save,
        filename: str
):
    import modules.galtsystems_data_processor.process_by_category as process_by_category

    servers = list(sorted(servers, key=lambda x: (x.category, x.config_price)))
    processed_data = process_by_category.servers.servers_process(servers)
    gs_servers, good_cfg, part_cfg, bad_cfg = processed_data

    wb = Workbook()
    ws_gs = wb.active
    ws_gs.title = "ГалтСистемс"
    ws_gs.append(["Категория", "Название", "Цена"])

    ws_good = wb.create_sheet(title="Идеальный конфиг")

    # Первый лист: Сводная инфо по хорошим серверам, нужным нашей компании
    for k, v in gs_servers.items():
        ws_gs.append(["Сервер", k, v])
    ws_gs = format_excel_columns_width(ws_gs)

    # Остальные листы

    def write_cfg_to_book(cfg_servers: dict, wsheet):
        rows = 0
        for server in cfg_servers.values():
            url = ''
            for i, line in enumerate(server):
                if not i:
                    url = line[0][1]
                    line[0] = line[0][0]

                wsheet.append(line)

            if url != '':
                wsheet.cell(row=rows + 1, column=1).hyperlink = url
                wsheet.cell(row=rows + 1, column=1).style = "Hyperlink"
                wsheet.cell(row=rows + 1, column=3).font = Font(bold=True)
                wsheet.cell(row=rows + 1, column=4).font = Font(bold=True)

            rows += len(server)

    if len(good_cfg):
        write_cfg_to_book(good_cfg, ws_good)
        ws_good = format_excel_columns_width(ws_good)
    if len(part_cfg):
        ws_part = wb.create_sheet(title="Не полный конфиг")
        write_cfg_to_book(part_cfg, ws_part)
        ws_part = format_excel_columns_width(ws_part)
    if len(bad_cfg):
        ws_bad = wb.create_sheet(title="Плохой конфиг")
        write_cfg_to_book(bad_cfg, ws_bad)
        ws_bad = format_excel_columns_width(ws_bad)

    filename = filename + "_" + get_today_full_date_str() + ".xlsx"

    wb.save(folder_to_save / filename)

    print("Успешное сохранение данных с парсера в файл: ", folder_to_save / filename)
    return True
