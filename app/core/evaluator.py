import asyncio
import json
import re
import time
import aiohttp
from datetime import datetime
from sqlmodel import Session, select
from app.database import engine
from app.models import EvaluationLog, EvaluationResult, LLMModel, Dataset, TaskStatus

# Regex for extracting "answer: X" or "\boxed{X}"
# Priority: 1. "answer:\s*(.*)" 2. "\\boxed\{(.*?)\}"
ANSWER_PATTERNS = [
    re.compile(r"answer:\s*(.+?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"\\boxed\{(.+?)\}", re.IGNORECASE)
]

class AsyncEvaluator:
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.session_db = Session(engine)

    def _get_task_context(self):
        task = self.session_db.get(EvaluationLog, self.task_id)
        if not task:
            raise ValueError(f"Task {self.task_id} not found")
        model = self.session_db.get(LLMModel, task.model_id)
        dataset = self.session_db.get(Dataset, task.dataset_id)
        return task, model, dataset

    async def run(self):
        task, model, dataset = self._get_task_context()
        
        # Update status
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.utcnow()
        self.session_db.add(task)
        self.session_db.commit()

        try:
            # Read Dataset
            with open(dataset.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total = len(lines)
            task.total_samples = total
            self.session_db.add(task)
            self.session_db.commit()

            # Concurrency Control
            semaphore = asyncio.Semaphore(model.concurrency_limit)
            
            async with aiohttp.ClientSession() as http_session:
                tasks = []
                for line in lines:
                    data = json.loads(line)
                    tasks.append(
                        self.process_single_sample(
                            http_session, semaphore, model, data
                        )
                    )
                
                # Run all tasks
                results = await asyncio.gather(*tasks)

            # Aggregation
            correct_count = sum(1 for r in results if r['is_correct'])
            total_latency = sum(r['latency_ms'] for r in results)
            total_tokens = sum(r['tokens_used'] for r in results)
            
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            task.processed_samples = total
            task.accuracy = correct_count / total if total > 0 else 0
            task.avg_latency_ms = total_latency / total if total > 0 else 0
            task.avg_tokens = total_tokens / total if total > 0 else 0
            
            self.session_db.add(task)
            self.session_db.commit()

        except Exception as e:
            task.status = TaskStatus.FAILED
            # In production, log specific error
            print(f"Task Failed: {e}")
            self.session_db.add(task)
            self.session_db.commit()
        finally:
            self.session_db.close()

    async def process_single_sample(self, http_session, semaphore, model, data):
        async with semaphore:
            q = data.get("q", "")
            gt = data.get("a", "")
            
            start_ts = time.time()
            # Enforce "Answer: " format in system prompt
            system_prompt = "You are a helpful assistant. Please format your final answer starting with 'answer: '."
            
            payload = {
                "model": model.model_name_identifier,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": q}
                ],
                "temperature": 0.0,
                "max_tokens": 1024 
            }
            
            raw_output = ""
            tokens = 0
            
            try:
                headers = {"Authorization": f"Bearer {model.api_key}", "Content-Type": "application/json"}
                async with http_session.post(f"{model.api_base_url}/chat/completions", json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        resp_json = await resp.json()
                        raw_output = resp_json['choices'][0]['message']['content']
                        tokens = resp_json.get('usage', {}).get('total_tokens', 0)
                    else:
                        raw_output = f"Error: {resp.status} - {await resp.text()}"
            except Exception as e:
                raw_output = f"Exception: {str(e)}"
            
            latency = (time.time() - start_ts) * 1000
            
            # Extraction & Scoring
            extracted = self._extract_answer(raw_output)
            instruction_followed = bool(re.search(r"answer:", raw_output, re.IGNORECASE))
            is_correct = self._check_correctness(extracted, gt)
            
            # Save Result immediately (or batch if scaling higher)
            # Creating a new session for thread-safety in async context if needed, 
            # but here we use the shared one carefully or better, create one per db op.
            # Ideally, we should batch inserts, but for now we'll do row-by-row for simplicity.
            # NOTE: SQLModel Session is not thread-safe. We should create a new session here or pass a specific one.
            # However, since we are in an async function running in gather, we need to be careful with blocking DB calls.
            # Simplification: We return the dict and batch insert in the main thread/loop if possible, 
            # OR use a separate Sync DB session inside a `run_in_executor` block.
            # For this MVP, let's just return the data and let the main loop save it? 
            # No, 'gather' waits for all. We want real-time updates.
            # Solution: Use a local session for this insert.
            
            self._save_result(q, gt, raw_output, extracted, is_correct, instruction_followed, latency, tokens)
            
            return {
                "is_correct": is_correct,
                "latency_ms": latency,
                "tokens_used": tokens
            }

    def _save_result(self, q, gt, raw, extracted, is_correct, instruction_followed, latency, tokens):
        # Create a fresh session for this operation to avoid conflicts
        with Session(engine) as session:
            result = EvaluationResult(
                task_id=self.task_id,
                question=q,
                ground_truth=gt,
                raw_output=raw,
                extracted_answer=extracted,
                is_correct=is_correct,
                instruction_followed=instruction_followed,
                latency_ms=latency,
                tokens_used=tokens
            )
            session.add(result)
            session.commit()

    def _extract_answer(self, text):
        for pattern in ANSWER_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return text.strip() # Fallback to full text if no pattern found (or empty)

    def _check_correctness(self, extracted, ground_truth):
        if not extracted or not ground_truth:
            return False
        # Simple containment or exact match (normalized)
        return ground_truth.strip().lower() in extracted.lower()

