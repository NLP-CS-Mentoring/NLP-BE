# Qwen Job Posting Cleaner

This folder documents the offline NLP preprocessing step used before building the
job posting vector database.

## Purpose

Raw job postings collected from web crawling and OCR often contain noisy text,
company introductions, benefits, broken OCR fragments, and unrelated content.
This step uses a Qwen 32B instruction model to normalize each posting into five
fields:

- 기술 스택
- 주요 업무
- 자격 요건
- 우대 사항
- 근무 조건

The cleaned output is then embedded and stored in ChromaDB for the career RAG API.

## Public Repo Notes

The full crawled dataset and cleaned output are not included in this repository
because they may contain third-party job posting content. Use the sample files in
`samples/` to inspect the expected input shape.

The original experiment was run in a Colab GPU environment. The reusable script
is provided as `qwen_job_cleaner.py`; the notebook is kept only as a lightweight
experiment record.

## Example

```bash
python NLP_Qwen2.5_32B/qwen_job_cleaner.py \
  --model-id Qwen/Qwen2.5-32B-Instruct \
  --input-file samples/sample_job_postings.json \
  --output-file outputs/job_postings_cleaned_qwen32b.json \
  --batch-size 4
```

