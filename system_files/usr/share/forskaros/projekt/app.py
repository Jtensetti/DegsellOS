"""ForskarOS: start, forskningsprojekt och verktyg i ett fönster (GTK 4 och libadwaita).

Designprinciper: docs/DESIGN.md. Varje vy har högst en primär knapp. I ett
projekt är det nästa steg, som räknas ut i oversikt.py. Allt som
kommandoraden forskaros-projekt kan göra finns kvar i rader och i menyn.

  forskaros                       startvyn
  forskaros --projekt MAPP        öppna ett projekt
  forskaros --verktyg             verktygslådan
  forskaros --sjalvtest MAPP      gå igenom alla vyer (för CI), valfritt med
                                  FORSKAROS_SKARMDUMPAR=mapp för PNG-bilder
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import traceback

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Graphene", "1.0")
from gi.repository import Adw, Gdk, Gio, GLib, Graphene, Gtk  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from belagg import add_source, approve, source_choices, source_label  # noqa: E402
from oversikt import (PROJEKTMAPP, STATUS_STYLE, next_step, overview, progress,  # noqa: E402
                      recent_projects, remember_project, suggest_key)
from projekt import create, domain, run, verify  # noqa: E402

APP_ID = "io.github.jtensetti.Forskaros"
PROFILES = Path(os.environ.get("FORSKAROS_PROFILDIR") or HERE.parent / "profiler")
SETUP = HERE.parents[2] / "bin" / "forskaros-setup"
ACTION_LABEL = {"granska": "Granska", "bygg": "Bygg rapport", "upprepa": "Upprepa",
                "rapport": "Öppna rapporten", "manus": "Öppna manus"}

# Appen följer systemets accentfärg och ljusa eller mörka läge (docs/DESIGN.md).
CSS = """
.status { border-radius: 999px; padding: 2px 10px; font-weight: 600; font-size: 0.85em;
          background-color: alpha(currentColor, 0.1); }
.next-step { padding: 24px; }
.step-line { min-height: 1px; min-width: 12px; background-color: alpha(currentColor, 0.2); }
.evidence { padding: 12px 14px; }
.quote { font-style: italic; }
"""


def projects_root():
    return Path(os.environ.get("FORSKAROS_PROJEKTROT") or Path.home() / PROJEKTMAPP)


def config_dir():
    return os.environ.get("FORSKAROS_KONFIG") or GLib.get_user_config_dir()


def label(text, *classes, wrap=True, xalign=0.0, selectable=False, **props):
    item = Gtk.Label(label=text, wrap=wrap, xalign=xalign, selectable=selectable, **props)
    item.set_wrap_mode(2)  # ord och tecken
    if selectable:
        item.set_focusable(False)  # annars markeras hela texten när vyn öppnas
    for cls in classes:
        item.add_css_class(cls)
    return item


def status_pill(text):
    pill = label(text, "status", wrap=False)
    style = STATUS_STYLE.get(text, "")
    if style:
        pill.add_css_class(style)
    pill.set_valign(Gtk.Align.CENTER)
    return pill


def row(title, subtitle="", on_activate=None, suffixes=(), icon=None):
    item = Adw.ActionRow(title=title, subtitle=subtitle, use_markup=False)
    item.set_subtitle_lines(3)
    if icon:
        item.add_prefix(Gtk.Image.new_from_icon_name(icon))
    for suffix in suffixes:
        item.add_suffix(suffix)
    if on_activate:
        item.set_activatable(True)
        item.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
        item.connect("activated", lambda *_: on_activate())
    return item


def flat_button(text, on_click, icon=None):
    button = Gtk.Button(valign=Gtk.Align.CENTER)
    if icon:
        content = Adw.ButtonContent(label=text, icon_name=icon)
        button.set_child(content)
    else:
        button.set_label(text)
    button.add_css_class("flat")
    button.connect("clicked", lambda *_: on_click())
    return button


def primary_button(text, on_click):
    button = Gtk.Button(label=text, halign=Gtk.Align.START)
    button.add_css_class("suggested-action")
    button.add_css_class("pill")
    button.connect("clicked", lambda *_: on_click())
    return button


def stepper(steps):
    """Granska › Bygg › Upprepa › Dela, med klara steg bockade och nästa steg i accentfärg."""
    box = Gtk.Box(spacing=8)
    for index, (name, state) in enumerate(steps):
        if index:
            line = Gtk.Box(valign=Gtk.Align.CENTER, hexpand=True)
            line.add_css_class("step-line")
            box.append(line)
        item = Gtk.Box(spacing=4)
        if state == "klar":
            item.append(Gtk.Image.new_from_icon_name("object-select-symbolic"))
        text = label(name, "caption-heading", wrap=False)
        item.append(text)
        if state == "nu":
            item.add_css_class("accent")
        else:
            item.add_css_class("dim-label")
        spoken = {"klar": "klart", "nu": "nästa steg", "senare": "senare"}[state]
        item.update_property([Gtk.AccessibleProperty.LABEL], [f"{name}: {spoken}"])
        box.append(item)
    return box


def content(title, body, subtitle=None, end=()):
    header = Adw.HeaderBar()
    header.set_title_widget(Adw.WindowTitle(title=title, subtitle=subtitle or ""))
    for widget in end:
        header.pack_end(widget)
    clamp = Adw.Clamp(maximum_size=720, tightening_threshold=560)
    clamp.set_child(body)
    scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
    scroll.set_child(clamp)
    view = Adw.ToolbarView()
    view.add_top_bar(header)
    view.set_content(scroll)
    view.scroll = scroll
    return view


def page(title, body, subtitle=None, end=()):
    return Adw.NavigationPage(child=content(title, body, subtitle, end), title=title)


def column():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
    for side in ("top", "bottom", "start", "end"):
        getattr(box, f"set_margin_{side}")(24)
    return box


def base_status():
    """Grundverktygens installation vid första start. None när den är klar eller utanför ForskarOS."""
    if Path("/var/lib/forskaros/grund.klar").exists() or not Path("/usr/lib/systemd/system/forskaros-grund.service").exists():
        return None
    state = subprocess.run(["systemctl", "show", "forskaros-grund.service", "-p", "SubState", "--value"],
                           capture_output=True, text=True).stdout.strip()
    if state in ("auto-restart", "failed"):
        return "Grundverktygen kunde inte installeras. Kontrollera nätet; ForskarOS försöker igen var annan minut."
    return "Grundverktygen installeras i bakgrunden. Du kan börja arbeta under tiden."


def read_profiles():
    profiles = []
    for path in sorted(PROFILES.glob("*.profil")):
        meta, tools = {}, []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("# ") and ": " in line:
                key, value = line[2:].split(": ", 1)
                meta[key] = value
            elif line.strip() and not line.startswith("#"):
                kind, ident, desc = line.split(None, 2)
                tools.append({"typ": kind, "id": ident, "namn": desc})
        profiles.append({"id": path.stem.split("-", 1)[1], "namn": meta.get("namn", path.stem),
                         "beskrivning": meta.get("beskrivning", ""), "aktivt": meta.get("aktivt-val"), "verktyg": tools})
    return profiles


def flatpaks():
    try:
        return set(subprocess.run(["flatpak", "list", "--app", "--columns=application"],
                                  capture_output=True, text=True, timeout=10).stdout.split())
    except (OSError, subprocess.TimeoutExpired):
        return set()


def installed(profile, listed):
    """Sant när allt i profilen som går att kontrollera finns på datorn."""
    apps = Path.home() / ".local/share/applications"
    for tool in profile["verktyg"]:
        kind, ident = tool["typ"], tool["id"]
        found = {"flatpak": lambda: ident in listed,
                 "webb": lambda: (apps / f'forskaros-webb-{ident.split("|")[0]}.desktop').exists(),
                 }.get(kind, lambda: shutil.which(ident) is not None)()
        if not found:
            return False
    return True


def home_path(path):
    """~/Forskningsprojekt/Studie i stället för hela sökvägen."""
    try:
        return "~/" + str(Path(path).relative_to(Path.home()))
    except ValueError:
        return str(path)


class Window(Adw.ApplicationWindow):
    def __init__(self, app, start):
        super().__init__(application=app, title="ForskarOS", default_width=780, default_height=760)
        self.toasts = Adw.ToastOverlay()
        self.nav = Adw.NavigationView()
        self.toasts.set_child(self.nav)
        self.set_content(self.toasts)
        self.project = None
        self.project_page = None
        self.busy = False
        self.lab = False
        self.banner = None
        self.start = Adw.NavigationPage(title="ForskarOS", tag="start")
        self.start.connect("showing", lambda *_: self.render_start())
        self.render_start()
        self.nav.add(self.start)
        # Läs om projektet när forskaren kommer tillbaka från redigeraren eller kalkylprogrammet.
        self.connect("notify::is-active", lambda *_: self.came_back())
        GLib.timeout_add_seconds(30, self.poll_base)
        if start.get("projekt"):
            self.open_project(Path(start["projekt"]))
        elif start.get("verktyg"):
            self.nav.push(self.tools_page())

    # ---- gemensamt -------------------------------------------------------
    def toast(self, text, button=None, action=None):
        # Bara det senaste beskedet gäller. Äldre besked köas inte upp.
        if getattr(self, "last_toast", None):
            self.last_toast.dismiss()
        item = Adw.Toast(title=text, timeout=6)
        self.last_toast = item
        if button:
            item.set_button_label(button)
            item.connect("button-clicked", lambda *_: action())
        self.toasts.add_toast(item)

    def guarded(self, action):
        try:
            action()
        except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
            self.toast(str(error))

    def open_path(self, path):
        path = Path(path)
        if not path.exists():
            self.toast(f"{path.name} finns inte.")
            return

        def launched(launcher, result):
            try:
                launcher.launch_finish(result)
            except GLib.Error as error:
                if not error.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    self.toast(f"Inget program kunde öppna {path.name}. Installera verktyg under Verktyg.")
        Gtk.FileLauncher.new(Gio.File.new_for_path(str(path))).launch(self, None, launched)

    def alert(self, heading, body, responses, on_response, appearance=None):
        dialog = Adw.AlertDialog(heading=heading, body=body)
        for key, text in responses:
            dialog.add_response(key, text)
        if appearance:
            dialog.set_response_appearance(appearance[0], appearance[1])
            dialog.set_default_response(appearance[0])
        dialog.set_close_response(responses[0][0])
        dialog.connect("response", lambda _d, response: on_response(response))
        dialog.present(self)
        return dialog

    def in_background(self, work, done):
        """Kör work i en tråd och done(resultat, fel) i gränssnittets tråd."""
        def worker():
            try:
                result, error = work(), None
            except Exception as exc:  # visas för forskaren, inte som krasch
                result, error = None, str(exc) or exc.__class__.__name__
            GLib.idle_add(lambda: (done(result, error), False)[1])
        threading.Thread(target=worker, daemon=True).start()

    def came_back(self):
        if not self.is_active() or self.busy:
            return
        visible = self.nav.get_visible_page()
        if visible is self.project_page and self.project is not None:
            self.guarded(self.refresh_project)
        elif visible is self.start:
            self.render_start()

    def poll_base(self):
        """Uppdatera raden om grundverktygen tills installationen är klar."""
        status = base_status()
        if self.banner is not None:
            self.banner.set_revealed(bool(status))
            if status:
                self.banner.set_title(status)
        return bool(status)

    def about(self):
        try:
            version = Path("/usr/share/forskaros/VERSION").read_text(encoding="utf-8").split()[0]
        except (OSError, IndexError):
            version = "utvecklingsversion"
        dialog = Adw.AboutDialog(application_name="ForskarOS", application_icon="forskaros", version=version,
                                 comments="En arbetsmiljö för forskning: frågor, data, analys, granskning och upprepning.",
                                 website="https://github.com/jtensetti/researchos",
                                 license_type=Gtk.License.CUSTOM,
                                 license="ForskarOS är fri programvara. Varje verktyg har sin egen licens.")
        dialog.present(self)

    # ---- start -----------------------------------------------------------
    def render_start(self):
        body = column()
        status = base_status()
        self.banner = Adw.Banner(title=status or "", button_label="Visa logg", revealed=bool(status))
        self.banner.connect("button-clicked", lambda *_: self.show_log())
        body.append(self.banner)
        intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        intro.append(label("Vad vill du arbeta med?", "title-1"))
        intro.append(label("Ett forskningsprojekt håller ihop data, analys, källor och rapport. "
                           "Forskningsmappen i Obsidian är för frågor, hypoteser och anteckningar.", "dim-label"))
        intro.append(primary_button("Nytt forskningsprojekt", lambda: self.nav.push(self.new_project_page())))
        body.append(intro)

        recent = Adw.PreferencesGroup(title="Senaste projekt")
        projects = recent_projects(config_dir())
        if not projects:
            recent.add(row("Inga projekt än", "Skapa ett nytt eller öppna ett befintligt."))
        for project in projects:
            try:
                level = "Skyddat material" if domain(project)["skydd"] == "skyddad" else "Öppet material"
            except ValueError:
                level = "projekt.json behöver rättas"
            recent.add(row(project.name, f"{level} · {project.parent}",
                           on_activate=lambda p=project: self.open_project(p), icon="folder-documents-symbolic"))
        recent.add(row("Öppna annat projekt…", "Välj en mapp med underlag och körningar.",
                       on_activate=self.choose_project, icon="document-open-symbolic"))
        body.append(recent)

        vault = Adw.PreferencesGroup(title="Forskningsmappen")
        vault.add(row("Öppna i Obsidian", "Forskningsfrågor, hypoteser, motprov och ForskarOS Core.",
                      on_activate=self.open_obsidian, icon="accessories-text-editor-symbolic"))
        vault.add(row("Läs Forskarhandboken", "Arbetsmetoden och verktygen, med övningar utan AI.",
                      on_activate=lambda: self.spawn(["forskaros-handbok"]), icon="help-contents-symbolic"))
        vault.add(row("Fokusläge i 50 minuter", "Stänger av notiser och loggar passet.",
                      on_activate=lambda: self.spawn(["forskaros-fokus", "50"]), icon="alarm-symbolic"))
        body.append(vault)

        tools = Adw.PreferencesGroup(title="Verktyg")
        tools.add(row("Välj forskningsverktyg", "Kontor, statistik, skrivande, kvalitativ analys och lokal AI.",
                      on_activate=lambda: self.nav.push(self.tools_page()), icon="applications-science-symbolic"))
        body.append(tools)
        menu = Gio.Menu()
        menu.append("Om ForskarOS", "win.om")
        if not self.lookup_action("om"):
            action = Gio.SimpleAction(name="om")
            action.connect("activate", lambda *_: self.about())
            self.add_action(action)
        more = Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu, tooltip_text="Huvudmeny")
        self.start.set_child(content("ForskarOS", body, end=[more]))

    def spawn(self, argv):
        try:
            subprocess.Popen(argv, start_new_session=True)
        except OSError as error:
            self.toast(f"{argv[0]} kunde inte startas: {error.strerror}")

    def show_log(self):
        out = subprocess.run(["journalctl", "--no-pager", "-u", "forskaros-grund.service", "-n", "15"],
                             capture_output=True, text=True).stdout or "Loggen är tom."
        self.alert("Installationslogg", out, [("ok", "Stäng")], lambda *_: None)

    def choose_project(self):
        dialog = Gtk.FileDialog(title="Välj projektmapp", modal=True)
        if projects_root().is_dir():
            dialog.set_initial_folder(Gio.File.new_for_path(str(projects_root())))

        def chosen(source, result):
            try:
                folder = source.select_folder_finish(result)
            except GLib.Error:
                return
            self.open_project(Path(folder.get_path()))
        dialog.select_folder(self, None, chosen)

    def open_obsidian(self):
        if subprocess.run(["flatpak", "info", "md.obsidian.Obsidian"], capture_output=True).returncode == 0:
            self.spawn(["flatpak", "run", "md.obsidian.Obsidian"])
            self.toast("Första gången: välj Open folder as vault och mappen ForskarOS i din hemkatalog.")
            return
        profile = next((p for p in read_profiles() if p["id"] == "obsidian"), None)
        if profile:
            self.install(profile, then=lambda: self.open_obsidian())

    # ---- nytt projekt ---------------------------------------------------
    def new_project_page(self):
        body = column()
        intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        intro.append(label("Nytt forskningsprojekt", "title-1"))
        intro.append(label("Projektet får exempeldata som du kan prova arbetsflödet med och sedan ersätta med ditt eget material.",
                           "dim-label"))
        body.append(intro)

        names = Adw.PreferencesGroup()
        name = Adw.EntryRow(title="Projektets namn")
        names.add(name)
        body.append(names)

        methods = Adw.PreferencesGroup(title="Metod")
        quantitative = Gtk.CheckButton(active=True)
        qualitative = Gtk.CheckButton(group=quantitative)
        for check, title, subtitle in [
                (quantitative, "Kvantitativ", "Observationer i en tabell, till exempel från Calc. Jämför grupper eller villkor."),
                (qualitative, "Kvalitativ", "Kodade utdrag ur intervjuer eller dokument, till exempel från Taguette.")]:
            item = Adw.ActionRow(title=title, subtitle=subtitle, use_markup=False, activatable_widget=check)
            item.add_prefix(check)
            methods.add(item)
        body.append(methods)

        material = Adw.PreferencesGroup(title="Material")
        protected = Adw.SwitchRow(title="Skyddat material", use_markup=False,
                                  subtitle="Intervjuer eller personuppgifter. Analysen körs utan nätverk och utan åtkomst till hemkatalogen.")
        material.add(protected)
        body.append(material)

        place = Gtk.Box(spacing=6)
        where = label("", "caption", "dim-label", hexpand=True)
        place.append(where)
        root = {"mapp": projects_root()}
        place.append(flat_button("Ändra plats…", lambda: choose_root()))
        body.append(place)
        create_button = primary_button("Skapa projekt", lambda: self.guarded(make))
        body.append(create_button)

        def target():
            text = name.get_text().strip()
            return root["mapp"] / text if text else None

        def valid():
            text = name.get_text().strip()
            return bool(text) and "/" not in text and not text.startswith(".") and not target().exists()

        def refresh(*_):
            path = target()
            create_button.set_sensitive(valid())
            if path is None:
                where.set_text(f"Sparas i {home_path(root['mapp'])}")
            elif path.exists():
                where.set_text(f"Det finns redan en mapp som heter {path.name} där. Välj ett annat namn.")
            elif not valid():
                where.set_text("Namnet kan inte innehålla / eller börja med en punkt.")
            else:
                where.set_text(f"Sparas i {home_path(path)}")

        def choose_root():
            dialog = Gtk.FileDialog(title="Välj var projektet ska sparas", modal=True)

            def chosen(source, result):
                try:
                    root["mapp"] = Path(source.select_folder_finish(result).get_path())
                except GLib.Error:
                    return
                refresh()
            dialog.select_folder(self, None, chosen)

        def make():
            if not valid():
                return
            path = target()
            method = "kvantitativ" if quantitative.get_active() else "kvalitativ"
            path.parent.mkdir(parents=True, exist_ok=True)
            create(method, path, "skyddad" if protected.get_active() else "öppen")
            self.nav.pop()
            self.open_project(path)
            self.toast("Projektet är skapat. Börja med att granska exemplets påståenden.")

        name.connect("changed", refresh)
        name.connect("entry-activated", lambda *_: self.guarded(make))
        refresh()
        self.new_project_widgets = {"name": name, "protected": protected, "create": make}
        return page("Nytt projekt", body)

    # ---- projekt ---------------------------------------------------------
    def open_project(self, folder):
        folder = Path(folder).resolve()
        if not (folder / "underlag").is_dir() or not (folder / "korningar").is_dir():
            self.toast("Välj en projektmapp med underlag och körningar.")
            return
        self.project = folder
        remember_project(config_dir(), folder)
        self.project_page = Adw.NavigationPage(title=folder.name, tag="projekt")
        self.render_project()
        self.nav.push(self.project_page)

    def refresh_project(self):
        if self.project_page is not None:
            self.render_project()

    def render_project(self):
        state = overview(self.project, domain)
        self.state = state
        action, title, why = next_step(state)
        body = column()

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.add_css_class("card")
        card.add_css_class("next-step")
        card.append(stepper(progress(state)))
        card.append(label(title, "title-2", margin_top=8))
        card.append(label(why))
        actions = Gtk.Box(spacing=12)
        self.next_button = primary_button(ACTION_LABEL[action], lambda: self.do(action))
        self.spinner = Gtk.Spinner()
        actions.append(self.next_button)
        actions.append(self.spinner)
        card.append(actions)
        body.append(card)

        claims = Adw.PreferencesGroup(title="Påståenden",
                                      description="Meningar i manuset som är kopplade till data, filer eller källpassager.")
        claims.set_header_suffix(flat_button("Koppla underlag", lambda: self.guarded(lambda: self.nav.push(self.link_page())),
                                             icon="list-add-symbolic"))
        if not state["påståenden"]:
            claims.add(row("Inga kopplade påståenden än",
                           "Välj Koppla underlag och klistra in länken på meningens plats i manuset."))
        for key, claim in state["påståenden"].items():
            claims.add(row(claim["text"], key, on_activate=lambda k=key: self.nav.push(self.claim_page(k)),
                           suffixes=[status_pill(claim["status"])]))
        body.append(claims)

        inputs = Adw.PreferencesGroup(title="Underlag")
        folder = self.project / "underlag"
        inputs.add(row("Data", "data.csv · öppnas i kalkylprogrammet", on_activate=lambda: self.open_path(folder / "data.csv"),
                       suffixes=[flat_button("Importera…", lambda: self.import_file("data.csv", "Välj en CSV-fil"))],
                       icon="x-office-spreadsheet-symbolic"))
        inputs.add(row("Manus", "manus.md · frågan, förutsägelsen och tolkningen", on_activate=lambda: self.open_path(folder / "manus.md"),
                       icon="x-office-document-symbolic"))
        inputs.add(row("Källor", "kallor.bib · exporterad från Zotero", on_activate=lambda: self.open_path(folder / "kallor.bib"),
                       suffixes=[flat_button("Importera…", lambda: self.import_file("kallor.bib", "Välj en BibTeX-fil från Zotero"))],
                       icon="accessories-dictionary-symbolic"))
        inputs.add(row("Analys", "analys.py · det som körs i varje körning", on_activate=lambda: self.open_path(folder / "analys.py"),
                       icon="text-x-script-symbolic"))
        body.append(inputs)

        runs = Adw.PreferencesGroup(title="Körningar",
                                    description="Varje körning sparar underlag, resultat och rapport. Dokumenterad, återkörbar eller återkörd visar hur säker den är.")
        if not state["körningar"]:
            runs.add(row("Inga körningar än", "Bygg rapporten för att skapa den första."))
        newest = list(reversed(state["körningar"]))
        target = runs
        for index, item in enumerate(newest):
            if index == 3:
                target = Adw.ExpanderRow(title=f"Äldre körningar ({len(newest) - 3})")
                runs.add(target)
            line = row(item["namn"], item["varför"], suffixes=[
                status_pill(item["nivå"]),
                flat_button("Rapport", lambda r=item["mapp"]: self.open_report(r)),
                flat_button("Upprepa", lambda r=item["mapp"]: self.repeat(r))])
            (target.add_row if isinstance(target, Adw.ExpanderRow) else target.add)(line)
        body.append(runs)

        menu = Gio.Menu()
        menu.append("Bygg rapport", "win.bygg")
        menu.append("Kör i versionslåst labb", "win.labb")
        menu.append("Upprepa en körning från annan mapp…", "win.upprepa-annan")
        menu.append("Visa projektmappen", "win.projektmapp")
        menu.append("Uppdatera", "win.uppdatera")
        self.install_actions()
        more = Gtk.MenuButton(icon_name="open-menu-symbolic", menu_model=menu, tooltip_text="Mer")
        subtitle = "Skyddat material" if state["skydd"] == "skyddad" else "Öppet material"
        old = self.project_page.get_child()
        offset = old.scroll.get_vadjustment().get_value() if old else 0
        view = content(state["namn"], body, subtitle=subtitle, end=[more])
        self.project_page.set_child(view)
        # Behåll läsplatsen när vyn byggs om efter en granskning eller körning.
        GLib.idle_add(lambda: view.scroll.get_vadjustment().set_value(offset) and False)
        self.project_page.set_title(state["namn"])

    def install_actions(self):
        if getattr(self, "_actions", False):
            return
        self._actions = True
        for name, handler in [("bygg", lambda: self.do("bygg")), ("upprepa-annan", self.repeat_other),
                              ("projektmapp", lambda: self.open_path(self.project)), ("uppdatera", self.refresh_project)]:
            action = Gio.SimpleAction(name=name)
            action.connect("activate", lambda *_a, h=handler: h())
            self.add_action(action)
        lab = Gio.SimpleAction.new_stateful("labb", None, GLib.Variant.new_boolean(False))

        def toggle(action, _):
            self.lab = not action.get_state().get_boolean()
            action.set_state(GLib.Variant.new_boolean(self.lab))
            self.toast("Nästa körning görs i det versionslåsta labbet." if self.lab else "Nästa körning görs lokalt.")
        lab.connect("activate", toggle)
        self.add_action(lab)

    def set_busy(self, busy):
        self.busy = busy
        if hasattr(self, "next_button"):
            self.next_button.set_sensitive(not busy)
            self.spinner.set_spinning(busy)

    def do(self, action):
        if self.busy:
            return
        if action == "granska":
            first = next((k for k, c in self.state["påståenden"].items() if c["status"] != "Granskad"), None)
            if first:
                self.nav.push(self.claim_page(first, series=True))
        elif action == "bygg":
            self.set_busy(True)
            project, lab = self.project, self.lab
            self.in_background(lambda: run(project, lab), self.built)
        elif action == "upprepa":
            self.repeat(self.state["körningar"][-1]["mapp"])
        elif action == "rapport":
            self.open_report(self.state["körningar"][-1]["mapp"])
        elif action == "manus":
            self.open_path(self.project / "underlag/manus.md")

    def built(self, result, error):
        self.set_busy(False)
        if error:
            self.toast(error)
            return
        self.refresh_project()
        self.toast("Rapporten är klar.", "Öppna", lambda: self.open_report(result))

    def repeat(self, folder):
        if self.busy:
            return
        self.set_busy(True)

        def done(_, error):
            self.set_busy(False)
            self.refresh_project()
            self.toast(error or "Upprepad: alla resultat har samma SHA-256.")
        self.in_background(lambda: verify(Path(folder)), done)

    def repeat_other(self):
        dialog = Gtk.FileDialog(title="Välj körningsmappen med korning.json", modal=True)

        def chosen(source, result):
            try:
                folder = Path(source.select_folder_finish(result).get_path())
            except GLib.Error:
                return
            self.repeat(folder)
        dialog.select_folder(self, None, chosen)

    def open_report(self, folder):
        report = Path(folder) / "resultat/rapport.html"
        if Gio.AppInfo.get_default_for_type("text/html", False):
            self.open_path(report)
        else:
            # En ny dator kan sakna webbläsare medan grundverktygen installeras.
            self.spawn([sys.executable, "-I", str(HERE / "rapportvy.py"), str(report)])

    def import_file(self, name, title):
        dialog = Gtk.FileDialog(title=title, modal=True)

        def chosen(source, result):
            try:
                picked = Path(source.open_finish(result).get_path())
            except GLib.Error:
                return

            def replace(response):
                if response != "ersatt":
                    return
                target = self.project / "underlag" / name
                tmp = target.with_name(f".{name}.tmp")
                tmp.write_bytes(picked.read_bytes())
                tmp.replace(target)
                self.refresh_project()
                self.toast(f"{picked.name} är nu {name}. Granska påståendena mot det nya underlaget.")
            self.alert(f"Ersätt {name}?", f"{picked.name} kopieras in i projektet. Tidigare körningar har egna kopior.",
                       [("avbryt", "Avbryt"), ("ersatt", "Ersätt")], replace,
                       appearance=("ersatt", Adw.ResponseAppearance.SUGGESTED))
        dialog.open(self, None, chosen)

    # ---- påstående -------------------------------------------------------
    def claim_page(self, key, series=False):
        """Ett påstående med sitt underlag. I en serie (knappen Granska) går Bekräfta vidare till nästa."""
        claim = self.state["påståenden"][key]
        pending = [k for k, c in self.state["påståenden"].items() if c["status"] != "Granskad"]
        body = column()
        head = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        head.append(label(claim["text"], "title-2", selectable=True))
        pill_row = Gtk.Box(spacing=8)
        pill_row.append(status_pill(claim["status"]))
        if claim["tidigare"]:
            pill_row.append(label(f'Senast granskat {claim["tidigare"]["tid"][:16].replace("T", " ")} UTC', "caption", "dim-label"))
        head.append(pill_row)
        if claim["ändrat"]:
            head.append(label("Ändrat sedan granskningen: " + "; ".join(claim["ändrat"])))
        if claim["kommentar"]:
            head.append(label(claim["kommentar"], "dim-label"))
        body.append(head)

        for item in claim["underlag"]:
            spec = item["spec"]
            group = Adw.PreferencesGroup(title=source_label(spec))
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.add_css_class("card")
            box.add_css_class("evidence")
            if item["fel"]:
                box.append(label(item["fel"], "error"))
            elif "källa" in spec:
                box.append(label("»" + " ".join(spec["citat"].split()) + "«", "quote", selectable=True))
                box.append(label(item.get("titel") or spec["källa"], "caption", "dim-label"))
            elif "sha256" in item:
                box.append(label(f'Hela filen · SHA-256 {item["sha256"][:16]}…', "caption", "monospace"))
            else:
                lines = ["\t".join(spec["kolumner"])] + ["\t".join(r) for r in item["rader"][:40]]
                box.append(label(f'{len(item["rader"])} matchande rader', "caption", "dim-label"))
                box.append(label("\n".join(lines), "monospace", selectable=True))
            group.add(box)
            body.append(group)

        can_confirm = claim["status"] in ("Ej granskad", "Ompröva")
        confirm = primary_button("Bekräfta granskning", lambda: self.guarded(lambda: confirm_review()))
        confirm.set_sensitive(can_confirm)
        buttons = Gtk.Box(spacing=12)
        buttons.append(confirm)
        folder = self.project / "underlag"
        if claim["status"] == "Ompröva":
            # Håller inte påståendet längre ändrar forskaren meningen i stället för att bekräfta.
            buttons.append(flat_button("Ändra meningen i manus", lambda: self.open_path(folder / "manus.md")))
        elif claim["status"] == "Underlag saknas":
            buttons.append(flat_button("Öppna belagg.json", lambda: self.open_path(folder / "belagg.json")))
        body.append(buttons)
        hint = {"Granskad": "Granskningen gäller det underlag som visas här.",
                "Underlag saknas": "Laga kopplingen i belagg.json eller lägg tillbaka underlaget. Sedan kan påståendet granskas."}
        body.append(label(hint.get(claim["status"], "Du bekräftar att underlaget ovan stöder meningen. "
                          "Ändras underlaget senare visas påståendet som Ompröva."), "caption", "dim-label"))

        def confirm_review():
            approve(self.project / "underlag", key, claim["avtryck"])
            self.nav.pop()
            self.refresh_project()
            remaining = [k for k, c in self.state["påståenden"].items() if c["status"] in ("Ej granskad", "Ompröva")]
            if series and remaining:
                self.nav.push(self.claim_page(remaining[0], series=True))
            elif remaining:
                self.toast("Granskningen är sparad.", "Nästa", lambda: self.nav.push(self.claim_page(remaining[0])))
            else:
                self.toast("Alla påståenden är granskade.")
        self.claim_widgets = {"confirm": confirm_review}
        place = f"{pending.index(key) + 1} av {len(pending)} att granska" if series and key in pending else "Påstående"
        return page(key, body, subtitle=place)

    # ---- koppla underlag -------------------------------------------------
    def link_page(self):
        folder = self.project / "underlag"
        choices = source_choices(folder)
        if not choices:
            raise ValueError("Lägg först en fil eller källa i projektets underlag.")
        body = column()
        body.append(label("Koppla en mening i manuset till det den bygger på. Länken kopieras, och du klistrar in den på meningens plats.",
                          "dim-label"))
        group = Adw.PreferencesGroup()
        text = Adw.EntryRow(title="Meningen i manuset")
        source = Adw.ComboRow(title="Underlag", model=Gtk.StringList.new([c[0] for c in choices]))
        roles = ["stöd", "motbelägg", "metod"]
        role = Adw.ComboRow(title="Roll", model=Gtk.StringList.new(roles))
        quote = Adw.EntryRow(title="Citat ur källan, ordagrant")
        where = Adw.EntryRow(title="Sida, till exempel s. 12")
        for widget in (text, source, role, quote, where):
            group.add(widget)
        body.append(group)
        advanced = Adw.PreferencesGroup(description="ID:t står i länken. Ett befintligt ID lägger till underlag till det påståendet.")
        key = Adw.EntryRow(title="ID i länken")
        advanced.add(key)
        body.append(advanced)
        save = primary_button("Spara och kopiera länk", lambda: self.guarded(lambda: store()))
        body.append(save)
        try:
            taken = set(json.loads((folder / "belagg.json").read_text(encoding="utf-8"))["påståenden"])
        except (OSError, ValueError, KeyError):
            taken = set()
        suggested = {"key": ""}

        def propose(*_):
            # Föreslå ett ID tills forskaren skriver ett eget.
            if key.get_text() == suggested["key"]:
                suggested["key"] = suggest_key(text.get_text(), taken) if text.get_text().strip() else ""
                key.set_text(suggested["key"])
        text.connect("changed", propose)

        def passage(*_):
            is_source = "källa" in choices[source.get_selected()][1]
            quote.set_visible(is_source)
            where.set_visible(is_source)
        source.connect("notify::selected", passage)
        passage()

        def store():
            name, sentence = key.get_text().strip(), text.get_text().strip()
            if not sentence:
                raise ValueError("Skriv meningen som ska stå i manuset.")
            spec = dict(choices[source.get_selected()][1], roll=roles[role.get_selected()])
            if "källa" in spec:
                spec["citat"] = quote.get_text().strip()
                if where.get_text().strip():
                    spec["sida"] = where.get_text().strip()
                for suffix in (".md", ".txt"):
                    if (folder / "kallor" / (spec["källa"] + suffix)).is_file():
                        spec["fil"] = f'kallor/{spec["källa"]}{suffix}'
                        break
            add_source(folder, name, spec)
            escaped = "".join("\\" + c if c in r"\[]*_<>$~^`" else c for c in sentence)
            link = f"[{escaped}](#belagg-{name})"
            self.get_clipboard().set_content(Gdk.ContentProvider.new_for_value(link))
            self.last_link = link
            self.nav.pop()
            self.refresh_project()
            self.toast("Länken är kopierad. Klistra in den på meningens plats i manus.md.", "Öppna manus",
                       lambda: self.open_path(folder / "manus.md"))
        self.link_widgets = {"key": key, "text": text, "source": source, "quote": quote, "where": where,
                             "choices": choices, "store": store}
        return page("Koppla underlag", body)

    # ---- verktyg ---------------------------------------------------------
    def tools_page(self):
        body = column()
        intro = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        intro.append(label("Forskningsverktyg", "title-1"))
        intro.append(label("Öppna verktyg installeras från Flathub och Homebrew. Grundprofilen installeras automatiskt vid första start. "
                           "Obsidian och molntjänsterna installeras bara om du väljer dem.", "dim-label"))
        body.append(intro)
        group = Adw.PreferencesGroup()
        profiles = read_profiles()
        listed = flatpaks()
        done = {p["id"] for p in profiles if installed(p, listed)}
        for profile in profiles:
            expander = Adw.ExpanderRow(title=profile["namn"], subtitle=profile["beskrivning"])
            expander.set_subtitle_lines(3)
            for tool in profile["verktyg"]:
                name, _, about = tool["namn"].partition(" – ")
                expander.add_row(row(name, about))
            if profile["id"] in done:
                expander.add_suffix(label("Installerad", "caption", "dim-label", wrap=False))
            else:
                button = Gtk.Button(label="Installera", valign=Gtk.Align.CENTER)
                button.connect("clicked", lambda _b, p=profile, b=button: self.install(p, button=b))
                expander.add_suffix(button)
            group.add(expander)
        body.append(group)
        body.append(label("Samma val finns i terminalen: forskaros-setup --lista", "caption", "dim-label"))
        return page("Verktyg", body)

    def install(self, profile, button=None, then=None):
        def go(response):
            if response not in ("installera",):
                return
            if button:
                button.set_sensitive(False)
                button.set_label("Installerar…")
            argv = [str(SETUP) if SETUP.exists() else "forskaros-setup", "--profil", profile["id"], "--ja"]
            if profile["aktivt"]:
                argv.append("--godkänt")  # forskaren har gjort det aktiva valet i dialogen

            def done(result, error):
                if button:
                    button.set_sensitive(True)
                    button.set_label("Installera")
                if error or result.returncode:
                    lines = [] if error else (result.stderr or result.stdout).strip().splitlines()
                    detail = error or (lines[-1] if lines else "okänt fel")
                    self.toast(f'{profile["namn"]} kunde inte installeras: {detail}')
                    return
                if button:
                    button.set_label("Installerat")
                    button.set_sensitive(False)
                self.toast(f'{profile["namn"]} är installerat.')
                if then:
                    then()
            self.toast(f'Installerar {profile["namn"]}. Det kan ta några minuter; du kan arbeta under tiden.')
            self.in_background(lambda: subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL), done)

        tools = ", ".join(t["namn"].split(" – ")[0] for t in profile["verktyg"])
        if profile["aktivt"] == "moln":
            self.alert("Använda AI-tjänster i molnet?",
                       f"{tools} skickar det du skriver till tjänsterna. Lägg inte in personuppgifter eller skyddat material. "
                       "ForskarOS skapar genvägar; tjänsterna har egna villkor.",
                       [("avbryt", "Avbryt"), ("installera", "Jag väljer molntjänsterna")], go,
                       appearance=("installera", Adw.ResponseAppearance.DESTRUCTIVE))
        elif profile["aktivt"] == "licens":
            self.alert(f'Installera {profile["namn"]}?',
                       f'{profile["beskrivning"]} Du godkänner programmets licensvillkor.',
                       [("avbryt", "Avbryt"), ("installera", "Installera")], go,
                       appearance=("installera", Adw.ResponseAppearance.SUGGESTED))
        else:
            go("installera")


# ---- skärmdumpar och självtest -------------------------------------------
def screenshot(window, path):
    """PNG av fönstrets innehåll som det senast ritades. False om det inte är ritat än."""
    widget = window.get_content()
    width, height = widget.get_width(), widget.get_height()
    snap = Gtk.Snapshot()
    Gtk.WidgetPaintable.new(widget).snapshot(snap, width, height)
    node = snap.to_node()
    if node is None:
        return False
    texture = window.get_renderer().render_texture(node, Graphene.Rect().init(0, 0, width, height))
    texture.save_to_png(str(path))
    return True


def selftest(window, app):
    """Gå igenom alla vyer med ett riktigt projekt. Avslutar med kod 1 vid fel.

    Varje steg är (skärmdump, åtgärd). Skärmdumpen tas innan åtgärden, när
    vyn har ritats färdigt. En åtgärd som returnerar "vänta" körs igen.
    """
    shots = os.environ.get("FORSKAROS_SKARMDUMPAR")
    failures = []
    settings = Gtk.Settings.get_default()
    settings.set_property("gtk-enable-animations", False)
    settings.set_property("gtk-cursor-blink", False)

    def start():
        assert window.nav.get_visible_page() is window.start
        window.nav.push(window.new_project_page())

    def fill_new():
        widgets = window.new_project_widgets
        widgets["name"].set_text("Hypotesbyten efter återkoppling")
        widgets["protected"].set_active(True)

    def create_project():
        window.new_project_widgets["create"]()
        assert window.project is not None and window.state["skydd"] == "skyddad"
        assert next_step(window.state)[0] == "granska"

    def review_first():
        window.do("granska")

    def confirm():
        window.claim_widgets["confirm"]()

    def review_rest():
        for _ in range(len(window.state["påståenden"])):  # serien går vidare av sig själv
            if all(c["status"] == "Granskad" for c in window.state["påståenden"].values()):
                break
            window.claim_widgets["confirm"]()
        assert window.nav.get_visible_page() is window.project_page, "serien ska sluta i projektet"
        assert next_step(window.state)[0] == "bygg", next_step(window.state)
        window.do("bygg")

    def wait_build():
        if window.busy:
            return "vänta"
        assert window.state["körningar"], "ingen körning byggdes"
        assert next_step(window.state)[0] == "upprepa", next_step(window.state)

    def open_link():
        window.nav.push(window.link_page())

    def fill_link():
        widgets = window.link_widgets
        index = next(i for i, (text, _) in enumerate(widgets["choices"]) if text.startswith("Källpassage"))
        widgets["source"].set_selected(index)
        widgets["text"].set_text("Även intervjuerna i exemplet är konstruerade.")
        assert widgets["key"].get_text() == "aven-intervjuerna-exemplet", widgets["key"].get_text()
        widgets["quote"].set_text("De kommer inte från verkliga intervjuer.")
        widgets["where"].set_text("s. 1")
        assert widgets["quote"].get_visible()

    def store_link():
        window.link_widgets["store"]()
        assert "#belagg-aven-intervjuerna-exemplet" in window.last_link

    def tools():
        window.nav.push(window.tools_page())

    def changed_data():
        # Som när forskaren rättar data i kalkylprogrammet och går tillbaka till ForskarOS.
        window.nav.pop_to_page(window.project_page)
        data = window.project / "underlag/data.csv"
        data.write_text(data.read_text(encoding="utf-8").replace("Saklig respons,1", "Saklig respons,0", 1),
                        encoding="utf-8")
        window.refresh_project()
        assert next_step(window.state)[:2] == ("granska", "1 påstående att ompröva"), next_step(window.state)

    def reconsider():
        window.do("granska")
        assert window.state["påståenden"]["saklig"]["status"] == "Ompröva"

    steps = [("1-start", start), (None, fill_new), ("2-nytt-projekt", create_project),
             ("3-projekt", review_first), ("4-pastaende", confirm), (None, review_rest), (None, wait_build),
             ("5-projekt-efter-korning", open_link), (None, fill_link), ("6-koppla-underlag", store_link),
             (None, tools), ("7-verktyg", changed_data), ("8-ompröva", reconsider), ("9-ompröva-påstående", None)]

    def tick():
        if not steps:
            window.selftest_done = True
            app.quit()
            return False
        name, action = steps[0]
        try:
            if name and shots:
                if getattr(window, "last_toast", None):
                    # Beskeden är provade i stegen. Bilderna visar vyn utan dem.
                    window.last_toast.dismiss()
                    window.last_toast = None
                    return True
                Path(shots).mkdir(parents=True, exist_ok=True)
                if not screenshot(window, Path(shots) / f"{name}.png"):
                    return True  # inte ritat än
            if action is None or action() != "vänta":
                steps.pop(0)
            elif name:
                steps[0] = (None, action)
        except Exception:
            failures.append(traceback.format_exc())
            app.quit()
            return False
        return True

    window.selftest_failures = failures
    GLib.timeout_add(400, tick)


def main(argv):
    start, test_dir = {}, None
    args = iter(argv[1:])
    for arg in args:
        if arg == "--projekt":
            start["projekt"] = next(args)
        elif arg == "--verktyg":
            start["verktyg"] = True
        elif arg == "--sjalvtest":
            test_dir = Path(next(args))
            os.environ["FORSKAROS_PROJEKTROT"] = str(test_dir / PROJEKTMAPP)
            os.environ["FORSKAROS_KONFIG"] = str(test_dir / "konfig")
    app = Adw.Application(application_id=APP_ID, flags=Gio.ApplicationFlags.NON_UNIQUE)
    holder = {}

    def activate(application):
        provider = Gtk.CssProvider()
        css = CSS
        if test_dir and os.environ.get("FORSKAROS_ACCENT") and Adw.get_minor_version() < 6:
            # Bara för skärmbilder: libadwaita före 1.6 saknar GNOME:s accentfärger,
            # så självtestet kan lägga in ForskarOS accentfärg för hand.
            fill, _, text = os.environ["FORSKAROS_ACCENT"].partition(",")
            css += f"@define-color accent_bg_color {fill}; @define-color accent_color {text or fill};"
        provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        window = Window(application, start)
        holder["window"] = window
        quit_action = Gio.SimpleAction(name="avsluta")
        quit_action.connect("activate", lambda *_: application.quit())
        application.add_action(quit_action)
        for action, keys in [("win.bygg", ["<Control>b"]), ("app.avsluta", ["<Control>q"])]:
            application.set_accels_for_action(action, keys)
        window.present()
        if test_dir:
            selftest(window, application)

    def guarded_activate(application):
        try:
            activate(application)
        except Exception:
            holder["fel"] = traceback.format_exc()
            application.quit()

    app.connect("activate", guarded_activate)
    code = app.run([argv[0]])
    window = holder.get("window")
    failures = ([holder["fel"]] if "fel" in holder else []) + getattr(window, "selftest_failures", [])
    if test_dir and not failures and not getattr(window, "selftest_done", False):
        failures.append("Självtestet avslutades innan alla vyer var genomgångna.")
    if failures:
        print(failures[0], file=sys.stderr)
        return 1
    if test_dir:
        print("OK: ForskarOS-appen: start, nytt projekt, granskning, körning, koppla underlag, verktyg")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
