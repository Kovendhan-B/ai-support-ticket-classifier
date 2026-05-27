from pathlib import Path
from string import Template

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR.parent / "prompts"

def load_prompt(version: str) -> Template:
    file_path = PROMPT_DIR / f"classify_{version}.txt"
    try:
        with open(file_path,"r",encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Prompt template not found: {file_path}"
        )
    except Exception as e:
        raise Exception(f"Error loading prompt template: {e}")
    
def build_prompt(version: str, ticket_text: str) -> str:
    template_str = load_prompt(version)
    template = Template(template_str)
    return template.safe_substitute(ticket_text=ticket_text)

if __name__ == "__main__":
    version = "v1"
    ticket_text = "I was charged twice for my last order. Please help!"
    try:
        prompt = build_prompt(version, ticket_text)
        print(prompt)
    except Exception as e:
        print(f"Error: {e}")