# Koblingen til medisinsk data science

Bruksområdet er industriell overvåking. Kompetansen som vises er data science, med flere metodiske problemer som også opptrer i medisinske datasett.

| Metodisk problem | Medisinsk eksempel | Implementasjon i AlarmLab |
|---|---|---|
| Korrelerte observasjoner | Flere målinger fra samme pasient | Hele simuleringskjøringer holdes i samme delsett |
| Relevant referansenivå | Normalverdi avhenger av pasient og situasjon | Forventet sensorverdi avhenger av last, pumpekommando og omgivelse |
| Ujevn datakvalitet | Manglende eller feilaktige målinger | Eksplisitte kontroller for mangler, verdigrenser og frosne sensorer |
| Kostnaden ved falske varsler | Gjentatte varsler kan belaste helsepersonell | Falske alarmstarter per normaltime og tid i alarm rapporteres |
| Varsling til riktig tid | En hendelse må kunne identifiseres når den oppstår | Ny alarm etter feilstart; forsinkelse rapporteres sammen med missede hendelser |
| Generalisering | Ny pasientgruppe, klinikk eller måleenhet | Separate stressforsøk med støy og endret driftskontekst |
| Menneskelig vurdering | Modellstøtte må vurderes i kontekst | Måling, referanse, kvalitetsstatus og begrunnelse vises samlet |
| Begrenset evidens | Små eller skjeve holdout-grupper | Antall hendelser, dekning og usikkerhetsintervaller er synlige |

## Hva dette lar deg demonstrere

Du kan forklare hvorfor tilfeldig splitting av tidssteg er en dårlig evaluering av nye kjøringer. Du kan vise en modell som lærer betinget forventning i stedet for å behandle alle sensorverdier likt. Du kan diskutere hvorfor en liten empirisk halerang ikke er en feilsannsynlighet.

Du får også et konkret eksempel på at evalueringen bestemmer hva vi tror modellen kan: en modell kan ha høye skårer gjennom en hel feilperiode, men likevel ikke gi en ny alarm når hendelsen starter. Forskjellen er relevant for alle beslutningssystemer som brukes over tid.

## Hva overføringen ikke betyr

Ingen pasientdata er brukt. Prosjektet estimerer ikke klinisk risiko, og industrimetrikkene gir ikke dokumentasjon på medisinsk nytte. En klinisk anvendelse ville kreve eget endepunkt, pasientbasert validering, relevant populasjon, måleprosess, klinisk vurdering og håndtering av persondata.

Dette er derfor et metodeprosjekt med et annet anvendelsesområde. Det er en ryddig måte å vise at utdanningen din kan bidra i en ny bransje uten å påstå kompetanse eller validering som prosjektet ikke dokumenterer.

## En presis formulering i intervju

«Bakgrunnen min er data science med medisinsk retning. I dette prosjektet har jeg arbeidet med problemstillinger som går igjen på tvers av anvendelser: tidsserier, korrelerte observasjoner, datakvalitet og falske alarmer. Industridomenet er nytt for meg, men jeg kan vise hvordan jeg undersøker en modell systematisk og hvordan jeg avgrenser konklusjonene.»

Bruk formuleringen etter at du har kjørt gjennom og forstått metoden. Legg til det du selv har endret og analysert.
