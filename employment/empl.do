

use "C:\Users\mkrzakala\DATA\PathsWP6\\all_2023_a.dta", clear
gen empl_rate = 0 if (inrange(ilostat,1,3))
replace empl_rate = 1 if (ilostat==1)
keep if country=="PL"

collapse empl_rate [iw=coeffy], by(age_grp sex)

export excel using "C:\Users\mkrzakala\OneDrive - IBS\BENEFIT PROJEKT\analiza\simulation\employment\employment.xls", replace