from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet


class ActionDiagnoseSymptoms(Action):
    def name(self) -> Text:
        return "action_diagnose_symptoms"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the last user message
        latest_message = tracker.latest_message
        
        # Extract symptoms from the message
        symptoms = []
        for entity in latest_message.get("entities", []):
            if entity["entity"] == "symptom":
                symptoms.append(entity["value"])
        
        # Simple symptom-based diagnosis
        if "upper abdominal pain" in symptoms:
            response = "I see you're experiencing upper abdominal pain. This could be related to several conditions such as gastritis, stomach ulcers, or gallbladder issues. It's important to consult a healthcare professional for proper diagnosis and treatment. Would you like me to provide more information about any of these conditions?"
        elif "fever" in symptoms:
            response = "I see you have a fever. This is often a sign of infection. Please monitor your temperature and consult a doctor if it persists or if you have other symptoms like cough or difficulty breathing."
        elif "cough" in symptoms:
            response = "I see you have a cough. This could be related to a respiratory infection or allergies. If it persists or is severe, please consult a healthcare professional."
        else:
            response = "I see you're experiencing symptoms. While I can provide general information, it's important to consult a healthcare professional for proper diagnosis and treatment. Would you like me to provide more information about any specific symptoms?"
        
        dispatcher.utter_message(text=response)
        
        return []
