"""Updates the README.md with generated SVG slices and accessible alt text.

Every slice is part of one continuous Rosé Pine terminal HUD.
Alt text ensures full accessibility for screen readers.
"""
import datetime
import html
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
README = HERE.parent.parent / "README.md"
DATA = HERE / "data"


def days(n):
    return f"{n} day" if n == 1 else f"{n} days"


def stats_alt(d):
    since = datetime.date.fromisoformat(d["created_at"][:10])
    EXCLUDE = {"Jupyter Notebook", "HTML", "TeX", "Less", "CSS", "AutoHotkey"}
    langs = sorted({k: v for k, v in d["languages"].items() if k not in EXCLUDE}.items(), key=lambda kv: -kv[1])[:5]
    parts = [
        f'{d["stars"]} total stars',
        f'{d["contributions_year"]} contributions in {d["year"]}, {d["contributions_all"]} all time',
        f'{d["prs"]} pull requests ({d["prs_merged"]} merged)',
        f'current streak {days(d["streak_current"])}, longest {days(d["streak_longest"])}',
        f'{d["followers"]} followers',
        f'{d["forks"]} forks',
        f'member since {since:%B %Y}',
    ]
    text = "Stats: " + "; ".join(parts) + ". Top languages: " + ", ".join(k for k, _ in langs) + "."
    return html.escape(text, quote=True)


def city_alt(calendar):
    total = sum(n for _, n in calendar)
    busiest = max(calendar, key=lambda t: t[1]) if calendar else None
    text = f"Contribution skyline: an isometric night skyline with one building per day of the last year. {total:,} contributions"
    if busiest and busiest[1]:
        d = datetime.date.fromisoformat(busiest[0])
        text += f", busiest day {d:%B} {d.day} with {busiest[1]}"
    return html.escape(text + ".", quote=True)


def generate_readme(stats, calendar):
    alt_header = html.escape(
        "Mohamed Badry — building developer tools, terminal interfaces, and machine learning systems. Rust, Python, Linux.",
        quote=True,
    )
    alt_stats = stats_alt(stats)
    alt_city = city_alt(calendar) if calendar else "Contribution skyline: an isometric night skyline of daily contributions."
    alt_stack = html.escape(
        "Tech stack. Languages: Python, Rust, Java, SQL, Bash. ML & Data: PyTorch, Scikit-learn, NumPy, Pandas, Matplotlib, Seaborn, Plotly. "
        "Backend: FastAPI, PostgreSQL, SQLite, TimescaleDB. Infra & Cloud: Linux, Nix, Docker, GCP. Frontend & UI: Ratatui, Svelte, Tailwind CSS.",
        quote=True,
    )

    alt_wedjat = html.escape(
        "Wedjat — Satellite telemetry anomaly detection on a ground station. SGP4 orbit tracking, PyTorch VAE, and live dashboard. Built with Python, PyTorch, SvelteKit, TimescaleDB.",
        quote=True,
    )
    alt_statui = html.escape(
        "Statui — Async terminal API health check dashboard. HTTP connection pooling, shell variable expansion, zero UI lockup. Built with Rust, Ratatui, Tokio.",
        quote=True,
    )
    alt_islp = html.escape(
        "ISLP Solutions — Programmatic solutions and mathematical proofs for An Introduction to Statistical Learning with Python. Built with Python, Jupyter Book, Scikit-Learn.",
        quote=True,
    )
    alt_nixos = html.escape(
        "nixos-dotfiles — Declarative Linux system configuration with NixOS, Flakes, Home Manager, and Niri. Built with Nix, NixOS, Flakes.",
        quote=True,
    )

    content = f'''<p align="center">
<img src="./assets/header.svg" width="100%" align="top" alt="{alt_header}">
<img src="./assets/links.svg" width="100%" align="top" alt="Links">
<a href="https://www.linkedin.com/in/mohamed0badry/"><img src="./assets/links/linkedin.svg" width="25%" align="top" alt="LinkedIn"></a><a href="https://discord.com/users/573548974636793876"><img src="./assets/links/discord.svg" width="25%" align="top" alt="Discord"></a><a href="https://dev.to/mohamedbadry"><img src="./assets/links/devdotto.svg" width="25%" align="top" alt="DEV"></a><a href="mailto:m.badry.fl@gmail.com"><img src="./assets/links/mail.svg" width="25%" align="top" alt="Email"></a>
<img src="./assets/stats.svg" width="100%" align="top" alt="{alt_stats}">
<img src="./assets/contribution-city.svg" width="100%" align="top" alt="{alt_city}">
<img src="./assets/projects.svg" width="100%" align="top" alt="Projects">
<a href="https://github.com/Mohamed-Badry/statui"><img src="./assets/card-statui.svg" width="50%" align="top" alt="{alt_statui}"></a><a href="https://github.com/Mohamed-Badry/islp-solutions"><img src="./assets/card-islp-solutions.svg" width="50%" align="top" alt="{alt_islp}"></a>
<a href="https://github.com/Mohamed-Badry/nixos-dotfiles"><img src="./assets/card-nixos-dotfiles.svg" width="50%" align="top" alt="{alt_nixos}"></a><a href="https://github.com/Mohamed-Badry/wedjat"><img src="./assets/card-wedjat.svg" width="50%" align="top" alt="{alt_wedjat}"></a>
<img src="./assets/stack.svg" width="100%" align="top" alt="{alt_stack}">
<a href="https://github.com/georgekobaidze"><img src="./assets/footer.svg" width="100%" align="top" alt="Connection closed. Theme inspired by @georgekobaidze."></a>
</p>

'''
    return content


def main():
    if not (DATA / "stats.json").exists():
        sys.exit("error: stats.json not found, run fetch.py first")
    stats = json.loads((DATA / "stats.json").read_text())
    cal_file = DATA / "calendar.json"
    calendar = json.loads(cal_file.read_text()) if cal_file.exists() else []

    rendered = generate_readme(stats, calendar)
    README.write_text(rendered)
    print("README.md updated successfully")


if __name__ == "__main__":
    main()
