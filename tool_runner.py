import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Set, Optional
import fcntl
from database_access import DatabaseAccess
import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

class ToolRunner:
    def __init__(
        self,
        json_path: str = "m_ids_lina_run.json",
        poll_interval: int = 3600,  # 1 hour in seconds
        max_retries: int = 3,
        retry_delay: int = 5,  # seconds between retries
        max_parallel_runs: int = 10,  # maximum parallel tool runs
        log_file: str = "tool_runner.log"
    ):
        self.json_path = Path(json_path)
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_parallel_runs = max_parallel_runs
        self.db = DatabaseAccess()
        self.active_runs = Queue()  # Track currently running MIDs
        
        # Setup logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def read_json_with_lock(self) -> Optional[dict]:
        """Try to read JSON file with a read lock."""
        try:
            if not self.json_path.exists():
                return {}
                
            with open(self.json_path, 'r') as file:
                # Acquire read lock
                fcntl.flock(file.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                try:
                    data = json.load(file)
                    return data
                finally:
                    # Release lock
                    fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        except BlockingIOError:
            self.logger.warning("File is locked for writing")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error reading JSON: {e}")
            return None

    def get_unique_mids(self) -> Set[str]:
        """Get set of MIDs that don't exist in the JSON file."""
        all_mids = set(self.db.get_all_mids())
        
        for attempt in range(self.max_retries):
            json_data = self.read_json_with_lock()
            if json_data is not None:
                # Find MIDs that don't exist in the JSON file
                existing_mids = set(json_data.keys())
                unique_mids = all_mids - existing_mids
                return unique_mids
            
            self.logger.warning(f"Retry attempt {attempt + 1} of {self.max_retries}")
            time.sleep(self.retry_delay)
        
        return set()  # Return empty set if all retries failed

    def run_tool(self, mid: str):
        """Execute the tool run command for a given MID."""
        try:
            self.active_runs.put(mid)
            self.logger.info(f"Starting tool run for MID: {mid}")
            
            # Replace this with your actual tool command
            command = f"your_tool_command --mid {mid}"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully ran tool for MID: {mid}")
            else:
                self.logger.error(f"Tool run failed for MID: {mid}. Error: {result.stderr}")
        
        except Exception as e:
            self.logger.error(f"Error running tool for MID {mid}: {e}")
        finally:
            self.active_runs.get()
            self.active_runs.task_done()

    def run_polling_loop(self):
        """Main polling loop with parallel execution."""
        self.logger.info("Starting polling loop")
        
        while True:
            try:
                unique_mids = self.get_unique_mids()
                
                if unique_mids:
                    self.logger.info(f"Found {len(unique_mids)} unique MIDs")
                    
                    # Create a thread pool for parallel execution
                    with ThreadPoolExecutor(max_workers=self.max_parallel_runs) as executor:
                        # Submit all MIDs to the thread pool
                        futures = [executor.submit(self.run_tool, mid) for mid in unique_mids]
                        
                        # Wait for all runs to complete
                        for future in futures:
                            future.result()
                else:
                    self.logger.info("No unique MIDs found or couldn't read status file")
                
                self.logger.info(f"Sleeping for {self.poll_interval} seconds")
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                self.logger.info("Received shutdown signal, stopping...")
                break
            except Exception as e:
                self.logger.error(f"Error in polling loop: {e}")
                time.sleep(self.poll_interval)

if __name__ == "__main__":
    # Create and run the tool runner
    runner = ToolRunner(
        json_path="m_ids_lina_run.json",
        poll_interval=3600,  # 1 hour
        max_retries=3,
        retry_delay=5,
        max_parallel_runs=10  # adjust based on your system's capabilities
    )
    runner.run_polling_loop() 