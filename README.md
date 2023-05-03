# Aide à la paye d'une auxiliaire parentale ([Pajemploi](https://www.pajemploi.urssaf.fr/))

Ce projet vous aide à remplir vos déclarations Pajemploi pour votre auxiliaire parentale et à faire le suivi des congés payés et des jours de récupération dans le cadre d'une garde partagée ou non.

## Contexte

Une des difficultés principales de la paye d'une auxiliaire parentale est [l'obligation de mensualiser](https://www.pajemploi.urssaf.fr/pajewebinfo/cms/sites/pajewebinfo/accueil/employeur-de-garde-denfants-a-do/je-recrute-et-jemploie/determiner-le-salaire.html#c09f91) son salaire si ses horaires sont réguliers.

Cela implique que son salaire doit être le même tous les mois, indépendamment du nombre de jours ouvrés du mois.

Le salaire mensualisé de base correspond alors à :
`(Salaire horaire net X Nb d’heures de travail effectif par semaine X 52 semaines) ÷ 12`

Malheureusement, les spécificités propres à chaque mois (congés maladie, vacances, etc.) rendent la déclaration de la paye complexe néamoins.

Ce outil vous permet de prendre en compte ces spécificités, de mensualiser le salaire de votre auxiliaire parentale et de prendre en compte les changements de contrat en cours de mois le cas échéant.

## Comment l'utiliser ?

Entrez les paramêtres constitutifs de votre contrat avec votre auxiliaire parentale dans un fichier `data/{année en chiffre}/{mois en fr en lettre}/confgi.json` en respectant le format suivant :
```
[
    {
        "start_date_period": "2023-04-01",
        "end_date_period": "2023-04-30",
        "config":{
            "hourly_salary": 8.87, # salaire horaire **net**
            "worked_weekly_hours": 50, # nombre d'heures travaillées
            "recovered_weekly_hours": 2, # nombre d'heure non-rémunérées récupérées en jours de récupération
            "transport_monthly_cost": 84.10, # cout de transport de l'auxiliaire
            "transport_allowance_prct": 1, # % de remboursement des coûts de transport
            "daily_meal_allowance": 5, # montant de l'aide alimentaire 
            "allocation_key": {
                "family": ["Martin", "Dupont"],
                "salary": [0.5, 0.5],
                "meal_allowance": [0.5, 0.5],
                "transport_allowance": [0.5, 0.5]
            } # clé de répartition entre les familles de la garde partagée
        }
    },
]
```
La liste peut contenir plusieurs configuration si un changement de contrat a eu lieu en cours de mois.
Dans ce cas :
- Veillez à ce que les plages temporelles soient bien disjointes.
- Veillez à les lister dans l'ordre chronologique.

Entrez ensuite les jours particuliers du mois : jours de récupération / jours de congés, jours fériés du calendrier, arrêts maladie dans un fichier `data/{année en chiffre}/{mois en fr en lettre}/calendars.json` en respectant le format suivant :
```
{
    "paid_leave": [
        {
            "start_date_included": "2023-04-14",
            "end_date_excluded":"2023-04-15"
        }
    ],
    "holidays": [
        {
            "date": "2023-04-10",
            "name": "Pâques"
        }
    ],
    "sick_days": [
        {
            "start_date_included: "2023-04-25",
            "end_date_excluded": "2023-04-28"
        }
    ]
}
```
Laissez chaque liste vide le cas échéant.

Vous pouvez ensuite utiliser le fichier `wage-split-generator.ipynb` pour obtenir les détails à remplir sur Pajemploi.