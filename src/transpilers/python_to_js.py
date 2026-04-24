"""Python to JavaScript transpiler implementation"""

import ast
from typing import Dict, Any, Tuple, List, Optional
from src.transpilers.base import BaseTranspiler


class PythonToJavaScriptTranspiler(BaseTranspiler):
    """Transpile Python code to JavaScript"""
    
    async def transpile(
        self, 
        source_code: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str], List[str]]:
        """Convert Python code to JavaScript"""
        options = options or {}
        self.clear_messages()
        
        try:
            # Parse Python AST
            tree = ast.parse(source_code)
            
            # Convert AST to JavaScript
            js_code = self._ast_to_js(tree, options)
            
            # Format code if requested
            if options.get("format_code", True):
                js_code = self.format_code(js_code, "javascript", options)
            
            # Check for unsupported features
            self._check_unsupported_features(tree)
            
            return js_code, self.warnings, self.errors
            
        except SyntaxError as e:
            self.add_error(f"Python syntax error: {str(e)}")
            return "", self.warnings, self.errors
        except Exception as e:
            self.add_error(f"Transpilation error: {str(e)}")
            return "", self.warnings, self.errors
    
    def _ast_to_js(self, tree: ast.AST, options: Dict[str, Any]) -> str:
        """Convert AST to JavaScript code"""
        js_lines = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Convert function
                js_func = self._convert_function(node, options)
                js_lines.append(js_func)
                
            elif isinstance(node, ast.ClassDef):
                # Convert class
                js_class = self._convert_class(node, options)
                js_lines.append(js_class)
                
            elif isinstance(node, ast.Assign):
                # Convert assignment
                js_assign = self._convert_assignment(node, options)
                js_lines.append(js_assign)
            elif isinstance(node, ast.Expr):
                js_expr = self._expr_to_js(node.value)
                js_lines.append(js_expr + ";")
        
        return "\n\n".join(js_lines) if js_lines else "// No valid code to transpile"
    
    def _convert_function(self, node: ast.FunctionDef, options: Dict[str, Any]) -> str:
        """Convert Python function to JavaScript function"""
        func_name = node.name
        
        # Get parameters
        params = [arg.arg for arg in node.args.args]
        params_str = ", ".join(params)
        
        # Build function
        js_func = f"function {func_name}({params_str}) {{\n"
        
        # Add function body (simplified)
        js_func += "    // TODO: Convert function body\n"
        js_func += "    console.log('Function implementation needed');\n"
        js_func += "}"
        
        return js_func
    
    def _convert_class(self, node: ast.ClassDef, options: Dict[str, Any]) -> str:
        """Convert Python class to JavaScript class"""
        class_name = node.name
        
        js_class = f"class {class_name} {{\n"
        js_class += "    constructor() {\n"
        js_class += "        // TODO: Implement constructor\n"
        js_class += "    }\n"
        js_class += "}"
        
        return js_class
    
    def _convert_assignment(self, node: ast.Assign, options: Dict[str, Any]) -> str:
        """Convert Python assignment to JavaScript assignment"""
        # Simplified conversion
        targets = [self._expr_to_js(t) for t in node.targets]
        value = self._expr_to_js(node.value)
        
        return f"let {targets[0]} = {value};"
    
    def _expr_to_js(self, expr: ast.AST) -> str:
        """Convert Python expression to JavaScript"""
        if isinstance(expr, ast.Constant):
            return repr(expr.value)
        elif isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.Call):
            func_name = self._expr_to_js(expr.func)
            args = ", ".join([self._expr_to_js(a) for a in expr.args])
            
            # Special handling for print → console.log
            if func_name == "print":
                return f"console.log({args})"
            
            return f"{func_name}({args})"
        else:
            return "undefined"
    
    def _check_unsupported_features(self, tree: ast.AST):
        """Check for Python features not supported in JavaScript"""
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                self.add_warning(
                    "Async functions are not fully supported and will be converted to regular functions"
                )
            elif isinstance(node, ast.AsyncFor):
                self.add_warning(
                    "Async for loops are not supported and will be converted to regular for loops"
                )
            elif isinstance(node, ast.AsyncWith):
                self.add_warning(
                    "Async context managers are not supported"
                )
            elif isinstance(node, ast.Yield):
                self.add_warning(
                    "Generators/yield are partially supported"
                )
            elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.decorator_list:
                    self.add_warning(
                        "Decorators are not fully supported"
                    )
                
    def supports(self, source: str, target: str) -> bool:
        """Check if language pair is supported"""
        return source == "python" and target == "javascript"
    
    def get_source_language(self) -> str:
        return "python"
    
    def get_target_language(self) -> str:
        return "javascript"