from __future__ import unicode_literals, print_function
from jsontowidget import widget_from_json


class Survey(object):
    def __init__(self, json_survey, **kwargs):
        super(Survey, self).__init__(**kwargs)
        self.survey_file = json_survey
        self.questionnaires = {}
        self.prev_questionnaires = []
        self.load_questionnaires()

    def load_questionnaires(self):
        json_data = self.survey_file['survey']
        qs = self.questionnaires
        for each in json_data:
            qs[each] = Questionnaire(each, self)

    def get_header_definitions(self, questionnaire):
        q = self.questionnaires[questionnaire]
        return q.headers

    def get_subject_fields(self, questionnaire):
        q = self.questionnaires[questionnaire]
        return q.subject_fields

    def get_next_page(self, questionnaire, current_page):
        q = self.questionnaires[questionnaire]
        page_order = q.page_order
        if current_page is None:
            return page_order[0]
        else:
            index = page_order.index(current_page)
            if index+1 < len(page_order):
                return page_order[index+1]
            else:
                return None

    def get_prev_page(self, questionnaire, current_page):
        q = self.questionnaires[questionnaire]
        page_order = q.page_order
        if current_page is None:
            return page_order[-1]
        else:
            index = page_order.index(current_page)
            if index-1 >= 0:
                return page_order[index-1]
            else:
                return None

    def get_next_questionnaire(self, current_questionnaire):
        q = self.questionnaires[current_questionnaire]
        return q.next_questionnaire

    def get_allow_forward(self, current_questionnaire):
        q = self.questionnaires[current_questionnaire]
        return q.allow_forward

    def store_current_questionnaire(self, current_questionnaire):
        self.prev_questionnaires.append(current_questionnaire)        

    def get_previous_questionnaire(self):
        try:
            return self.prev_questionnaires[-1]
        except:
            return None

    def pop_previous_questionnaire(self):
        try:
            return self.prev_questionnaires.pop()
        except:
            return None

    def get_allow_add_subjects(self, questionnaire):
        try:
            return self.questionnaires[questionnaire].add_subjects
        except:
            return False

        

class Questionnaire(object):

    def __init__(self, name, survey, **kwargs):
        super(Questionnaire, self).__init__(**kwargs)
        self.survey = survey
        self.page_order = []
        self.headers = []
        self.name = name
        json_data = survey.survey_file['survey'][name]
        self.load_pages(name, survey)
        self.load_headers(name, survey)
        self.load_subject_fields(name, survey)
        if 'next_questionnaire' in json_data:
            self.next_questionnaire = json_data["next_questionnaire"]
        else:
            self.next_questionnaire = None
        if 'add_subjects' in json_data:
            self.add_subjects = json_data["add_subjects"]
        else:
            self.add_subjects = False
        if 'allow_forward' in json_data:
            self.allow_forward = json_data["allow_forward"]
        else:
            self.allow_forward = False
        if 'demographic' in json_data:
            self.demographic = json_data['demographic']
        if 'demographic_restrictions' in json_data:
            self.demographic_restrictions = json_data['demographic_restrictions']


    def load_subject_fields(self, name, survey):
        json_data = survey.survey_file['survey'][name]
        self.subject_fields = json_data['subject_fields']

    def load_headers(self, name, survey):
        json_data = survey.survey_file['survey'][name]
        self.headers = json_data['headers']

    def load_pages(self, name, survey):
        json_data = survey.survey_file['survey'][name]
        pages_json = json_data['pages']
        pages = self.pages = {}
        self.page_order = json_data['page_order']
        for each in pages_json:
            p = Page(each, name, survey)
            pages[each] = p


class Page(object):

    def __init__(self, name, questionnaire_name, survey, **kwargs):
        super(Page, self).__init__(**kwargs)
        self.q_name = questionnaire_name
        self.survey = survey
        self.name = name
        self.question_order = []
        self.load_questions(name, questionnaire_name, survey)

    def load_questions(self, name, q_name, survey):
        json_data = survey.survey_file['survey'][q_name]['pages'][name]
        questions_json = json_data['questions']
        questions = self.questions = {}
        self.question_order = json_data['question_order']
        if 'disable_binds' in json_data:
            self.disable_binds = disable_binds = json_data['disable_binds']
        else:
            self.disable_binds = disable_binds = []
        for each in questions_json:
            q = Question(each, questions_json[each])
            questions[each] = q
        for bind in disable_binds:
            a, b = bind
            q1 = questions[a]
            q2 = questions[b]
            wid1 = q1.widget
            wid2 = q2.widget
            wid1.bind(answer=q2.call_disable_bind)
            wid2.bind(answer=q1.call_disable_bind)
    


class Question(object):
    
    def __init__(self, question_name, question_json, **kwargs):
        super(Question, self).__init__(**kwargs)
        self.widget = wid = widget_from_json(question_json)
        wid.question_name = question_name

    def call_disable_bind(self, instance, value):
        if instance.validate_question():
            self.widget.disabled = True
        else:
            self.widget.disabled = False
