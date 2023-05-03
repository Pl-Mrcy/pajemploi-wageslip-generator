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
            "start_date_included": "2023-04-25",
            "end_date_excluded": "2023-04-28",
            "is_work_accident": "False"
        }
    ]
}
```
Laissez chaque liste vide le cas échéant.

Vous pouvez ensuite utiliser le fichier `wage-split-generator.ipynb` pour obtenir les détails à remplir sur Pajemploi.

### Suivi des congés payés

Vous pouvez suivre les congés payés de votre auxiliaire parentale en utilisant la dernière partie du script.
Pour cela, nous utilisons le fichier `data/suivi-conges.json` pour garder automatiquement une trace des congés au fil du temps.

Vous pouvez utiliser les champs disponibles `nbr_jours_conges_payes_initiaux` et `nbr_jours_recuperation_initiaux` si vous commencez à 
utiliser cet outil en cours de route. Sinon, laissez ces champs à 0.

Le script se charge de remplir le calendrier automatiquement ensuite dans le champs `suivi`.

Si vous tournez plusieurs simulations pour la même année et le même mois, le script écrase automatiquement les données dans ce calendrier avec
les derniers résultats.

## Détails

### Jours de récupération

Il n’est pas LÉGAL de rémunérer les heures sup 49 et 50 quand elles sont effectuées, on ne peut rémunérer que la majoration de 50%. Les heures elles-mêmes doivent être RÉCUPÉRÉES.
Il est donc possible de rémunérer la majoration de 50% seulement ou de faire récupérer la totalité des heures 49 et 50 majorés de 50%.

Pour indiquer que vous souhaiter rémunérer la majoration de 50% et ne faire récupérer que les heures 49 et 50 non majorées, indiquez dans la configuration : 
```
    "worked_weekly_hours": 50, 
    "recovered_weekly_hours": 0,
```

Si au contraire, vous ne souhaitez pas du tout rémunérer les heures 49 et 50 et les faire récupérer de facon majorée, indiquez :
```
    "worked_weekly_hours": 50, 
    "recovered_weekly_hours": 2,
```

### Accumulation des congés-payés

L'auxiliaire parentale ne cumule pas de congés payés pendant un arrêt maladie, sauf s'il s'agit d'un accident du travail.

Le script calcul combien de congés payés et jours de récupération la nounou a accumulé ce mois-ci.

## Reste à faire
**ATTENTION**:
Le script ne gère pas correctement les congés maladie dûs à un accident de travail. 
En effet, dans ce cas, les congés payés s'accumulent même sur le temps de congé maladie.