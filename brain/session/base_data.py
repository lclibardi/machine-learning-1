#!/usr/bin/python

## @base_data.py
#  This file serves as the superclass for 'data_xx.py' files.
#
#  Note: the term 'dataset' used throughout various comments in this file,
#        synonymously implies the user supplied 'file upload(s)', and XML url
#        references.
from brain.database.save_entity import Save_Entity
from brain.database.save_dataset import Save_Dataset
from brain.validator.validate_dataset import Validate_Dataset
from brain.validator.validate_mime import Validate_Mime
from brain.converter.convert_upload import Convert_Upload
from brain.database.save_label import Save_Label

## Class: Base_Data, explicitly inherit 'new-style' class
#
#  Note: this class is invoked within 'data_xx.py'
class Base_Data(object):

    ## constructor:
    def __init__(self, svm_data):
        self.flag_validate_mime = False
        self.observation_labels = []

    ## validate_mime_type: validate mime type for each dataset.
    def validate_mime_type(self):
        validator = Validate_Mime(self.svm_data, self.svm_session)
        self.response_mime_validation = validator.validate()

        if self.response_mime_validation['error'] != None:
            self.response_error.append(self.response_mime_validation['error'])
            self.flag_validate_mime = True

    ## save_svm_entity: save the current entity into the database, then return
    #                   the corresponding entity id.
    def save_svm_entity(self, session_type):
        svm_entity = {'title': self.svm_data['data']['settings'].get('svm_title', None), 'uid': 1, 'id_entity': None}
        db_save    = Save_Entity(svm_entity, session_type)

        # save dataset element
        db_return  = db_save.save()

        # return error(s)
        if not db_return['status']:
            self.response_error.append(db_return['error'])
            return {'status': False, 'id': None, 'error': self.response_error}

        # return session id
        elif db_return['status'] and session_type == 'data_new':
            return {'status': True, 'id': db_return['id'], 'error': None}

    ## validate_dataset: validate each dataset element.
    def validate_dataset(self):
        for list in self.dataset:
            for val in list['svm_dataset']:
                validated_dataset = Validate_Dataset(val, self.svm_session)

            if validated_dataset.validate()['error']:
                self.response_error.append(validated_dataset.validate()['error'])

    ## save_svm_dataset: save each dataset element into a database table.
    def save_svm_dataset(self, session_type):
        for data in self.dataset:
            for dataset in data['svm_dataset']:
                db_save = Save_Dataset({'svm_dataset': dataset, 'id_entity': data['id_entity']}, session_type)

                # save dataset element, append error(s)
                db_return = db_save.save()
                if db_return['error']: self.response_error.append(db_return['error'])

    ## save_observation_label: save the list of unique independent variable labels
    #                          from a supplied session (entity id) into the database.
    #
    #  @self.observation_labels, list of features (independent variables), defined
    #      after invoking the 'dataset_to_dict' method.
    #
    #  @session_id, the corresponding returned session id from invoking the
    #      'save_svm_entity' method.
    def save_observation_label(self, session_type, session_id):
        if len(self.observation_labels) > 0:
            for label in self.observation_labels:
                db_save = Save_Label({'label': label, 'id_entity': session_id}, session_type)

                # save dataset element, append error(s)
                db_return = db_save.save()
                if not db_return['status']: self.response_error.append(db_return['error'])

    ## dataset_to_dict: convert either csv, or xml dataset(s) to a uniform
    #                   dict object.
    #
    #  @flag_convert, when true, indicates the file-upload mime type passed
    #      validation, and returned unique file(s) (redundancies removed).
    #
    #  @flag_append, when false, indicates the neccessary 'self.dataset' was
    #      not properly defined, causing this method to 'return', which
    #      essentially stops the execution of the current session.
    #
    #  @index_count, used to 'check label consistent'.
    def dataset_to_dict(self, id_entity):
        flag_convert = False
        flag_append  = True
        index_count  = 0

        try:
            self.response_mime_validation['dataset']['file_upload']
            flag_convert = True
        except Exception as error:
            self.response_error.append(error)
            print error
            return False

        if (flag_convert):
            self.dataset = []
            svm_property = self.svm_data

            for val in self.response_mime_validation['dataset']['file_upload']:
                # reset file-pointer
                val['file'].seek(0)

                # csv to dict
                if val['type'] in ('text/plain', 'text/csv'):
                    try:
                        # conversion
                        dataset_converter = Convert_Upload(val['file'])
                        dataset_converted = dataset_converter.csv_to_dict()

                        # check label consistency, assign labels
                        if index_count > 0 and sorted(dataset_converter.get_observation_labels()) != self.observation_labels: self.response_error.append('The supplied observation labels (dependent variables), are inconsistent')
                        self.observation_labels = sorted(dataset_converter.get_observation_labels())

                        # build new (relevant) dataset
                        self.dataset.append({'id_entity': id_entity, 'svm_dataset': dataset_converted})
                    except Exception as error:
                        self.response_error.append(error)
                        flag_append = False

                # xml to dict
                elif val['type'] in ('application/xml', 'text/xml' ):
                    try:
                        # conversion
                        dataset_converter = Convert_Upload(val['file'])
                        dataset_converted = dataset_converter.xml_to_dict()

                        # check label consistency, assign labels
                        if index_count > 0 and sorted(dataset_converter.get_observation_labels()) != self.observation_labels: self.response_error.append('The supplied observation labels (dependent variables), are inconsistent')
                        self.observation_labels = sorted(dataset_converter.get_observation_labels())

                        # build new (relevant) dataset
                        self.dataset.append({'id_entity': id_entity, 'svm_dataset': dataset_converted})
                    except Exception as error:
                        self.response_error.append(error)
                        flag_append = False

            index_count += 1
            if not flag_append: return False

