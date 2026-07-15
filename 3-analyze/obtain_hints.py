import numpy as np
import os
import json
# import pandas as pd
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

LANTHANIDE_ELEMENTS = [
    "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu",
]


def get_hints(data, thresholds):
    ecut_keys = sorted(
        [k for k in data if k.startswith("ecut-")],
        key=lambda x: int(x.split("-")[1]),
    )

    ecut = np.array([int(k.split("-")[1]) for k in ecut_keys])
    energy = np.array([data[k]["energy"] for k in ecut_keys])

    ref_energy = energy[-1]
    delta = energy - ref_energy
    abs_delta = np.abs(delta)

    conv_ecut = {}
    for label, thr in thresholds.items():
        conv_idx = None
        for i in range(len(abs_delta)):
            if np.all(abs_delta[i:] * 1e3 < thr):
                conv_idx = i
                break
        conv_ecut[label] = ecut[conv_idx] if conv_idx is not None else None
    return conv_ecut


def get_eos_hints(data, thresholds):
    ecut_keys = sorted(
        [k for k in data if k.startswith("ecut-")],
        key=lambda x: int(x.split("-")[1]),
    )

    ecut = np.array([int(k.split("-")[1]) for k in ecut_keys])

    delta = np.array([
        data[k]["delta/natoms"] if data[k]["delta/natoms"] is not None else np.nan
        for k in ecut_keys
    ], dtype=float)

    eos_ok = np.array([data[k]["eos_is_converged"] for k in ecut_keys], dtype=bool)

    v0_b0_b1 = data["reference_ae_V0_B0_B1"]

    v0 = v0_b0_b1[0]
    b0 = v0_b0_b1[1]

    # delta1 (delta_prime) = delta * v0_ref * b0_ref / (v0_AE * b0_AE), where v0_ref = 30 bohr^3, b0_ref = 100 Gpa.
    # so, 2.7747 is the multiple of v0_ref * b0_ref with a unit transform from bohr^3 * Gpa to eV
    delta1 = delta * 2.7747 / (v0 * b0)

    valid = eos_ok & np.isfinite(delta1)
    delta1[~valid] = np.nan

    # =====================
    # Reference (highest Ecut)
    # =====================
    delta_ref = delta1[-1]
    abs_diff = np.abs(delta1 - delta_ref)

    conv_ecut = {}

    for label, thr in thresholds.items():
        conv_idx = None
        for i in range(len(abs_diff)):
            if np.all(abs_diff[i:] < thr):
                conv_idx = i
                break
        conv_ecut[label] = ecut[conv_idx] if conv_idx is not None else None
    print(conv_ecut)
    conv_ecut.update({"dfact_meV": delta[-1], 'dfactprime_meV': delta1[-1]})
    return conv_ecut


def dojo_hints(
        pseudo_dojo_path : str,
        accuracy: str = 'standard',
        etot_conv_results_path: str | None = None,
        delta1_conv_results_path: str | None = None,
        element_basename: str | None = None,
        djson: str | None = None,
        etot_thresholds : dict | None = None,
        delta1_thresholds: dict | None = None,
):
    if etot_thresholds is None:
        etot_thresholds = {
            # meV/atom
            "low": 10.0,
            "normal": 5.0,
            "high": 2.0,
        }
    if delta1_thresholds is None:
        delta1_thresholds = {
            # meV/atom
            "low": 0.5,
            "normal": 0.3,
            "high": 0.1,
        }

    hints_results = {}
    if element_basename is None:
        print(f"element_basename is None, try to load {accuracy}.txt at {pseudo_dojo_path}")
        element_basename = os.path.join(pseudo_dojo_path, f'{accuracy}.txt')
        if os.path.isfile(element_basename) is False:
            print(f"ERROR: could not find element_basename file")
            exit(-1)
    if etot_conv_results_path is None:
        etot_conv_results_path = os.path.join(pseudo_dojo_path, f'etot-{accuracy}')
        print(f"try to load etot convergency results at {etot_conv_results_path}")
    if delta1_conv_results_path is None:
        delta1_conv_results_path = os.path.join(pseudo_dojo_path, f'delta1-{accuracy}')
        print(f"try to load delta1 convergency results at {delta1_conv_results_path}")

    with open(element_basename, "r+") as fp:
        lines = fp.readlines()

    for element in ATOMIC_SYMBOLS:
        etot_file = f'{element}-hints.txt'
        etot_file = os.path.join(etot_conv_results_path, etot_file)
        if os.path.isfile(etot_file) is False:
            cprint(f'WARNING: Convergency results for {element} is missing.', color='yellow')
            continue
        with open(etot_file, "r+") as fp:
            etot_results = json.load(fp)
        etot_hints = get_hints(etot_results, etot_thresholds)

        delta1_file = f'{element}-eos_converge_results.json'
        delta1_file = os.path.join(delta1_conv_results_path, delta1_file)
        if os.path.isfile(delta1_file) is False:
            cprint(f'WARNING: Convergency results for {element} is missing.', color='yellow')
            continue
        with open(delta1_file, 'r+') as fp:
            delta1_results = json.load(fp)
        delta1_hints = get_eos_hints(delta1_results, delta1_thresholds)

        for line in lines:
            el, pseudo_name = line.strip().split('/')
            if el == element:
                break
        oncv_out = os.path.join(pseudo_dojo_path, line.strip())
        oncv_out = oncv_out.replace('.psp8', '.out')
        onc_parser = OncvParser(oncv_out)
        onc_parser.scan()
        oncv_hints = onc_parser.hints

        if element in LANTHANIDE_ELEMENTS and accuracy != "lanthanide3+":
            tmp = {'low': max(etot_hints['low'], delta1_hints['low']),
                   'normal': max(etot_hints['normal'], delta1_hints['normal'],),
                   'high': max(etot_hints['high'], delta1_hints['high']),
                   'dfact_meV': delta1_hints['dfact_meV'],
                   'dfactprime_meV': delta1_hints['dfactprime_meV']
                   }
        else:
            tmp = {'low': max(etot_hints['low'], delta1_hints['low']),
                   'normal': max(etot_hints['normal'], delta1_hints['normal'], oncv_hints['normal']['ecut']),
                   'high': max(etot_hints['high'], delta1_hints['high'], oncv_hints['high']['ecut']),
                   'dfact_meV': delta1_hints['dfact_meV'],
                   'dfactprime_meV': delta1_hints['dfactprime_meV']
                   }
        hints_results.update({element: tmp})

    #df = pd.DataFrame.from_dict(hints_results, orient="index")
    #df.index.name = "element"
    #df = df[["low", "normal", "high"]]
    #df.to_csv("pseudodojo_hints.csv")

    if djson is None:
        print(f"djson file is None, try to load {accuracy}.djson at {pseudo_dojo_path}")
        djson = os.path.join(pseudo_dojo_path, f'{accuracy}.djson')
        if os.path.isfile(djson) is False:
            print(f"ERROR: could not find element_basename file")
            exit(-1)

    with open(djson, 'r+') as fp:
        djson_results = json.load(fp)
    for element, hints in hints_results.items():
        djson_results['pseudos_metadata'][f'{element}']['hints']['high']['ecut'] = float(hints['high'])
        djson_results['pseudos_metadata'][f'{element}']['hints']['normal']['ecut'] = float(hints['normal'])
        djson_results['pseudos_metadata'][f'{element}']['hints']['low']['ecut'] = float(hints['low'])
        djson_results['pseudos_metadata'][f'{element}']['dfact_meV'] = hints['dfact_meV']
        djson_results['pseudos_metadata'][f'{element}']['dfactprime_meV'] = hints['dfactprime_meV']
    djson_results['dojo_info']['description'] = "Standard table designed for GS applications"
    with open(djson, 'w') as fp:
        text = json.dumps(djson_results, indent=4)
        fp.write(text)
    return hints_results


if __name__ == "__main__":
    pseudo_path = "/home/wjing/PycharmProjects/pseudos_generation/ONCVPSP-LDA-SR-PDv0.6"
    dojo_h = dojo_hints(
        pseudo_path,
        accuracy='standard',
    )
