# PseudoDojo-verification-scripts
scripts for eos-workflow to verificate PseudoDojo ONCVPSP pseudopotentials. It contains generation, verification, and parser parts.

## 1-preliminary
### pseudopotential_generation.py
The function *pseudodojo_generation* in this script can generate a new PseudoDojo pseudopotential family "ONCVPSP-XC-R-PDvx.x:accuracy" based on an old one. XC is the exchange-correlation functional, and only support PBE, LDA (PW), and PBEsol now. R is the relativisitic format, it contains SR (scalar relativisitic) and FR (fully relativisitic) types, the latter is used for SOC calculation. accuracy corresponds to different pseudopotenials according to their treatment for valence electrons, it contains three types: standard, stringent, and lanthanide3+. The standard accuracy is the most commonly used, which contains most of elements in the periodic table. The stringent accuracy only contains part of elements in the table with taking more electrons as valence electrons when compare with accuracy ones. The lanthanide3+ corresponds to elements La-Lu with treating 4f electrons frozen in the core, which is termed as "_3" pseudopotentials in VASP.

The choice of XC and R can be different to the old PsedudoDojo. For example, you can use ONCVPSP-PBE-SR-v0.4 to generate ONCVPSP-LDA-FR-v0.5. However, the accuracy is the same between two families.

### pseudopotential_check.py
The function *pd_check* in this script can check GHOST(-) states and other fatal ERROR happens in ONCVPSP pseudopotential generation. The report will store in dojo-error-report-{accuracy}.txt.

The function *pd_compare* can check the parameter consistency of files among input file *.in* and output files *.out*, *.psp8*, *.upf*. This function can also compare input parameters between two PseudoDojo pseudopotential families. The comparison results will be exported in dojo-comparison-report-{accuracy}.txt

### temporary_djson_for_testing.py
For eos-workflow to verificate PseudoDojo ONCVPSP pseudopotentials, those pseudopotentials are stored in ONCVPSP family "ONCVPSP-XC-R-PDvx.x:accuracy". When you want to verify specific element in that ONCVPSP family. The f"{accuracy}.djson" file will help atomate2+abipy to find where stores the pseudopotential of that element and also the recommend cutoff energy hints. In addition, f"{accuracy}.djson" file also provide basic informations for each pseudopotentials. Thus, f"{accuracy}.djson" is the kernel file stored in the main branch of "ONCVPSP-XC-R-PDvx.x". One "ONCVPSP-XC-R-PDvx.x" folder may contains different accuracy elements.

If you generate some new pseudopotentials, there are two way to verificate them. 
1. Still use the old ONCVPSP family, but modify the *basename* in f"{accuracy}.djson" to the name of the new pseudopotential and also put your new pseudopotential to the same folder of the old one.
2. Create a new ONCVPSP family, for example ONCVPSP-PBE-SR-PDv1.0 by using pseudopotential_generation.py. Then, do the same thing as option 1. In this case, you have to modify a global variable "_ONCVPSP_REPOS" in PATH_TO_ABIPY/abipy/flowtk/psrepos.py, and pip show abipy can find PATH_TO_ABIPY.

When you want to test pseudopotentials on remote cluster, options above should be also applied at remote cluster.

Thus, the function *temporary_djson_generation* in this script can generate a temporary f"{accuracy}.djson" file based on f"{accuracy}.txt", which can be used for convergency testing.

## 2-submit
### convergency_tests_submission.py
Since recommend cutoff energy hints are important information for a pseudopotentials. The function *convergency_tests* in this script will submit jobs to test the convergency behavior of pseudopotentials and also for the purpose to obtain hints.

There are three kinds of convergency test, which are labeled by the key *factory* in the function: etot, delta1, and phonon. The convergency results of etot and delta1, combined with the ecut estimated by ONCVPSP will obtain the recommned cutoff energy hints (more details refer to https://doi.org/10.1016/j.cpc.2018.01.012). 

It is noted that phonon related calculations are still not combined to the *main* branch of atomate2/abinit. When you care about the phonon behavior, a developer version of atomate2 and abipy are needed, which is available in *developer-packages-for-phonon* folder.

After you pip install eos_workflow, cd *developer-packages-for-phonon* folder, and fisrt pip install atomate2-phonon, then abipy-phonon.

In addition, the key *frontend* in *convergency_tests* function is only useful for remote cluster, which will run specific jobs on local rather than to the queue for calculation node. This trick can save time when this job is just a one-step operation, so there is no need to submit suck kind of jobs like time-consuming DFT calculations to queue and waiting for the source of calculation nodes. 

### eos_tests_submission.py
The function *eos_tests* in this script can submit EOS calculations for given pseudopotentials. There are ten testing configurations, four unaries: BCC, FCC, SC, Diamond; six oxides: X2O, XO, X2O3, XO2, X2O5, XO3. More details can refer to https://doi.org/10.1038/s42254-023-00655-3. 

When the key *ecut* is None in the *eos_tests* function, the hint value with *high* label in f"{accuracy}.djson" file will be adopted as the recommended cutoff energy. Thus, if you do not know what cutoff energy should be used, you need to first use convergency_tests_submission.py and obtain_hints.py to obtain recommend cutoff energy.

Still, the key *frontend* is only helpful for remote cluster. More details for the settings can refer to.

## 3-analyze
### results_download.py
The function *download_remotely* can download delta1/etot/phonon convergency reports and also EOS calculation results from remote cluster by search flows for *start* to *end* DB id of flows.

In addition, it is highly recommend to store delta1/etot/phonon convergency reports to corresponding f"delta1/etot/phonon-{accuracy}" folder, and to store EOS results to f"eos-{accuracy}" folder, and all of these folders are created at the main folder of ONCVPSP-XC-R-PDvx.x. These settings will benifit the following steps.

### obtain_hints.py
The function *dojo_hints* will read delta1/etot convergency reports to obtain cutoff hints values and write them to f"{accuracy}.djson" file. If the path to delta1/etot convergency reports are not provided, the function will search f"delta1/etot-{accuracy}" folder in *pseudo_path*.

## 4-export
The function *write_djrepo* will summarize delta1/etot/phonon convergency reports and also EOS calculation results to f"{basename}.djrepo" file at {element} folder, where the same path to store pseudopotential files, i.e. f"{element}/{basename}.psp8" provided in f"{accuracy}.txt" file.












