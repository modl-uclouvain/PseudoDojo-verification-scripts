from eos_workflow.workflows import eos_workflows
from jobflow_remote import submit_flow, set_run_config
from jobflow import run_locally
from atomate2.abinit.sets.base import as_pseudo_table
from pathlib import Path
import json

EOS_FUNC = [
    "eos_check",
    "eos_delta_calculation",
    "export_result",
    "export_single_workflow",
    "store_inputs",
]
XC = ['LDA', 'PBE', 'PBEsol']


def eos_tests(
        element: str,
        pseudos: str,
        ecut: float | None = None,
        configurations: list[str] | None = None,
        precision: str = "debug",
        volume_scaling_list: list[float] | None = None,
        frontend: str | None = None,
        run_local: bool = False,
        xc: str | None= None,
):
    if xc is None:
        xc = pseudos.split('-')[1]
        if xc.upper() in XC:
            pass
        else:
            print(f'ERROR: UNKNOWN XC format: {xc}')
            exit(-1)
    if ecut is None:
        filepath = None
        pseudo_table = as_pseudo_table(pseudos).as_dict()
        for key, value in pseudo_table.items():
            if key == element:
                filepath = value["filepath"]
                break
        if filepath is None:
            print(f"ERROR: could not find {element} in djson of {pseudos}")
            exit(-1)
        accuracy = pseudos.split(':')[1]
        filepath = Path(filepath).parents[1] / f"{accuracy}.djson"
        with open(filepath, 'r+') as fp:
            dj = json.load(fp)
        ecut = dj['pseudos_metadata'][f'{element}']['hints']['high']['ecut']
        ecut_oxy = dj['pseudos_metadata']['O']['hints']['high']['ecut']
        ecut = max(ecut, ecut_oxy)

    eos_jobs = eos_workflows(element, ecut, pseudos,
                             precision=precision,
                             volume_scaling_list=volume_scaling_list,
                             configurations=configurations,
                             xc=xc,
                             )
    if frontend:
        for func in EOS_FUNC:
            eos_jobs = set_run_config(eos_jobs, name_filter=func, worker=frontend)

    if run_local is True:
        res = run_locally(eos_jobs, create_folders=True)
    else:
        res = submit_flow(eos_jobs)
        print("The following jobids are submitted:")
        print(res)
    print(element)
    print(pseudos)
    return res


if __name__ == "__main__":
    import os

    os.environ["PATH"] = (
            "/home/wjing/programs/abinit-9.10.1/build_gfortran/src/98_main:"
            + os.environ.get("PATH", "")
    )

    os.environ["LD_LIBRARY_PATH"] = (
            "/home/wjing/local/lib:"
            + os.environ.get("LD_LIBRARY_PATH", "")
    )

    elem = 'Sn'
    pseudotable = 'ONCVPSP-LDA-SR-PDv0.6:standard'
    config = None
    ecut = None
    eos = eos_tests(elem, pseudotable, frontend="lucia_frontend", configurations=config, ecut=ecut)
