## Koffie Insurance System/Reporting Engineer - Coding Challenge

### Objective

This repo contains an intentionally incomplete python application to generate a report output.

Complete the application by writing a series of python functions to extract the provided data,
append columns which contain calculated values, and create an aggregated output report.

### Time Expectation

We expect this challenge to take you 3-5 hours to complete (one or two evenings). You may take as much time as you need to submit the challenge.

### Requirements

This application should do the following

1. Read the provided Excel file into python as a pandas DataFrame
2. Add four calculated columns to the DataFrame:
   1. Pro-rata Gross Written Premium
   2. Earned premium
   3. Unearned premium
   4. Taxes
3. Aggregate by Company Name to count number of vehicles/VINs and sum vehicle pro-rata GWP, earned premium, unearned premium, and taxes
4. Generate a report output showing number of vehicles and sums of the calculated values by company

You can assume that the input filename is static and does not change. You do not need to spend time adding capabilities 
to specify the filename from the command line, etc.

#### Output Format

The output file should be an Excel worksheet containing the following columns:

- Company Name
- Report Date
- Total Count of Vehicles (VINs)
- Total Annual GWP
- Total Pro-Rata GWP
- Total Earned Premium
- Total Unearned Premium
- Total Taxes

### Instructions for Calculations

#### Pro-rata GWP
1. Divide the total annual premium by the number of days in a year to get daily GWP
2. Determine the number of days between the effective date and expiration date to get number of effective days
3. Multiply daily GWP (#1) by the number of effective days (#2) to get pro-rata GWP


#### Earned/unearned premium
1. Calculate pro-rata GWP
2. Calculate number of effective days
4. Divide pro-rata GWP (#2) by number of days effective (#1) to get daily GWP
5. Determine the number of days between the effective date and the report date
6. Determine the number of days between report date and the expiration date
7. Multiply number of days effective (#4) by daily GWP (#3) to calculate earned premium
8. Multiply number of days remaining (#5) by daily GWP (#3) to calculate unearned premium

#### Tax Rates

- IL: 1.766%
- TN: 2.51%

### Project Structure and Setup

You may structure your project as you wish.

To test your application, we will create a new `pyenv` environment, install requirements.txt, and run it from the command line, i.e.: `python main.py`

You do not need to deploy your code, but you should be prepared to have a conversation about your ideas on how to do so.

When you're ready to submit your work to us, create a git repo, push your results, and send us the link.

### Our Evaluation

- Basic functionality
- Code quality
- Error handling
- Documentation (readme/comments/tests)
- Ability to explain your implementation decisions
