# A log for my decision logic and investigation

## Before training the model:

### Which information could genuinely be known when a new mortgage application is assessed? Is anything recorded **after** the decision?

#### What the law suggests:

The legal and practical basis is that _FCA rule MCOB 11.6.2R_ generally requires an affordability assessment before entering into the mortgage. Rules _11.6.8R_ and _11.6.10–13_ cover **income evidence**, **expenditure** and **obtaining details of outstanding commitments**. These are regulatory requirements and don't prescribe this exact set of data fields.

#### **Data fields:**

- `annual_income_gbp`
  - Income declared and assessed using evidence available at application.
  - Need specificity or investigation regarding gross/net income, and individual/joint income.
  - FCA rules require income evidence.
- `property_value_gbp`
  - Initially the stated purchase price or estimated value; could subsequently the lender’s valuation.
  - An initial estimate is not the same as an underwriting valuation need specificity or investigation regarding which is displayed here.
- `deposit_gbp`
  - Assumed to be the proposed deposit, not the subsequent deposit decided after the fact.
  - May be related to loan amount and/or LTV.
- `requested_loan_gbp`
  - Could be known if it is the amount 'requested' at that stage (which is inferred from the word 'requested' in the field name), rather than a later approved or advanced amount.
- `loan_to_value_pct`
  - Loan amount ÷ relevant property value × 100.
  - Need specificity or investigation regarding whether the denominator is an initial estimate/lender valuation and whether financed fees are included.
  - FCA disclosure rules explicitly address LTV.
- `monthly_debt_commitments_gbp`
  - Could be known if these are existing monthly debt obligations established during assessment, (need clarity over when ongoing debts will reduce or increase).
  - Need specificity or investigation regarding whether this is included in `debt_to_income_ratio`.
  - FCA rules require reasonable steps to establish actual outstanding commitments so there is reasonable justification to assume this was recorded before.
- `debt_to_income_ratio`
  - Could be known since this is calculable from information available at application time. Largely depends on if a fixed interest rate is used to evaluate this at application time.
  - Need to define the DTI formula: _monthly debt payments ÷ monthly income_ differs from _outstanding debt ÷ annual income_, and a proposed mortgage payment might also be included. The field name does not establish which measure was used, so candidate formulas were tested.
- `credit_score`
  - A score most likely obtained or calculated during assessment.
- `employment_type`
  - Could be known if it is employment status at time of application.
- `employment_years`
  - Could be known if it is historical tenure established from the application/supporting evidence.
  - Need to define whether this means current employer, continuous employment, or time self-employed; these are different measures.
- `savings_gbp`
  - Could be savings established from statements or other evidence at time of application.
  - However a lender does not automatically know every savings account, and evidence of the deposit does not necessarily establish total savings.
  - Need specificity or investigation regarding whether this includes the deposit. A consistency calculation can help investigate this.
- `missed_payments_24m`
  - Could be known if backward looking. Such as missed payments in the 24 months before assessment, drawn from available credit history.
  - Could work towards verifying this by comparing it to `repayment_difficulty_12m` if there are any people who flag as a 1 for this field but dont show any `missed_payments_24m` then `missed_payments_24m` can be reasonably assumed to be at a different time to the 12m period (most likely before) for the purposes of our model.
  - Its timing cannot be proved from the data alone; it must be confirmed as a pre-application lookback before use.
- `credit_utilisation_pct`
  - Reported revolving-credit balances relative to limits, likely using the report available at application.
- `previous_default_flag`
  - Defaults likely recorded before assessment inferred from 'previous'.
  - It likely doesn't represent perfect knowledge of lifetime defaults: credit-report retention periods and reporting coverage limit what can be inferred (Experian explains that defaults generally disappear from credit reports after six years).
- `term_years`
  - Could be known if this is the requested/proposed mortgage term.
  - A later revised or final term is a different version, so its timing must be confirmed.
- `interest_rate_pct`
  - The recorded rate may be a pre-decision assumption or a final offered rate. Its timing must be confirmed before use.
  - Tests seem to indicate that DTI is calculated with a fixed rate so this might only be known after.
- `application_channel`
  - The route through which the application arrived, such as broker, branch or online. This is operational metadata knowable on receipt (that is a practical inference).
- `repayment_difficulty_12m`
  - This is the following 12 months. A future outcome, unavailable at the original decision.
  - Not necessarily default (do not label its score a PD).
  - Exact definition of 'observed repayment difficulty' isn't provided.
  - THIS IS OUR TARGET.

#### Assumptions and field-selection decision:

- **Valid candidates:**
  - `property_value_gbp` assumed to be recorded at time of application.
  - `deposit_gbp` assumed to be recorded at time of application but may be _related_ to `requested_loan_gbp` and `loan_to_value_pct`.
  - `requested_loan_gbp` assumed to be recorded at time of application. The assumption is more safe because of the fields name 'requested'.
  - `loan_to_value_pct` assumed to be recorded at time of application. My LTV test shows this is most likely (`requested_loan_gbp` / `property_value_gbp`) \* 100.
  - `debt_to_income_ratio` assumed to be recorded before a decision is made (which is where we would encounter a timing or leakage issue). Investigation shows it is likely: (`monthly_debt_commitments_gbp` + `requested_loan_gbp` \* 0.055/12 ) / (`annual_income_gbp`/12). It doesnt seem to use `interest_rate_pct` for its calculation.
  - `monthly_debt_commitments_gbp` assumed to be recorded at time of application. Is _related_ to `debt_to_income_ratio` but may provide new information.
  - `credit_score` assumed to be recorded at time of application. Many missing values that need handling.
  - `savings_gbp` assumed to be recorded at time of application. Many missing values that need handling. Some uncertainty about definition and visibility.
  - `missed_payments_24m` assumed to be recorded at time of application for the previous 24 months. Investigation shows `missed_payments_24m` was recorded at a different time to the TARGET (assumed before).
  - `credit_utilisation_pct` assumed to be recorded at time of application. Many missing values that need handling. Credit score usually takes monthly credit utilisation into account but any values that are missing a credit score seem to atleast contain credit utilisation and vice versa.
  - `previous_default_flag` retained only if the relevant history predates assessment. Indicates the applicant has a formal financial default recorded on their credit history within the last 6 years before application approved.
  - `term_years` assumed to be recorded at time of application. Divisible by 5 so is most likely the 'overall term' of the mortgage. This is the total lifespan of the loan. It is the time horizon calculated to completely pay off the debt down to zero.

- **Conditional candidates:**
  - `annual_income_gbp` investigate availability and interpretation.
  - `employment_type` encoding and fairness concerns need consideration.
  - `employment_years` needs careful consideration and definition before we can know if it is useful. Also contains a lot of missing values.

- **Excluded from predictors:**
  - `application_id` excluded as it is an identifier.
  - `application_channel` should be excluded from the model because it is an administrative variable with proxy and fairness concerns.
  - `repayment_difficulty_12m` is the future target and must never be an input.
  - `interest_rate_pct` excluded as the investigation shows indication it may not have been known at application time.

IQR flags are statistical screening results, not proof that a value is invalid.
For example, a high income, property value, or savings balance may be genuine.
Some lower fences are negative because the IQR formula is distribution-based; this does not make negative financial values valid.
Domain rules are checked separately.
The screening therefore informs review rather than automatic deletion or replacement.

**Action Points:**

- Check the versions of rate, term, property value and LTV. They can exist before assessment but may have been overwritten after a decision.

### Does an identifier or outcome leak the answer into the inputs?

- Even historical missed payments become leakage if sourced from a later report containing information unavailable then. Use information available at the decision timestamp.

### Are values missing, unusual, duplicated or inconsistent?

The dataset contains 800 applications and 19 fields.

#### MISSING VALUES SUMMARY:

|                        | Missing Count | Missing % |
| ---------------------- | ------------- | --------- |
| credit_score           | 21            | 2.6       |
| employment_years       | 31            | 3.9       |
| savings_gbp            | 24            | 3.0       |
| credit_utilisation_pct | 19            | 2.4       |

**TOTAL MISSING CELLS:** 95 across 91 distinct applications (representing approximately 11.4% of applications)

- No duplicate application IDs.
- No fully duplicated records.

#### Interquartile Range (IQR) screening to identify statistically unusual values:

**IQR SCREENING:**
| field | q1 | q3 | lower_fence | upper_fence | flagged_count |
| ------------ | --------- | --------- | --------- | --------- | --------- |
| annual_income_gbp | 40150.000 | 68857.00000 | -2910.500000 | 111917.500000 | 27 |
| property_value_gbp | 196644.500 | 315957.00000 | 17675.750000 | 494925.750000 | 21 |
| deposit_gbp | 30121.250 | 63414.50000 | -19818.625000 | 113354.375000 | 25 |
| requested_loan_gbp | 156799.000 | 252050.50000 | 13921.750000 | 394927.750000 | 24 |
| loan_to_value_pct | 76.310 | 86.44750 | 61.103750 | 101.653750 | 4 |
| monthly_debt_commitments_gbp | 192.750 | 510.00000 | -283.125000 | 985.875000 | 27 |
| debt_to_income_ratio | 0.207 | 0.41825 | -0.109875 | 0.735125 | 31 |
| credit_score | 649.000 | 738.00000 | 515.500000 | 871.500000 | 3 |
| employment_years | 3.500 | 9.10000 | -4.900000 | 17.500000 | 20 |
| savings_gbp | 4627.250 | 18488.50000 | -16164.625000 | 39280.375000 | 49 |
| missed_payments_24m | 0.000 | 1.00000 | -1.500000 | 2.500000 | 12 |
| credit_utilisation_pct | 23.810 | 52.18000 | -18.745000 | 94.735000 | 0 |
| term_years | 20.000 | 30.00000 | 5.000000 | 45.000000 | 0 |
| interest_rate_pct | 4.310 | 5.29000 | 2.840000 | 6.760000 | 7 |

#### Domain validation:

No domain-invalid values found.

#### Consistency and contradiction checks:

Loan / property / deposit inconsistencies (> £1):

- Empty DataFrame
- Columns: [application_id, requested_loan_gbp, property_value_gbp, deposit_gbp, expected_loan_gbp, loan_difference_gbp]
- Index: []

Recorded / calculated LTV inconsistencies (> 0.02 percentage points):

- Empty DataFrame
- Columns: [application_id, loan_to_value_pct, calculated_ltv_pct, ltv_difference_percentage_points]
- Index: []

Requested loan plus deposit matches property value within approximately £1.
Recorded LTV closely matches requested_loan_gbp / property_value_gbp × 100.

Recorded DTI Checks:

- **DTI Hypothesis A (Variable rate) mismatches:** 633 mismatches (absolute difference > 0.01)

- **DTI Hypothesis B (Fixed 4.5% rate) mismatches:** 794 mismatches (absolute difference > 0.01)

- **DTI Hypothesis C (Fixed 5% rate) mismatches:** 709 mismatches (absolute difference > 0.01)

- **DTI Hypothesis D (Fixed 5.5% rate) mismatches:** 0 mismatches (absolute difference > 0.01)

- **DTI Hypothesis E (Fixed 6% rate) mismatches:** 701 mismatches (absolute difference > 0.01)

**Most likely DTI calculation:**

- Fixed 5.5% rate
- 0 mismatches (absolute difference > 0.01)
- Median absolute difference: 0.000

The recorded DTI most closely matches the tested simplified formula using a fixed
5.5% rate, with zero differences above the chosen 0.01 tolerance. This is the
closest tested hypothesis, not a confirmed definition of the recorded DTI or
real-world ground truth. The result does not prove that `interest_rate_pct` was
available before the lending decision, so it remains separate to avoid leakage.

### Are highly related variables providing useful information, or simply repeating each other?

#### CORRELATION ANALYSIS:

**Top 20 strongest absolute correlations (disregarding `application_id` & `repayment_difficulty_12m`):**
| | | |
| -- | -- | -- |
| property_value_gbp | requested_loan_gbp | 0.972662 |
| | deposit_gbp | 0.682387 |
| deposit_gbp | loan_to_value_pct | -0.673520 |
| annual_income_gbp | debt_to_income_ratio | -0.642914 |
| requested_loan_gbp | debt_to_income_ratio | 0.515017 |
| deposit_gbp | requested_loan_gbp | 0.493975 |
| property_value_gbp | debt_to_income_ratio | 0.481011 |
| monthly_debt_commitments_gbp | debt_to_income_ratio | 0.366926 |
| requested_loan_gbp | loan_to_value_pct | 0.223219 |
| deposit_gbp | debt_to_income_ratio | 0.179799 |
| loan_to_value_pct | debt_to_income_ratio | 0.177770 |
| previous_default_flag | interest_rate_pct | 0.099236 |
| credit_score | interest_rate_pct | -0.091687 |
| annual_income_gbp | deposit_gbp | 0.090761 |
| savings_gbp | previous_default_flag | -0.075887 |
| requested_loan_gbp | monthly_debt_commitments_gbp | 0.067506 |
| annual_income_gbp | loan_to_value_pct | -0.066481 |
| monthly_debt_commitments_gbp | employment_years | 0.064707 |
| property_value_gbp | monthly_debt_commitments_gbp | 0.064216 |
| monthly_debt_commitments_gbp | missed_payments_24m | -0.060057 |

**Some variables are strongly related and may contain overlapping information:**

- `property_value_gbp` and `requested_loan_gbp` have a correlation of approximately 0.97.
- `deposit_gbp` and `loan_to_value_pct` have a correlation of approximately −0.67.
- `annual_income_gbp` and `debt_to_income_ratio` have a correlation of approximately −0.64.
- `requested_loan_gbp` and `debt_to_income_ratio` have a correlation of approximately 0.52.
- `loan_to_value_pct` (LTV) is also calculated from the requested loan and property value, so including all three may repeat similar information. This could make the model harder to interpret and may give a feature more influence without adding genuinely new evidence.

**Approach:**

- Compare feature sets experimentally by adding one justified feature at a time, use the same train/test process, and compare precision, recall, F1, ROC AUC, and the confusion matrix.
- Keep the simpler model if additional variables do not provide meaningful improvement.

### What could false negatives and false positives mean for a real human reviewer?

**A false negative**

- Occurs when the model predicts no repayment difficulty but the observed outcome is class 1.
- In practice, this could cause a reviewer to underestimate risk and fail to request additional evidence or scrutiny.

**A false positive**

- Occurs when the model flags repayment difficulty but the observed outcome is class 0.
- This could lead to unnecessary additional checks, delay, or inconvenience for an applicant.

**Both types of error matter. The importance depends on the system’s purpose:**

- If the system is intended to identify applications needing further review, recall may be important because missed cases are concerning.
- If excessive referrals create significant burden or unfair treatment, precision also matters.
- Accuracy alone is insufficient because the majority class is more common and a model can achieve reasonable accuracy while missing all class-1 cases.

### Could variables be unfair proxies, and how would you document and investigate this limitation?

Potential proxy concerns include:

- application_channel, which may reflect digital access, geography, broker access, or socioeconomic circumstances.
- employment_type, which may disadvantage self-employed, contractor, or non-standard workers.
- Income, savings, deposit, property value, and loan amount, which may reflect wealth and regional housing differences.
- Credit score, missed payments, utilisation, and previous defaults, which may reflect unequal access to credit or historical financial disadvantage.
- Employment history, which could disadvantage applicants with career breaks or less traditional work patterns.

The dataset does not contain protected-characteristic information, timestamps, or detailed data provenance. Therefore, fairness cannot be established from the available data. However, the absence of protected attributes does not prove that the model is fair.
