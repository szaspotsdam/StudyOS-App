import sys
import glob
import serial
import tkinter as tk
from tkinter import messagebox, ttk
import json

# Globale Variable für die serielle Verbindung
ser = None
disconnect_button = None  # Globale Referenz für den Disconnect-Button
data_dict = {}  # Dictionary zum Zwischenspeichern der gescannten Daten und Namen

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def open_port_selection():
    # Popup-Fenster für die Auswahl des Ports erstellen
    popup = tk.Toplevel(root)
    popup.title("Port Auswahl")
    popup.geometry("350x300")

    label = tk.Label(popup, text="Wähle einen Port aus der Liste:")
    label.pack(pady=10)

    available_ports = serial_ports()

    listbox = tk.Listbox(popup, selectmode=tk.SINGLE, height=10)
    for port in available_ports:
        listbox.insert(tk.END, port)
    listbox.pack(pady=10)

    def confirm_selection():
        # Auswahl des Ports
        selected_index = listbox.curselection()
        if selected_index:
            chosen_port = listbox.get(selected_index)
            popup.destroy()
            read_serial_data(chosen_port)
        else:
            messagebox.showwarning("Warnung", "Bitte wählen Sie einen Port aus.")
    
    confirm_button = ttk.Button(popup, text="Bestätigen", command=confirm_selection)
    confirm_button.pack(pady=10)

def read_serial_data(port):
    global ser, disconnect_button
    try:
        # Öffne die serielle Verbindung
        ser = serial.Serial(port, 9600, timeout=1)
        ser.flush()  # Puffer leeren

        def update_data():
            if ser and ser.in_waiting > 0:
                # Lese Daten von der seriellen Schnittstelle
                line = ser.readline().decode('utf-8').rstrip()
                if line:
                    # Hier wird der gescannte Code in die Tabelle eingefügt
                    tree.insert("", "end", values=(line, ""))  # Leerer Name (wird später ausgefüllt)
                    text_area.insert(tk.END, line + '\n')
                    text_area.see(tk.END)
            
            if ser:  # Wenn die Verbindung noch aktiv ist, erneut nach 100 ms aufrufen
                root.after(100, update_data)

        # Starte den Daten-Update-Prozess
        update_data()

        # Disconnect-Button erstellen, falls noch nicht vorhanden
        if disconnect_button is None:
            disconnect_button = ttk.Button(root, text="Disconnect", command=disconnect_serial)
            disconnect_button.pack(pady=10)

    except serial.SerialException as e:
        messagebox.showerror("Fehler", f"Serielle Verbindung konnte nicht geöffnet werden: {e}")

def disconnect_serial():
    global ser, disconnect_button
    if ser and ser.is_open:
        ser.close()
        ser = None
        messagebox.showinfo("Verbindung getrennt", "Die serielle Verbindung wurde erfolgreich getrennt.")
        clear_table()  # Tabelle nach dem Trennen leeren

        # Disconnect-Button entfernen
        if disconnect_button is not None:
            disconnect_button.pack_forget()  # Entferne den Button
            disconnect_button = None  # Setze den Button auf None

    else:
        messagebox.showwarning("Keine Verbindung", "Es ist keine serielle Verbindung aktiv.")

def clear_table():
    """ Löscht alle Einträge in der Tabelle """
    for row in tree.get_children():
        tree.delete(row)
    text_area.delete('1.0', tk.END)  # Leere auch das Textfeld
    data_dict.clear()  # Leere das Dictionary

def add_name():
    selected_item = tree.selection()
    if selected_item:
        name = name_entry.get()
        if name:
            # Aktualisiere den Namen in der ausgewählten Zeile
            scanned_code = tree.item(selected_item, 'values')[0]
            tree.item(selected_item, values=(scanned_code, name))
            name_entry.delete(0, tk.END)  # Leere das Eingabefeld nach der Eingabe

            # Füge den gescannten Code und den Namen zum Dictionary hinzu
            data_dict[scanned_code] = name

            # Automatisch die nächste Zeile auswählen
            next_index = tree.index(selected_item) + 1  # Index der nächsten Zeile
            if next_index < len(tree.get_children()):
                next_item = tree.get_children()[next_index]
                tree.selection_set(next_item)
        else:
            messagebox.showwarning("Fehler", "Bitte einen Namen eingeben.")
    else:
        messagebox.showwarning("Fehler", "Bitte eine Zeile auswählen, um den Namen hinzuzufügen.")

def save_to_json():
    # Speichern in JSON-Datei
    with open("data.json", "w") as f:
        json.dump(data_dict, f, indent=4)
    
    messagebox.showinfo("Erfolgreich", "Daten wurden in 'data.json' gespeichert.")
    clear_table()

def delete_selection():
    # Lösche die ausgewählte Zeile aus der Tabelle
    selected_item = tree.selection()
    if selected_item:
        scanned_code = tree.item(selected_item, 'values')[0]
        del data_dict[scanned_code]  # Entferne den Eintrag aus dem Dictionary
        tree.delete(selected_item)
        messagebox.showinfo("Gelöscht", "Die ausgewählte Zeile wurde gelöscht.")
    else:
        messagebox.showwarning("Fehler", "Keine Zeile ausgewählt.")

# Hauptfenster
root = tk.Tk()
root.geometry("800x600")  # Vergrößere das Fenster
root.title("Serielle Daten mit Namen speichern")

# Textfeld zum Anzeigen der empfangenen Daten (vergrößert)
text_area = tk.Text(root, height=10, width=100)  # Vergrößere das Textfeld
text_area.pack(pady=10)

# Hauptframe
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Left Frame für die Tabelle
left_frame = tk.Frame(main_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Treeview (Tabelle) erstellen
columns = ("scanned_code", "name")
tree = ttk.Treeview(left_frame, columns=columns, show="headings")
tree.heading("scanned_code", text="Gescannte Daten")
tree.heading("name", text="Name")
tree.pack(pady=20, fill=tk.BOTH, expand=True)

# Right Frame für das Namensfeld und den Button
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

# Eingabefeld für den Namen
name_label = tk.Label(right_frame, text="Name eingeben:")
name_label.pack(pady=5)
name_entry = tk.Entry(right_frame)
name_entry.pack(pady=5)

# Button zum Hinzufügen des Namens in die Tabelle
add_name_button = ttk.Button(right_frame, text="Name hinzufügen", command=add_name)
add_name_button.pack(pady=5)

# Buttons für Löschen und Speichern im unteren Bereich des Fensters
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

delete_button = ttk.Button(button_frame, text="Ausgewählte Zeile löschen", command=delete_selection)
delete_button.pack(side=tk.LEFT, padx=5)

save_button = ttk.Button(button_frame, text="Alle Daten in JSON speichern", command=save_to_json)
save_button.pack(side=tk.LEFT, padx=5)

# Button, um das Popup-Fenster zu öffnen
open_button = ttk.Button(button_frame, text="Port auswählen", command=open_port_selection)
open_button.pack(side=tk.LEFT, padx=5)

root.mainloop()


