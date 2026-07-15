import os
import json
import subprocess
from jobflow_remote import ConfigManager, JobController
from pathlib import Path


FUNCTIONS_AND_FILENAMES = {
    "etot_convergency": {"function_name": "write_to_file", "file_name": "hints.txt"},
    "delta1_convergency": {"function_name": "export_result", "file_name": "eos_converge_results.json"},
    "phonon": {"function_name": "write_to_file", "file_name": "phonon.txt"},
    "eos": {"function_name": "export_result", "file_name": "eos_fitting_results.json"},
}


def get_remote_run_dirs(function_name, flow_id_start, flow_id_end):
    cm = ConfigManager()
    jc = JobController.from_project(cm.get_project())
    run_dirs = []
    db_ids = [str(x) for x in range(flow_id_start, flow_id_end + 1)]
    while len(db_ids) > 0:
        db_id = db_ids.pop(0)
        flows_info_list = jc.get_flows_info(db_ids=db_id)
        if len(flows_info_list) == 0:
            # this id belongs to a deleted flow
            continue
        flows_info = flows_info_list[0]
        job_ids = flows_info.db_ids
        tmp = []
        for jid in job_ids:
            job_info = jc.get_jobs_info(db_ids=jid)[0]
            if jid in db_ids:
                idx = db_ids.index(jid)
                db_ids.pop(idx)
            if job_info.state.name != "COMPLETED":
                print(f"d_id={jid} is not finished, skipping!")
                continue
            if job_info.name == function_name:
                tmp.append(float(jid))
        if len(tmp) > 0:
            final_result_id = int(max(tmp))
            job_info = jc.get_jobs_info(db_ids=str(final_result_id))[0]
            run_dirs.append(job_info.run_dir)
    print(run_dirs)
    return run_dirs


def safe_rename(new):
    new = Path(new)

    if not new.exists():
        return new

    i = 1
    while True:
        candidate = new.with_stem(f"{new.stem}_{i}")
        if not candidate.exists():
            return candidate
        i += 1


def download_remote_jsons(
    file_name: str,
    file_dirs: list[str],
    cluster_name: str,
    store_dir: str | None = None,
    overwrite: bool = True
):
    if store_dir is None:
        store_dir = os.getcwd()
    for fdir in file_dirs:
        fdir = os.path.join(fdir, file_name)
        file = f"{cluster_name}:{fdir}"
        command = ['scp', file, store_dir]
        try:
            subprocess.run(command, check=True)
        except :
            print(f'can not download from {file}')
            continue
        tmp = os.path.join(store_dir, file_name)
        with open(tmp, 'r+') as fp:
            data = json.load(fp)
        try:
            elment = data['element']
        except:
            for key, value in data.items():
                elment = key
        new_name = f'{elment}-{file_name}'
        new_name = os.path.join(store_dir, new_name)
        if os.path.exists(new_name):
            if overwrite:
                print(f'WARNING: {new_name} will be overwritten.')
            else:
                new_name = safe_rename(new_name)
        command = ['mv', tmp, new_name]
        print(f'{elment} is finished')
        subprocess.run(command, check=True)


def download_remotely(
        start_flow_id: int,
        end_flow_id: int,
        function_name: str,
        file_name: str,
        store_path: str,
        cluster_name: str,
        overwrite: bool = True
):
    remote_dir = get_remote_run_dirs(function_name, start_flow_id, end_flow_id)
    download_remote_jsons(file_name, remote_dir, cluster_name=cluster_name, store_dir=store_path, overwrite=overwrite)


if __name__ == "__main__":
    factory = "phonon"
    store = '/home/wjing/PycharmProjects/pseudos_generation/ONCVPSP-LDA-SR-PDv0.6/phonon-standard'
    start = 407420
    end = 411118

    func_name = FUNCTIONS_AND_FILENAMES[factory]["function_name"]
    f_name = FUNCTIONS_AND_FILENAMES[factory]["file_name"]
    download_remotely(start, end, func_name, f_name, store_path=store, cluster_name="lucia", overwrite=False)
