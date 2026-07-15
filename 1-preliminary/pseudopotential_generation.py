import os.path
from pathlib import Path
import shutil
from eos_workflow.utilities import OncvpspInput
import subprocess
from abipy.ppcodes.oncv_parser import OncvParser
from monty.termcolor import cprint

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

IEXC = {'PBE': 4, 'LDA': "-001012", 'PBEsol': "-116133"}


def pseudodojo_generation(
        old_pseudo_path: str,
        oncvpsp_path: str,
        version: str,
        new_pseudo_path: str | None = None,
        xc: str = "PBE",
        relative: str = 'SR',
        accuracy: str = "standard",
        full_periodic_table: bool = True,
):
    if new_pseudo_path is None:
        new_pseudo_path = os.getcwd()
    dojo_name = f"ONCVPSP-{xc}-{relative}-PDv{version}"
    new_pseudo_path = os.path.join(new_pseudo_path, dojo_name)
    ps_folder = Path(new_pseudo_path)
    ps_folder.mkdir(exist_ok=True)

    element_names = os.path.join(old_pseudo_path, f"{accuracy}.txt")
    # shutil.copy(element_names, new_pseudo_path)
    basenames = []
    new_results = []
    with open(element_names, 'r') as fp:
        results = fp.readlines()
    for element in ATOMIC_SYMBOLS:
        filename = None
        for line in results:
            el = line.split('/')[0]
            tmp = line.strip().split('/')[1]
            if el == element:
                element_folder = ps_folder / f"{element}"
                element_folder.mkdir(exist_ok=True)
                filename = tmp
                if relative == 'FR' and '_r' not in filename:
                    tmp = tmp.replace('.psp8', '_r.psp8')
                    line = line.replace('.psp8', '_r.psp8')
                    basenames.append(f'{el}/{tmp}\n')
                    new_results.append(line)
                if relative == 'SR' and '_r' in filename:
                    tmp = tmp.replace('_r.psp8', '.psp8')
                    line = line.replace('_r.psp8', '.psp8')
                    basenames.append(f'{el}/{tmp}\n')
                    new_results.append(line)
                break
        if filename is None:
            if full_periodic_table:
                cprint(f"{element} not found in {element_names}", color="yellow")
            continue

        filename = filename.replace('.psp8', '.in')
        src = Path(old_pseudo_path) / f"{element}" / filename
        if relative == 'FR' and '_r' not in filename:
            filename = filename.replace('.in', '_r.in')
        ln = element_folder / filename

        shutil.copy(src, ln)
        ln_input = OncvpspInput(file_path=str(ln))
        try:
            iexc = IEXC[xc]
        except KeyError:
            cprint(f'{xc} is not a key in f{IEXC}', color="red")
            exit(-1)
        ln_input.basic_setting['iexc'] = iexc
        ln_input.basic_setting['psfile'] = 'both'
        ln_input.write_to_path(ln)

        ln_output = str(ln).replace('.in', '.out')
        if relative == 'SR':
            oncvpsp = Path(oncvpsp_path) / 'oncvpsp.x'
        else:
            oncvpsp = Path(oncvpsp_path) / 'oncvpspr.x'

        with ln.open("rb") as fin, Path(ln_output).open("wb") as fout:
            subprocess.run([str(oncvpsp)], stdin=fin, stdout=fout, check=True)

        ln_parser = OncvParser(ln_output).scan()
        if not ln_parser.run_completed:
            cprint(f'Problems in {element} psp generation!', color="red")
            continue
        if len(ln_parser.errors) != 0:
            cprint(f'Problems in {element} psp results!', color="red")
            for line in ln_parser.errors:
                print(line)
            continue

        psp8_path = str(ln_output).replace('.out', '.psp8')
        # Extract psp8 files from the oncvpsp output and write it to file.
        with open(psp8_path, "wt") as fh:
            fh.write(ln_parser.get_psp8_str())

        # Write UPF2 file if available.
        upf_str = ln_parser.get_upf_str()
        if upf_str is not None:
            with open(psp8_path.replace(".psp8", ".upf"), "wt") as fh:
                fh.write(upf_str)
        else:
            cprint("UPF2 file has not been produced. Use `both` in input file!", color="red")

        psml_raw = 'ONCVPSP.psml'
        psml_ln = element_folder / filename
        psml_ln = str(psml_ln).replace('.in', '.psml')
        command = ['mv', str(psml_raw), psml_ln]
        subprocess.run(command, check=True)

        cprint(f"{element} psp is successfully generated.", color="green")

    new_pseudo_path = os.path.join(new_pseudo_path, f"{accuracy}.txt")
    with open(new_pseudo_path, 'w+') as fp:
        fp.writelines(new_results)


if __name__ == "__main__":
    oncvpsp_path = '/home/wjing/project/git_repo/oncvpsp/src'
    old = '/home/wjing/PycharmProjects/PseudoDojo-verification-scripts/ONCVPSP-PBE-SR-PDv0.6'
    XC = 'LDA'
    relative_format = 'SR'
    new = '/home/wjing/PycharmProjects/pseudos_generation/'
    version = "0.6"
    accuracy = 'stringent'

    pseudodojo_generation(old_pseudo_path=old, oncvpsp_path=oncvpsp_path, version=version, new_pseudo_path=new, accuracy=accuracy, relative=relative_format, xc=XC)


