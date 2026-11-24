# Pocket Option — aprofundare tehnică, 5 noiembrie 2026

Statut: cercetare și specificație propusă; document suport, fără autoritate canonică nouă.

Continuă [raportul inițial](README.md). Cod analizat: `main` la `77641158d7abf16a23edcc9bbadd8ab24ab77015`. Constatările despre cod se referă la acest commit. Interfața și documentația au fost inspectate separat. Nu s-au executat ordine, activat boturi sau modificat parametrii strategiei.

## 1. Constatările noi care schimbă planul

| Constatare | Dovadă și limită | Consecință |
|---|---|---|
| Există export de tranzacții | Butonul „Export to XLS” a fost observat în istoricul real și demo; fișierul nu a putut fi descărcat din cauza unei erori de conexiune | Putem proiecta importul rezultatelor; formatul fizic și parserul rămân de verificat |
| Istoricul demo are retenție limitată | Pagina avertizează că îl șterge luni la 00:00 UTC+2, săptămânal | Dovezile trebuie arhivate înainte de ștergere; nu se presupune existența unui istoric perpetuu |
| Ordinul condiționat pe preț nu promite intrare exact la nivel | Ghidul autentificat spune că deschide la următorul tick după atingerea nivelului | Se înregistrează separat pragul cerut, momentul declanșării și intrarea acceptată |
| Indicatorii și viteza folosesc politici diferite pentru lumânări | Codul poate include lumânarea în formare în EMA/RSI/ATR; viteza selectează explicit lumânări M1 închise | Comparația numerică trebuie să declare ce lumânări erau închise și ce valori erau provizorii |
| Perioada numerică nu identifică formula indicatorului | RSI/ATR din cod folosesc medii simple; formula exactă a terminalului nu a fost stabilită | Avem nevoie de comparație pe aceleași intrări, fără modificarea arbitrară a strategiei |
| Un interval încheiat nu dovedește acoperirea lui completă cu tick-uri | La conectare în mijlocul intervalului, primul tick observat inițializează OHLC; ulterior intervalul este marcat încheiat | Introducem în contractul de cercetare dovada acoperirii, separat de indicatorul `complete` |
| Există durate de execuție fracționare în calcule | De exemplu, 3 minute × 0,95 = 171 secunde | Adaptorul trebuie să verifice granularitatea acceptată; rotunjirea schimbă ipoteza calibrată |

Aceste constatări nu demonstrează că o tranzacție ar fi fost câștigată cu alt indicator. Ele identifică diferențe măsurabile care pot invalida comparații aparent corecte.

## 2. Exportul istoricului: ce știm efectiv

Au fost inspectate paginile oficiale [istoric](https://pocketoption.com/en/cabinet/trading-history/) și [istoric demo](https://pocketoption.com/en/cabinet/demo-trading-history/). Pagina demo a fost selectată explicit; antetul general al site-ului poate arăta alt mod decât secțiunea de istoric. Identitatea sursei se stabilește din pagina și selectorul efectiv, nu doar din antet.

Coloanele observate sunt:

| Coloană în interfață | Câmp propus pentru import | Verificarea necesară |
|---|---|---|
| Order | `broker_order_ref_private` | Identificator opac, păstrat privat; deduplicare împreună cu sursa și modul |
| Expiration | `expiration_raw`, apoi `requested_duration_seconds` dacă semantica este confirmată | Se păstrează valoarea originală; nu se confundă cu ora finală |
| Asset | `broker_asset_display`, `otc_flag` | Se diferențiază simbolul obișnuit de varianta OTC |
| Open time | `broker_open_time_raw`, apoi UTC verificat | Fus orar, milisecunde și sensul timestamp-ului trebuie confirmate |
| Closing time | `broker_close_time_raw`, apoi UTC verificat | Nu se înlocuiește cu ora teoretică estimată de bot |
| Open price | `broker_entry_price` | Precizie zecimală și tipul cotației |
| Closing price | `broker_settlement_price` | Preț de decontare, separat de maximul/minimul din timpul tranzacției |
| Trade amount | `stake`, `currency` | Locale, separator zecimal, monedă și mod demo/real |
| Profit | `displayed_result_raw`, `payout_rate_raw` | Se verifică dacă valoarea include miza returnată; nu se presupune profit net |

Direcția BUY/SELL nu apărea drept coloană textuală separată în tabelul inspectat. Exportul sau detaliul ordinului trebuie verificat pentru a o recupera. Nu o deducem din sensul schimbării prețului: aceeași mișcare poate fi WIN pentru o direcție și LOSS pentru cealaltă.

**Starea exportului:** buton observat, solicitare efectuată numai în demo, descărcare nefinalizată. Browserul a primit `upstream connect error ... connection timeout`; nu a rezultat un fișier verificabil. Același tip de eroare a apărut la revenirea în terminal, inclusiv după o singură reîncărcare. Nu este dovadă că platforma este indisponibilă pentru toți utilizatorii sau că formatul XLS este defect. Nu a fost atribuită automat unei protecții anti-bot.

Nu au fost copiate în git tranzacții, identificatori, solduri sau date financiare individuale. Contractul de mai sus descrie structura, nu publică istoricul contului. Exportul de ordine oferă rezultate și câteva prețuri; nu oferă automat toate tick-urile sau toate lumânările dintre intrare și expirare.

### Importatorul propus

Prima versiune ar trebui să citească fișierul într-o zonă privată de analiză, să păstreze valorile brute și să producă un raport de validare înainte de orice asociere cu semnalele. Nu se presupune că extensia `.xls` garantează un anumit format intern. Se verifică semnătura fișierului și structura reală după prima descărcare reușită.

Cazuri obligatorii: fus orar necunoscut; direcție absentă; înregistrare duplicată; aceeași pereche cu și fără OTC; rezultat care include miza; monedă diferită; expirare modificată; timestamp final absent; rând incomplet. În aceste cazuri importatorul păstrează starea UNVERIFIED sau respinge asocierea, fără a inventa câmpurile lipsă.

Asocierea unui ordin cu un semnal cere identificator explicit sau dovadă suficientă și neambiguă despre sursă, instrument, direcție și intervalul de intrare. Vecinătatea temporală singură nu dovedește asocierea. Ordinele duplicate, copiate sau suprapuse nu devin observații independente.

## 3. Expirarea, declanșarea și modificarea ordinului

[Ghidul autentificat al ordinelor pe preț](https://pocketoption.com/en/cabinet/platform-guide/#placing-a-by-the-asset-price-trade-order) precizează declanșarea la următorul tick și condiții de payout minim și fonduri suficiente. Aceasta este descrierea produsului, nu un test de latență sau de preț executat. Nu a fost creat un ordin condiționat.

[Articolul oficial despre plasarea tranzacției](https://pocketoption.com/blog/en/knowledge-base/trading/how-to-place-a-trade-on-pocket-option/) descrie durate presetate și personalizate, precum și decontarea față de prețul intrării. Referința precisă de pornire a duratei la nivel de server și regulile de cuantizare nu au fost măsurate.

Există și o nuanță față de formularea simplificată „parametrii sunt blocați”: [ghidul Rollover](https://pocketoption.com/en/cabinet/platform-guide/#using-the-rollover-feature) descrie o prelungire condiționată a ordinului și creșterea sumei investite. Nu am activat funcția și nu o propun ca metodă de corectare a pierderilor. Pentru cercetare, ordinele modificate trebuie excluse din cohorta standard sau etichetate într-o cohortă distinctă.

Jurnalul trebuie să păstreze separat:

`requested_activation_time / requested_price → broker_accepted_at → broker_entry_price → broker_expiry_at → broker_settlement_price`.

Durata cerută, durata acceptată, timpul efectiv scurs și eventualele modificări sunt câmpuri diferite. Un semnal vechi nu devine valid prin alegerea unei durate mai mari.

## 4. Diferențe concrete ale indicatorilor și datelor

### Lumânare în formare și acoperire

În `send/core/market_model.py:296–324`, EMA, RSI și ATR preiau seriile furnizate, inclusiv cea mai nouă lumânare, dacă este încă în formare. În `:184–229` și `:388–392`, viteza folosește selecția explicită de lumânări M1 închise. Un RSI observat după închidere poate fi diferit de RSI folosit cu câteva secunde înainte, fără să existe o eroare aritmetică.

În `send/runtime/finnhub_market_data.py:307–338`, un bucket începe la primul tick primit. Dacă fluxul a pornit în mijlocul intervalului, porțiunea precedentă nu este cunoscută. Marcarea ulterioară `complete=True` indică încheierea intervalului, nu că au fost văzute toate prețurile lui. Există mecanism analog în `twelvedata_market_data.py:399–427`.

Pentru cercetare propunem câmpuri distincte: începutul bucket-ului, primul tick observat, momentul conectării, sursa completării istorice și starea acoperirii. Nu completăm golurile cu lumânări sintetice doar ca graficele să semene.

### Inițializarea EMA 200

EMA din cod pornește de la prima închidere disponibilă (`market_model.py:95–100`), iar fluxurile au o limită de 500 de lumânări. Pentru două EMA cu aceleași prețuri ulterioare, dar diferență inițială între semințe `Δ₀`, diferența rămasă este:

`Δ(N) = Δ₀ × (199/201)^(N−1)`.

| Număr total de lumânări | Influența rămasă din diferența inițială |
|---:|---:|
| 201 | 13,5333% |
| 206 | 12,8733% |
| 500 | 0,680538% |

Procentele sunt exemple matematice despre inițializare, **nu erori măsurate față de Pocket**. Diferența efectivă depinde de istoricul și semințele reale. Nu rezultă că 500 de lumânări garantează orice toleranță aleasă.

### RSI și ATR: demonstrație pe intrări identice

Au fost executate direct funcțiile existente `_rsi` și `_atr` și s-a comparat aritmetica cu recurența Wilder explicită, inițializată prin media primelor 14 valori. Nu s-a folosit un flux de piață și nu s-a modificat codul.

| Exemplu ipotetic | Formula din cod | Recurența Wilder explicită |
|---|---:|---:|
| RSI14: preț inițial 100, apoi 14 creșteri de o unitate și două scăderi de o unitate | 85,7142857143 | 86,2244897959 |
| ATR14: 14 valori True Range egale cu 1, apoi 14 și 1 | 1,9285714286 | 1,8622448980 |

Diferențele demonstrează că aceeași perioadă poate produce alte valori prin altă mediere. Nu identifică formula terminalului Pocket. Documentația [TradingView RSI](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/) folosește RMA în exemplul de calcul; [TradingView ATR](https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/) precizează RMA implicit și alte variante selectabile. Acestea sunt referințe de comparație, nu specificații Pocket.

Un caz limită suplimentar: `_rsi([1.1] * 15, 14)` întoarce 100 deoarece pierderea medie este zero, chiar dacă și câștigul este zero (`market_model.py:103–116`). Acesta este un comportament de documentat și evaluat față de contract; nu dovedește singur că motorul produce un BUY, deoarece celelalte filtre pot bloca. Alegerea 50 sau UNAVAILABLE ar necesita o decizie și o modificare specificată separat.

### Coerența surselor și timpului

| Aspect | Cod și observație | Cerință pentru viitorul adaptor |
|---|---|---|
| M1 și M5 sunt citite succesiv | `signal_engine.py:751–780` | Se înregistrează momentele ambelor citiri și o referință coerentă de evaluare, mai ales la granița lumânărilor |
| Unități diferite ale timestamp-urilor | Finnhub live presupune milisecunde; Twelve Data live presupune secunde | Conversie explicită și separarea timpului de deschidere de timpul de închidere al lumânării |
| Normalizarea nu dovedește proveniența | `core/candle_adapter.py:79–111` poate eticheta simbolul furnizat de apelant | Validarea identității și sursei trebuie făcută înainte de normalizare |
| Politici diferite pentru goluri mai vechi | Finnhub cere segment M5 contiguu; Twelve poate păstra goluri mai vechi în istoricul folosit de EMA | Se compară istoricul efectiv, fără a presupune aceeași acoperire doar din numărul de rânduri |

## 5. Precizia duratelor și rotunjirea

`send/core/time_model.py:166–187` folosește rotunjirea în sus la minut a timpului intern. Astfel, 3,01 minute devin 4 minute. Un caz de limită în virgulă mobilă precum `3.0000000000000004` devine tot 4. Comportamentul este verificabil; clasificarea lui drept defect depinde de toleranța cerută de contract, care nu este redefinită aici.

`send/core/execution_model.py:126–136` poate calcula `3 × (1 − 0,05) = 2,85 minute = 171 secunde`, dacă valoarea se află în intervalul calibrat. În reprezentare binară, expresia poate produce `170.99999999999997` secunde. Conversia prin simpla trunchiere ar putea transforma 171 în 170; rotunjirea la presetul de trei minute ar schimba orizontul în 180.

Adaptorul propus trebuie să distingă conversia numerică fără schimbarea duratei de cuantizarea la o durată diferită. Durata acceptată și regulile serverului rămân de verificat. Nu transferăm validarea unui orizont de 171 secunde către 170 sau 180 secunde.

## 6. Ce instrument construim primul și cum îl evaluăm

Recomandarea tehnică este **importatorul privat al rezultatelor și laboratorul de paritate**, înainte de adăugarea altor indicatori. Fără direcție, rezultat și timp verificabile, nu avem etichete suficiente pentru calibrarea Pocket.

După validarea datelor, primul experiment despre „blocaje” ar trebui să folosească o singură caracteristică: distanța până la cea mai apropiată zonă structurală deja confirmată, normalizată cu ATR din momentul deciziei. Reutilizăm coridorul existent.

Protocol propus:

1. Înghețăm nivelurile care erau cunoscute efectiv la momentul deciziei; un pivot confirmat cu lumânări ulterioare nu poate fi folosit retrospectiv mai devreme.
2. Păstrăm aceleași date, versiuni, treaptă de severitate și orizont pentru comparația de bază.
3. Înregistrăm separat atingerea zonei, atingerea bufferului înainte de orizont, direcția terminală și rezultatul brokerului când este cunoscut.
4. Stabilim toleranța zonei și împărțirea cronologică înainte de rezultate; păstrăm setul de evaluare separat.
5. Raportăm beneficiul suplimentar, incertitudinea, golurile și dependența dintre observații. Lipsa beneficiului este un rezultat valid.

Instrumentul descrie zone și comportamente observate. Nu demonstrează ordine ascunse, lichiditate instituțională sau momentul exact al următorului blocaj. Noile metrici nu înlocuiesc automat formulele canonice și nu activează praguri de producție.

## 7. Limitele accesului programatic

Au fost urmărite și articolele oficiale despre [Forex API](https://pocketoption.com/blog/en/knowledge-base/regulation-and-safety/forex-trading-api/) și [TradingView/Telegram/Excel](https://pocketoption.com/blog/en/news/data/automated-trading-integrating-bots-with-tradingview-telegram-and-excel/). Ele prezintă concepte și integrări generice; nu a fost identificat un contract de endpoint, autentificare, permisiuni read-only sau streaming pentru Quick Trading. Nu rezultă că un astfel de acces este imposibil; rămâne neconfirmat.

Ghidul oficial [Quick Trading versus MT Trading](https://pocketoption.com/blog/en/product-guides/forex-trading-on-pocket-option-quick-trading-vs-mt-trading/) distinge produse cu mecanisme diferite. Accesul MT5 nu dovedește acces la cotațiile ori rezultatele Quick/OTC. Ghidul [graficelor](https://pocketoption.com/blog/en/product-guides/how-to-read-pocket-option-charts/) arată și că Heikin Ashi folosește valori mediate; acestea nu trebuie folosite drept prețuri efective de intrare sau decontare.

Nu au fost instalate biblioteci neoficiale și nu au fost extrase sesiuni de autentificare pentru a improviza un API. Nu a fost găsită o procedură verificată de export al întregului flux de tick-uri sau OHLC. Confirmarea exportului tranzacțiilor nu rezolvă această lipsă.

## 8. Starea livrării

Raportul inițial, commit `1347bf0e628a3243bf2f0a9764348b69ef626f3f`, a trecut Repository CI, rularea `42123329603`. PR #241 era deschis și neintegrat la verificare. Această aprofundare are propriul commit și necesită verificarea lui separată; succesul anterior nu este transferat automat.

Exemplele numerice au fost verificate prin executarea funcțiilor pure existente și aritmetică independentă. Nu s-a reluat suita completă doar pentru cercetarea documentară. Nu se pretind integrare live, export finalizat, strategie recalibrată, modificări în producție sau profitabilitate.

Sursele publice și interfața autentificată au fost consultate la 5 noiembrie 2026. Paginile din cabinet pot necesita autentificare. Constatările din ghid sunt declarații ale produsului; exemplele numerice sunt ipotetice; constatările despre cod sunt legate de commit-ul fixat la început.
