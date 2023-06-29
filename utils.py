from datetime import date, timedelta, datetime
from IPython.display import Markdown, display
import pandas as pd
import numpy as np
import os
import json
from functools import reduce


def load_config(year, month):
    # Load the month's config(s) 
    config_filename = f"data/{year}/{month}/config.json"
    try:
        with open(config_filename, 'r') as file:
            config = json.load(file)
        return config
    except:
        raise "No config file for this period"
    
def load_calendars(year, month):
    # Load the month's paid_leaves, sick_days and holidays
    calendars_filename = f"data/{year}/{month}/calendars.json"
    try:
        with open(calendars_filename, 'r') as file:
            config = json.load(file)
        return config['paid_leave'], config['holidays'], config['sick_days']
    except:
        print("No config file for this period")
        return [], [], []


def apply_calendar(row, calendar):
    for period in calendar:
        start_date_included = datetime.strptime(period['start_date_included'], "%Y-%m-%d").date()
        end_date_excluded = datetime.strptime(period['end_date_excluded'], "%Y-%m-%d").date()
        if (start_date_included == end_date_excluded) and (pd.Timestamp(start_date_included) == row['date']):
            return 0.5
        elif pd.Timestamp(start_date_included) <= row['date'] < pd.Timestamp(end_date_excluded):
            return 1
    return 0

def is_holiday(row, holidays):
    for holiday in holidays:
        holiday_date = datetime.strptime(holiday['date'], "%Y-%m-%d").date()
        if pd.Timestamp(holiday_date) == row['date']:
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

    return df_month

    
def compute_salary(hours, config):
    #  il n’est pas LÉGAL de rémunérer les heures sup 49 et 50 quand elles sont effectuées, 
    #  on ne peut rémunérer que la majoration de 50%. 
    # Les heures elles-mêmes doivent être RÉCUPÉRÉES.
    return (hours[0]+hours[1]*1.25+hours[2]*0.5)*config["hourly_salary"]

def compute_meal_allowance(num_full_worked_days, config):
    return num_full_worked_days * config['daily_meal_allowance']

def compute_transport_allowance(num_working_days_period, num_working_days_month, config):
    transport_cost = config['transport_monthly_cost']*config['transport_allowance_prct']
    period_weight = num_working_days_period / num_working_days_month
    return transport_cost*period_weight

def split_working_hours(hours):
    if hours > 50:
        print("Il n'est pas permis de faire travailler votre assitante plus que 50 heures par semaine.")
        raise
    else:
        normal_hours = min(40, hours)
        increased_25prct_hours = min(8, max(0, hours - 40))
        increased_50prct_hours = max(0, hours - 48)
        return normal_hours, increased_25prct_hours, increased_50prct_hours

def compute_paid_and_recovered_weekly_hours(worked_weekly_hours, recovered_weekly_hours):

    worked_normal_hours, worked_increased_hours_25prct, worked_increased_hours_50prct = split_working_hours(worked_weekly_hours)
    paid_normal_hours, paid_increased_hours_25prct, paid_increased_hours_50prct = split_working_hours(worked_weekly_hours-recovered_weekly_hours)

    if paid_increased_hours_50prct > 0:
        recovered_hours_50prct_unincreased = paid_increased_hours_50prct
    else:
        recovered_hours_50prct_unincreased = 0
    recovered_weekly_hours = [worked_normal_hours-paid_normal_hours+recovered_hours_50prct_unincreased, worked_increased_hours_25prct-paid_increased_hours_25prct, worked_increased_hours_50prct-paid_increased_hours_50prct]

    return [paid_normal_hours, paid_increased_hours_25prct, paid_increased_hours_50prct], recovered_weekly_hours


def compute_paid_leave_acquired_period(worked_weekly_hours, total_recovered_hours_carried, num_working_sick_days_period, period_weight):
    # Calcul du nombre de congés payés accumulés
    # L'auxiliaire n'accumule pas de congés payés pendant un congé maladie.
    # En revanche, les jours fériés et les congés payés comptent pour le calcul des congés payés suivants.
    sick_leave_weight = num_working_sick_days_period/(5*52/12)
    contractual_cp_days_per_year = 25
    contractual_cp_days_per_month = contractual_cp_days_per_year/12
    cp_aquired_period = (1-sick_leave_weight)*period_weight*contractual_cp_days_per_month
    recovered_days_acquired_period = period_weight*total_recovered_hours_carried/(worked_weekly_hours/5)

    return cp_aquired_period, recovered_days_acquired_period

def compute_wage_period(period, num_working_days_month, vacation_calendar, holidays, sick_days):
    config = period['config']
    
    paid_hours, recovered_hours = compute_paid_and_recovered_weekly_hours(config['worked_weekly_hours'], config['recovered_weekly_hours'])

    num_weeks_per_month = 52/12
    
    paid_hours_carried = [num_weeks_per_month*h for h in paid_hours]
    total_recovered_hours_carried = num_weeks_per_month*(recovered_hours[0]+recovered_hours[1]*1.25+recovered_hours[2]*1.5)
    
    df_period, num_days_period, num_working_days_period, num_vacation_days_period, num_holidays_period, num_working_sick_days_period, num_full_worked_days_period, num_worked_hours_period = generate_calendar(period['start_date_period'], period['end_date_period'], vacation_calendar, holidays, sick_days)
    
    period_weight = num_working_days_period / num_working_days_month
    
    # We want to take into account the sick days in the computation
    # However, since we smooth the salary over the months of the year to have an equal salary each month
    # despite the number of working days varying, we can´t make a simple withdrawal of the sick hours
    # We compte the number of the number of weeks she was on sick leave and allocate those bits of weeks
    # on normal hours and increased hours.
    total_working_sick_hours_period_carried = (num_working_sick_days_period/5)*(sum(paid_hours))
    sick_hours_carried = [total_working_sick_hours_period_carried*h/sum(paid_hours_carried) for h in paid_hours_carried]
    
    num_effective_hours_period = [paid_hours_carried[i]*period_weight-sick_hours_carried[i] for i in range(len(paid_hours_carried))]
    
    salary_period = compute_salary(
        hours=num_effective_hours_period,
        config=config
    )
    meal_allowance_period = compute_meal_allowance(num_full_worked_days_period, config)
    transport_allowance_period = compute_transport_allowance(num_working_days_period, num_working_days_month, config)
    
    
    cp_aquired_period, recovered_days_acquired_period = compute_paid_leave_acquired_period(config['worked_weekly_hours'], total_recovered_hours_carried, num_working_sick_days_period, period_weight)

    allocation_df = pd.DataFrame(config['allocation_key'])

    wage_allocation = allocation_df.copy()
    wage_allocation['salary'] = wage_allocation['salary']*salary_period
    wage_allocation['num_normal_hours'] = allocation_df['salary']*num_effective_hours_period[0]
    wage_allocation['num_increased_hours_25prct'] = allocation_df['salary']*num_effective_hours_period[1]
    wage_allocation['num_increased_hours_50prct'] = allocation_df['salary']*num_effective_hours_period[2]
    wage_allocation['meal_allowance'] = wage_allocation['meal_allowance']*meal_allowance_period
    wage_allocation['transport_allowance'] = wage_allocation['transport_allowance']*transport_allowance_period
    wage_allocation.set_index('family', inplace=True)
    
    return wage_allocation, cp_aquired_period, recovered_days_acquired_period

def compute_period_wages(start_date, end_date, periods, vacation_calendar, holidays, sick_days):
    df_month, num_days_month, num_working_days_month, num_vacation_days_month, num_holidays_month, num_working_sick_days_month, num_full_worked_days_month, num_worked_hours_month = generate_calendar(start_date, end_date, vacation_calendar, holidays, sick_days)
    
    wages = []
    cp_aquired = []
    recovered_days_acquired = []
    for period in periods:
        wage, cp_aquired_period, recovered_days_acquired_period= compute_wage_period(period=period, num_working_days_month=num_working_days_month, vacation_calendar=vacation_calendar, holidays=holidays, sick_days=sick_days)
        wages.append(wage)
        cp_aquired.append(cp_aquired_period)
        recovered_days_acquired.append(recovered_days_acquired_period)

    return wages, cp_aquired, recovered_days_acquired

def compute_total_wages(period_wages):
    return reduce(lambda x, y: x.add(y, fill_value=0), period_wages)
    
def display_urssaf_input_values(total_wages_month, family_name):
    display(Markdown(f"<b>À entrer dans Pajemploi pour votre famille :</b>"))
    display(Markdown(f"Salaire net {family_name} : {total_wages_month.loc[family_name]['salary'] + total_wages_month.loc[family_name]['meal_allowance']}€"))
    display(Markdown(f"Nombre d'heures effective : {total_wages_month.loc[family_name]['num_normal_hours']}"))
    display(Markdown(f"Nombre d'heures supplémentaires à 25% : {total_wages_month.loc[family_name]['num_increased_hours_25prct']}"))
    display(Markdown(f"Nombre d'heures supplémentaires à 50% : {total_wages_month.loc[family_name]['num_increased_hours_50prct']}"))
    display(Markdown(f"Frais de transport: {total_wages_month.loc[family_name]['transport_allowance']}€"))

def display_paid_leave_acquired(cp_aquired, recovered_days_acquired):
    display(Markdown(f"<b>Pendant cette période, l'auxiliaire a acquis :</b>"))
    display(Markdown(f"{sum(cp_aquired)} jours de congés payés."))
    display(Markdown(f"{sum(recovered_days_acquired)} jours de récupération."))