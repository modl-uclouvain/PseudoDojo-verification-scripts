import os
import re
from pathlib import Path
from monty.termcolor import cprint
from abipy.ppcodes.oncv_parser import OncvParser

ATOMIC_SYMBOLS = (
    'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne',
    'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca',
    'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn',
    'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr',
    'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn',
    'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd',
    'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb',
    'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
    'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th',
    'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm',
    'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',
    'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og',
)

IEXC_INT = {'PBE': 4, 'LDA': -1012, 'PBEsol': -116133}


def pd_check(
        pseudo_path,
        accuracy: str = "standard",
        xc: str = "PBE",
        relative: str = 'SR',
        full_periodic_table: bool = True,
):
    element_names = os.path.join(pseudo_path, f"{accuracy}.txt")

    reports = []
    with open(element_names, 'r') as fp:
        results = fp.readlines()
    for element in ATOMIC_SYMBOLS:
        error_flags = False
        filename = None
        for line in results:
            el = line.split('/')[0]
            ps_name = line.strip().split('/')[1]
            if el == element:
                if relative == 'FR' and '_r' not in ps_name:
                    cprint(f"{ps_name} missing \'_r\' suffix for full relativistic format", color="red")
                    reports.append(f"{element}: {ps_name} missing \'_r\' suffix for full relativistic format\n")
                    error_flags = True
                    break
                filename = os.path.join(pseudo_path, line.strip())
                ps_report = filename.replace('.psp8', '.out')
                if os.path.isfile(ps_report) is False:
                    cprint(f"{filename} is missing", color="red")
                    reports.append(f"{element}: {filename} is missing\n")
                    error_flags = True
                    filename = None
                    break
                ps_parser = OncvParser(ps_report).scan()
                if not ps_parser.run_completed:
                    cprint(f'{element} psp generation is not completed', color="red")
                    reports.append(f"{element}: psp generation is not completed\n")
                    error_flags = True
                    filename = None
                    break
                if len(ps_parser.errors) != 0:
                    cprint(f'ERROR happens in {element} psp results!', color="red")
                    reports.append(f"{element}: ERROR happens in {element} psp results\n")
                    for err in ps_parser.errors:
                        print(f"{err}")
                        reports.append(f'{element}: {err}\n')
                    error_flags = True
                    filename = None
                    break
                if ps_parser.iexc != IEXC_INT[xc]:
                    cprint(f"The XC of {ps_name}.out is {ps_parser.iexc}, not match the para: xc={xc} settings", color="red")
                    reports.append(f"{element}: The XC of {ps_name}.out is {ps_parser.iexc}, not match the para: xc={xc} settings\n")
                    error_flags = True
                    filename = None
                    break
                if os.path.isfile(filename) is False:
                    cprint(f"{filename} is missing", color="red")
                    reports.append(f"{element}: {filename} is missing\n")
                    error_flags = True
                    filename = None
                    break
                cprint(f"{element} is successful!", color="green")

        if filename is None:
            if full_periodic_table and not error_flags:
                cprint(f"{element} not found in {element_names}", color="yellow")
            continue

    report_file = os.path.join(pseudo_path, f'dojo-error-report-{accuracy}.txt')
    with open(report_file, 'w') as fp:
        fp.writelines(reports)


def clean_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    return line.split()


def parse_input(path):
    lines = []
    for line in Path(path).read_text().splitlines():
        items = clean_line(line)
        if items:
            lines.append(items)
    return lines


def parse_output(path):
    lines = []
    start_reading = False
    in_atomic_config = False

    for line in Path(path).read_text().splitlines():
        line = line.strip()

        if line.startswith("# ATOM AND REFERENCE CONFIGURATION"):
            start_reading = True
            in_atomic_config = True
            continue

        if not start_reading:
            continue

        if line.startswith("# PSEUDOPOTENTIAL AND OPTIMIZATION"):
            in_atomic_config = False
            continue

        if line.startswith("# nvcnf"):
            break

        items = clean_line(line)
        if not items:
            continue

        # Only remove energy column in the atomic n/l/f block
        if in_atomic_config and len(items) >= 4:
            try:
                int(items[0])
                int(items[1])
                float(items[2])
                items = items[:3]
            except ValueError:
                pass

        lines.append(items)

    return lines


def normalize_value(x):
    try:
        v = float(x)
        return f"{v:.8g}"
    except ValueError:
        return x.lower()


def normalize(lines):
    return [[normalize_value(x) for x in line] for line in lines]


def pd_compare(
        pseudo_path,
        accuracy: str = "standard",
        comparison_format: int = 0,
        another_pseudo_path=None,
):
    element_names = os.path.join(pseudo_path, f"{accuracy}.txt")

    reports = []
    if comparison_format == 0:
        reports.append("COMPARE .in AND .out/.psp8/.upf\n\n")
    elif comparison_format == 1:
        reports.append("COMPARE .in AND .out\n\n")
    elif comparison_format == 2:
        reports.append("COMPARE .in AND .psp8\n\n")
    elif comparison_format == 3:
        reports.append("COMPARE .in AND .upf\n\n")
    elif comparison_format == 4:
        reports.append(f"COMPARE .in BETWEEN {pseudo_path} AND {another_pseudo_path}\n\n")
    else:
        cprint('Unknown comparison format, skipping', color='red')
        reports.append('Unknown comparison format, skipping\n')

    with open(element_names, 'r') as fp:
        results = fp.readlines()
    for line in results:
        element = line.split('/')[0]
        filename = os.path.join(pseudo_path, line.strip())
        input_file = filename.replace('.psp8', '.in')
        inp = normalize(parse_input(input_file))

        output_files = []
        if comparison_format == 0:
            output_files.append(filename.replace('.psp8', '.out'))
            output_files.append(filename)
            output_files.append(filename.replace('.psp8', '.upf'))
        elif comparison_format == 1:
            output_file = filename.replace('.psp8', '.out')
            output_files.append(output_file)
        elif comparison_format == 2:
            output_file = filename
            output_files.append(output_file)
        elif comparison_format == 3:
            output_file = filename.replace('.psp8', '.upf')
            output_files.append(output_file)
        elif comparison_format == 4:
            output_file = os.path.join(another_pseudo_path, line.strip())
            if 'SR' in pseudo_path and 'FR' in another_pseudo_path:
                output_file = output_file.replace('.psp8', '_r.in')
            elif 'FR' in pseudo_path and 'SR' in another_pseudo_path:
                output_file = output_file.replace('_r.psp8', '.in')
            else:
                output_file = output_file.replace('.psp8', '.in')
            output_files.append(output_file)
        else:
            cprint('Unknown comparison format, skipping', color='red')

        for output_file in output_files:
            if os.path.isfile(output_file) is False:
                cprint(f'Could not found {output_file}', color='yellow')
                continue
            if comparison_format == 4:
                out = normalize(parse_input(output_file))
            else:
                out = normalize(parse_output(output_file))
            ps_name = output_file.split('/')[-1]
            if inp == out:
                cprint(f"{element} is OK: output parameters in *{ps_name}* match input parameters.", color='green')
                reports.append(f"{element} is OK: output parameters in *{ps_name}* match input parameters.\n")
            else:
                cprint(f"Mismatch found in *{ps_name}* of {element}.", color='red')
                reports.append(f"Mismatch found in *{ps_name}* of {element}.\n")
                for i, (a, b) in enumerate(zip(inp, out), start=1):
                    if a != b:
                        print(f"Line {i} (ignoring lines start with #):")
                        print("  input :", a)
                        print("  output:", b)
                        reports.append(f"Line {i} (ignoring lines start with #):\n")
                        reports.append(f"  input :{a}\n")
                        reports.append(f"  output:{b}\n")

                if len(inp) != len(out):
                    cprint(f"Different number of parsed lines: input={len(inp)}, output={len(out)}", color='red')
                    reports.append(f"Different number of parsed lines: input={len(inp)}, output={len(out)}\n")

    report_file = os.path.join(pseudo_path, f'dojo-comparison-report-{accuracy}.txt')
    with open(report_file, 'w') as fp:
        fp.writelines(reports)


if __name__ == "__main__":
    acc = 'stringent'
    pd_path = "/home/wjing/PycharmProjects/pseudos_generation/ONCVPSP-LDA-SR-PDv0.6"
    pd_check(
        pd_path,
        accuracy=acc,
        xc='LDA',
        full_periodic_table=False
    )

    pd_compare(
        pd_path,
        # another_pseudo_path="/home/wjing/PycharmProjects/PseudoDojo-verification-scripts/ONCVPSP-PBE-SR-PDv0.6",
        accuracy=acc,
        comparison_format=0,
    )
