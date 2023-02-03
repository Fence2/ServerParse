import re
from pathlib import Path
from dataclasses import dataclass
from modules.parser_tools import Patterns, search_from_pattern, sub_not_digits, get_options, get_unique_name, get_attrs


@dataclass(slots=True, kw_only=True)
class TRAY:
    type: str = ""
    brand: str = ""
    form_factor: str = ""


specs = (
    Patterns.SERVER.brand,
    Patterns.TRAY.small_form_fact,
    Patterns.TRAY.large_form_fact,
    Patterns.TRAY.is_adapter,
)


def get_tray_specs_keys(all_tray):
    for tray in all_tray:
        tray_specs: list = [search_from_pattern(spec, tray.name) for spec in specs]
        tray.key = TRAY(
            brand=tray_specs[0] if tray_specs[0] is not None else '',
        )

        if tray_specs[1] is not None and tray_specs[2] is None:
            tray.key.form_factor = "SFF"
        elif tray_specs[1] is None and tray_specs[2] is not None:
            tray.key.form_factor = "LFF"
        elif tray_specs[1] is not None and tray_specs[2] is not None:
            tray.key.form_factor = "SFF + LFF"
        else:
            tray.key.form_factor = ""

        if tray_specs[3] is not None:
            tray.key.type = "Переходник"
        elif re.search(r"заглушк", tray.name, flags=re.I) is not None:
            tray.key.type = "Заглушки"
        elif re.search(r"корзин", tray.name, flags=re.I) is not None:
            tray.key.type = "Корзина"
        else:
            tray.key.type = "Салазки"

    return all_tray


def get_tray_name(tray_item: TRAY, gs_tray_final: dict):
    tray_name = list()
    if len(tray_item.type):
        tray_name.append(f"{tray_item.type}")
    if len(tray_item.brand):
        tray_name.append(f"{tray_item.brand}")
    if len(tray_item.form_factor):
        tray_name.append(f"{tray_item.form_factor}")

    tray_name = " ".join([i for i in tray_name if len(i.strip())])

    return get_unique_name(tray_name, gs_tray_final)


def get_gs_tray_item(gs_tray):
    return TRAY(
        type=gs_tray.get('Type', ''),
        brand=gs_tray.get('Manufacturer', ''),
        form_factor=gs_tray.get('Form-factor', ''),
    )


def tray_process(all_tray):
    gs_tray_final = dict()
    tray_options = get_options(Path.cwd() / "Options.xlsx",
                               sheet_name="OPTIONS")
    if tray_options is None:
        return {}, all_tray

    if not len(all_tray):
        for gs_tray in tray_options:
            gs_tray_item = get_gs_tray_item(gs_tray)
            tray_name = get_tray_name(gs_tray_item, gs_tray_final)
            gs_tray_final[tray_name] = 0
        return gs_tray_final, all_tray

    all_tray = get_tray_specs_keys(all_tray)

    for gs_tray in tray_options:
        gs_tray_item = get_gs_tray_item(gs_tray)
        tray_from_parser = None
        for tray in all_tray:
            good = list()
            for attr in get_attrs(TRAY):
                good.append(
                    getattr(tray.key, attr).upper() == getattr(gs_tray_item, attr).upper() if getattr(gs_tray_item,
                                                                                                      attr) != "" else True)

            good = all(good)
            if good:
                tray.we_need = True
                tray_from_parser = tray
                break

        price = tray_from_parser.price if tray_from_parser is not None else 0

        tray_name = get_tray_name(gs_tray_item, gs_tray_final)

        gs_tray_final[tray_name] = price

    return gs_tray_final, all_tray


__all__ = ["tray_process"]
