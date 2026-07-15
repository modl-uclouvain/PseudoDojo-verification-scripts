import json
import os
from monty.termcolor import cprint
from copy import deepcopy
from datetime import datetime
from pymatgen.core.xcfunc import XcFunc

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


def get_deltafactor(element, delta_path):
    delta_path = os.path.join(delta_path, f'{element}-eos_converge_results.json')
    if not os.path.isfile(delta_path):
        cprint(f"Can not find {delta_path}", color="red")
        return None

    with open(delta_path, 'r+') as fp:
        data = json.load(fp)
    dfactor = {}
    ecut_keys = sorted(
        [k for k in data if k.startswith("ecut-")],
        key=lambda x: int(x.split("-")[1]),
    )
    for k in ecut_keys:
        tmp = {
            "b0": None,
            "b0_GPa": None,
            "b1": None,
            "dfact_meV": None,
            "dfactprime_meV": None,
            "etotals": None,
            "num_sites": None,
            'v0': None,
            "volumes": None
        }
        if not isinstance(data[k]["delta/natoms"], float):
            continue
        tmp["v0"], tmp["b0"], tmp["b1"] = data[k]["v0_b0_b1"]
        tmp["b0_GPa"] = tmp["b0"] * 160.218  # unit transform: eV/A^3 to GPa
        tmp["etotals"] = data[k]["energies"]
        tmp["volumes"] = data["volumes"]
        tmp["num_sites"] = data["num_of_atoms"]
        tmp["dfact_meV"] = data[k]["delta/natoms"]
        # the definition of dfactprime (delta1) here is different to delta1 obtained by eos metric program
        # and here is the correct equation which is consistent with paper, using v0_ref = 30 Bohr^3, b0_ref = 100 GPa
        tmp["dfactprime_meV"] = tmp["dfact_meV"] * 2.7747 / (tmp["v0"] * tmp["b0"])

        k = k.split("-")[1]
        dfactor.update({k: tmp})
    return dfactor


def get_nu_metric(element, eos_path):
    eos_path = os.path.join(eos_path, f'{element}-eos_fitting_results.json')
    if not os.path.isfile(eos_path):
        cprint(f"Can not find {eos_path}", color="red")
        return None
    with open(eos_path, 'r+') as fp:
        data = json.load(fp)
    return data[element]


def get_etot(element, etot_path):
    etot_path = os.path.join(etot_path, f'{element}-hints.txt')
    if not os.path.isfile(etot_path):
        cprint(f"Can not find {etot_path}", color="red")
        return None
    with open(etot_path, 'r+') as fp:
        data = json.load(fp)
    data.pop("element")
    data.pop("pseudos")
    return data


def qpt_to_key(qpt, ndigits=6):
    """
    Convert a q-point list/tuple into a stable string key.

    Example:
        [0, 0.5, 0.25] -> "0.000000,0.500000,0.250000"
    """
    return ",".join(f"{float(x):.{ndigits}f}" for x in qpt)


def key_to_qpt(key):
    """
    Convert a string key back to a tuple of floats.

    Example:
        "0.000000,0.500000,0.250000" -> (0.0, 0.5, 0.25)
    """
    return tuple(float(x) for x in key.split(","))


def get_phonon(element, phonon_path):
    phonon_file = os.path.join(phonon_path, f"{element}-phonon.txt")
    if not os.path.isfile(phonon_file):
        cprint(f"Can not find {phonon_file}", color="red")
        return None

    with open(phonon_file, "r") as fp:
        data = json.load(fp)

    qpts = data["qpt_list"]
    ecut_keys = [k for k in data.keys() if k.startswith("ecut-")]
    ecut_keys_sorted = sorted(ecut_keys, key=lambda x: int(x.split("-")[1]))

    # Initialize result dict with string keys
    qpt_results = {
        qpt_to_key(q): {"ecut": [], "freqs": [], "state": []}
        for q in qpts
    }

    for ecut_key in ecut_keys_sorted:
        ecut = int(ecut_key.split("-")[1])

        for entry in data[ecut_key]:
            qpt_key = qpt_to_key(entry["phonon wavevector"])
            freqs = entry["phonon frequencies (cm^-1)"]
            state = entry["calculation state"]

            # In case this q-point was not listed in qpt_list beforehand
            if qpt_key not in qpt_results:
                qpt_results[qpt_key] = {"ecut": [], "freqs": [], "state": []}

            qpt_results[qpt_key]["ecut"].append(ecut)
            qpt_results[qpt_key]["freqs"].append(freqs)
            qpt_results[qpt_key]["state"].append(state)

    final_results = {'noasr_phfreqs_cm^-1': qpt_results, 'configuration': data['configuration']}

    return final_results


def write_djrepo(
        pseudo_path: str,
        accuracy: str = 'standard',
        etot_conv_path: str | None = None,
        eos_conv_path: str | None = None,
        phonon_conv_path: str | None = None,
        eos_path: str | None = None,
):
    if etot_conv_path is None:
        etot_conv_path = os.path.join(pseudo_path, f'etot-{accuracy}')
        if not os.path.isdir(etot_conv_path):
            print("WARNING: Etot convergency testing results are missing.")
            etot_conv_path = None

    if eos_conv_path is None:
        eos_conv_path = os.path.join(pseudo_path, f"delta1-{accuracy}")
        if not os.path.isdir(eos_conv_path):
            print("WARNING: delta1 convergency testing results are missing.")
            eos_conv_path = None

    if phonon_conv_path is None:
        phonon_conv_path = os.path.join(pseudo_path, f"phonon-{accuracy}")
        if not os.path.isdir(phonon_conv_path):
            print("WARNING: Phonon convergency testing results are missing.")
            phonon_conv_path = None

    if eos_path is None:
        eos_path = os.path.join(pseudo_path, f"eos-{accuracy}")
        if not os.path.isdir(eos_path):
            print("WARNING: EOS results are missing.")
            eos_path = None

    pseudo_names = os.path.join(pseudo_path, f'{accuracy}.txt')
    if not os.path.isfile(pseudo_names):
        print(f"ERROR: Can not find {accuracy}.txt at {pseudo_path}!")
        exit(-1)
    with open(pseudo_names, 'r+') as fp:
        lines = fp.readlines()

    pseudo_djson = os.path.join(pseudo_path, f'{accuracy}.djson')
    if not os.path.isfile(pseudo_djson):
        print(f"ERROR: Can not find {accuracy}.djson at {pseudo_path}!")
        exit(-1)
    with open(pseudo_djson, 'r+') as fp:
        dojo_results = json.load(fp)
        version = dojo_results["dojo_info"]["dojo_dir"]
        version = version.split('PDv')[1]

    for line in lines:
        element, basename = line.strip().split('/')
        line = line.strip().replace('.psp8', '.djrepo')
        djrepo = os.path.join(pseudo_path, line)
        hints = dojo_results["pseudos_metadata"][element]["hints"]
        ppgen_hints = deepcopy(hints)
        ppgen_hints["high"]["pawecutdg"] = hints["high"]["ecut"]
        ppgen_hints["normal"]["pawecutdg"] = hints["normal"]["ecut"]
        ppgen_hints["low"]["pawecutdg"] = hints["low"]["ecut"]
        tmp = {
            'basename': basename,
            'nc': dojo_results["pseudos_metadata"][element]['nc'],
            'nv': dojo_results["pseudos_metadata"][element]['nv'],
            'deltafactor': get_deltafactor(element, eos_conv_path),
            'etot': get_etot(element, etot_conv_path),
            'nu-metric': get_nu_metric(element, eos_path),
            'hints': hints,
            'md5': dojo_results["pseudos_metadata"][element]["md5"],
            'phonon': get_phonon(element, phonon_conv_path),
            'ppgen_hints': ppgen_hints,
            'pseudo_type': 'NC',
            'symbol': element,
            'tags': ['GW'],
            'validation': {"validated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            'version': version,
            'xc': XcFunc.from_name(dojo_results["dojo_info"]["xc_name"]).as_dict()
        }
        with open(djrepo, 'w+') as fp:
            text = json.dumps(tmp, indent=4)
            fp.write(text)


if __name__ == "__main__":
    pp_path = "/home/wjing/PycharmProjects/pseudos_generation/ONCVPSP-LDA-SR-PDv0.6/"
    write_djrepo(pp_path, accuracy="standard",)
