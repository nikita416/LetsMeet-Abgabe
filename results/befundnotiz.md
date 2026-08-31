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

