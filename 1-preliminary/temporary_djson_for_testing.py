import os
import json
from pathlib import Path
from eos_workflow.utilities import OncvpspInput
from collections import OrderedDict
from monty.termcolor import cprint
from abipy.flowtk.psrepos import md5_for_filepath

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
XC_NAME ={'PBE': 'PBE', 'LDA': 'PW', 'PBEsol': 'PBEsol'}


def temporary_djson_generation(
        version: str,
        pseudo_path: str,
        xc: str = "PBE",
        relative: str = 'SR',
        accuracy: str = "standard"
):
    dojo_name = f"ONCVPSP-{xc}-{relative}-PDv{version}"
    element_names = f"{pseudo_path}/{accuracy}.txt"
    ps_folder = Path(pseudo_path)

    # Add template for dojo_info section
    d = OrderedDict()
    d['pp_type'] = 'NC'
    d['description'] = "A temporary djson used to obtain hints"
    d['xc_name'] = XC_NAME[xc]
    d['references'] = ['Dojo paper']
    d['authors'] = ['W. Jing', "M. J. van Setten", "M. Giantomassi"]
    d['dojo_dir'] = dojo_name

    with open(element_names, 'r') as fp:
        results = fp.readlines()
    meta = OrderedDict()
    for element in ATOMIC_SYMBOLS:
        filename = None
        for line in results:
            el = line.split('/')[0]
            tmp = line.strip().split('/')[1]
            if el == element:
                filename = tmp
                break
        if filename is None:
            cprint(f"{element} not found in {element_names}", color="yellow")
            continue
        oncv_in = filename.replace('.psp8', '.in')
        pseudo = ps_folder / f"{element}" / filename
        element_input = ps_folder / f"{element}" / oncv_in
        tmp = OrderedDict()
        oncv_input = OncvpspInput(file_path=str(element_input))

        tmp["basename"] = filename
        tmp["Z_val"] = oncv_input.valence_electron_numbers
        tmp["l_max"] = oncv_input.lmax
        tmp["nc"] = oncv_input.basic_setting['nc']
        tmp['nv'] = oncv_input.basic_setting['nv']
        try:
            tmp["md5"] = md5_for_filepath(str(pseudo))
        except FileNotFoundError:
            cprint(f"{element} pseudo potential is not generated correctly.", color="yellow")
        tmp["dfact_meV"] = None
        tmp["dfactprime_meV"] = None
        tmp["tags"] = ["GW"]
        tmp["hints"] = {
            "high": {"ecut": 100},
            "normal": {"ecut": 100},
            "low": {"ecut": 100},
        }
        meta[f"{element}"] = tmp

    pseudo_djson = OrderedDict()
    pseudo_djson["dojo_info"] = d
    pseudo_djson["pseudos_metadata"] = meta

    output = os.path.join(pseudo_path, f"{accuracy}.djson")
    with open(output, "w+") as fp:
        json.dump(pseudo_djson, fp, indent=4)


if __name__ == "__main__":
    temporary_djson_generation(
        version='0.6',
        pseudo_path="/home/wjing/PycharmProjects/pseudos_generation/ONCVPSP-LDA-SR-PDv0.6",
        xc='LDA',
        relative='SR',
        accuracy="lanthanide3+"
    )
