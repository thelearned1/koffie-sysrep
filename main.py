import pandas as pd


def read_file() -> pd.DataFrame:
    df = pd.read_excel('input_data.xlsx')
    return df


def get_tax_rate(state):
    state_rates = {'IL': .0251, 'TN': .01766, }
    return state_rates[state]


def write_new_file(aggregated_data_frame: pd.DataFrame, report_date: str):
    aggregated_data_frame.to_excel(f'aggregated_report-{report_date}.xlsx')
    return


def main():
    report_date = '2022-08-01'
    df = read_file()
    # your processing here
    write_new_file(df, report_date)
    return
