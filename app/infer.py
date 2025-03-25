import os

from openai import OpenAI
from textwrap import dedent

from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).parent.parent

load_dotenv(override=True)

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that can answer questions and help with tasks.
"""


class InferenceManager:
    def __init__(
        self,
        base_url="http://localhost:2300/v1/",
        api_key="-",
        model: str | None = None,
        stream: bool = False,
        max_tokens: int = 2048,
        temperature: float = 0.5,
        top_p: float = 0.90,
        frequency_penalty: float = 1.03,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT
    ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model
        self.stream = stream
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.system_prompt = system_prompt
        self.conversation_history = [
            {"role": "system", "content": dedent(self.system_prompt)}
        ]
        
    def get_default_sys_prompt(self) -> str:
        """Return the current system prompt."""
        return self.system_prompt
        
    def infer(self, qr: str, prompt: str = None, chat_history: list = None) -> str:
        """
        Generate a response based on user query and optional chat history.
        This method is designed to be compatible with reply_and_remember in main.py.
        
        Args:
            qr: The user query/input
            prompt: Optional custom system prompt
            chat_history: Optional list of (query, response) tuples from previous conversation
            
        Returns:
            The model's response as a string
        """
        # Reset conversation with custom prompt if provided
        if prompt:
            self.reset_conversation(prompt)
        elif chat_history and not self.conversation_history[1:]:
            # Only reset if we haven't already built up history in this session
            self.reset_conversation()
            
        # Ensure system prompt is in conversation history
        if not self.conversation_history or self.conversation_history[0]["role"] != "system":
            system_content = prompt if prompt else self.system_prompt
            self.conversation_history.insert(0, {"role": "system", "content": dedent(system_content)})
            
        # Add chat history if provided and not already in conversation
        if chat_history and len(self.conversation_history) <= 1:
            for query, response in chat_history:
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": response})
                
        # Get response to the current query
        return self.get_non_streaming_response(qr)

    def get_response(self, user_input: str):
        """
        Get response from the model based on user input.
        Calls the appropriate method based on streaming setting.
        """
        if self.stream:
            return self.get_streaming_response(user_input)
        else:
            return self.get_non_streaming_response(user_input)

    def get_non_streaming_response(self, user_input: str):
        """
        Get a complete response from the model based on user input.
        Returns the complete response as a string.
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            # Get completion from API
            chat_completion = self.client.chat.completions.create(
                model=self.model if self.model else self.client.models.list().data[0].id,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                stream=False
            )
            
            # Handle non-streaming response
            full_response = chat_completion.choices[0].message.content
            
            # Add assistant's message to history
            self.conversation_history.append({"role": "assistant", "content": full_response})
            
            return full_response
                
        except Exception as e:
            error_msg = f"Error during API call: {str(e)}"
            return error_msg

    def get_streaming_response(self, user_input: str):
        """
        Get streaming response from the model based on user input.
        Returns a generator that yields response chunks.
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_input})

        try:
            # Get streaming completion from API
            chat_completion = self.client.chat.completions.create(
                model=self.model if self.model else self.client.models.list().data[0].id,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                stream=True
            )
            
            # Handle streaming response
            full_response = ""
            for chunk in chat_completion:
                if hasattr(chunk.choices[0].delta, 'content'):
                    content = chunk.choices[0].delta.content
                    if content:
                        full_response += content
                        yield content
            
            # Add assistant's message to history after collecting the full response
            self.conversation_history.append({"role": "assistant", "content": full_response})
                
        except Exception as e:
            error_msg = f"Error during API call: {str(e)}"
            yield error_msg

    def reset_conversation(self, custom_prompt: str = None):
        """
        Reset the conversation history to initial state with system prompt.
        
        Args:
            custom_prompt: Optional custom system prompt to use
        """
        if custom_prompt:
            self.conversation_history = [
                {"role": "system", "content": dedent(custom_prompt)}
            ]
        else:
            self.conversation_history = [
                {"role": "system", "content": dedent(self.system_prompt)}
            ]

    def start_chat(self):
        """Start an interactive chat session in the console."""
        print("Chat started. Type 'quit' to exit.")
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit', 'bye']:
                break
            
            if self.stream:
                print("Assistant: ", end='', flush=True)
                for chunk in self.get_streaming_response(user_input):
                    print(chunk, end='', flush=True)
                print()  # Add a newline after streaming response
            else:
                response = self.get_non_streaming_response(user_input)
                print(f"\nAssistant: {response}")