import os
import instructor
from openai import OpenAI
import weave
import wandb  # Add this import
from instructor import Mode

weave.init('openrouter-chat')

# Add wandb initialization
wandb_key = os.environ.get("WANDB_API_KEY")
if wandb_key:
    wandb.login(key=wandb_key)
    wandb.init(project="openrouter-chat")
else:
    print("WANDB_API_KEY not found. Skipping wandb initialization.")

# Initialize OpenAI client with Instructor
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
openrouter_base_url = "https://openrouter.ai/api/v1"
client = instructor.from_openai(OpenAI(
    api_key=openrouter_api_key,
    base_url=openrouter_base_url),
    mode=Mode.JSON
)

from pydantic import BaseModel, Field

class Score(BaseModel):
    """A score includes the value and description used to determine the metric being evaluated."""
    score: int = Field(..., description="The score of the user")
    determination: str = Field(..., description="The description that determines the score.",
                               examples=["Score 0 - There is no factual evidence to support the claim",
                                         "Score 1 - There is factual evidence to support the claim"])

class Metric(BaseModel):
    """A metric is a set of criteria with numerical scores and descriptions used to evaluate the output of a language model. It is based on the prompt input."""
    metric: str = Field(..., description="The description of the metric being described.")
    metric_type: str = Field(..., description="The type of metric being described as either a binary or graded metric.",
                      examples=["Graded (0-5)", "Binary (Pass/Fail)"])
    criteria: list[Score] = Field(..., description="Based on the metric, returns the set of scores that will be used to evaluate the metric.")


class FullMetric(BaseModel):
    """A list of components to evaluate an Language Model Response, which includes the description of the individual metrics, the set of criteria and scores per metric."""
    description: str = Field(..., description="The description of the metric")
    metric: list[Metric] = Field(..., min_length=3, max_length=10, description="The metric being described",
                                 examples=[
                                     "Metric 1: The response includes a factual error and scores using a Binary Criteria. Criteria: The response includes a factual error. Score: 0",
                                     "Metric 2: The response is not descriptive and scores using a 5 point Likert Scale Criteria. Criteria: The response is not descriptive. Score: 1"
                                 ]  )


# Define a function for the travel agent to use
from pydantic import BaseModel, Field
from textwrap import dedent

def generate_metric(user_prompt, llm_response):
    system_content = dedent("""
    Instructions:
    You are an AI assistant tasked with evaluating a response generated by an LLM (Large Language Model). 
    Your evaluation must be tailored to the specific NLP task and domain expertise required by the user's prompt. 
    Follow the steps below to produce a comprehensive, expert-level assessment using dynamically generated metrics that are highly relevant to the task and domain at hand.

    Step 1: Analyze the Task and Domain
    1. Identify the NLP Task Type:
    Examine the user prompt and the LLM's response to determine the specific NLP task involved. Possible tasks include:
    Question Answering (QA)
    Named Entity Recognition (NER)
    Creative Generation (e.g., storytelling, poem writing)
    Summarization
    Translation
    Dialogue Generation
    Information Extraction
    Classification
    2. Determine the Required Domain Expertise:
    Identify the subject matter and domain-specific knowledge needed to address the prompt effectively. Possible domains include:
    Medicine
    Law
    Literature
    Computer Science
    Finance
    Psychology
    Education
    ---
    Step 2: Generate Customized Evaluation Metrics
    Based on the identified NLP task and domain expertise, generate a set of evaluation metrics that are both task-specific and domain-specific. Ensure that these metrics are defined clearly and are appropriate for an expert in the field to use as a standard.
    A. Task-Specific Metrics
    Define metrics that are standard for evaluating the identified NLP task.
    Examples:
    For Question Answering:
    Accuracy of Answer
    Completeness
    Relevance
    For NER:
    Precision
    Recall
    F1 Score
    For Creative Generation:
    Originality
    Creativity
    Emotional Impact
    B. Domain-Specific Metrics
    Define metrics that reflect the standards and expectations of the identified domain.
    Examples:
    For Medicine:
    Clinical Accuracy
    Use of Medical Terminology
    Adherence to Ethical Guidelines
    For Law:
    Legal Accuracy
    Citation of Relevant Laws
    Logical Consistency in Arguments
    ---
    Step 3: Evaluate the LLM's Response Using the Generated Metrics
    For each metric:
    1. Define the Metric:
    Provide a clear and concise definition so that it is understood how the evaluation will be conducted.
    2. Evaluation Method:
    Graded Metrics: Use a numerical scale (e.g., 0-5) where appropriate.
    Binary Metrics: Use Pass/Fail, Yes/No, or Compliant/Non-Compliant where a binary assessment is more suitable.
    3. Assess the Response:
    Apply the metric to the LLM's response.
    Provide specific examples or evidence from the response to support your assessment.
    4. Provide a Score or Judgment:
    Assign a score or make a binary judgment as defined.
    ---
    Step 4: Provide an Overall Assessment and Recommendations
    Summarize the Overall Quality:
    Highlight the main strengths and weaknesses observed in the response.
    Final Recommendations:
    Offer actionable suggestions for improvement.
    Suggest any additional resources or corrections needed.
    ---
    Template for the Evaluation Report:
    ---
    User Prompt:
    [Insert User Prompt Here]
    LLM's Response:
    [Insert LLM's Response Here]
    ---
    Analysis:
    1. Identified NLP Task Type: [Specify the task]
    2. Identified Domain Expertise Required: [Specify the domain]
    ---
    Customized Evaluation Metrics:
    Metric 1: [Name of Metric]
    Type: [Graded (0-5) or Binary (Pass/Fail)]
    Definition: [Provide a clear definition]
    Assessment:
    [Apply the metric to the response, citing specific examples]
    Score/Judgment: [Provide the score or Pass/Fail]
    (Repeat for each metric)
    ---
    Overall Assessment:
    Summary of Findings:
    [Summarize the key points from the evaluation]
    Strengths:
    [List what the response did well]
    Areas for Improvement:
    [List what can be improved, with suggestions]
    Final Recommendations:
    [Provide actionable advice]
    ---
    Example Evaluation Report:
    (Below is an illustrative example using placeholders. Replace with actual content.)
    ---
    User Prompt:
    "Explain the process of mitosis in human cells."
    LLM's Response:
    "Mitosis is the process by which a cell divides into two new cells. It consists of phases called prophase, metaphase, anaphase, and telophase. During mitosis, DNA replicates, and the cell splits equally."
    ---
    Analysis:
    1. Identified NLP Task Type: Expository Answering
    2. Identified Domain Expertise Required: Cell Biology
    ---
    Customized Evaluation Metrics:
    Metric 1: Scientific Accuracy
    Type: Graded (0-5)
    Definition: Evaluates the correctness of biological facts presented.
    Assessment:
    The response correctly identifies mitosis as a cell division process.
    It mentions the phases but omits cytokinesis.
    It incorrectly states that DNA replicates during mitosis (DNA replication occurs during interphase).
    Score: 3/5
    Metric 2: Use of Terminology
    Type: Binary (Pass/Fail)
    Definition: Assesses correct use of biological terms.
    Assessment:
    Terms like "prophase," "metaphase," "anaphase," and "telophase" are used correctly.
    Misuse of "DNA replicates during mitosis."
    Judgment: Fail
    Metric 3: Completeness
    Type: Graded (0-5)
    Definition: Measures how thoroughly the response covers the process.
    Assessment:
    Lacks mention of interphase and cytokinesis.
    Does not describe what happens in each phase.
    Score: 2/5
    ---
    Overall Assessment:
    Summary of Findings:
    The response demonstrates a basic understanding of mitosis but contains factual inaccuracies and omissions.
    Strengths:
    Correctly lists the main phases of mitosis.
    Areas for Improvement:
    Correct the misconception about DNA replication timing.
    Include details about each phase.
    Mention cytokinesis and its role.
    Final Recommendations:
    Revise the response to correct factual errors.
    Expand on each phase to enhance completeness.
    Ensure all biological terms are used accurately.
    ---
    Note: This evaluation is tailored to the specific task (explaining a biological process) and domain (cell biology), using metrics that are relevant and meaningful to experts in the field.
    ---
    Guidelines for Using This Prompt:
    Adaptability: The prompt is designed to be flexible. The evaluator dynamically generates metrics based on the task and domain identified.
    Specificity: By focusing on task-specific and domain-specific metrics, the evaluation becomes more precise and valuable.
    Expert-Level Assessment: The metrics and evaluation criteria aim to reflect the standards expected by professionals in the relevant field.
    Actionable Feedback: Providing detailed assessments and recommendations helps improve future LLM responses.                        
    """)

    # Use the Instructor framework for function calling
    evaluation = client.chat.completions.create(
        # model="microsoft/phi-3-mini-128k-instruct:free",
        model="openai/gpt-4o",
        response_model=FullMetric,
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"User Prompt: {user_prompt}"},
            {"role": "user", "content": f"LLM's Response: {llm_response}"},
        ],
        temperature=0.7,
    )
    return evaluation

sample_prompt = "Given a Hypertensive CKD patient with Heart Failure and declining kidney function and hypokalemia, provide a care plan to improve their health."
sample_response = "The patient should receive a beta blockers, low-salt diet, diuretics, and potassium supplements. No further action is needed because this already addresses all their needs."

generated_metric = generate_metric(sample_prompt, sample_response)

from rich import print as rprint

# rprint(generated_metric)
for m in generated_metric.metric:
    print("Metric: ", m.metric)
    print("Metric Type: ", m.metric_type)
    for c in m.criteria:
        print("Score: ", c.score)
        print("Determination: ", c.determination)

# Log the response to wandb
if wandb.run is not None:
    wandb.log({
        # "city": travel_info.city,
        # "description": travel_info.description,
        # "top_attractions": travel_info.top_attractions,
        # "best_time_to_visit": travel_info.best_time_to_visit
    })

# Finish the wandb run
if wandb.run is not None:
    wandb.finish()