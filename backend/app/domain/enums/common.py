from enum import Enum


class SurveyMode(str, Enum):
    TEXT = "text"
    QUESTIONNAIRE = "questionnaire"


class SurveyStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Stance(str, Enum):
    AGREE = "agree"
    DISAGREE = "disagree"
    MIXED = "mixed"


class QuestionType(str, Enum):
    STANCE = "stance"
    LIKERT = "likert"
    MCQ = "mcq"
