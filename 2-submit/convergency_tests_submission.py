from eos_workflow.convergency import etot_convergency_workflows, eos_convergency_workflows
from eos_workflow.phonon_convergency_workflow import phonon_convergency_workflow
from jobflow_remote import submit_flow, set_run_config
from jobflow import run_locally

EOS_FRONTEND_FUNC = [
    "eos_check",
    "eos_delta_calculation",
    "export_result",
    "converge_results",
    "export_single_workflow",
    "store_inputs",
    "generate_insert_ecuts",
    "get_eos_hints",
    "merge_results"
]

ETOT_FRONTEND_FUNC = [
    "hints_check",
    "write_to_file",
    "get_hints",
    "generate_insert_ecuts",
    "merge_results",
]

PHONON_FRONTEND_FUNC = [
    "Merge DDB",
    "parse_phonon_files",
    "write_to_file",
    "store_inputs"
]

XC_LIST = ['LDA', 'PBE', 'PBEsol']

def convergency_tests(
        element: str,
        configuration: str,
        factory: str,
        ecuts: list[float] | None = None,
        pseudos: str = "ONCVPSP-PBE-SR-PDv0.4:standard",
        precision: str = 'debug',
        frontend: str | None = None,
        run_local: bool = False,
        xc: str | None = None,
):
    if xc is None:
        xc = pseudos.split('-')[1]
        if xc.upper() in XC_LIST:
            pass
        else:
            print(f'ERROR: UNKNOWN XC format: {xc}')
            exit(-1)

    if factory == "delta1":
        jobs = eos_convergency_workflows(
            element,
            configuration,
            ecuts,
            pseudos,
            precision=precision,
            xc=xc,
        )
        if frontend:
            for func_name in EOS_FRONTEND_FUNC:
                jobs = set_run_config(jobs, name_filter=func_name, worker=frontend)

    elif factory == "etot":
        jobs = etot_convergency_workflows(
            element,
            configuration,
            ecuts,
            pseudos,
            precision=precision,
            xc=xc,

        )
        if frontend:
            for func_name in ETOT_FRONTEND_FUNC:
                jobs = set_run_config(jobs, name_filter=func_name, worker=frontend)

    elif factory == "phonon":
        jobs = phonon_convergency_workflow(
            element,
            configuration,
            pseudos,
            ecuts=ecuts,
            qpt_list=[[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]],
            xc=xc,
        )
        if frontend:
            for func_name in ETOT_FRONTEND_FUNC:
                jobs = set_run_config(jobs, name_filter=func_name, worker=frontend)

    else:
        print(f"unknown {factory}!")
        exit(-1)

    if run_local is True:
        res = run_locally(jobs, create_folders=True)
    else:
        res = submit_flow(jobs)
        print("The following jobids are submitted:")
        print(res)
    print(element)
    print(pseudos)
    return res


if __name__ == "__main__":
    pseudos = "ONCVPSP-LDA-SR-PDv0.6:standard"
    element = 'H'
    configuration = 'FCC'
    XC = "LDA"
    ecuts = [20, 25, 100]
    factory = 'delta1'
    convergency_tests(
        element=element,
        configuration=configuration,
        factory=factory,
        ecuts=ecuts,
        pseudos=pseudos,
        frontend="lucia_frontend",
        xc=XC,
    )
