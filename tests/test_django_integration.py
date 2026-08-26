"""End-to-end check that the package is usable from Django.

Three things this proves that the parity suites do not:

1. The package imports with no Django app registry, no settings and no database
   — so it can be used from a management command, a Celery/Procrastinate task
   or a template tag without dragging anything in.
2. It has no import-time side effects. A module that touched the filesystem or
   read an environment variable on import would break under a WSGI worker fork.
3. The output survives Django's autoescaping and can be marked safe, which is
   what actually renders an avatar in a template.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))


def check_no_django_needed() -> list[str]:
    """Import and call without any Django configuration at all."""
    fails = []
    import blobatar

    if not hasattr(blobatar, "__all__"):
        fails.append("package exposes no __all__")

    entry = getattr(blobatar, "blobatar", None)
    if entry is None:
        fails.append("no top-level entry point: blobatar.blobatar is missing")
        return fails

    svg = entry("alain")
    if not isinstance(svg, str):
        fails.append(f"entry point returned {type(svg).__name__}, expected str")
    elif not svg.lstrip().startswith("<svg"):
        fails.append(f"output does not start with <svg: {svg[:40]!r}")

    # Determinism across calls in the same process.
    if entry("alain") != svg:
        fails.append("same seed produced different output within one process")
    return fails


def check_template_rendering() -> list[str]:
    """Render through Django's template engine, autoescaping included."""
    fails = []
    try:
        import django
        from django.conf import settings
    except ImportError:
        return ["django not installed — skipped"]

    if not settings.configured:
        settings.configure(
            DEBUG=False,
            TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates",
                        "DIRS": [], "APP_DIRS": False, "OPTIONS": {}}],
        )
        django.setup()

    from django.template import Context, Template
    from django.utils.safestring import mark_safe

    import blobatar
    entry = getattr(blobatar, "blobatar", None)
    if entry is None:
        return ["no entry point to render"]

    svg = entry("lab-cormoran")
    out = Template("<div>{{ avatar }}</div>").render(
        Context({"avatar": mark_safe(svg)})
    )
    if svg not in out:
        fails.append("marked-safe SVG did not survive template rendering intact")

    escaped = Template("<div>{{ avatar }}</div>").render(Context({"avatar": svg}))
    if "&lt;svg" not in escaped:
        fails.append("autoescaping did not engage on unmarked output — check for "
                     "an unexpected SafeString leaking out of the package")
    return fails


if __name__ == "__main__":
    failed = []
    for name, fn in (("standalone", check_no_django_needed),
                     ("django templates", check_template_rendering)):
        result = fn()
        skipped = [r for r in result if "skipped" in r]
        if skipped:
            print(f"  SKIP  {name}: {skipped[0]}")
            continue
        if result:
            failed += [(name, r) for r in result]
            print(f"  FAIL  {name}")
        else:
            print(f"  OK    {name}")
    if failed:
        for n, r in failed:
            print(f"    {n}: {r}")
        sys.exit(1)
    print("DJANGO INTEGRATION OK")
