from runners.detector import (
    Toolchain,
    detect_all,
    detect_cpp,
    detect_java,
    detect_javascript,
    detect_kotlin,
    detect_python,
    detect_rust,
)
from runners.python_runner import PythonRunner
from runners.rust_runner import RustRunner
from runners.java_runner import JavaRunner
from runners.cpp_runner import CppRunner
from runners.kotlin_runner import KotlinRunner
from runners.javascript_runner import JavaScriptRunner
from runners.gguf_runner import GGUFRunner

__all__ = [
    "Toolchain",
    "detect_all",
    "detect_cpp",
    "detect_java",
    "detect_javascript",
    "detect_kotlin",
    "detect_python",
    "detect_rust",
    "PythonRunner",
    "RustRunner",
    "JavaRunner",
    "CppRunner",
    "KotlinRunner",
    "JavaScriptRunner",
    "GGUFRunner",
]


class NoRunnerForLanguage(NotImplementedError):
    pass


def get_runner(language: str) -> object:
    if language == "python":
        return PythonRunner()
    if language == "rust":
        return RustRunner()
    if language == "java":
        return JavaRunner()
    if language == "cpp":
        return CppRunner()
    if language == "kotlin":
        return KotlinRunner()
    if language == "javascript":
        return JavaScriptRunner()
    raise NoRunnerForLanguage(
        f"Running {language} is not wired up yet. Check the runners/ folder."
    )
