import os
import sys

from teletools.preprocessing import normalize_number

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_phone_normalization():
    """Testa a função de normalização de números de telefone"""

    # Casos de teste
    test_cases = [
        "(11)99999-9999",
        "1199999-9999",
        "11999999999",
        "+551199999-9999",
        "+5511999999999",
        "(011)99999-9999",
        "01199999-9999",
    ]

    print("Testando normalização de números de telefone:\n")

    for phone in test_cases:
        try:
            normalized = normalize_number(phone)
            print(f"Original: {phone:<20} | Normalizado: {normalized}")
        except Exception as e:
            print(f"Erro ao processar {phone}: {e}")


if __name__ == "__main__":
    # Teste interativo
    while True:
        user_input = input("\nDigite um número de telefone (ou 'quit' para sair): ")
        if user_input.lower() == "quit":
            break

        try:
            result = normalize_number(user_input)
            print(f"Número normalizado: {result}")
        except Exception as e:
            print(f"Erro: {e}")

    # Executar casos de teste predefinidos
    test_phone_normalization()
