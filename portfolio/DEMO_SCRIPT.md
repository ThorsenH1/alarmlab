# Fem minutters demonstrasjon

Dette er et øvingsmanus. Vis de faktiske filene og bruk egne ord.

## 0:00–0:40 — Problemstillingen

«Jeg undersøker forskjellen mellom en høy avviksskår og et brukbart varsel om en ny hendelse. Bakgrunnen min i medisinsk data science gjorde spørsmål om datakvalitet, falske alarmer og validering naturlige å ta med.»

Vis første side i demoen. Forklar at dette er en generisk simulator, og at den separate fanen med ekte data bruker en hydraulisk testrigg.

## 0:40–1:40 — Modellen

Velg pumpesvekkelse, kjente driftsforhold og residualmodellen. Start fra begynnelsen og flytt tidslinjen til etter feilstart.

Vis målt og forventet volumstrøm. Forklar at forventningen er lært på normale kjøringer ut fra last, pumpekommando og omgivelse. Vis residualene, og presiser at de peker på avvikende signaler, ikke beviser årsaken.

Bytt til Isolation Forest. Forklar at alle tre detektorene kalibreres på egne normale kjøringer og vurderes på de samme testepisodene.

## 1:40–2:30 — Evalueringen

Åpne «Eksperimenter». Vis antall hendelser, falske alarmer per normaltime og forsinkelse.

«Et tilfeldig tidspunktssplitt ville gitt korrelerte datapunkter på begge sider. Jeg holder hele kjøringer adskilt. Jeg teller en ny alarm etter hendelsesstart, og viser forsinkelse sammen med oversette hendelser.»

Vis Wilson-intervallet rundt 24/24. Forklar hvorfor 24 observerte treff ikke betyr at sann recall er kjent til 100 %.

## 2:30–3:20 — Det som svikter

Bytt til tredoblet sensorstøy. Vis at residualmodellen kan være i alarm før feilstart.

«Dette er prosjektets viktigste negative resultat. En vedvarende alarm kan ha høy skår på feilpunktene uten å markere at noe nytt har skjedd. Derfor rapporterer jeg også tiden systemet står i alarm.»

Vis deretter manglende målinger. «Vurdering utilgjengelig» skal forklares som en begrensning i datagrunnlaget.

## 3:20–4:10 — Ekte data

Åpne «Ekte sensordata». Forklar at hver rad er en fullført 60-sekunders syklus med egenskaper fra ni fysiske sensorer.

«Jeg holder komplette driftskombinasjoner adskilt. Resultatene er perfekte på denne testen, men dataene kommer fra én rigg. Jeg kan derfor ikke påstå at modellen generaliserer til et nytt anlegg. Denne klassifikasjonen er også en annen oppgave enn simulatorens tidlige varsling.»

## 4:10–5:00 — Ditt bidrag og neste forsøk

Vis ett kodeavsnitt du faktisk kan forklare, for eksempel alarm_states eller event_table. Vis én test som verifiserer en metodisk egenskap.

Fortell deretter hva du selv har undersøkt etter den første KI-assisterte implementasjonen. Hvis du ikke har gjort en egen videre analyse ennå, si det. Presenter et konkret neste forsøk: ny alarm-logikk utviklet på egne utviklingskjøringer og vurdert på nye, urørte frø.

Avslutt med hvorfor dette interesserer deg i den aktuelle avdelingen. Ikke bruk prosjektet som dokumentasjon på erfaring fra IFE eller et virkelig kontrollrom.

## Spørsmål du bør kunne svare på

- Hvorfor kan tilfeldig splitting gi for gode resultater?
- Hva lærer Ridge-modellen, og hva er håndkonstruert?
- Hvorfor kan simulatoren favorisere residualmodellen?
- Hva er forskjellen på en empirisk halerang og en feilsannsynlighet?
- Hvorfor blir ny-hendelsesrecall null i støystesten?
- Hvorfor må forsinkelse leses sammen med recall?
- Hva utelates fra nevneren til falske alarmer per time?
- Hva betyr 0 % dekning?
- Hvorfor er de ekte dataene en separat benchmark?
- Hvilken dokumentasjon mangler før man kan si at grensesnittet hjelper mennesker?
