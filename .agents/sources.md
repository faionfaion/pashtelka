# Pashtelka News Sources

## Tier 1: Daily Automated Monitoring

### RSS Feeds

| Source | Feed URL | Category | Notes |
|--------|----------|----------|-------|
| RTP (latest) | `https://www.rtp.pt/noticias/rss` | General | Public broadcaster, free |
| RTP (country) | `https://www.rtp.pt/noticias/rss/pais` | National | Domestic news |
| RTP (world) | `https://www.rtp.pt/noticias/rss/mundo` | World | International |
| RTP (economy) | `https://www.rtp.pt/noticias/rss/economia` | Economy | Business/finance |
| RTP (culture) | `https://www.rtp.pt/noticias/rss/cultura` | Culture | Events, arts |
| Publico | `https://feeds.feedburner.com/PublicoRSS` | General | Quality daily, metered |
| Observador | `https://observador.pt/feed/` | General | Digital-native |
| CM Jornal | `https://www.cmjornal.pt/rss` | General | Highest circulation |
| NaM | `https://www.noticiasaominuto.com/rss` | Breaking | May need user-agent header |

### APIs (JSON, no auth)

| Service | Endpoint | Data | Update Frequency |
|---------|----------|------|-----------------|
| IPMA Weather | `https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/{id}.json` | 5-day forecast | Every 6h |
| IPMA Warnings | `https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json` | Weather alerts | Real-time |
| IPMA UV | `https://api.ipma.pt/open-data/forecast/meteorology/uv/uv.json` | UV index | Daily |
| IPMA Seismic | `https://api.ipma.pt/open-data/observation/seismic/{area}.json` | Earthquakes | Real-time |
| IPMA Observations | `https://api.ipma.pt/open-data/observation/meteorology/stations/observations.json` | Current weather | Hourly |
| IPMA Location IDs | `https://api.ipma.pt/open-data/distrits-islands.json` | District/city lookup | Static |
| IPMA Weather Types | `https://api.ipma.pt/open-data/weather-type-classe.json` | Code translation | Static |
| Metro Lisboa | `http://app.metrolisboa.pt/status/getLinhas.php` | Line status | Real-time |

### IPMA Location IDs (key cities)

| City | globalIdLocal |
|------|--------------|
| Lisboa | 1110600 |
| Porto | 1131200 |
| Faro | 0806011 |
| Cascais | 1104300 |
| Sintra | 1111500 |
| Coimbra | 0612300 |
| Braga | 0303200 |

## Tier 2: Regular Monitoring

| Source | URL | Type | Focus |
|--------|-----|------|-------|
| Jornal de Noticias | https://www.jn.pt | National daily | Porto + North |
| Diario de Noticias | https://www.dn.pt | National daily | Lisbon |
| ECO | https://eco.sapo.pt | Economy | Business news |
| Jornal de Negocios | https://www.jornaldenegocios.pt | Business | Markets, economy |

## Tier 3: Topic-Specific

### Immigration
| Source | URL | Update |
|--------|-----|--------|
| AIMA | https://www.aima.gov.pt | Check daily |
| Portal Gov.pt | https://eportugal.gov.pt | Legal changes |
| Diario da Republica | https://diariodarepublica.pt | New laws |

### Municipal
| Municipality | URL |
|-------------|-----|
| CM Lisboa | https://informacao.lisboa.pt |
| CM Porto | https://www.cm-porto.pt |
| CM Faro | https://www.cm-faro.pt |
| CM Cascais | https://www.cascais.pt |
| CM Sintra | https://www.cm-sintra.pt |

### Utilities
| Service | URL | Notes |
|---------|-----|-------|
| EPAL (water Lisbon) | https://www.epal.pt | Facebook for alerts |
| E-REDES (electricity) | https://www.e-redes.pt | Outage schedule page |
| CP (trains) | https://www.cp.pt/passageiros/en/train-times/Alerts | Train disruptions |
| Carris Metro (Lisbon) | https://www.carrismetropolitana.pt | Bus disruptions |

### Tax
| Service | URL | Key Dates |
|---------|-----|-----------|
| Portal das Financas | https://www.portaldasfinancas.gov.pt | IRS: Apr 1 - Jun 30 |
| e-Fatura | https://faturas.portaldasfinancas.gov.pt | Validate by Mar 2 |

## Tier 4: English Cross-Reference

| Source | URL | Focus |
|--------|-----|-------|
| The Portugal News | https://www.theportugalnews.com | Largest EN, Algarve HQ |
| Portugal Resident | https://www.portugalresident.com | Algarve expat |
| Algarve Daily News | https://algarvedailynews.com | Algarve regional |
| Expatica PT | https://www.expatica.com/pt/ | Expat community |

## Ukrainian Community Resources

| Resource | URL/Contact | Type |
|----------|------------|------|
| HELPUA.PT | https://helpua.pt | Refugee support nonprofit |
| Spilka (Union of Ukrainians) | Founded 2003 | Community org |
| Sobor Association | UWC member | National org |
| Ukrainian Embassy PT | https://portugal.mfa.gov.ua | Consular services |
