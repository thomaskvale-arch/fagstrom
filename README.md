# Fagstraum

Offentlege faglege funn med eigne omtalar og lenkjer til originalkjeldene.
Nettside: https://thomaskvale-arch.github.io/fagstrom/

## RSS

- Alt nytt: `https://thomaskvale-arch.github.io/fagstrom/feeds/all.xml`
- KI i praksis: `https://thomaskvale-arch.github.io/fagstrom/feeds/ki.xml`
- Digitalisering: `https://thomaskvale-arch.github.io/fagstrom/feeds/digitalisering.xml`
- Kompetanse: `https://thomaskvale-arch.github.io/fagstrom/feeds/kompetanse.xml`

## Publisering

På Thomas sin Windows-PC: opne snarvegen **Fagstraum – nytt funn**. Fyll inn tittel, kjeldelenkje, omtale og tema. Vel «Sjå over og publiser», og deretter «Publiser offentleg». GitHub CLI må vere innlogga med skrivetilgang til repoet. Passord og token ligg ikkje i programmet eller nettsida.

`publisher.py` er eit lokalt Windows-program, ikkje eit offentleg redigeringsskjema. Utkast blir lagra i `%LOCALAPPDATA%\Fagstraum\utkast.json`. Programmet les siste versjon frå GitHub før publisering, bevarer andre innlegg og bruker stabil ID for å unngå duplikat ved nytt forsøk etter nettfeil. «Lagra på GitHub» tyder at nettsida deretter må byggjast; knappen for publiseringsstatus viser om bygginga lukkast.

Innlegg ligg i `entries.json`. Ei lagra endring på main byggjer og publiserer automatisk via GitHub Actions. Berre tilsikta offentleg innhald skal leggjast her; ikkje nøklar, interne dokument eller private transkripsjonar.

Format for eitt innlegg (døme, ikkje eit publisert funn):

```json
{
  "id": "eit-stabilt-unikt-namn",
  "published": "2026-10-24T19:00:00+02:00",
  "title": "Tittel på funnet",
  "summary": "Di eiga korte forklaring på kvifor dette er interessant.",
  "url": "https://example.org/artikkel",
  "topics": ["ki", "kompetanse"]
}
```

Behald ID og publiseringstidspunkt ved rettingar. Nye innlegg skal få nye ID-ar og eit publiseringstidspunkt seinare enn tidlegare innlegg; bruk tidspunktet du legg til funnet, ikkje datoen på originalartikkelen. Dette hjelper RSS-lesarar å unngå gjentekne varsel. Mottakaren bør òg lagre behandla ID-ar dersom du treng sikker duplikatkontroll.

## Teams (ikkje kopla til enno)

Opprett ein Power Automate-flyt med RSS-utløysaren «When a feed item is published», lim inn temafeeden og vel publiseringstid som grunnlag. Legg til Teams-handlinga «Post message in a chat or channel» med tittel, omtale og kjeldelenkje. Dette krev jobbkonto og at arbeidsgivaren tillèt koplingane.

Set opp og test flyten før første reelle innlegg. RSS er ikkje straksvarsling. Abonnement på fleire overlappande tema kan gi same funn i fleire kanalar; det er tilsikta.

## Lokal bygging

Køyr `python build.py`; resultatet ligg i `_site/`. Prosjektet bruker berre Python sitt standardbibliotek. Innhaldet i repoet og på nettsida er offentleg.
