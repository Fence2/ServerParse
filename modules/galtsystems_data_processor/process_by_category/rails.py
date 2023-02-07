from pathlib import Path
from dataclasses import dataclass
from modules.parser.tools import Patterns, search_from_pattern, sub_not_digits, get_options, get_unique_name, get_attrs


@dataclass(slots=True, kw_only=True)
class RAILS:
    brand: str = ""
    height: str = ""
    form_factor: str = ""
    keys: str = ""


specs = (
    Patterns.SERVER.brand,
    Patterns.SERVER.units,
    Patterns.TRAY.small_form_fact,
    Patterns.TRAY.large_form_fact,
)


def get_rails_specs_keys(all_rails):
    for rails in all_rails:
        rails_specs: list = [search_from_pattern(spec, rails.name) for spec in specs]
        rails.key = RAILS(
            brand=rails_specs[0] if rails_specs[0] is not None else '',
            height=str(sub_not_digits(rails_specs[1])) if rails_specs[1] is not None else '',
        )
        if rails_specs[2] is not None and rails_specs[3] is None:
            rails.key.form_factor = "SFF"
        elif rails_specs[2] is None and rails_specs[3] is not None:
            rails.key.form_factor = "LFF"
        elif rails_specs[2] is not None and rails_specs[3] is not None:
            rails.key.form_factor = "SFF + LFF"
        else:
            rails.key.form_factor = ""
    return all_rails


def get_rails_name(rails_item: RAILS, gs_rails_final: dict):
    rails_name = list()
    rails_name.append(rails_item.brand)
    if len(rails_item.height):
        rails_name.append(f"{rails_item.height}U")
    if len(rails_item.form_factor):
        rails_name.append(f"{rails_item.form_factor}")
    if len(rails_item.keys):
        rails_name.append(f"{','.join(rails_item.keys)}")

    rails_name = " ".join([i for i in rails_name if len(i.strip())])

    return get_unique_name(rails_name, gs_rails_final)


def get_gs_rails_item(gs_rails):
    item = RAILS(
        brand=gs_rails.get('Manufacturer', ''),
        height=gs_rails.get('Server form-factor', ''),
        form_factor=gs_rails.get('Slots form-factor', ''),
        keys=gs_rails.get('Word in name', ''),
    )
    if len(item.keys):
        if not isinstance(item.keys, list):
            item.keys = [item.keys]
    else:
        item.keys = []
    return item


def rails_process(all_rails):
    gs_rails_final = dict()
    rails_options = get_options(Path.cwd() / "Options.xlsx",
                                sheet_name="RAILS")
    if rails_options is None:
        return {}, all_rails

    if not len(all_rails):
        for gs_rails in rails_options:
            gs_rails_item = get_gs_rails_item(gs_rails)
            rails_name = get_rails_name(gs_rails_item, gs_rails_final)
            gs_rails_final[rails_name] = 0
        return gs_rails_final, all_rails

    all_rails = get_rails_specs_keys(all_rails)

    for gs_rails in rails_options:
        gs_rails_item = get_gs_rails_item(gs_rails)
        rails_from_parser = None
        for rails in all_rails:
            good = list()
            for attr in get_attrs(RAILS)[:-1]:
                if isinstance(getattr(gs_rails_item, attr), str):
                    if len(getattr(gs_rails_item, attr)):
                        good.append(getattr(rails.key, attr).upper() == getattr(gs_rails_item, attr).upper())
                    else:
                        good.append(True)
                else:
                    good.append(getattr(rails.key, attr) in getattr(gs_rails_item, attr))

            if len(gs_rails_item.keys):
                good_rails = [key.lower() in rails.name.lower() for key in gs_rails_item.keys]
                good.append(any(good_rails))
            else:
                good.append(True)

            good = all(good)
            if good:
                rails.we_need = True
                rails_from_parser = rails
                break

        price = rails_from_parser.price if rails_from_parser is not None else 0

        rails_name = get_rails_name(gs_rails_item, gs_rails_final)

        gs_rails_final[rails_name] = price

    return gs_rails_final, all_rails


__all__ = ["rails_process"]
