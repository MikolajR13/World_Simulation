# Symulacja Agentowa

## Model Danych

Poniższy diagram UML przedstawia strukturę klas używaną w symulacji społeczeństw (agentów).

```mermaid
classDiagram
    class Agent {
        +int zdrowie
        +int wiek
        +int liczebność
        +int rozmnażalność
        +int śmiertelność
        +int agresja
        +int ufność
        +int zaradność
        +int wytrzymałość
        +int głód
        +int pragnienie
        +int zapasWody
        +int zapasJedzenia
        +Osada osada
        +Point pozycja
        +obliczRozmnażalność()
        +obliczŚmiertelność()
        +obliczAgresję()
        +obliczUfność()
        +obliczZaradność()
        +obliczWytrzymałość()
        +aktualizujGłód()
        +aktualizujPragnienie()
        +aktualizujZdrowie()
        +aktualizujLiczebność()
        +zbierajZapasJedzenia()
        +zbierajZapasWody()
        +zużywajZapasJedzenia()
        +zużywajZapasWody()
        +migruj()
        +atakujAgenta(Agent) : boolean
        +łączPlemiona(Agent) : boolean
        +budujOsadę() : Osada
        +rozbudujOsadę()
        +przejdźNastępnyOkres()
    }
    
    class Osada {
        +int poziomRozwoju
        +int pojemnośćMagazynu
        +int obrona
        +boolean czyZbudowana
        +Point pozycja
        +buduj()
        +rozbuduj()
        +zwiększPojemnośćMagazynu()
        +zwiększObronę()
        +poprawParametryPola(Pole pole)
    }
    
    class Pole {
        +int trudnośćTerenu
        +int niebezpieczeństwo
        +int dostępnośćWody
        +int dostępnośćJedzenia
        +boolean możliwośćBudowy
        +Osada osadaNaPolu
        +aktualizujZasoby()
        +określWpływNaAgenta(Agent)
        +poprawParametry(int zmianaWody, int zmianaJedzenia, int zmianaNiebezpieczeństwa)
    }
    
    class Mapa {
        +int szerokość
        +int wysokość
        +Pole[][] pola
        +Pole getPole(Point pozycja)
        +List<Pole> getPolaSąsiednie(Point pozycja)
        +List<Point> znajdźNajkorzystniejszeTereny(Point obecnaPozycja, int promień)
        +sprawdźMożliwośćBudowy(Point) : boolean
        +aktualizujParametryPólZOsadami()
    }
    
    class Środowisko {
        +Mapa mapa
        +int sezon
        +int warunekPogodowy
        +aktualizujZasoby()
        +wpływNaAgentów(Agent[])
        +sprawdźInterakcjeMiędzyAgentami(Agent[])
        +generujZdarzenieLosowe()
        +zmieńSezon()
    }
    
    class Symulacja {
        +Agent[] agenci
        +Środowisko środowisko
        +int obecnyOkres
        +wykonajKrok()
        +inicjalizuj()
        +zbierzStatystyki()
        +wykryjKonflikty()
        +rozwiążKonflikty()
    }
    
    Symulacja "1" -- "1..*" Agent : zawiera
    Symulacja "1" -- "1" Środowisko : zawiera
    Środowisko -- Agent : wpływa na
    Agent "1" -- "0..1" Osada : posiada
    Środowisko "1" -- "1" Mapa : zawiera
    Mapa "1" -- "many" Pole : składa się z
    Agent -- Agent : wchodzi w interakcje
```

## Opis modelu

### Agent (społeczeństwo)
Agent reprezentuje społeczeństwo/plemię z parametrami takimi jak:
- **Parametry życiowe**: zdrowie, wiek, liczebność, rozmnażalność, śmiertelność
- **Parametry społeczne**: agresja, ufność, zaradność
- **Parametry zasobów**: zapas wody, zapas jedzenia, głód, pragnienie
- **Parametry mobilności**: wytrzymałość, pozycja

### Osada
Agenci mogą budować osady, które poprawiają parametry pola, na którym się znajdują:
- Zwiększają dostępność wody i jedzenia
- Zmniejszają niebezpieczeństwo
- Zapewniają magazynowanie zasobów

### Mapa i pola
Mapa składa się z pól, gdzie każde pole ma własne parametry:
- Trudność terenu
- Niebezpieczeństwo
- Dostępność wody i jedzenia
- Możliwość budowy

### Środowisko
Zarządza warunkami globalnymi takimi jak:
- Sezon
- Warunki pogodowe
- Zdarzenia losowe

### Symulacja
Koordynuje działanie całego systemu, inicjalizuje agentów i środowisko, oraz wykonuje kroki symulacji.
