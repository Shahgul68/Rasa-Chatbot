import logging
import os
import sys
import traceback
import pandas as pd
import numpy as np
import spacy
from sklearn.metrics.pairwise import cosine_similarity

# Initialize logger first
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
    
logging.basicConfig(
    filename='logging.log',
    filemode='a',
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG
)

# Lazy loading for spaCy model and data
_nlp = None
_diagnosis_df = None
_symptoms_df = None

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            logging.info("Loading spaCy model...")
            _nlp = spacy.load('en_core_web_sm')
            # Test the model
            test_doc = _nlp("test")
            if not hasattr(test_doc, 'vector'):
                raise ValueError("spaCy model loaded but doesn't have vector attribute")
            logging.info("spaCy model loaded successfully")
        except Exception as e:
            logging.error(f"Error loading spaCy model: {str(e)}")
            logging.error(traceback.format_exc())
            try:
                logging.info("Attempting to download spaCy model...")
                import subprocess
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                _nlp = spacy.load('en_core_web_sm')
                logging.info("spaCy model downloaded and loaded successfully")
            except Exception as e2:
                logging.error(f"Failed to download spaCy model: {str(e2)}")
                logging.error(traceback.format_exc())
                raise
    return _nlp

def get_diagnosis_df():
    global _diagnosis_df
    if _diagnosis_df is None:
        _diagnosis_df = pd.read_pickle("input_data/diagnosis_data.pkl")
    return _diagnosis_df

def get_symptoms_df():
    global _symptoms_df
    if _symptoms_df is None:
        _symptoms_df = pd.read_pickle("input_data/symptoms.pkl")
    return _symptoms_df

def encode_symptom(symptom):
    '''
    Convert symptom string to vector using spacy

    :param symptom: Symptom description as string
    :return: Vector representation of the symptom
    '''
    try:
        if not isinstance(symptom, str) or not symptom.strip():
            raise ValueError(f"Invalid symptom input: {symptom}")
            
        logging.info(f"Encoding symptom: {symptom}")
        nlp = get_nlp()
        if nlp is None:
            raise ValueError("spaCy model not loaded")
            
        doc = nlp(symptom)
        if not hasattr(doc, 'vector'):
            raise ValueError("spaCy document has no vector attribute")
            
        vector = doc.vector.tolist()
        if not vector or not any(vector):
            raise ValueError("Empty vector generated for symptom")
            
        logging.info(f"Successfully encoded symptom: {symptom}")
        return vector
        
    except Exception as e:
        logging.error(f"Error in encode_symptom: {str(e)}")
        logging.error(traceback.format_exc())
        raise

def create_illness_vector(encoded_symptoms):
    '''
    Compares the list of encoded symptoms to a list of encoded symptoms. Any symptom above threshold (0.85) will be
    flagged.

    :param encoded_symptoms: A list of encoded symptoms
    :return: A single vector flagging each symptoms appearance in the user message (based on vector similarity)
    '''
    symptoms_df = get_symptoms_df()
    threshold = 0.85
    symptoms_df = symptoms_df.copy()  # Create a copy to avoid modifying the original
    symptoms_df['symptom_flagged'] = 0

    for encoded_symptom in encoded_symptoms:
        if not encoded_symptom:  # Skip empty symptom vectors
            continue
            
        symptoms_df['similarity'] = list(cosine_similarity(
            np.array(encoded_symptom).reshape(1, -1),
            np.array(list(symptoms_df['symptom_vector']))
        )[0])

        symptoms_df.loc[symptoms_df['similarity'] > threshold, 'symptom_flagged'] = 1
        number_of_symptoms_flagged = len(symptoms_df.loc[symptoms_df['similarity'] > threshold, 'symptom_flagged'])
        logging.info(f"Flagged {number_of_symptoms_flagged} potential symptom matches")
        
    return list(symptoms_df['symptom_flagged'])


def get_diagnosis(illness_vector):
    '''
    Compares the symptoms vector to our diagnosis df and generate the diagnosis (if one exists)

    :param illness_vector: Vector representing the illness symptoms
    :return: A string containing the diagnosis based on illness vector similarity
    '''
    diagnosis_df = get_diagnosis_df()
    threshold = 0.5
    
    if not illness_vector or not any(illness_vector):
        return "I couldn't identify any symptoms to make a diagnosis."
    
    # Create a copy to avoid modifying the original dataframe
    diagnosis_df = diagnosis_df.copy()
    
    try:
        diagnosis_df['similarity'] = list(cosine_similarity(
            np.array(illness_vector).reshape(1, -1),
            np.array(list(diagnosis_df['illness_vector']))
        )[0])

        # If there is an illness (or multiple illnesses)
        if len(diagnosis_df.loc[diagnosis_df['similarity'] > threshold]) > 0:
            illness = diagnosis_df.sort_values(by='similarity', ascending=False)['illness'].iloc[0]
            logging.info(f"Diagnosing user with {illness}")
            return f"Based on your symptoms it looks like you could have {illness}"
        else:
            closest_match = diagnosis_df.sort_values(by='similarity', ascending=False)[
                ['illness', 'similarity']
            ].iloc[0]
            logging.info(
                f"Unable to find a diagnosis, the closest match was {closest_match['illness']} "
                f"at {closest_match['similarity']}"
            )
            return "I'm not entirely sure, but I can suggest that you might have " \
                   f"{closest_match['illness']}. However, please consult a doctor for a proper diagnosis."
    except Exception as e:
        logging.error(f"Error in get_diagnosis: {str(e)}")
        return "I encountered an error while trying to process your symptoms. Please try again later."