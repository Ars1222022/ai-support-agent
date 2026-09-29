# AI Support Agent · Lektion 7

Ett nybörjarprojekt där du steg för steg bygger och undersöker en svensk AI-supportagent. Projektet visar hur dokument kan sökas med RAG, hur LangGraph styr ett arbetsflöde, hur svar kan utvärderas och hur AI-anrop kan följas i Phoenix.

## Tekniköversikt och avgränsningar

### Fungerar i appen

- Docker Compose med separata app-, Chroma- och Phoenix-tjänster.
- RAG: dokument, embeddings och sökning i Chroma.
- LangGraph: kategorisering och RAG-flöde.
- Groq/OpenAI för AI-svar när en API-nyckel finns.
- Phoenix för spårning av LLM-anrop efter ett lyckat anrop.
- Offline-evals: fyra enkla kontroller.

### Förenklat för workshopen

- Evals är grundläggande och testar inte svarskvalitet lika grundligt som professionella eval-verktyg.
- Researcher → writer → reviewer är en enkel kedja i LangGraph, inte autonoma agenter.

### Saknas eller är frivillig fördjupning

- Fullständiga RAGAS-evals ingår inte.
- MCP, verktygsanrop och strukturerade svar hör främst till lektion 6 och ingår inte i denna app.
- Kubernetes nämns som nästa steg, men konfigureras inte.
- Ollama och lokal AI-modell finns som frivillig bonusprofil och kräver extra RAM och diskutrymme. Den ingår inte i standardtestet.

Du kan köra appen på två sätt:

1. **Docker Compose (rekommenderat för kursen):** app, Chroma och Phoenix kör i separata containrar. Python behöver inte installeras på datorn.
2. **Lokalt utan Docker:** Python och alla paket installeras i projektets `.venv`.

Välj ett sätt. Du behöver inte både Docker och en Python-venv.

## Vad finns i appen?

Webbappen byggs med Streamlit. Öppna fliken **Kurssteg** och prova stegen:

| Kurssteg | Vad du får prova |
| --- | --- |
| 1 · RAG och retrieval | Läs supportdokument, dela in dem i textavsnitt, skapa embeddings och hitta relevanta avsnitt i Chroma. |
| 2 · RAG-agent | Skicka den hämtade texten till Groq eller OpenAI och be modellen svara med stöd i källorna. |
| 3 · Enkel LangGraph | Skicka en fråga till en retur-, frakt- eller allmän kategori. |
| 4 · LangGraph med RAG | Låt grafen avgöra om den ska svara direkt eller söka i kunskapsbasen först. |
| 5 · Rollbaserad pipeline | Följ stegen researcher → writer → reviewer. Det är en pedagogisk kedja med roller, inte tre självständiga agenter. |
| 6–7 · Evals | Kör fyra offline-kontroller av hämtad kontext och förväntade fakta. Kontrollerna är enkla nyckelordsregler, inte fullständiga RAGAS- eller LLM-baserade evals. |
| 8 · Phoenix tracing | Se traces från LLM-anrop i Phoenix. Det kräver en API-nyckel och minst ett lyckat LLM-anrop. |
| 9 · Ollama (bonus) | Prova en lokal modell. Den hämtas separat och kan använda mycket disk och RAM. |

Supportinformationen i `data/support_docs.txt` är påhittad demodata. Appen visar källorna som användes. Utan API-nyckel fungerar indexering, retrieval, den enkla LangGraph-grafen och offline-evals. LLM-svar, rollpipeline och Phoenix-traces kräver ett fungerande LLM-anrop.

## Förutsättningar

### Docker Compose

- Windows eller macOS: Docker Desktop, startat och redo.
- Linux: Docker Engine och Docker Compose-plugin.
- Cirka 4 GB RAM till Docker rekommenderas. Standardtjänsterna har tillsammans gränser på cirka 3,25 GB. Ollama-bonusen behöver mer.
- Internet behövs första gången för att hämta images, Python-paket och embedding-modellen.

VS Code och Dev Containers-tillägget är valfria. Du kan följa kursen i appen och köra Compose-kommandon i en vanlig terminal.

### Öppna projektet i VS Code Dev Containers (valfritt)

1. Installera VS Code och tillägget **Dev Containers**.
2. Klona repot och öppna projektmappen i VS Code.
3. Öppna kommandopaletten med `Ctrl+Shift+P` (Windows/Linux) eller `Cmd+Shift+P` (macOS).
4. Välj **Dev Containers: Reopen in Container**. Första gången bygger Docker appimagen och hämtar beroenden.
5. När containern är klar öppnar du appen på `http://localhost:8501`. Portarna 6006 (Phoenix) och 8000 (Chroma API) vidarebefordras också.

VS Code tillägget använder samma `docker-compose.yml` som snabbstarten ovan; skapa inte en andra Compose-konfiguration.

### Lokal körning utan Docker

Python **3.12** måste redan vara installerat. Installationsskripten skapar `.venv` och installerar kursens Python-paket dit; de installerar inte själva Python-programmet.

## Starta med Docker Compose (rekommenderat)

1. Installera och starta Docker Desktop, eller installera Docker Engine + Compose på Linux.
2. Hämta projektet från GitHub och öppna projektmappen i en terminal. På Windows går det även att öppna terminalen i VS Code.
3. Bygg och starta tjänsterna:

   ```sh
   docker compose up --build -d
   ```

4. Kontrollera att tjänsterna körs:

   ```sh
   docker compose ps
   ```

5. Kör projektets verifiering. Windows PowerShell:

   ```powershell
   .\verify-docker.ps1
   ```

   macOS/Linux:

   ```sh
   bash ./verify-docker.sh
   ```

6. Öppna appen på [http://localhost:8501](http://localhost:8501). Phoenix finns på [http://localhost:6006](http://localhost:6006). Chroma är en API-tjänst, inte en webbsida; kontrollera den på [http://localhost:8000/api/v2/heartbeat](http://localhost:8000/api/v2/heartbeat).

Första bygget och modellhämtningen kan ta flera minuter. Koden och appdata sparas i projektmappen; Docker-images och byggcache hanteras av Docker. Om projektet ligger på en annan disk hamnar `.runtime` där, men Docker-images ligger kvar på Docker-motorns diskavbildning. Den kan flyttas i Docker Desktop under **Settings → Resources → Advanced → Disk image location**. [Docker Desktop-inställningar](https://docs.docker.com/desktop/settings-and-maintenance/settings/).

**Har datorn lite ledigt utrymme på C:?** Flytta Docker Desktop:s diskavbildning till en disk med mer plats **innan** första bygget. Lägg även projektmappen där. `.runtime` hamnar bredvid projektet, men Docker-images och byggcache sparas separat av Docker.

### Prova appen utan en API-nyckel

1. Klicka **Bygg om kunskapsbas** i appens sidomeny och vänta tills indexeringen är klar.
2. Öppna **Kurssteg → 6–7 · Evals** och klicka **Kör offline-evals**.
3. För att fråga supportagenten med ett genererat LLM-svar behöver du även konfigurera en nyckel enligt nästa avsnitt.

### Lägg till Groq- eller OpenAI-nyckel

Appen skapar inte API-nyckeln. Skaffa den från ditt konto hos Groq eller OpenAI. Behandla nyckeln som ett lösenord: lägg den bara i den lokala `.env`-filen och dela den aldrig i GitHub eller chatt.

1. Skapa `.env` från exempelmallen i projektroten:

   ```powershell
   Copy-Item .env.example .env
   ```

   macOS/Linux:

   ```sh
   cp .env.example .env
   ```

2. Öppna `.env` i en texteditor och fyll i **en** nyckel:

   ```dotenv
   GROQ_API_KEY=din_groq_nyckel
   ```

   eller:

   ```dotenv
   OPENAI_API_KEY=din_openai_nyckel
   ```

3. Spara filen. Välj motsvarande leverantör i appens **sidomeny** under **AI-leverantör**.
4. Ladda om appcontainern så att den läser den nya konfigurationen:

   ```sh
   docker compose up -d lesson7
   ```

5. Ställ en fråga i fliken **Chatta**. För att se en trace, öppna Phoenix efter ett lyckat LLM-anrop.

`.env` är ignorerad av Git. Skicka aldrig nyckeln till GitHub. API-leverantören kan debitera användning enligt ditt konto och sina villkor.

## Kursövningar med konkreta exempel

Ändra gärna den påhittade informationen i `data/support_docs.txt` och prova sedan **Bygg om kunskapsbas**.

1. **RAG:** fråga ”Vad kostar expressfrakt?” och öppna **Visa källor**. Ändra fraktpriset i demodokumentet, bygg om indexet och fråga igen.
2. **RAG-agent:** jämför ett källbaserat svar med den hämtade kontexten. Prova en fråga vars svar saknas i dokumenten.
3. **LangGraph:** öppna kurssteg 3, prova ”Hur returnerar jag en vara?” och sedan ”Vad kostar frakten?”. Jämför kategorin.
4. **LangGraph + RAG:** prova en hälsning och en fråga om expressfrakt. Se om grafen hämtar kunskap.
5. **Rollpipeline:** kör en returfråga och öppna mellanresultaten från researcher och writer.
6–7. **Evals:** kör offline-kontrollerna och läs vilka faktatermer som hittades. Lägg märke till att detta är en liten pedagogisk kontroll, inte en fullständig kvalitetsmätning av genererade svar.
8. **Tracing:** konfigurera en API-nyckel, skicka en fråga och se om anropet visas i Phoenix.
9. **Ollama (bonus):** använd endast om datorn har tillräckligt med ledigt RAM och diskutrymme. Hämta modellfilen separat enligt kommandona i kurssteget.

Docker ger en reproducerbar miljö med Dockerfile och Compose-tjänster. Dev Containers kan användas i VS Code via konfigurationen i `.devcontainer/`. Kursen visar Docker och Compose; Kubernetes nämns som nästa steg men konfigureras inte här.

## Kör lokalt utan Docker

Lokal körning kräver Python 3.12 installerat på datorn. Öppna terminalen i projektmappen.

**Windows PowerShell:**

```powershell
.\setup-lesson7.ps1
.\run-lesson7.ps1
```

**macOS/Linux:**

```sh
bash ./setup-lesson7.sh
bash ./run-lesson7.sh
```

`setup` skapar `.venv` och `.runtime` i projektmappen. `run` startar appen och Phoenix. Öppna `http://localhost:8501`; Phoenix finns på `http://localhost:6006`. Lokal Chroma körs inbäddad i Python-processen, så ingen separat Chroma-tjänst eller Docker behövs. Skapa `.env` enligt avsnittet ovan om du vill ha LLM-svar.

Kör lokal verifiering i en andra terminal medan appen körs:

```powershell
.\verify-local.ps1
```

```sh
bash ./verify-local.sh
```

## Stoppa och starta igen

Stoppa Docker-tjänsterna utan att ta bort projektdata:

```sh
docker compose down
```

Starta igen utan att bygga om:

```sh
docker compose up -d
```

`.runtime/` innehåller embedding-cache, Chroma-data och Phoenix-data. Ta bara bort den mappen om du medvetet vill radera dessa lokala data. `docker compose down` tar inte bort Docker-images eller byggcache.

## Felsökning

```sh
docker compose ps
docker compose logs --tail 80 lesson7 chroma phoenix
```

- **Appen öppnas inte:** kontrollera att `lesson7` kör och titta i appens logg. App: `http://localhost:8501`.
- **Chroma visar 404 på startsidan:** normalt; Chroma har ingen startsida. Använd heartbeat-adressen ovan.
- **API-nyckel saknas:** kontrollera att `.env` ligger bredvid `docker-compose.yml`, att nyckeln är rätt vald i sidomenyn och kör `docker compose up -d lesson7` igen.
- **Phoenix saknar traces:** skicka först ett lyckat LLM-anrop med en giltig nyckel. Phoenix visar inte tavlor/traces om inget anrop har skickats.
- **Porten är upptagen:** stäng programmet som använder 8501, 8000 eller 6006.
- **Docker fungerar inte:** starta Docker Desktop och vänta tills motorn är redo. Kontrollera diskutrymme med `docker system df`.
- **Verifieringsskriptet:** PowerShell kör `./verify-docker.ps1`; macOS/Linux kör `bash ./verify-docker.sh`.

### Vad verifieringsskripten kontrollerar

- `verify-docker.ps1` / `verify-docker.sh`: Compose-konfiguration, att appcontainern kör, Python-importer, offline-smoke-test samt HTTP-svar från app, Chroma och Phoenix. Vid fel visas tjänstloggar.
- `verify-local.ps1` / `verify-local.sh`: offline-smoke-test och appens/Phoenix HTTP-svar. Vid fel visar skriptet var du hittar app- respektive Phoenix-loggar.
- `smoke_test.py`: läser demodokument, indexerar sju avsnitt, testar svensk retrieval, en LangGraph-rutt och fyra offline-evals.

Verifieringen hjälper dig hitta var felet uppstår; den reparerar inte automatiskt API-nycklar, portkonflikter eller Docker-installationen. Börja felsöka med **första felmeddelandet**, inte med följdfelen längre ner.

## Vad projektet förenklar

- Steg 6 och 7 visas som en gemensam uppsättning med fyra enkla offline-kontroller. De utvärderar inte LLM-svar och ersätter inte fullständiga RAGAS-evals.
- Researcher → writer → reviewer är tre steg i en LangGraph-graf, inte autonoma agenter med egna verktyg/minnen.
- Ollama är en frivillig bonus. Standardläget använder Chroma, Sentence Transformers, LangGraph och Groq/OpenAI.
- Projektet lär inte ut Kubernetes och innehåller ingen Kubernetes-konfiguration.
- Skripten är förberedda för Windows, macOS och Linux, men har i den här arbetsmiljön verifierats i Docker på Windows. Separat test på Mac och Linux återstår; operativsystemstöd ska därför inte tolkas som att varje dator/processor har provats.
