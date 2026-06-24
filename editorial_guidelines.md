# Règles éditoriales — Revue de presse romande

Ce fichier définit ce qui entre dans la revue de presse et ce qui en est exclu.
Il est pensé pour être modifié par une personne non technique : pas besoin de
toucher au code. Le script lit les sections ci-dessous.

Quand un sujet est mal classé ou ne devrait pas figurer, ajoutez un mot-clé
d'exclusion ou un exemple ici, puis relancez le pipeline.

## Beats (cantons couverts)
- Vaud
- Genève
- Fribourg
- Valais

## Réglages
- max_par_canton: 4
- fenetre_heures: 24

## Sources prioritaires
Ces sources sont remontées en premier quand elles sont disponibles.
- RTS
- 24 Heures
- Tribune de Genève
- La Liberté
- Le Nouvelliste
- Le Temps
- Heidi.news
- Watson

## Exclure (mots-clés)
Tout titre contenant l'un de ces mots (insensible à la casse) est écarté.
- horoscope
- publireportage
- sponsorisé
- promo
- bon plan
- concours
- people
- télé-réalité
- pronostic
- loto

## Principes (pour la version IA, optionnelle)
- Priorité à l'intérêt rédactionnel cantonal : politique, économie locale,
  société, institutions, justice, environnement, culture régionale.
- Une phrase ou deux maximum par sujet, en français clair.
- Toujours conserver le lien vers la source.
- Pas de doublons : un même événement n'apparaît qu'une fois.
- En cas de doute sur le canton, classer là où l'événement se déroule.
