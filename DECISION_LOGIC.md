# A log for my decision logic and investigation

## Before training the model:

### Which information could genuinely be known when a new mortgage application is assessed? Is anything recorded **after** the decision?

#### What the law suggests:

The legal and practical basis is that _FCA rule MCOB 11.6.2R_ generally requires an affordability assessment before entering into the mortgage. Rules _11.6.8R_ and _11.6.10–13_ cover **income evidence**, **expenditure** and **obtaining details of outstanding commitments**. These are regulatory requirements and don't prescribe this exact set of data fields.

#### **Data fields:**

- `annual_income_gbp`
  - Income declared and assessed using evidence available at application.
  - Need specificiy or investication regarding gross/net income, and individual/joint income.
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
  - Need specificiy or investication regarding whether the denominator is an initial estimate/lender valuation and whether financed fees are included.
  - FCA disclosure rules explicitly address LTV.
- `monthly_debt_commitments_gbp`
  - Could be known if these are existing monthly debt obligations established during assessment, (need clarity over when ongoing debts will reduce or increase).
  - Need specificiy or investication regarding whether this is included in `debt_to_income_ratio` or not.
  - FCA rules require reasonable steps to establish actual outstanding commitments so there is reasonable justification to assume this was recorded before.
- `debt_to_income_ratio`
  - Could be known since this is calculable from information available at application time. Largely depends on if a fixed interest rate is used to evaluate this at application time.
  - Need to define the DTI formula: _monthly debt payments ÷ monthly income_ differs from _outstanding debt ÷ annual income_ etc. Also a proposed mortgage payment might be included if known. The field name does not establish which measure was used so we must test whether interest rate recorded in data was known at time or whether a fixed rate was used.
- `credit_score`
  - A score most likely obtained or calculated during assessment.
- `employment_type`
  - Could be known if it is employment status at time of application.
- `employment_years`
  - Could be known if it is historical tenure established from the application/supporting evidence.
  - Need to define whether this means current employer, continuous employment or time self-employed; those are different measures.
- `savings_gbp`
  - Could be savings established from statements or other evidence at time of application.
  - However a lender does not automatically know every savings account, and evidence of the deposit does not necessarily establish total savings.
  - Need specificiy or investication regarding whether this includes deposit. A simple calculation should work to verify.
- `missed_payments_24m`
  - Could be known if backward looking. Such as missed payments in the 24 months before assessment, drawn from available credit history.
  - Could verify this by comparing it to `repayment_difficulty_12m` if there are any people who flag as a 1 for this field but dont show any `missed_payments_24m` then `missed_payments_24m` can be reasonably assumed to be at a different time to the 12m period (most likely before) for the purposes of our model.
- `credit_utilisation_pct`
  - Reported revolving-credit balances relative to limits, likely using the report available at application.
- `previous_default_flag`
  - Defaults likely recorded before assessment inferred from 'previous'.
  - It likely doesnt represent perfect knowledge of lifetime defaults: Experian explains that defaults generally disappear from credit reports after six years.
- `term_years`
  - Could be known depending on if this is the requested/proposed mortgage term.
  - Loan duration usually appears in pre-application disclosures but a later revised or final term is a different version. Could probably calculate this.
- `interest_rate_pct`
  - Could be known if this is the pre-disclosed rate. Could check this in relation to other values to find out.
  - FCA rules require pre-application disclosures containing the borrowing rate. However tests seem to reveal that DTI is calculated with a fixed rate so this might only be known after.
- `application_channel`
  - The route through which the application arrived, such as broker, branch or online. This is operational metadata knowable on receipt (that is a practical inference).
- `repayment_difficulty_12m`
  - This is the following 12 months. A future outcome, unavailable at the original decision.
  - Not necessarily default (do not label its score a PD).
  - Exact definition of 'observed repayment difficulty' isnt provided.
  - THIS IS OUR TARGET.

#### Assumptions (continuously updated):

- `missed_payments_24m` and `previous_default_flag` assumed these are usuable and that relevant history predates the application.
- `credit_score` and `credit_utilisation_pct` assumed to come from a credit report available at assessment.

#### The following fields require caution/ action/ investigation:

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

[UPDATE ONCE DONE]

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

The recorded DTI most closely matches the tested formula using a fixed 5.5% rate, with zero differences above the chosen 0.01 tolerance.(CLOSEST tested hypothesis, NOT a confirmed definition of the recorded DTI.)

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
