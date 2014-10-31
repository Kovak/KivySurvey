from __future__ import unicode_literals, print_function
__version__ = '0.0.1'
import kivy
from flat_kivy import FlatApp, ThemeManager
from kivy.properties import (StringProperty, NumericProperty, ObjectProperty,
    ListProperty, DictProperty, BooleanProperty)
try:
    from plyer import gps
except:
    pass
from flat_kivy.ui_elements import (ErrorContent, OptionContent, FlatIconButton, 
    FlatLabel)
from surveyquestions import SurveyQuestionNumerical
from kivy.base import EventLoop
from kivy.clock import Clock
from flat_kivy.numpad import DecimalNumPad, NumPad
from flat_kivy.ui_elements import FlatPopup as Popup
from flat_kivy.utils import construct_target_file_name
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.event import EventDispatcher
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from flat_kivy.ui_elements import (ButtonBehavior, GrabBehavior, 
    TouchRippleBehavior, ThemeBehavior)
from kivy.uix.anchorlayout import AnchorLayout
from dbinterface import DBInterface
from surveyquestions import SurveyQuestion
from survey import Survey
from kivy.storage.jsonstore import JsonStore
from functools import partial
from kivy.lang import global_idmap, Builder
from flat_kivy.font_definitions import style_manager



class NavTray(BoxLayout):
    go_back_callback = ObjectProperty(None, allownone=True)
    go_forward_callback = ObjectProperty(None, allownone=True)
    ramp_group_name = StringProperty('navtray_group')

    def _go_forward(self):
        go_forward_callback = self.go_forward_callback
        if go_forward_callback is not None:
            go_forward_callback()

    def _go_back(self):
        go_back_callback = self.go_back_callback
        if go_back_callback is not None:
            go_back_callback()


class SubjectsLayout(GridLayout):
    subject_id = NumericProperty(None, allownone=True)
    questionnaire = StringProperty(None, allownone=True)


class SurveyHeader(GridLayout):
    subject_id = NumericProperty(None, allownone=True)
    questionnaire = StringProperty(None, allownone=True)
    use_parent_id = BooleanProperty(False)

    def on_questionnaire(self, instance, value):
        self.load_headers(self.subject_id)

    def on_subject_id(self, instance, value):
        self.load_headers(value)
    
    def load_headers(self, subject_id):
        ksurvey = self.kivysurvey
        headers = ksurvey.get_header_lines()
        db_interface = ksurvey.db_interface
        add_widget = self.add_widget
        if self.use_parent_id:
            try:
                subject_id = ksurvey.previous_subject_ids[-1]
            except:
                pass
        self.clear_widgets()
        for each in headers:
            content = ''
            for header in each:
                if isinstance(header, list):
                    content += str(db_interface.get_entry(
                        subject_id, header[0], header[1], header[2]))
                else:
                    content += header
                content += ' '

            if content is not '':
                label = FlatLabel(text=str(content))
 
            else:
                label = FlatLabel(text='Error Retrieving Field: ' + 
                    each[0] + each[1] + each[2])
            label.color_tuple = ('Gray', '0000')
            add_widget(label)


class SubjectButton(GrabBehavior, TouchRippleBehavior, ButtonBehavior, 
    ThemeBehavior, BoxLayout):
    of_interest = BooleanProperty(False)
    color = ListProperty([1., 1., 1., 1.])
    color_down = ListProperty([1., 1., 1., 1.])
    button_fields = ListProperty(None, allownone=True)
    font_color_tuple = ListProperty(['Grey', '1000'])
    color_tuple = ListProperty(['Blue', '500'])
    ripple_color_tuple = ListProperty(['Grey', '0000'])
    style = StringProperty(None, allownone=True)
    font_ramp_tuple = ListProperty(['default', '1'])


    def __init__(self, **kwargs):
        super(SubjectButton, self).__init__(**kwargs)

    def on_color(self, instance, value):
        self.color_down = [x*.7 for x in value]
    
    def on_button_fields(self, instance, value):
        self.clear_widgets()
        for each in value:
            if type(each) is str:
                txt = each
            else:
                txt = str(each)
            l = FlatLabel(text=txt, theme=(b'blue', b'variant_3'), 
                color_tuple=self.font_color_tuple, style=self.style,
                )
            l.font_ramp_tuple = self.font_ramp_tuple
            self.bind(font_ramp_tuple=l.setter('font_ramp_tuple'))
            self.bind(font_color_tuple=l.setter('color_tuple'))
            self.bind(style=l.setter('style'))
            
            self.add_widget(l)


class QuestionsLayout(GridLayout):
    subject_id = NumericProperty(None, allownone=True)
    questionnaire = StringProperty(None, allownone=True)
    page = StringProperty(None, allownone=True)
    manual_control = BooleanProperty(False)
    ramp_name = StringProperty('default')
    font_ramp_tuple = ListProperty(['default', '1'])

    def __init__(self, **kwargs):
        super(QuestionsLayout, self).__init__(**kwargs)
        Clock.schedule_once(self.setup)

    def load_member(self, p_id):
        pass

    def on_questionnaire(self, instance, value):
        page = self.page
        if not self.manual_control:
            if page is not None and value is not None:
                self.load_page(str(page), str(value))
                self.load_page_data()
            else:
                self.clear_all()

    def clear_all(self):
        for each in self.children:
            each.font_ramp_tuple = ('default', '1')
        self.clear_widgets()


    def on_page(self, instance, value):
        questionnaire = self.questionnaire
        if not self.manual_control:
            if questionnaire is not None and value is not None:
                self.load_page(str(value), str(questionnaire))
                self.load_page_data()
            else:
                self.clear_all()

    def save_page_data(self):
        survey = self.kivysurvey
        db_interface = survey.db_interface
        subject_id = self.subject_id
        page = self.page
        questionnaire = self.questionnaire

        if self.check_answers_valid():
            for question in self.children:
                if isinstance(question, SurveyQuestion): 
                    if not question.disabled:
                        question_name = question.question_name
                        answer = question.to_json()
                        db_interface.set_entry(subject_id, questionnaire, 
                            page, question_name, answer)

    def load_page_data(self):
        ksurvey = self.kivysurvey
        db_interface = ksurvey.db_interface
        page = self.page
        questionnaire = self.questionnaire
        subject_id = self.subject_id

        for question in self.children:
            if isinstance(question, SurveyQuestion): 
                if not question.disabled:
                    question_name = question.question_name
                    question.from_json(db_interface.get_entry(subject_id, 
                        questionnaire, page, question_name))
                    question.do_transition = False
                    Clock.schedule_once(question._schedule_validate)
                    Clock.schedule_once(question._schedule_reset_do_transition)

    def setup(self, dt):
        pass

    def load_page(self, page_name, questionnaire_name):
        survey = self.kivysurvey.survey
        questionnaire = survey.questionnaires[questionnaire_name]
        try:
            page = questionnaire.pages[page_name]
        except:
            page = None
        if page is not None:
            self.clear_all()
            questions = page.questions
            for each in page.question_order:
                question = questions[each]
                wid = question.widget
                print(wid)
                wid.font_ramp_tuple = self.font_ramp_tuple
                self.add_widget(wid)

    def check_answers_valid(self):
        answers_valid = True
        db_interface = self.kivysurvey.db_interface
        # verifier = db_interface.verifier
        # verify = verifier.verify
        # raise_error = self.app.root.raise_error
        # for question in self.children:
        #     if isinstance(question, SurveyQuestion): 
        #         if not question.disabled:
        #             if question.check_answered():
        #                 if not verify(
        #                     question.question_name, question.answer, 
        #                     self.current_individual_id):
        #                     answers_valid = False
        #                     raise_error('Answer Not Valid',
        #                         str(question.answer) + ' is not valid for ' 
        #                         + question.question_text)
        #             else:
        #                 answers_valid = False
        #                 raise_error('Questions Not Completed',
        #                     'You must answer ' + question.question_text)
        return answers_valid

    def clear_questions(self):
        self.parent.scroll_to_top()
        for question in self.children:
            if isinstance(question, SurveyQuestion):
                question.clear_question()


class SubjectsScreen(Screen):
    allow_add_subject = BooleanProperty(False)
    add_subject_button = ObjectProperty(None)
    current_subjects = ListProperty(None, allownone=True)
    font_ramp_tuple = ListProperty(['default', '1'])
    field_font_ramp_tuple = ListProperty(['default_field', '1'])

    def __init__(self, **kwargs):
        super(SubjectsScreen, self).__init__(**kwargs)
        self.add_subject_button = add_sub = FlatIconButton(
            text='Add Subject',
            size_hint=(1.0, None),
            height=str('80dp'),
            icon='fa-pencil-square',
            theme=(b'blue', b'variant_1'),
            color=(43./255., 153./255., 1.0),
            font_ramp_tuple=self.font_ramp_tuple,
            on_release=self.add_member_callback)
        self.bind(font_ramp_tuple=add_sub.setter('font_ramp_tuple'))

    def add_member_callback(self, instance):
        self.kivysurvey.add_member()

 
    def on_allow_add_subject(self, instance, value):
        nav_layout = self.ids.navtray.ids.custom
        add_subject_button = self.add_subject_button
        if value and add_subject_button not in nav_layout.children:
            nav_layout.add_widget(add_subject_button)
            
        elif not value and add_subject_button in nav_layout.children:
            nav_layout.remove_widget(add_subject_button)

    def on_current_subjects(self, instance, value):
        subjects_layout = self.ids.subjects
        for each in subjects_layout.children:
            each.font_ramp_tuple = ('default', '1')
        subjects_layout.clear_widgets()
        if value is not None:
            for each in value:
                self.add_subject(each)

    def add_subject(self, subject_id):
        #get data for displaying
        #create button
        #add button to subjects layout
        subjects_layout = self.ids.subjects
        ksurvey = self.kivysurvey
        db_interface = ksurvey.db_interface
        get_entry = db_interface.get_entry
        survey = ksurvey.survey
        questionnaire = ksurvey.questionnaire
        current_page = ksurvey.current_page.page
        fields = survey.get_subject_fields(questionnaire)
        new_fields = []
        new_fields_a = new_fields.append
        for each in fields:
            if isinstance(each, list):
                new_fields_a(get_entry(subject_id, each[0], each[1], each[2]))
            else:
                new_fields_a(each)
        new_button = SubjectButton(
            on_release=partial(ksurvey.open_member, 
            subject_id),
            font_ramp_tuple=self.field_font_ramp_tuple)
        self.bind(field_font_ramp_tuple=new_button.setter('font_ramp_tuple'))
        subjects_layout.add_widget(new_button)
        new_button.button_fields = new_fields



class QuestionnaireScreen(Screen):
    page = StringProperty(None, allownone=True)
    name = StringProperty('question_screen_group')


class KivySurvey(ScreenManager):
    current_page = ObjectProperty(None, allownone=True)
    current_subjects = ListProperty(None, allownone=True)
    db_interface = ObjectProperty(None)
    current_subjects = ListProperty(None, allownone=True)
    subject_id = NumericProperty(None, allownone=True)
    previous_subject_ids = ListProperty(None, allownone=True)
    current_page = ObjectProperty(None, allownone=True)
    current_subjects_page = ObjectProperty(None, allownone=True)
    next_page = StringProperty(None, allownone=True)
    prev_page = StringProperty(None, allownone=True)
    survey = ObjectProperty(None)
    current_location = DictProperty({})
    gps_loc_interval = NumericProperty(30.0)
    questionnaire = StringProperty(None, allownone=True)
    top_level_questionnaire = StringProperty(None, allownone=True)
    root = ObjectProperty(None)

    def __init__(self, **kwargs):
        global_idmap.update({'kivysurvey': self})
        self.db_interface = DBInterface(self)
        super(KivySurvey, self).__init__(**kwargs)
        self.transition = SlideTransition()
        json = JsonStore(construct_target_file_name('survey.json', __file__))
        for each in json:
            print(each)
        self.survey = Survey(json)
        try:
            gps.configure(on_location=self.receive_gps)
        except:
            pass
        Clock.schedule_once(self.start_gps)

    def on_subject_id(self, instance, value):
        self.load_subjects(value, self.questionnaire)

    def create_subject(self):
        db_interface = self.db_interface
        uid = db_interface.get_unique_id()
        prev_id = self.previous_subject_ids[-1]
        db_interface.add_subject(prev_id, self.questionnaire, uid)
        return uid

    def pop_subjects(self):
        previous_subject_ids = self.previous_subject_ids
        if len(previous_subject_ids) > 0:
            self.subject_id = self.previous_subject_ids.pop()
        else:
            self.subject_id = None
              
    def on_questionnaire(self, instance, value):
        self.load_subjects(self.subject_id, value)
        self.current_subjects_page.allow_add_subject = (
            self.survey.get_allow_add_subjects(value))

    def load_subjects(self, subject_id, questionnaire):
        self.current_subjects = self.db_interface.get_subjects(
            subject_id, questionnaire)

    def get_header_lines(self):
        return self.survey.get_header_definitions(self.questionnaire)

    def set_next_page(self):
        survey = self.survey
        next_page = survey.get_next_page(
            self.questionnaire, self.current_page.page)
        
        if next_page is None:
            return False
        else:
            self.next_page = None
            self.next_page = next_page
            return True

    def add_member(self):
        self.transition.direction = 'left'
        self.previous_subject_ids.append(self.subject_id)
        self.subject_id = None
        self.reset_questionnaire()

    def open_member(self, member_id, instance):
        self.transition.direction = 'left'
        self.previous_subject_ids.append(self.subject_id)
        self.subject_id = member_id
        self.reset_questionnaire()
        current_page = self.current_page.ids.questions
        current_page.load_page_data()

    def reset_questionnaire(self):
        self.current_page.page = None
        self.set_next_page() 
        self.swap_pages()
        self.current_page.ids.questions.clear_questions()

    def set_prev_page(self):
        survey = self.survey
        prev_page = survey.get_prev_page(
            self.questionnaire, self.current_page.page)
        if prev_page is None:
            return False
        else:
            self.prev_page = prev_page
            return True

    def swap_subjects(self):
        subjects1 = self.ids.subjects1
        subjects2 = self.ids.subjects2
        current_subjects_page = self.current_subjects_page
        if current_subjects_page is subjects1:
            self.current = 'subjects2'
            self.current_subjects_page = subjects2
        elif current_subjects_page is subjects2:
            self.current = 'subjects1'
            self.current_subjects_page = subjects1
        self.current_subjects_page.allow_add_subject = (
            self.survey.get_allow_add_subjects(self.questionnaire))
        self.current_page.ids.scrollview.scroll_to_top()

    def swap_pages(self):

        questions1 = self.ids.questions1
        questions2 = self.ids.questions2
        current_page = self.current_page
        if current_page is questions1:
            self.current = 'questions2'
            self.current_page = questions2
            questions1.page = None
        elif current_page is questions2:
            self.current = 'questions1'
            self.current_page = questions1
            questions2.page = None
        self.current_page.ids.scrollview.scroll_to_top()

    def on_next_page(self, instance, value):
        questions1 = self.ids.questions1
        questions2 = self.ids.questions2
        current_page = self.current_page
        if current_page is questions1:
            questions2.page = value
        elif current_page is questions2:
            questions1.page = value

    def on_prev_page(self, instance, value):
        questions1 = self.ids.questions1
        questions2 = self.ids.questions2
        current_page = self.current_page
        if current_page is questions1:
            questions2.page = value
        elif current_page is questions2:
            questions1.page = value

    def start_questionnaire(self, questionnaire):
        self.current_page.page = None
        self.swap_subjects()
        self.questionnaire = questionnaire
        self.set_next_page()

    def save_page(self):
        current_page = self.current_page.ids.questions
        current_page.save_page_data()


    def go_back(self):
        does_page_exist = self.set_prev_page()
        survey = self.survey
        questionnaire = self.questionnaire
        prev_questionnaire = survey.get_previous_questionnaire()
        self.transition.direction = 'right'
        if self.current in ['subjects1', 'subjects2']:
            if prev_questionnaire is None:
                self.app.root.change_screen('cluster', go_back=True)
                return
            else:
                if survey.get_allow_add_subjects(questionnaire):
                    self.pop_subjects()
                self.start_questionnaire(survey.pop_previous_questionnaire())
        elif does_page_exist:
            self.swap_pages()
        else:
            if self.subject_id is None:
                self.pop_subjects()
                self.swap_subjects()
            else:
                self.pop_subjects()
                self.swap_subjects()

    def go_forward(self):
        does_page_exist = self.set_next_page()
        survey = self.survey
        questionnaire = self.questionnaire
        next_questionnaire = survey.get_next_questionnaire(questionnaire)
        self.transition.direction = 'left'
        if self.current in ['subjects1', 'subjects2']:
            if next_questionnaire is None:
                if survey.get_allow_add_subjects(questionnaire):
                    self.pop_subjects()
                prev_questionnaire = survey.pop_previous_questionnaire()
                self.start_questionnaire(prev_questionnaire)
            else:
                if survey.get_allow_forward(questionnaire):
                    survey.store_current_questionnaire(questionnaire)
                    self.start_questionnaire(next_questionnaire)
        elif does_page_exist:
            self.save_page()
            self.swap_pages()
        else:
            is_creating_subject = False
            if survey.get_allow_add_subjects(questionnaire) and (
                self.subject_id is None):
                self.subject_id = self.create_subject()
            self.save_page()
            if next_questionnaire is None:
                self.pop_subjects()
                prev_questionnaire = survey.pop_previous_questionnaire()
                self.start_questionnaire(prev_questionnaire)
            elif survey.get_allow_add_subjects(next_questionnaire):
                survey.store_current_questionnaire(questionnaire)
                self.start_questionnaire(next_questionnaire)
            else:
                self.pop_subjects()
                self.swap_subjects()

    def start_gps(self, dt):
        try:
            gps.start()
        except:
            pass

    def receive_gps(self, **kwargs):
        if kwargs is not {}:
            self.current_location = kwargs
            gps.stop()
            Clock.schedule_once(self.start_gps, self.gps_loc_interval)

    def raise_error(self, error_title, error_text):
        self.app.raise_error(error_title, error_text)

    def raise_option_dialogue(self, option_title, option_text, options, 
            callback):
        self.app.raise_option_dialogue(option_title, option_text, options,
            callback)

    def raise_numpad(self, numpad_title, callback, units=None,
        minimum=None, maximum=None, do_decimal=False):
        self.app.raise_numpad(numpad_title, callback, units, 
            minimum, maximum, do_decimal)


class KivySurveyApp(FlatApp):
    kivy_survey = ObjectProperty(None)

    def __init__(self, **kwargs):

        self.setup_font_ramps()
        super(KivySurveyApp, self).__init__(**kwargs)
        self.setup_themes()
        

    def build(self):
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)  
        return self.setup_kivy_survey()

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            self.root.go_back()
            return True

    def setup_font_ramps(self):
        font_styles = {
            'Display 4': {
                'font': 'Roboto-Light.ttf', 
                'sizings': {'mobile': (112, 'sp'), 'desktop': (112, 'sp')},
                'alpha': .65,
                'wrap': False,
                }, 
            'Display 3': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (56, 'sp'), 'desktop': (56, 'sp')},
                'alpha': .65,
                'wrap': False,
                },
            'Display 2': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (45, 'sp'), 'desktop': (45, 'sp')},
                'alpha': .65,
                'wrap': True,
                'wrap_id': '1',
                'leading': (48, 'pt'),
                },
            'Display 1': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (34, 'sp'), 'desktop': (34, 'sp')},
                'alpha': .65,
                'wrap': True,
                'wrap_id': '2',
                'leading': (40, 'pt'),
                },
            'Headline': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (24, 'sp'), 'desktop': (24, 'sp')},
                'alpha': .87,
                'wrap': True,
                'wrap_id': '3',
                'leading': (32, 'pt'),
                },
            'Title': {
                'font': 'Roboto-Medium.ttf', 
                'sizings': {'mobile': (20, 'sp'), 'desktop': (20, 'sp')},
                'alpha': .87,
                'wrap': False,
                },
            'Subhead': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (16, 'sp'), 'desktop': (15, 'sp')},
                'alpha': .87,
                'wrap': True,
                'wrap_id': '4',
                'leading': (28, 'pt'),
                },
            'Body 2': {
                'font': 'Roboto-Medium.ttf', 
                'sizings': {'mobile': (14, 'sp'), 'desktop': (13, 'sp')},
                'alpha': .87,
                'wrap': True,
                'wrap_id': '5',
                'leading': (24, 'pt'),
                },
            'Body 1': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (14, 'sp'), 'desktop': (13, 'sp')},
                'alpha': .87,
                'wrap': True,
                'wrap_id': '6',
                'leading': (20, 'pt'),
                },
            'Caption': {
                'font': 'Roboto-Regular.ttf', 
                'sizings': {'mobile': (12, 'sp'), 'desktop': (12, 'sp')},
                'alpha': .65,
                'wrap': False,
                },
            'Menu': {
                'font': 'Roboto-Medium.ttf', 
                'sizings': {'mobile': (14, 'sp'), 'desktop': (13, 'sp')},
                'alpha': .87,
                'wrap': False,
                },
            'Button': {
                'font': 'Roboto-Medium.ttf', 
                'sizings': {'mobile': (14, 'sp'), 'desktop': (14, 'sp')},
                'alpha': .87,
                'wrap': False,
                },
            }
        for each in font_styles:
            style = font_styles[each]
            sizings = style['sizings']
            style_manager.add_style(style['font'], each, sizings['mobile'], 
                sizings['desktop'], style['alpha'])

        style_manager.add_font_ramp('1', ['Display 2', 'Display 1', 
            'Headline', 'Subhead', 'Body 2', 'Body 1'])

    def setup_themes(self):
        self.theme_manager.add_theme_type('SubjectButton', SubjectButton)
        variant_1 = {
            'FlatButton':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_duration_in': .1,
                'ripple_scale': 2.0,
                },
            'FlatIconButton':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_scale': 2.0,
                'ripple_duration_in': .1,
                'icon_color_tuple': ('Gray', '1000')
                },
            'FlatToggleButton':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_duration_in': .1,
                'ripple_scale': 2.0,
                },
            'FlatCheckBox':{
                'color_tuple': ('Gray', '0000'),
                'ripple_color_tuple': ('Cyan', '100'),
                'check_color_tuple': ('LightBlue', '500'),
                'outline_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_scale': 2.0,
                'check_scale': .7,
                'ripple_duration_in': .07,
                'outline_size': '10dp',
                },
            'CheckBoxListItem':{
                'color_tuple': ('Gray', '0000'),
                'ripple_color_tuple': ('Cyan', '100'),
                'check_color_tuple': ('LightBlue', '500'),
                'outline_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_scale': 2.0,
                'check_scale': .7,
                'ripple_duration_in': .1,
                'outline_size': '10dp',
                },
            }

        variant_2 = {
            'FlatButton':{
                'color_tuple': ('Green', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_duration_in': .1,
                'ripple_scale': 2.0,
                },
            'FlatIconButton':{
                'color_tuple': ('Green', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_scale': 2.0,
                'ripple_duration_in': .1,
                'icon_color_tuple': ('Gray', '1000')
                },
            }
        variant_3 = {
            'FlatIconButton':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_scale': 2.0,
                'ripple_duration_in': .1,
                'icon_color_tuple': ('Gray', '1000')
                },
            'FlatLabel': {
                'style': 'Display 2',
                'color_tuple': ('Gray', '1000'),
                },
            'FlatToggleButton':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_duration_in': .1,
                'ripple_scale': 2.0,
                },
            'SubjectButton':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_duration_in': .1,
                'ripple_scale': 2.0,
                },
            'CheckBoxListItem':{
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'style': 'Display 2',
                'ripple_scale': 2.0,
                'ripple_duration_in': .07,
                'icon_color_tuple': ('Gray', '1000'),
                'check_color_tuple': ('LightBlue', '500'),
                },
            }
        question_headings = {
            'FlatLabel': {
                'style': 'Display 1',
                'color_tuple': ('Gray', '1000'),
                'do_resize': False
                },
            }
        position_titles = {
            'FlatLabel': {
                'style': 'Display 1',
                'color_tuple': ('LightBlue', '900'),
                'do_resize': True
                },
            }
        numpad = {
            'FlatButton': {
                'style': 'Display 2',
                'color_tuple': ('LightBlue', '500'),
                'ripple_color_tuple': ('Cyan', '100'),
                'font_color_tuple': ('Gray', '1000'),
                'ripple_scale': 2.0,
                'ripple_duration_in': .07,

                },
            }
        self.theme_manager.add_theme('blue', 'variant_1', variant_1)
        self.theme_manager.add_theme('blue', 'variant_2', variant_2)
        self.theme_manager.add_theme('blue', 'variant_3', variant_3)
        self.theme_manager.add_theme('blue', 'question_headings', 
            question_headings)
        self.theme_manager.add_theme('blue', 'position_titles', 
            position_titles)
        self.theme_manager.add_theme('blue', 'numpad', numpad)

    def setup_kivy_survey(self):
        if __name__ != '__main__':
            self.kivy_survey = survey = Builder.load_file(
                construct_target_file_name('kivysurvey.kv', __file__))
        else:
            self.kivy_survey = survey = KivySurvey()
        survey.current_page = current_page = survey.ids.questions1
        survey.current_subjects_page = survey.ids.subjects1
        db_interface = survey.db_interface
        survey.start_questionnaire('household_questionnaire')
        survey.subject_id = 0
        return survey



if __name__ == '__main__':
    KivySurveyApp().run()