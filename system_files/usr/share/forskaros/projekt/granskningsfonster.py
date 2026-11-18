"""Skrivbordsvyer för att koppla och granska påståenden i arbetsmappen."""
from gi.repository import Gdk, Gtk

from belagg import add_source, approve, detail, inspect, read_json, source_choices


def review(parent, folder):
    claims = inspect(folder)
    if not claims:
        raise ValueError("Manuset saknar länkade påståenden. Välj Koppla underlag och lägg länken i manus.md.")
    dialog = Gtk.Dialog(title="Granska påståenden", transient_for=parent, modal=True)
    dialog.set_default_size(730, 540)
    dialog.add_button("Stäng", Gtk.ResponseType.CLOSE)
    confirm = dialog.add_button("Bekräfta granskning", Gtk.ResponseType.APPLY)
    box = dialog.get_content_area()
    box.set_border_width(14)
    box.set_spacing(8)
    menu = Gtk.ComboBoxText()
    box.pack_start(menu, False, False, 0)
    def fill_menu(active):
        menu.remove_all()
        for key, item in claims.items():
            menu.append(key, f'{item["status"]} · {key}')
        if claims:
            menu.set_active_id(active if active in claims else next(iter(claims)))
    view = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD_CHAR, cursor_visible=False)
    scroll = Gtk.ScrolledWindow()
    scroll.add(view)
    box.pack_start(scroll, True, True, 0)
    message = Gtk.Label(xalign=0, wrap=True)
    box.pack_start(message, False, False, 0)

    def display(*_):
        if menu.get_active_id() not in claims:
            return
        item = claims[menu.get_active_id()]
        view.get_buffer().set_text(detail(item))
        confirm.set_sensitive(item["status"] not in ("Granskad", "Underlag saknas"))

    menu.connect("changed", display)
    fill_menu(next(iter(claims)))
    dialog.show_all()
    try:
        while dialog.run() == Gtk.ResponseType.APPLY:
            key = menu.get_active_id()
            try:
                approve(folder, key, claims[key]["avtryck"])
                message.set_text("Granskningen är sparad. Bygg rapporten för att dela den här versionen.")
            except ValueError as error:
                message.set_text(str(error))
            claims = inspect(folder)
            if key not in claims:
                break
            fill_menu(key)
    finally:
        dialog.destroy()


def connect_source(parent, folder, status):
    choices = source_choices(folder)
    if not choices:
        raise ValueError("Lägg först en källa i projektets underlag.")
    path = folder / "belagg.json"
    known = read_json(path)["påståenden"] if path.exists() else {}
    linked = inspect(folder)
    dialog = Gtk.Dialog(title="Koppla underlag till ett påstående", transient_for=parent, modal=True)
    dialog.set_default_size(590, 325)
    dialog.add_button("Avbryt", Gtk.ResponseType.CANCEL)
    dialog.add_button("Spara koppling och kopiera länk", Gtk.ResponseType.OK)
    grid = Gtk.Grid(column_spacing=12, row_spacing=12, border_width=16)
    dialog.get_content_area().add(grid)
    key = Gtk.ComboBoxText.new_with_entry()
    for name in known:
        key.append_text(name)
    key.get_child().set_placeholder_text("Ett eget ID, exempelvis observation-1")
    title = Gtk.Entry(placeholder_text="Meningen som ska stå i manuset")
    key.connect("changed", lambda _: title.set_text(linked[key.get_active_text()]["text"])
                if key.get_active_text() in linked else None)
    source = Gtk.ComboBoxText()
    for label, _ in choices:
        source.append_text(label)
    source.set_active(0)
    role = Gtk.ComboBoxText()
    for value in ("stöd", "motbelägg", "metod"):
        role.append_text(value)
    role.set_active(0)
    for index, (label, widget) in enumerate([("Påståendets ID", key), ("Länktext", title),
                                            ("Underlag", source), ("Roll", role)]):
        grid.attach(Gtk.Label(label=label, xalign=0), 0, index, 1, 1)
        grid.attach(widget, 1, index, 1, 1)
        widget.set_hexpand(True)
    message = Gtk.Label(xalign=0, wrap=True, label="Klistra sedan in länken på meningens plats i manus.md.")
    grid.attach(message, 0, 4, 2, 1)
    dialog.show_all()
    try:
        while dialog.run() == Gtk.ResponseType.OK:
            name = key.get_child().get_text().strip()
            text = title.get_text().strip()
            if not text:
                message.set_text("Ange en mening att länka från.")
                continue
            try:
                add_source(folder, name, dict(choices[source.get_active()][1], roll=role.get_active_text()))
            except ValueError as error:
                message.set_text(str(error))
                continue
            # Skydda Markdown-tecken så att den valda meningen förblir vanlig länktext.
            escaped = "".join("\\" + c if c in r"\[]*_<>$~^`" else c for c in text)
            link = f"[{escaped}](#belagg-{name})"
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(link, -1)
            clipboard.store()
            status.set_text(f"Kopplingen är sparad. Länken till {name} är kopierad till urklipp.")
            break
    finally:
        dialog.destroy()
