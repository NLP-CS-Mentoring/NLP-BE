import argparse
import json
import os
from pathlib import Path

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


DEFAULT_MODEL_ID = os.getenv("QWEN_MODEL_ID", "Qwen/Qwen2.5-32B-Instruct")
DEFAULT_INPUT_FILE = os.getenv(
    "JOB_POSTINGS_INPUT", "samples/sample_job_postings.json"
)
DEFAULT_OUTPUT_FILE = os.getenv(
    "JOB_POSTINGS_OUTPUT", "outputs/job_postings_cleaned_qwen32b.json"
)


SYSTEM_PROMPT = """당신은 유능한 '채용 정보 구조화 전문가'입니다.
입력된 텍스트는 OCR 노이즈와 채용과 무관한 잡담이 섞여 있습니다.

[임무]
1. 텍스트를 분석하여 핵심 채용 정보 5가지만 추출하십시오.
2. OCR 노이즈와 회사 홍보 멘트는 삭제하십시오.
3. 특정 항목에 대한 정보가 원본에 없다면 '내용 없음'이라고 적으십시오.

[출력 포맷]
- 기술 스택:
- 주요 업무:
- 자격 요건:
- 우대 사항:
- 근무 조건:
"""


def create_prompt(tokenizer, raw_text: str) -> str | None:
    if not raw_text or len(raw_text) < 50 or "실패" in raw_text:
        return None

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"[원본 텍스트]\n{raw_text[:10000]}"},
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def load_model(model_id: str):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        quantization_config=quantization_config,
        trust_remote_code=True,
    )
    return tokenizer, model


def clean_jobs(
    model_id: str,
    input_file: Path,
    output_file: Path,
    batch_size: int,
    checkpoint_interval: int,
) -> None:
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with input_file.open("r", encoding="utf-8") as f:
        jobs = json.load(f)

    tokenizer, model = load_model(model_id)
    cleaned_jobs = []
    output_file.parent.mkdir(parents=True, exist_ok=True)

    for batch_start in tqdm(range(0, len(jobs), batch_size)):
        batch_jobs = jobs[batch_start : batch_start + batch_size]
        batch_prompts = []
        valid_indices = []

        for idx, job in enumerate(batch_jobs):
            prompt = create_prompt(tokenizer, job.get("content", ""))
            if prompt:
                batch_prompts.append(prompt)
                valid_indices.append(idx)

        generated_responses = []
        if batch_prompts:
            inputs = tokenizer(
                batch_prompts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=12000,
            ).to(model.device)

            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=1024,
                    do_sample=False,
                    use_cache=True,
                )

            input_lengths = [len(x) for x in inputs.input_ids]
            for idx, output_ids in enumerate(generated_ids):
                new_tokens = output_ids[input_lengths[idx] :]
                generated_responses.append(
                    tokenizer.decode(new_tokens, skip_special_tokens=True)
                )

        for idx, job in enumerate(batch_jobs):
            if idx in valid_indices:
                response_idx = valid_indices.index(idx)
                job["content"] = generated_responses[response_idx]
            cleaned_jobs.append(job)

        finished = batch_start + len(batch_jobs)
        if checkpoint_interval and finished % checkpoint_interval == 0:
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(cleaned_jobs, f, ensure_ascii=False, indent=2)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(cleaned_jobs, f, ensure_ascii=False, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Clean OCR-heavy job postings with a Qwen 32B instruction model."
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--input-file", default=DEFAULT_INPUT_FILE)
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--checkpoint-interval", type=int, default=40)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    clean_jobs(
        model_id=args.model_id,
        input_file=Path(args.input_file),
        output_file=Path(args.output_file),
        batch_size=args.batch_size,
        checkpoint_interval=args.checkpoint_interval,
    )
