from __future__ import annotations

from pathlib import Path
import PySimpleGUI as sg


def ask_user_for_file() -> Path | None:
    """
    - Make a popup window that asks the user to select the CSV
    filepath to summarize

    Returns:
        Path | None: if user follows directions, a filepath is returned, otherwise None
    """
    layout = [
        [sg.Text("Google Form Summarizer", font="Courier 24")],
        [sg.FileBrowse("Select a CSV file", font="Courier 18")],
        [
            sg.Button("Submit", font="Courier 14", button_color="green"),
            sg.Button(
                "Quit",
                font="Courier 10",
                button_color="red",
            ),
        ],
    ]

    window = sg.Window("Select a CSV file").Layout(layout)

    filepath = None

    while True:
        event, values = window.Read()

        if event is None or event == "Quit":
            break

        if event == "Submit":
            filepath = Path(values["Select a CSV file"])

        window.Close()

    return filepath
