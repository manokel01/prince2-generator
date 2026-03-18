import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, ListItem, ListView
from textual.binding import Binding
from textual.screen import ModalScreen

class RationaleModal(ModalScreen):
    """Zero-border rationale feedback."""
    def __init__(self, rationale, is_correct, **kwargs):
        super().__init__(**kwargs)
        self.rationale = rationale
        self.is_correct = is_correct

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("CORRECT" if self.is_correct else "INCORRECT", id="status-label"),
            Static(self.rationale, id="rationale-text"),
            Label("Press Enter to continue...", id="close-hint"),
            id="modal-container"
        )

    def on_key(self) -> None:
        self.dismiss()

class ExamApp(App):
    CSS = """
    Screen {
        background: #000000;
        color: #ffffff;
    }
    #main-layout {
        height: 100%;
    }
    #sidebar {
        width: 25;
        background: #080808;
        border-right: solid #222222;
        padding: 1;
    }
    #content-area {
        padding: 2;
    }
    .question-text {
        text-style: bold;
        margin-bottom: 1;
        color: #00ff00;
    }
    .scenario-box {
        background: #111111;
        padding: 1;
        margin-bottom: 1;
        display: none;
        max-height: 40%;
        overflow-y: scroll;
    }
    .scenario-box.visible {
        display: block;
    }
    ListView {
        background: transparent;
        margin-top: 1;
    }
    ListItem {
        padding: 1;
        background: #000000;
    }
    ListItem:hover {
        background: #111111;
    }
    ListItem.--highlight {
        background: #222222;
        color: #00ff00;
        text-style: bold;
    }
    #modal-container {
        width: 60%;
        height: auto;
        background: #000000;
        border: solid #00ff00;
        padding: 2;
        align: center middle;
    }
    #status-label {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
    }
    #close-hint {
        color: #444444;
        text-align: center;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "toggle_scenario", "Toggle Scenario"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.exam_data = []
        self.current_idx = 0
        self.score = 0
        self.scenario_text = ""

    def on_mount(self):
        try:
            data_file = Path("exam_data.json")
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    self.exam_data = json.load(f)
            
            scenario_path = Path("data/target_scenario/Louistown_scenario.md")
            if scenario_path.exists():
                self.scenario_text = scenario_path.read_text(encoding="utf-8")
            
            if self.exam_data:
                self.update_question()
            else:
                self.notify("Error: exam_data.json is empty.", severity="error")
        except Exception as e:
            self.notify(f"Error loading exam: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Label("PRINCE2 PROCTOR", id="title")
                yield Label("Progress: 0/0", id="progress")
                yield Label("Score: 0", id="score-label")
            with Vertical(id="content-area"):
                yield Static(self.scenario_text, id="scenario-view", classes="scenario-box")
                yield Static("Loading...", id="question-display", classes="question-text")
                yield ListView(id="options-list")
        yield Footer()

    def update_question(self):
        if not self.exam_data:
            return
            
        if self.current_idx >= len(self.exam_data):
            self.query_one("#question-display").update(f"EXAM COMPLETE\nFinal Score: {self.score}/{len(self.exam_data)}")
            self.query_one("#options-list").clear()
            return

        q = self.exam_data[self.current_idx]
        self.query_one("#question-display").update(f"Q{self.current_idx + 1}: {q['question']}")
        
        list_view = self.query_one("#options-list")
        list_view.clear()
        
        options = q.get('options', {})
        for key in sorted(options.keys()):
            val = options[key]
            list_view.append(ListItem(Label(f"[{key}] {val}"), name=key))
        
        self.query_one("#progress").update(f"Progress: {self.current_idx + 1}/{len(self.exam_data)}")

    def on_list_view_selected(self, event: ListView.Selected):
        if not self.exam_data or self.current_idx >= len(self.exam_data):
            return

        choice = event.item.name
        q = self.exam_data[self.current_idx]
        correct_ans = q.get('answer', '')
        is_correct = choice == correct_ans
        
        if is_correct:
            self.score += 1
            self.query_one("#score-label").update(f"Score: {self.score}")

        def after_modal():
            self.current_idx += 1
            self.update_question()

        self.push_screen(RationaleModal(q.get('rationale', 'No rationale provided.'), is_correct), callback=after_modal)

    def action_toggle_scenario(self):
        self.query_one("#scenario-view").toggle_class("visible")

if __name__ == "__main__":
    ExamApp().run()
