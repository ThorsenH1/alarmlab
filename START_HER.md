# Start her

AlarmLab er et komplett forskningsprosjekt i anvendt maskinlæring, laget for å koble bakgrunnen din i medisinsk data science til IFEs arbeid i Halden.

Den røde tråden er enkel: **Det holder ikke at en modell oppdager unormale datapunkter. Varslet må komme på riktig tidspunkt, være forståelig og bygge på brukbare data.**

## Først: åpne og prøv

1. Åpne [demo/index.html](demo/index.html). Alt ligger i HTML-filen.
2. Velg pumpesvekkelse og residualmodellen. Flytt tidslinjen bakover og fremover.
3. Bytt til Isolation Forest. Samme signal, annen vurdering.
4. Velg tredoblet sensorstøy. Se hvorfor et system kan være i alarm lenge uten å markere en ny hendelse.
5. Velg manglende målinger. Systemet viser at vurderingen er utilgjengelig.
6. Åpne «Eksperimenter» og «Ekte sensordata». Tallene kommer fra kjørte Python-eksperimenter.

## Hva du får

| Del | Innhold |
|---|---|
| Python-pakke | Simulator, datakontroller, modeller, alarmtilstander, evaluering, ekte-data-benchmark og rapportbygging |
| Data | Reproduserbare syntetiske tidsserier og avledede egenskaper fra et åpent, målt hydraulikkdatasett |
| Resultater | Faktiske prediksjoner, hendelsestabeller, metrikker, figurer og SHA-256-manifest |
| Demo | Lokal, interaktiv avspilling med modellvalg, forklaringer og øvelseslogg |
| Dokumentasjon | Metode, datakort, modellkort, arkitektur, valg og begrunnelser, svakheter og foreslått brukerstudie |
| Formidling | Presentasjonsmanus, søknadsnotater og en plan for å gjøre arbeidet til din egen faglige erfaring |

## Faglig nivå og kobling til utdanningen din

Du viser ferdigheter innen tidsserier, feature engineering, regresjon, unsupervised anomaly detection, supervised learning, evalueringsdesign, usikkerhet og visualisering.

Likheten med medisinsk data science ligger i problemene: korrelerte målinger, datalekkasje mellom samme pasient eller kjøring, falske varsler, endrede måleforhold og behovet for menneskelig vurdering. En industrimodell er ikke klinisk validert, men arbeidet demonstrerer overførbar metodekompetanse.

## Hva som er ferdig – og hva som fortsatt er forskning

Programmet, demoen og standardeksperimentene er implementert og kjørt. Enhetstester og nettleserkontroller ligger ved som verifikasjon. CI-oppsettet er laget for å kjøre samme kode på GitHub; fjernkjøringen er foreløpig ikke gjennomført.

Det er ikke gjennomført en brukerstudie, innsamlet IFE-data eller testet på et virkelig kontrollrom. Simulatoren beskriver en enkel kjølekrets, ikke et kjernekraftverk. Dokumentene skiller mellom gjennomført arbeid og foreslåtte videre undersøkelser.

## Slik får du faglig eierskap

Les først prosjektfortellingen og metodekapittelet. Kjør deretter programmet selv. Velg én begrunnet endring, for eksempel alarmens tidslogikk, og undersøk den på nye tilfeldige frø. Skriv hva du forventet, hva du observerte og hva endringen ikke løste. Da får du et konkret bidrag du kan vise og forklare.

Den første versjonen er laget med omfattende KI-assistanse. I en søknad bør du beskrive din egen forståelse og dine faktiske bidrag presist. Et godt intervju handler mer om å forklare datadeling og en svakhet enn om å kunne vise et perfekt skjermbilde.

## Anbefalt leserekkefølge

1. [Prosjektfortelling](docs/PROJECT_STORY.md)
2. [Medisinsk data science](docs/MEDICAL_DATA_SCIENCE.md)
3. [Metode](docs/METHODS.md)
4. [Kjørte resultater](artifacts/RESULTS.md)
5. [Arkitektur og programgjennomgang](docs/ARCHITECTURE.md)
6. [Fem minutters demonstrasjon](portfolio/DEMO_SCRIPT.md)

Annonsen oppgir søknadsfrist **15. november 2026** og ber om ønsket avdeling, CV, vitnemål, karakterutskrift og personlig søknadsbrev. Den direkte faglige prioriteringen for dette prosjektet er ADS. Se [annonsen](https://www.finn.no/job/ad/478074499).
