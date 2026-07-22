# PseudoDojo-verification-scripts
scripts for eos-workflow to verificate PseudoDojo ONCVPSP pseudopotentials. It contains generation, verification, and parser parts.

## 1-preliminary
### pseudopotential_generation.py
The function *pseudodojo_generation* in this script can generate a new PseudoDojo pseudopotential family "ONCVPSP-XC-R-PDvx.x:accuracy" based on an old one. XC is the exchange-correlation functional, and only support PBE, LDA (PW), and PBEsol now. R is the relativisitic format, it contains SR (scalar relativisitic) and FR (fully relativisitic) types, the latter is used for SOC calculation. accuracy corresponds to different pseudopotenials according to their treatment for valence electrons, it contains three types: standard, stringent, and lanthanide3+. The standard accuracy is the most commonly used, which contains most of elements in the periodic table. The stringent accuracy only contains part of elements in the table with taking more electrons as valence electrons when compare with accuracy ones. The lanthanide3+ corresponds to elements La-Lu with treating 4f electrons frozen in the core, which is termed as "_3" pseudopotentials in VASP.

The choice of XC and R can be different to the old PsedudoDojo. For example, you can use ONCVPSP-PBE-SR-v0.4 to generate ONCVPSP-LDA-FR-v0.5. However, the accuracy is the same between two families.

### pseudopotential_check.py
The function *pd_check* in this script can check GHOST(-) states and other fatal ERROR happens in ONCVPSP pseudopotential generation. The report will store in dojo-error-report-{accuracy}.txt.

The function *pd_compare" can check the parameter consistency of files among input file *.in* and output files *.out*, *.psp8*, *.upf*. This function can also compare input parameters between two PseudoDojo pseudopotential families. The comparison results will be exported in dojo-comparison-report-{accuracy}.txt

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

It is noted that phonon related calculations are still not combined to the *main* branch of atomate2/abinit. When you care about the phonon behavior, a developer version of atomate2 and abipy are needed, which is available here:
#### atomate2-phonon
#### abipy-phonon
After you pip install eos_workflow, git clone two developer packages above and pip install atomate2-phonon and then abipy-phonon.

### eos_tests_submission.py




