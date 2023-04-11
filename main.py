from kivy.properties import StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivy.uix.stacklayout import StackLayout
from kivymd.uix.textfield import MDTextField
from kivy.clock import Clock
from kivy.metrics import sp
from word_generator import initialize_words_list
import functools


def do_not_run_twice(func):
    prev_call = None

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal prev_call

        if (args, kwargs) == prev_call:
            return None
        prev_call = args, kwargs
        return func(*args, **kwargs)

    return wrapper


class MainLayout(MDBoxLayout):
    pass


class WordLabel(MDLabel):
    pass


class ResultsPopup(MDBoxLayout):
    pass


class WordsBox(StackLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.words = None
        self.font_size = sp(20)
        self.initialize()

    def initialize(self):
        self.words = initialize_words_list()
        self.populate_words()

    def populate_words(self):
        for word in self.words:
            label = WordLabel(text=word)
            label.font_size = self.font_size
            self.add_widget(label)
        self.children[-1].underline = True
        self.children[-1].text_color = "#333333"

    def reset(self):
        self.clear_widgets()
        self.initialize()
        self.font_size = sp(20)
        self.parent.scroll_y = 1

class WordsInput(MDTextField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.input_field = StringProperty("")
        self.timer_started = False
        self.minute_timer = None

        self.current_word_label = None
        self.next_word_label = None
        self.scroll_amount = 59

        # counters
        self.current_word_index = 0
        self.word_line = 0
        self.correct_words = 0
        self.wrong_words = 0
        self.correct_chars = 0
        self.wrong_chars = 0
        self.timer_seconds = 60

        self.dialog = MDDialog(type='custom', content_cls=ResultsPopup(), buttons=[
            MDFlatButton(text='OK', on_release=self.close_dialog)])

    def evaluate_typed_word(self, text: str) -> None:
        """ Main function checking the entry and calling all modifiers/validators """
        if not self.timer_started:
            print("Starting timer.")
            self.timer_started = True
            self.hint_text = "Keep typing..."
            self.start_timer()
            self.parent.parent.ids['restart_button'].disabled = True
        if len(text) > 0 and text[-1].isspace():
            self.on_space_action(typed_word=text.strip())
            self.text = ''

    @do_not_run_twice
    def on_space_action(self, typed_word: str) -> None:
        self.current_word_label = self.parent.parent.ids['words_text'].children[-self.current_word_index - 1]
        self.next_word_label = self.parent.parent.ids['words_text'].children[-(self.current_word_index + 2)]

        self.color_words(typed_word=typed_word)
        self.update_score()
        self.current_word_index += 1
        self.do_scroll()

    def color_words(self, typed_word: str) -> None:
        current_word = self.current_word_label.text

        if typed_word == current_word:
            self.current_word_label.text_color = "#03c04a"
            self.correct_words += 1
            self.correct_chars += len(current_word)
        else:
            self.current_word_label.text_color = "#b90e0a"
            self.wrong_words += 1
            self.wrong_chars += len(current_word)

        self.next_word_label.underline = True
        self.next_word_label.text_color = "#333333"
        self.current_word_label.underline = False

    def update_score(self):
        """ Updates the top bar scores """
        wpm_result = self.calculate_pm(total_count=self.correct_words)
        self.parent.parent.ids['wpm'].text = str(wpm_result)
        cpm_result = self.calculate_pm(total_count=self.correct_chars)
        self.parent.parent.ids['cpm'].text = str(cpm_result)

    def calculate_pm(self, total_count: int) -> int:
        """ Calculates words/chars per minutes based on seconds passed and total count of words/chars """
        seconds_passed = (60 - self.timer_seconds) + 1
        pm = int(total_count * (60 / seconds_passed))
        return pm

    def do_scroll(self):
        """ Manage the text scroll when needed """
        current_word_pos_y = self.current_word_label.pos[1]
        next_word_pos_y = self.next_word_label.pos[1]

        if next_word_pos_y < current_word_pos_y:
            self.word_line += 1

        if next_word_pos_y < current_word_pos_y and self.word_line > 1:
            row_height = self.scroll_amount
            words_box_height = self.parent.parent.ids['words_text'].height
            scroll_amount = row_height / words_box_height
            self.parent.parent.ids['words_scroll_view'].scroll_y -= scroll_amount

    def start_timer(self):
        self.minute_timer = Clock.schedule_interval(self.count_seconds, 1)
        self.minute_timer()

    def count_seconds(self, dt):
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.parent.parent.ids['timer'].text = str(self.timer_seconds)

        else:
            self.disable_input()
            self.update_final_score()
            self.show_score_dialog()
            Clock.unschedule(self.minute_timer)
            self.parent.parent.ids['restart_button'].disabled = False

    def disable_input(self):
        self.disabled = True
        self.hint_text = "Time is up!"
        self.text = ""

    def update_final_score(self):
        corrected_wpm = self.correct_words
        corrected_cpm = self.correct_chars
        total_cpm = corrected_cpm + self.wrong_chars

        self.parent.parent.ids['wpm'].text = str(corrected_wpm)
        self.parent.parent.ids['cpm'].text = f"{self.correct_chars} / {self.correct_chars + self.wrong_chars}"

        score_1 = f"Your score is {corrected_cpm} CPM (that is {corrected_wpm} Words Per Minute)"
        if self.wrong_words == 0:
            score_2 = f"Congratulations! You did all {corrected_wpm} correctly!"
        else:
            score_2 = f"You did {total_cpm} CPM, but as you did " \
                      f"{(lambda x: f'{x} word' if x == 1 else f'{x} words')(self.wrong_words)} " \
                      f"words wrong your score was corrected."
        self.dialog.content_cls.ids["popup_score_message1"].text = score_1
        self.dialog.content_cls.ids["popup_score_message2"].text = score_2

    def show_score_dialog(self):
        self.dialog.open()

    def close_dialog(self, obj):
        self.dialog.dismiss()

    def reset(self):
        Clock.unschedule(self.minute_timer)

        self.timer_started = False
        self.minute_timer = None

        self.current_word_label = None
        self.next_word_label = None
        self.scroll_amount = 59

        # counters
        self.current_word_index = 0
        self.word_line = 0
        self.correct_words = 0
        self.wrong_words = 0
        self.correct_chars = 0
        self.wrong_chars = 0
        self.timer_seconds = 60

        self.hint_text = "Start typing to start the test"
        self.text = ""
        self.disabled = False

        self.parent.parent.ids['wpm'].text = "?"
        self.parent.parent.ids['cpm'].text = "?"
        self.parent.parent.ids['timer'].text = "60"


class TypeThisApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        # self.theme_cls.primary_hue = "200"
        return

    def reset(self):
        self.root.ids.words_text.reset()
        self.root.ids.type_input.reset()

    def font_up(self):
        self.root.ids.words_text.font_size += 1
        self.root.ids.type_input.scroll_amount += 1
        self.root.ids.words_text.clear_widgets()
        self.root.ids.words_text.populate_words()

    def font_down(self):
        self.root.ids.words_text.font_size -= 1
        self.root.ids.type_input.scroll_amount -= 1
        self.root.ids.words_text.clear_widgets()
        self.root.ids.words_text.populate_words()


if __name__ == "__main__":
    TypeThisApp().run()
