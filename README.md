```
⠀⠀⠀⠀⠀⠀⠀⠠⡧⠀⠀⠄⠀⣆
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⡄⠀⠀⠀⢺⠂⠀⠀⠀⢀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣧
⠤⣤⣤⣤⣤⣤⣤⣤⣤⣿⣿⠇⠀⢿⣿⣿⣷⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⣶⠶⠶⠶
⠀⠀⠘⢿⣿⣿⣟⠛⠛⠛⠛
⠀⠀⠁⠀⠈⠛⣿⣿⣦     ✧ card generator | a luhn-based tool ✧
⠀⠀⠀⠀⠀⠀⠀⢹⣿⡿            coded by t.me/vi77an
```

<div align="center">

**vl gen** · gerador de cartões de teste com verificação Luhn

![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)
![Web](https://img.shields.io/badge/web-html%20%7C%20zero%20deps-blueviolet?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos%20%7C%20browser-lightgrey?style=flat-square)

---

</div>

## sobre

**vl gen** é uma ferramenta para gerar cartões de teste válidos pelo algoritmo de Luhn a partir de um número completo, incompleto ou com padrão de `x` nas posições variáveis. Disponível em dois formatos: script Python CLI e interface web standalone (zero instalação).

---

## arquivos

```
projeto/
├── vl_gen.py        ← script CLI (Python)
├── vl_gen.html      ← interface web (abre direto no navegador)
└── output/           ← CSVs gerados pelo CLI
    └── gerador.log   ← log de operações
```

> A pasta `output/` é criada automaticamente ao rodar o script.

---

## requisitos

### cli
* Python 3.10 ou superior
* dependências opcionais (para cores e barra de progresso):

```
pip install colorama tqdm
```

### web
* nenhum — basta abrir `vl_gen.html` no navegador

---

## uso

### cli

```
python gerador.py
```

Ou passando o cartão diretamente:

```
python vl_gen.py "4321678901234xxx|10|27"
python vl_gen.py "4321678901234549|10|27" --no-interactive
```

### web

Abra o arquivo `vl_gen.html` em qualquer navegador moderno. Sem servidor, sem instalação.

---

## formatos de entrada

O script e a interface aceitam qualquer separador não-numérico entre os campos:

```
4321678901234xxx|10|27          ← padrão com x (recomendado)
4321678901234549|10|27          ← cartão completo (seleciona variação)
432167890123|10|27              ← incompleto (completa com x automático)
4321678901234xxx/10/27          ← separador barra
4321678901234xxx 10 27          ← separador espaço
```

> O CVV é sempre normalizado para `000`. O ano de 4 dígitos é convertido automaticamente para 2.

---

## modos de operação

| modo | detecção | comportamento |
| --- | --- | --- |
| **completo** | 16 dígitos, sem `x` | exibe seletor de variação (1.000x / 100x / 10x) |
| **padrão** | 16 chars com `x` | gera direto a partir das posições variáveis |
| **incompleto** | menos de 16 chars, sem `x` | completa com `x` no final e gera |

### variações (modo completo)

Quando um cartão de 16 dígitos é informado, é possível escolher quantas posições variar a partir do 13º dígito:

| variação | posições variáveis | combinações possíveis |
| --- | --- | --- |
| `xxxxxxxxxxxxXXXX` | 4 últimas | ~1.000 |
| `xxxxxxxxxxxxDXXX` | 3 últimas + 1 fixo | ~100 |
| `xxxxxxxxxxxxDDXX` | 2 últimas + 2 fixos | ~10 |

> O último `x` é sempre o dígito verificador do Luhn — calculado, não iterado.

---

## saída

Os cartões gerados são exibidos na tela e salvos em `.csv` com o formato:

```
card_number,month,year,cvv
4321678901234549,10,27,000
...
```

Nome do arquivo gerado pelo CLI:

```
output/<padrão>_<MM>_<AA>.csv
```

Na interface web, o CSV pode ser baixado com um clique ou copiado linha a linha.

---

## créditos

desenvolvido com 🩷 por [vilanele](https://t.me/vi77an)
