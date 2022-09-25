import pandas as pd
import numpy as np
import datetime as dt

INPUT_FILE_PATH = 'input_data.xslx'

def read_file() -> pd.DataFrame:
    df = pd.read_excel(INPUT_FILE_PATH)
    return df


def get_tax_rate(state):
    state_rates = {'IL': .0251, 'TN': .01766, }
    return state_rates[state]

def write_new_file(aggregated_data_frame: pd.DataFrame, report_date: str):
    aggregated_data_frame.to_excel(f'aggregated_report-{report_date}.xlsx')
    return

def get_annual_days (start_date: dt.date) -> int:
    ''' Given a starting date, returns the number of proleptic Gregorian 
        days between that date and the same day of the same month one 
        year later.  For example:

            — `get_annual_days('2021-01-01')` -> 365

            — `get_annual_days('2016-03-15')` -> 365

            — `get_annual_days('2016-02-15')` -> 366

            — `get_annual_days('1582-01-01')` -> 365 and _not_ 355

        
    '''
    one_year = dt.timedelta(years=1)  
    end_date = start_date+one_year
    return (end_date-start_date).days

def get_pro_rata_gwp (srs: pd.Series) -> pd.Series:
    ''' Given an appropriately sanitized Pandas `Series` with effective 
        date, expiration date,  and annual gross written premium (GWP) 
        of a policy, returns the  pro-rata GWP of that policy.
    ''' 
    return srs['Effective Days']*srs['Daily GWP']

def get_daily_gwp (srs: pd.Series) -> pd.Series:
    ''' Given an appropriately sanitized Pandas `Series` with annual 
        Gross Written Premium (GWP) and effective date of a policy, 
        returns the daily GWP of that policy.
    '''
    return srs['Annual GWP']/get_annual_days(srs['Effective Date'])

def get_earned_unearned_premium (srs: pd.Series) -> pd.Series:
    rd = dt.date.today()
    sd = srs['Effective Date'], ed = srs['Expiration Date']
    if (rd <= sd):
        effective_so_far = 0
        ineffective_remaining = srs['Effective Days']
    elif (rd <= ed):
        effective_so_far =  (rd-sd).days
        ineffective_remaining = (ed-rd).days
    else: 
        effective_so_far = srs['Effective Days']
        ineffective_remaining = 0   # if only 

    return [effective_so_far*srs['Daily GWP'], 
            ineffective_remaining*srs['Daily GWP']]

def get_taxes (srs: pd.Series) -> pd.Series:
    return get_tax_rate(srs['State'])*srs['Pro-Rata GWP']

def sanitize_data (df: pd.DataFrame): return df # STUB

def main():
    report_date = '2022-08-01'
    df = sanitize_data(read_file())
    df['Effective Days'] = df.apply(lambda srs: (srs['Expiration Date']-
                                                 srs['End Date'].days), 
                                    axis=1)
    df['Daily GWP'] = df.apply(get_daily_gwp, axis=1)
    df['Pro-Rata GWP'] = df.apply(get_pro_rata_gwp, axis=1)
    df[['Earned Premium', 
        'Unearned Premium']] = df.apply(get_earned_unearned_premium, 
                                        axis=1,
                                        result_type='expand')
    df['Taxes'] = df.apply(get_taxes, axis=1)
    # your processing precedes
    write_new_file(df, report_date)
    return
