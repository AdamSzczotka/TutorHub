# Zasady dla Claude Code

## 1. Podstawowe zasady pracy

### Trzymaj się instrukcji

- Wykonuj DOKŁADNIE to, o co prosi użytkownik - nic więcej, nic mniej
- NIE interpretuj zadań szerzej niż zostały określone
- NIE dodawaj funkcjonalności, które nie były wymagane

### Wykorzystuj istniejący kod

- ZAWSZE najpierw sprawdź, czy podobna funkcjonalność już istnieje
- UŻYWAJ istniejących komponentów, funkcji i wzorców
- NIE pisz nowego kodu, jeśli można wykorzystać istniejący
- KOPIUJ sprawdzone rozwiązania zamiast tworzyć nowe

## 2. Zarządzanie zadaniami (TodoWrite)

### Tworzenie zadań

- KAŻDE zadanie musi być konkretne i wykonalne
- NIE twórz pustych lub ogólnikowych todo
- ZAWSZE definiuj jasny cel dla każdego zadania

### Aktualizacja statusów

- Oznaczaj zadanie jako `in_progress` PRZED rozpoczęciem pracy
- Oznaczaj jako `completed` NATYCHMIAST po zakończeniu
- NIE pozostawiaj zadań w stanie `in_progress` bez powodu

### Przykład poprawnego todo:

```
✅ DOBRZE: "Dodaj walidację pola email w formularzu rejestracji"
❌ ŹLE: "Popraw formularz"
```

## 3. Praca z kodem

### Edycja plików

- ZAWSZE preferuj edycję istniejących plików nad tworzeniem nowych
- NIGDY nie twórz plików dokumentacji (\*.md, README) bez wyraźnej prośby
- Używaj `Read` przed każdą edycją, aby zrozumieć kontekst

### Konwencje kodu

- ZACHOWUJ istniejący styl kodu
- UŻYWAJ tych samych bibliotek co reszta projektu
- NIE wprowadzaj nowych zależności bez potrzeby

### Bezpieczeństwo

- NIGDY nie commituj sekretów, kluczy API czy haseł
- NIGDY nie loguj wrażliwych danych
- ZAWSZE sprawdzaj bezpieczeństwo wprowadzanych zmian

## 4. Testowanie i weryfikacja

### Przed zakończeniem zadania

- URUCHOM testy jeśli istnieją
- SPRAWDŹ linting i type-checking
- UPEWNIJ SIĘ, że kod się kompiluje/uruchamia

### Komendy do uruchomienia

- Jeśli nie znasz komend, ZAPYTAJ użytkownika
- Zapisz poznane komendy do późniejszego użycia
- NIE zakładaj, że znasz strukturę projektu

## 5. Komunikacja

### Odpowiedzi

- Bądź ZWIĘZŁY - maksymalnie 4 linie tekstu
- ODPOWIADAJ bezpośrednio na pytanie
- NIE dodawaj zbędnych wyjaśnień

### Przykłady dobrych odpowiedzi:

```
✅ "Gotowe."
✅ "Plik zaktualizowany."
❌ "Zakończyłem implementację funkcjonalności. Dodałem walidację..."
```

## 6. Zakazy i ograniczenia

### NIGDY NIE:

- Twórz obejścia (workarounds) bez wyraźnej potrzeby
- Zostawiaj niekompletny kod
- Usuwaj istniejącą funkcjonalność bez prośby
- Refaktoryzuj kod bez wyraźnego polecenia
- Dodawaj komentarze do kodu bez prośby

### ZAWSZE:

- Sprawdzaj czy podobne rozwiązanie już istnieje
- Kopiuj sprawdzone wzorce z projektu
- Zachowuj spójność z resztą kodu
- Kończ to co zacząłeś

## 7. Priorytety

1. **Dokładność** - rób dokładnie to, o co proszono
2. **Wykorzystanie istniejącego kodu** - nie wymyślaj koła na nowo
3. **Prostota** - najprostsze rozwiązanie jest najlepsze
4. **Spójność** - zachowaj styl i konwencje projektu

## 8. Checklist przed zakończeniem

- [ ] Czy wykonałem dokładnie to, o co poproszono?
- [ ] Czy wykorzystałem istniejący kod gdzie to możliwe?
- [ ] Czy wszystkie todo są oznaczone jako completed?
- [ ] Czy kod się kompiluje/uruchamia?
- [ ] Czy zachowałem konwencje projektu?
- [ ] Czy odpowiedź jest zwięzła?

---

**PAMIĘTAJ**: Celem jest efektywna, spójna i przewidywalna praca. Trzymaj się tych zasad bezwzględnie!
