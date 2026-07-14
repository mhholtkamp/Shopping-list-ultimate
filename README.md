# Shopping List Ultimate

Een Home Assistant-integratie om EAN/UPC-barcodes te scannen, producten lokaal of via Open Food Facts te vinden en ze met zo weinig mogelijk handelingen aan een `todo`-boodschappenlijst toe te voegen.

> Screenshot-placeholder: mobiele scankaart, productbevestiging en recente producten.

## Functies

- UI-configuratie en opties via Config Entry
- EAN-13, EAN-8, UPC-A en UPC-E check-digit-validatie
- lokale opslag in Home Assistant `.storage`; camerabeelden worden nooit opgeslagen
- Open Food Facts API v2 met herkenbare User-Agent
- aangepaste productnamen, scanstatistieken en opnieuw ophalen
- samenvoegen als `Melk ×2`
- services voor dashboards, automations, ESPHome en scanners
- sensoren voor laatste product, bekende producten en totaal aantal scans
- scan-event `shopping_list_ultimate_barcode_scanned`
- responsieve Lovelace-kaart voor lichte en donkere thema's

## Installatie

### HACS

1. Open HACS → Integraties → menu → **Aangepaste repositories**.
2. Voeg de GitHub-URL van deze repository toe als categorie **Integratie**.
3. Installeer Shopping List Ultimate en herstart Home Assistant.
4. Voeg `/shopping_list_ultimate/shopping-list-ultimate-card.js?v=0.1.2` toe als JavaScript-module via **Dashboard → Bronnen**. Kopiëren naar `/config/www` is niet nodig.

### Handmatig

Kopieer `custom_components/shopping_list_ultimate` naar `/config/custom_components/` en herstart Home Assistant. Voeg daarna `/shopping_list_ultimate/shopping-list-ultimate-card.js?v=0.1.2` toe als JavaScript-module via **Dashboard → Bronnen**.

## Configuratie

Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen → Shopping List Ultimate**. Kies de standaard todo-lijst, landcode (`nl`, `be`, enz.), taal, afbeeldingen, automatisch toevoegen, lokaal opslaan van onbekende producten en samenvoegen.

Voeg daarna een handmatige kaart toe:

```yaml
type: custom:shopping-list-ultimate-card
todo_entity: todo.boodschappen
```

De kaart vraagt pas cameratoegang nadat **Product scannen** is gekozen. Browsers zonder BarcodeDetector gebruiken de lokaal meegeleverde ZXing-bundle; handmatige barcode-invoer blijft altijd beschikbaar.

## Services

- `shopping_list_ultimate.lookup_barcode` — lookup en scanregistratie; geeft een response terug
- `shopping_list_ultimate.add_barcode` — lookup plus toevoegen aan een todo-lijst
- `shopping_list_ultimate.add_product` — lokaal product maken
- `shopping_list_ultimate.update_product` — naam, afbeelding, categorie e.d. wijzigen
- `shopping_list_ultimate.delete_product` — lokaal product verwijderen
- `shopping_list_ultimate.refresh_product` — opnieuw ophalen bij Open Food Facts, met behoud van aangepaste naam

### Automation

```yaml
alias: Barcode scanner naar boodschappen
triggers:
  - trigger: state
    entity_id: sensor.usb_barcode_scanner
actions:
  - action: shopping_list_ultimate.add_barcode
    data:
      barcode: "{{ trigger.to_state.state }}"
      todo_entity: todo.boodschappen
      quantity: 1
mode: queued
```

### ESPHome

Een scanner kan de code als event aan Home Assistant leveren:

```yaml
text_sensor:
  - platform: template
    name: Barcode scanner
    id: barcode_scanner

api:
  actions:
    - action: submit_barcode
      variables:
        code: string
      then:
        - homeassistant.event:
            event: esphome.barcode_scanned
            data:
              barcode: !lambda return code;
```

Combineer dit met:

```yaml
triggers:
  - trigger: event
    event_type: esphome.barcode_scanned
actions:
  - action: shopping_list_ultimate.add_barcode
    data:
      barcode: "{{ trigger.event.data.barcode }}"
      todo_entity: todo.boodschappen
```

USB- en Bluetooth-scanners die zich als toetsenbord gedragen kunnen de handmatige invoer in de kaart gebruiken en Enter/Opzoeken sturen.

## Privacy

Video blijft uitsluitend in de browser en wordt gestopt zodra een code is gevonden of de kaart sluit. Er is geen tracking. Alleen de gevalideerde barcode wordt naar Open Food Facts verstuurd als die niet lokaal bekend is.

## FAQ en probleemoplossing

**Camera geweigerd?** Geef Home Assistant cameratoegang in de OS-instellingen en gebruik HTTPS.  
**Geen cameraknop of geen herkenning?** Gebruik de handmatige invoer; zie de beperking hieronder.  
**Open Food Facts offline?** Reeds bekende lokale producten blijven beschikbaar. Probeer onbekende producten later opnieuw.  
**Todo niet beschikbaar?** Controleer of de gekozen `todo.*`-entiteit bestaat en beschikbaar is.  
**Productnaam aanpassen?** Roep `update_product` aan met `custom_name`; deze blijft behouden bij vernieuwen.  
**Opslag herstellen?** Controleer Home Assistant-logs en schrijfrechten op `/config/.storage`.

## Ontwikkeling en tests

```bash
python -m pip install homeassistant pytest pytest-asyncio ruff
ruff check .
pytest
```

CI voert Ruff, Pytest, Hassfest en HACS-validatie uit.

## Bekende beperkingen

- Bewerken gebruikt in deze eerste versie de Home Assistant-services; een aparte visuele bewerkdialoog volgt in een latere frontendrelease.
- Open Food Facts-resultaten hangen af van door de community ingevulde productgegevens.

## Licentie

GNU General Public License v3.0; zie `LICENSE`.
