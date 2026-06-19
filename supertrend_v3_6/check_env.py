import sys
import os

def check():
    print("--- Verificando Ambiente do Supertrend v3.6 ---")

    # 1. Versão do Python
    print(f"Versão do Python: {sys.version}")

    # 2. Verificando Dependências
    try:
        import pandas
        print("✅ Pandas instalado.")
    except ImportError:
        print("❌ Pandas NÃO encontrado. Execute: pip install pandas")

    try:
        import numpy
        print("✅ NumPy instalado.")
    except ImportError:
        print("❌ NumPy NÃO encontrado. Execute: pip install numpy")

    try:
        import ccxt
        print("✅ CCXT instalado.")
    except ImportError:
        print("❌ CCXT NÃO encontrado. Execute: pip install ccxt")

    try:
        import tabulate
        print("✅ Tabulate instalado.")
    except ImportError:
        print("❌ Tabulate NÃO encontrado. Execute: pip install tabulate")

    # 3. Verificando estrutura de arquivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files = ["main.py", "core/calculator.py", "core/engine.py", "data/provider.py"]
    for f in files:
        full_path = os.path.join(script_dir, f)
        if os.path.exists(full_path):
            print(f"✅ Arquivo {f} encontrado.")
        else:
            print(f"❌ Arquivo {f} NÃO encontrado em {full_path}")

if __name__ == "__main__":
    check()
