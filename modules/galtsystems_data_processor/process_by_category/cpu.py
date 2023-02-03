from pathlib import Path
from dataclasses import dataclass
from modules.parser_tools import Patterns, search_from_pattern, sub_not_digits, get_options, get_unique_name, get_attrs


@dataclass(slots=True, kw_only=True)
class CPU:
    brand: str = ""
    genX: str = ""
    genE: str = ""
    metal: str = ""
    model: str = ""
    version: str = ""
    new: str = ""


specs = (
    Patterns.CPU.brand,
    Patterns.CPU.genX,
    Patterns.CPU.metal,
    Patterns.CPU.genE,
    Patterns.CPU.model,
    Patterns.CPU.version,
    Patterns.NEW
)


def get_cpu_specs_keys(all_cpu):
    for cpu in all_cpu:
        cpu_specs: list = [search_from_pattern(spec, cpu.name) for spec in specs]
        cpu.key = CPU(
            brand=cpu_specs[0] if cpu_specs[0] is not None else '',
            genX='Y' if cpu_specs[1] is not None else '',
            metal=cpu_specs[2] if cpu_specs[2] is not None else '',
            genE=str(sub_not_digits(cpu_specs[3])) if cpu_specs[3] is not None else '',
            model=cpu_specs[4] if cpu_specs[4] is not None else '',
            version=str(sub_not_digits(cpu_specs[5])) if cpu_specs[5] is not None else '',
            new='Y' if cpu_specs[6] is not None else '',
        )
    return all_cpu


def get_cpu_name(cpu_item: CPU, gs_cpu_final: dict):
    cpu_name = list()
    cpu_name.append(cpu_item.brand)
    if len(cpu_item.genX):
        cpu_name.append(f"X{cpu_item.model}")
    elif len(cpu_item.metal):
        cpu_name.append(f"{cpu_item.metal} {cpu_item.model}")
    elif len(cpu_item.genE):
        cpu_name.append(f"E{cpu_item.genE}-{cpu_item.model}")
    else:
        cpu_name.append(cpu_item.model)

    if len(cpu_item.version):
        cpu_name.append("v" + cpu_item.version)
    if len(cpu_item.new):
        cpu_name.append("NEW")

    cpu_name = " ".join([i for i in cpu_name if len(i.strip())])

    return get_unique_name(cpu_name, gs_cpu_final)


def get_gs_cpu_item(gs_cpu):
    return CPU(
        brand=gs_cpu.get('Manufacturer', ''),
        genX=gs_cpu.get('X (Y/N)', '') if gs_cpu.get('X (Y/N)', '') == 'Y' else '',
        metal=gs_cpu.get('Bronze/Silver/Gold', ''),
        genE=gs_cpu.get('E (3/5)', ''),
        model=gs_cpu.get('Model (Digits and letters at the end)', ''),
        version=gs_cpu.get('Version', ''),
        new=gs_cpu.get('New (Y/N)' if gs_cpu.get('New (Y/N)', '') == 'Y' else '', ''),
    )


def cpu_process(all_cpu):
    gs_cpu_final = dict()
    cpu_options = get_options(Path.cwd() / "Options.xlsx",
                              sheet_name="CPU")
    if cpu_options is None:
        return {}, all_cpu

    if not len(all_cpu):
        for gs_cpu in cpu_options:
            gs_cpu_item = get_gs_cpu_item(gs_cpu)
            cpu_name = get_cpu_name(gs_cpu_item, gs_cpu_final)
            gs_cpu_final[cpu_name] = 0
        return gs_cpu_final, all_cpu

    all_cpu = get_cpu_specs_keys(all_cpu)

    for gs_cpu in cpu_options:
        gs_cpu_item = get_gs_cpu_item(gs_cpu)
        cpu_from_parser = None
        for cpu in all_cpu:
            good = list()
            for attr in get_attrs(CPU):
                if isinstance(getattr(gs_cpu_item, attr), str):
                    good.append(getattr(cpu.key, attr).upper() == getattr(gs_cpu_item, attr).upper())
                else:
                    good.append(getattr(cpu.key, attr) in getattr(gs_cpu_item, attr))

            good = all(good)
            if good:
                cpu.we_need = True
                cpu_from_parser = cpu
                break

        price = cpu_from_parser.price if cpu_from_parser is not None else 0

        cpu_name = get_cpu_name(gs_cpu_item, gs_cpu_final)

        gs_cpu_final[cpu_name] = price

    return gs_cpu_final, all_cpu


__all__ = ["cpu_process"]
