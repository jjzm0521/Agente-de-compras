import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Callable, Dict, Any

class ChatApplication:
    def __init__(self, root: tk.Tk, agent_app: Callable, initial_agent_state: Dict[str, Any]):
        self.root = root
        self.agent_app = agent_app
        self.current_agent_state = initial_agent_state

        self.root.title("Agente de Compras Conversacional")
        self.root.geometry("600x700") # Aumentado tamaño para mejor visualización

        # Área de Chat
        self.chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 10))
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Frame para entrada y botón
        input_frame = tk.Frame(root)
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        # Campo de Entrada de Usuario
        self.user_input_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.user_input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,5)) # Aumentado padding vertical
        self.user_input_entry.bind("<Return>", self.send_message_event)

        # Botón de Envío
        self.send_button = tk.Button(input_frame, text="Enviar", command=self.send_message, padx=10, pady=8, font=("Arial", 10))
        self.send_button.pack(side=tk.RIGHT)

        # Configurar cierre de ventana
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Mensaje inicial del agente (si existe en el estado inicial o una bienvenida genérica)
        # Esto podría venir del primer `invoke` si el agente está diseñado para saludar al inicio.
        # Por ahora, un mensaje fijo y luego veremos si el agente puede dar el primer saludo.
        self.add_message_to_chat("🤖 Agente:", "¡Hola! Soy tu asistente de compras personal. ¿Cómo puedo ayudarte hoy?")
        # Opcionalmente, podríamos hacer una invocación inicial al agente sin input para obtener saludo.
        # self.process_agent_turn(initial=True)


    def add_message_to_chat(self, sender: str, message: str, is_error: bool = False):
        self.chat_area.config(state=tk.NORMAL)
        tag = "error" if is_error else sender # Para aplicar color si es error

        if is_error:
             self.chat_area.tag_configure("error_sender", foreground="red", font=("Arial", 10, "bold"))
             self.chat_area.tag_configure("error_message", foreground="red")
             self.chat_area.insert(tk.END, f"{sender} ", "error_sender")
             self.chat_area.insert(tk.END, f"{message}\n\n", "error_message")
        elif sender == "👤 Tú:":
            self.chat_area.tag_configure("user_sender", foreground="blue", font=("Arial", 10, "bold"))
            self.chat_area.tag_configure("user_message", foreground="black")
            self.chat_area.insert(tk.END, f"{sender} ", "user_sender")
            self.chat_area.insert(tk.END, f"{message}\n\n", "user_message")
        else: # Agente
            self.chat_area.tag_configure("agent_sender", foreground="green", font=("Arial", 10, "bold"))
            self.chat_area.tag_configure("agent_message", foreground="black")
            self.chat_area.insert(tk.END, f"{sender} ", "agent_sender")
            self.chat_area.insert(tk.END, f"{message}\n\n", "agent_message")

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END) # Auto-scroll

    def send_message_event(self, event=None):
        self.send_message()

    def send_message(self):
        user_text = self.user_input_entry.get().strip()
        if not user_text:
            return

        self.add_message_to_chat("👤 Tú:", user_text)
        self.user_input_entry.delete(0, tk.END)

        # Deshabilitar entrada mientras el agente procesa
        self.user_input_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)

        self.process_agent_turn(user_input=user_text)

    def process_agent_turn(self, user_input: str = None, initial: bool = False):
        try:
            if initial: # Para una posible primera interacción del agente (saludo)
                 self.current_agent_state["current_user_input"] = None # O un input especial de inicio
            else:
                self.current_agent_state["current_user_input"] = user_input

            # Invocar el grafo del agente
            # El recursion_limit puede necesitar ajuste.
            print(f"DEBUG: GUI enviando al agente: {self.current_agent_state['current_user_input']}")
            updated_state = self.agent_app.invoke(self.current_agent_state, config={"recursion_limit": 25}) #Aumentado límite
            self.current_agent_state = updated_state

            master_decision = self.current_agent_state.get("master_agent_decision", {})
            agent_response = master_decision.get("response_text", "No he podido procesar tu solicitud.")

            # El nodo respond_to_user_node en el grafo ya podría estar imprimiendo a consola.
            # Aquí nos aseguramos que se muestre en la GUI.
            # Si el response_text ya está siendo impreso por el agente, podríamos tener duplicados en consola
            # pero es importante para la GUI.
            print(f"DEBUG: GUI recibió del agente: {agent_response}")

            self.add_message_to_chat("🤖 Agente:", agent_response)

            if master_decision.get("next_action") == "end_conversation":
                self.add_message_to_chat("🤖 Agente:", "Sesión finalizada.")
                self.user_input_entry.config(state=tk.DISABLED)
                self.send_button.config(state=tk.DISABLED)
            else:
                # Rehabilitar entrada para el siguiente turno del usuario
                self.user_input_entry.config(state=tk.NORMAL)
                self.send_button.config(state=tk.NORMAL)
                self.user_input_entry.focus()


        except Exception as e:
            error_msg = f"Ocurrió un error al procesar con el agente: {e}"
            print(f"ERROR en GUI: {error_msg}") # Loguear el error completo
            self.add_message_to_chat("🤖 Agente (Error):", "Lo siento, he encontrado un problema técnico. Intenta de nuevo.", is_error=True)
            # Rehabilitar entrada para que el usuario pueda intentar de nuevo
            self.user_input_entry.config(state=tk.NORMAL)
            self.send_button.config(state=tk.NORMAL)
            self.user_input_entry.focus()


    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Seguro que quieres salir?"):
            # Aquí podríamos añadir lógica de limpieza del agente si fuera necesario
            self.root.destroy()

# Esto es solo para pruebas directas del GUI, main.py será el punto de entrada final
# def main_gui_test():
#     root = tk.Tk()

#     # --- Inicio de Simulación de Agente ---
#     # Esto simula lo que main.py haría: crear el agente y el estado inicial
#     def mock_agent_app(state, config=None):
#         print(f"Mock Agent App Invocado con input: {state.get('current_user_input')}")
#         user_input = state.get("current_user_input", "").lower()
#         response = "Respuesta simulada del agente."
#         next_action = "respond_to_user"
#         if not user_input: # Saludo inicial
#             response = "¡Hola desde el agente simulado!"
#         elif "hola" in user_input:
#             response = "¡Hola! ¿Cómo te puedo ayudar?"
#         elif "adiós" in user_input or "salir" in user_input:
#             response = "Vale, ¡hasta luego!"
#             next_action = "end_conversation"
#         elif "error" in user_input:
#             raise Exception("Esto es un error simulado del agente.")
#         elif "busca " in user_input:
#             query = user_input.split("busca ", 1)[1]
#             response = f"Buscando '{query}'... (simulado)"
#             # Simular que se llamó a una herramienta y ahora el master agent debe procesar el resultado
#             # En un caso real, esto sería manejado por el flujo del grafo.
#             # Para simplificar la simulación, el master_agent_decision ya tendría la respuesta.

#         state["master_agent_decision"] = {
#             "response_text": response,
#             "next_action": next_action
#         }
#         state["conversation_history"] = state.get("conversation_history", []) + [("user", user_input), ("ai", response)]
#         return state

#     initial_state_mock = {
#         "conversation_history": [],
#         "current_user_input": None,
#         "master_agent_decision": None,
#         # ... otros campos que el agente real podría necesitar ...
#     }
#     # --- Fin de Simulación de Agente ---

#     app = ChatApplication(root, agent_app=mock_agent_app, initial_agent_state=initial_state_mock)
#     # Para obtener el saludo inicial del agente simulado, si está diseñado para ello:
#     # app.process_agent_turn(initial=True) # O el mensaje de bienvenida ya está puesto en __init__
#     root.mainloop()

# if __name__ == "__main__":
#     # main_gui_test() # Descomentar para probar la GUI aisladamente con el mock
#     pass # main.py será el que ejecute esto
