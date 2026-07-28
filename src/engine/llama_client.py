import sys
from llama_cpp import Llama, LlamaGrammar
from model import error
import os 
import json
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GRAMMAR_PATH = os.path.join(CURRENT_DIR, "grammar.gbnf")
class LlamaClient:
    def __init__(self, model_path: str="/Users/jatin/Models/Qwen3-4B-Q4_K_M.gguf",n_ctx: int=4096, n_gpu_layers: int=-1, grammer_path: str=DEFAULT_GRAMMAR_PATH):
        """
        Initialize the LlamaClient.

        Args:
            model_path (str): The path to the Llama model file.
            n_ctx (int): The context size.
            n_gpu_layers (int): The number of GPU layers to use.
            grammer_path (str): The path to the Llama grammar file.
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.grammar = LlamaGrammar.from_file(grammer_path)
        self.model = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers)

    def explain_error(self, error: error.ErrorModel) -> str:
        """
        Use the Llama model to explain an error message.

        Args:
            error (error.ErrorModel): The error to explain.

        Returns:
            str: The explanation of the error message.
        """
        system_prompt = (
            "You are a low-level CLI diagnostic tool. "
            "Analyze the terminal output and exit code. "
            "Explain the root cause of the error concisely in 2-3 sentences. "
            "Do not output markdown code blocks unless providing a command."
        )
        
        user_prompt = (
            f"Command: {error.message}\n"
            f"Exit Code: {error.code}\n"
            f"Terminal Output:\n{error.output_buffer[-3000:]}"
        )

        response = self.model.create_chat_completion(
          messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}    
          ],
          stream=True,
          temperature=0.1,
        )
        sys.stdout.write("\n\033[1;31m[SIGKILL DIAGNOSTIC]\033[0m\n")
        for chunk in response:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta:
                sys.stdout.write(delta['content'])
                sys.stdout.flush()
        sys.stdout.write("\n\033[1;31m[END OF DIAGNOSTIC]\033[0m\n")

    def step(self, messages: list[dict]) -> dict:
        """
        Perform a single step of interaction with the Llama model.

        Args:
            messages (list[dict]): A list of messages to send to the model.

        Returns:
            dict: The model's response.
        """
        response = self.model.create_chat_completion(
            messages=messages,
            stream=True,
            temperature=0.1,
            grammar=self.grammar
        )
        output = ""
        for chunk in response:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta:
                output += delta['content']
                sys.stdout.write(delta['content'])
                sys.stdout.flush()
        return json.loads(output)