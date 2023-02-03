from pathlib import Path
from dataclasses import dataclass
from modules.parser_tools import Patterns, search_from_pattern, sub_not_digits, get_options, get_unique_name


@dataclass(slots=True, kw_only=True)
class RAID:
    model: str = ""
    speed: str = ""


specs = (
    Patterns.RAID.model,
    Patterns.RAM.capacity,
)


def get_raid_specs_keys(all_raid):
    for raid in all_raid:
        raid_specs: list = [search_from_pattern(spec, raid.name) for spec in specs]
        raid.key = RAID(
            model=raid_specs[0] if raid_specs[0] is not None else '',
            speed=str(sub_not_digits(raid_specs[1])) if raid_specs[1] is not None else '',
        )
    return all_raid


def get_raid_name(raid_item: RAID, gs_raid_final: dict):
    raid_name = list()
    if len(raid_item.model):
        raid_name.append(f"{raid_item.model}")
    if len(raid_item.speed):
        raid_name.append(f"{raid_item.speed}Gb/s")

    raid_name = " ".join([i for i in raid_name if len(i.strip())])

    return get_unique_name(raid_name, gs_raid_final)


def get_gs_raid_item(gs_raid):
    return RAID(
        model=gs_raid.get('Model', ''),
        speed=gs_raid.get('Bandwidth (Gb/s)', ''),
    )


def raid_process(all_raid):
    gs_raid_final = dict()
    raid_options = get_options(Path.cwd() / "Options.xlsx",
                               sheet_name="RAID")
    if raid_options is None:
        return {}, all_raid

    if not len(all_raid):
        for gs_raid in raid_options:
            gs_raid_item = get_gs_raid_item(gs_raid)
            raid_name = get_raid_name(gs_raid_item, gs_raid_final)
            gs_raid_final[raid_name] = 0
        return gs_raid_final, all_raid

    all_raid = get_raid_specs_keys(all_raid)

    for gs_raid in raid_options:
        gs_raid_item = get_gs_raid_item(gs_raid)
        gs_raid_item_model = gs_raid_item.model.split()
        raid_from_parser = None
        for raid in all_raid:
            good = list()
            for attr in ['speed']:
                if isinstance(getattr(gs_raid_item, attr), str):
                    good.append(getattr(raid.key, attr).upper() == getattr(gs_raid_item, attr).upper())
                else:
                    good.append(getattr(raid.key, attr) in getattr(gs_raid_item, attr))
            for word in gs_raid_item_model:
                word = word.upper()
                if word not in raid.name.upper():
                    good.append(False)
                    break
            else:
                good.append(True)

            good = all(good)
            if good:
                raid.we_need = True
                raid_from_parser = raid
                break

        price = raid_from_parser.price if raid_from_parser is not None else 0

        raid_name = get_raid_name(gs_raid_item, gs_raid_final)

        gs_raid_final[raid_name] = price

    return gs_raid_final, all_raid


__all__ = ["raid_process"]
