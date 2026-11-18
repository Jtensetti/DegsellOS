from pathlib import Path
from urllib.parse import unquote, urlsplit
import shutil
import tempfile
from threading import Thread

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib, Gtk

from granskningsfonster import connect_source, review


def window(create, run, verify, domain, coverage, protections):
    app = Gtk.Window(title="ForskarOS – forskningsprojekt")
    app.set_default_size(570, 350)
    app.set_border_width(22)
    layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    app.add(layout)
    current = None
    last = None

    def label(text):
        item = Gtk.Label(label=text, xalign=0, wrap=True, selectable=True)
        layout.pack_start(item, False, False, 0)
        return item

    def row():
        item = Gtk.Box(spacing=8)
        layout.pack_start(item, False, False, 0)
        return item

    def button(group, title, action):
        item = Gtk.Button(label=title)
        item.connect("clicked", lambda _: guarded(action))
        group.pack_start(item, False, False, 0)
        return item

    def guarded(action):
        try:
            action()
        except Exception as error:
            status.set_text(str(error))

    def choose(title, saving=False):
        action = Gtk.FileChooserAction.SAVE if saving else Gtk.FileChooserAction.SELECT_FOLDER
        dialog = Gtk.FileChooserNative.new(title, app, action, "Skapa" if saving else "Välj", "Avbryt")
        if saving:
            dialog.set_current_name("Min studie")
        response = dialog.run()
        path = dialog.get_filename()
        dialog.destroy()
        return Path(path) if response == Gtk.ResponseType.ACCEPT and path else None

    def select_project(folder):
        nonlocal current, last
        if folder is None:
            return
        if not (folder / "underlag/analys.py").is_file() or not (folder / "korningar").is_dir():
            raise ValueError("Välj en projektmapp med underlag och körningar.")
        current = folder
        completed = sorted(p for p in (folder / "korningar").iterdir()
                           if not p.name.startswith(".") and (p / "korning.json").is_file())
        last = completed[-1] if completed else None
        show_heading()
        files.set_sensitive(True)
        imports.set_sensitive(True)
        evidence_group.set_sensitive(True)
        build_group.set_sensitive(True)
        results.set_sensitive(last is not None)
        status.set_text(str(folder))

    def show_heading():
        manifest = domain(current)
        text = f'{current.name} · {"skyddat material" if manifest["skydd"] == "skyddad" else "öppet material"}'
        if last is not None:
            level, why = coverage(last)
            text += f"\nSenaste körningen: {level}. {why}."
        heading.set_text(text)

    def new_project():
        path = choose("Var ska det nya projektet skapas?", saving=True)
        if path is not None:
            select_project(create(method.get_active_id(), path, protection.get_active_id()))

    def open_file(path):
        if not path.exists():
            raise FileNotFoundError(path)
        Gio.AppInfo.launch_default_for_uri(path.as_uri(), None)

    def open_report():
        report = last / "resultat/rapport.html"
        if Gio.AppInfo.get_default_for_type("text/html", False):
            open_file(report)
            return
        # En ny arbetsstation kan sakna Firefox medan grundprofilen installeras.
        gi.require_version("WebKit2", "4.1")
        from gi.repository import WebKit2
        preview = Gtk.Window(title=f"Rapport · {current.name}", transient_for=app)
        preview.set_default_size(840, 650)
        view = WebKit2.WebView.new_with_context(WebKit2.WebContext.new_ephemeral())
        view.get_settings().set_enable_javascript(False)
        table = report.with_name("resultat.csv")
        inputs = (last / "underlag").resolve()

        def navigation(_, decision, kind):
            if kind == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
                uri = decision.get_navigation_action().get_request().get_uri()
                url = urlsplit(uri)
                if url.scheme == "file" and url.netloc == "":
                    source = Path(unquote(url.path)).resolve()
                    if source == table or (source.is_relative_to(inputs) and source.is_file()):
                        decision.ignore()
                        if source.suffix.lower() in (".py", ".csv", ".md", ".txt", ".bib", ".json", ".r"):
                            source_window = Gtk.Window(title=source.name, transient_for=preview)
                            source_window.set_default_size(720, 480)
                            scroll = Gtk.ScrolledWindow()
                            text = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
                            text.get_buffer().set_text(source.read_text(encoding="utf-8-sig", errors="replace"))
                            scroll.add(text)
                            source_window.add(scroll)
                            source_window.show_all()
                        else:
                            guarded(lambda: open_file(source))
                        return True
                if uri.split("#", 1)[0] not in (report.as_uri(), "about:blank", ""):
                    decision.ignore()
                    return True
            return False

        view.connect("decide-policy", navigation)
        preview.add(view)
        preview.show_all()
        view.load_uri(report.as_uri())

    def import_file(name, title):
        picker = Gtk.FileChooserNative.new(title, app, Gtk.FileChooserAction.OPEN, "Välj fil", "Avbryt")
        selected = picker.run()
        source = picker.get_filename()
        picker.destroy()
        if selected != Gtk.ResponseType.ACCEPT or not source:
            return
        target = current / "underlag" / name
        prompt = Gtk.MessageDialog(transient_for=app, modal=True, message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.OK_CANCEL, text=f"Ersätt {name} i arbetsmappen?")
        prompt.format_secondary_text(f"Kopiera {Path(source).name} till {current.name}. Tidigare körningar har egna kopior.")
        accepted = prompt.run()
        prompt.destroy()
        if accepted == Gtk.ResponseType.OK:
            with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
                copied = Path(tmp) / name
                shutil.copyfile(source, copied)
                copied.replace(target)
            status.set_text(f"{Path(source).name} finns nu i projektet som {name}. Granska påståendena mot det nya underlaget.")

    def work(action, building):
        layout.set_sensitive(False)
        status.set_text("Bygger rapporten …" if building else "Kontrollerar underlaget och kör om analysen …")

        def finish(result, error):
            nonlocal last
            layout.set_sensitive(True)
            if error:
                status.set_text(error)
            elif building:
                last = result
                results.set_sensitive(True)
                show_heading()
                status.set_text(f"Rapporten är klar. Körning {last.name}")
            else:
                show_heading()
                status.set_text("Återskapad. Alla resultat har samma SHA-256. Upprepningen är loggad i körningen.")
            return False

        def worker():
            try:
                result = action()
            except Exception as error:
                GLib.idle_add(finish, None, str(error))
            else:
                GLib.idle_add(finish, result, None)
        Thread(target=worker).start()

    def build():
        use_lab = lab.get_active()
        work(lambda: run(current, use_lab), True)

    def repeat_other():
        folder = choose("Välj körningsmappen med korning.json")
        if folder is not None:
            work(lambda: verify(folder), False)

    new = row()
    method = Gtk.ComboBoxText()
    method.append("kvantitativ", "Kvantitativ · observationer")
    method.append("kvalitativ", "Kvalitativ · kodade utdrag")
    method.set_active(0)
    new.pack_start(method, False, False, 0)
    protection = Gtk.ComboBoxText()
    protection.append("öppen", "Öppet material")
    protection.append("skyddad", "Skyddat material")
    protection.set_active(0)
    protection.set_tooltip_text(protections["skyddad"])
    new.pack_start(protection, False, False, 0)
    button(new, "Skapa projekt…", new_project)
    button(new, "Öppna projekt…", lambda: select_project(choose("Välj projektmapp")))
    heading = label("Välj ett befintligt projekt eller skapa ett med exempeldata.")
    files = row()
    button(files, "Öppna data", lambda: open_file(current / "underlag/data.csv"))
    button(files, "Öppna manus", lambda: open_file(current / "underlag/manus.md"))
    button(files, "Visa projektmapp", lambda: open_file(current))
    imports = row()
    button(imports, "Importera CSV…", lambda: import_file("data.csv", "Välj en CSV-fil från kalkylprogram eller Taguette"))
    button(imports, "Importera BibTeX…", lambda: import_file("kallor.bib", "Välj en exporterad BibTeX-fil från Zotero"))
    evidence_group = row()
    button(evidence_group, "Koppla underlag…", lambda: connect_source(app, current / "underlag", status))
    button(evidence_group, "Granska påståenden…", lambda: review(app, current / "underlag"))
    build_group = row()
    button(build_group, "Bygg rapport", build)
    lab = Gtk.CheckButton(label="Kör i versionslåst labb (Podman)")
    build_group.pack_start(lab, False, False, 0)
    results = row()
    button(results, "Öppna sparad rapport", open_report)
    button(results, "Visa körningsmapp", lambda: open_file(last))
    button(results, "Upprepa körning", lambda: work(lambda: verify(last), False))
    button(row(), "Upprepa från annan mapp…", repeat_other)
    status = label("")
    for group in (files, imports, evidence_group, build_group, results):
        group.set_sensitive(False)
    if (Path.cwd() / "underlag/analys.py").is_file():
        guarded(lambda: select_project(Path.cwd()))
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()
