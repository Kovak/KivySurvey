from __future__ import unicode_literals, print_function
from kivy.uix.widget import Widget
from kivy.properties import (BooleanProperty, ObjectProperty, StringProperty,
    NumericProperty, ReferenceListProperty, ListProperty)
from flat_kivy.numpad import NumPad, DecimalNumPad
from kivy.clock import Clock
from kivy.utils import platform
from flat_kivy.ui_elements import (TextInputFocus, 
    CheckBoxListItem as CheckboxAnswerWidget, 
    FlatPopup as Popup, FlatToggleButton)
from kivy.lang import Builder
from functools import partial
from kivy.core.window import Window
from kivy.uix.screenmanager import NoTransition, SlideTransition
from flat_kivy.utils import construct_target_file_name
Builder.load_file(construct_target_file_name('surveyquestions.kv', __file__))


class SurveyQuestion(Widget):
    allow_no_answer = BooleanProperty(False)
    answer = ObjectProperty(None, allownone=True)
    question_name = StringProperty('default_question_name')
    question_text = StringProperty(None)
    validated = BooleanProperty(False)
    font_ramp_tuple = ListProperty(['question_default', '1'])
    do_transition = BooleanProperty(True)
    do_state = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SurveyQuestion, self).__init__(**kwargs)
        self._no_trans = NoTransition()
        self._slide_trans = SlideTransition()

    def on_validated(self, instance, value):
        do_transition = self.do_transition
        slide_trans = self._slide_trans
        no_trans = self._no_trans
        try:
            sm = self.ids.sm
        except:
            print("can't find sm class")
            return
        if value:
            if do_transition:
                sm.transition = slide_trans
                sm.transition.direction = 'left'
            else:
                sm.transition = no_trans
            sm.current = 'inactive'
        else:
            if do_transition:
                sm.transition = slide_trans
                sm.transition.direction = 'right'
            else:
                sm.transition = no_trans
            sm.current = 'active'


    def on_touch_move(self, touch):
        super(SurveyQuestion, self).on_touch_move(touch)
        if self.collide_point(touch.x, touch.y) and self.do_state:
            bm = self.ids.back_manager
            if touch.dx < -15 and self.validated and bm.current == 'no_button':
                bm.transition.direction = 'left'
                bm.current = 'button'
            elif touch.dx > 15 and self.validated and bm.current == 'button':
                bm.transition.direction = 'right'
                bm.current = 'no_button' 

    def unvalidate(self):
        bm =  self.ids.back_manager
        bm.transition.direction = 'right'
        bm.current = 'no_button'
        self.validated = False

    def clear_question(self):
        self.answer = None
        self.unvalidate()

    def check_answered(self):
        if self.allow_no_answer:
            return True
        else:
            return self.answer is not None

    def _schedule_validate(self, dt):
        self._validate(self.validate_question())

    def _validate(self, validated):
        if validated:
            self.validated = True
        else:
            self.validated = False

    def _schedule_reset_do_transition(self, dt):
        self.do_transition = True

    def validate_question(self):
        return self.answer is not None

    def to_json(self):
        return self.answer

    def from_json(self, json_data):
        self.answer = json_data


class SurveyQuestionNumerical(SurveyQuestion):
    min_answer = NumericProperty(None, allownone=True)
    max_answer = NumericProperty(None, allownone=True)
    do_decimal = BooleanProperty(False)
    numpad_open_callback = ObjectProperty(None)
    do_state = BooleanProperty(True)
    units = StringProperty(None, allownone=True)


    def numpad_open_callback(self):
        self.kivysurvey.raise_numpad(self.question_text, self.numpad_return_callback,
            units=self.units, minimum=self.min_answer, maximum=self.max_answer,
            do_decimal=self.do_decimal)

    def numpad_return_callback(self, value, is_return):
        if value is 0 and is_return:
            value = None
        if is_return:
            Clock.schedule_once(self._schedule_validate, .2)
        self.answer = value

    def validate_question(self):
        min_answer = self.min_answer
        max_answer = self.max_answer
        answer = self.answer
        if answer is not None:
            if min_answer is not None and max_answer is not None:
                return min_answer < answer < max_answer
            elif min_answer is not None:
                return min_answer < answer
            elif max_answer is not None:
                return answer < max_answer
            else:
                return True
        else:
            return False


class SurveyQuestionBirthDate(SurveyQuestion):
    day = StringProperty(None, allownone=True)
    month = StringProperty(None, allownone=True)
    year = StringProperty(None, allownone=True)
    current_field = StringProperty(None, allownone=True)
    numpad = ObjectProperty(None)
    numpad_open_callback = ObjectProperty(None)
    numpad_close_callback = ObjectProperty(None)
    day_maximum_value = NumericProperty(31)
    do_state = BooleanProperty(True)
    answer = ReferenceListProperty(day, month, year)

    def __init__(self, **kwargs):
        super(SurveyQuestionBirthDate, self).__init__(**kwargs)

    def validate_question(self):
        return self.day is not None and (
            self.month is not None and self.year is not None)

    def check_answered(self):
        if self.allow_no_answer:
            return True
        else:
            return self.day is not None and (
                self.month is not None and self.year is not None)

    def to_json(self):
        return self.answer

    def from_json(self, json_data):
        self.set_answer(json_data)

    def set_answer(self, answer_value):
        try:
            self.day = answer_value[0]
            self.month = answer_value[1]
            self.year = answer_value[2]
        except:
            self.clear_question()
            
    def clear_question(self):
        self.day = None
        self.month = None
        self.year = None

    def check_answered(self):
        if self.allow_no_answer:
            return True
        else:
            return self.day is not None and (
                self.month is not None and self.year is not None)

    def on_year(self, instance, value):
        if self.month == '02':
            self.day_maximum_value = self.calculate_days_in_february()
            if self.day is not None and int(self.day) > self.day_maximum_value:
                self.day = None

    def calculate_days_in_february(self):
        year = self.year
        if year is not None:
            is_leap_year = False
            year = int(year)
            if year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0):
                is_leap_year = True
            if is_leap_year:
                return 29
            else:
                return 28
        else:
            return 28

    def on_month(self, instance, value):
        months_with_31 = ['01', '03', '05', '07', '08', '10', '12']
        months_with_30 = ['04', '06', '09', '11']
        months_with_28 = ['02']
        if value in months_with_31:
            self.day_maximum_value = 31
        elif value in months_with_30:
            self.day_maximum_value = 30
        elif value in months_with_28:
            self.day_maximum_value = self.calculate_days_in_february()
        if self.day is not None and int(self.day) > self.day_maximum_value:
            self.day = None

    def open_numpad(self, field):
        self.current_field = field
        title = 'Input ' + field + ': '
        if field == 'day':
            maximum_value = self.day_maximum_value
        elif field == 'month':
            maximum_value = 12
        elif field == 'year':
            maximum_value = 3000
        self.kivysurvey.raise_numpad(title, self.numpad_return_callback,
            maximum=maximum_value,)

    def numpad_return_callback(self, value, is_return):
        current_field = self.current_field
        if current_field == 'day':
            if value < 10:
                self.day = '0' + str(value)
            if value == 0:
                self.day = None
            else:
                self.day = str(value)
        elif current_field == 'month':
            if value < 10:
                self.month = '0' + str(value)
            if value == 0:
                self.month = None
            else:
                self.month = str(value)
        elif current_field == 'year':
            if value == 0:
                self.year = None
            else:
                self.year = str(value)
        if is_return:
            self.current_field = None
            Clock.schedule_once(self._schedule_validate, .2)


class SurveyQuestionYesNo(SurveyQuestion):
    answer_group = StringProperty('Default Answers')
    answer1_text = StringProperty('Yes')
    answer2_text = StringProperty('No')
    do_state = BooleanProperty(True)
    no_answer_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SurveyQuestionYesNo, self).__init__(**kwargs)
        self.setup_no_answer_button()
        Clock.schedule_once(self.setup)

    def toggle_function(self, instance):
        buttons = instance.get_widgets(self.answer_group)
        is_button_down = False
        for button in buttons:
            if button.state == 'down':
                is_button_down = True
                self.answer = button.text
        if not is_button_down:
            self.answer = None
        self.answer_valid = is_button_down
        del buttons
        Clock.schedule_once(self._schedule_validate, .2)

    def clear_question(self):
        for button in self.answer_layout.children:

            button.state = 'normal'

    def setup(self, dt):
        pass

    def from_json(self, json_data):
        self.set_answer(json_data)

    def set_answer(self, new_value):
        self.answer = new_value
        for button in self.answer_layout.children:
            if button.text == new_value:
                button.state = 'down'

    def setup_no_answer_button(self):
        self.no_answer_button = no_answer_button = FlatToggleButton(
            text='No Answer', group=self.answer_group, 
            on_release=self.toggle_function,
            no_up=True,
            theme=('blue', 'variant_3'),
            height='80dp',
            max_lines=1,
            font_ramp_tuple=self.font_ramp_tuple,
            size_hint=(1., None),)
        
        if self.allow_no_answer:
            self.bind(font_ramp_tuple=no_answer_button.setter(
                'font_ramp_tuple'))
            self.answer_layout.add_widget(no_answer_button)

    def on_answer_group(self, instance, value):
        if self.no_answer_button is not None:
            self.no_answer_button.group = value

    def on_allow_no_answer(self, instance, value):
        no_answer_button = self.no_answer_button
        try:
            answer_layout = self.ids.answer_layout
        except:
            Clock.schedule_once(lambda x: partial(
                self.on_allow_no_answer, instance, value), .1)
            return
        if value and no_answer_button not in answer_layout.children:
            answer_layout.add_widget(no_answer_button)
        else:
            if no_answer_button in answer_layout.children:
                answer_layout.remove_widget(no_answer_button)


class SurveyQuestionToggle(SurveyQuestion):
    answer_group = StringProperty('Default Answers')
    button = ObjectProperty(None)
    answer_text = StringProperty('Yes')

    def __init__(self, **kwargs):
        super(SurveyQuestionToggle, self).__init__(**kwargs)

    def toggle_function(self, instance):
        button = self.button
        if button.state == 'down':
            self.answer = True
        else:
            self.answer = False

    def clear_question(self):
        self.button.state = 'normal'


class SurveyQuestionTextInput(SurveyQuestion):
    text_input = ObjectProperty(None)
    do_state = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(SurveyQuestionTextInput, self).__init__(**kwargs)
        Clock.schedule_once(self.setup)

    def setup(self, dt):
        self.setup_textinput_popup()

    def setup_textinput_popup(self):
        self.text_input = text_input = TextInputFocus()
        self.text_input_popup = popup = Popup(title='Input Name', 
            size_hint=(1.0, 1.0), content=text_input)
        text_input.bind(text=self.setter('answer'))
        text_input.close_callback = self.close
        text_input.texti.bind(focus=self.on_focus)

    def close(self):
        self.text_input_popup.dismiss()
        Window.release_all_keyboards()
        Clock.schedule_once(self._schedule_validate, .2)

    def on_focus(self, instance, value):
        if not value:
            Window.release_all_keyboards()

    def clear_question(self):
        self.text_input.texti.text = ''
        self.answer = None


class CheckboxQuestion(SurveyQuestion):
    answers = ListProperty(None)
    group = StringProperty('')
    answer_layout = ObjectProperty(None)
    font_ramp_tuple = ListProperty(['default', '1'])

    def on_group(self, instance, value):
        self.on_answers(None, self.answers)

    def on_answer_layout(self, instance, value):
        if value is not None:
            self.on_answers(None, self.answers)

    def on_answers(self, instance, value):
        answer_layout = self.answer_layout
        if answer_layout is not None:
            answer_layout.clear_widgets()
            for answer in value:
                answer_wid = CheckboxAnswerWidget(
                    text=answer, group=self.group, size_hint=(1.0, .25),
                    theme=('blue', 'variant_3'), font_ramp_tuple=self.font_ramp_tuple)
                self.bind(font_ramp_tuple=answer_wid.setter('font_ramp_tuple'))
                answer_layout.add_widget(answer_wid)
                answer_wid.bind(active=self.set_answer)

    def from_json(self, json_data):
        for each in self.answer_layout.children:
            if each.text == json_data:
                each.toggle_checkbox()


    def set_answer(self, instance, value):
        if value:
            self.answer = instance.text
        else:
            self.answer = None

    def clear_question(self):
        for each in self.answer_layout.children:
            each.ids.checkbox.active = False
