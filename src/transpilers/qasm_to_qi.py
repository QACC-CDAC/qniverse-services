"""QASM to QI transpiler"""

import subprocess
import json
from typing import Dict, Any, Tuple, List, Optional

from src.transpilers.base import BaseTranspiler


class QasmToQITranspiler(BaseTranspiler):
    """Transpile OpenQASM to QI Python code"""

    async def transpile(
        self,
        source_code: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str], List[str]]:
        
        options = options or {
                    "shots": "1024",
                    "backendName": "Tuna-5",
                    "decompose": True,
                    "processor":""
                }
        self.clear_messages()


        try:
            payload = {
                "qasm": source_code,
                "target": "qi",
                "options": options
            }

            result = subprocess.run(
                ["node", "lib/qniverse-quantum-transpiler/src/index.js"],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=10
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() or result.stdout.strip()
                self.add_error(error_msg)
                return "", self.warnings, self.errors

            return result.stdout.strip(), self.warnings, self.errors

        except Exception as e:
            self.add_error(f"QASM transpilation error: {str(e)}")
            return "", self.warnings, self.errors

    def supports(self, source: str, target: str) -> bool:
        return source == "qasm" and target == "qi"

    def get_source_language(self) -> str:
        return "qasm"

    def get_target_language(self) -> str:
        return "qi"
