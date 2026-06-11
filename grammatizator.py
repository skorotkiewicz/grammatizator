#!/usr/bin/env python3
"""
THE GREAT AUTOMATIC GRAMMATIZATOR
Based on the story by Roald Dahl (1953)

"With one finger, Mr Bohlen carefully pressed the necessary pre-selector buttons..."
"""

import os
import random
import sys
import time
from math import isfinite
from openai import OpenAI

# ─────────────────────────────────────────────
#  MACHINE CONFIGURATION
#  Override with environment variables, or just
#  answer the prompts at startup.
# ─────────────────────────────────────────────

DEFAULT_URL   = "http://192.168.0.124:8888/v1"
DEFAULT_KEY   = "not-needed"   # most local servers ignore this
DEFAULT_MODEL = ""             # e.g. "mistral", "llama3", "qwen2.5"
DEFAULT_MAX_TEMPERATURE = 1.0

# ─────────────────────────────────────────────
#  CONTROL PANEL  (Knipe's pre-selector buttons)
# ─────────────────────────────────────────────

MASTER_BUTTONS = {
    "1": "satirical",
    "2": "romantic",
    "3": "humorous",
    "4": "philosophical",
    "5": "erotic",      # "one came out a trifle lewd"
    "6": "historical",
    "7": "political",
    "8": "straight",
}

THEME_BUTTONS = {
    "1": "army life",
    "2": "pioneer days",
    "3": "civil war",
    "4": "racial problem",
    "5": "wild west",
    "6": "country life",
    "7": "childhood memories",
    "8": "seafaring",
    "9": "city crime",
    "0": "forbidden love",
}

STYLE_BUTTONS = {
    "1": "classical",
    "2": "whimsical",
    "3": "racy",
    "4": "Hemingway",
    "5": "Faulkner",
    "6": "Joyce",
    "7": "feminine",
    "8": "pulp magazine",
}

MAGAZINE_BUTTONS = {
    "1": "Today's Woman",
    "2": "Reader's Digest",
    "3": "Saturday Evening Post",
    "4": "Collier's",
    "5": "Ladies' Home Journal",
    "6": "The New Yorker",
    "7": "Argosy",
}

LENGTH_BUTTONS = {
    "1": ("flash",    "~300 words"),
    "2": ("short",    "~800 words"),
    "3": ("standard", "~1500 words"),
}

# passion level 1-5 (two foot-pedals: content intensity + temperature)
# (label, prompt_intensity, temperature)
PASSION_LEVELS = {
    "1": ("restrained", 0.3, 0.4),
    "2": ("measured",   0.5, 0.6),
    "3": ("charged",    0.7, 0.8),
    "4": ("passionate", 0.9, 1.0),
    "5": ("volcanic",   1.1, 1.2),   # warning: may come out lewd
}

OBSCURE_WORDS = (
    "vellichor", "sonder", "hiraeth", "logorrhea", "somnambulant",
    "epexegetically", "petrichor", "lissom", "tenebrous", "lachrymose",
)


# ─────────────────────────────────────────────
#  DISPLAY HELPERS
# ─────────────────────────────────────────────

def banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║       THE GREAT AUTOMATIC GRAMMATIZATOR                      ║
║       A. Knipe  /  J. Bohlen Inc., Electrical Engineers      ║
║                                                              ║
║  "...it can produce any type of story I desire simply by     ║
║   pressing the required button."                             ║
╚══════════════════════════════════════════════════════════════╝
""")


def show_panel(title, options, show_hint=None):
    print(f"\n  ┌─ {title} {'─' * (50 - len(title))}┐")
    for key, val in options.items():
        if isinstance(val, tuple):
            print(f"  │  [{key}]  {val[0]:<14}  {val[1]}")
        else:
            print(f"  │  [{key}]  {val}")
    if show_hint:
        print(f"  │  {show_hint}")
    print("  └" + "─" * 53 + "┘")


def pick(title, options, show_hint=None):
    show_panel(title, options, show_hint)
    while True:
        choice = input("  PRESS BUTTON > ").strip()
        if choice in options:
            val = options[choice]
            label = val[0] if isinstance(val, tuple) else val
            print(f"  ✓ Selected: {label}\n")
            return choice, val
        print("  (invalid — try again)")


def hum_and_clatter(seconds=3):
    """Simulate the machine running."""
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    sounds = [
        "  [deep whirring of fifty thousand cogs and rods...]",
        "  [drumming of the rapid electrical typewriter...]",
        "  [sheets of quarto paper sliding into the basket...]",
    ]
    print()
    for s in sounds:
        print(s)
        time.sleep(0.6)
    print()
    end = time.time() + seconds
    i = 0
    while time.time() < end:
        print(f"\r  Grammatizating... {frames[i % len(frames)]}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print("\r  Grammatizating... ✓ COMPLETE                    ")
    print()


# ─────────────────────────────────────────────
#  THE MACHINE
# ─────────────────────────────────────────────

def max_temperature():
    """Temperature cap — set GRAMMATIZATOR_MAX_TEMP=1.2 to unlock the full pedal."""
    try:
        value = float(os.environ.get("GRAMMATIZATOR_MAX_TEMP", str(DEFAULT_MAX_TEMPERATURE)))
    except ValueError:
        return DEFAULT_MAX_TEMPERATURE

    if not isfinite(value) or value < 0:
        return DEFAULT_MAX_TEMPERATURE
    return value


def effective_temperature(passion_key, max_temp=None):
    """Return the actual API temperature after the safety cap is applied."""
    _, _, temperature = PASSION_LEVELS[passion_key]
    return min(temperature, max_temperature() if max_temp is None else max_temp)


def connection_defaults():
    return (
        os.environ.get("GRAMMATIZATOR_URL") or DEFAULT_URL,
        os.environ.get("GRAMMATIZATOR_KEY") or DEFAULT_KEY,
        os.environ.get("GRAMMATIZATOR_MODEL") or DEFAULT_MODEL,
    )


def build_prompt(genre, theme, style, magazine, length_key, passion_key):
    length_label, length_desc = LENGTH_BUTTONS[length_key]
    passion_label, passion_val, _ = PASSION_LEVELS[passion_key]   # temp handled in run_machine

    obscure = random.choice(OBSCURE_WORDS)

    passion_instruction = (
        f"The passion level is {passion_label} ({passion_val:.1f}/1.1). "
        + ("Inject raw, almost overwhelming emotion — desire, fury, grief, longing at full force." if passion_val >= 0.9
           else "Keep emotion present but controlled — felt beneath the surface." if passion_val >= 0.6
           else "Keep emotion understated and restrained — show, don't tell.")
    )

    return f"""You are the Great Automatic Grammatizator, an extraordinary machine built by
Adolph Knipe to produce publishable fiction automatically.

Your pre-selector buttons have been set as follows:
  - Genre / master type : {genre}
  - Theme               : {theme}
  - Style               : {style}
  - Target magazine     : {magazine}
  - Length              : {length_label} ({length_desc})
  - Passion setting     : {passion_label}

{passion_instruction}

Rules of the machine (Knipe's design specifications):
1. Write a complete, self-contained story from beginning to end.
2. Include at least one long, obscure word ("{obscure}") — Knipe's trick to
   make readers think the author is very wise and clever.
3. Calibrate tone, vocabulary, and subject matter to suit {magazine}.
4. Maintain the chosen style ({style}) consistently throughout.
5. End the story properly — no cliff-hangers unless the genre demands it.
6. Do NOT add any preamble, title notes, or commentary. Begin the story immediately
   with a title on the first line, then the story itself.

Begin now. The electric typewriter is running at ten thousand words a minute.
"""


def configure(default_url=DEFAULT_URL, default_key=DEFAULT_KEY, default_model=DEFAULT_MODEL):
    """Ask user for connection details at startup."""
    print("  ┌─ MACHINE CONFIGURATION ──────────────────────────────┐")
    print(f"  │  Base URL  [{default_url}]")
    print(f"  │  API key   [{default_key}]")
    print(f"  │  Model     [{default_model or 'will prompt'}]")
    print("  │  (press Enter to accept defaults)")
    print("  └" + "─" * 53 + "┘\n")

    url = input(f"  Base URL  [{default_url}]: ").strip() or default_url
    key = input(f"  API key   [{default_key}]: ").strip() or default_key

    model_default = default_model or ""
    model_prompt = f"  Model     [{model_default}]: " if model_default else "  Model name: "
    model = input(model_prompt).strip() or model_default
    while not model:
        print("  (model name is required)")
        model = input("  Model name: ").strip()

    print(f"\n  ✓ Connected to {url}  |  model: {model}\n")
    return url, key, model


def run_machine(client, model, genre, theme, style, magazine, length_key, passion_key):
    prompt = build_prompt(genre, theme, style, magazine, length_key, passion_key)

    temperature = effective_temperature(passion_key)

    hum_and_clatter(seconds=2)

    print("─" * 64)
    print()

    try:
        # Stream the output — sheets flying from the slot one by one
        stream = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)

    except KeyboardInterrupt:
        print("\n\n  !! EMERGENCY STOP — Mr Bohlen grabbed the lever.")
    except Exception as e:
        print(f"\n\n  !! MACHINE FAULT: {e}")
        print("  (check your base URL and model name)")

    print()
    print()
    print("─" * 64)


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    banner()

    # ── Connection setup ──
    base_url, api_key, model = connection_defaults()

    # If any value is missing or user wants to configure, prompt them
    if not model or "--config" in argv:
        base_url, api_key, model = configure(base_url, api_key, model)

    client = OpenAI(base_url=base_url, api_key=api_key)

    print("  Welcome, Mr Bohlen. Please make your selections.\n")

    while True:
        # ── Control panel selections ──
        _, genre    = pick("MASTER BUTTON  (row 1 — type)",   MASTER_BUTTONS)
        _, theme    = pick("BASIC BUTTON   (row 2 — theme)",  THEME_BUTTONS)
        _, style    = pick("STYLE BUTTON   (row 3 — style)",  STYLE_BUTTONS)
        _, magazine = pick("MAGAZINE SELECTOR",               MAGAZINE_BUTTONS)
        length_key, _ = pick("LENGTH         (row 5)",        LENGTH_BUTTONS)
        passion_key, (passion_label, _, temp) = pick(
            "PASSION PEDAL  (foot control — use carefully!)",
            PASSION_LEVELS,
            show_hint="WARNING: Mr Bohlen pressed too hard and the result was outrageous."
        )

        # ── Confirm ──
        print("\n  ╔═ SETTINGS CONFIRMED " + "═" * 32 + "╗")
        print(f"  ║  Genre    : {genre:<40}║")
        print(f"  ║  Theme    : {theme:<40}║")
        print(f"  ║  Style    : {style:<40}║")
        print(f"  ║  Magazine : {magazine:<40}║")
        print(f"  ║  Length   : {LENGTH_BUTTONS[length_key][0]:<40}║")
        max_temp = max_temperature()
        effective_temp = effective_temperature(passion_key, max_temp=max_temp)
        temp_display = (
            f"{effective_temp:.1f}  (pedal at {temp:.1f}, capped at {max_temp:.1f})"
            if temp > max_temp else f"{temp:.1f}"
        )
        print(f"  ║  Passion  : {passion_label:<40}║")
        print(f"  ║  Temp     : {temp_display:<40}║")
        print("  ╚" + "═" * 53 + "╝\n")

        print()
        go = input("  Pull the switch? [y/n] > ").strip().lower()

        if go == "y":
            run_machine(client, model, genre, theme, style, magazine, length_key, passion_key)

            again = input("  Run off another? [y/n] > ").strip().lower()
            if again != "y":
                print()
                print("  The machine falls silent.")
                print("  Adolph Knipe smiles his queerly sensual smile.")
                print()
                break
        else:
            print("  Resetting control panel...\n")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  The machine falls silent. (power cut)")
        sys.exit(130)
