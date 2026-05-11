# Apêndice B: Templates de Prompts Utilizados

## Template da Trilha A
```text
You are an expert SQL assistant.
Given the following question, write a valid SQL SELECT query that answers it.
Return only the SQL query, with no explanation or markdown formatting.

Question: {question}

SQL:
```

## Template da Trilha B
```text
You are an expert SQL assistant.
Given the following schema and question, write a valid SQL SELECT query that answers it.
Use only tables and columns present in the schema.
Return only the SQL query, with no explanation or markdown formatting.

Schema:
{schema}

Question: {question}

SQL:
```

## Template da Trilha C
```text
You are an expert SQL assistant.
Given the following schema, retrieved context, and question, write a valid SQL SELECT query that answers it.
Use only tables and columns present in the schema.
Return only the SQL query, with no explanation or markdown formatting.

Schema:
{schema}

Retrieved Context:
{retrieved_context}

Question: {question}

SQL:
```
