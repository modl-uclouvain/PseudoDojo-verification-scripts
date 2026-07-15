import os
import json

function = 'eos'
accuracy = 'standard'
SUFFIX = {'etot': 'hints.txt', 'delta1': 'eos_converge_results.json', 'phonon': 'phonon.txt', 'eos': 'eos_fitting_results.json'}
suffix = SUFFIX[function]
pp_path = "/home/wjing/PycharmProjects/PseudoDojo-verification-scripts/ONCVPSP-PBE-SR-PDv0.6"
pp_files = os.path.join(pp_path, f"{accuracy}.txt")
with open(pp_files) as fp:
    lines = fp.readlines()

for line in lines:
    element = line.split('/')[0]
    json_file = os.path.join(pp_path, f"{function}-{accuracy}/{element}-{suffix}")
    with open(json_file, "r+") as f:
        results = json.load(f)
    if function == 'eos':
        results[element]['pseudolib'] = f'ONCVPSP-PBE-SR-PDv0.6:{accuracy}'
    else:
        results['pseudos'] = f'ONCVPSP-PBE-SR-PDv0.6:{accuracy}'

    with open(json_file, 'w+') as f:
        text = json.dumps(results, indent=4)
        f.write(text)

