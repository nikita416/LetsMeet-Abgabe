# Befundnotiz – LetsMeet-Datenmigration

## 31.08.2026 – Erste Analyse der Excel-Quelle

### Was ist uns an der Quelle aufgefallen?

- Die Excel-Datei enthält 1576 Zeilen und 8 Spalten.
- Die E-Mail-Adresse ist bei allen 1576 Personen vorhanden.
- Alle E-Mail-Adressen sind eindeutig.
- In der Hobby-Spalte befinden sich bei 10 Personen keine Werte.
- Die übrigen untersuchten Spalten enthalten keine leeren Werte.
- Personenbezogene Angaben befinden sich teilweise als zusammengesetzte Werte in einzelnen Spalten, zum Beispiel `Nachname, Vorname` und `Straße Nr, PLZ Ort`.

### Was haben wir entschieden, und warum?

- Die Excel-Datei wird beim Profilieren zunächst vollständig als Text gelesen. Dadurch bleiben Telefonnummern, Postleitzahlen und Schreibweisen unverändert.
- Leere Hobby-Angaben werden nicht durch erfundene Werte ersetzt.
- Personen ohne Hobby-Angaben werden in Akt 1 trotzdem übernommen, weil Hobbys nicht Bestandteil des Datenvertrags V1 sind.
- E-Mail-Adressen werden als eindeutiges Merkmal der importierten Personen verwendet, weil alle Werte vorhanden und eindeutig sind.

### Welche Alternative wurde verworfen?

- Leere Hobby-Angaben könnten mit einem Platzhalter wie `unbekannt` gefüllt werden. Diese Alternative wurde verworfen, weil der Platzhalter nicht aus der Quelle stammt und dadurch falsche Daten entstehen würden.
- Telefonnummern und Postleitzahlen könnten als Zahlen eingelesen werden. Diese Alternative wurde verworfen, weil dabei führende Nullen und Formatierungszeichen verloren gehen könnten.

### Was haben wir nicht übernommen, und warum?

- Zum jetzigen Zeitpunkt wurde noch nichts nach PostgreSQL importiert. Die Quelle wird zunächst profiliert.
- Die Hobby-Daten werden in Akt 1 nicht in die Pflicht-View übernommen, weil sie nicht zum Datenvertrag V1 gehören.

### Datenschutz und Schutzbedarf

- Namen, Adressen, E-Mail-Adressen, Telefonnummern, Geburtsdaten, Geschlecht und Interessen sind personenbezogene Daten.
- Geburtsdatum, Geschlecht und Interessen benötigen einen erhöhten Schutz, weil sie persönliche Eigenschaften und Präferenzen betreffen.
- Die Daten dürfen nur innerhalb der vorgesehenen Schulumgebung verarbeitet werden.
- Die Daten sollen nicht öffentlich veröffentlicht oder an unbeteiligte Personen weitergegeben werden.
- Zugangsdaten und personenbezogene Daten sollen nicht zusätzlich in öffentliche Git-Repositories kopiert werden.


    ## 31.08.2026 – Analyse der zusammengesetzten Felder

### Was ist uns aufgefallen?

- Alle 1576 Namenswerte enthalten den vorgesehenen Trenner `Komma + genau ein Leerzeichen`.
- Bei 73 Namen entstehen nach der Trennung zusätzliche äußere Leerzeichen in Vor- oder Nachnamen.
- 1573 Adressen enthalten zwei Trennstellen.
- Drei Adressen enthalten eine zusätzliche Trennstelle, weil der Ortsname `Demmin, Hansestadt` ein Komma enthält.
- Alle 1576 Geburtsdaten entsprechen dem Format `TT.MM.JJJJ` und konnten als Datum gelesen werden.
- Nach der Transformation enthält der V1-Datensatz 1576 vollständige Zeilen.

### Was haben wir entschieden, und warum?

- Namen werden mit `split(", ", n=1)` in Nachname und Vorname getrennt.
- Adressen werden mit `split(", ", n=2)` in Straße, Postleitzahl und Ort getrennt.
- Der Ort enthält dadurch alles nach dem zweiten Komma. So bleibt `Demmin, Hansestadt` vollständig erhalten.
- Zusätzliche äußere Leerzeichen werden nicht mit `strip()` entfernt, weil Akt 1 die Inhalte der Quelle unverändert übernehmen soll.
- Geburtsdaten werden ausdrücklich mit dem Format `%d.%m.%Y` in Datumswerte umgewandelt.
- Postleitzahlen werden als Text gespeichert, damit führende Nullen nicht verloren gehen.

### Welche Alternative wurde verworfen?

- Eine Trennung der Adresse an jedem Komma wurde verworfen, weil dadurch Ortsnamen mit einem Komma in mehrere Teile zerlegt würden.
- Eine automatische Bereinigung mit `strip()` wurde verworfen, weil sie Quelldaten verändern würde.
- Eine automatische Erkennung des Datumsformats wurde verworfen. Das explizite Format ist nachvollziehbarer und verhindert eine Verwechslung von Tag und Monat.

### Was haben wir nicht übernommen, und warum?

- Die Straße und die Hausnummer werden in der Pflicht-View V1 nicht ausgegeben, weil sie nicht Bestandteil des Datenvertrags sind.
- Telefon, Geschlecht, Interessen und Hobbys werden in Akt 1 noch nicht in der Pflicht-View ausgegeben.

## 31.08.2026 – Abschluss Akt 1

### Ergebnis des reproduzierbaren Imports

- Die PostgreSQL-Struktur wurde nach dem Leeren der Datenbank vollständig aus den versionierten Skripten neu aufgebaut.
- Der Import hat 1576 Personen in die Tabelle `users_v1` geladen.
- Die Pflicht-View `migration_users` besitzt die vereinbarten sechs Spalten und Datentypen.
- Die eigenen Tests ergaben keine leeren E-Mail-Adressen, keine doppelten E-Mail-Adressen und keine unvollständigen Pflichtdatensätze.
- Der offizielle Prüfbefehl `letsmeet check V1` endete mit `GATE GRÜN`.
- Alle verglichenen Werte stimmen zeichengenau und ungetrimmt mit der Quelle überein.
- 15 Postleitzahlen mit führender Null wurden unverändert übernommen.
- 58 Personen besitzen laut Quelle eine vierstellige Postleitzahl. Diese Werte wurden ebenfalls unverändert übernommen.

### Grenzen des Imports

- Akt 1 übernimmt nur die Felder des Datenvertrags V1.
- Telefonnummern, Geschlecht, Interessen und Hobbys befinden sich noch nicht im Zielmodell.
- Zehn Personen besitzen in der Excel-Quelle keine Hobby-Angaben.
- Der Import prüft die technische Struktur und die vereinbarten Transformationsregeln, bewertet aber noch nicht die fachliche Richtigkeit aller personenbezogenen Angaben.

## 31.08.2026 – Analyse von Interessen und Hobbys

### Interessen

- In der Excel-Quelle kommen die Werte `m`, `w` und `mw` vor.
- `mw` wird als zwei einzelne Interessencodes `m` und `w` interpretiert.
- Dadurch entstehen 1609 Zuordnungen zwischen Personen und Interessencodes.
- Es gibt keine doppelten Kombinationen aus E-Mail-Adresse und Interessencode.
- Die Codes werden unverändert gespeichert und nicht in Bezeichnungen übersetzt.
- Für die Interessencodes wird gemäß Datenvertrag keine eigene Übersetzungstabelle angelegt.

### Hobbys

- Aus der Excel-Quelle wurden 4828 Hobbyzuordnungen ermittelt.
- Insgesamt kommen 220 unterschiedliche Hobbybezeichnungen vor.
- Alle Hobbyangaben konnten nach dem Muster `Bezeichnung %Priorität%` gelesen werden.
- Es wurden keine doppelten Kombinationen aus E-Mail-Adresse, Hobby und Quelle gefunden.
- Zehn Personen besitzen keine Hobbyangaben.
- Die aktuelle Lieferung enthält Prioritäten von 0 bis 100.
- Das Zielmodell erlaubt trotzdem den fachlich vereinbarten Bereich von -100 bis 100.
- Für Akt 2 wird bei jeder Hobbyzuordnung `source = 'excel'` gespeichert.

## 31.08.2026 – Kundinnenentscheidung zu Quellenkonflikten

- Die Kundinnenentscheidung wurde bei der Lehrkraft eingeholt.
- Bei widersprüchlichen Namen und Telefonnummern hat MongoDB Vorrang.
- Die E-Mail-Schreibweise wird gemäß Datenvertrag weiterhin aus Excel übernommen.
- Die Zuordnung der Profile erfolgt ohne Beachtung der Groß- und Kleinschreibung.
- Namen aus MongoDB werden nach derselben Regel wie in Akt 1 mit `Komma + genau ein Leerzeichen` getrennt.
- Nicht widersprüchliche Excel-Felder wie Geburtsdatum, Postleitzahl, Ort, Geschlecht, Interessen und Hobbys bleiben aus der Excel-Quelle erhalten.

## 31.08.2026 – Abschluss Akt 2

### Ergebnis

- Der gemeinsame Neuaufbau aus Excel und MongoDB wurde nach dem Leeren der PostgreSQL-Datenbank erfolgreich ausgeführt.
- Der offizielle Prüfbefehl `letsmeet check V2` endete mit `GATE GRÜN`.
- Alle fünf Vertrags-Views besitzen die geforderten Spalten und Datentypen.
- 1576 Personen wurden vollständig übernommen.
- 1609 Interessenangaben wurden übernommen; Mehrfachangaben wurden in einzelne Zeilen aufgelöst.
- 4828 Hobbyzuordnungen wurden einschließlich Prioritäten und Quelle übernommen.
- 500 gerichtete Likes wurden mit Status und Zeitpunkt übernommen.
- 300 gerichtete Nachrichten wurden mit Absender, Empfänger, Zeitpunkt und Conversation-ID übernommen.
- Bei Quellenkonflikten wurde gemäß Kundinnenentscheidung MongoDB priorisiert.
- Die Schreibweise der E-Mail-Adresse stammt weiterhin aus Excel.

### Weitere Befunde

- Es gibt 50 verschiedene `conversation_id`.
- 48 Conversation-IDs kommen bei mehr als einem Teilnehmerpaar vor.
- Die Conversation-ID kann deshalb nicht ohne weitere fachliche Klärung als eindeutiger Schlüssel eines Teilnehmerpaares interpretiert werden.
- Für `birgit.voss@gmaiil.ork` enthält MongoDB den Telefonwert `0`.
- Dieser Wert besitzt keinen erkennbaren Informationsgehalt, wurde aber gemäß Kundinnenentscheidung und ohne stillschweigende Korrektur übernommen.
## 14.09.2026 – Abschluss Akt 3

### XML-Basislieferung

- Die Datei `Lets_Meet_Hobbies.xml` enthält 100 Personen und 300 Hobbyzuordnungen.
- Alle in der XML-Datei genannten Personen konnten den vorhandenen Personen anhand der E-Mail-Adresse zugeordnet werden.
- Zwischen den 300 XML-Hobbyzuordnungen und den Excel-Hobbyzuordnungen bestanden keine fachlichen Duplikate.
- Alle 300 Zuordnungen wurden mit `source = 'xml'` und `priority = NULL` übernommen.
- Nach dem Basisimport bestanden insgesamt 5128 Hobbyzuordnungen.

### Änderungspaket

- Das unveränderte Archiv `letsmeet-transfer-v3.zip` wurde mit SHA-256 geprüft.
- Die Prüfsumme stimmt mit dem vorgegebenen Wert `5370a041066db2c8d76bba1ab95e79b33be984a2d92d73b5ad409a02d8bd1385` überein.
- Das Änderungspaket enthält acht physische Datensätze.
- Eine zusätzliche gültige Hobbyzuordnung wurde übernommen.
- Das Profil `transfer.mojibake@letsmeet.invalid` wurde nach nachvollziehbarer Korrektur des Mojibake-Textes übernommen. Dabei wurde `MÃ¼ller` zu `Müller` korrigiert.
- Das Profil `transfer.p2@letsmeet.invalid` wurde wegen des nicht zulässigen wörtlichen Fehlwerts `unbekannt` im Feld `city` abgelehnt.
- Ein Like mit unbekannter Zielperson wurde abgelehnt.
- Eine bereits vorhandene Hobbyzuordnung wurde nicht dupliziert und als Ablehnung dokumentiert.
- Eine Hobbyzuordnung mit der Priorität 101 wurde wegen Überschreitung des vereinbarten Wertebereichs von -100 bis 100 abgelehnt.
- Eine doppelte Hobbyzuordnung innerhalb des Änderungspakets wurde einmal übernommen und einmal als Duplikat abgelehnt.
- Das Profil aus `encoding-invalid.xml` wurde abgelehnt, weil die Datei entgegen ihrer UTF-8-Deklaration nicht als gültiges UTF-8 gelesen werden kann.
- Insgesamt wurden sechs Ablehnungen eindeutig über `source` und `source_ref` dokumentiert.

### Abnahme und Idempotenz

- Nach dem Änderungspaket enthält der Bestand 1577 Personen, 1609 Interessen, 5129 Hobbyzuordnungen, 500 Likes und 300 Nachrichten.
- Alle sechs Vertrags-Views entsprechen dem Datenvertrag V3.
- Nach dem ersten Import wurde ein offizieller Vergleichszustand gespeichert.
- Derselbe Import des Änderungspakets wurde anschließend ein zweites Mal ausgeführt.
- Alle sechs Vertrags-Views blieben nach dem zweiten Import mengen- und wertgleich.
- Der offizielle Snapshotvergleich endete mit `GATE GRÜN`.

## ERD-Modell – Freigabe-URL

- Freigabe-URL des ERD-Modells: https://station.heidelab.de/letsmeet-erd/#d=2.7Vfdrts2DH4XX2cCKZGilLvtYlgxDCjW3W1F4CTKiVHHObCdYj0HeZu-SV9skH8SOz8nadEWG7A7WxL58ftESeRzku5WD-k8vFom0yQPdbUJoU4myWa7DHmeTJ-TUNRZnYY6FMn0z-ekSDchmSavQ1lti2SSpHVdZvNdHYazYZNmeTJJsqp-s1jnu1BVIU-mdbkL-8lh1Sorq3rW_AxG8_TC4Dwr6_Vsmdaj0aouY7SDkcdtVaf5bLFdjhYusvrDaNl6W4wWPIRiGcpk_3Yw9st2Pv9wjeE6TrZhXqY59PR6va231zw9xslZtrwpV2SfnQrzWG5XWT7P8uU4-N9CVaUP4Rropp2-B3axLd6HskrrbFvE9cNd2S5HslahqGdpPY7kVVGHMrq-FkvWLqjbXbum5ttJMg9PWVjviocuFdNhHs4HO9bvURoz-V1aLn9MpknRff8U6V_djDLblifJUm135SJ0pG5hVrvF-gtQP31chTIUT0OULmnmQ8TeFZ5A9BsSqqx-ak_EWaSHn8PiVRl2xTJcj_dlP9c49gc5exeW1yhXdVrvqtG5j8uP2ZOOkvhzRKhCw-mGk8NN9bj69LF4qK_67f0M8_iSpy6NqyyU9SwdxjnUatPQi_dUFg9UzOTn3tX0Ofk7mSKwYrAi7JwhI4iT5EMy1WgUey_eGiHQVvaTLvdaM2atwHntDCGQA99YodbKG-2MBw3M3tJ-0mVWa_YDWqvIAGsREu-FbWNIhhQyE3omMpqM2U-Sv3YAAPPw1H40frrPhkE_3yRh-wMHHFSM1gCgOLIWmO7HGTgfA_UJPMYyAgqsIdCarEAHBBiBNIAX8h6E7wdqUnOMQQKKwYkDR6SFTANirCgj1qEjtCIuYvT51-2ut8qS0dp5z0C-tbOoFVtNbMAKktXnsXVuzoNr030cHYNyxlPcdGeNNq7VgMUoQdFiHbHXxn4GzOGgnCAhKYtsmdBoRtdmD5NR5IWs82S45XM8P52lR0XiLGhyZFi7xvIHQUXA5NCTAYdyQYqDp_MoTw7hyZ6RKPJGQAsJeWPlbsghRnPqOu3jbT8GEbTKaAajLYLW_trp3U-SarEOmzTaHautOp2HPO8euCwWZQGOd8zhzlmH8t2uWNVxvqvPkklSPab5SZ02qMRe__qfqcBa4ngk3r-yd_M-rc8O5Af-9UDY7rG92_-4arsg7c1qbXJtj1ZpXoXm7-fO7SQpw-qPNjNeHXKiDKs3TWADF_GZ-T2sBo_Ym5Cv2ndswNwcmR-fx7u5nxaPF9h_SdE4GlqGcjbQ5esqcUQqwyJk778l1kB1Oqo-LCbu1v1CoXwhrQs4rYAHAEXY3X1PfFPhr53PG6B4Ajpycx_yzRK_VRHPa_r_dRzreNK0tLrplyrif6OCL5yqG7h0gnvq6b5roTBXWrJ7xHpsCoJZOvveqnXA8-8EPJCLzjvMe5SKa8uvHO0hvnHwZ03t90Z9ubk-7z9DX7xai8qSIHvDGrRua1eyip3T4oyIsMQWMuChWzWitABbtLHX8rpr67xyiOI8ovdELtro3sZ6ZQFAs2NAZ6Qt_UF5QnQAFpxHJop1eDC9EWllrXcsmjwTUGtkHCkkRHZoAQib4OjYSpMiDQYESaPV3BJip5i9cRzxxHPsOQsYMbKakZiJjbQVvGhR3ntvPViHHFunohfBGlDIxolBBrTcNnVeo9IGhIEYRGOkU_QaeEfKaNRgnffiuj4Q4pKesUFWINaj89aJE9O2K86ZZlgAtAAZjDY9Y-iQRYGQF4c2djW43-_3_wA