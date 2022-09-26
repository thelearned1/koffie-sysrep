from array import array
from itertools import count
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
    start_date = srs['Effective Date'] 
    agwp = srs['Annual GWP']
    if (agwp is None):
        return 0        # can't determine daily GWP without annual GWP

    if (start_date is None):    # there is no (parsable) Effective Date
        return agwp/365.2425    # so use average number of days in the year.

    # Use the actual number of days in the policy year
    return agwp/get_annual_days(start_date)

def get_earned_unearned_premium (srs: pd.Series, report_date: dt.date) -> pd.Series:
    ''' Given:

        — a pandas `Series` containing an effective date, expiration
        date, and daily gross written premium 
        
        — the date of the report

        returns a list of two elements: the earned premium and unearned 
        premium of that policy current to the report date.

        If there is no effective date, earned premium will be zero.
        If there is no expiration date, unearned premium will be zero.
    '''
    sd = srs['Effective Date']
    ed = srs['Expiration Date']
    if (not (sd and ed)):    # either of these is None / falsy
        if (sd and not ed):  # can calculate earned premium, not unearned premium
            effective_so_far = max((report_date-sd).days, 0)
            ineffective_remaining = 0
        elif (ed and not sd):# can calculate unearned premium, not earned premium
            return [0, max((ed-report_date).days, 0)]
        else:                # can calculate neither earned nor unearned premium
            return [0, 0]
    elif (report_date < sd): # report date is prior to effective date
        effective_so_far = 0
        ineffective_remaining = srs['Effective Days']
    elif (report_date < ed): # report date is in the range [effective date, expiration date]
        effective_so_far =  (report_date-sd).days
        ineffective_remaining = (ed-report_date).days
    else:                    # report date is after the expiration date
        effective_so_far = srs['Effective Days']
        ineffective_remaining = 0  
    return [effective_so_far*srs['Daily GWP'], 
            ineffective_remaining*srs['Daily GWP']]

def get_taxes (srs: pd.Series) -> pd.Series:
    ''' Given a pandas `Series`, returns the taxes on pro-rata GWP for
        the state in which the policy was written.
    '''
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
    vinre = '^[0-9A-HJ-NPR-Z]{17}$' # VINs cannot contain 'O', 'Q', or 'I'
    vin = srs['VIN'].upper()
    vin = vin if (vin and re.search(vinre, vin)!=None) else None
    effective = dt_cleanup(srs['Effective Date'])
    expiration = dt_cleanup(srs['Expiration Date'])
    if (effective > expiration): 
        effective = None
        expiration = None
    gwp = int_cleanup(srs['Annual GWP'])
    return [vin, effective, expiration, gwp] 

def sanitize_df (df: pd.DataFrame):
    ndf = df.copy()
    ndf[['VIN', 
        'Effective Date', 
        'Expiration Date', 
        'Annual GWP']] = ndf.apply(sanitize_row, axis=1, result_type='expand')
    return ndf

def get_effective_days (srs: pd.Series):
    start_date = srs['Effective Date']
    end_date = srs['Expiration Date']
    if (start_date and end_date):
        return (end_date - start_date).days
    return 0

def main():
    s_report_date = '2022-08-01'
    # my processing follows

    # storing s_report_date as a Datetime `date` for later
    report_date = dt.datetime.strptime(s_report_date, '%Y-%m-%d').date()

    # There is some dirt in this data. 
    df = sanitize_df(read_file())

    # Effective days and Daily GWP are used repeatedly, so we are writing
    # values directly into the pandas series for efficiency.
    df['Effective Days'] = df.apply(get_effective_days, axis=1)
    df['Daily GWP'] = df.apply(get_daily_gwp, axis=1)

    # four required new columns for aggregation (see README).  These
    # rely on Effective Days and Daily GWP.
    df['Pro-Rata GWP'] = df['Daily GWP']*df['Effective Days'] # vectorized
    df[['Earned Premium', 'Unearned Premium']] = df.apply(  
        lambda x: get_earned_unearned_premium(x, report_date), 
        axis=1,
        result_type='expand')
    # Relies on pro-rata GWP
    df['Taxes'] = df.apply(get_taxes, axis=1) 

    # Aggregation 
    ag_functions = {
        'VIN': 'count',
        'Annual GWP': 'sum',
        'Pro-Rata GWP': 'sum',
        'Earned Premium': 'sum',
        'Unearned Premium': 'sum',
        'Taxes': 'sum'
    }

    aggregated_df = (
         df.groupby('Company Name')
        .aggregate(ag_functions)
        .rename(columns = {
            'VIN': 'Total Count of Vehicles (VINs)',
            'Annual GWP': 'Total Annual GWP',
            'Pro-Rata GWP': 'Total Pro-Rata GWP',
            'Earned Premium': 'Total Earned Premium',
            'Unearned Premium': 'Total Unearned Premium',
            'Taxes': 'Total Taxes'
        })
    )

    currencies = [
        'Total Annual GWP', 
        'Total Pro-Rata GWP', 
        'Total Earned Premium',
        'Total Unearned Premium',
        'Total Taxes'
    ]

    aggregated_df[currencies] = aggregated_df[currencies].round(2)

    # my processing precedes
    write_new_file(aggregated_df, s_report_date)
    return

if (__name__=='__main__'):
    main()
