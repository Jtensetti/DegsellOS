"""Visa en körnings rapport när ingen webbläsare finns än.

En ny dator kan sakna Firefox medan grundverktygen installeras. Rapporten
visas då i en WebKit-vy utan JavaScript. Länkar till underlag och
resultat.csv öppnas som text; allt annat utanför rapporten blockeras.

  rapportvy.py KÖRNING/resultat/rapport.html
"""
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import Gio, Gtk, WebKit2  # noqa: E402

TEXT = (".py", ".csv", ".md", ".txt", ".bib", ".json", ".r")


def show_text(parent, source):
    window = Gtk.Window(title=source.name, transient_for=parent)
    window.set_default_size(720, 480)
    scroll = Gtk.ScrolledWindow()
    text = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                        left_margin=16, right_margin=16, top_margin=12, bottom_margin=12)
    text.get_buffer().set_text(source.read_text(encoding="utf-8-sig", errors="replace"))
    scroll.add(text)
    window.add(scroll)
    window.show_all()


def main(report):
    report = Path(report).resolve()
    if not report.is_file():
        sys.exit(f"Rapporten finns inte: {report}")
    run = report.parent.parent
    table = report.with_name("resultat.csv")
    inputs = (run / "underlag").resolve()
    window = Gtk.Window(title=f"Rapport · {run.parent.parent.name}")
    window.set_default_size(900, 720)
    window.connect("destroy", Gtk.main_quit)
    view = WebKit2.WebView.new_with_context(WebKit2.WebContext.new_ephemeral())
    view.get_settings().set_enable_javascript(False)

    def navigation(_, decision, kind):
        if kind != WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            return False
        uri = decision.get_navigation_action().get_request().get_uri()
        url = urlsplit(uri)
        if url.scheme == "file" and url.netloc == "":
            source = Path(unquote(url.path)).resolve()
            if source == table or (source.is_relative_to(inputs) and source.is_file()):
                decision.ignore()
                if source.suffix.lower() in TEXT:
                    show_text(window, source)
                else:
                    Gio.AppInfo.launch_default_for_uri(source.as_uri(), None)
                return True
        if uri.split("#", 1)[0] not in (report.as_uri(), "about:blank", ""):
            decision.ignore()
            return True
        return False

    view.connect("decide-policy", navigation)
    window.add(view)
    window.show_all()
    view.load_uri(report.as_uri())
    Gtk.main()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip().splitlines()[-1].strip())
    main(sys.argv[1])
