from typing import Any, Text, Dict, List
import os
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from diaganose_functions.diagnose import encode_symptom, create_illness_vector, get_diagnosis

# Configure logging
log_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(log_dir, 'rasa_actions.log')

# Clear any existing handlers
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),  # 'w' to overwrite previous logs
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ActionDiagnoseSymptoms(Action):
    def name(self) -> Text:
        return "action_diagnose_symptoms"

    async def run(
        self, 
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        logger.info("\n" + "="*50)
        logger.info("ActionDiagnoseSymptoms started")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Input data directory exists: {os.path.exists('input_data')}")
        if os.path.exists('input_data'):
            logger.info(f"Input data directory contents: {os.listdir('input_data')}")
        try:
            logger.info("Action Diagnose Symptoms Triggered")
            logger.info(f"Latest Message: {tracker.latest_message}")
            
            # Get the symptom from the latest message
            symptom_entity = next(
                (e for e in tracker.latest_message.get("entities", []) 
                 if e["entity"] == "symptom"),
                None
            )
            
            if not symptom_entity:
                dispatcher.utter_message(text="I'm sorry, I didn't catch that. Could you describe your symptoms again?")
                return []
                
            symptom = symptom_entity.get("value")
            logger.info(f"Extracted symptom: {symptom}")
            
            # Encode the symptom
            encoded_symptom = encode_symptom(symptom)
            logger.info(f"Encoded symptom: {encoded_symptom}")
            
            # Create illness vector
            illness_vector = create_illness_vector([encoded_symptom])
            logger.info(f"Illness vector: {illness_vector}")
            
            # Get diagnosis
            diagnosis = get_diagnosis(illness_vector)
            logger.info(f"Diagnosis: {diagnosis}")
            
            dispatcher.utter_message(text=diagnosis)
            
        except Exception as e:
            error_msg = f"Error in diagnosis: {str(e)}"
            logger.error(error_msg, exc_info=True)
            dispatcher.utter_message(
                text=f"I'm sorry, I couldn't process your symptoms. "
                     f"The error was: {str(e)}. Please try again with different symptoms."
            )
            return []