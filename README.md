# PseudoDojo-verification-scripts
scripts for eos-workflow to verificate PseudoDojo ONCVPSP pseudopotentials. It contains generation, verification, and parser parts.

## 1-preliminary
### pseudopotential_generation.py
The function *pseudodojo_generation* in this script can generate a new PseudoDojo pseudopotential family "ONCVPSP-XC-R-PDvx.x:accuracy" based on an old one. XC is the exchange-correlation functional, and only support PBE, LDA (PW), and PBEsol now. R is the relativisitic format, it contains SR (scalar relativisitic) and FR (fully relativisitic) types, the latter is used for SOC calculation. accuracy corresponds to different pseudopotenials according to their treatment for valence electrons, it contains three types: standard, stringent, and lanthanide3+. The standard accuracy is the most commonly used, which contains most of elements in the periodic table. The stringent accuracy only contains part of elements in the table with taking more electrons as valence electrons when compare with accuracy ones.

The choice of XC and R can be different to the old PsedudoDojo. For example, you can use ONCVPSP-PBE-SR-v0.4 to generate ONCVPSP-LDA-FR-v0.5. However, the accuracy is the same between two families.

### pseudopotential_check.py
The function *pd_check* in this script can check GHOST(-) states and other fatal ERROR happens in ONCVPSP pseudopotential generation. The report will store in dojo-error-report-{accuracy}.txt.

The function *pd_compare" can check the parameter consistency of files among input file *.in* and output files *.out*, *.psp8*, *.upf*. This function can also compare input parameters between two PseudoDojo pseudopotential families.

### temporary_djson_for_testing.py


