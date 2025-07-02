import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def load_api_key():
    """Carga la API key de OpenAI desde el archivo .env."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY no encontrada. "
            "Asegúrate de que esté definida en tu archivo .env o como variable de entorno."
        )
    return api_key

def get_llm(temperature: float = 0.0, model_name: str = None) -> ChatOpenAI:
    """
    Inicializa y retorna una instancia del LLM de OpenAI.

    Args:
        temperature: La temperatura para la generación del LLM.
        model_name: El nombre del modelo a usar (ej: "gpt-4o-mini").
                    Si es None, se tomará de la variable de entorno OPENAI_MODEL_NAME,
                    o se usará el default de ChatOpenAI.

    Returns:
        Una instancia de ChatOpenAI.
    """
    api_key = load_api_key() # Esto también valida que la API key exista

    if model_name is None:
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini") # Default a gpt-4o-mini si no está en .env

    llm = ChatOpenAI(
        openai_api_key=api_key,
        model_name=model_name,
        temperature=temperature
    )
    print(f"LLM inicializado con el modelo: {llm.model_name}, Temperatura: {temperature}")
    return llm

if __name__ == "__main__":
    try:
        # Prueba de carga de API key y LLM
        # Para que esto funcione, necesitas tener un archivo .env en la raíz del proyecto
        # con tu OPENAI_API_KEY="sk-..."
        # y opcionalmente OPENAI_MODEL_NAME="gpt-4o-mini"

        # Simular estar en el directorio raíz para que .env sea encontrado
        # Esto es solo para la prueba directa de este script.
        # En la aplicación principal, .env se carga desde donde se ejecuta python -m src.main
        if os.path.basename(os.getcwd()) == "utils":
            os.chdir(os.path.join("..", "..")) # Moverse dos directorios arriba a la raíz del proyecto
            print(f"Cambiado el directorio a: {os.getcwd()} para encontrar .env")

        llm_instance = get_llm()
        print("LLM instanciado exitosamente.")

        # Ejemplo de invocación simple (requiere que la API key sea válida)
        # from langchain_core.messages import HumanMessage
        # response = llm_instance.invoke([HumanMessage(content="Hola, ¿cómo estás?")])
        # print(f"Respuesta del LLM: {response.content}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e_gen:
        print(f"Un error inesperado ocurrió: {e_gen}")
