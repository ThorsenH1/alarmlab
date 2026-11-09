# Fra problem til et etterprøvbart prosjekt

## Utgangspunktet

Oppgaven var å lage et porteføljeprosjekt som viser relevant erfaring for en sommerstilling ved IFE i Halden, med data science og medisinsk data science som faglig bakgrunn. IFEs offentlige beskrivelser peker mot tilstandsovervåking, anvendt KI og samspillet mellom mennesker og tekniske systemer.

Et naturlig prosjekt kunne stoppet ved å klassifisere feil i sensordata. Her ble problemstillingen avgrenset til noe mer operativt: Når gir en modell faktisk et brukbart varsel om en ny hendelse?

Det valget påvirker hele løsningen. Dataene må inneholde tidsforløp. Evalueringen må måle hendelser og normal driftstid. Grensesnittet må kunne vise at modellen avstår fra vurdering. Forklaringen må beskrive observerte avvik uten å fremstille dem som en sikker diagnose.

## Forskningsspørsmålene

**RQ1:** Kan driftskontekst redusere falske alarmer og oppdage flere simulerte avvik enn ukondisjonerte sensorgrenser og Isolation Forest?

**RQ2:** Hvordan endres dette når sensorstøyen eller driftskonteksten avviker fra treningsgrunnlaget?

**RQ3:** Kan en separat klassifikasjonspipeline håndtere ekte multivariate sensormålinger med en eksplisitt gruppedeling?

**RQ4:** Hvordan bør en operatør få se datakvalitet, modellgrunnlag og alarmhistorikk? Implementasjonen gir et grensesnitt og en studieprotokoll. Effekten på mennesker er foreløpig et åpent spørsmål.

## Hvorfor to datagrunnlag

En simulator gir kontroll over feilstart, alvorlighetsgrad, normal drift og måleproblemer. Dette gjør det mulig å beregne varslingsforsinkelse og undersøke spesifikke feilmoduser.

En simulator kan også favorisere en modell som bygger på lignende antakelser. Derfor inneholder prosjektet et separat eksperiment med målte data fra en hydraulisk rigg. Dette viser en reell feature- og klassifikasjonspipeline, men det validerer ikke simulatorens detektor. De to forsøkene har ulike målvariabler og ulike tidsmessige forutsetninger.

## Fra signal til varsel

Første trinn er en enkel referanse: hvor langt ligger en sensorverdi fra normal median? Den svarer på om en verdi er uvanlig i treningsmaterialet, men forstår ikke at en høyere last kan gjøre en høyere temperatur normal.

Isolation Forest tar flere signaler og driftskontekst samtidig. Den gir en ikke-lineær referanse som krever få antakelser om normalfordeling.

Residualmodellen lærer forventede sensorverdier gitt kjente driftsvariabler. Differansen mellom målt og forventet verdi kan vises direkte. Alarmens terskel fastsettes deretter på egne normale kjøringer. Ingen feil fra testsettet brukes til å velge terskelen.

En datakontroll kommer før vurderingen. Et manglende signal eller en ukjent driftskontekst skal kunne gi «vurdering utilgjengelig». Det er en egen tilstand, med egen betydning for modellens dekning.

## Hvorfor alarmen er en egen modellkomponent

En enkelt overskridelse kan være støy. Tre sammenhengende overskridelser gir her en alarm, og fem lave skårer avslutter den. Dette er et demonstrasjonsvalg, ikke en industriell standard.

Tidslogikken kan redusere korte varselutbrudd, men kan samtidig holde en alarm aktiv. Derfor må både antall alarmstarter og tiden i alarm rapporteres. Det er dette som gjør prosjektets vinkling konkret: statistisk avvik, alarmtilstand og nyoppdaget hendelse er tre forskjellige størrelser.

## Hva de første resultatene viste

I hovedtesten oppdaget residualmodellen 24 av 24 innførte avvik, med én falsk alarmstart over omtrent 10,29 overvåkede normaltimer. Sensorgrenser og Isolation Forest oppdaget begge 11 av 24. Det støtter RQ1 innenfor denne simulatoren og disse valgene.

Stresstesten endret bildet. Ved tredoblet sensorstøy oppstod alarmene før feilstart og kunne forbli aktive. Med kravet om en ny alarm etter feilstart ble ingen av de tolv hendelsene regnet som oppdaget. Det er en faktisk feilmodus i kombinasjonen av modell og alarmtilstand.

Resultatet er beholdt. Hvis tidslogikken senere endres for å løse dette, er de nåværende stresstestene utviklingsdata. En ny vurdering av generalisering må bruke nye, uavhengige kjøringer.

## Hva de ekte dataene viste

Kjølertilstand ble skilt perfekt av begge lærte klassifikatorer på den valgte gruppedelingen. En utforskende pumpelekkasjeoppgave ble lagt til etter dette funnet; også den viste seg å være lett på den samme riggen. Begge resultatene er rapportert uten å lete videre etter en mer imponerende eller mer dramatisk skår.

Dette sier noe om dataenes separerbarhet, ikke at en fremtidig industrimodell har 100 % treffsikkerhet. Nye anlegg, andre måleøkter og tidsmessige endringer er ikke representert som uavhengige holdout-enheter.

## Den ferdige demonstrasjonen

Grensesnittet spiller av lagrede modellprediksjoner. Tidslinjen viser bare signaler frem til valgt tidspunkt. Fasiten kan slås på for læring. Den inngår ikke i modellens vurdering.

En person kan loggføre sin observasjon sammen med tidspunkt, modellstatus og datasettets fingeravtrykk. Dette er nødvendig infrastruktur for en senere pilot, men slike logger er ikke i seg selv dokumentasjon på forbedret situasjonsforståelse.

## Prosjektets bidrag og avgrensning

Bidraget er kombinasjonen av kausal signalbehandling, eksplisitte datagrenser, hendelsesbasert evaluering, dokumenterte negative resultater og en menneskelig vurderingsflate. Dette er særpreget ved prosjektet; metodene er etablerte, og det hevdes ikke at algoritmen er en ny forskningsoppfinnelse.

Den første implementasjonen og denne dokumentasjonen er utarbeidet med KI-assistanse. Fortellingen beskriver faktiske prosjektvalg og observerte resultater. Den er ikke en oppdiktet personlig arbeidsdagbok eller dokumentasjon på brukerintervjuer som ikke er gjort.
