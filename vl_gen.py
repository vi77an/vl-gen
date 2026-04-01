#!/usr/bin/env python3
# criado por t.me/vi77an *-*
# com amor, carinho e com claudinho
"""
gerador de cartões de teste com verificação Luhn.
tema visual: draculinho by @vi77an
"""

import sys
import os
import re
import csv
import logging
import argparse
from datetime import datetime
from itertools import product
from pathlib import Path

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# ─── Dracula Palette via colorama ──────────────────────────────────────────── @vi77an
def c(text, color):
    if not HAS_COLOR:
        return text
    colors = {
        "purple":  Fore.MAGENTA  + Style.BRIGHT,
        "cyan":    Fore.CYAN     + Style.BRIGHT,
        "green":   Fore.GREEN    + Style.BRIGHT,
        "yellow":  Fore.YELLOW   + Style.BRIGHT,
        "red":     Fore.RED      + Style.BRIGHT,
        "pink":    Fore.MAGENTA,
        "white":   Fore.WHITE    + Style.BRIGHT,
        "dim":     Style.DIM     + Fore.WHITE,
        "orange":  Fore.YELLOW,
    }
    reset = Style.RESET_ALL if HAS_COLOR else ""
    return colors.get(color, "") + str(text) + reset

# ─── Output / Log dirs ─────────────────────────────────────────────────────── @vi77an
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

LOG_FILE = OUTPUT_DIR / "gerador.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def log(msg):
    logging.info(msg)

# ─── Luhn ──────────────────────────────────────────────────────────────────── @vi77an
def luhn_checksum(number: str) -> int:
    """Retorna o checksum Luhn (deve ser 0 para cartão válido)."""
    total = 0
    reverse_digits = number[::-1]
    for i, d in enumerate(reverse_digits):
        n = int(d)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10

def luhn_valid(number: str) -> bool:
    return luhn_checksum(number) == 0

def luhn_complete(prefix: str) -> str | None:
    """Dado um prefixo (sem o dígito verificador), retorna o dígito que completa o Luhn."""
    for d in range(10):
        candidate = prefix + str(d)
        if luhn_valid(candidate):
            return candidate
    return None

# ─── Parsing de entrada ────────────────────────────────────────────────────── @vi77an
def parse_input(raw: str) -> dict:
    """
    Aceita qualquer separador não-dígito e não-x entre os campos.
    Retorna dict com keys: card, month, year, cvv
    year sempre em yy; cvv sempre '000'.
    """
    # Divide pelos separadores (qualquer coisa que não seja dígito, 'x' ou 'X')
    parts = re.split(r"[^0-9xX]+", raw.strip())
    parts = [p for p in parts if p]  # remove vazios

    if len(parts) < 1:
        raise ValueError("Entrada inválida.")

    card_raw = parts[0]

    month = parts[1] if len(parts) > 1 else "12"
    year  = parts[2] if len(parts) > 2 else "99"

    # Normaliza ano
    if len(year) == 4:
        year = year[2:]

    # CVV sempre 000
    cvv = "000"

    return {
        "card": card_raw.lower(),   # x em minúsculo para consistência
        "month": month.zfill(2),
        "year": year,
        "cvv": cvv,
    }

def validate_date(month: str, year: str) -> bool:
    """Retorna True se MM/YY >= data atual."""
    now = datetime.now()
    try:
        exp = datetime.strptime(f"01/{month}/{year}", "%d/%m/%y")
        # Ajusta: cartão válido até o último dia do mês de expiração
        # Simplificado: compara ano/mês
        exp_ym = (exp.year, exp.month)
        now_ym = (now.year, now.month)
        return exp_ym >= now_ym
    except ValueError:
        return False

# ─── Detecção de modo ──────────────────────────────────────────────────────── @vi77an
def count_x(card: str) -> int:
    return card.count('x')

def is_complete_card(card: str) -> bool:
    """16 dígitos, sem x."""
    return len(card) == 16 and card.isdigit()

def is_partial_card(card: str) -> bool:
    """Contém x e total de chars (dígitos+x) == 16."""
    return 'x' in card and (len(card) == 16)

def is_incomplete_card(card: str) -> bool:
    """Menos de 16 chars sem x → faltam dígitos no final."""
    return 'x' not in card and len(card) < 16

# ─── Geração de matrizes (modo cartão completo) ────────────────────────────── @vi77an
def build_matrices(card: str) -> list[str]: 
    """
    Substitui o 5º dígito de trás por 0-9 e marca os últimos 4 como xxxx.
    card deve ter 16 dígitos sem x.
    Retorna lista de 10 strings padrão de matriz, ex: '432167890120xxxx'
    """
    matrices = []
    prefix12 = card[:12]  # primeiros 12 dígitos
    # 5º da direita = índice 11 (0-based), ou seja card[11]
    # Os 4 últimos (índices 12-15) viram xxxx
    for d in range(10):
        mat = prefix12[:11] + str(d) + "xxxx"
        matrices.append(mat)
    return matrices

# ─── Geração de cartões a partir de uma matriz/padrão ─────────────────────── @vi77an
def generate_cards_from_pattern(pattern: str, month: str, year: str) -> list[dict]:
    """
    Gera todos os cartões válidos pelo Luhn a partir de um padrão com x.
    O último dígito (posição 15) é sempre calculado pelo Luhn.
    Se o último char for x: ele é o dígito de Luhn (só 1 valor válido por prefixo).
    Se o último char for fixo: valida o cartão completo.
    """
    x_positions = [i for i, ch in enumerate(pattern) if ch == 'x']

    if not x_positions:
        # padrão fixo, sem x
        if luhn_valid(pattern):
            return [_card_dict(pattern, month, year)]
        return []

    last_x = x_positions[-1]
    fixed_x_positions = x_positions[:-1]  # todos os x exceto o último

    # Itera sobre combinações dos x internos
    cards = []
    combos = list(product("0123456789", repeat=len(fixed_x_positions)))

    iterator = tqdm(combos, desc=c("  Gerando", "cyan"), unit="combo") if HAS_TQDM and len(combos) > 100 else combos

    for combo in iterator:
        # Monta o prefixo com combo aplicado
        chars = list(pattern)
        for pos, digit in zip(fixed_x_positions, combo):
            chars[pos] = digit

        prefix = "".join(chars[:last_x])  # tudo antes do último x @vi77an

        # BIN sempre fixo (primeiros 6)
        # (já garantido pela restrição de entrada, mas verificamos)
        # Calcula dígito Luhn para a posição last_x
        candidate = luhn_complete(prefix)
        if candidate is None:
            continue

        # Verifica que os dígitos fixos após last_x batem @vi77an
        tail_fixed = pattern[last_x+1:]
        full = candidate + tail_fixed
        if len(full) != 16:
            continue
        if not luhn_valid(full):
            continue

        cards.append(_card_dict(full, month, year))

    return cards

def _card_dict(number: str, month: str, year: str) -> dict:
    return {
        "card_number": number,
        "month": month,
        "year": year,
        "cvv": "000",
    }

# ─── CSV ───────────────────────────────────────────────────────────────────── @vi77an
def csv_filename(pattern: str, month: str, year: str) -> Path:
    safe = pattern.replace('x', 'x')  # já está ok
    return OUTPUT_DIR / f"{safe}_{month}_{year}.csv"

def save_csv(cards: list[dict], filepath: Path):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["card_number", "month", "year", "cvv"])
        writer.writeheader()
        writer.writerows(cards)

def check_duplicate(filepath: Path) -> bool:
    return filepath.exists()

# ─── UI helpers ────────────────────────────────────────────────────────────── @vi77an
BANNER = f"""
{c('╔══════════════════════════════════════════╗', 'purple')}
{c('║', 'purple')}  {c('   vl@gen:~/luhn.js    ', 'cyan')}                 {c('║', 'purple')}
{c('║', 'purple')}  {c('com verificação luhn  |  by t.me/vi77an', 'dim')} {c('║', 'purple')}
{c('╚══════════════════════════════════════════╝', 'purple')}
"""

def ask(prompt: str) -> str:
    return input(c(prompt, "yellow")).strip()

def yn(prompt: str) -> bool:
    ans = ask(prompt + " (s/n): ").lower()
    return ans in ("s", "sim", "y", "yes")

def print_info(msg):    print(c("  ℹ ", "cyan")  + msg)
def print_ok(msg):      print(c("  ✔ ", "green") + msg)
def print_warn(msg):    print(c("  ⚠ ", "yellow")+ msg)
def print_err(msg):     print(c("  ✖ ", "red")   + msg)

# ─── Fluxos principais ─────────────────────────────────────────────────────── @vi77an

def flow_complete_card(parsed: dict, non_interactive: bool = False) -> bool:
    """Fluxo para cartão completo de 16 dígitos."""
    card   = parsed["card"]
    month  = parsed["month"]
    year   = parsed["year"]

    matrices = build_matrices(card)

    print(c("\n  Selecione sua matriz:\n", "purple"))
    for i, mat in enumerate(matrices, 1):
        print(f"  {c(f'[{i:02d}]', 'pink')} {c(mat, 'white')}")
    print()

    if non_interactive:
        print_err("Modo não-interativo requer padrão com x ou cartão incompleto.")
        return False

    raw_choice = ask("\n  Escolha [01-10]: ")
    try:
        choice = int(raw_choice)
        if not 1 <= choice <= 10:
            raise ValueError
    except ValueError:
        print_err("Opção inválida.")
        return False

    selected_matrix = matrices[choice - 1]
    return flow_select_variation(selected_matrix, month, year)


def ask_digit(prompt: str) -> str | None:
    """Pede um único dígito 0-9 ao usuário. Retorna None se inválido."""
    raw = ask(prompt).strip()
    if len(raw) == 1 and raw.isdigit():
        return raw
    print_err("Digite apenas um dígito de 0 a 9.")
    return None


def flow_select_variation(matrix: str, month: str, year: str, non_interactive: bool = False) -> bool:
    """
    Dado uma matriz com 4 x no final (ex: 512267223639xxxx), oferece 4 variações:

    Lógica correta de Luhn:
      O último x é SEMPRE o dígito verificador Luhn (1 valor determinístico por prefixo).
      Os x anteriores são dígitos livres (cada um = 10 possibilidades).

      xxxx  →  3 livres + 1 Luhn  =  10³  =  1.000 válidos  (prefixo de 12 fixo)
      ?xxx  →  2 livres + 1 Luhn  =  10²  =    100 válidos  (prefixo de 13: pede 1 dígito)
      ??xx  →  1 livre  + 1 Luhn  =  10¹  =     10 válidos  (prefixo de 14: pede 2 dígitos)

    Para as opções 2 e 3, o script pede ao usuário o(s) dígito(s) extra(s)
    que fixam o prefixo antes dos x restantes.
    """
    prefix12 = matrix[:12]  # os 12 dígitos fixos da matriz selecionada @vi77an

    # Exibe as opções com placeholder ? para os dígitos que o usuário vai fornecer
    display_variants = [
        (prefix12 + "xxxx", "1.000 possibilidades"),
        (prefix12 + "?xxx", "100 possibilidades — você escolhe 1 dígito extra"),
        (prefix12 + "??xx", "10 possibilidades  — você escolhe 2 dígitos extra"),
        ("custom",           "outra variação"),
    ]

    print(c("\n  Selecione a variação desejada:\n", "purple"))
    for i, (pat, desc) in enumerate(display_variants, 1):
        display = pat if pat != "custom" else c("── personalizado ──", "dim")
        print(f"  {c(f'[{i:02d}]', 'pink')} {c(display, 'white')} {c('- ' + desc + '!', 'dim')}")
    print()

    if non_interactive:
        print_err("Modo não-interativo: use padrão com x diretamente.")
        return False

    raw = ask("  Escolha [01-04]: ")
    try:
        v = int(raw)
        if not 1 <= v <= 4:
            raise ValueError
    except ValueError:
        print_err("Opção inválida.")
        return False

    if v == 4:
        return flow_custom_variation(month, year)

    if v == 1:
        # 1.000 → prefixo de 12 + xxxx
        pattern = prefix12 + "xxxx"

    elif v == 2:
        # 100 → prefixo de 12 + 1 dígito escolhido + xxx
        print_info(f"Prefixo fixo: {c(prefix12, 'white')}")
        print_info("Digite o 13º dígito (posição fixa antes dos xxx):")
        d1 = ask_digit("  Dígito [0-9]: ")
        if d1 is None:
            return False
        pattern = prefix12 + d1 + "xxx"

    elif v == 3:
        # 10 → prefixo de 12 + 2 dígitos escolhidos + xx
        print_info(f"Prefixo fixo: {c(prefix12, 'white')}")
        print_info("Digite o 13º dígito (posição fixa antes dos xx):")
        d1 = ask_digit("  13º dígito [0-9]: ")
        if d1 is None:
            return False
        print_info("Digite o 14º dígito (posição fixa antes dos xx):")
        d2 = ask_digit("  14º dígito [0-9]: ")
        if d2 is None:
            return False
        pattern = prefix12 + d1 + d2 + "xx"

    return flow_generate(pattern, month, year)


def flow_custom_variation(month: str, year: str, non_interactive: bool = False) -> bool:
    """Usuário digita o padrão customizado com x."""
    print_info("Digite a variação com x nas posições desejadas.")
    print_info(c("Exemplo: 43216789012x4x4x|10|30|300", "dim"))
    raw = ask("  Variação: ")
    parsed = parse_input(raw)
    pattern = parsed["card"]
    m = parsed["month"] or month
    y = parsed["year"]  or year

    # BIN (primeiros 6) deve ser fixo @vi77an
    if 'x' in pattern[:6]:
        print_err("Os primeiros 6 dígitos (BIN) devem ser fixos.")
        return False

    return flow_generate(pattern, m, y)


def flow_generate(pattern: str, month: str, year: str) -> bool:
    """Gera os cartões, salva CSV, exibe resultado."""
    filepath = csv_filename(pattern, month, year)

    if check_duplicate(filepath):
        print_warn(f"Matriz {c(pattern, 'orange')} já foi gerada antes!")
        print_warn(f"Arquivo: {c(str(filepath), 'dim')}")
        log(f"DUPLICATE | {pattern} | {month}/{year}")
        return False

    nx = count_x(pattern)
    expected = 10 ** (nx - 1) if nx > 0 else (1 if luhn_valid(pattern) else 0)
    print_info(f"Padrão: {c(pattern, 'white')}  |  Máx. válidos esperados: {c(str(expected), 'cyan')}")

    cards = generate_cards_from_pattern(pattern, month, year)

    if not cards:
        print_err("Nenhum cartão válido gerado.")
        return False

    save_csv(cards, filepath)
    print_ok(f"{c(str(len(cards)), 'green')} cartão(ões) gerado(s) com sucesso!")
    print_ok(f"Acesse em: {c(str(filepath), 'cyan')}")
    log(f"GENERATED | {pattern} | {month}/{year} | {len(cards)} cards | {filepath}")
    return True


def flow_incomplete_card(parsed: dict, non_interactive: bool = False) -> bool:
    """Cartão incompleto (sem x, menos de 16 dígitos): completa com x e gera."""
    card  = parsed["card"]
    month = parsed["month"]
    year  = parsed["year"]

    missing = 16 - len(card)
    pattern = card + "x" * missing

    nx = count_x(pattern)
    expected = 10 ** (nx - 1) if nx > 1 else 10

    print_info(f"Padrão detectado: {c(pattern, 'white')}")
    print_info(f"Possibilidades válidas estimadas: {c(str(expected), 'cyan')}")

    if not non_interactive:
        if not yn("  Deseja gerar agora?"):
            print_info("Operação cancelada.")
            return False

    return flow_generate(pattern, month, year)


def flow_pattern_card(parsed: dict, non_interactive: bool = False) -> bool:
    """Cartão com x explícito na posição desejada."""
    pattern = parsed["card"]
    month   = parsed["month"]
    year    = parsed["year"]

    if 'x' in pattern[:6]:
        print_err("Os primeiros 6 dígitos (BIN) devem ser fixos.")
        return False

    nx = count_x(pattern)
    expected = 10 ** (nx - 1) if nx > 0 else 0
    print_info(f"Padrão: {c(pattern, 'white')}  |  Possibilidades válidas: {c(str(expected), 'cyan')}")

    if not non_interactive:
        if not yn("  Confirma geração?"):
            print_info("Operação cancelada.")
            return False

    return flow_generate(pattern, month, year)


# ─── Loop principal ────────────────────────────────────────────────────────── @vi77an

def main_loop(initial_input: str | None = None, non_interactive: bool = False):
    print(BANNER)
    if not HAS_COLOR:
        print_warn("colorama não instalado. Execute: pip install colorama tqdm")
    if not HAS_TQDM:
        print_warn("tqdm não instalado. Barra de progresso desativada.")

    first = True
    while True:
        if first and initial_input:
            raw = initial_input
            first = False
        else:
            print()
            raw = ask("Insira cartão/matriz (formato: CARTAO|MM|AA ou CARTAO|MM|AA|CVV): ")
            if not raw:
                continue

        try:
            parsed = parse_input(raw)
        except ValueError as e:
            print_err(str(e))
            if non_interactive:
                break
            continue

        # Validação de data @vi77an
        if not validate_date(parsed["month"], parsed["year"]):
            print_err(
                f"Cartão expirado! Data {c(parsed['month']+'/'+ parsed['year'], 'orange')} "
                f"está fora da validade."
            )
            log(f"EXPIRED | {parsed['card']} | {parsed['month']}/{parsed['year']}")
            if non_interactive:
                break
            continue

        card = parsed["card"]

        if is_complete_card(card):
            flow_complete_card(parsed, non_interactive)
        elif is_partial_card(card):
            flow_pattern_card(parsed, non_interactive)
        elif is_incomplete_card(card):
            flow_incomplete_card(parsed, non_interactive)
        else:
            print_err(f"Formato de cartão inválido: {c(card, 'orange')}")
            if non_interactive:
                break
            continue

        if non_interactive:
            break

        print()
        if not yn("  Deseja continuar no gerador?"):
            print(c("\n  Ok, até logo! 👋\n", "purple"))
            break


# ─── Entry point ───────────────────────────────────────────────────────────── @vi77an

def main():
    parser = argparse.ArgumentParser(
        description="Gerador de cartões de teste com verificação Luhn.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python gerador.py "4321678901234549|10|30|300"
  python gerador.py "4321678901234|10|30" --no-interactive
  python gerador.py "43216789012x4x4x|10|30" --no-interactive
        """,
    )
    parser.add_argument(
        "cartao",
        nargs="?",
        help="Cartão/matriz inicial (ex: 4321678901234549|10|30|300)",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        dest="non_interactive",
        help="Modo não-interativo: gera direto sem prompts (requer padrão com x ou incompleto)",
    )

    args = parser.parse_args()
    main_loop(
        initial_input=args.cartao,
        non_interactive=args.non_interactive,
    )


if __name__ == "__main__":
    main()

# volte sempre :) #vi77an
