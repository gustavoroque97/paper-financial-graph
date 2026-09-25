import re

# Read tables
with open('tables.md', 'r') as f:
    tables_content = f.read()
    
# We can extract the tables based on headers
def extract_table(header_str, text):
    parts = text.split(header_str)
    if len(parts) > 1:
        part = parts[1]
        lines = []
        for line in part.split('\n'):
            if line.startswith('###') and not line.strip() == '':
                break
            lines.append(line)
        return '\n'.join(lines).strip()
    return ""

t_acao_qtd = extract_table('### 2. Ações vs Não-Ações por Ano (Quantidade %)', tables_content)
t_acao_mcap = extract_table('### 3. Ações vs Não-Ações por Ano (Market Cap %)', tables_content)
t_ns_qtd = extract_table('### 4. Detalhe de Não-Ações por Ano (Quantidade %)', tables_content)
t_ns_mcap = extract_table('### 5. Detalhe de Não-Ações por Ano (Market Cap %)', tables_content)
t_setor_qtd = extract_table('### 6. Ações por Setor e Ano (Quantidade %)', tables_content)
t_setor_mcap = extract_table('### 7. Ações por Setor e Ano (Market Cap %)', tables_content)
t_hcm_extremos = extract_table('### 8. HCM: Decil 1 (Central) vs Decil 10 (Periférico) - Tipos de Ativo (Count %)', tables_content)
t_pozzi_extremos = extract_table('### 9. Pozzi: Decil 1 (Central) vs Decil 10 (Periférico) - Tipos de Ativo (Count %)', tables_content)
t_hcm_setores_extremos = extract_table('### 10. HCM: Setores nas Ações - Decil 1 vs Decil 10 (Count %)', tables_content)


md = f"""# Resumo da Análise de Composição do Universo de Investimento

Este documento sumariza os resultados e as tabelas geradas no notebook `universe_composition_analysis.ipynb`, que avalia a estrutura do universo de ativos e os extremos de cada portfólio.

## 1. Distribuição Global de Tipos de Ativos
O universo de investimento contém um total de **40.662 registros** ao longo dos anos, divididos em grandes grupos (ações e não-ações). A grande maioria é composta por ações individuais, seguidas pelos ETFs.

**Total Histórico (Contagem Absoluta):**
- **Stock (Ações):** 24.004
- **ETF:** 11.981
- **Closed-End Fund:** 3.200
- **REIT (Fundo Imobiliário):** 1.477

---

## 2. Ações vs Não-Ações (Evolução Temporal)
A análise temporal revela como a composição do mercado e da amostra tem se alterado ao longo da última década.

**Explicação Breve:**
Existe uma clara **tendência de crescimento na proporção de Não-Ações** (principalmente ETFs) por quantidade. Em 2014, o universo era composto por 65% de Ações e 35% de Não-Ações. Em 2024, essa proporção mudou para **55% Ações e 45% Não-Ações**. Por Market Cap, ações dominavam com >80% até 2018. **Atenção:** As tabelas indicam que, de 2019 em diante, as ações passam a representar subitamente mais de ~99% do Market Cap total. Isso sugere fortemente uma mudança na metodologia da base de dados de origem (market cap de fundos pode estar ausente).

### 2.1 Por Quantidade (Count %)
{t_acao_qtd}

### 2.2 Por Market Cap (Mcap %)
{t_acao_mcap}

---

## 3. Composição Detalhada dos "Não-Ações"

**Explicação Breve:**
Quando isolamos apenas o grupo de Não-Ações (ETFs, CEFs e REITs), observamos que **os ETFs dominam**, saltando de **63%** do universo de Não-Ações em 2014 para **78%** em 2024. Em contrapartida, os **Closed-End Funds (CEFs)** caíram de **26% para 14,5%**, e os **REITs** de ~10% para 7,4%. Os ETFs também lideram com folga a distribuição de Market Cap deste segmento.

### 3.1 Detalhe de Não-Ações por Quantidade
{t_ns_qtd}

### 3.2 Detalhe de Não-Ações por Market Cap
{t_ns_mcap}

---

## 4. Composição Setorial das Ações

**Explicação Breve:**
Analisando apenas as "Stocks", o setor **Financeiro** lidera a quantidade de empresas (representando historicamente em torno de ~20% a 21%), seguido por **Industrials** (~15 a 17%) e **Healthcare** (crescendo de 13% para mais de 19%). Por Market Cap, os dados reforçam a anomalia pós-2019, onde o setor **Financeiro aparece concentrando de 95% a 97% do Market Cap**, indicando que valores de Market Cap para outros setores estão ausentes na fonte.

### 4.1 Ações por Setor (Quantidade %)
{t_setor_qtd}

### 4.2 Ações por Setor (Market Cap %)
{t_setor_mcap}

---

## 5. Composição de Portfólios Extremos (Decil 1 vs Decil 10)

A análise buscou entender a característica estrutural dos ativos que compõem o **Decil 1 (Portfólio Central)** e o **Decil 10 (Portfólio Periférico)** das duas principais topologias de rede investigadas: **HCM** e **Pozzi**.

### 5.1 Topologia HCM (Ações vs Não-Ações)

**Explicação Breve:**
O núcleo do HCM (Decil 1) abriga a maior parte das Ações puras (~55-75% nos primeiros anos, embora haja flutuação). Interessante notar que na periferia (Decil 10), existe uma predominância frequente de Não-Ações (acima de 50% em muitos anos).

{t_hcm_extremos}

### 5.2 Topologia Pozzi (Ações vs Não-Ações)

**Explicação Breve:**
O modelo Pozzi (PMFG) consegue conectar os fundos/ETFs muito mais no núcleo do que o HCM. Seu Decil 1 tem uma alta porcentagem de ETFs, enquanto o seu **Decil 10 joga fortemente as Ações puras para a periferia** (alcançando picos de até 81% de ações na periferia em 2023).

{t_pozzi_extremos}

### 5.3 Setores nas Ações Extremos (HCM)

**Explicação Breve:**
Olhando apenas para as ações no HCM: o **núcleo (Decil 1)** é dominado por indústrias cíclicas (**Industrials ~30%** e **Financial ~25%**). Por outro lado, a periferia (**Decil 10**) tem um altíssimo desvio para o setor de **Healthcare** (chegando a incríveis 67% em 2023!), além de Financial. O isolamento do setor de Saúde na periferia da rede faz muito sentido econômico devido ao seu comportamento idiossincrático (empresas biológicas e farmacêuticas descoladas do ciclo de mercado).

{t_hcm_setores_extremos}
"""

with open('/home/maria-eduarda/.gemini/antigravity/brain/74fd619d-1c6f-4531-855f-958fbc18a97c/artifacts/universe_composition_summary.md', 'w') as f:
    f.write(md)

