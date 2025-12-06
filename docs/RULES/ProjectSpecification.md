# Specyfikacja Funkcjonalna Systemu

## CMS Szkoły Korepetycyjnej "Na Piątkę"

> **Wersja**: 1.0.0
> **Data**: Wrzesień 2025
> **Status**: Finalna specyfikacja do implementacji
> **Czas realizacji**: 3 miesiące

---

## 1. WPROWADZENIE

### 1.1 Wizja Projektu

System "Na Piątkę" to kompleksowa platforma do zarządzania szkołą korepetycyjną, zaprojektowana dla polskiego systemu edukacyjnego. Platforma automatyzuje procesy administracyjne, usprawnia komunikację między korepetytorami, uczniami i rodzicami oraz zapewnia przejrzysty system planowania i rozliczeń.

### 1.2 Cel Biznesowy

- **Automatyzacja** procesów administracyjnych (80% redukcji czasu)
- **Centralizacja** danych uczniów, korepetytorów i zajęć
- **Transparentność** dla rodziców (dostęp do postępów dziecka)
- **Optymalizacja** wykorzystania sal i czasu korepetytorów
- **Skalowalność** od 50 do 1000+ uczniów

### 1.3 Grupa Docelowa

- **Właściciel szkoły**: Pełna kontrola i zarządzanie
- **Korepetytorzy**: 10-30 osób, różne przedmioty
- **Uczniowie**: 50-1000 osób, klasy 1-8 + liceum
- **Rodzice**: Dostęp do informacji o dziecku

### 1.4 Kluczowe Wyróżniki

- System **bezpośredniego tworzenia użytkowników przez admina** (brak publicznej rejestracji)
- **Polski system edukacyjny** (klasy, przedmioty)
- **Real-time** kalendarz z rezerwacją sal
- **Automatyczne powiadomienia** (email, SMS w przyszłości)
- **RODO/GDPR** compliance

---

## 2. WYMAGANIA FUNKCJONALNE

### 2.1 System Autoryzacji

#### 2.1.1 Bezpośrednie tworzenie użytkowników

- **Tylko admin** może tworzyć nowych użytkowników
- Admin wprowadza: imię, nazwisko, email, rolę, klasę (dla uczniów)
- System generuje **tymczasowe hasło** automatycznie
- Email z danymi logowania wysyłany automatycznie
- **Pierwsze logowanie** wymusza zmianę hasła
- Uczniowie muszą uzupełnić dane kontaktowe rodziców

#### 2.1.2 Logowanie i Sesje

- Email + hasło
- **Remember Me** (30 dni)
- **Timeout sesji** po 2h nieaktywności
- Ostrzeżenie 5 min przed wygaśnięciem
- **2FA** (planowane w v2)

#### 2.1.3 Odzyskiwanie Hasła

- Link resetujący ważny 1h
- Email z instrukcjami
- Wymuszenie silnego hasła (8+ znaków, cyfra, wielka litera)

### 2.2 Role i Uprawnienia

#### 2.2.1 Administrator (1 osoba)

**Pełny dostęp do systemu:**

- Zarządzanie użytkownikami (CRUD)
- Wysyłanie zaproszeń
- Konfiguracja przedmiotów i poziomów
- Zarządzanie salami
- Dostęp do wszystkich kalendarzy
- Raporty finansowe i statystyki
- Audit log wszystkich akcji
- Ustawienia systemu

#### 2.2.2 Korepetytor

**Zarządzanie własnymi zajęciami:**

- Przeglądanie przypisanych uczniów
- Tworzenie i edycja własnych lekcji
- Zarządzanie obecnością
- Dodawanie ocen i uwag
- Dostęp do kalendarza (własne lekcje)
- Komunikacja z rodzicami uczniów
- Przeglądanie własnych statystyk

#### 2.2.3 Uczeń

**Dostęp do własnych danych:**

- Przeglądanie planu zajęć
- Dostęp do materiałów
- Przeglądanie ocen i uwag
- Kalendarz własnych lekcji
- Kontakt z korepetytorami
- Status obecności

#### 2.2.4 Rodzic (przez konto ucznia)

**Monitoring postępów dziecka:**

- Przeglądanie planu zajęć dziecka
- Dostęp do ocen i uwag
- Statystyki obecności
- Kontakt z korepetytorami
- Powiadomienia o nieobecnościach

### 2.3 Zarządzanie Użytkownikami

#### 2.3.1 Profile Użytkowników

**Dane podstawowe (wszyscy):**

- Imię, nazwisko
- Email (unikalny)
- Telefon
- Avatar
- Status aktywności

**Dodatkowe dla korepetytorów:**

- Biografia
- Stawka godzinowa
- Lata doświadczenia
- Wykształcenie
- Certyfikaty
- Przedmioty i poziomy
- Dostępność (godziny)
- Strefa czasowa

**Dodatkowe dla uczniów:**

- Klasa
- Obecny poziom
- Cele edukacyjne
- Dane rodziców (2 kontakty)
- Kontakt alarmowy
- Uwagi

#### 2.3.2 Operacje CRUD

- Tworzenie bezpośrednio przez admina
- Edycja profilu (ograniczona dla uczniów)
- Dezaktywacja konta (soft delete)
- Eksport danych (RODO)
- Historia zmian (audit log)

### 2.4 System Lekcji i Korepetycji

#### 2.4.1 Struktura Lekcji

**Event (Lekcja):**

- Tytuł i opis
- Przedmiot + poziom
- Korepetytor
- Sala (fizyczna/online)
- Czas (start, koniec)
- Typ: indywidualna/grupowa
- Max uczestników (dla grupowych)
- Status: zaplanowana/w trakcie/zakończona/anulowana
- Kolor w kalendarzu

#### 2.4.2 Zarządzanie Lekcjami

- **Tworzenie**: drag & drop w kalendarzu lub formularz
- **Edycja**: zmiana terminu, sali, korepetytora
- **Anulowanie**: z powodem, powiadomienie uczestników
- **Kopiowanie**: duplikowanie lekcji
- **Serie lekcji**: powtarzające się (codziennie/tygodniowo/miesięcznie)

#### 2.4.3 Filtrowanie i Wyszukiwanie

**Real-time filtrowanie bez przeładowania:**

- Po korepetytorze
- Po uczniu
- Po przedmiocie
- Po poziomie
- Po sali
- Po statusie
- Po dacie (od-do)
- Wyszukiwanie tekstowe

#### 2.4.4 Przypisywanie Uczniów do Zajęć

- **Tylko admin** przypisuje uczniów do zajęć
- Zarządzanie listą uczestników
- Limity miejsc (dla zajęć grupowych)
- Automatyczne powiadomienia o przypisaniu/usunięciu

### 2.5 System Kalendarza

#### 2.5.1 Widoki

- **Dzień**: szczegółowy plan
- **Tydzień**: tygodniowy rozkład (domyślny)
- **Miesiąc**: przegląd miesięczny
- **Lista**: tabelaryczny widok
- **Zasoby**: widok po salach

#### 2.5.2 Funkcjonalności

- **Drag & drop** przesuwanie lekcji
- **Resize** zmiana długości lekcji
- **Click** tworzenie nowej lekcji
- **Hover** podgląd szczegółów
- **Konflikty**: automatyczne wykrywanie nakładających się lekcji
- **Kolory**: różne dla typów/przedmiotów

#### 2.5.3 Integracje

- Eksport do iCal
- Synchronizacja z Google Calendar (v2)
- Outlook integration (v2)

### 2.6 Zarządzanie Salami

#### 2.6.1 Typy Sal

- **Fizyczne**: sale w budynku
- **Online**: wirtualne pokoje (Zoom/Teams)

#### 2.6.2 Parametry Sali

- Nazwa i numer
- Pojemność (max osób)
- Lokalizacja (piętro, budynek)
- Wyposażenie (JSON):
  - Tablica (zwykła/interaktywna)
  - Projektor
- Status aktywności

#### 2.6.3 Rezerwacje

- Kalendarz dostępności
- Blokowanie sal (remont, wydarzenie)
- Priorytety rezerwacji
- Automatyczne przydzielanie

### 2.7 System Obecności

#### 2.7.1 Rejestracja Obecności

- **Check-in** przez korepetytora
- Status: obecny/nieobecny/spóźniony/usprawiedliwiony
- Czas wejścia/wyjścia
- Notatki

#### 2.7.2 Statystyki

- % frekwencji per uczeń
- Trendy obecności
- Raporty miesięczne
- Alerty przy niskiej frekwencji (<80%)

### 2.8 System Fakturowania

#### 2.8.1 Cykl Fakturowania

- **Faktury z góry** za następny miesiąc
- Generowanie na koniec bieżącego miesiąca
- Termin płatności: 14 dni
- Automatyczne przypomnienia

#### 2.8.2 Dane Faktury

- Numer faktury (automatyczny)
- Dane szkoły (sprzedawca)
- Dane rodzica/ucznia (nabywca)
- Lista zajęć planowanych na następny miesiąc
- Stawka per lekcja/godzina
- Podsumowanie kwot (netto, VAT, brutto)
- Metoda płatności

#### 2.8.3 Proces Fakturowania

1. **25. dzień miesiąca** - system zbiera planowane zajęcia
2. **Kalkulacja** - suma zajęć × stawka
3. **Generowanie PDF** - faktura proforma/VAT
4. **Wysyłka email** do rodziców
5. **Monitoring płatności** - status faktury
6. **Przypomnienia** - 7 dni przed terminem
7. **Korekty** - przy anulowaniu zajęć

#### 2.8.4 Statusy Faktur

- Wygenerowana
- Wysłana
- Opłacona
- Przeterminowana
- Anulowana
- Skorygowana

#### 2.8.5 Integracje

- Generator PDF (React PDF)
- Email z załącznikiem
- Eksport do księgowości (CSV/XML)
- Przelewy24/Stripe (v2)

### 2.9 System Powiadomień

#### 2.9.1 Typy Powiadomień

- **Email**: główny kanał
- **In-app**: powiadomienia w systemie
- **SMS**: planowane w v2
- **Push**: mobilne w v3

#### 2.9.2 Zdarzenia Wyzwalające

- Nowe zaproszenie
- Zmiana terminu lekcji
- **Prośba o anulowanie** (dla admina)
- **Decyzja o anulowaniu** (dla ucznia/korepetytora)
- Anulowanie lekcji
- Przypomnienie o lekcji (24h przed)
- **Przypomnienie o zajęciach do odrobienia** (7 dni przed wygaśnięciem)
- Nieobecność dziecka (dla rodziców)
- Nowa ocena/uwaga
- Zbliżający się termin płatności

### 2.10 Komunikacja

#### 2.10.1 Wiadomości Wewnętrzne

- Konwersacje 1-na-1
- Grupy (klasa, przedmiot)
- Załączniki (max 10MB)
- Historia wiadomości
- Status przeczytania

#### 2.10.2 Ogłoszenia

- Globalne (admin)
- Per grupa/klasa
- Przypinane
- Z datą wygaśnięcia

### 2.12 System Anulowania i Przełożenia Zajęć

#### 2.12.1 Zasady Anulowania

- **Minimalne wyprzedzenie**: 24 godziny przed zajęciami
- **Limit anulowań**: 3 per miesiąc (opcjonalnie)
- **Tylko admin** zatwierdza prośby o anulowanie
- **Automatyczna blokada** anulowania <24h
- **Zajęcia grupowe**: możliwość rezygnacji bez anulowania całych zajęć

#### 2.12.2 Proces Anulowania

1. **Uczeń składa prośbę** (min 24h przed)
2. **System weryfikuje** warunki czasowe
3. **Admin otrzymuje** powiadomienie
4. **Admin zatwierdza/odrzuca** z uzasadnieniem
5. **Powiadomienia** do ucznia i korepetytora
6. **Zajęcia trafiają** do puli "do odrobienia"

#### 2.12.3 System Odrabiania

- **30 dni** na odrobienie od daty anulowania
- **Widoczny licznik** dni pozostałych
- **Lista zajęć do odrobienia** w panelu ucznia
- **Automatyczne wygasanie** po 30 dniach
- **Przypomnienia** 7 dni przed wygaśnięciem
- **Możliwość przedłużenia** przez admina (wyjątkowe sytuacje)

#### 2.12.4 Przełożenie Zajęć

- **Prośba o nowy termin** przy anulowaniu
- **Propozycja 3 alternatywnych** terminów
- **Admin przypisuje** nowy termin
- **Automatyczna aktualizacja** kalendarzy
- **Zachowanie powiązania** z oryginalną lekcją

#### 2.12.5 Widoki i Uprawnienia

**Uczeń:**

- Przycisk "Anuluj/Przełóż" (>24h przed)
- Status prośby (oczekuje/zatwierdzona/odrzucona)
- Lista zajęć do odrobienia z timerem
- Historia anulowań

**Admin:**

- Panel zarządzania prośbami
- Zatwierdzanie/odrzucanie z komentarzem
- Przypisywanie nowych terminów
- Statystyki anulowań per uczeń
- Możliwość wymuszenia anulowania

**Korepetytor:**

- Powiadomienia o anulowaniach
- Wolne sloty po anulowaniach
- Zajęcia odróbkowe w kalendarzu

#### 2.12.6 Integracja z Fakturami

- Anulowane zajęcia **nie są fakturowane**
- **Korekta faktury** przy anulowaniu po wystawieniu
- **Przeliczenie** kwoty do zapłaty
- **Nota korygująca** automatycznie generowana

### 2.13 Raporty i Statystyki

#### 2.13.1 Dla Admina

- Liczba użytkowników (trend)
- Wykorzystanie sal (%)
- Frekwencja globalna
- Przychody (per korepetytor/przedmiot)
- Najpopularniejsze przedmioty
- **Statystyki anulowań** (per uczeń/miesiąc)
- **Zajęcia do odrobienia** (aktywne/wygasłe)
- Audit log akcji

#### 2.13.2 Dla Korepetytora

- Liczba przeprowadzonych lekcji
- Liczba uczniów
- Średnia frekwencja
- Zarobki (miesięczne)
- Oceny uczniów (postępy)

#### 2.13.3 Dla Ucznia/Rodzica

- Frekwencja
- Postępy (oceny)
- Nadchodzące lekcje
- **Zajęcia do odrobienia** (z licznikiem dni)
- Historia obecności
- **Historia anulowań**
- Wydatki (v2)

---

## 3. SCHEMAT BAZY DANYCH

### 3.1 Tabele Główne

#### users

```sql
- id (PK)
- name, surname
- email (unique)
- phone
- password (hashed)
- role (admin/tutor/student)
- is_active (boolean)
- last_login_at
- avatar_path
- parent_phone, parent_name, parent_email (dla uczniów)
- secondary_parent_phone, secondary_parent_name
- student_phone
- profile_completed (boolean)
- remember_token
- created_at, updated_at
```

#### tutors (profil korepetytora)

```sql
- id (PK)
- user_id (FK → users, unique)
- bio (text)
- hourly_rate (decimal)
- experience_years (int)
- education (text)
- certifications (JSON)
- availability_hours (JSON)
- timezone
- is_verified (boolean)
- verification_date
- rating_avg (decimal)
- lessons_completed (int)
```

#### students (profil ucznia)

```sql
- id (PK)
- user_id (FK → users, unique)
- class (varchar) "1A", "8B", "3LO"
- current_level
- learning_goals (text)
- timezone
- emergency_contact
- notes (text)
- joined_at
- total_lessons (int)
- completed_lessons (int)
```

#### events (lekcje)

```sql
- id (PK)
- title, description
- subject_id (FK → subjects)
- level_id (FK → levels)
- tutor_id (FK → users)
- room_id (FK → rooms)
- start_time, end_time (datetime)
- is_group_lesson (boolean)
- max_participants (int)
- status (scheduled/ongoing/completed/cancelled)
- notes (text)
- color (hex)
- created_at, updated_at
```

#### rooms (sale)

```sql
- id (PK)
- name (unique)
- capacity (int)
- location (varchar)
- description (text)
- equipment (JSON)
- is_active (boolean)
- created_at, updated_at
```

#### subjects (przedmioty)

```sql
- id (PK)
- name (unique) "Matematyka", "Fizyka"
- description
- icon (varchar)
- is_active (boolean)
```

#### levels (poziomy)

```sql
- id (PK)
- name (unique) "Klasa 1-3", "Klasa 4-6"
- description
- order_index (int)
- color (hex)
```

### 3.2 Tabele Powiązań

#### event_students (uczniowie na lekcji)

```sql
- id (PK)
- event_id (FK → events)
- student_id (FK → users)
- attendance_status (present/absent/late/excused)
- attendance_marked_at
- notes
- created_at, updated_at
UNIQUE(event_id, student_id)
```

#### tutor_subjects (przedmioty korepetytora)

```sql
- id (PK)
- tutor_id (FK → users)
- subject_id (FK → subjects)
- level_id (FK → levels)
- rate_per_hour (decimal)
- is_active (boolean)
```

#### subject_levels (powiązanie przedmiot-poziom)

```sql
- id (PK)
- subject_id (FK → subjects)
- level_id (FK → levels)
UNIQUE(subject_id, level_id)
```

### 3.3 Tabele Systemowe

#### invitations

```sql
- id (PK)
- token (unique, random 32 chars)
- email
- first_name, last_name
- class (dla uczniów)
- role (tutor/student)
- accepted_at (datetime)
- expires_at (datetime)
- invited_by (FK → users)
- user_id (FK → users, utworzone konto)
```

#### attendance_logs

```sql
- id (PK)
- event_id (FK → events)
- student_id (FK → users)
- status (present/absent/late/excused)
- marked_by (FK → users)
- marked_at (datetime)
- notes
```

#### audit_logs

```sql
- id (PK)
- user_id (FK → users)
- action (varchar)
- model_type, model_id
- old_values (JSON)
- new_values (JSON)
- ip_address
- user_agent
- created_at
```

#### messages

```sql
- id (PK)
- sender_id (FK → users)
- recipient_id (FK → users)
- subject
- content (text)
- is_read (boolean)
- read_at
- attachments (JSON)
- created_at
```

#### notifications

```sql
- id (PK)
- user_id (FK → users)
- type (varchar)
- title, message
- data (JSON)
- is_read (boolean)
- read_at
- created_at
```

#### leads (formularze kontaktowe)

```sql
- id (PK)
- name, email, phone
- subject, message
- status (new/contacted/converted)
- source (web/facebook/google)
- assigned_to (FK → users)
- gdpr_consent (boolean)
- marketing_consent (boolean)
- metadata (JSON)
```

#### invoices (faktury)

```sql
- id (PK)
- invoice_number (unique)
- student_id (FK → users)
- month_year (date)
- total_amount (decimal)
- tax_amount (decimal)
- status (generated/sent/paid/overdue/cancelled)
- due_date
- paid_at
- payment_method
- notes (text)
- pdf_path
- created_at, updated_at
```

#### invoice_items (pozycje faktury)

```sql
- id (PK)
- invoice_id (FK → invoices)
- event_id (FK → events)
- description
- quantity (int)
- unit_price (decimal)
- total_price (decimal)
- created_at
```

#### cancellation_requests (prośby o anulowanie)

```sql
- id (PK)
- event_id (FK → events)
- student_id (FK → users)
- reason (text)
- request_date (datetime)
- status (pending/approved/rejected)
- admin_comment (text)
- approved_by (FK → users)
- approved_at (datetime)
- new_event_id (FK → events, dla przełożenia)
- created_at, updated_at
```

#### makeup_lessons (zajęcia do odrobienia)

```sql
- id (PK)
- original_event_id (FK → events)
- student_id (FK → users)
- cancellation_date (date)
- expires_at (datetime, 30 dni od anulowania)
- status (pending/scheduled/completed/expired)
- rescheduled_event_id (FK → events)
- extended_by (FK → users, admin który przedłużył)
- extended_at (datetime)
- created_at, updated_at
```

### 3.4 Indeksy

- users: email, role, is_active
- events: start_time, end_time, tutor_id, room_id, status
- event_students: event_id, student_id
- attendance_logs: event_id, student_id, marked_at
- messages: sender_id, recipient_id, is_read
- cancellation_requests: event_id, student_id, status, request_date
- makeup_lessons: student_id, status, expires_at
- invoices: student_id, month_year, status

---

## 4. MODUŁY FUNKCJONALNE

### 4.1 Landing Page (Publiczny)

**URL**: `/`

- Hero section z CTA
- O nas
- Oferta (przedmioty)
- Zespół (korepetytorzy)
- Formularz kontaktowy
- Cennik
- FAQ
- Stopka z danymi kontaktowymi

### 4.2 Panel Administratora

**URL**: `/admin/*`
**Zabezpieczenie**: IP whitelist + autoryzacja

#### 4.2.1 Dashboard

- Widgety ze statystykami
- Wykres użytkowników
- Ostatnie aktywności
- Alerty systemowe

#### 4.2.2 Zarządzanie Użytkownikami

- Lista z filtrowaniem i sortowaniem
- Bezpośrednie tworzenie użytkowników
- Edycja profili
- Dezaktywacja kont
- Eksport do CSV

#### 4.2.3 Zarządzanie Lekcjami

- Kalendarz główny
- Lista wszystkich lekcji
- Real-time filtrowanie
- Edycja masowa
- Raporty

#### 4.2.4 Zarządzanie Anulowaniami

- **Panel próśb o anulowanie**
- **Zatwierdzanie/odrzucanie** z komentarzem
- **Przypisywanie nowych terminów**
- **Statystyki anulowań**
- **Lista zajęć do odrobienia** (wszystkich uczniów)

#### 4.2.5 Konfiguracja

- Przedmioty i poziomy
- Sale
- Ustawienia emaili
- Szablony wiadomości

### 4.3 Panel Korepetytora

**URL**: `/tutor/*`

#### 4.3.1 Dashboard

- Dzisiejsze lekcje
- Nadchodzące wydarzenia
- Statystyki miesięczne
- Nieprzeczytane wiadomości

#### 4.3.2 Moje Lekcje

- Kalendarz własny
- Zarządzanie obecnością
- Dodawanie uwag

#### 4.3.3 Moi Uczniowie

- Lista przypisanych
- Profile z postępami
- Komunikacja

### 4.4 Panel Ucznia

**URL**: `/student/*`

#### 4.4.1 Dashboard

- Plan na dziś/tydzień
- Ostatnie oceny
- Nadchodzące testy
- Materiały do pobrania

#### 4.4.2 Mój Kalendarz

- Widok własnych lekcji
- Przeglądanie zaplanowanych zajęć
- **Przycisk anulowania** (>24h przed)
- **Status próśb** o anulowanie

#### 4.4.3 Zajęcia do Odrobienia

- **Lista anulowanych zajęć**
- **Licznik dni** do wygaśnięcia (30 dni)
- **Status odrobienia** (oczekuje/zaplanowane/ukończone)
- **Przypomnienia** o wygasających zajęciach

#### 4.4.4 Postępy

- Frekwencja
- Uwagi korepetytorów

### 4.5 Portal Rodzica

**URL**: dostęp przez konto dziecka

#### 4.5.1 Monitoring

- Plan zajęć dziecka
- Obecności
- Postępy
- Kontakt z korepetytorami

#### 4.5.2 Powiadomienia

- Nieobecności
- Ważne ogłoszenia
- Terminy płatności

---

## 5. PROCESY BIZNESOWE

### 5.1 Onboarding Nowego Użytkownika

```mermaid
1. Admin tworzy konto użytkownika bezpośrednio
2. System generuje tymczasowe hasło
3. System wysyła email z danymi logowania
4. Użytkownik loguje się pierwszym razem
5. Wymuszenie zmiany hasła tymczasowego
6. Uczeń: uzupełnia dane rodziców
7. Korepetytor: uzupełnia profil
8. Aktywacja konta zakończona
```

### 5.2 Planowanie Lekcji

```mermaid
1. Admin/Korepetytor otwiera kalendarz
2. Wybiera wolny termin (drag & drop)
3. Wypełnia: przedmiot, poziom, salę
4. Dodaje uczniów (indywidualne) lub limit (grupowe)
5. System sprawdza konflikty
6. Zapisuje i wysyła powiadomienia
7. Uczestnicy widzą w swoich kalendarzach
```

### 5.3 Proces Obecności

```mermaid
1. 15 min przed lekcją - przypomnienie
2. Korepetytor rozpoczyna lekcję
3. Oznacza obecność uczniów
4. System loguje czas
5. Po lekcji - możliwość dodania uwag
6. Automatyczne statystyki frekwencji
7. Alert przy <80% obecności
```

### 5.4 Cykl Fakturowania

```mermaid
1. 25. dzień miesiąca - zbieranie planowanych zajęć na następny miesiąc
2. Generowanie faktur proforma
3. Wysyłka faktur do rodziców
4. Termin płatności: 14 dni
5. Przypomnienia o płatności (7 dni przed terminem)
6. Monitoring wpłat
7. Korekty przy anulowaniu zajęć
```

### 5.5 Proces Odrabiania Zajęć

```mermaid
1. Zajęcia anulowane trafiają do puli "do odrobienia"
2. System pokazuje licznik 30 dni
3. Uczeń/admin wybiera nowy termin
4. Korepetytor potwierdza dostępność
5. Utworzenie nowej lekcji powiązanej z anulowaną
6. Automatyczne przypomnienie 7 dni przed wygaśnięciem
7. Po 30 dniach - automatyczne wygasanie lub przedłużenie przez admina
```

### 5.6 Cykl Miesięczny Raportowania

```mermaid
1. Koniec miesiąca - generowanie raportów
2. Podsumowanie godzin per korepetytor
3. Statystyki obecności per uczeń
4. Analiza anulowań i zajęć odrobionych
5. Wysyłka podsumowań do rodziców
6. Planowanie następnego miesiąca
```

---

## 6. INTEGRACJE

### 6.1 Email (v1)

- **Provider**: Resend / SMTP Gmail
- Transakcyjne (zaproszenia, resety)
- Powiadomienia (zmiany lekcji)
- Newsletter (v2)

### 6.2 Kalendarz (v1-v2)

- Eksport iCal
- Google Calendar API (v2)
- Outlook integration (v2)

### 6.3 Płatności (v2)

- Stripe / Przelewy24
- Faktury automatyczne
- Przypomnienia o płatnościach

### 6.4 SMS (v2)

- SMSAPI / Twilio
- Przypomnienia o lekcjach
- Alerty o nieobecnościach

### 6.5 Video (v3)

- Zoom API / Google Meet
- Automatyczne tworzenie pokoi
- Nagrywanie lekcji

---

## 7. WYMAGANIA NIEFUNKCJONALNE

### 7.1 Wydajność

- **Response time**: <200ms (95 percentyl)
- **Concurrent users**: 100+
- **Database queries**: <50ms
- **Page load**: <3s (mobile 3G)
- **API rate limit**: 100 req/min per user

### 7.2 Bezpieczeństwo

- **HTTPS** everywhere
- **Bcrypt** hashowanie haseł
- **CSRF** protection
- **XSS** prevention
- **SQL injection** protection (Prisma)
- **Rate limiting** na API
- **IP whitelist** dla admina
- **Audit log** wszystkich zmian
- **GDPR/RODO** compliance
- **Data encryption** at rest

### 7.3 Skalowalność

- **Horizontal scaling** (multiple instances)
- **Database pooling**
- **CDN** dla assets
- **Queue system** dla zadań
- **Caching** (Redis)

### 7.4 Dostępność

- **Uptime**: 99.9% (8.77h downtime/rok)
- **Backup**: codziennie
- **Recovery time**: <4h
- **Monitoring**: 24/7 (Sentry)

### 7.5 Kompatybilność

- **Browsers**: Chrome 100+, Firefox 100+, Safari 14+, Edge
- **Mobile**: Responsive design
- **Screen**: 320px - 4K
- **Accessibility**: WCAG 2.1 Level AA

---

## 8. MVP vs FULL VERSION

### 8.1 MVP (Miesiąc 1-2)

**Must Have:**

- ✅ System autoryzacji (bezpośrednie tworzenie przez admina)
- ✅ 3 role (admin, tutor, student)
- ✅ CRUD użytkowników
- ✅ Kalendarz z lekcjami
- ✅ Zarządzanie salami
- ✅ System obecności
- ✅ Email powiadomienia
- ✅ Panel admina (IP-restricted)
- ✅ Responsywny design
- ✅ Real-time filtrowanie
- ✅ Eksport CSV
- ✅ Wiadomości wewnętrzne
- ✅ Statystyki i raporty
- ✅ Portal rodzica
- ✅ Audit log
- ✅ Lepszy UX kalendarza

### 8.3 Wersja 2.0 (Przyszłość)

**Nice to Have:**

- ⏳ System płatności online (integracja Stripe/Przelewy24)
- ⏳ Faktury z automatycznym księgowaniem
- ⏳ SMS powiadomienia
- ⏳ 2FA autoryzacja
- ⏳ Google/Outlook sync
- ⏳ Oceny i dziennik
- ⏳ Materiały edukacyjne
- ⏳ Forum dyskusyjne

### 8.4 Wersja 3.0 (Długoterminowa)

**Future:**

- ⏳ Aplikacja mobilna
- ⏳ Video konferencje
- ⏳ AI asystent
- ⏳ Gamifikacja
- ⏳ Multi-tenant (wiele szkół)
- ⏳ Marketplace korepetytorów

---

## 9. KRYTERIA SUKCESU

### 9.1 Techniczne

- ✅ Wszystkie testy przechodzą (>80% coverage)
- ✅ Response time <200ms
- ✅ Zero krytycznych bugów
- ✅ Deployment bez downtime

### 9.2 Biznesowe

- ✅ 50+ aktywnych użytkowników w pierwszym miesiącu
- ✅ 90% satysfakcji użytkowników
- ✅ 50% redukcji czasu administracyjnego
- ✅ ROI w ciągu 6 miesięcy

### 9.3 UX

- ✅ Onboarding <5 minut
- ✅ Intuicyjny bez szkoleń
- ✅ Mobile-first
- ✅ Dostępność WCAG 2.1

---

## 10. HARMONOGRAM IMPLEMENTACJI

### Miesiąc 1: Fundament

**Tydzień 1-2:**

- Setup projektu Next.js + tRPC
- Konfiguracja PostgreSQL + Prisma
- System autoryzacji (NextAuth)
- Modele bazowe

**Tydzień 3-4:**

- System bezpośredniego tworzenia użytkowników
- Role i uprawnienia
- Panel admina (podstawowy)
- CRUD użytkowników

### Miesiąc 2: Core Features

**Tydzień 5-6:**

- Kalendarz (FullCalendar)
- Zarządzanie lekcjami
- System sal

**Tydzień 7-8:**

- System obecności
- Powiadomienia email
- Real-time filtrowanie

### Miesiąc 3: Finalizacja

**Tydzień 9-10:**

- Portal ucznia
- Portal rodzica
- System fakturowania
- Wiadomości wewnętrzne

**Tydzień 11-12:**

- Testy E2E
- Optymalizacja
- Deployment
- Dokumentacja

---

## 11. RYZYKA I MITYGACJE

### 11.1 Ryzyka Techniczne

| Ryzyko                       | Prawdopodobieństwo | Wpływ  | Mitygacja                |
| ---------------------------- | ------------------ | ------ | ------------------------ |
| Brak migracji (nowy projekt) | Brak               | Brak   | Świeży start, czysty kod |
| Wydajność przy 1000+ users   | Niskie             | Wysoki | Load testing, caching    |
| Integracje zewnętrzne        | Średnie            | Średni | Fallback solutions       |

### 11.2 Ryzyka Biznesowe

| Ryzyko            | Prawdopodobieństwo | Wpływ  | Mitygacja           |
| ----------------- | ------------------ | ------ | ------------------- |
| Opór przed zmianą | Średnie            | Średni | Szkolenia, wsparcie |
| Zmiana wymagań    | Wysokie            | Średni | Agile, częste demo  |
| Konkurencja       | Niskie             | Niski  | Unikalne features   |

---

## 12. DEFINICJE I SKRÓTY

- **CMS**: Content Management System
- **CRUD**: Create, Read, Update, Delete
- **RODO**: Rozporządzenie o Ochronie Danych Osobowych
- **GDPR**: General Data Protection Regulation
- **MVP**: Minimum Viable Product
- **SPA**: Single Page Application
- **SSR**: Server Side Rendering
- **2FA**: Two-Factor Authentication
- **API**: Application Programming Interface
- **UI/UX**: User Interface/User Experience

---

**Dokument zatwierdzony przez**: Właściciela systemu
**Data zatwierdzenia**: Wrzesień 2025
**Następna rewizja**: Po MVP (miesiąc 2)
