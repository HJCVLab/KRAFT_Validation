### 4.4. Distributional and regional coverage checks

Distributional and regional coverage checks were performed to complement the descriptive statistics reported in Sections 4.2 and 4.3. These checks focused on whether transaction records were continuously available over the study period, whether all first-level administrative regions were represented, and whether the validation-purpose price-per-square-meter variable showed the expected right-skewed distribution of housing transaction prices.

First, annual transaction counts were computed from the year-specific transaction files. Figure 2 shows the annual number of apartment transactions from 2015 to 2024. The annual counts confirm continuous transaction coverage across the ten-year study period. The number of annual transactions ranged from 254,273 in 2022 to 799,414 in 2020. The total number of records across the annual files was 5,320,379, which matches the total transaction count used in the integrity and descriptive validation checks.

Second, regional coverage was examined at the Sido level. Figure 3 shows the number of transaction records by first-level administrative region. All 17 Sido regions were represented in the transaction records. The largest number of transactions was observed in Gyeonggi (1,461,211), while the smallest number was observed in Jeju (27,425). The five regions with the largest transaction counts were Gyeonggi (1,461,211), Seoul (707,852), Busan (391,623), Gyeongnam (358,611), Incheon (345,846). These differences are consistent with the uneven population size, housing stock, and market activity across metropolitan and non-metropolitan regions.

To further verify temporal-regional completeness, Sido-month coverage was checked for all 17 regions and 120 monthly periods. A total of 2,040 of 2,040 Sido-month combinations contained at least one transaction record. The number of transactions per Sido-month ranged from 110 to 34,237. The number of Sido-month combinations without any transaction record was 0. This result confirms that the released transaction data provide continuous regional coverage at the first-level administrative-region and monthly levels.

Finally, the distribution of the validation-purpose transaction price per square meter was inspected. Figure 4 shows the distribution of the log-transformed price-per-square-meter variable. The untransformed price per square meter had a median of 341.373 and a 99th percentile of 1,852.225 in units of 10,000 KRW per square meter, with a maximum of 9,126.006. The distribution was right-skewed, as expected for housing-market transaction prices that vary by region, unit size, construction quality, and local market conditions. These high-value observations were therefore treated as distributional features of the transaction data rather than automatically removed.

Together, the annual, regional, Sido-month, and price-distribution checks support the completeness and plausibility of the KRAFT transaction records. The generated figures and count tables are provided together with the validation code to support reproducibility.

**Figure 2. Annual number of apartment transactions from 2015 to 2024.** Annual transaction counts were computed by grouping the transaction records by contract year.

**Figure 3. Number of apartment transactions by Sido.** Transaction counts were computed for each first-level administrative region over the full 2015–2024 period.

**Figure 4. Distribution of validation-purpose transaction price per square meter.** The figure shows the log10-transformed distribution of transaction price per square meter, calculated as transaction price divided by exclusive residential area.
