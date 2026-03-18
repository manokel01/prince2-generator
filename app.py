import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Label, ListItem, ListView
from textual.binding import Binding
from textual.screen import ModalScreen

class ScenarioModal(ModalScreen):
    """Full-screen reading view for the scenario overlay."""
    
    BINDINGS = [
        Binding("s", "dismiss", "Close Scenario"),
        Binding("escape", "dismiss", "Close"),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", "Scroll Up", show=False),
    ]

    def __init__(self, scenario_text, **kwargs):
        super().__init__(**kwargs)
        self.scenario_text = scenario_text

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("SCENARIO REFERENCE", id="scenario-title"),
            # Native scrollable wrapper
            ScrollableContainer(Static(self.scenario_text, id="scenario-text"), id="scenario-scroll"),
            Label("Press 's' or 'Esc' to close...", id="scenario-close-hint"),
            id="scenario-modal-container"
        )

    def action_dismiss(self) -> None:
        self.dismiss()
        
    def action_scroll_down(self) -> None:
        self.query_one("#scenario-scroll").scroll_relative(y=3, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#scenario-scroll").scroll_relative(y=-3, animate=False)

class RationaleModal(ModalScreen):
    """Zero-border rationale feedback."""
    
    BINDINGS = [
        Binding("enter", "dismiss", "Continue"),
        Binding("escape", "dismiss", "Continue"),
        Binding("space", "dismiss", "Continue"),
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", "Scroll Up", show=False),
    ]

    def __init__(self, rationale, is_correct, **kwargs):
        super().__init__(**kwargs)
        self.rationale = rationale
        self.is_correct = is_correct

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("CORRECT" if self.is_correct else "INCORRECT", id="status-label", classes="correct" if self.is_correct else "incorrect"),
            # Native scrollable wrapper
            ScrollableContainer(Static(self.rationale, id="rationale-text"), id="rationale-scroll"),
            Label("Press Enter to continue...", id="close-hint"),
            id="modal-container"
        )

    def action_dismiss(self) -> None:
        self.dismiss()

    def action_scroll_down(self) -> None:
        self.query_one("#rationale-scroll").scroll_relative(y=3, animate=False)

    def action_scroll_up(self) -> None:
        self.query_one("#rationale-scroll").scroll_relative(y=-3, animate=False)

class ExamApp(App):
    CSS = """
    Screen {
        background: #000000;
        color: #ffffff;
    }
    ScenarioModal, RationaleModal {
        align: center middle;
    }
    #main-layout {
        height: 100%;
    }
    #sidebar {
        width: 30;
        background: #080808;
        border-right: solid #222222;
        padding: 1;
        height: 100%;
    }
    #content-area {
        padding: 2;
        height: 100%;
    }
    .question-text {
        text-style: bold;
        margin-bottom: 2;
        color: #00ff00;
    }
    ListView {
        background: transparent;
        border: none;
    }
    ListView:focus {
        border: none;
    }
    #options-list {
        height: auto;
        margin-top: 1;
    }
    #q-list {
        margin-top: 1;
        height: 1fr;
        border-top: solid #222222;
        padding-top: 1;
    }
    ListItem {
        padding: 1;
        background: #000000;
    }
    ListItem:hover {
        background: #111111;
    }
    ListItem:focus {
        background: #222222;
    }
    ListItem.--highlight {
        background: #222222;
        color: #00ff00;
        text-style: bold;
    }
    .answered-item Label {
        color: #555555;
    }
    #modal-container {
        width: 70%;
        height: auto;
        background: #000000;
        border: solid #00ff00;
        padding: 2;
    }
    #rationale-scroll {
        max-height: 60vh;
        scrollbar-background: #000000;
        scrollbar-color: #222222;
    }
    #scenario-modal-container {
        width: 80%;
        height: 80%;
        background: #000000;
        border: solid #00ff00;
        padding: 2;
    }
    #scenario-scroll {
        height: 1fr;
        scrollbar-background: #000000;
        scrollbar-color: #222222;
    }
    #scenario-title {
        text-align: center;
        width: 100%;
        text-style: bold;
        color: #00ff00;
        margin-bottom: 1;
    }
    #scenario-close-hint {
        color: #444444;
        text-align: center;
        margin-top: 1;
    }
    #status-label {
        text-align: center;
        width: 100%;
        text-style: bold;
        margin-bottom: 1;
    }
    .correct { color: #00ff00; }
    .incorrect { color: #ff0000; }
    #close-hint {
        color: #444444;
        text-align: center;
        margin-top: 2;
    }
    #tab-hint {
        color: #666666;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "toggle_scenario", "Toggle Scenario"),
        Binding("tab", "switch_focus", "Switch Panel Focus"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.exam_data = []
        self.current_idx = 0
        self.score = 0
        self.scenario_text = ""
        self.answered = set()

    def on_mount(self):
        try:
            data_file = Path("exam_data.json")
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    self.exam_data = json.load(f)[:70]
            
            scenario_path = Path("data/target_scenario/Louistown_scenario.md")
            if scenario_path.exists():
                self.scenario_text = scenario_path.read_text(encoding="utf-8")
            
            if self.exam_data:
                self.populate_sidebar()
                self.update_question()
                self.query_one("#options-list").focus() 
            else:
                self.notify("Error: exam_data.json is empty.", severity="error")
        except Exception as e:
            self.notify(f"Error loading exam: {e}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield Label("PRINCE2 PROCTOR", id="title")
                yield Label("Progress: 0/70", id="progress")
                yield Label("Score: 0", id="score-label")
                yield Label("Tab: Switch Panel", id="tab-hint")
                yield ListView(id="q-list")
            with Vertical(id="content-area"):
                yield Static("Loading...", id="question-display", classes="question-text")
                yield ListView(id="options-list")
        yield Footer()

    def populate_sidebar(self):
        q_list = self.query_one("#q-list")
        q_list.clear()
        for i in range(len(self.exam_data)):
            mark = " [✓]" if i in self.answered else ""
            item = ListItem(Label(f"Question {i+1}{mark}"), name=str(i))
            if i in self.answered:
                item.add_class("answered-item")
            q_list.append(item)

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
            list_view.append(ListItem(Label(f"{key}) {val}"), name=key))
        
        self.query_one("#progress").update(f"Progress: {self.current_idx + 1}/{len(self.exam_data)}")
        
        q_list = self.query_one("#q-list")
        q_list.index = self.current_idx

    def on_list_view_selected(self, event: ListView.Selected):
        list_id = event.list_view.id
        
        if list_id == "q-list":
            self.current_idx = int(event.item.name)
            self.update_question()
            self.query_one("#options-list").focus()
            
        elif list_id == "options-list":
            if self.current_idx in self.answered:
                self.notify("Already answered. Skipping...", severity="warning")
                self.current_idx += 1
                self.update_question()
                return

            choice = event.item.name
            q = self.exam_data[self.current_idx]
            correct_ans = q.get('answer', '')
            is_correct = choice == correct_ans
            
            if is_correct:
                self.score += 1
                self.query_one("#score-label").update(f"Score: {self.score}")

            self.answered.add(self.current_idx)
            
            try:
                q_list = self.query_one("#q-list")
                target_item = q_list.children[self.current_idx]
                target_item.query_one(Label).update(f"Question {self.current_idx + 1} [✓]")
                target_item.add_class("answered-item")
            except Exception:
                pass

            def after_modal(_=None):
                self.current_idx += 1
                self.update_question()
                self.query_one("#options-list").focus()

            self.push_screen(RationaleModal(q.get('rationale', 'No rationale provided.'), is_correct), callback=after_modal)

    def action_switch_focus(self):
        q_list = self.query_one("#q-list")
        opt_list = self.query_one("#options-list")
        if q_list.has_focus:
            opt_list.focus()
        else:
            q_list.focus()

    def action_cursor_down(self):
        if self.query_one("#options-list").has_focus:
            self.query_one("#options-list").action_cursor_down()
        elif self.query_one("#q-list").has_focus:
            self.query_one("#q-list").action_cursor_down()

    def action_cursor_up(self):
        if self.query_one("#options-list").has_focus:
            self.query_one("#options-list").action_cursor_up()
        elif self.query_one("#q-list").has_focus:
            self.query_one("#q-list").action_cursor_up()

    def action_toggle_scenario(self):
        if self.scenario_text:
            self.push_screen(ScenarioModal(self.scenario_text))
        else:
            self.notify("Scenario text not loaded.", severity="warning")

if __name__ == "__main__":
    ExamApp().run()
