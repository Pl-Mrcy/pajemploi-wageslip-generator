from datetime import date, timedelta
from IPython.display import Markdown, display
import pandas as pd
import numpy as np
from functools import reduce


def apply_calendar(row, calendar):
    for period in calendar:
        if (period['start_date_included'] == period['end_date_excluded']) and (pd.Timestamp(period['start_date_included']) == row['date']):
            return 0.5
        elif pd.Timestamp(period['start_date_included']) <= row['date'] < pd.Timestamp(period['end_date_excluded']):
            return 1
    return 0

def is_holiday(row, holidays):
    for holiday in holidays:
        if pd.Timestamp(holiday['date']) == row['date']:
            return 1
    return 0

def generate_calendar(start_date, end_date, vacation_calendar, holidays, sick_days):
    date_range = pd.date_range(start_date, end_date)
    working_days = [day.weekday() < 5 for day in date_range]
    df = pd.DataFrame({'date': date_range, 'working_day': working_days})
    df['holidays'] = df.apply(is_holiday, axis=1, holidays=holidays)
    df['sick_days'] = df.apply(apply_calendar, axis=1, calendar=sick_days)
    df['vacation'] = df.apply(apply_calendar, axis=1, calendar=vacation_calendar)
    df['working_holidays'] = df['working_day']*df['holidays']
    df['working_sick_days'] = df['working_day']*(1-df['holidays'])*df['sick_days']
    df['working_vacation'] = df['working_day']*(1-df['holidays'])*(1-df['sick_days'])*df['vacation']
    df['worked_days'] = df['working_day']*(1-df['vacation'])*(1-df['holidays'])*(1-df['sick_days'])
    df['worked_hours'] = df['worked_days']*10
    
    return df, len(df), df['working_day'].sum(), df['working_vacation'].sum(), df['working_holidays'].sum(), df['working_sick_days'].sum(), np.floor(df['worked_days'].sum()), df['worked_hours'].sum()

def display_monthly_review(start_date, end_date, vacation_calendar, holidays, sick_days):
    df_month, num_days_month, num_working_days_month, num_vacation_days_month, num_holidays_month, num_working_sick_days_month, num_full_worked_days_month, num_worked_hours_month = generate_calendar(start_date, end_date, vacation_calendar, holidays, sick_days)
    
    display(Markdown(f"<b> Résumé du mois :</b>"))
    display(Markdown(f"Le mois a compté {num_days_month} jours"))
    display(Markdown(f"Le mois a compté {num_working_days_month} jours ouvrés"))
    display(Markdown(f"Le mois a compté {num_vacation_days_month} jours de congés payés"))
    display(Markdown(f"Le mois a compté {num_holidays_month} jour(s) férié(s) de semaine"))
    display(Markdown(f"Le mois a compté {num_working_sick_days_month} jour(s) de congé maladie ouvrés"))
    display(Markdown(f"Le mois a compté {num_full_worked_days_month} jours complètement travaillées"))
    display(Markdown(f"Le mois a compté {num_worked_hours_month} heures travaillées"))

    
def compute_salary(num_normal_hours, num_increased_hours, config):
    normal_hours_wage = num_normal_hours*config["hourly_salary"]
    increased_hours_wage = num_increased_hours*(config["hourly_salary"]*1.25)
    return normal_hours_wage+increased_hours_wage

def compute_meal_allowance(num_full_worked_days, config):
    return num_full_worked_days * config['daily_meal_allowance']

def compute_transport_allowance(num_working_days_period, num_working_days_month, config):
    transport_cost = config['transport_monthly_cost']*config['transport_allowance_prct']
    period_weight = num_working_days_period / num_working_days_month
    return transport_cost*period_weight

def compute_wage_period(period, num_working_days_month, vacation_calendar, holidays, sick_days):
    config = period['config']
    
    num_weeks_per_month = 52/12
    num_normal_hours = num_weeks_per_month*config['normal_weekly_hours']
    num_increased_hours = num_weeks_per_month*config['increased_weekly_hours']
    num_recovered_hours = num_weeks_per_month*config['recovered_weekly_hours']*config['recovery_coefficient']
    num_recovered_days_yearly = 12*(num_recovered_hours/config['num_daily_hours'])
    
    df_period, num_days_period, num_working_days_period, num_vacation_days_period, num_holidays_period, num_working_sick_days_period, num_full_worked_days_period, num_worked_hours_period = generate_calendar(period['start_date_period'], period['end_date_period'], vacation_calendar, holidays, sick_days)
    
    period_weight = num_working_days_period / num_working_days_month
    
    # We want to take into account the sick days in the computation
    # However, since we smooth the salary over the months of the year to have an equal salary each month
    # despite the number of working days varying, we can´t make a simple withdrawal of the sick hours
    # We compte the number of the number of weeks she was on sick leave and allocate those bits of weeks
    # on normal hours and increased hours.
    num_working_sick_hours_period_averaged = (num_working_sick_days_period/5)*(config['normal_weekly_hours']+config['increased_weekly_hours'])
    num_sick_normal_hours_period_averaged = num_working_sick_hours_period_averaged*(num_normal_hours/(num_normal_hours+num_increased_hours))
    num_sick_increased_hours_period_averaged = num_working_sick_hours_period_averaged*(num_increased_hours/(num_normal_hours+num_increased_hours))
    
    num_effective_normal_hours_period = num_normal_hours-num_sick_normal_hours_period_averaged
    num_effective_increased_hours_period = num_increased_hours-num_sick_increased_hours_period_averaged
    
    salary_period = compute_salary(
        num_normal_hours=num_effective_normal_hours_period*period_weight,
        num_increased_hours=num_effective_increased_hours_period*period_weight,
        config=config
    )
    meal_allowance_period = compute_meal_allowance(num_full_worked_days_period, config)
    transport_allowance_period = compute_transport_allowance(num_working_days_period, num_working_days_month, config)
    
    wage_allocation = config['allocation_key'].copy()
    wage_allocation['salary'] = wage_allocation['salary']*salary_period
    wage_allocation['num_normal_hours'] = config['allocation_key']['salary']*num_effective_normal_hours_period*period_weight
    wage_allocation['num_increased_hours'] = config['allocation_key']['salary']*num_effective_increased_hours_period*period_weight
    wage_allocation['meal_allowance'] = wage_allocation['meal_allowance']*meal_allowance_period
    wage_allocation['transport_allowance'] = wage_allocation['transport_allowance']*transport_allowance_period
    wage_allocation.set_index('family', inplace=True)
    
    return wage_allocation

def compute_period_wages(start_date, end_date, periods, vacation_calendar, holidays, sick_days):
    df_month, num_days_month, num_working_days_month, num_vacation_days_month, num_holidays_month, num_working_sick_days_month, num_full_worked_days_month, num_worked_hours_month = generate_calendar(start_date, end_date, vacation_calendar, holidays, sick_days)
    
    wages = []
    for period in periods:
        tmp = compute_wage_period(period=period, num_working_days_month=num_working_days_month, vacation_calendar=vacation_calendar, holidays=holidays, sick_days=sick_days)
        wages.append(tmp)

    return wages

def compute_total_wages(period_wages):
    return reduce(lambda x, y: x.add(y, fill_value=0), period_wages)
    
def display_urssaf_input_values(total_wages_month, family_name):
    display(Markdown(f"<b>À entrer dans Pajemploi :</b>"))
    display(Markdown(f"Salaire net {family_name} : {total_wages_month.loc[family_name]['salary'] + total_wages_month.loc[family_name]['meal_allowance']}€"))
    display(Markdown(f"Nombre d'heures effective : {total_wages_month.loc[family_name]['num_normal_hours']}"))
    display(Markdown(f"Nombre d'heures supplémentaires à 25% : {total_wages_month.loc[family_name]['num_increased_hours']}"))
    display(Markdown(f"Frais de transport: {total_wages_month.loc[family_name]['transport_allowance']}€"))