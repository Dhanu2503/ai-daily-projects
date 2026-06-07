import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import openai
import os

class PersonaPostProApp:
    def __init__(self, master):
        self.master = master
        master.title("PersonaPost Pro: AI Content Stylist")
        master.geometry("1000x800") # Increased size for better usability
        master.resizable(True, True)

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            messagebox.showerror("API Key Missing", 
                                 "Please set the OPENAI_API_KEY environment variable. You can get one from platform.openai.com.")
            master.destroy()
            return

        self.client = openai.OpenAI(api_key=self.api_key)

        self.create_widgets()

    def create_widgets(self):
        # --- Main Frame --- Styles and Padding ---
        style = ttk.Style()
        style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Helvetica', 10))
        style.configure('TButton', font=('Helvetica', 10, 'bold'), padding=8)
        style.map('TButton', background=[('active', '#e0e0e0')])
        style.configure('TCombobox', font=('Helvetica', 10))

        main_frame = ttk.Frame(self.master, padding="15 15 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid for main_frame to allow resizing
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1) # Input area
        main_frame.grid_rowconfigure(6, weight=1) # Output area

        # --- Title ---
        title_label = ttk.Label(main_frame, text="PersonaPost Pro: AI Content Stylist", font=("Helvetica", 18, "bold"), foreground='#333')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)

        # --- Input Section ---
        ttk.Label(main_frame, text="Your Original Content:", font=("Helvetica", 12, "bold")).grid(row=1, column=0, sticky=tk.NW, pady=(5,0))
        self.input_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=15, font=("Helvetica", 10), bd=1, relief="solid")
        self.input_text.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 15))
        main_frame.grid_rowconfigure(2, weight=1)

        # --- Persona Selection ---
        persona_frame = ttk.Frame(main_frame)
        persona_frame.grid(row=3, column=0, columnspan=2, pady=(10, 15), sticky=tk.W + tk.E)
        persona_frame.grid_columnconfigure(2, weight=1)

        ttk.Label(persona_frame, text="Select Persona Style:", font=("Helvetica", 12, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.personas = {
            "Professional": "Rewrite the content in a highly professional, formal, and corporate tone. Ensure clarity, conciseness, and appropriate business language. Aim for a polished, authoritative style suitable for official communications or reports.",
            "Casual & Friendly": "Rewrite the content in a casual, friendly, and approachable tone. Use simpler language, contractions, and a conversational style. Make it relatable and easy to read, like a chat with a friend.",
            "Humorous": "Rewrite the content with a humorous and lighthearted tone. Incorporate wit, gentle sarcasm (if appropriate), and engaging anecdotes. The goal is to entertain and make the reader smile, while still conveying the core message.",
            "Academic": "Rewrite the content in an academic and scholarly tone. Use precise terminology, avoid colloquialisms, and structure arguments logically with clear thesis statements and supporting evidence. Suitable for research papers or formal essays.",
            "Concise & Direct": "Rewrite the content to be extremely concise and direct. Remove any unnecessary words or phrases while retaining the core message. Get straight to the point without fluff, ideal for summaries or quick updates.",
            "Empathetic & Supportive": "Rewrite the content with an empathetic and supportive tone. Focus on understanding the reader's perspective, validating their feelings, and offering encouragement or constructive help. Use gentle and understanding language.",
            "Marketing & Persuasive": "Rewrite the content with a strong marketing and persuasive tone. Highlight benefits, create urgency, and encourage action. Use compelling language, rhetorical questions, and calls-to-action to motivate the reader.",
            "Storyteller": "Rewrite the content by framing it as a compelling story. Use vivid descriptions, build narrative tension, and engage the reader through character or event development. Transform information into an immersive experience."
        }
        self.persona_var = tk.StringVar(self.master)
        self.persona_var.set("Professional") # default value
        self.persona_dropdown = ttk.Combobox(persona_frame, textvariable=self.persona_var, values=list(self.personas.keys()), state="readonly", width=30, font=("Helvetica", 10))
        self.persona_dropdown.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self.persona_dropdown.bind("<<ComboboxSelected>>", self.update_persona_description)

        self.persona_description_label = ttk.Label(persona_frame, text=self.personas["Professional"], wraplength=450, font=("Helvetica", 9, "italic"), foreground='#555')
        self.persona_description_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))

        # --- Action Button ---
        self.restyle_button = ttk.Button(main_frame, text="Restyle Content", command=self.restyle_content)
        self.restyle_button.grid(row=4, column=0, columnspan=2, pady=(20, 20))

        # --- Output Section ---
        ttk.Label(main_frame, text="Restyled Content:", font=("Helvetica", 12, "bold")).grid(row=5, column=0, sticky=tk.NW, pady=(5,0))
        self.output_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=80, height=15, font=("Helvetica", 10), state=tk.DISABLED, bd=1, relief="solid", background='#e9e9e9')
        self.output_text.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=(0, 15))
        main_frame.grid_rowconfigure(6, weight=1)

        # --- Status Bar ---
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W, font=("Helvetica", 9, "italic"), foreground='#666')
        self.status_bar.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10,0))

    def update_persona_description(self, event=None):
        selected_persona = self.persona_var.get()
        self.persona_description_label.config(text=self.personas.get(selected_persona, "No description available."))

    def restyle_content(self):
        input_content = self.input_text.get("1.0", tk.END).strip()
        selected_persona = self.persona_var.get()

        if not input_content:
            messagebox.showwarning("Input Missing", "Please enter some content to restyle.")
            return
        
        if not selected_persona:
            messagebox.showwarning("Persona Missing", "Please select a persona style.")
            return

        self.status_bar.config(text=f"Processing content with '{selected_persona}' persona...")
        self.restyle_button.config(state=tk.DISABLED) # Disable button during processing
        self.master.update_idletasks() # Update GUI immediately

        # Define the system prompt based on selected persona
        system_prompt = self.personas.get(selected_persona, self.personas["Professional"]) # Fallback to Professional

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", # Can be changed to "gpt-4" or "gpt-4o" if user has access
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": input_content}
                ],
                temperature=0.7, # Adjust creativity: 0.0 for deterministic, 1.0 for very creative
                max_tokens=2000 # Limit output length
            )
            
            restyled_text = response.choices[0].message.content.strip()
            
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", restyled_text)
            self.output_text.config(state=tk.DISABLED)
            
            self.status_bar.config(text="Ready")

        except openai.APIConnectionError as e:
            messagebox.showerror("Connection Error", f"Could not connect to OpenAI API: {e}")
            self.status_bar.config(text="Error: Connection failed")
        except openai.RateLimitError as e:
            messagebox.showerror("Rate Limit Exceeded", f"You've sent too many requests too quickly. Please wait and try again: {e}")
            self.status_bar.config(text="Error: Rate limit exceeded")
        except openai.APIStatusError as e:
            messagebox.showerror("API Error", f"OpenAI API returned an error: {e.status_code} - {e.response}")
            self.status_bar.config(text="Error: API call failed")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.status_bar.config(text="Error: Unexpected issue")
        finally:
            self.restyle_button.config(state=tk.NORMAL) # Re-enable button

def main():
    root = tk.Tk()
    app = PersonaPostProApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
