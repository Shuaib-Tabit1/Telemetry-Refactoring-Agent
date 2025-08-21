"""
Enhanced Pipeline Orchestrator with fault tolerance, caching, and parallel execution.
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
from enum import Enum

T = TypeVar('T')

class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class StageResult(Generic[T]):
    stage_name: str
    status: StageStatus
    result: Optional[T] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    cache_hit: bool = False
    
class PipelineCache:
    """Intelligent caching system for pipeline stages."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_key(self, stage_name: str, inputs: Any) -> str:
        """Generate cache key from stage name and inputs."""
        try:
            input_str = json.dumps(inputs, sort_keys=True, default=str)
        except (TypeError, ValueError):
            # If serialization fails, use a simple hash of the stage name and input type
            input_str = f"{stage_name}_{type(inputs).__name__}_{str(hash(str(inputs)))}"
        return hashlib.sha256(f"{stage_name}:{input_str}".encode()).hexdigest()
    
    def get(self, stage_name: str, inputs: Any) -> Optional[Any]:
        """Retrieve cached result."""
        cache_key = self._get_cache_key(stage_name, inputs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                cache_file.unlink(missing_ok=True)
        return None
    
    def set(self, stage_name: str, inputs: Any, result: Any) -> None:
        """Cache result."""
        cache_key = self._get_cache_key(stage_name, inputs)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, default=str, indent=2)
        except Exception as e:
            logging.warning(f"Failed to cache result for {stage_name}: {e}")

class EnhancedOrchestrator:
    """Enhanced pipeline orchestrator with fault tolerance and performance optimizations."""
    
    def __init__(self, 
                 output_dir: Path,
                 max_retries: int = 3,
                 enable_cache: bool = True,
                 parallel_workers: int = 4):
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.parallel_workers = parallel_workers
        self.cache = PipelineCache(output_dir / ".cache") if enable_cache else None
        self.stage_results: Dict[str, StageResult] = {}
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(output_dir / "pipeline.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def execute_stage(self, 
                           stage_name: str, 
                           stage_func: Callable,
                           inputs: Any,
                           dependencies: List[str] = None) -> StageResult:
        """Execute a pipeline stage with retry logic and caching."""
        
        # Check dependencies
        if dependencies:
            for dep in dependencies:
                if dep not in self.stage_results or self.stage_results[dep].status != StageStatus.COMPLETED:
                    return StageResult(stage_name, StageStatus.SKIPPED, error=f"Dependency {dep} not completed")
        
        # Check cache
        if self.cache:
            cached_result = self.cache.get(stage_name, inputs)
            if cached_result is not None:
                self.logger.info(f"Stage {stage_name}: Cache hit")
                return StageResult(stage_name, StageStatus.COMPLETED, cached_result, cache_hit=True)
        
        # Execute stage with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Stage {stage_name}: Starting (attempt {attempt + 1})")
                start_time = time.time()
                
                result = await asyncio.to_thread(stage_func, inputs)
                execution_time = time.time() - start_time
                
                # Cache successful result
                if self.cache and result is not None:
                    self.cache.set(stage_name, inputs, result)
                
                stage_result = StageResult(stage_name, StageStatus.COMPLETED, result, execution_time=execution_time)
                self.stage_results[stage_name] = stage_result
                self.logger.info(f"Stage {stage_name}: Completed in {execution_time:.2f}s")
                return stage_result
                
            except Exception as e:
                self.logger.warning(f"Stage {stage_name}: Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries:
                    stage_result = StageResult(stage_name, StageStatus.FAILED, error=str(e))
                    self.stage_results[stage_name] = stage_result
                    return stage_result
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def execute_parallel_batch(self, 
                              stage_name: str,
                              batch_func: Callable,
                              items: List[Any],
                              batch_size: int = 10) -> List[Any]:
        """Execute a batch of items in parallel."""
        
        results = []
        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            # Process in batches
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                # Submit batch to thread pool
                futures = [executor.submit(batch_func, item) for item in batch]
                
                # Collect results as they complete
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout
                        if result:
                            results.extend(result if isinstance(result, list) else [result])
                    except Exception as e:
                        self.logger.warning(f"Batch item failed: {e}")
        
        return results
    
    def save_stage_report(self) -> None:
        """Save detailed stage execution report."""
        report = {
            "execution_summary": {
                "total_stages": len(self.stage_results),
                "completed": sum(1 for r in self.stage_results.values() if r.status == StageStatus.COMPLETED),
                "failed": sum(1 for r in self.stage_results.values() if r.status == StageStatus.FAILED),
                "cache_hits": sum(1 for r in self.stage_results.values() if r.cache_hit),
                "total_execution_time": sum(r.execution_time for r in self.stage_results.values())
            },
            "stage_details": {name: asdict(result) for name, result in self.stage_results.items()}
        }
        
        with open(self.output_dir / "pipeline_report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
