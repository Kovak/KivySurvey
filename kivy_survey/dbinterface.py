from __future__ import unicode_literals, print_function
from datetime import datetime, timedelta, date
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock

class DBInterface(object):

    def __init__(self, kivysurvey, **kwargs):
        super(DBInterface, self).__init__(**kwargs)
        date = self.convert_time_to_json_ymd(self.get_time())
        self.data = data = JsonStore('data/' + date + '.json')
        self.reset_timers = reset_timers = JsonStore('data/reset_timers.json')
        if 'survey_data' not in data:
            data['survey_data'] = {}
        self.kivysurvey = kivysurvey
        #We will preserve entry 0 for application and configuration data
        self.subject_ids = 1
        sub_id = self.get_entry(0, 'data', 'config', 'subject_ids')
        if sub_id is not None:
            self.subject_ids = sub_id
        self.sync = Clock.create_trigger(self.trigger_sync)
        self.check_reset()

    def check_reset(self):
        reset_timers = self.reset_timers
        current_time = self.get_time()
        keys_to_del = []
        for each in reset_timers:
            expire_time = self.convert_time_from_json(each)
            if expire_time < current_time:
                data = reset_timers[each]
                self.set_entry(data['subject_id'], data['questionnaire'], 
                    data['page'], data['question'], None)
                keys_to_del.append(each)
        for key in keys_to_del:
            reset_timers.delete(key)
            

    def trigger_sync(self, dt):
        data = self.data
        data._is_changed = True
        data.store_sync()

    def get_entry(self, subject_id, questionnaire, page, question):
        data = self.data['survey_data']
        try:
            return data[str(
                subject_id)][questionnaire][page][question]['answer']
        except:
            return None

    def get_subjects(self, subject_id, questionnaire):
        data = self.data['survey_data']
        survey = self.kivysurvey.survey
        q = survey.questionnaires[questionnaire]
        if hasattr(q, 'demographic'):
            real_questionnaire = q.demographic
        else:
            real_questionnaire = questionnaire
        try:
            questionnaire_data = data[str(subject_id)][real_questionnaire]
        except:
            return []
        try:
            original_subjects = questionnaire_data['subjects']
        except:      
            return []
        if hasattr(q, 'demographic_restrictions'):
            restrictions = q.demographic_restrictions
            subjects_to_return = []
            sub_a = subjects_to_return.append
            for each in original_subjects:
                status = True
                for restric in restrictions:
                    data = self.get_entry(each, restric[0], restric[1], 
                        restric[2])
                    restric_type = type(restric[3])
                    if restric_type is list:
                        minimum, maximum = restric[3]
                        if not minimum <= data <= maximum:
                            status = False

                    elif restric_type is unicode:
                        if not data == restric[3]:
                            status = False
                if status:
                    sub_a(each)
            return subjects_to_return
        else:
            return original_subjects


    def add_subject(self, subject_id, questionnaire, subject_id_to_add):
        data = self.data['survey_data']
        subject_id = str(subject_id)
        if subject_id not in data:
            data[subject_id] = subject_data = {}
        else:
            subject_data = data[subject_id]
        if questionnaire not in subject_data:
            subject_data[questionnaire] = q_data = {'subjects': []}
        else:
            q_data = subject_data[questionnaire]
        q_data['subjects'].append(subject_id_to_add)

    def get_unique_id(self):
        ret_id = self.subject_ids
        self.subject_ids += 1
        self.set_entry(0, 'data', 'config', 'subject_ids', self.subject_ids)
        return ret_id

    def set_entry(self, subject_id, questionnaire, page, question, answer, 
        do_reset=False, reset_in_hours=None):
        data = self.data['survey_data']
        s_id = str(subject_id)
        if s_id not in data:
            data[s_id] = subject_data = {}
        else:
            subject_data = data[s_id]
        if questionnaire not in subject_data:
            subject_data[questionnaire] = q_data = {}
        else:
            q_data = subject_data[questionnaire]
        if page not in q_data:
            q_data[page] = page_data = {}
        else:
            page_data = q_data[page]
        if question not in page_data:
            page_data[question] = q_data = {'answer': None, 'history': {}}
        else:
            q_data = page_data[question]
        if q_data['answer'] != answer:
            time = self.get_time()
            time_stamp = self.convert_time_to_json(time)
            q_data['history'][time_stamp] = answer
            q_data['answer'] = answer
        
            self.sync()
            if do_reset:
                timed = timedelta(hours=reset_in_hours)
                expire_time = time + timed
                expires_at = self.convert_time_to_json(expire_time)
                reset_timers = self.reset_timers
                reset_timers[expires_at] = {'subject_id': subject_id, 
                    'questionnaire': questionnaire,
                    'page': page,
                    'question': question}

    def get_time(self):
        return datetime.utcnow()

    def convert_time_to_json_ymd(self, datetime):
        if datetime is not None:
            return datetime.strftime('%Y-%m-%d')
        else:
            return None

    def convert_time_to_json(self, datetime):
        if datetime is not None:
            return datetime.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            return None

    def convert_time_from_json(self, jsontime):
        if jsontime is not None:
            return datetime.strptime(jsontime, '%Y-%m-%dT%H:%M:%S')
        else:
            return None
