from app.formatter.base import SemanticFormatter
from app.models.semantic import SemanticConcept

class IEC61360Formatter:

    def format(self, semantic_data):
        raise NotImplementedError