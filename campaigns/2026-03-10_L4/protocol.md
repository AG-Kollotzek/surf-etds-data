# Messprotokoll 2026-03-10_L4

Transcription of the measurement protocol of this campaign (PDF, 15 pages), with role codes
instead of names. Wording, values and typing errors as in the original (German). Not
transcribed: page numbers and one organisational to-do. The original is kept by the lab.

<!-- transcription -->

## Messprotokoll: Versuchsreihe 10.03.2026

QMP1, Student2, Student4

### Allgemeine Informationen

- Datum: 10.03.2026
- Aufbau: 15:18
- Abbau: 19:49
- Umgebungstemperatur: Konstant bei ca. 23.1 °C (sofern nicht anders angegeben)
- ExacTrac als Vorbereitung: Lateral: -0.3, Longitudinal: -0.4, Vertikal: 0.1) → Werte entsprechen nicht den Erwartung (siehe Werte bei Messungen) → Hypothese: Phantom war wahrscheinlich nicht perfekt auf home
- Testdurchlauf: Am Anfang und Ende jeder Messreihe wurde ein "Wobbeln"durchgeführt
- Statistik: Jede Messung wurde im Regelfall dreimal durchgeführt

### Messprotokolle 1 - 3: Standardmessung

Ziel: Standardmessung
Name: ETD_QA_PoP_SingleCouchRotation.json
Konfiguration: Hitzepads aus

**Messung 1**
Start Messung: 16:01
Ende Messung: 16:08
ExacTrac Zeit: 16:04 - 16:06
ExacTrac Datensatz: 160617
CSV: 160448.png
Zweiter ExacTrac (zur Kontrolle):
Zeit: 16:07 - 16:07
Werte: Lateral: 0.2, Longitudinal: -0.4, Vertikal: 0.2

**Messung 2**
Start Messung: 16:09
Ende Messung: 16:12
ExacTrac Zeit: 16:10 - 16:11
Werte: Lateral: 0.1, Longitudinal: -0.3, Vertikal: 0.2
ExacTrac Datensatz: 161117
CSV: 160950.png

**Messung 3**
Start Messung: 16:12
Ende Messung: 16:15
ExacTrac Zeit: 16:13 - 16:14
ExacTrac Datensatz: 161416
CSV: 161302.png
Werte: Lateral: 0.2, Longitudinal: -0.4, Vertikal: 0.2

### Messprotokolle 4 - 6: Longitudinal

Ziel: 5 mal longitudinal ±10mm (2 Sekunden Pause bei 0 vor neuen Durchlauf)
Name: ETD_QA_PoP_SingleCouchRotation_OnlyH.json
Konfiguration: Hitzepads aus

**Messung 4**
Start Messung: 16:16
Ende Messung: 16:18
ExacTrac Zeit: 16:15 - 16:17
ExacTrac Werte: Lateral: 0.2, Longitudinal: -0.4, Vertikal: 0.2
ExacTrac Datensatz: 161724
CSV: 161538.png

**Messung 5**
Start Messung: 16:19
Ende Messung: 16:21
Werte: stabil
ExacTrac Datensatz: 162054
CSV: 161859.png

**Messung 6**
Start Messung: 16:21
Ende Messung: 16:23
ExacTrac Datensatz: 162326
CSV: 162130.png

### Messprotokolle 7 - 9: Vertikal

Ziel: 5 mal vertikal ±10mm
Name: ETD_QA_PoP_SingleCouchRotation_OnlyV.json
Konfiguration: Hitzepads aus

**Messung 7**
Start Messung: 16:24
Ende Messung: 16:27
ExacTrac Zeit: 16:25 - 16:26
ExacTrac Datensatz: 162647
CSV: 162451.png

**Messung 8**
Start Messung: 16:27
Ende Messung: 16:29
ExacTrac Zeit: 16:27 - 16:29
ExacTrac Datensatz: 162922
CSV: 162728

**Messung 9**
Start Messung: 16:29
Ende Messung: 16:32
ExacTrac Zeit: 16:29 - 16:32
ExacTrac Datensatz: 163157
CSV: 162951
Zweiter ExacTrac (zur Kontrolle):
Zeit: 16:32 - 16:32
Werte: Lateral: 0.2, Longitudinal: -0.3, Vertikal: 0.2

### Messprotokolle 10 - 12: Rotation

Ziel: Rotation ±5 Grad, 5 Wiederholungen
Name: ETD_QA_PoP_SingleCouchRotation_OnlyR.json
Konfiguration: Hitzepads aus

**Messung 10**
Start Messung: 16:33
Ende Messung: 16:35
ExacTrac Datensatz: 163508
CSV: 163325.png
Notiz: Problem bei Brainlab gefunden. Backlash korrigiert, Offset dennoch vorhanden, von einer Rotation zur anderen: 5 ° vs. 4.7 ° , für folgende Messungen gleiche tracking area verwendet und nicht neu eingezeichnet

**Messung 11**
Start Messung: 16:36
Ende Messung: 16:38
ExacTrac Zeit: 16:36 - 16:37
ExacTrac Datensatz: 163758
CSV: 163613.png

**Messung 12**
Start Messung: 16:38
Ende Messung: 16:41
ExacTrac Zeit: 16:38 - 16:40
ExacTrac Datensatz: 164007
CSV: 163820.png

### Messprotokoll 13: Extrempositionen

Start Messung: 17:16
Ende Messung: 17:33
Ziel: Überprüfung von Extrempositionen mit ExacTrac, hd5 geloggt
Konfiguration: Hitzepads aus, Start von Nullposition
ExacTrac Werte: Lateral: 0.2, Longitudinal: -0.3, Vertikal: 0.2
CSV: 172148

| Longitudinal (h) | |
|---|---|
| 0 | → 0.2, -0.3, 0.2 |
| +10 | → 0.3, -10.3, 0.2 |
| 0 | → 0.2, -0.3, 0.2 |

| Vertikal (v) | |
|---|---|
| 0 | → 0.2, -0.3, 0.2 |
| +10 | → 0.7, -14.3, -0.2 |
| -10 | → -0.4, 14.1, -0.3 |
| 0 | → 0.2, -0.3, 0.2 |

| Rotation (r) | |
|---|---|
| 0 | → 0.2, -0.3, 0.2 |
| +5 | → 0.1, -0.4, 0.2 |
| -5 | → 0.2, -0.2, 0.2 |
| 0 | → 0.2, -0.3, 0.2 |
| +30 | → -0.2, -0.7, 0.2 |
| -30 | → 0.6, -0.1, 0.2 |
| +45 | → -0.3, -1.1, 0.2 |
| +90 | → -0.1,-1.8,0.2 |
| +60 | → -0.3, -1.4, 0.2 |
| 0 | → 0.1, -0.3, 0.2 |

### Messprotokolle 14 - 19: Variable Geschwindigkeit

Ziel: Untersuchung Rotationsgeschwindigkeit (±5 Grad)
Name: ETD_QA_PoP_SingleCouchRotation_RvarySpeed.json
Konfiguration: Hitzepads aus, von langsam zu schnell, blueprint ähnlich wie only rotation nur mit unterschiedlicher Geschwindigkei, finden Geschwindigkeiten in json/ExacTrac Datei

**Messung 14**
Start Messung: 17:34
Ende Messung: 17:40
ExacTrac Zeit: 17:36 - 17:39
ExacTrac Datensatz: 173928
CSV: 173645

**Messung 15**
Start Messung: 17:40
Ende Messung: 17:44
ExacTrac Zeit: 17:40 - 17:43
ExacTrac Datensatz: 174334
CSV: 174056

**Messung 16**
Start Messung: 17:46
Ende Messung: 17:48
ExacTrac Zeit: 17:46 - 17:48
ExacTrac Datensatz: 174832
CSV: 174558

**Messung 17**
Notiz: enger gezeichnet, Phantom ähnlicher
Start Messung: 17:49
Ende Messung: 17:53
ExacTrac Datensatz: 175259
CSV: 175019

**Messung 18**
Notiz: noch enger gezeichnet, Phantom ähnlicher, Viereck, Stirn/Nase vom Phantomkopf
Start Messung: 17:54
Ende Messung: 17:57
ExacTrac Datensatz: 175635
CSV: 175356

**Messung 19**
Notiz: maximal ausgemalt, aber nicht über Phantom hinaus
Start Messung: 18:01
Ende Messung: 18:05
ExacTrac Datensatz: 180108
CSV: 175824

### Messprotokoll 20: Mapping Rotation/Yaw

Ziel: Mapping Phantombewegung vs. Scan in 1 ° Schritten, Überprüfung ab wann Werte ungenau
Konfiguration: Heating Pads aus
Start Messung: 18:07
Ende Messung: 18:14
ExacTrac Datensatz: 181427

| Soll (°) | Ist (Phantom) |
|---|---|
| 0 | 0 |
| 1 | -1.0 |
| 2 | -2.0 |
| 2.5 | -2.4 |
| 3 | -2.9 |
| 3.5 | -3.4 |
| 4 | -3.9 |
| 4.5 | -4.4 |
| 5 | -4.9 |
| 6 | -5.8 |
| 7 | -6.8 |
| 8 | -7.8 |
| 9 | -8.9 |
| 10 | -10.0 |
| 11 | -11.0 |
| 12 | -12.0 |
| 13 | -13.0 |
| 14 | -14.0 |
| 15 | -14.8 |
| 0 | -0.3 |
| 10 | -10.0 |

### Messprotokolle 21 - 22: Vertical Slide

Ziel: Messung Neigung bei vertikalem Slide
Name: ETD_QA_PoP_SingleCouchRotation_VerticalSlide.json
Konfiguration: Starten bei v +50 weil Neigung notwendig
Vorbereitung: ExacTrac (0.1, -0.3, 0.2), Generator-Synchronisation geprüft

**Messung 21**
Start Messung: 18:15
Ende Messung: 18:23
ExacTrac Zeit: 18:21 - 18:23
ExacTrac 1: 0.1, -0.3, 0.2 → Generator 1 und 2 nicht synched, deswegen Phantom sichtbar
ExacTrac 2: 0.1, -0.3, 0.2 → Generator 1 und 2 synched, deswegen Phantom nicht sichtbar
ExacTrac Datensatz: 182337
CSV: 182011
Notiz: Tracking mehrmals verloren

**Messung 22**
Start Messung: 18:23
Ende Messung: 18:27
ExacTrac Datensatz: 182630
CSV: 182433
Notiz: Tracking wieder mehrmals verloren, aber weniger als bei Messung 22

### Messprotokoll 23: Wärmeprozess

Ziel: Vergleich Bewegungssequenz Kalt vs. Warm
Name: ETD_QA_BasicPoP.json
Konfiguration: Standard Bewegung wenn kalt, dann erwärmen, gleiche Bewegungssequenz nochmal mit warmen Heating Pads fahren

**1. Sequenz (Kalt)**
Start Messung: 18:34
Ende Messung: 18:35
Temperatur: 23.0 - 23.2 °C
ExacTrac Datensatz: 184321
CSV: 183437

Zwischenschritt: Erhitzen beide Heating Pads auf 32 °C, 18:36, ExacTrac ging zwischendurch verloren weil der Temperatur Unterschied wahrscheinlich zu hoch war

**2. Sequenz (Warm)**
Start Messung: 18:42
Ende Messung: 18:43
Temperatur: Unten 31.5 °C, Oben 32.8 °C
ExacTrac Datensatz: 184321
CSV: 184205

Erneuter ExacTrac (zur Kontrolle):
Zeit: 18:43 - 18:45
ExacTrac Datensatz: 184456
CSV: 184348

### Messprotokolle 24 - 26: Wiederholung Longitudinal

Ziel: 5 mal longitudinal ±10mm (2 Sekunden Pause bei 0 vor neuen Durchlauf)
Name: ETD_QA_PoP_SingleCouchRotation_OnlyH.json
Konfiguration: Hitzepads an
Temperatur: 32 °C

- Messung 24: ExacTrac Datensatz: 190312, CSV 190114
- Messung 25: ExacTrac Datensatz: 190609, CSV 190405
- Messung 26: ExacTrac Datensatz: 190831, CSV 190639

### Messprotokolle 27 - 29: Wiederholung Vertikal

Ziel: 5 mal vertikal ±10mm
Name: ETD_QA_PoP_SingleCouchRotation_OnlyV.json
Konfiguration: Hitzepads an
Temperatur: 32 °C

- Messung 27: ExacTrac Datensatz: 191212, CSV: 191006
- Messung 28: ExacTrac Datensatz: 191421, CSV: 191235
- Messung 29: ExacTrac Datensatz: 191651, CSV: 191507

### Messprotokolle 30 - 32: Wiederholung Rotation

Ziel: Rotation ±5 Grad, 5 Wiederholungen
Name: ETD_QA_PoP_SingleCouchRotation_OnlyR.json
Konfiguration: Hitzepads an
Temperatur: 32 °C

- Messung 30: Zeit: 19:18 - 19:20, ExacTrac Datensatz: 192007, CSV: 191806
- Messung 31: Zeit: 19:20 - 19:22, ExacTrac Datensatz: 192224, CSV: 192031
- Messung 32: Zeit: 19:23 - 19:24 ,ExacTrac Datensatz: 192441, CSV: 192250

### Messprotokoll 33: Very speed

Name: ETD_QA_PoP_SingleCouchRotation_RvarySpeed.json
Ziel: einmalige Rotation ±5 Grad, unterschiedliche Geschwindigkeiten
Konfiguration: Hitzepads an
Temperatur: 32 °C
Start Messung: 19:26
Ende Messung: 19:28
ExacTrac Datensatz: 192853
CSV: 192615

### Messprotokolle 34 - 35: Wiederholung Vertical Slide

Ziel: Messung Neigung bei vertikalem Slide
Name: ETD_QA_PoP_SingleCouchRotation_VerticalSlide.json
Konfiguration: Starten bei v +50 weil Neigung notwendig, Hitzepads an
Temperatur: 32 °C
Notiz: Tracking bei beiden Messungen beim nicken verloren gegangen

- Messung 34: Zeit: 19:33 - 19:35, ExacTrac Datensatz: 193528, CSV: 193140
- Messung 35: Zeit: 19:36 - 19:38, ExacTrac Datensatz: 193801, CSV: 193557

### Messprotokoll 36: Wiederholung: Mapping Rotation/Yaw

Ziel: Mapping Phantombewegung vs. Scan in 1 ° Schritten, Überprüfung ab wann Werte ungenau
Konfiguration: Heating Pads an
Temperatur: 32 °C
ExacTrac davor: -0.2, -0.3, 0.1
Start Messung: 19:40
Ende Messung: 19:47
ExacTrac Datensatz: 194758

| Soll (°) | Ist (Phantom) |
|---|---|
| 0 | 0 |
| 1 | -0.8 |
| 2 | -1.7 |
| 2.5 | -2.2 |
| 3 | -2.7 |
| 3.5 | -3.2 |
| 4 | -3.7 |
| 4.5 | -4.2 |
| 5 | -4.7 |
| 6 | -5.6 |
| 7 | -6.6 |
| 8 | -7.6 |
| 9 | -8.7 |
| 10 | -9.8 |
| 11 | -10.8 |
| 12 | -11.7 |
| 13 | -12.8 |
| 14 | -13.7 |
| 15 | -14.7 |

Notiz: Werte deutlich anders, war die Kamera zu lange an?
Abschließender ExacTrac (19:48): -0.2, -0.2, 0.1
