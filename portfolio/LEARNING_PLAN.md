# Plan for faglig eierskap

Målet er at du skal kunne forklare og endre prosjektet. Den første versjonen er et arbeidsgrunnlag; din egen kjøring, tolkning og videre analyse er den erfaringen du kan beskrive personlig.

## Første økt — forstå dataene

Les prosjektfortellingen og datakortet. Kjør notebooken. Velg én normal kjøring og én feilkjøring, og tegn temperatur og volumstrøm selv.

**Leveranse:** en kort egen forklaring på hvilke kolonner som er målinger, driftskontekst og fasit. Forklar hvorfor fasiten ikke er en inputvariabel.

## Andre økt — forstå modellen

Les features.py og models.py. Beregn en residual manuelt fra en rad i predictions.csv.gz. Finn terskelen i synthetic_summary.json og kontroller hva modellen skulle gjort ved dette tidspunktet.

**Leveranse:** et regneeksempel med måling, forventning, skalert avvik og terskel. Forklar hvorfor den største residualen ikke er en diagnose.

## Tredje økt — forstå evalueringen

Les alarms.py og evaluation.py. Gå gjennom en falsk alarm og en oppdaget hendelse. Finn første alarmstart etter feilstart og beregn forsinkelsen.

**Leveranse:** ett eksempel der sample-score og hendelsesmetrikken forteller forskjellige ting. Gjør rede for hva som skjer når en alarm allerede er aktiv.

## Fjerde økt — gjør én egen endring

Velg en begrenset hypotese. Et eksempel: «Et varighetskrav med et separat mål på normal alarmbelastning gir en bedre avveining ved moderat støy.»

Bruk en kopi av konfigurasjonen og et utviklingsfrø. Noter forventningen før forsøket. Bestem varianten før du kjører et nytt testfrø. Rapporter også dekning og hendelser som ikke blir oppdaget.

**Leveranse:** en ny rapport med konfigurasjon, frø, resultattabell og en vurdering av hva forsøket faktisk støtter. Lag en ekte Git-commit for arbeidet du gjør; ikke konstruer en tilbakedatert utviklingshistorikk.

## Femte økt — øv på formidling

Kjør femminuttersdemonstrasjonen for en medstudent. Be vedkommende peke på én uklarhet. Registrer dette som uformell tilbakemelding, ikke som en gjennomført kontrollert brukerstudie.

**Leveranse:** din egen forklaring av prosjektet og ett konkret forbedringsforslag.

## Prioritering før søknaden

Hvis tiden er knapp: forstå én modell, én datadeling og én negativ observasjon grundig. En presis beskrivelse av begrensningene er mer nyttig enn flere modellnavn. Søknadsfristen i annonsen er 15. november 2026.
