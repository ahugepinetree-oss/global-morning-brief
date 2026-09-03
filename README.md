# Global Morning Brief

A personal daily economic-English web app.

## What happens every morning
1. GitHub Actions runs at 07:10 Asia/Seoul.
2. `scripts/generate_brief.py` asks the OpenAI Responses API to search current global economic news.
3. It synthesizes one cross-market theme and writes `data/today.json`.
4. The same GitHub Pages URL reads the new JSON automatically.

## Learning design
- Main article: original C1-style financial/news English.
- B2 help: optional, hidden until requested.
- Plain Korean explanations for difficult words and economic institutions.
- Multiword news expressions.
- Personal word bank saved in browser localStorage.
- Pronunciation buttons use browser speech synthesis.
- Global snapshot: US / UK / Europe / Japan / China / South Korea.

## First-time setup
1. Create a GitHub repository and upload this project.
2. Repository → Settings → Secrets and variables → Actions → New repository secret.
3. Name: `OPENAI_API_KEY`
4. Value: your OpenAI API key.
5. Repository → Settings → Pages → Source: **GitHub Actions**.
6. Open the Actions tab and run **Daily Global Morning Brief** once manually.
7. Your site will be available at `https://YOUR-USERNAME.github.io/REPOSITORY/`.

## Change the morning time
Edit `.github/workflows/daily.yml`.
The current schedule is 07:10 in `Asia/Seoul`.

## Important
The app synthesizes and links to sources; it should not reproduce article text. Before commercial use, review source terms, copyright/licensing, privacy, and API cost controls.
