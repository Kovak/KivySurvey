import kivy
from kivy.storage.jsonstore import JsonStore

survey = {
	"household_questionnaire": 
		{"pages": {"household1": 
			{"questions": 
				{"household_id": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Enter Household ID: "
						}
					}
				}, 
			"question_order": ["household_id", ]},
			}, 
		"page_order": ["household1", ],
		"headers": [('Enter Households for Cluster', 
			('data', 'cluster', 'current_cluster'))],
		"next_questionnaire": "add_member",
		"allow_forward": False,
		"add_subjects": True,
		"subject_fields": ['Household', 
			('household_questionnaire', 'household1', 'household_id')]
		},
	"add_member":
		{"pages": {"addmember1": 
			{"questions": 
				{"name": 
					{"type": "SurveyQuestionTextInput", 
					"args": {
						"question_text": "Enter Name: "
						}
					},
				"age": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Age in completed years: "
						}
					},
				"gender": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": "Gender: ",
						"answer_group": 'gender',
						"answer1_text": 'M',
						'answer2_text': 'F',
						}
					},
				"status": 
					{"type": "CheckboxQuestion", 
					"args": {
						"question_text": "Status: ",
						"group": 'born_joined',
						"answers": ['Born during recall period', 
							'Joined household during recall period'],
						"allow_no_answer": True,
						}
					},
				}, 
			"question_order": ["name", "age", "gender", "status"]},
			},
		"page_order": ["addmember1"],
		"add_subjects": True,
		"allow_forward": True,
		"next_questionnaire": "child_survey",
		"headers": [('Add Member for Household', 
			('household_questionnaire', 'household1', 'household_id'))],
		"subject_fields": [('add_member', 'addmember1', 'name'), 
			('add_member', 'addmember1', 'age'),
			('add_member', 'addmember1', 'gender')]
		},
	"child_survey":
		{"pages": {"child_survey1": 
			{"questions": 
				{"birthdate": 
					{"type": "SurveyQuestionBirthDate", 
					"args": {
						"question_text": "Enter Date of Birth: "
						}
					},
				"age_in_months": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Age in Months: ",
						"do_decimal": False,

						}
					},
				"weight": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Record Weight: ",
						"units": "kg",
						"do_decimal": True,
						}
					},
				"height": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Record Weight: ",
						"units": "cm",
						"do_decimal": True,
						}
					},
				"height_type": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": "Type of Height Measurement: ",
						"answer1_text": 'Child Standing (Height)',
						"answer2_text": 'Child Recumbent (Length)',
						}
					},
				"muac": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Record MUAC: ",
						"units": "mm",
						"do_decimal": True,
						}
					},
				"edema": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": "Is Bilateral Edema Present?",
						"answer_group": 'edema_question'
						}
					},
				}, 
			"question_order": ["birthdate", "age_in_months", "weight", "height", 
				"height_type","muac", "edema"],
			"disable_binds": [("birthdate", "age_in_months")],},
			"child_survey2": 
				{"questions":
				{"diarrhoea": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": 
							"In the last two weeks, has the child had diarrhoea?",
						"allow_no_answer": True,
						}
					},
				},
				"question_order": ['diarrhoea']
			},
			},
		"page_order": ["child_survey1", 'child_survey2'],
		"add_subjects": False,
		"allow_forward": True,
		"demographic_restrictions": [('add_member', 
			'addmember1', 'age', (0, 6))],
		"demographic": 'add_member',
		"next_questionnaire": "women_survey",
		"headers": [('Child Survey for Household', 
			('household_questionnaire', 'household1', 'household_id'))],
		"subject_fields": [('add_member', 'addmember1', 'name'), 
			('add_member', 'addmember1', 'age'),
			('add_member', 'addmember1', 'gender')]
		},
	"women_survey":
		{"pages": {"women_survey1": 
			{"questions": 
				{"weight": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Record Weight: ",
						"units": "kg",
						"do_decimal": True,
						}
					},
				"height": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Record Weight: ",
						"units": "cm",
						"do_decimal": True,
						}
					},
				"muac": 
					{"type": "SurveyQuestionNumerical", 
					"args": {
						"question_text": "Record MUAC: ",
						"units": "mm",
						"do_decimal": True,
						}
					},
				"pregnant": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": "Are you currently pregnant?",
						"allow_no_answer": True,
						"answer_group": 'pregnant_question',
						}
					},
				"breastfeeding": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": "Are you currently breastfeeding?",
						"allow_no_answer": True,
						"answer_group": 'breastfeeding_question',
						}
					},
				}, 
			"question_order": ["weight", "height", "muac", 
			"pregnant", "breastfeeding"],},
		"women_survey2": 
			{"questions":
				{"ever_pregnant": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": 
							"Have you ever been pregnant?",
						"allow_no_answer": True,
						"answer_group": 'ever_pregnant'
						}
					},
				"ante-natal_care": 
					{"type": "SurveyQuestionYesNo", 
					"args": {
						"question_text": 
							"When you were pregnant, did you receive any ante-natal care?",
						"allow_no_answer": True,
						"answer_group": 'ante-natal'
						}
					},
				},
				"question_order": ['ever_pregnant', 'ante-natal_care']
			},},
		"page_order": ["women_survey1", "women_survey2"],
		"add_subjects": False,
		"allow_forward": True,
		"demographic_restrictions": [('add_member', 
			'addmember1', 'age', (15, 49)), ('add_member', 
			'addmember1', 'gender', 'F')],
		"demographic": 'add_member',
		"headers": [('Women Survey for Household', 
			('household_questionnaire', 'household1', 'household_id'))],
		"subject_fields": [('add_member', 'addmember1', 'name'), 
			('add_member', 'addmember1', 'age'),
			('add_member', 'addmember1', 'gender')]
		},
	
}

json = JsonStore('survey.json')
json['survey'] = survey