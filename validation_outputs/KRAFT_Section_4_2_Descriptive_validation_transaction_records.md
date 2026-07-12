### 4.2. Descriptive validation of transaction records

Descriptive validation was conducted for the main transaction-level variables to examine whether the released apartment transaction records have interpretable ranges and distributions. Following prior dataset studies that reported descriptive statistics, variable ranges, and distributional summaries as part of dataset description or validation [15–18], we summarized the core numerical variables using valid observations, mean, standard deviation, minimum, first quartile, median, third quartile, and maximum values. In addition, because housing-market datasets commonly include transaction prices and property characteristics as key variables [19], we also inspected the relationship between transaction price and exclusive residential area through a validation-purpose price-per-square-meter variable.

For each numerical variable \(x\), the number of valid observations was calculated as

\[
N_x = \sum_{i=1}^{N} I(x_i \neq \mathrm{missing}),
\]

where \(I(\cdot)\) is an indicator function. The sample mean and standard deviation were computed as

\[
\bar{x} = \frac{1}{N_x} \sum_{i=1}^{N_x} x_i
\]

and

\[
s_x = \sqrt{\frac{1}{N_x - 1} \sum_{i=1}^{N_x} (x_i - \bar{x})^2}.
\]

Quartiles were calculated as the 25th, 50th, and 75th percentiles of each variable distribution:

\[
Q_1(x) = \mathrm{Quantile}_{0.25}(x), \quad
Q_2(x) = \mathrm{Quantile}_{0.50}(x), \quad
Q_3(x) = \mathrm{Quantile}_{0.75}(x).
\]

Here, \(Q_2(x)\) corresponds to the median. For validation purposes, we additionally calculated transaction price per square meter as

\[
Price\_per\_sqm\_10k\_KRW_i =
\frac{Transaction\_Price\_10k\_KRW_i}{Exclusive\_Area\_sqm_i}.
\]

This derived value was used only to inspect the plausibility of transaction prices relative to residential area and is not required as a released variable.

Table 4 reports the descriptive statistics of the core transaction-level variables. The transaction price variable had a mean of 33,703.180 and a median of 25,400.000 in units of 10,000 KRW, with values ranging from 400.000 to 2,500,000.000. The mean was larger than the median, indicating a right-skewed distribution that is consistent with heterogeneous apartment prices across regions, unit sizes, and market segments. Exclusive residential area had a mean of 75.158 square meters and a median of 76.000 square meters, with an interquartile range from 59.730 to 84.960 square meters.

Floor values ranged from -4.000 to 83.000, with a median of 8.000. Negative floor values were present in 281 records and correspond to basement or below-ground floor notation in the source data rather than preprocessing errors. Construction year ranged from 1,961 to 2,025, with a median of 2,001. A total of 225 records (0.0042% of transaction records) had construction years later than the contract year; these records were retained because they correspond to pre-completion or scheduled-completion apartment transactions in the source data.

The validation-purpose price-per-square-meter variable had a mean of 436.899 and a median of 341.373 in units of 10,000 KRW per square meter. Its maximum value was 9,126.006, reflecting the right-skewed nature of apartment prices. Because apartment transaction prices are expected to exhibit right-skewed distributions due to regional, size, and quality differences, extreme high values were inspected as part of distributional validation rather than automatically removed. Overall, the descriptive statistics indicate that the transaction-level variables have plausible ranges and are suitable for reuse in transaction-level or aggregated housing-market analyses.

**Table 4. Descriptive statistics of transaction-level variables.**

| Variable | N | Mean | Std. | Min | Q1 | Median | Q3 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Transaction_Price_10k_KRW` | 5,320,379 | 33,703.180 | 32,687.463 | 400.000 | 15,400.000 | 25,400.000 | 41,000.000 | 2,500,000.000 |
| `Exclusive_Area_sqm` | 5,320,379 | 75.158 | 25.850 | 9.260 | 59.730 | 76.000 | 84.960 | 424.320 |
| `Floor` | 5,320,379 | 9.254 | 6.398 | -4.000 | 4.000 | 8.000 | 13.000 | 83.000 |
| `Construction_Year` | 5,320,379 | 2,001.936 | 9.665 | 1,961.000 | 1,995.000 | 2,001.000 | 2,009.000 | 2,025.000 |
| `Price_per_sqm_10k_KRW` | 5,320,379 | 436.899 | 350.986 | 7.583 | 232.480 | 341.373 | 516.375 | 9,126.006 |
