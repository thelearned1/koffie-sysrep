from array import array
import string
import pandas as pd
import numpy as np
import datetime as dt
from dateutil.relativedelta import relativedelta
import re

INPUT_FILE_PATH = 'input_data.xlsx'

def read_file() -> pd.DataFrame:
    print ('reading '+INPUT_FILE_PATH)
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
    end_date = start_date+relativedelta(years=1)
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
    rd = dt.datetime.today().date()
    sd = srs['Effective Date']
    ed = srs['Expiration Date']
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

def dt_cleanup (d):
    if (isinstance(d, dt.datetime)):
        return d.date()
    elif (isinstance(d, dt.date)):
        return d
    else:
        try:
            nd = dt.datetime.strptime(d.replace('O', '0'), '%Y-%m-%d').date()
            return nd
        except:
            return np.NaN

def int_cleanup (i):
    if (not isinstance(i, (int, float))):
        try:
            i = int(i.replace('O', '0'))
        except:
            return np.NaN
    return i

def sanitize_row (srs: pd.Series) -> array: 
    vinre = '^[0-9a-zA-Z]{17}$'
    vin = srs['VIN']
    vin = vin if (vin and len(vin)==17 and re.search(vinre, vin)!=None) else np.NaN
    effective = dt_cleanup(srs['Effective Date'])
    expiration = dt_cleanup(srs['Expiration Date'])
    if (effective > expiration): 
        effective = np.NaN
    gwp = int_cleanup(srs['Annual GWP'])
    return [vin, effective, expiration, gwp] 

def sanitize_df (df: pd.DataFrame):
    ndf = df.copy()
    ndf[['VIN', 'Effective Date', 
         'Expiration Date', 
         'Annual GWP']] = ndf.apply(sanitize_row, axis=1, result_type='expand')
    return ndf.dropna(subset=['VIN', 'Effective Date', 'Expiration Date', 'Annual GWP'])

def main():
    s_report_date = '2022-08-01'
    # my processing follows
    report_date = dt.datetime.strptime(s_report_date, '%Y-%m-%d').date()
    df = sanitize_df(read_file())
    df['Effective Days'] = df.apply(lambda srs: (srs['Expiration Date']-
                                                 srs['Effective Date']).days, 
                                    axis=1)
    df['Daily GWP'] = df.apply(get_daily_gwp, axis=1)
    df['Pro-Rata GWP'] = df.apply(get_pro_rata_gwp, axis=1)
    df[['Earned Premium', 
        'Unearned Premium']] = df.apply(get_earned_unearned_premium, 
                                        axis=1,
                                        result_type='expand')
    df['Taxes'] = df.apply(get_taxes, axis=1)
    # my processing precedes
    write_new_file(df, s_report_date)
    return

if (__name__=='__main__'):
    main()
