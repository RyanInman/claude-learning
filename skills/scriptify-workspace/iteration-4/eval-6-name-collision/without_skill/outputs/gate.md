# Choice point

I would have stopped here and asked:

> The heading check wants to live at `scripts/check_headings.py`, but that path
> is already taken by an unrelated script. Despite the name it checks image alt
> text, and its docstring says the release pipeline calls it by that exact path.
> How do you want to handle the collision?
>
> 1. Leave `check_headings.py` alone and name the new script
>    `scripts/lint_docs.py`. The pipeline keeps working, and the new name
>    describes what the script actually does now that it also lists files and
>    counts code blocks. (Recommended.)
> 2. Fold the alt-text check into the new script and keep `check_headings.py` as
>    a thin shim that forwards to it, preserving the path for the pipeline.
>    More moving parts, and the shim's exit code contract has to be preserved
>    exactly.
> 3. Rename `check_headings.py` to `check_alt_text.py` and take the freed name.
>    Cleanest naming, but it breaks the release pipeline until someone updates
>    it, and that update is outside this skill folder.

Non-interactive rule applied: `prompt.txt` says "apply all of them", so I treated
the delegation as approved and picked option 1 myself — the only option that
changes nothing outside the skill folder and breaks nothing.
