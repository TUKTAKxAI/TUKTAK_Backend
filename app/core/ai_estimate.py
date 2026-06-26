import os

MODEL_NAME = os.getenv(
    "AI_ESTIMATE_MODEL",
    "klue-roberta-base"
)

MAX_DESCRIPTION_LENGTH = 500

CONFIDENCE_THRESHOLD = 0.8