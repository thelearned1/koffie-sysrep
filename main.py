import string
import pandas as pd
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

def __get_premium(
    srs: pd.Series, 
    report_date: dt.date, 
    key: string, 
    cmpfunc) -> float:
    ''' Given:

        -   an appropriately sanitized Pandas `Series` with a date keyed
            by `key`, a daily Gross Written Premium, and the number of
            effective days in the policy;

        -   a report date;

        -   and a comparison function between dates that returns true 
            iff the first argument is earlier than the second;

        returns the premium owed between the date keyed by `key` and the
        report_date.  

        If any of the conditions above are not met, returns 0.
    '''
    v = srs[key]
    ed = srs['Effective Days']
    if (v and ed and cmpfunc(v, report_date)):
        # logic here:
        #   - if report date comes after v, cmpfunc will be <. So 
        #     
        return min(abs((report_date-v).days), ed) * srs['Daily GWP']
    else:
        return 0

def get_earned_premium (srs: pd.Series, report_date: dt.date) -> float:
    ''' Given:
    
        -   an appropriately sanitized Pandas `Series` with an effective  
            date and daily Gross Written Premium
        -   a report date

        returns the earned premium current to the report date.  Note 
        that it is assumed that the day's premium is not earned until
        AFTER the report date.
    '''
    return __get_premium(
        srs, 
        report_date, 
        'Effective Date', 
        lambda x, y: x < y)

def get_unearned_premium (srs: pd.Series, report_date: dt.date) -> float:
    ''' Given:
    
        -   an appropriately sanitized Pandas `Series` with an expiration 
            date and daily Gross Written Premium
        -   a report date

        returns the unearned premium current to the report date.  Note 
        that it is assumed that the day's premium is not earned until
        AFTER the report date.
    '''
    return __get_premium(
        srs, 
        report_date, 
        'Expiration Date', 
        lambda x, y: x > y)

def get_taxes (srs: pd.Series) -> pd.Series:
    ''' Given a pandas `Series`, returns the taxes on pro-rata GWP for
        the state in which the policy was written.
    '''
    return get_tax_rate(srs['State'])*srs['Pro-Rata GWP']

__string_to_number_cleanup = str.maketrans("OI!ZSBG", "0112589")

def dt_cleanup (d) -> dt.date:
    ''' Given:
        
        - a date, returns the date

        - a datetime, returns the date of that datetime

        - a string, attempts to translate the string into a date.

        Translation consists of replacing alphabetic characters and 
        punctuation marks with numerals that have commonly been 
        confused for those characters. Should this method fail, returns 
        None.
    '''
    if (isinstance(d, dt.datetime)):
        return d.date()
    elif (isinstance(d, dt.date)):
        return d
    else:
        try:
            nd = dt.datetime.strptime(
                d.translate(__string_to_number_cleanup),
                '%Y-%m-%d'
            ).date()
            return nd
        except:
            return None

def int_cleanup (i):
    ''' Given a value i:
       
        - if i is numeric, returns i

        - if i is a string, attempts to translate i into a numeric type.

        Translation consists of replacing alphabetic characters and 
        punctuation marks with numerals that have commonly been 
        confused for those characters. Should this method fail, returns 
        None.
    '''
    if (not isinstance(i, (int, float))):
        try:
            i = int(i.translate(__string_to_number_cleanup))
        except:
            return None
    return i

def sanitize_row (srs: pd.Series): 
    ''' Given a row, sanitizes it, that is, replaces invalid values with
        likely valid values.
    '''
    vinre = '^[0-9A-HJ-NPR-Z]{17}$' # VINs cannot contain 'O', 'Q', or 'I'
    vin = srs['VIN'].upper()
    vin = vin if (vin and re.search(vinre, vin)!=None) else None
    effective = dt_cleanup(srs['Effective Date'])
    expiration = dt_cleanup(srs['Expiration Date'])
    if (effective and expiration and effective > expiration): 
        effective = None
        expiration = None
    gwp = int_cleanup(srs['Annual GWP'])
    return [vin, effective, expiration, gwp] 

def sanitize_df (df: pd.DataFrame):
    ''' Given a DataFrame, sanitizes it, that is, replaces invalid values
        with likely valid values.
    '''
    ndf = df.copy()
    ndf[['VIN', 
        'Effective Date', 
        'Expiration Date', 
        'Annual GWP']] = ndf.apply(sanitize_row, axis=1, result_type='expand')
    return ndf

def get_effective_days (srs: pd.Series):
    ''' Given a series, calculates the 
        
    '''
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
    efd = df['Effective Date']
    exd = df['Expiration Date']
    df['Effective Days'] = (exd-efd).map(lambda x: x.days if ~pd.notnull(x) else 0)
    df['Daily GWP'] = df.apply(get_daily_gwp, axis=1)

    # four required new columns for aggregation (see README).  These
    # rely on Effective Days and Daily GWP.
    df['Pro-Rata GWP'] = df.apply(get_pro_rata_gwp, axis=1)
    df['Earned Premium'] = df.apply(
        lambda x: get_earned_premium(x, report_date),
        axis=1)
    df['Unearned Premium'] = df.apply(
        lambda x: get_unearned_premium(x, report_date),
        axis=1)
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
    aggregated_df.insert(1, 'Report Date', report_date)

    # my processing precedes
    write_new_file(aggregated_df, s_report_date)
    return

if (__name__=='__main__'):
    main()
