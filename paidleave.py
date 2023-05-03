import json
from IPython.display import Markdown, display


def load_suivi_conge():
    # Load the month's config(s) 
    config_filename = f"data/suivi-conges.json"
    with open(config_filename, 'r') as file:
        config = json.load(file)
    return config

def clean_calendar(calendar, year, month):
    return [entry for entry in calendar if ((entry["month"] != month) | ((entry["year"] != year)) )]


def compute_nbr_accumulated_days(suivi, cleaned_calendar):
    ## Compute the number of days off available
    total_cp_accumulated = suivi["nbr_jours_conges_payes_initiaux"]
    total_jour_recuperation_accumulated = suivi["nbr_jours_recuperation_initiaux"]
    for m in cleaned_calendar:
        total_cp_accumulated += m["nbr_cp_acquis"]-m["nbr_cp_poses"]
        total_jour_recuperation_accumulated += m["nbr_jours_recuperation_acquis"]-m["nbr_jours_recuperation_poses"]
    return total_cp_accumulated, total_jour_recuperation_accumulated


def update_calendar(clean_calendar, year, month, total_jour_recuperation_accumulated, days_off_used, cp_aquired, recovered_days_acquired):
    nbr_jours_recuperation_poses = min(total_jour_recuperation_accumulated, days_off_used)
    nbr_cp_poses = days_off_used-nbr_jours_recuperation_poses

    updated_calendar = clean_calendar.copy()
    updated_calendar.append(
        {
            "year": year,
            "month": month,
            "nbr_cp_poses": float(nbr_cp_poses),
            "nbr_jours_recuperation_poses": float(nbr_jours_recuperation_poses),
            "nbr_cp_acquis": sum(cp_aquired),
            "nbr_jours_recuperation_acquis": sum(recovered_days_acquired),
            "salaire_net": 0,
            "frais_de_transport": 0
        }
    )
    return updated_calendar

def save_to_suivi(suivi, updated_calendar):
    data = {
        "nbr_jours_conges_payes_initiaux": suivi['nbr_jours_conges_payes_initiaux'],
        "nbr_jours_recuperation_initiaux": suivi['nbr_jours_recuperation_initiaux'],
        "suivi": updated_calendar
    }
    config_filename = f"data/suivi-conges.json"
    with open(config_filename, 'w') as file:
        json.dump(data, file)
    return data


def update_suivi(year, month, cp_aquired, recovered_days_acquired, days_off_used):
    suivi = load_suivi_conge()
    cleaned_calendar = clean_calendar(suivi["suivi"], year, month)

    total_cp_accumulated, total_jour_recuperation_accumulated = compute_nbr_accumulated_days(suivi, cleaned_calendar)

    updated_calendar = update_calendar(cleaned_calendar, year, month, total_jour_recuperation_accumulated, days_off_used, cp_aquired, recovered_days_acquired)

    save_to_suivi(suivi, updated_calendar)

def display_paid_leave_accumulated():
    suivi = load_suivi_conge()
    total_cp_accumulated, total_jour_recuperation_accumulated = compute_nbr_accumulated_days(suivi, suivi['suivi'])

    display(Markdown(f"<b>A ce jour, il reste à l'auxiliaire :</b>"))
    display(Markdown(f"{total_cp_accumulated} jours de congés payés."))
    display(Markdown(f"{total_jour_recuperation_accumulated} jours de récupération."))