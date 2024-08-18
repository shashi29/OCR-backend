invoice_data_prompt = """
Analyze the given business document and create a structured text output as follows:
Copy[DOCUMENT_TYPE]_SUMMARY

METADATA:
key1: value1
key2: value2

MAIN_CONTENT:
[Core information summary]

[Tables if applicable:]
| Column1 | Column2 | Column3 |
|---------|---------|---------|
| Data1   | Data2   | Data3   |

FINANCIAL_INFORMATION:
[Financial summary if present]

ADDITIONAL_INFORMATION:
[Other relevant details]

ADDITIONAL_NOTES:
[Information not fitting above structure]

COMMENTS:
[Explanations for ambiguities]
Use 'N/A' for missing fields. Present as a single text block with clear headers. Maintain consistent formatting for easy RAG system parsing.
Here is the data:
"""